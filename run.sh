#!/bin/bash

# Meeting Minutes AI - Startup Script
# This script sets up and runs the Meeting Minutes AI application

set -e

echo "🎙️ Meeting Minutes AI - Starting Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration before proceeding."
    print_warning "Especially add your OpenAI API key and other credentials."
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p uploads/audio uploads/exports logs

# Set permissions
chmod 755 uploads logs
chmod 755 uploads/audio uploads/exports

# Check if we're running with sudo and warn about permissions
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. This may cause permission issues with Docker volumes."
fi

# Function to check service health
check_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    print_status "Checking $service_name health..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service_name | grep -q "Up (healthy)"; then
            print_success "$service_name is healthy!"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "$service_name failed to become healthy after $max_attempts attempts"
            return 1
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
}

# Parse command line arguments
COMMAND=${1:-"start"}
ENVIRONMENT=${2:-"production"}

case $COMMAND in
    "start")
        print_status "Starting Meeting Minutes AI..."
        
        # Pull latest images
        print_status "Pulling latest Docker images..."
        docker-compose pull
        
        # Build application
        print_status "Building application..."
        docker-compose build
        
        # Start services
        print_status "Starting services..."
        docker-compose up -d
        
        # Wait for services to be healthy
        sleep 10
        
        # Check service health
        check_service_health postgres
        check_service_health redis
        check_service_health backend
        
        print_success "Meeting Minutes AI is now running!"
        echo ""
        echo "🌐 Access the application:"
        echo "   Web Interface: http://localhost"
        echo "   API Documentation: http://localhost/docs"
        echo "   Health Check: http://localhost/health"
        echo ""
        echo "📊 Monitoring:"
        echo "   View logs: docker-compose logs -f"
        echo "   Check status: docker-compose ps"
        echo ""
        ;;
        
    "stop")
        print_status "Stopping Meeting Minutes AI..."
        docker-compose down
        print_success "Application stopped."
        ;;
        
    "restart")
        print_status "Restarting Meeting Minutes AI..."
        docker-compose down
        docker-compose up -d
        print_success "Application restarted."
        ;;
        
    "logs")
        print_status "Showing application logs..."
        docker-compose logs -f ${2:-""}
        ;;
        
    "status")
        print_status "Application status:"
        docker-compose ps
        ;;
        
    "update")
        print_status "Updating Meeting Minutes AI..."
        docker-compose down
        docker-compose pull
        docker-compose build
        docker-compose up -d
        print_success "Application updated and restarted."
        ;;
        
    "backup")
        print_status "Creating backup..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_dir="backup_${timestamp}"
        mkdir -p $backup_dir
        
        # Backup database
        docker-compose exec postgres pg_dump -U postgres meeting_minutes > $backup_dir/database.sql
        
        # Backup uploads
        cp -r uploads $backup_dir/
        
        # Create archive
        tar -czf $backup_dir.tar.gz $backup_dir
        rm -rf $backup_dir
        
        print_success "Backup created: $backup_dir.tar.gz"
        ;;
        
    "restore")
        if [ -z "$2" ]; then
            print_error "Please provide backup file: ./run.sh restore backup_file.tar.gz"
            exit 1
        fi
        
        print_status "Restoring from backup: $2"
        
        # Extract backup
        tar -xzf $2
        backup_dir=$(basename $2 .tar.gz)
        
        # Stop services
        docker-compose down
        
        # Restore uploads
        rm -rf uploads
        cp -r $backup_dir/uploads .
        
        # Start database
        docker-compose up -d postgres
        sleep 10
        
        # Restore database
        docker-compose exec -T postgres psql -U postgres -d meeting_minutes < $backup_dir/database.sql
        
        # Start all services
        docker-compose up -d
        
        # Cleanup
        rm -rf $backup_dir
        
        print_success "Restore completed."
        ;;
        
    "dev")
        print_status "Starting development environment..."
        export DEBUG=True
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        print_success "Development environment started."
        ;;
        
    "test")
        print_status "Running tests..."
        docker-compose exec backend pytest backend/tests/ -v
        ;;
        
    "shell")
        print_status "Opening backend shell..."
        docker-compose exec backend bash
        ;;
        
    "clean")
        print_status "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        print_success "Cleanup completed."
        ;;
        
    *)
        echo "Meeting Minutes AI - Startup Script"
        echo ""
        echo "Usage: ./run.sh [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  start     Start the application (default)"
        echo "  stop      Stop the application"
        echo "  restart   Restart the application"
        echo "  logs      Show application logs"
        echo "  status    Show service status"
        echo "  update    Update and restart application"
        echo "  backup    Create application backup"
        echo "  restore   Restore from backup file"
        echo "  dev       Start development environment"
        echo "  test      Run tests"
        echo "  shell     Open backend shell"
        echo "  clean     Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  ./run.sh start"
        echo "  ./run.sh logs backend"
        echo "  ./run.sh backup"
        echo "  ./run.sh restore backup_20241201_120000.tar.gz"
        ;;
esac