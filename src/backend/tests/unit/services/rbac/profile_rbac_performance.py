"""cProfile-based profiling for RBAC permission evaluation.

This module uses cProfile to identify performance bottlenecks in RBAC code.
Validates Task 2.3 success criterion: "Profiling shows no obvious bottlenecks"

Usage:
    # Run profiling
    uv run python profile_rbac_performance.py

    # Run with custom iterations
    uv run python profile_rbac_performance.py --iterations 500

    # Generate visual call graph
    uv run python profile_rbac_performance.py --call-graph
"""

import argparse
import asyncio
import cProfile
import io
import pstats
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

from langflow.services.database.models.flow import Flow
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.rbac import Permission, Role, RoleAssignment, RolePermission
from langflow.services.database.models.user import User
from langflow.services.database.models.user_group import UserGroup, UserGroupMember
from langflow.services.database.models.workspace import Workspace
from langflow.services.deps import async_session_scope
from langflow.services.rbac.cache import reset_permission_cache
from langflow.services.rbac.enforcement import RBACEnforcementEngine


class RBACProfiler:
    """Profiler for RBAC permission evaluation performance."""

    def __init__(self, iterations: int = 100):
        """Initialize profiler.

        Args:
            iterations: Number of permission checks to profile
        """
        self.iterations = iterations
        self.session = None
        self.test_data = {}

    async def setup_test_data(self):
        """Create test data for profiling."""
        async with async_session_scope() as session:
            self.session = session

            # Create workspace
            workspace = Workspace(
                name="Profile Test Workspace",
                slug=f"profile-workspace-{uuid4().hex[:8]}",
                description="Workspace for profiling",
            )
            session.add(workspace)
            await session.commit()
            await session.refresh(workspace)

            # Create user
            user = User(
                username=f"profile_user_{uuid4().hex[:8]}",
                password="hashed_password",
                is_active=True,
                is_superuser=False,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Create project (folder)
            project = Folder(
                name="Profile Test Project",
                user_id=uuid4(),
                workspace_id=workspace.id,
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)

            # Create flow
            flow = Flow(
                name="Profile Test Flow",
                data={},
                folder_id=project.id,
                user_id=uuid4(),
            )
            session.add(flow)
            await session.commit()
            await session.refresh(flow)

            # Create permission
            permission = Permission(
                resource_type="flow",
                action="read",
                display_name="Read Flow",
                description="Permission to read flows",
            )
            session.add(permission)
            await session.commit()
            await session.refresh(permission)

            # Create role
            role = Role(
                name=f"profile_role_{uuid4().hex[:8]}",
                display_name="Profile Test Role",
                description="Role for profiling",
            )
            session.add(role)
            await session.commit()
            await session.refresh(role)

            # Link role to permission
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
            session.add(role_permission)
            await session.commit()

            # Assign role to user at workspace scope
            assignment = RoleAssignment(
                role_id=role.id,
                assignee_type="user",
                user_id=user.id,
                scope_type="workspace",
                scope_id=workspace.id,
            )
            session.add(assignment)
            await session.commit()

            # Create user group for group membership testing
            group = UserGroup(
                workspace_id=workspace.id,
                name=f"profile_group_{uuid4().hex[:8]}",
                description="Group for profiling",
            )
            session.add(group)
            await session.commit()
            await session.refresh(group)

            membership = UserGroupMember(
                group_id=group.id,
                user_id=user.id,
                is_active=True,
            )
            session.add(membership)
            await session.commit()

            self.test_data = {
                "user_id": user.id,
                "flow_id": flow.id,
                "workspace_id": workspace.id,
                "project_id": project.id,
                "group_id": group.id,
            }

            print("✓ Test data created successfully")
            print(f"  User ID: {user.id}")
            print(f"  Flow ID: {flow.id}")
            print(f"  Workspace ID: {workspace.id}")

    async def profile_cached_permission_checks(self):
        """Profile cached permission checks (hot path)."""
        print(f"\n{'=' * 60}")
        print("PROFILING: Cached Permission Checks (Hot Path)")
        print(f"{'=' * 60}")

        async with async_session_scope() as session:
            engine = RBACEnforcementEngine(session)

            # Prime cache
            await engine.has_permission(
                user_id=self.test_data["user_id"],
                permission="flow.read",
                resource_type="flow",
                resource_id=self.test_data["flow_id"],
            )

            # Profile cached checks
            profiler = cProfile.Profile()

            async def run_checks():
                for _ in range(self.iterations):
                    await engine.has_permission(
                        user_id=self.test_data["user_id"],
                        permission="flow.read",
                        resource_type="flow",
                        resource_id=self.test_data["flow_id"],
                    )

            profiler.enable()
            await run_checks()
            profiler.disable()

            # Print results
            self._print_profile_stats(profiler, "cached_permission_checks")

    async def profile_uncached_permission_checks(self):
        """Profile uncached permission checks (cold path)."""
        print(f"\n{'=' * 60}")
        print("PROFILING: Uncached Permission Checks (Cold Path)")
        print(f"{'=' * 60}")

        profiler = cProfile.Profile()

        async def run_checks():
            for _ in range(self.iterations // 2):  # Fewer iterations for cold path
                # Reset cache each time to force cold path
                reset_permission_cache()

                async with async_session_scope() as session:
                    engine = RBACEnforcementEngine(session)
                    await engine.has_permission(
                        user_id=self.test_data["user_id"],
                        permission="flow.read",
                        resource_type="flow",
                        resource_id=self.test_data["flow_id"],
                    )

        profiler.enable()
        await run_checks()
        profiler.disable()

        # Print results
        self._print_profile_stats(profiler, "uncached_permission_checks")

    async def profile_scope_resolution(self):
        """Profile scope chain resolution."""
        print(f"\n{'=' * 60}")
        print("PROFILING: Scope Chain Resolution")
        print(f"{'=' * 60}")

        async with async_session_scope() as session:
            engine = RBACEnforcementEngine(session)

            profiler = cProfile.Profile()

            async def run_resolution():
                for _ in range(self.iterations):
                    # This will traverse workspace -> project -> flow scope chain
                    await engine.has_permission(
                        user_id=self.test_data["user_id"],
                        permission="flow.read",
                        resource_type="flow",
                        resource_id=self.test_data["flow_id"],
                    )

            # Clear cache to force scope resolution
            reset_permission_cache()

            profiler.enable()
            await run_resolution()
            profiler.disable()

            self._print_profile_stats(profiler, "scope_resolution")

    async def profile_cache_operations(self):
        """Profile cache operations."""
        print(f"\n{'=' * 60}")
        print("PROFILING: Cache Operations")
        print(f"{'=' * 60}")

        from langflow.services.rbac.cache import PermissionCache

        reset_permission_cache()
        cache = PermissionCache(maxsize=10000, ttl=300)

        user_id = uuid4()
        resource_id = uuid4()

        profiler = cProfile.Profile()

        async def run_cache_ops():
            for i in range(self.iterations * 10):  # More iterations for cache ops
                # Set and get
                await cache.set(user_id, "flow.read", "flow", resource_id, True)
                await cache.get(user_id, "flow.read", "flow", resource_id)

                # Vary keys to test hash performance
                varied_resource_id = uuid4()
                cache._make_key(user_id, "flow.read", "flow", varied_resource_id)

        profiler.enable()
        await run_cache_ops()
        profiler.disable()

        self._print_profile_stats(profiler, "cache_operations")

    def _print_profile_stats(self, profiler: cProfile.Profile, profile_name: str):
        """Print profiling statistics.

        Args:
            profiler: The cProfile.Profile instance
            profile_name: Name for this profiling run
        """
        # Create string buffer for stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)

        # Sort by cumulative time
        ps.strip_dirs()
        ps.sort_stats(pstats.SortKey.CUMULATIVE)

        print("\nTop 20 functions by cumulative time:")
        print("-" * 60)
        ps.print_stats(20)
        print(s.getvalue())

        # Sort by time per call
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats(pstats.SortKey.TIME)

        print("\nTop 20 functions by time per call:")
        print("-" * 60)
        ps.print_stats(20)
        print(s.getvalue())

        # Save stats to file for later analysis
        stats_file = Path(__file__).parent / f"profile_{profile_name}.prof"
        profiler.dump_stats(str(stats_file))
        print(f"\n✓ Profile stats saved to: {stats_file}")

        # Identify potential bottlenecks
        self._analyze_bottlenecks(profiler)

    def _analyze_bottlenecks(self, profiler: cProfile.Profile):
        """Analyze profile for potential bottlenecks.

        Args:
            profiler: The cProfile.Profile instance
        """
        print(f"\n{'=' * 60}")
        print("BOTTLENECK ANALYSIS")
        print(f"{'=' * 60}")

        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats(pstats.SortKey.CUMULATIVE)

        # Get stats
        stats = ps.stats

        # Identify functions taking >10% of total time
        total_time = ps.total_tt
        bottlenecks = []

        for func, (cc, nc, tt, ct, callers) in stats.items():
            if ct > total_time * 0.10:  # >10% of total time
                filename, line, func_name = func
                bottlenecks.append({
                    "function": f"{filename}:{line}({func_name})",
                    "cumulative_time": ct,
                    "percentage": (ct / total_time) * 100,
                    "calls": cc,
                })

        if bottlenecks:
            print("\n⚠️  Potential Bottlenecks (>10% of total time):")
            print("-" * 60)
            for i, bottleneck in enumerate(sorted(bottlenecks, key=lambda x: -x["cumulative_time"]), 1):
                print(f"{i}. {bottleneck['function']}")
                print(f"   Cumulative Time: {bottleneck['cumulative_time']:.4f}s ({bottleneck['percentage']:.1f}%)")
                print(f"   Calls: {bottleneck['calls']}")
                print()
        else:
            print("\n✅ No obvious bottlenecks detected (all functions <10% of total time)")

        # Check for excessive function calls
        high_call_funcs = []
        for func, (cc, nc, tt, ct, callers) in stats.items():
            if cc > self.iterations * 100:  # More than 100x the iteration count
                filename, line, func_name = func
                high_call_funcs.append({
                    "function": f"{filename}:{line}({func_name})",
                    "calls": cc,
                    "time_per_call": tt / cc if cc > 0 else 0,
                })

        if high_call_funcs:
            print("\n⚠️  High Call Count Functions (potential N+1 issues):")
            print("-" * 60)
            for i, func in enumerate(sorted(high_call_funcs, key=lambda x: -x["calls"]), 1):
                print(f"{i}. {func['function']}")
                print(f"   Calls: {func['calls']}")
                print(f"   Time per Call: {func['time_per_call']*1000:.4f}ms")
                print()
        else:
            print("\n✅ No excessive function call patterns detected")

    async def run_all_profiles(self):
        """Run all profiling scenarios."""
        print("=" * 60)
        print("RBAC PERFORMANCE PROFILING")
        print("=" * 60)
        print(f"Iterations per test: {self.iterations}")
        print("=" * 60)

        await self.setup_test_data()
        await self.profile_cached_permission_checks()
        await self.profile_uncached_permission_checks()
        await self.profile_scope_resolution()
        await self.profile_cache_operations()

        print("\n" + "=" * 60)
        print("PROFILING COMPLETE")
        print("=" * 60)
        print("\nProfile data files created in current directory:")
        print("  - profile_cached_permission_checks.prof")
        print("  - profile_uncached_permission_checks.prof")
        print("  - profile_scope_resolution.prof")
        print("  - profile_cache_operations.prof")
        print("\nAnalyze with:")
        print("  uv run python -m pstats profile_*.prof")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Profile RBAC performance")
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations per test (default: 100)",
    )
    parser.add_argument(
        "--call-graph",
        action="store_true",
        help="Generate call graph visualization (requires gprof2dot and graphviz)",
    )

    args = parser.parse_args()

    profiler = RBACProfiler(iterations=args.iterations)

    # Run profiling
    asyncio.run(profiler.run_all_profiles())

    # Generate call graph if requested
    if args.call_graph:
        print("\nGenerating call graph visualizations...")
        try:
            import subprocess

            profile_files = Path(__file__).parent.glob("profile_*.prof")
            for profile_file in profile_files:
                dot_file = profile_file.with_suffix(".dot")
                png_file = profile_file.with_suffix(".png")

                # Convert prof to dot
                subprocess.run(
                    ["gprof2dot", "-f", "pstats", str(profile_file), "-o", str(dot_file)],
                    check=True,
                )

                # Convert dot to png
                subprocess.run(
                    ["dot", "-Tpng", str(dot_file), "-o", str(png_file)],
                    check=True,
                )

                print(f"  Created: {png_file}")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  ⚠️  Could not generate call graphs: {e}")
            print("  Install with: pip install gprof2dot && brew install graphviz")


if __name__ == "__main__":
    main()
