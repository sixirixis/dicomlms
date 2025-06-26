#!/bin/bash

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
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "📋 Recent Logs (last 10 lines):"
docker-compose logs --tail=10
