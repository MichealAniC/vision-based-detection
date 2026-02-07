#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create directory for persistent storage if it doesn't exist
# We will use /var/data as the mount point for Render Disk
if [ ! -d "/var/data" ]; then
    echo "Creating local data directory for testing..."
    mkdir -p vision_attendance/data
else
    echo "Using Render persistent disk..."
fi
