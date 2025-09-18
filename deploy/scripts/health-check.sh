#!/bin/bash

# LangBuilder with RBAC - Health Check Script
# Comprehensive health check for all system components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
TIMEOUT=${TIMEOUT:-30}
VERBOSE=${VERBOSE:-false}

echo -e "${BLUE}🔍 LangBuilder with RBAC - Health Check${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Utility functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if service is running
check_service_running() {
    local service_name=$1
    local container_name=$2
    
    if [ "$VERBOSE" = "true" ]; then
        log_info "Checking if $service_name is running..."
    fi
    
    if docker-compose -f "$DEPLOY_DIR/docker-compose.yml" ps | grep -q "$container_name.*Up"; then
        log_success "$service_name is running"
        return 0
    else
        log_error "$service_name is not running"
        return 1
    fi
}

# Check HTTP endpoint
check_http_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    if [ "$VERBOSE" = "true" ]; then
        log_info "Checking $name at $url..."
    fi
    
    if curl -f -s --max-time "$TIMEOUT" "$url" > /dev/null; then
        log_success "$name is accessible"
        return 0
    else
        log_error "$name is not accessible at $url"
        return 1
    fi
}

# Check API endpoint with JSON response
check_api_endpoint() {
    local name=$1
    local url=$2
    local auth_header=${3:-""}
    
    if [ "$VERBOSE" = "true" ]; then
        log_info "Checking $name API at $url..."
    fi
    
    local curl_cmd="curl -f -s --max-time $TIMEOUT"
    if [ -n "$auth_header" ]; then
        curl_cmd="$curl_cmd -H \"$auth_header\""
    fi
    
    if eval "$curl_cmd $url" | jq . > /dev/null 2>&1; then
        log_success "$name API is responding with valid JSON"
        return 0
    else
        log_error "$name API is not responding or returning invalid JSON"
        return 1
    fi
}

# Check database connectivity
check_database() {
    log_info "Checking database connectivity..."
    
    cd "$DEPLOY_DIR"
    
    if docker-compose exec -T db pg_isready -U langflow -d langflow > /dev/null 2>&1; then
        log_success "Database is accepting connections"
    else
        log_error "Database is not accepting connections"
        return 1
    fi
    
    # Check if RBAC tables exist
    if [ "$VERBOSE" = "true" ]; then
        log_info "Checking RBAC tables..."
    fi
    
    if docker-compose exec -T db psql -U langflow -d langflow -c "SELECT COUNT(*) FROM workspace;" > /dev/null 2>&1; then
        log_success "RBAC tables are accessible"
    else
        log_error "RBAC tables are not accessible"
        return 1
    fi
    
    return 0
}

# Check Redis connectivity
check_redis() {
    log_info "Checking Redis connectivity..."
    
    cd "$DEPLOY_DIR"
    
    if docker-compose exec -T result_backend redis-cli ping | grep -q "PONG"; then
        log_success "Redis is responding"
        return 0
    else
        log_error "Redis is not responding"
        return 1
    fi
}

# Check RabbitMQ connectivity
check_rabbitmq() {
    log_info "Checking RabbitMQ connectivity..."
    
    cd "$DEPLOY_DIR"
    
    if docker-compose exec -T broker rabbitmqctl status > /dev/null 2>&1; then
        log_success "RabbitMQ is running"
        return 0
    else
        log_error "RabbitMQ is not running properly"
        return 1
    fi
}

# Check RBAC functionality
check_rbac_functionality() {
    log_info "Checking RBAC functionality..."
    
    # Test permission checking endpoint
    if check_api_endpoint "Permission Check" "http://localhost:7860/api/v1/rbac/permissions/resource-types"; then
        log_success "RBAC permission system is functional"
    else
        log_error "RBAC permission system is not functional"
        return 1
    fi
    
    # Test workspace endpoint
    if check_http_endpoint "RBAC Workspaces" "http://localhost:7860/api/v1/rbac/workspaces/"; then
        log_success "RBAC workspace API is accessible"
    else
        log_warning "RBAC workspace API requires authentication"
    fi
    
    return 0
}

# Check frontend RBAC integration
check_frontend_rbac() {
    log_info "Checking frontend RBAC integration..."
    
    # Check if RBAC admin interface loads
    if curl -f -s --max-time "$TIMEOUT" "http://localhost:80/" | grep -q "langflow"; then
        log_success "Frontend is serving content"
        
        # Check if RBAC-specific content is present
        if curl -f -s --max-time "$TIMEOUT" "http://localhost:80/" | grep -q -i "rbac\|permission\|workspace"; then
            log_success "Frontend includes RBAC functionality"
        else
            log_warning "Frontend may not include RBAC functionality"
        fi
    else
        log_error "Frontend is not accessible"
        return 1
    fi
    
    return 0
}

