#!/bin/bash
# Run Locust load test for RBAC performance validation
#
# Usage:
#   ./run_locust_load_test.sh [users] [spawn_rate] [run_time]
#
# Examples:
#   ./run_locust_load_test.sh 1000 100 5m  # 1000 users, 100/sec spawn, 5 min
#   ./run_locust_load_test.sh 100 10 30s   # Quick test: 100 users, 30 sec

set -e

# Configuration
USERS=${1:-1000}
SPAWN_RATE=${2:-100}
RUN_TIME=${3:-5m}
HOST=${4:-http://localhost:7860}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCUST_FILE="$SCRIPT_DIR/locust_rbac_performance.py"
REPORT_FILE="$SCRIPT_DIR/locust_rbac_report.html"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "RBAC Load Test Configuration"
echo "========================================="
echo "Users:       $USERS"
echo "Spawn Rate:  $SPAWN_RATE users/sec"
echo "Run Time:    $RUN_TIME"
echo "Host:        $HOST"
echo "Report:      $REPORT_FILE"
echo "========================================="
echo ""

# Check if backend is running
echo "Checking if backend is accessible..."
if curl -s -f "$HOST/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is running at $HOST"
else
    echo -e "${RED}✗${NC} Backend is not accessible at $HOST"
    echo ""
    echo "Please start the backend first:"
    echo "  cd /Users/dongmingjiang/AppGraph/LangBuilder"
    echo "  make backend"
    exit 1
fi

# Check if locust file exists
if [ ! -f "$LOCUST_FILE" ]; then
    echo -e "${RED}✗${NC} Locust file not found: $LOCUST_FILE"
    exit 1
fi

echo ""
echo "Starting Locust load test..."
echo ""

# Run Locust
cd "$SCRIPT_DIR"
uv run locust \
    -f "$(basename "$LOCUST_FILE")" \
    --host "$HOST" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --headless \
    --html "$REPORT_FILE" \
    --csv "$SCRIPT_DIR/locust_rbac_stats"

EXIT_CODE=$?

echo ""
echo "========================================="
echo "Load Test Complete"
echo "========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Load test passed"
else
    echo -e "${RED}✗${NC} Load test failed with exit code $EXIT_CODE"
fi

echo ""
echo "Report generated: $REPORT_FILE"
echo "CSV stats: $SCRIPT_DIR/locust_rbac_stats_*.csv"
echo ""

exit $EXIT_CODE
