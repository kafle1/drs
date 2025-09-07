#!/bin/bash

# DRS Docker Helper Script
# This script provides convenient commands for managing the DRS Docker environment

set -e

PROJECT_NAME="drs"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install docker-compose and try again."
        exit 1
    fi
}

# Function to show usage
usage() {
    echo "DRS Docker Helper Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start          Start all services"
    echo "  stop           Stop all services"
    echo "  restart        Restart all services"
    echo "  build          Build all services"
    echo "  rebuild        Rebuild all services (no cache)"
    echo "  logs           Show logs from all services"
    echo "  logs-backend   Show backend logs"
    echo "  logs-frontend  Show frontend logs"
    echo "  logs-db        Show database logs"
    echo "  status         Show status of all services"
    echo "  clean          Stop and remove all containers, volumes, and images"
    echo "  db-shell       Open PostgreSQL shell"
    echo "  backend-shell  Open backend container shell"
    echo "  frontend-shell Open frontend container shell"
    echo "  test-backend   Run backend tests"
    echo "  test-frontend  Run frontend tests"
    echo "  backup-db      Backup database"
    echo "  restore-db     Restore database from backup"
    echo "  prod           Start production services"
    echo "  dev            Start development services"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs-backend"
    echo "  $0 prod"
}

# Function to start services
start_services() {
    print_info "Starting DRS services..."
    docker-compose -f $COMPOSE_FILE up -d
    print_success "Services started successfully!"
    print_info "Frontend: http://localhost:3000"
    print_info "Backend API: http://localhost:8000"
    print_info "API Docs: http://localhost:8000/docs"
}

# Function to stop services
stop_services() {
    print_info "Stopping DRS services..."
    docker-compose -f $COMPOSE_FILE down
    print_success "Services stopped successfully!"
}

# Function to restart services
restart_services() {
    print_info "Restarting DRS services..."
    docker-compose -f $COMPOSE_FILE restart
    print_success "Services restarted successfully!"
}

# Function to build services
build_services() {
    print_info "Building DRS services..."
    docker-compose -f $COMPOSE_FILE build
    print_success "Services built successfully!"
}

# Function to rebuild services
rebuild_services() {
    print_info "Rebuilding DRS services (no cache)..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    print_success "Services rebuilt successfully!"
}

# Function to show logs
show_logs() {
    service=$1
    if [ -n "$service" ]; then
        print_info "Showing logs for $service..."
        docker-compose -f $COMPOSE_FILE logs -f $service
    else
        print_info "Showing logs for all services..."
        docker-compose -f $COMPOSE_FILE logs -f
    fi
}

# Function to show status
show_status() {
    print_info "DRS Services Status:"
    docker-compose -f $COMPOSE_FILE ps
}

# Function to clean up
cleanup() {
    print_warning "This will stop and remove all containers, volumes, and images."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose -f $COMPOSE_FILE down -v --rmi all
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled."
    fi
}

# Function to open database shell
db_shell() {
    print_info "Opening PostgreSQL shell..."
    docker-compose -f $COMPOSE_FILE exec db psql -U drs_user -d drs_db
}

# Function to open backend shell
backend_shell() {
    print_info "Opening backend container shell..."
    docker-compose -f $COMPOSE_FILE exec backend sh
}

# Function to open frontend shell
frontend_shell() {
    print_info "Opening frontend container shell..."
    docker-compose -f $COMPOSE_FILE exec frontend sh
}

# Function to run backend tests
test_backend() {
    print_info "Running backend tests..."
    docker-compose -f $COMPOSE_FILE exec backend pytest
}

# Function to run frontend tests
test_frontend() {
    print_info "Running frontend tests..."
    docker-compose -f $COMPOSE_FILE exec frontend npm test
}

# Function to backup database
backup_db() {
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="backup_${timestamp}.sql"
    print_info "Creating database backup: $backup_file"
    docker-compose -f $COMPOSE_FILE exec db pg_dump -U drs_user drs_db > $backup_file
    print_success "Database backup created: $backup_file"
}

# Function to restore database
restore_db() {
    echo "Available backup files:"
    ls -la backup_*.sql 2>/dev/null || echo "No backup files found"
    read -p "Enter backup file name: " backup_file
    if [ -f "$backup_file" ]; then
        print_info "Restoring database from $backup_file"
        docker-compose -f $COMPOSE_FILE exec -T db psql -U drs_user -d drs_db < $backup_file
        print_success "Database restored successfully!"
    else
        print_error "Backup file not found: $backup_file"
    fi
}

# Function to start production services
start_production() {
    print_info "Starting production services..."
    docker-compose -f $COMPOSE_FILE --profile production up -d
    print_success "Production services started!"
    print_info "Application: http://localhost"
    print_info "API: http://localhost/api"
}

# Function to start development services
start_development() {
    print_info "Starting development services..."
    docker-compose -f $COMPOSE_FILE up -d
    print_success "Development services started!"
    print_info "Frontend: http://localhost:3000"
    print_info "Backend: http://localhost:8000"
}

# Main script logic
check_docker
check_compose

case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    build)
        build_services
        ;;
    rebuild)
        rebuild_services
        ;;
    logs)
        show_logs
        ;;
    logs-backend)
        show_logs backend
        ;;
    logs-frontend)
        show_logs frontend
        ;;
    logs-db)
        show_logs db
        ;;
    status)
        show_status
        ;;
    clean)
        cleanup
        ;;
    db-shell)
        db_shell
        ;;
    backend-shell)
        backend_shell
        ;;
    frontend-shell)
        frontend_shell
        ;;
    test-backend)
        test_backend
        ;;
    test-frontend)
        test_frontend
        ;;
    backup-db)
        backup_db
        ;;
    restore-db)
        restore_db
        ;;
    prod)
        start_production
        ;;
    dev)
        start_development
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
