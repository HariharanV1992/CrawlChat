#!/bin/bash

# Local Lambda Deployment Script for CrawlChat
# This script deploys both Lambda functions locally using Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LAMBDA_API_PORT=9000
CRAWLER_PORT=9001
LAMBDA_API_CONTAINER="crawlchat-lambda-api-local"
CRAWLER_CONTAINER="crawler-service-local"

# Directories
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRAWLCHAT_DIR="$BASE_DIR/crawlchat-service"
LAMBDA_SERVICE_DIR="$CRAWLCHAT_DIR/lambda-service"
CRAWLER_SERVICE_DIR="$CRAWLCHAT_DIR/crawler-service"

echo -e "${BLUE}🚀 CrawlChat Local Lambda Deployment${NC}"
echo "=================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_status "Docker found"
    
    # Check directories
    if [ ! -d "$LAMBDA_SERVICE_DIR" ]; then
        print_error "Lambda service directory not found: $LAMBDA_SERVICE_DIR"
        exit 1
    fi
    
    if [ ! -d "$CRAWLER_SERVICE_DIR" ]; then
        print_error "Crawler service directory not found: $CRAWLER_SERVICE_DIR"
        exit 1
    fi
    
    print_status "All prerequisites met"
}

# Stop existing containers
stop_containers() {
    echo "🛑 Stopping existing containers..."
    
    # Stop Lambda API container
    if docker ps -q -f name="$LAMBDA_API_CONTAINER" | grep -q .; then
        docker stop "$LAMBDA_API_CONTAINER" >/dev/null 2>&1
        docker rm "$LAMBDA_API_CONTAINER" >/dev/null 2>&1
        print_status "Stopped Lambda API container"
    fi
    
    # Stop Crawler container
    if docker ps -q -f name="$CRAWLER_CONTAINER" | grep -q .; then
        docker stop "$CRAWLER_CONTAINER" >/dev/null 2>&1
        docker rm "$CRAWLER_CONTAINER" >/dev/null 2>&1
        print_status "Stopped Crawler container"
    fi
}

# Build Docker images
build_images() {
    echo "🔨 Building Docker images..."
    
    # Build Lambda API image
    echo "Building Lambda API image..."
    if docker build -t crawlchat-lambda-api:local -f "$LAMBDA_SERVICE_DIR/Dockerfile" "$LAMBDA_SERVICE_DIR"; then
        print_status "Lambda API image built successfully"
    else
        print_error "Failed to build Lambda API image"
        exit 1
    fi
    
    # Build Crawler image
    echo "Building Crawler image..."
    if docker build -t crawler-service:local -f "$CRAWLER_SERVICE_DIR/Dockerfile" "$CRAWLER_SERVICE_DIR"; then
        print_status "Crawler image built successfully"
    else
        print_error "Failed to build Crawler image"
        exit 1
    fi
}

# Run containers
run_containers() {
    echo "🚀 Starting containers..."
    
    # Environment variables
    ENV_VARS=(
        "-e" "AWS_REGION=ap-south-1"
        "-e" "LAMBDA_FUNCTION_NAME=crawlchat-api-function"
        "-e" "CRAWLER_FUNCTION_NAME=crawlchat-crawler-function"
        "-e" "STACK_NAME=crawlchat-stack"
        "-e" "MONGODB_URI=${MONGODB_URI:-}"
        "-e" "DB_NAME=${DB_NAME:-stock_market_crawler}"
        "-e" "SCRAPINGBEE_API_KEY=${SCRAPINGBEE_API_KEY:-}"
        "-e" "CRAWLCHAT_SQS_QUEUE=crawlchat-crawl-tasks"
    )
    
    # Run Lambda API container
    echo "Starting Lambda API container..."
    if docker run -d \
        --name "$LAMBDA_API_CONTAINER" \
        -p "$LAMBDA_API_PORT:8080" \
        "${ENV_VARS[@]}" \
        crawlchat-lambda-api:local; then
        print_status "Lambda API container started"
    else
        print_error "Failed to start Lambda API container"
        exit 1
    fi
    
    # Run Crawler container
    echo "Starting Crawler container..."
    if docker run -d \
        --name "$CRAWLER_CONTAINER" \
        -p "$CRAWLER_PORT:8080" \
        "${ENV_VARS[@]}" \
        crawler-service:local; then
        print_status "Crawler container started"
    else
        print_error "Failed to start Crawler container"
        exit 1
    fi
}

# Wait for containers to be ready
wait_for_containers() {
    echo "⏳ Waiting for containers to be ready..."
    
    local timeout=60
    local count=0
    
    while [ $count -lt $timeout ]; do
        # Check Lambda API
        if curl -s "http://localhost:$LAMBDA_API_PORT/health" >/dev/null 2>&1; then
            print_status "Lambda API container is ready"
            break
        fi
        
        # Check Crawler
        if curl -s "http://localhost:$CRAWLER_PORT/health" >/dev/null 2>&1; then
            print_status "Crawler container is ready"
            break
        fi
        
        sleep 2
        count=$((count + 2))
    done
    
    if [ $count -ge $timeout ]; then
        print_warning "Timeout waiting for containers (some may still be starting)"
    fi
}

# Test functions
test_functions() {
    echo "🧪 Testing functions..."
    
    # Test Lambda API
    echo "Testing Lambda API..."
    if curl -s "http://localhost:$LAMBDA_API_PORT/health" >/dev/null 2>&1; then
        print_status "Lambda API health check passed"
    else
        print_warning "Lambda API health check failed"
    fi
    
    # Test Crawler
    echo "Testing Crawler..."
    if curl -s "http://localhost:$CRAWLER_PORT/health" >/dev/null 2>&1; then
        print_status "Crawler health check passed"
    else
        print_warning "Crawler health check failed"
    fi
}

# Show status
show_status() {
    echo "📊 Container Status:"
    docker ps --filter "name=crawlchat" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "🌐 Service URLs:"
    echo "  Lambda API: http://localhost:$LAMBDA_API_PORT"
    echo "  Crawler: http://localhost:$CRAWLER_PORT"
    echo ""
    echo "📋 Useful commands:"
    echo "  View Lambda API logs: docker logs $LAMBDA_API_CONTAINER"
    echo "  View Crawler logs: docker logs $CRAWLER_CONTAINER"
    echo "  Stop all: docker stop $LAMBDA_API_CONTAINER $CRAWLER_CONTAINER"
    echo "  Clean up: docker rm $LAMBDA_API_CONTAINER $CRAWLER_CONTAINER"
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    
    # Stop and remove containers
    stop_containers
    
    # Remove images
    docker rmi crawlchat-lambda-api:local >/dev/null 2>&1 || true
    docker rmi crawler-service:local >/dev/null 2>&1 || true
    
    print_status "Cleanup completed"
}

# Main deployment function
deploy() {
    check_prerequisites
    stop_containers
    build_images
    run_containers
    wait_for_containers
    test_functions
    show_status
    
    echo ""
    print_status "Local Lambda deployment completed!"
    echo "You can now test the functions at the URLs shown above."
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "cleanup")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "logs")
        if [ -n "$2" ]; then
            docker logs "$2"
        else
            echo "Usage: $0 logs <container_name>"
            echo "Available containers: $LAMBDA_API_CONTAINER, $CRAWLER_CONTAINER"
        fi
        ;;
    *)
        echo "Usage: $0 [deploy|cleanup|status|logs]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy Lambda functions locally (default)"
        echo "  cleanup - Stop and remove containers and images"
        echo "  status  - Show container status"
        echo "  logs    - Show logs for a container"
        ;;
esac 