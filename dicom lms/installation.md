# Installation Guide - Medical Imaging LMS

## System Requirements

### Hardware Requirements
- **Minimum**: 4 CPU cores, 8GB RAM, 100GB storage
- **Recommended**: 8+ CPU cores, 32GB RAM, 1TB SSD storage
- **GPU**: Optional NVIDIA GPU for accelerated rendering

### Software Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL (for certificate generation)

## Installation Steps

### 1. Download and Setup
```bash
# Clone the repository
git clone https://github.com/your-org/medical-imaging-lms.git
cd medical-imaging-lms

# Make deployment script executable
chmod +x deploy.sh
```

### 2. Deploy the System
```bash
# Run the automated deployment
./deploy.sh
```

The deployment script will:
- Check prerequisites
- Create necessary directories
- Generate SSL certificates
- Set up environment variables
- Build Docker images
- Start all services
- Perform health checks

### 3. Access the System
After deployment, access:
- **Moodle LMS**: https://localhost/
- **Orthanc DICOM Server**: http://localhost:8042/
- **OHIF Viewer**: http://localhost:3000/
- **Pathology Viewer**: http://localhost:8080/

### 4. Complete Moodle Setup
1. Visit https://localhost/
2. Complete Moodle installation wizard
3. Install Medical Imaging plugin
4. Configure Orthanc connection in admin settings

### 5. Upload Sample Data
1. Access Orthanc at http://localhost:8042/
2. Upload DICOM studies
3. Upload pathology slides via pathology viewer

## Configuration

### Environment Variables (.env)
- Update passwords and settings in `.env` file
- Configure SMTP for email notifications
- Set up SSL certificate paths

### Moodle Configuration
- Install Medical Imaging activity plugin
- Configure Orthanc server connection
- Set up user roles and permissions

### Security Configuration
- Update SSL certificates for production
- Configure firewall rules
- Set up backup procedures

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check for running services on required ports
2. **Permission errors**: Ensure proper directory permissions
3. **Memory issues**: Increase Docker memory limits
4. **SSL errors**: Regenerate certificates if needed

### Log Access
```bash
# View all service logs
./deploy.sh logs

# View specific service logs
docker-compose logs moodle-app
docker-compose logs orthanc-server
```

### Service Management
```bash
# Start services
./deploy.sh start

# Stop services
./deploy.sh stop

# Restart services
./deploy.sh restart

# Check system health
./scripts/monitor.sh
```

## Next Steps
1. Import medical imaging curriculum
2. Create user accounts for students and instructors
3. Set up course structures
4. Configure assessment criteria
5. Train users on the system

For detailed configuration options, see the [Configuration Guide](configuration.md).
