#!/usr/bin/env bash
# Build script for Render deployment

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p templates

echo "Build completed successfully!"
