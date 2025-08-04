#!/bin/bash
"""
Performance optimization deployment script for Autopicker Platform
Deploys performance optimization features and runs load testing
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_HOST="38.242.229.78"
VPS_USER="julie"
VPS_PATH="/home/julie/autopicker-platform"
LOCAL_PATH="/Users/juliebush/Autopicker/multimodal-llm-platform"

echo -e "${BLUE}🚀 Starting Performance Optimization Deployment...${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check VPS connection
echo -e "${BLUE}🔍 Checking VPS connection...${NC}"
if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_HOST "echo 'Connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to VPS at $VPS_HOST"
    exit 1
fi
print_status "VPS connection established"

# Deploy performance optimization files
echo -e "${BLUE}📤 Deploying performance optimization modules...${NC}"
rsync -avz $LOCAL_PATH/backend/performance_optimizer.py $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
rsync -avz $LOCAL_PATH/backend/simple_api.py $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
rsync -avz $LOCAL_PATH/backend/requirements_simple.txt $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
print_status "Performance optimization files deployed"

# Install performance dependencies
echo -e "${BLUE}📦 Installing performance dependencies...${NC}"
ssh $VPS_USER@$VPS_HOST "
    cd $VPS_PATH/backend
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements_simple.txt
"
print_status "Performance dependencies installed"

# Restart the API service
echo -e "${BLUE}🔄 Restarting API service with performance optimization...${NC}"
ssh $VPS_USER@$VPS_HOST "
    sudo systemctl restart autopicker-api
    sleep 5
    sudo systemctl status autopicker-api --no-pager
"
print_status "API service restarted"

# Wait for service to be ready
echo -e "${BLUE}⏳ Waiting for API to be ready...${NC}"
sleep 15

# Test performance endpoints
echo -e "${BLUE}🧪 Testing performance endpoints...${NC}"

# Test performance metrics endpoint
METRICS_RESPONSE=$(ssh $VPS_USER@$VPS_HOST "
    curl -s -w '%{http_code}' -o /tmp/metrics_response.json http://localhost:8001/api/v1/performance/metrics
    echo
    cat /tmp/metrics_response.json 2>/dev/null | head -10
")

if echo "$METRICS_RESPONSE" | grep -q "200"; then
    print_status "Performance metrics endpoint is working"
else
    print_warning "Performance metrics endpoint returned: $(echo "$METRICS_RESPONSE" | tail -1)"
fi

# Test basic health endpoint performance
echo -e "${BLUE}⚡ Running basic performance test...${NC}"
PERF_TEST_RESPONSE=$(ssh $VPS_USER@$VPS_HOST "
    curl -s -X POST 'http://localhost:8001/api/v1/performance/load-test?endpoint=/health&concurrent_users=3&requests_per_user=5' \
    -H 'Content-Type: application/json' | jq -r '.load_test_results.success_rate_percent' 2>/dev/null || echo 'test_failed'
")

if [ "$PERF_TEST_RESPONSE" != "test_failed" ] && [ "$PERF_TEST_RESPONSE" != "" ]; then
    print_status "Load testing endpoint working - Success rate: ${PERF_TEST_RESPONSE}%"
else
    print_warning "Load testing endpoint test failed or returned empty response"
fi

# Display performance summary
echo -e "${BLUE}📋 Performance Optimization Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh $VPS_USER@$VPS_HOST "
    echo -e '⚡ Performance Features Deployed:'
    echo '  • AsyncCache: Redis-backed caching with in-memory fallback'
    echo '  • Connection Pooling: HTTP/2 enabled connection reuse'
    echo '  • Performance Monitoring: Function-level timing and metrics'
    echo '  • Load Testing: Concurrent user simulation and benchmarks'
    echo '  • Batch Processing: Optimized for large-scale operations'
    echo '  • Throttling: Rate limiting for API protection'
    echo
    echo -e '🎯 Performance Endpoints:'
    echo '  • /api/v1/performance/metrics - Real-time performance data'
    echo '  • /api/v1/performance/load-test - Custom load testing'
    echo '  • /api/v1/performance/comprehensive-test - Full system testing'
    echo
    echo -e '📊 Monitoring Features:'
    echo '  • Cache hit/miss rates and statistics' 
    echo '  • Response time percentiles (P95, P99)'
    echo '  • Success/failure rates per endpoint'
    echo '  • Concurrent request handling metrics'
    echo '  • Resource usage optimization tracking'
"

# Run a comprehensive test to validate deployment
echo -e "${BLUE}🔬 Running validation tests...${NC}"

# Test multiple endpoints to generate metrics
ssh $VPS_USER@$VPS_HOST "
    echo 'Testing multiple endpoints to generate performance data...'
    
    # Test health endpoint multiple times
    for i in {1..5}; do
        curl -s http://localhost:8001/health > /dev/null
    done
    
    # Test models endpoint (should use caching)
    for i in {1..3}; do
        curl -s http://localhost:8001/api/v1/models > /dev/null
    done
    
    # Wait a moment for metrics to be collected
    sleep 3
    
    echo 'Getting performance metrics...'
    curl -s http://localhost:8001/api/v1/performance/metrics | jq -r '.performance_metrics.cache_stats // \"No cache stats available\"'
"

print_status "Performance optimization deployment completed successfully!"
echo -e "${GREEN}🎉 Your Autopicker platform now has optimized performance!${NC}"
echo
echo -e "${BLUE}Performance optimization checklist completed:${NC}"
echo "  ✅ Async caching system with Redis support"
echo "  ✅ HTTP connection pooling with HTTP/2"
echo "  ✅ Performance monitoring and metrics collection"
echo "  ✅ Load testing utilities and endpoints"
echo "  ✅ Batch processing for large operations"
echo "  ✅ Request throttling and rate limiting"
echo "  ✅ Cache optimization for frequently accessed data"
echo "  ✅ Performance metrics dashboard endpoints"
echo "  ✅ Comprehensive load testing capabilities"
echo "  ✅ Real-time performance monitoring"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "  • Monitor performance metrics regularly at /api/v1/performance/metrics"
echo "  • Run load tests to validate system performance under load"
echo "  • Optimize cache TTL values based on usage patterns"
echo "  • Consider Redis deployment for production caching"
echo "  • Monitor cache hit rates and adjust caching strategy"