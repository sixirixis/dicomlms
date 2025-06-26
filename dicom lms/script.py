# Create the directory structure for the medical imaging LMS project
import os
import json

# Create main project directory structure
project_structure = {
    "medical-imaging-lms": {
        "docker": {
            "moodle": {},
            "orthanc": {},
            "ohif-viewer": {},
            "pathology-viewer": {}
        },
        "moodle-plugins": {
            "mod_medical_imaging": {
                "lang": {"en": {}},
                "templates": {},
                "classes": {},
                "amd": {"src": {}}
            }
        },
        "unified-viewer": {
            "src": {
                "components": {},
                "utils": {},
                "styles": {}
            }
        },
        "configs": {},
        "scripts": {},
        "docs": {}
    }
}

def create_directory_structure(structure, base_path=""):
    for name, content in structure.items():
        current_path = os.path.join(base_path, name)
        os.makedirs(current_path, exist_ok=True)
        if isinstance(content, dict):
            create_directory_structure(content, current_path)

create_directory_structure(project_structure)

print("✅ Created project directory structure")
print("📁 medical-imaging-lms/")
for root, dirs, files in os.walk("medical-imaging-lms"):
    level = root.replace("medical-imaging-lms", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}├── {os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        print(f"{subindent}├── {file}")