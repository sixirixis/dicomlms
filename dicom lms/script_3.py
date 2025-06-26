# Create Orthanc Dockerfile and configuration
orthanc_dockerfile = """FROM orthancteam/orthanc:24.5.3

# Install additional dependencies for DICOM-Web and optimizations
USER root

RUN apt-get update && apt-get install -y \\
    curl \\
    jq \\
    python3 \\
    python3-pip \\
    && rm -rf /var/lib/apt/lists/*

# Install Orthanc plugins
RUN pip3 install requests pillow

# Create necessary directories
RUN mkdir -p /var/lib/orthanc/db \\
    && mkdir -p /etc/orthanc \\
    && mkdir -p /var/log/orthanc \\
    && chown -R orthanc:orthanc /var/lib/orthanc \\
    && chown -R orthanc:orthanc /var/log/orthanc

# Copy custom Orthanc configuration
COPY orthanc.json /etc/orthanc/orthanc.json
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy DICOM test data loader script
COPY load-test-data.py /usr/local/bin/
RUN chmod +x /usr/local/bin/load-test-data.py

# Switch back to orthanc user
USER orthanc

# Expose DICOM and HTTP ports
EXPOSE 4242 8042

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:8042/system || exit 1

# Start Orthanc with custom configuration
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["Orthanc", "/etc/orthanc/orthanc.json"]
"""

# Create comprehensive Orthanc configuration
orthanc_config = """{
  "Name": "MedicalLMS-Orthanc",
  "StorageDirectory": "/var/lib/orthanc/db",
  "IndexDirectory": "/var/lib/orthanc/db",
  "StorageCompression": true,
  "MaximumStorageSize": 0,
  "MaximumPatientCount": 0,
  
  "HttpServerEnabled": true,
  "HttpPort": 8042,
  "HttpThreadsCount": 50,
  "HttpTimeout": 60,
  "HttpRequestTimeout": 30,
  "HttpVerbose": false,
  "HttpCompressionEnabled": true,
  "HttpCacheSize": 128,
  "KeepAlive": true,
  "TcpNoDelay": true,
  
  "DicomServerEnabled": true,
  "DicomAet": "MEDICALLMS",
  "DicomPort": 4242,
  "DicomThreadsCount": 4,
  "DicomAssociationTimeout": 30,
  "DicomScuTimeout": 10,
  "DicomScpTimeout": 30,
  
  "RemoteAccessAllowed": true,
  "AuthenticationEnabled": true,
  "RegisteredUsers": {
    "moodle": "moodle123!",
    "admin": "admin123!",
    "viewer": "viewer123!"
  },
  
  "CorsEnabled": true,
  "CorsOrigins": "*",
  
  "SslEnabled": false,
  "SslCertificate": "",
  "SslMinimumProtocolVersion": 4,
  "SslVerifyPeers": false,
  
  "DicomModalities": {
    "sample": [ "STORESCP", "localhost", 2000 ]
  },
  
  "OrthancPeers": {
  },
  
  "PatientsAllowDuplicates": true,
  "StudiesAllowDuplicates": true,
  "SeriesAllowDuplicates": true,
  "InstancesAllowDuplicates": true,
  
  "LogExportedResources": true,
  "LogFile": "/var/log/orthanc/orthanc.log",
  "LogLevel": "default",
  
  "JobsHistorySize": 10,
  "SaveJobs": true,
  
  "OverwriteInstances": false,
  "DefaultEncoding": "Latin1",
  "AcceptedTransferSyntaxes": [ "1.2.840.10008.1.*" ],
  "DeflatedTransferSyntaxAccepted": true,
  "JpegTransferSyntaxAccepted": true,
  "Jpeg2000TransferSyntaxAccepted": true,
  "JpegLosslessTransferSyntaxAccepted": true,
  "JpipTransferSyntaxAccepted": true,
  "Mpeg2TransferSyntaxAccepted": true,
  "RleTransferSyntaxAccepted": true,
  
  "UnknownSopClassAccepted": false,
  "DicomScuPreferredTransferSyntax": "1.2.840.10008.1.2.1",
  
  "UserMetadata": {
    "PatientBirthDate": 1000,
    "StudyDescription": 1001,
    "SeriesDescription": 1002
  },
  
  "UserContentType": {
    "dicom": 1024,
    "dicom-web": 1025
  },
  
  "StableAge": 60,
  "StrictAetComparison": false,
  "StoreMD5ForAttachments": true,
  
  "LimitFindInstances": 0,
  "LimitFindResults": 0,
  "LimitJobs": 10,
  "LimitFindAnswers": 0,
  
  "LogCategories": {
    "dicom": "default",
    "generic": "default",
    "http": "default",
    "sqlite": "default",
    "dicom-web": "default"
  },
  
  "Plugins": [
    "/usr/share/orthanc/plugins",
    "/usr/local/share/orthanc/plugins"
  ],
  
  "DicomWeb": {
    "Enable": true,
    "Root": "/dicom-web/",
    "EnableMetadata": true,
    "StudiesMetadata": "MainDicomTags",
    "SeriesMetadata": "MainDicomTags",
    "InstancesMetadata": "MainDicomTags",
    "QidoRoot": "/dicom-web",
    "WadoRoot": "/dicom-web",
    "Ssl": false,
    "StowMaxInstances": 10,
    "StowMaxSize": 100,
    "Host": "localhost",
    "Port": 8042,
    "HttpHeaders": {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }
  },
  
  "Worklists": {
    "Enable": false,
    "Database": "/var/lib/orthanc/worklists"
  },
  
  "PostgreSQL": {
    "EnableIndex": false,
    "EnableStorage": false,
    "Host": "localhost",
    "Port": 5432,
    "Database": "orthanc",
    "Username": "orthanc",
    "Password": "orthanc",
    "EnableSsl": false,
    "MaximumConnectionRetries": 10,
    "ConnectionRetryInterval": 5,
    "IndexConnectionsCount": 1,
    "StorageConnectionsCount": 1,
    "PrepareIndex": true
  },
  
  "WebViewer": {
    "CachePath": "/var/lib/orthanc/cache",
    "CacheSize": 100,
    "Threads": 4
  }
}"""

