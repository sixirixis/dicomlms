#!/bin/bash
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
