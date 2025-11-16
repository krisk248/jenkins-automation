#!/bin/bash
# ============================================================================
# Jenkins Build Server Setup Script
# ============================================================================
# This script helps deploy Jenkins build server on 192.168.1.136
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# ============================================================================

set -e

echo "============================================================================"
echo "Jenkins Build Server Setup"
echo "============================================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker installed: $(docker --version)"
echo "✅ Docker Compose installed: $(docker-compose --version)"
echo ""

# Check if old Jenkins is running
if docker ps | grep -q jenkins-master; then
    echo "⚠️  Found existing jenkins-master container"
    read -p "Do you want to stop and remove it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping and removing old container..."
        docker stop jenkins-master
        docker rm jenkins-master
        echo "✅ Old container removed"
    else
        echo "❌ Cannot continue with existing container running"
        exit 1
    fi
fi

echo ""
echo "Building and starting services..."
echo "This will take 5-10 minutes..."
echo ""

# Build and start
docker-compose down
docker-compose up -d --build

echo ""
echo "============================================================================"
echo "Services are starting..."
echo "============================================================================"
echo ""
echo "Jenkins:    http://192.168.1.136:7080"
echo "SonarQube:  http://192.168.1.136:9000"
echo ""
echo "Waiting for Jenkins to be ready..."
echo "This may take 2-3 minutes..."
echo ""

# Wait for Jenkins
for i in {1..60}; do
    if docker logs jenkins-master 2>&1 | grep -q "Jenkins is fully up and running"; then
        echo ""
        echo "✅ Jenkins is ready!"
        echo ""
        echo "============================================================================"
        echo "NEXT STEPS"
        echo "============================================================================"
        echo ""
        echo "1. Get Jenkins admin password:"
        echo "   docker exec jenkins-master cat /var/jenkins_home/secrets/initialAdminPassword"
        echo ""
        echo "2. Access Jenkins: http://192.168.1.136:7080"
        echo ""
        echo "3. Follow setup wizard and install suggested plugins"
        echo ""
        echo "4. See README.md for detailed configuration"
        echo ""
        exit 0
    fi
    echo -n "."
    sleep 3
done

echo ""
echo "⚠️  Jenkins is taking longer than expected to start"
echo "Check logs with: docker-compose logs -f jenkins"
