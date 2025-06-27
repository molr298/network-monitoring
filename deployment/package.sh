#!/bin/bash

# Ensure we're in the script's directory
cd "$(dirname "$0")"

# Create deployment directory
DEPLOY_DIR="network-monitoring"
mkdir -p "$DEPLOY_DIR"

# Function to clean macOS attributes
clean_mac_attributes() {
    # Remove macOS specific files and attributes
    find "$1" -type f -name '.DS_Store' -delete
    find "$1" -type d -name '__MACOSX' -exec rm -rf {} + 2>/dev/null || true
    
    # Remove extended attributes
    if command -v xattr >/dev/null; then
        find "$1" -exec xattr -c {} \;
    fi
}

# Function to copy files without macOS attributes
copy_files() {
    local src="$1"
    local dest="$2"
    
    # Create parent directory
    mkdir -p "$dest"
    
    # Copy files
    if command -v rsync >/dev/null; then
        rsync -a --exclude='.DS_Store' --exclude='.git' --exclude='node_modules' --exclude='__pycache__' "$src" "$dest"
    else
        cp -r "$src" "$dest"
    fi
    
    # Clean any macOS attributes
    clean_mac_attributes "$dest"
}

echo "Copying backend files..."
copy_files "../backend/" "$DEPLOY_DIR/backend/"

echo "Copying frontend files..."
copy_files "../frontend/" "$DEPLOY_DIR/frontend/"

# Copy other necessary files
cp docker-compose.yml "$DEPLOY_DIR/"
cp .env.example "$DEPLOY_DIR/.env"

# Final cleanup of any macOS specific files
clean_mac_attributes "$DEPLOY_DIR"

# Create a README
echo "Creating README..."
cat > "$DEPLOY_DIR/README.md" << 'EOL'
# Network Monitoring Deployment

## Prerequisites
- Docker and Docker Compose
- At least 4GB RAM (8GB recommended)

## Quick Start

1. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. Start the services:
   ```bash
   docker-compose up -d --build
   ```

3. Access the applications:
   - Web UI: http://localhost
   - Zabbix: http://localhost:8080 (Admin/zabbix)
   - Grafana: http://localhost:3000 (admin/admin)

## Configuration

Edit the `.env` file to configure:
- Google AI API key for AI features
- Email settings for notifications
- Other environment-specific settings
EOL

# Create a clean tar archive using a temporary directory
echo "Creating archive (this may take a minute)..."

# Create a temporary directory for the clean copy
TEMP_DIR=$(mktemp -d)
CLEAN_DIR="$TEMP_DIR/$(basename "$DEPLOY_DIR")"
mkdir -p "$CLEAN_DIR"

# Copy files without attributes
if command -v rsync >/dev/null; then
    rsync -a --no-perms --no-owner --no-group "$DEPLOY_DIR/" "$CLEAN_DIR/"
else
    cp -r "$DEPLOY_DIR/"* "$CLEAN_DIR/"
fi

# Ensure permissions are clean
find "$CLEAN_DIR" -type d -exec chmod 755 {} \;
find "$CLEAN_DIR" -type f -exec chmod 644 {} \;
chmod +x "$CLEAN_DIR/"*.sh 2>/dev/null || true

# Create the archive from the clean directory
cd "$TEMP_DIR"
tar -czf "$OLDPWD/$DEPLOY_DIR.tar.gz" "$(basename "$DEPLOY_DIR")"
cd "$OLDPWD"

# Clean up
export TEMP_DIR
rm -rf "$TEMP_DIR"
unset TEMP_DIR

echo "Deployment package created: $DEPLOY_DIR.tar.gz"
echo "To deploy, copy this file to your target machine and run:"
echo "  tar -xzf $DEPLOY_DIR.tar.gz"
echo "  cd $DEPLOY_DIR"
echo "  docker-compose up -d --build"