# Performance checks
check_performance() {
    log_info "Running performance checks..."
    
    # Check API response time
    local start_time=$(date +%s%N)
    if curl -f -s --max-time 5 "http://localhost:7860/health" > /dev/null; then
        local end_time=$(date +%s%N)
        local duration=$(((end_time - start_time) / 1000000))  # Convert to milliseconds
        
        if [ "$duration" -lt 1000 ]; then
            log_success "API response time: ${duration}ms (Good)"
        elif [ "$duration" -lt 2000 ]; then
            log_warning "API response time: ${duration}ms (Acceptable)"
        else
            log_warning "API response time: ${duration}ms (Slow)"
        fi
    else
        log_error "Could not measure API response time"
    fi
    
    # Check permission endpoint response time
    start_time=$(date +%s%N)
    if curl -f -s --max-time 5 "http://localhost:7860/api/v1/rbac/permissions/resource-types" > /dev/null; then
        end_time=$(date +%s%N)
        duration=$(((end_time - start_time) / 1000000))
        
        if [ "$duration" -lt 100 ]; then
            log_success "RBAC permission check: ${duration}ms (Excellent)"
        elif [ "$duration" -lt 200 ]; then
            log_success "RBAC permission check: ${duration}ms (Good)"
        else
            log_warning "RBAC permission check: ${duration}ms (Consider optimization)"
        fi
    else
        log_error "Could not measure RBAC permission response time"
    fi
}

# Check system resources
check_system_resources() {
    log_info "Checking system resources..."
    
    cd "$DEPLOY_DIR"
    
    # Check container resource usage
    if command -v docker &> /dev/null; then
        local stats=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(backend|frontend|db|redis|rabbit)")
        
        if [ -n "$stats" ]; then
            echo -e "${BLUE}📊 Container Resource Usage:${NC}"
            echo "$stats"
            log_success "Resource usage information available"
        else
            log_warning "Could not retrieve resource usage information"
        fi
    fi
    
    # Check disk space
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        log_success "Disk usage: ${disk_usage}% (Good)"
    elif [ "$disk_usage" -lt 90 ]; then
        log_warning "Disk usage: ${disk_usage}% (Consider cleanup)"
    else
        log_error "Disk usage: ${disk_usage}% (Critical - cleanup required)"
    fi
}

# Main health check function
run_health_checks() {
    local failed_checks=0
    
    echo -e "${YELLOW}🏥 Service Status Checks${NC}"
    echo "========================="
    
    # Service status checks
    check_service_running "Database" "db" || ((failed_checks++))
    check_service_running "Redis" "result_backend" || ((failed_checks++))
    check_service_running "RabbitMQ" "broker" || ((failed_checks++))
    check_service_running "Backend" "backend" || ((failed_checks++))
    check_service_running "Frontend" "frontend" || ((failed_checks++))
    
    echo ""
    echo -e "${YELLOW}🌐 Connectivity Checks${NC}"
    echo "======================"
    
    # Connectivity checks
    check_database || ((failed_checks++))
    check_redis || ((failed_checks++))
    check_rabbitmq || ((failed_checks++))
    
    echo ""
    echo -e "${YELLOW}🔧 API Endpoint Checks${NC}"
    echo "======================"
    
    # API endpoint checks
    check_http_endpoint "Core API Health" "http://localhost:7860/health" || ((failed_checks++))
    check_api_endpoint "Core API Docs" "http://localhost:7860/docs" || ((failed_checks++))
    check_rbac_functionality || ((failed_checks++))
    
    echo ""
    echo -e "${YELLOW}🖥️  Frontend Checks${NC}"
    echo "==================="
    
    # Frontend checks
    check_http_endpoint "Frontend" "http://localhost:80" || ((failed_checks++))
    check_frontend_rbac || ((failed_checks++))
    
    echo ""
    echo -e "${YELLOW}⚡ Performance Checks${NC}"
    echo "===================="
    
    # Performance checks
    check_performance
    
    echo ""
    echo -e "${YELLOW}📊 System Resource Checks${NC}"
    echo "========================="
    
    # System resource checks
    check_system_resources
    
    return $failed_checks
}

# Generate health report
generate_report() {
    local failed_checks=$1
    
    echo ""
    echo -e "${BLUE}📋 Health Check Summary${NC}"
    echo "======================="
    
    if [ "$failed_checks" -eq 0 ]; then
        echo -e "${GREEN}🎉 All health checks passed!${NC}"
        echo -e "${GREEN}✅ LangBuilder with RBAC is fully operational${NC}"
        echo ""
        echo -e "${BLUE}🌐 Service URLs:${NC}"
        echo -e "   Frontend: http://localhost:80"
        echo -e "   API Docs: http://localhost:7860/docs"
        echo -e "   RBAC Admin: http://localhost:80/admin/rbac"
        echo -e "   PgAdmin: http://localhost:5050"
        echo ""
        return 0
    elif [ "$failed_checks" -le 3 ]; then
        echo -e "${YELLOW}⚠️  Some health checks failed (${failed_checks} failures)${NC}"
        echo -e "${YELLOW}🔧 System may need attention but is partially operational${NC}"
        return 1
    else
        echo -e "${RED}❌ Multiple health checks failed (${failed_checks} failures)${NC}"
        echo -e "${RED}🚨 System requires immediate attention${NC}"
        return 2
    fi
}

# Show help
show_help() {
    echo "LangBuilder with RBAC - Health Check Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -v, --verbose     Enable verbose output"
    echo "  -t, --timeout N   Set timeout for HTTP checks (default: 30s)"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  TIMEOUT=N         Override default timeout"
    echo "  VERBOSE=true      Enable verbose mode"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run standard health checks"
    echo "  $0 --verbose            # Run with detailed output"
    echo "  TIMEOUT=60 $0           # Run with 60s timeout"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Change to deploy directory
cd "$DEPLOY_DIR"

# Run health checks
failed_checks=0
run_health_checks
failed_checks=$?

# Generate report
generate_report $failed_checks
exit_code=$?

exit $exit_code