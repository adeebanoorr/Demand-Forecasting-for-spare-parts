#!/bin/bash
set -ex

echo "--- STARTING FRONTEND BUILD ---"
PROJECT_ROOT=$(pwd)
WEBAPP_DIR="$PROJECT_ROOT/src/webapp"

echo "Directory: $WEBAPP_DIR"
cd "$WEBAPP_DIR"

if [ ! -f "package.json" ]; then
    echo "ERROR: package.json not found in $WEBAPP_DIR"
    exit 1
fi

echo "Installing dependencies..."
npm install --no-audit --no-fund

echo "Building production assets..."
npm run build

echo "Verifying build output..."
if [ -d "dist" ]; then
    echo "SUCCESS: dist directory created."
    ls -la dist
else
    echo "ERROR: dist directory MISSING after build."
    exit 1
fi

echo "--- FRONTEND BUILD COMPLETE ---"
