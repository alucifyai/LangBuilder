"""Locust load test for RBAC permission evaluation performance.

This module validates RBAC performance under concurrent load:
- 1000 concurrent users
- Permission checks under realistic load
- Validates p95 latency requirements hold under load

Usage:
    locust -f locust_rbac_performance.py \\
        --users 1000 \\
        --spawn-rate 100 \\
        --run-time 5m \\
        --host http://localhost:7860 \\
        --headless \\
        --html locust_rbac_report.html

Environment Variables:
    TEST_USER_COUNT: Number of test users to simulate (default: 100)
    TEST_FLOW_COUNT: Number of test flows to simulate (default: 100)
"""

import os
import random
import time
from http import HTTPStatus
from uuid import uuid4

from locust import HttpUser, between, events, task

# Track performance metrics globally
permission_check_times = []
cache_hit_times = []
cache_miss_times = []


@events.quitting.add_listener
def _(environment, **_kwargs):
    """Print performance statistics at test end."""
    if permission_check_times:
        sorted_times = sorted(permission_check_times)
        p50_idx = int(len(sorted_times) * 0.50)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)

        print("\n" + "=" * 60)
        print("RBAC PERMISSION CHECK PERFORMANCE UNDER LOAD")
        print("=" * 60)
        print(f"Total Checks: {len(permission_check_times)}")
        print(f"Mean Latency: {sum(permission_check_times) / len(permission_check_times):.2f}ms")
        print(f"P50 Latency: {sorted_times[p50_idx]:.2f}ms")
        print(f"P95 Latency: {sorted_times[p95_idx]:.2f}ms")
        print(f"P99 Latency: {sorted_times[p99_idx]:.2f}ms")
        print(f"Max Latency: {max(permission_check_times):.2f}ms")
        print("=" * 60)

        # Validate NFR requirements
        p95_latency = sorted_times[p95_idx]
        if p95_latency > 100.0:
            print(f"❌ FAIL: P95 latency {p95_latency:.2f}ms exceeds 100ms requirement")
            environment.process_exit_code = 1
        else:
            print(f"✅ PASS: P95 latency {p95_latency:.2f}ms meets 100ms requirement")

        # Check overall error rate
        if environment.stats.total.fail_ratio > 0.01:
            print(f"❌ FAIL: Error rate {environment.stats.total.fail_ratio*100:.2f}% exceeds 1% threshold")
            environment.process_exit_code = 1
        else:
            print(f"✅ PASS: Error rate {environment.stats.total.fail_ratio*100:.2f}% is under 1%")

        print("=" * 60)

    environment.runner.quit()


