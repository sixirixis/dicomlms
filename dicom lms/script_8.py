# Create deployment scripts and documentation

# Create deployment script
deploy_script = """#!/bin/bash
set -e

# Medical LMS Deployment Script
echo "🏥 Medical LMS - Integrated DICOM & Pathology Learning Management System"
echo "=================================================================="

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

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
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
            -keyout configs/ssl/privkey.pem \\
            -out configs/ssl/fullchain.pem \\
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
"""

# Create backup script
backup_script = """#!/bin/bash
set -e

# Medical LMS Backup Script
echo "🔄 Creating Medical LMS Backup..."

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups/backup_$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

# Backup databases
echo "📦 Backing up PostgreSQL database..."
docker-compose exec -T moodle-db pg_dump -U moodleuser moodle > "$BACKUP_DIR/moodle_db.sql"

# Backup Orthanc data
echo "📦 Backing up Orthanc DICOM data..."
tar -czf "$BACKUP_DIR/orthanc_data.tar.gz" -C data orthanc/

# Backup Moodle data
echo "📦 Backing up Moodle data files..."
tar -czf "$BACKUP_DIR/moodle_data.tar.gz" -C data moodledata/

# Backup pathology slides
echo "📦 Backing up pathology slides..."
tar -czf "$BACKUP_DIR/pathology_data.tar.gz" -C data pathology/

# Backup configuration
echo "📦 Backing up configuration..."
cp -r configs "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/" 2>/dev/null || true

# Create backup manifest
cat > "$BACKUP_DIR/manifest.txt" << EOF
Medical LMS Backup
Timestamp: $TIMESTAMP
Components:
- PostgreSQL database (moodle_db.sql)
- Orthanc DICOM data (orthanc_data.tar.gz)
- Moodle data files (moodle_data.tar.gz)
- Pathology slides (pathology_data.tar.gz)
- Configuration files (configs/)
- Environment file (.env)
EOF

echo "✅ Backup completed: $BACKUP_DIR"
echo "📊 Backup size: $(du -sh $BACKUP_DIR | cut -f1)"
"""

# Create restore script
restore_script = """#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "🔄 Restoring Medical LMS from backup: $BACKUP_DIR"

# Stop services
echo "⏹️ Stopping services..."
docker-compose down

# Restore database
if [ -f "$BACKUP_DIR/moodle_db.sql" ]; then
    echo "📥 Restoring PostgreSQL database..."
    docker-compose up -d moodle-db
    sleep 30
    docker-compose exec -T moodle-db psql -U moodleuser -d moodle < "$BACKUP_DIR/moodle_db.sql"
fi

# Restore Orthanc data
if [ -f "$BACKUP_DIR/orthanc_data.tar.gz" ]; then
    echo "📥 Restoring Orthanc data..."
    rm -rf data/orthanc/*
    tar -xzf "$BACKUP_DIR/orthanc_data.tar.gz" -C data/
fi

# Restore Moodle data
if [ -f "$BACKUP_DIR/moodle_data.tar.gz" ]; then
    echo "📥 Restoring Moodle data..."
    rm -rf data/moodledata/*
    tar -xzf "$BACKUP_DIR/moodle_data.tar.gz" -C data/
fi

# Restore pathology slides
if [ -f "$BACKUP_DIR/pathology_data.tar.gz" ]; then
    echo "📥 Restoring pathology slides..."
    rm -rf data/pathology/*
    tar -xzf "$BACKUP_DIR/pathology_data.tar.gz" -C data/
fi

# Restore configuration
if [ -d "$BACKUP_DIR/configs" ]; then
    echo "📥 Restoring configuration..."
    cp -r "$BACKUP_DIR/configs"/* configs/
fi

if [ -f "$BACKUP_DIR/.env" ]; then
    echo "📥 Restoring environment file..."
    cp "$BACKUP_DIR/.env" .
fi

# Start services
echo "▶️ Starting services..."
docker-compose up -d

echo "✅ Restore completed successfully"
"""

# Create monitoring script
monitor_script = """#!/bin/bash

# Medical LMS Monitoring Script
echo "📊 Medical LMS System Status"
echo "============================"

# Check Docker services
echo ""
echo "🐳 Docker Services:"
docker-compose ps

# Check disk usage
echo ""
echo "💾 Disk Usage:"
echo "Data directory: $(du -sh data/ 2>/dev/null || echo 'N/A')"
echo "Logs directory: $(du -sh logs/ 2>/dev/null || echo 'N/A')"

# Check service health
echo ""
echo "🏥 Service Health:"

# Moodle
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200"; then
    echo "✅ Moodle LMS: Healthy"
else
    echo "❌ Moodle LMS: Unhealthy"
fi

# Orthanc
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8042/system | grep -q "200"; then
    echo "✅ Orthanc Server: Healthy"
else
    echo "❌ Orthanc Server: Unhealthy"
fi

# OHIF Viewer
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -q "200"; then
    echo "✅ OHIF Viewer: Healthy"
else
    echo "❌ OHIF Viewer: Unhealthy"
fi

# Pathology Viewer
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health | grep -q "200"; then
    echo "✅ Pathology Viewer: Healthy"
else
    echo "❌ Pathology Viewer: Unhealthy"
fi

# Database
if docker-compose exec -T moodle-db pg_isready -U moodleuser >/dev/null 2>&1; then
    echo "✅ PostgreSQL Database: Healthy"
else
    echo "❌ PostgreSQL Database: Unhealthy"
fi

# Show resource usage
echo ""
echo "📈 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\\t{{.CPUPerc}}\\t{{.MemUsage}}"

echo ""
echo "📋 Recent Logs (last 10 lines):"
docker-compose logs --tail=10
"""

# Write deployment scripts
scripts_dir = "medical-imaging-lms/scripts"
os.makedirs(scripts_dir, exist_ok=True)

with open("medical-imaging-lms/deploy.sh", "w") as f:
    f.write(deploy_script)

with open(f"{scripts_dir}/backup.sh", "w") as f:
    f.write(backup_script)

with open(f"{scripts_dir}/restore.sh", "w") as f:
    f.write(restore_script)

with open(f"{scripts_dir}/monitor.sh", "w") as f:
    f.write(monitor_script)

# Make scripts executable
import stat
for script in ["medical-imaging-lms/deploy.sh", 
               f"{scripts_dir}/backup.sh", 
               f"{scripts_dir}/restore.sh", 
               f"{scripts_dir}/monitor.sh"]:
    current_permissions = os.stat(script).st_mode
    os.chmod(script, current_permissions | stat.S_IEXEC)

print("✅ Created deployment and management scripts")
print("📁 Files created:")
print("- deploy.sh (main deployment script)")
print("- scripts/backup.sh")
print("- scripts/restore.sh") 
print("- scripts/monitor.sh")
print("\n📋 Script Usage:")
print("• ./deploy.sh           - Deploy the complete system")
print("• ./deploy.sh start     - Start all services")
print("• ./deploy.sh stop      - Stop all services")
print("• ./deploy.sh restart   - Restart all services")
print("• ./deploy.sh logs      - View service logs")
print("• ./deploy.sh backup    - Create system backup")
print("• ./deploy.sh restore   - Restore from backup")
print("• ./scripts/monitor.sh  - Check system health")