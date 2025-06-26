#!/bin/bash
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
