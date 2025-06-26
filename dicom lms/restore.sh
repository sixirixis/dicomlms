#!/bin/bash
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
