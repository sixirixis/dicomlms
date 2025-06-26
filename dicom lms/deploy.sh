#!/bin/bash
set -e

# Medical LMS Deployment Script
echo "🏥 Medical LMS - Integrated DICOM & Pathology Learning Management System"
echo "=================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_prerequisites() {
    print_status "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_status "✅ Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating data directories..."

    mkdir -p data/{postgres,moodledata,moodle,orthanc,pathology,redis}
    mkdir -p logs/nginx
    mkdir -p configs/ssl

    # Set proper permissions
    chmod 755 data/postgres
    chmod 777 data/moodledata
    chmod 755 data/orthanc
    chmod 755 data/pathology
    chmod 755 data/redis

    print_status "✅ Directories created"
}

# Generate SSL certificates for HIPAA compliance
generate_ssl_certificates() {
    print_status "Generating SSL certificates..."

    if [ ! -f "configs/ssl/privkey.pem" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout configs/ssl/privkey.pem \
            -out configs/ssl/fullchain.pem \
            -subj "/C=US/ST=State/L=City/O=Medical LMS/OU=IT Department/CN=medicallms.local"

        print_status "✅ SSL certificates generated"
    else
        print_status "✅ SSL certificates already exist"
    fi
}

# Create environment file if it doesn't exist
setup_environment() {
    print_status "Setting up environment variables..."

    if [ ! -f ".env" ]; then
        cp .env.template .env

        # Generate random passwords
        POSTGRES_PASS=$(openssl rand -base64 32)
        MOODLE_PASS=$(openssl rand -base64 16)
        ORTHANC_PASS=$(openssl rand -base64 16)
        REDIS_PASS=$(openssl rand -base64 16)
        ENCRYPTION_KEY=$(openssl rand -base64 32 | head -c 32)

        # Update .env file
        sed -i "s/your_secure_database_password_here/$POSTGRES_PASS/g" .env
        sed -i "s/your_secure_admin_password_here/$MOODLE_PASS/g" .env
        sed -i "s/your_secure_orthanc_password_here/$ORTHANC_PASS/g" .env
        sed -i "s/your_secure_redis_password_here/$REDIS_PASS/g" .env
        sed -i "s/your_32_character_encryption_key_here/$ENCRYPTION_KEY/g" .env

        print_warning "Environment file created with random passwords."
        print_warning "Please review and update .env file with your specific settings."
        print_warning "Moodle admin password: $MOODLE_PASS"
    else
        print_status "✅ Environment file already exists"
    fi
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."

    docker-compose build --no-cache

    print_status "✅ Docker images built successfully"
}

# Start services
start_services() {
    print_status "Starting Medical LMS services..."

    # Start database first
    docker-compose up -d moodle-db
    print_status "⏳ Waiting for database to be ready..."
    sleep 30

    # Start Orthanc
    docker-compose up -d orthanc-server
    print_status "⏳ Waiting for Orthanc server..."
    sleep 20

    # Start remaining services
    docker-compose up -d

    print_status "✅ All services started"
}

# Check service health
check_health() {
    print_status "Checking service health..."

    # Wait for services to be fully ready
    sleep 60

    services=("moodle-app" "orthanc-server" "ohif-viewer" "pathology-viewer" "unified-viewer")

    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            print_status "✅ $service is running"
        else
            print_error "❌ $service is not running"
        fi
    done
}

# Display access information
show_access_info() {
    echo ""
    echo -e "${BLUE}🏥 Medical LMS Deployment Complete!${NC}"
    echo "=================================================================="
    echo ""
    echo -e "${GREEN}Access URLs:${NC}"
    echo "• Moodle LMS:           https://localhost/"
    echo "• Orthanc DICOM Server: http://localhost:8042/"
    echo "• OHIF Viewer:          http://localhost:3000/"
    echo "• Pathology Viewer:     http://localhost:8080/"
    echo "• Unified Viewer:       http://localhost:3001/"
    echo ""
    echo -e "${GREEN}Default Credentials:${NC}"
    echo "• Moodle Admin:         admin / (check .env file)"
    echo "• Orthanc:              moodle / (check .env file)"
    echo ""
    echo -e "${YELLOW}Important Notes:${NC}"
    echo "• Add 'medicallms.local' to your /etc/hosts file pointing to 127.0.0.1"
    echo "• Install the Medical Imaging plugin in Moodle admin interface"
    echo "• Configure Orthanc connection in Moodle site administration"
    echo "• For production: update SSL certificates and passwords"
    echo "• Enable GPU acceleration for better performance"
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo "1. Visit https://localhost/ to complete Moodle setup"
    echo "2. Install the Medical Imaging activity plugin"
    echo "3. Upload DICOM studies to Orthanc"
    echo "4. Create medical imaging activities in courses"
    echo ""
}

# Main deployment process
main() {
    check_prerequisites
    create_directories
    generate_ssl_certificates
    setup_environment
    build_images
    start_services
    check_health
    show_access_info
}

# Parse command line arguments
case "$1" in
    "start")
        print_status "Starting Medical LMS services..."
        docker-compose up -d
        ;;
    "stop")
        print_status "Stopping Medical LMS services..."
        docker-compose down
        ;;
    "restart")
        print_status "Restarting Medical LMS services..."
        docker-compose restart
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "update")
        print_status "Updating Medical LMS..."
        docker-compose pull
        docker-compose up -d
        ;;
    "backup")
        print_status "Creating backup..."
        ./scripts/backup.sh
        ;;
    "restore")
        if [ -z "$2" ]; then
            print_error "Usage: $0 restore <backup_file>"
            exit 1
        fi
        print_status "Restoring from backup: $2"
        ./scripts/restore.sh "$2"
        ;;
    *)
        print_status "Deploying Medical LMS for the first time..."
        main
        ;;
esac
