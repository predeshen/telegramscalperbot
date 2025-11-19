#!/bin/bash
# Install Missing Scanner Services (multi-crypto-scanner and us100-scanner)
# Run with: sudo bash deployment/install_missing_services.sh

set -e

echo "=========================================="
echo "Installing Missing Scanner Services"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run as root (use sudo)"
  exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo "⚠️  Warning: Running as root user"
    echo "Please specify the user to run services as:"
    read -p "Username: " ACTUAL_USER
fi

# Detect project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Configuration:"
echo "  User: $ACTUAL_USER"
echo "  Project Directory: $PROJECT_DIR"
echo

# Confirm
read -p "Is this correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled"
    exit 1
fi

echo
echo "Installing missing service files..."

# Services to install
SERVICES=("multi-crypto-scanner.service" "us100-scanner.service")

for service_file in "${SERVICES[@]}"; do
    source_file="$SCRIPT_DIR/$service_file"
    
    if [ ! -f "$source_file" ]; then
        echo "❌ Error: $source_file not found"
        exit 1
    fi
    
    echo "  Processing $service_file..."
    
    # Create temporary file with updated paths
    sed -e "s|/home/ubuntu/telegramscalperbot|$PROJECT_DIR|g" \
        -e "s|User=ubuntu|User=$ACTUAL_USER|g" \
        -e "s|Group=ubuntu|Group=$ACTUAL_USER|g" \
        "$source_file" > "/tmp/$service_file"
    
    # Copy to systemd directory
    cp "/tmp/$service_file" "/etc/systemd/system/$service_file"
    rm "/tmp/$service_file"
    
    echo "  ✓ Installed $service_file"
done

# Reload systemd
echo
echo "Reloading systemd daemon..."
systemctl daemon-reload
echo "✓ Systemd reloaded"

echo
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo
echo "1. Enable services to start on boot:"
echo "   sudo systemctl enable multi-crypto-scanner us100-scanner"
echo
echo "2. Start the services:"
echo "   sudo systemctl start multi-crypto-scanner us100-scanner"
echo
echo "3. Check status:"
echo "   sudo systemctl status multi-crypto-scanner us100-scanner"
echo
echo "4. View logs:"
echo "   sudo journalctl -u multi-crypto-scanner -f"
echo "   sudo journalctl -u us100-scanner -f"
echo
