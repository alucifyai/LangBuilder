#!/usr/bin/env python3
"""Comprehensive security coverage audit for RBAC API endpoints."""

import os
import re
from pathlib import Path

def audit_security_coverage():
    """Perform comprehensive security coverage audit."""
    print("🔒 COMPREHENSIVE RBAC API SECURITY COVERAGE AUDIT")
    print("=" * 60)

    rbac_path = Path("src/backend/base/langflow/api/v1/rbac")

    # Files that should contain API endpoints
    endpoint_files = [
        "audit.py",
        "environments.py",
        "iac.py",
        "permissions.py",
        "projects.py",
        "role_assignments.py",
        "roles.py",
        "service_accounts.py",
        "user_groups.py",
        "workspaces.py"
    ]

    total_endpoints = 0
    total_secured = 0
    detailed_results = []

    print("\n📊 FILE-BY-FILE SECURITY ANALYSIS:")
    print("-" * 60)

    for filename in endpoint_files:
        filepath = rbac_path / filename

        if not filepath.exists():
            print(f"❌ {filename}: FILE NOT FOUND")
            continue

        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Count @router endpoints
            router_matches = re.findall(r'@router\.\w+', content)
            endpoint_count = len(router_matches)

            # Count @secure_endpoint decorators
            secure_matches = re.findall(r'@secure_endpoint', content)
            secure_count = len(secure_matches)

            total_endpoints += endpoint_count
            total_secured += secure_count

            # Determine status
            if endpoint_count == 0:
                status = "ℹ️ NO ENDPOINTS"
                coverage_pct = "N/A"
            elif secure_count == endpoint_count:
                status = "✅ FULLY SECURED"
                coverage_pct = "100%"
            elif secure_count > 0:
                status = "⚠️ PARTIALLY SECURED"
                coverage_pct = f"{(secure_count/endpoint_count)*100:.1f}%"
            else:
                status = "❌ NOT SECURED"
                coverage_pct = "0%"

            detailed_results.append({
                'file': filename,
                'endpoints': endpoint_count,
                'secured': secure_count,
                'status': status,
                'coverage': coverage_pct
            })

            print(f"{filename:20} | {secure_count:2d}/{endpoint_count:2d} secured | {coverage_pct:>6} | {status}")

        except Exception as e:
            print(f"❌ {filename}: ERROR - {e}")

    # Calculate overall coverage
    if total_endpoints > 0:
        overall_coverage = (total_secured / total_endpoints) * 100
    else:
        overall_coverage = 0

    print("\n" + "=" * 60)
    print("📈 OVERALL SECURITY COVERAGE SUMMARY:")
    print("=" * 60)
    print(f"Total API Endpoint Files Analyzed: {len(endpoint_files)}")
    print(f"Total @router Endpoints Found:     {total_endpoints}")
    print(f"Total @secure_endpoint Applied:    {total_secured}")
    print(f"Overall Security Coverage:         {overall_coverage:.1f}%")

    if overall_coverage == 100.0:
        print("🎯 SECURITY STATUS: ✅ 100% COVERAGE ACHIEVED!")
    elif overall_coverage >= 90.0:
        print("🎯 SECURITY STATUS: ✅ EXCELLENT (≥90%)")
    elif overall_coverage >= 70.0:
        print("🎯 SECURITY STATUS: ⚠️ GOOD (≥70%)")
    else:
        print("🎯 SECURITY STATUS: ❌ NEEDS IMPROVEMENT (<70%)")

    # Check for any endpoints without security
    print("\n🔍 DETAILED ENDPOINT VERIFICATION:")
    print("-" * 60)

    unsecured_count = 0
    for result in detailed_results:
        if result['endpoints'] > 0 and result['secured'] < result['endpoints']:
            missing = result['endpoints'] - result['secured']
            print(f"⚠️ {result['file']}: {missing} endpoint(s) missing security")
            unsecured_count += missing

    if unsecured_count == 0:
        print("✅ ALL ENDPOINTS HAVE SECURITY DECORATORS!")
    else:
        print(f"❌ {unsecured_count} endpoint(s) still need security decorators")

    # Verify security patterns
    print("\n🔧 SECURITY PATTERN VERIFICATION:")
    print("-" * 60)

    security_patterns = {
        "Security Middleware": "@secure_endpoint",
        "Enhanced Authentication": "get_authenticated_user",
        "Runtime Enforcement": "RuntimeEnforcementContext",
        "Request Parameter": "request: Request",
        "Security Requirements": "SecurityRequirement",
        "Validation Requirements": "ValidationRequirement"
    }

    pattern_results = {}
    for filename in endpoint_files:
        filepath = rbac_path / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                content = f.read()

            file_patterns = {}
            for pattern_name, pattern in security_patterns.items():
                file_patterns[pattern_name] = pattern in content
            pattern_results[filename] = file_patterns

    # Check pattern adoption
    for pattern_name in security_patterns.keys():
        files_with_pattern = sum(1 for file_patterns in pattern_results.values()
                               if file_patterns.get(pattern_name, False))
        total_files = len([f for f in endpoint_files if (rbac_path / f).exists()])
        pattern_coverage = (files_with_pattern / total_files) * 100 if total_files > 0 else 0

        if pattern_coverage >= 80:
            status = "✅"
        elif pattern_coverage >= 60:
            status = "⚠️"
        else:
            status = "❌"

        print(f"{status} {pattern_name:<25}: {files_with_pattern:2d}/{total_files:2d} files ({pattern_coverage:5.1f}%)")

    print("\n" + "=" * 60)

    return overall_coverage == 100.0, {
        'total_endpoints': total_endpoints,
        'total_secured': total_secured,
        'overall_coverage': overall_coverage,
        'files_analyzed': len(endpoint_files),
        'detailed_results': detailed_results
    }

if __name__ == "__main__":
    success, results = audit_security_coverage()
    exit(0 if success else 1)
