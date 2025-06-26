#!/usr/bin/env python3
import os
import sys
import time
import requests
import json
from datetime import datetime

def wait_for_orthanc():
    """Wait for Orthanc to be fully started"""
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
    """Create sample patient and study data for testing"""
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