# Create Orthanc entrypoint script
orthanc_entrypoint = """#!/bin/bash
set -e

echo "Starting Orthanc DICOM Server for Medical LMS..."

# Create necessary directories
mkdir -p /var/lib/orthanc/db
mkdir -p /var/log/orthanc
mkdir -p /var/lib/orthanc/cache

# Set proper permissions
chown -R orthanc:orthanc /var/lib/orthanc
chown -R orthanc:orthanc /var/log/orthanc

# Wait a moment for any dependent services
sleep 5

# Check if we need to initialize with test data
if [ "$LOAD_TEST_DATA" = "true" ]; then
    echo "Loading test DICOM data..."
    # This will run in background after Orthanc starts
    (sleep 30 && python3 /usr/local/bin/load-test-data.py) &
fi

echo "Orthanc configuration:"
echo "- AET: MEDICALLMS"
echo "- DICOM Port: 4242"
echo "- HTTP Port: 8042"
echo "- Storage: /var/lib/orthanc/db"
echo "- DICOM-Web enabled at /dicom-web/"

# Start Orthanc
exec "$@"
"""

# Create test data loader script
test_data_loader = """#!/usr/bin/env python3
import os
import sys
import time
import requests
import json
from datetime import datetime

def wait_for_orthanc():
    \"\"\"Wait for Orthanc to be fully started\"\"\"
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get('http://localhost:8042/system', timeout=5)
            if response.status_code == 200:
                print("Orthanc is ready!")
                return True
        except:
            pass
        print(f"Waiting for Orthanc... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(2)
    return False

def create_sample_patient():
    \"\"\"Create sample patient and study data for testing\"\"\"
    try:
        # Sample patient data
        patient_data = {
            "Replace": True,
            "Tags": {
                "PatientName": "Doe^John^M^^",
                "PatientID": "12345",
                "PatientBirthDate": "19800101",
                "PatientSex": "M"
            }
        }
        
        # Create sample study
        study_data = {
            "Replace": True,
            "Tags": {
                "StudyInstanceUID": "1.2.826.0.1.3680043.8.498.12345678901234567890",
                "StudyDate": datetime.now().strftime("%Y%m%d"),
                "StudyTime": datetime.now().strftime("%H%M%S"),
                "StudyDescription": "Sample Medical Imaging Study",
                "AccessionNumber": "ACC001",
                "StudyID": "1"
            }
        }
        
        print("Sample DICOM data structure created for testing")
        print("Note: Actual DICOM files need to be uploaded through the web interface")
        print("or via DICOM C-STORE from imaging devices")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")

def main():
    print("Medical LMS DICOM Test Data Loader")
    
    if not wait_for_orthanc():
        print("Failed to connect to Orthanc")
        sys.exit(1)
    
    create_sample_patient()
    print("Test data setup complete")

if __name__ == "__main__":
    main()
"""

# Write Orthanc configuration files
os.makedirs("medical-imaging-lms/docker/orthanc", exist_ok=True)

with open("medical-imaging-lms/docker/orthanc/Dockerfile", "w") as f:
    f.write(orthanc_dockerfile)

with open("medical-imaging-lms/docker/orthanc/orthanc.json", "w") as f:
    f.write(orthanc_config)

with open("medical-imaging-lms/docker/orthanc/docker-entrypoint.sh", "w") as f:
    f.write(orthanc_entrypoint)

with open("medical-imaging-lms/docker/orthanc/load-test-data.py", "w") as f:
    f.write(test_data_loader)

# Create Orthanc configuration for configs directory
with open("medical-imaging-lms/configs/orthanc.json", "w") as f:
    f.write(orthanc_config)

print("✅ Created Orthanc DICOM Server configuration")
print("📁 Files created:")
print("- docker/orthanc/Dockerfile")
print("- docker/orthanc/orthanc.json")
print("- docker/orthanc/docker-entrypoint.sh")
print("- docker/orthanc/load-test-data.py")
print("- configs/orthanc.json")
print("\n📋 Orthanc Features:")
print("- DICOM-Web support (/dicom-web/)")
print("- CORS enabled for web viewers")
print("- Authentication with multiple users")
print("- Optimized for medical imaging workflows")
print("- Test data loader for development")