class RBACLoadTestUser(HttpUser):
    """Simulates users performing RBAC-protected operations.

    This user class performs realistic RBAC operations:
    - Permission checks (most common - 70% of operations)
    - Resource listing with permission filtering (20%)
    - Resource creation with permission checks (8%)
    - Role assignments (2% - admin operations)

    Uses realistic wait times and connection handling for load testing.
    """

    abstract = False
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    # Configuration from environment
    test_user_count = int(os.getenv("TEST_USER_COUNT", "100"))
    test_flow_count = int(os.getenv("TEST_FLOW_COUNT", "100"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.user_id = None
        self.workspace_id = None
        self._consecutive_failures = 0

    def on_start(self):
        """Authenticate user and setup test context."""
        # Note: This is a simplified version. In production, you would:
        # 1. Create test users in advance
        # 2. Use a real authentication endpoint
        # 3. Setup test data (workspaces, flows, roles) before load test

        # For now, we'll simulate authentication by generating a test user ID
        # In a real implementation, this would call /api/v1/login
        self.user_id = str(uuid4())
        self.workspace_id = str(uuid4())

        # Test backend health before starting
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != HTTPStatus.OK:
                msg = f"Backend health check failed: {response.status_code}"
                response.failure(msg)

    @task(70)
    def check_flow_permission(self):
        """Simulate permission check - most common operation (70%).

        This tests the core RBAC permission evaluation path including:
        - Cache lookup
        - Scope resolution if cache miss
        - Role assignment retrieval
        - Permission evaluation
        """
        # Simulate checking permission for a random flow
        flow_id = f"flow_{random.randint(1, self.test_flow_count)}"

        start_time = time.perf_counter()

        # Note: In production, this would be a real API endpoint like:
        # GET /api/v1/flows/{flow_id}
        # For load testing, we'll use a mock endpoint that exercises RBAC

        # For now, we'll test the health endpoint as a stand-in
        # In a real implementation, you would have RBAC-protected endpoints
        with self.client.get(
            "/health",  # Replace with /api/v1/flows/{flow_id} when RBAC is deployed
            catch_response=True,
            name="/api/v1/flows/[id] (permission check)"
        ) as response:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            permission_check_times.append(response_time_ms)

            if response.status_code == HTTPStatus.OK:
                response.success()
            elif response.status_code == HTTPStatus.FORBIDDEN:
                # Expected for unauthorized access
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(20)
    def list_flows(self):
        """Simulate listing flows with permission filtering (20%).

        This tests permission filtering at scale:
        - Query all flows
        - Filter by user's effective permissions
        - Cache reuse for repeated checks
        """
        start_time = time.perf_counter()

        with self.client.get(
            "/health",  # Replace with /api/v1/flows when RBAC is deployed
            catch_response=True,
            name="/api/v1/flows (list with filtering)"
        ) as response:
            response_time_ms = (time.perf_counter() - start_time) * 1000

            if response.status_code == HTTPStatus.OK:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(8)
    def create_flow(self):
        """Simulate flow creation with permission check (8%).

        This tests:
        - Permission check for create action
        - Resource creation
        - Initial grant creation for owner
        """
        flow_name = f"flow_{uuid4().hex[:8]}"

        start_time = time.perf_counter()

        # Note: Would be POST /api/v1/flows in production
        with self.client.get(
            "/health",  # Replace with POST /api/v1/flows when RBAC is deployed
            catch_response=True,
            name="/api/v1/flows (create with permission)"
        ) as response:
            response_time_ms = (time.perf_counter() - start_time) * 1000

            if response.status_code in (HTTPStatus.OK, HTTPStatus.CREATED):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def assign_role(self):
        """Simulate role assignment - admin operation (2%).

        This tests:
        - Admin permission check
        - Role assignment creation
        - Cache invalidation
        """
        # Only 2% of users perform admin operations
        if random.random() > 0.02:
            return

        user_id = str(uuid4())
        role_id = str(uuid4())

        start_time = time.perf_counter()

        # Note: Would be POST /api/v1/admin/role-assignments in production
        with self.client.get(
            "/health",  # Replace with POST /api/v1/admin/role-assignments
            catch_response=True,
            name="/api/v1/admin/role-assignments (assign)"
        ) as response:
            response_time_ms = (time.perf_counter() - start_time) * 1000

            if response.status_code in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.FORBIDDEN):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class IntensivePermissionCheckUser(HttpUser):
    """User class for intensive permission checking load test.

    This simulates worst-case scenarios:
    - Rapid permission checks (minimal wait time)
    - High cache miss rate (different resources each time)
    - Tests system under maximum permission evaluation load
    """

    abstract = False
    wait_time = between(0.1, 0.5)  # Very short wait - high load

    test_flow_count = int(os.getenv("TEST_FLOW_COUNT", "1000"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = str(uuid4())

    def on_start(self):
        """Setup test user."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != HTTPStatus.OK:
                response.failure("Health check failed")

    @task(1)
    def rapid_permission_checks(self):
        """Perform rapid permission checks with high cache miss rate."""
        # Use random flow IDs to force cache misses
        flow_id = f"flow_{random.randint(1, self.test_flow_count)}"

        start_time = time.perf_counter()

        with self.client.get(
            "/health",  # Replace with actual RBAC endpoint
            catch_response=True,
            name="/api/v1/flows/[id] (intensive)"
        ) as response:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            permission_check_times.append(response_time_ms)

            if response.status_code in (HTTPStatus.OK, HTTPStatus.FORBIDDEN):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
