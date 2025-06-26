# Medical Imaging LMS - Integrated DICOM & Pathology Learning Management System

![Medical LMS Architecture](docs/architecture-diagram.png)

## 🏥 Overview

The Medical Imaging LMS is a comprehensive learning management system specifically designed for medical imaging professionals. It combines Moodle's robust LMS capabilities with specialized medical imaging viewers to support education in radiology, pathology, nuclear medicine, and related specialties.

## ✨ Key Features

### 🎯 Target Audience
- **MRI/PET Technologists**
- **Radiology Residents**
- **Nuclear Medicine Residents**
- **Sonographers**
- **Pathologists and Pathology Residents**
- **Radiation Therapists**
- **Dermatologists**
- **Medical Imaging Educators**

### 🔧 Core Technologies
- **Moodle 4.5** - Learning Management System
- **OHIF Viewer v3** - DICOM Medical Imaging Viewer
- **Orthanc Server** - DICOM PACS Backend
- **OpenSeadragon** - Pathology Slide Viewer with IIIF support
- **PostgreSQL** - Database
- **Docker & Kubernetes** - Containerized Deployment
- **React/TypeScript** - Unified Viewer Interface

### 🏗️ Architecture Components

1. **LMS Foundation**
   - Moodle 4.5 with custom medical imaging plugin
   - SCORM and xAPI standards compliance
   - HIPAA-compliant user management and audit logging

2. **DICOM Support**
   - OHIF Viewer v3 with Cornerstone3D rendering engine
   - DICOMWeb protocol integration
   - Multi-planar reconstruction (MPR)
   - GPU-accelerated volume rendering
   - Measurement and annotation tools

3. **Pathology Support**
   - IIIF-compliant whole slide imaging
   - OpenSeadragon-based viewer
   - Multi-gigabyte slide support
   - Zoom and navigation tools
   - Annotation capabilities

4. **Unified Viewer Framework**
   - Automatic switching between DICOM and pathology viewers
   - Study UID-based routing
   - Integrated user interface

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended
- 100GB+ storage for medical data

### Installation

1. **Clone and Deploy**
   ```bash
   git clone https://github.com/your-org/medical-imaging-lms.git
   cd medical-imaging-lms
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Access the System**
   - Moodle LMS: https://localhost/
   - Orthanc Server: http://localhost:8042/
   - OHIF Viewer: http://localhost:3000/
   - Pathology Viewer: http://localhost:8080/

3. **Complete Setup**
   - Install Medical Imaging plugin in Moodle
   - Configure Orthanc connection
   - Upload sample DICOM studies

## 📖 Documentation

### User Guides
- [Student Guide](docs/student-guide.md) - How to use the medical imaging activities
- [Educator Guide](docs/educator-guide.md) - Creating and managing imaging courses
- [Administrator Guide](docs/admin-guide.md) - System administration and configuration

### Technical Documentation
- [Installation Guide](docs/installation.md) - Detailed setup instructions
- [Configuration Guide](docs/configuration.md) - System configuration options
- [API Documentation](docs/api.md) - Developer API reference
- [Security Guide](docs/security.md) - HIPAA compliance and security features

### Deployment
- [Docker Deployment](docs/docker-deployment.md) - Container-based deployment
- [Kubernetes Deployment](docs/kubernetes-deployment.md) - Scalable production deployment
- [Cloud Deployment](docs/cloud-deployment.md) - AWS/Azure/GCP deployment guides

## 🔒 HIPAA Compliance

### Security Features
- **End-to-end encryption** (TLS 1.3)
- **User authentication** and role-based access control
- **Audit logging** for all medical data access
- **Data retention policies** (7-year default)
- **Secure session management**
- **Network security** with container isolation

### Compliance Measures
- **PHI Protection** - No patient data in logs
- **Access Controls** - Granular permissions
- **Data Integrity** - Checksums and validation
- **Backup & Recovery** - Encrypted backup procedures
- **Risk Assessment** - Regular security audits

## 🎓 Educational Features

### Learning Activities
- **Interactive DICOM Viewing** - Multi-planar reconstruction, windowing, measurements
- **Pathology Case Studies** - High-resolution slide navigation
- **Assessment Integration** - Quizzes and case-based evaluations
- **Progress Tracking** - Viewing time and interaction analytics
- **Collaborative Learning** - Annotation sharing and discussion forums

### Supported Modalities
- **CT (Computed Tomography)**
- **MRI (Magnetic Resonance Imaging)**
- **PET (Positron Emission Tomography)**
- **X-Ray Radiography**
- **Ultrasound**
- **Nuclear Medicine**
- **Histopathology Slides**
- **Digital Microscopy**

## 🔧 Administration

### Management Commands
```bash
# Start all services
./deploy.sh start

# Stop all services
./deploy.sh stop

# View service logs
./deploy.sh logs

# Create backup
./deploy.sh backup

# Restore from backup
./deploy.sh restore backup_20241226_120000

# Monitor system health
./scripts/monitor.sh
```

### Configuration Files
- `docker-compose.yml` - Service orchestration
- `.env` - Environment variables
- `configs/orthanc.json` - DICOM server configuration
- `configs/nginx.conf` - Reverse proxy settings

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 4 cores, 2.0 GHz
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Network**: 100 Mbps
- **GPU**: Optional (recommended for 3D rendering)

### Recommended Production Setup
- **CPU**: 8+ cores, 3.0 GHz
- **RAM**: 32 GB+
- **Storage**: 1 TB+ NVMe SSD
- **Network**: 1 Gbps+
- **GPU**: NVIDIA RTX 4000+ for GPU acceleration
- **Load Balancer**: For high availability

## 🤝 Contributing

We welcome contributions from the medical imaging and educational technology communities!

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-org/medical-imaging-lms.git

# Start development environment
cd medical-imaging-lms
./deploy.sh

# Access development tools
docker-compose exec moodle-app bash
docker-compose exec unified-viewer npm run dev
```

### Code Style
- **PHP**: PSR-12 coding standard
- **JavaScript/TypeScript**: ESLint + Prettier
- **Documentation**: Markdown with doctoc

### Testing
- **Unit Tests**: PHPUnit for Moodle plugin
- **Integration Tests**: Jest for React components
- **E2E Tests**: Cypress for user workflows

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses
- **Moodle**: GPL v3.0
- **OHIF Viewer**: MIT License
- **Orthanc**: GPL v3.0
- **OpenSeadragon**: BSD License

## 🆘 Support

### Getting Help
- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join GitHub Discussions
- **Email**: support@medicallms.org

### Professional Support
Commercial support and customization services are available through our certified partners.

## 🙏 Acknowledgments

- **OHIF Community** - For the excellent medical imaging viewer
- **Orthanc Project** - For the robust DICOM server
- **Moodle Community** - For the outstanding LMS platform
- **Medical Imaging Professionals** - For feedback and requirements

## 🚦 Roadmap

### Version 1.1 (Q2 2024)
- [ ] AI-powered image analysis integration
- [ ] Advanced pathology annotation tools
- [ ] Mobile application support
- [ ] FHIR integration

### Version 1.2 (Q3 2024)
- [ ] Multi-institutional collaboration
- [ ] Advanced analytics and reporting
- [ ] VR/AR support for 3D imaging
- [ ] Machine learning model integration

---

**Medical Imaging LMS** - Empowering the next generation of medical imaging professionals through innovative educational technology.
