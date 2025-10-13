# RBAC Load Testing with Locust

This directory contains Locust load tests for validating RBAC performance under concurrent load as specified in Task 2.3 of the RBAC Implementation Plan.

## Overview

The load tests validate that RBAC permission evaluation maintains acceptable latency under realistic concurrent user load:

- **Target Load**: 1000 concurrent users
- **Performance Requirement**: P95 latency ≤100ms for permission checks
- **Error Rate Requirement**: <1% error rate under load

## Files

- `locust_rbac_performance.py` - Main Locust test file with user behaviors
- `run_locust_load_test.sh` - Helper script to run load tests
- `LOCUST_LOAD_TEST_README.md` - This documentation

## User Behaviors

The load test simulates two types of users:

### 1. RBACLoadTestUser (Realistic Mixed Operations)

Simulates typical user behavior with realistic operation mix:

- **70%**: Permission checks (read operations on flows)
- **20%**: List operations with permission filtering
- **8%**: Resource creation with permission checks
- **2%**: Admin operations (role assignments)

Wait time: 1-3 seconds between requests

### 2. IntensivePermissionCheckUser (Stress Testing)

Simulates worst-case high-frequency permission checking:

- **100%**: Rapid permission checks
- High cache miss rate (different resources each time)
- Minimal wait time (0.1-0.5 seconds)

## Running Load Tests

### Quick Start

```bash
# 1. Start the backend
cd /Users/dongmingjiang/AppGraph/LangBuilder
make backend

# 2. Run load test (in another terminal)
cd src/backend/tests/unit/services/rbac
./run_locust_load_test.sh
```

### Custom Configuration

```bash
# Run with custom parameters
./run_locust_load_test.sh [users] [spawn_rate] [run_time] [host]

# Examples:
./run_locust_load_test.sh 1000 100 5m    # 1000 users, 5 min test
./run_locust_load_test.sh 100 10 30s     # Quick test: 100 users, 30 sec
./run_locust_load_test.sh 5000 200 10m   # Stress test: 5000 users, 10 min
```

### Manual Locust Invocation

```bash
cd src/backend/tests/unit/services/rbac

# Run with UI (for interactive testing)
uv run locust -f locust_rbac_performance.py --host http://localhost:7860

# Run headless (for CI/CD)
uv run locust \
    -f locust_rbac_performance.py \
    --host http://localhost:7860 \
    --users 1000 \
    --spawn-rate 100 \
    --run-time 5m \
    --headless \
    --html locust_rbac_report.html
```

## Interpreting Results

### Performance Metrics

The test tracks and reports:

```
RBAC PERMISSION CHECK PERFORMANCE UNDER LOAD
============================================================
Total Checks: 50000
Mean Latency: 15.23ms
P50 Latency: 12.45ms
P95 Latency: 45.67ms
P99 Latency: 89.12ms
Max Latency: 120.34ms
============================================================
✅ PASS: P95 latency 45.67ms meets 100ms requirement
✅ PASS: Error rate 0.23% is under 1%
============================================================
```

### Success Criteria

The test **passes** if:

1. **P95 Latency** ≤100ms for permission checks
2. **Error Rate** <1%
3. **Exit Code** 0

The test **fails** if:

1. P95 latency exceeds 100ms
2. Error rate exceeds 1%
3. Backend is not accessible

### Generated Reports

After running, check these files:

- `locust_rbac_report.html` - Detailed HTML report with charts
- `locust_rbac_stats_stats.csv` - Per-endpoint statistics
- `locust_rbac_stats_stats_history.csv` - Time-series data
- `locust_rbac_stats_failures.csv` - Failure details

## Integration with CI/CD

### Example CI Pipeline

```yaml
# .github/workflows/performance-tests.yml
- name: Run RBAC Load Tests
  run: |
    make backend &
    BACKEND_PID=$!
    sleep 10  # Wait for backend to start

    cd src/backend/tests/unit/services/rbac
    ./run_locust_load_test.sh 1000 100 3m

    kill $BACKEND_PID
```

### Exit Codes

- `0`: All tests passed
- `1`: P95 latency exceeded OR error rate exceeded

## Troubleshooting

### Backend Not Accessible

```
✗ Backend is not accessible at http://localhost:7860
```

**Solution**: Start the backend first:
```bash
make backend
```

### Connection Errors

If seeing high connection errors:

1. Check backend logs for errors
2. Verify database is accessible
3. Reduce user count or spawn rate
4. Increase wait time between requests

### High Latency

If P95 latency is high:

1. Check database query performance (use cProfile)
2. Verify cache is enabled and working
3. Check database indexes are created
4. Monitor database connection pool
5. Check for N+1 query problems

### Low Cache Hit Rate

If cache isn't helping performance:

1. Verify cache TTL is appropriate (300s default)
2. Check cache size isn't too small (10000 default)
3. Verify cache invalidation isn't too aggressive
4. Monitor cache statistics during test

## Environment Variables

Configure test behavior:

- `TEST_USER_COUNT`: Number of test users to simulate (default: 100)
- `TEST_FLOW_COUNT`: Number of test flows to simulate (default: 100)

```bash
TEST_USER_COUNT=500 TEST_FLOW_COUNT=1000 ./run_locust_load_test.sh
```

## Implementation Status

### Current Status (Task 2.3)

The Locust load test file is **implemented** but uses placeholder endpoints (`/health`) because RBAC-protected API endpoints are not yet deployed in production.

**When RBAC APIs are deployed**, update these lines in `locust_rbac_performance.py`:

```python
# Replace placeholder endpoints with real RBAC-protected endpoints:

# Line ~110: Permission check
self.client.get(
    f"/api/v1/flows/{flow_id}",  # ← Update this
    catch_response=True,
    name="/api/v1/flows/[id] (permission check)"
)

# Line ~130: List flows
self.client.get(
    "/api/v1/flows",  # ← Update this
    catch_response=True,
    name="/api/v1/flows (list with filtering)"
)

# Line ~150: Create flow
self.client.post(
    "/api/v1/flows",  # ← Update this
    json={"name": flow_name, "data": {}},
    catch_response=True,
    name="/api/v1/flows (create with permission)"
)

# Line ~170: Assign role
self.client.post(
    "/api/v1/admin/role-assignments",  # ← Update this
    json={"user_id": user_id, "role_id": role_id},
    catch_response=True,
    name="/api/v1/admin/role-assignments (assign)"
)
```

### Future Enhancements

When implementing Phase 3 (API Integration):

1. Replace `/health` placeholders with actual RBAC endpoints
2. Add authentication header handling
3. Add realistic request payloads
4. Test with pre-seeded test data
5. Add more user behavior patterns (e.g., workspace switching)

## Related Documentation

- **Implementation Plan**: `docs/implementation-plans/RBAC_IMPLEMENTATION_PLAN_V3_FINAL.md` (Task 2.3)
- **Audit Report**: `docs/code-generations/TASK_2.3_AUDIT_REPORT.md`
- **Performance Tests**: `test_performance_validation.py` (unit-level benchmarks)
- **Make Commands**: See `Makefile` for `make locust` target

## References

- Locust Documentation: https://docs.locust.io/
- Performance Requirements: Task 2.3 Success Criterion 4 (1000 concurrent users)
- RBAC Implementation Plan: Section 4.2.3 (Performance Testing)
