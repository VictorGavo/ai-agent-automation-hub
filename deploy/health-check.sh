#!/bin/bash

# Health check script for Docker containers
# This script can be used to monitor the health of the automation hub services

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
TIMEOUT="${TIMEOUT:-10}"

log() {
    echo -e "${1}[$(date +'%Y-%m-%d %H:%M:%S')] $2${NC}"
}

check_service_health() {
    local service=$1
    local url=$2
    local expected_status=${3:-200}
    
    if curl -sf --max-time "$TIMEOUT" "$url" >/dev/null 2>&1; then
        log "$GREEN" "✅ $service: Health check passed"
        return 0
    else
        log "$RED" "❌ $service: Health check failed"
        return 1
    fi
}

check_container_status() {
    local service=$1
    local container_name=$2
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        log "$GREEN" "✅ $service: Container running"
        return 0
    else
        log "$RED" "❌ $service: Container not running"
        return 1
    fi
}

check_postgres_connection() {
    local container_name="automation_hub_postgres"
    
    if docker exec "$container_name" pg_isready -U automation -d automation_hub >/dev/null 2>&1; then
        log "$GREEN" "✅ PostgreSQL: Database accessible"
        return 0
    else
        log "$RED" "❌ PostgreSQL: Database not accessible"
        return 1
    fi
}

main() {
    log "$YELLOW" "🏥 Running AI Agent Automation Hub Health Check"
    echo "================================================"
    
    local all_healthy=true
    
    # Check container status
    echo "🐳 Container Status:"
    check_container_status "PostgreSQL" "automation_hub_postgres" || all_healthy=false
    check_container_status "Discord Bot" "automation_hub_discord_bot" || all_healthy=false
    
    echo
    
    # Check database connectivity
    echo "🗄️  Database Connectivity:"
    check_postgres_connection || all_healthy=false
    
    echo
    
    # Check service health endpoints
    echo "🌐 Service Health Endpoints:"
    check_service_health "Discord Bot" "http://localhost:8080/health" || all_healthy=false
    
    # Optional services (only check if running)
    if docker ps --format "table {{.Names}}" | grep -q "automation_hub_orchestrator"; then
        check_service_health "Orchestrator" "http://localhost:8081/health" || all_healthy=false
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "automation_hub_backend_agent"; then
        check_service_health "Backend Agent" "http://localhost:8082/health" || all_healthy=false
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "automation_hub_testing_agent"; then
        check_service_health "Testing Agent" "http://localhost:8083/health" || all_healthy=false
    fi
    
    echo
    echo "================================================"
    
    if $all_healthy; then
        log "$GREEN" "🎉 All services are healthy!"
        exit 0
    else
        log "$RED" "⚠️  Some services are not healthy"
        
        echo
        echo "Troubleshooting commands:"
        echo "- Check logs: docker-compose logs -f"
        echo "- Check container status: docker-compose ps"
        echo "- Restart services: docker-compose restart"
        echo "- Check systemd service: sudo systemctl status automation-hub"
        
        exit 1
    fi
}

# Show usage if help requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [options]"
    echo
    echo "Environment variables:"
    echo "  COMPOSE_FILE    Docker compose file to use (default: docker-compose.yml)"
    echo "  TIMEOUT         Timeout for health checks in seconds (default: 10)"
    echo
    echo "Examples:"
    echo "  $0                    # Run health check with defaults"
    echo "  TIMEOUT=30 $0         # Run with 30 second timeout"
    echo "  $0 --help             # Show this help"
    exit 0
fi

main "$@"