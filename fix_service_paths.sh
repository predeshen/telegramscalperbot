#!/bin/bash
# Fix Service File Paths
# Updates all service files to use correct paths for current installation

set -e

echo "=========================================="
echo "Fix Service File Paths"
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
PROJECT_DIR="$SCRIPT_DIR"

echo "Configuration:"
echo "  User: $ACTUAL_USER"
echo "  Project Directory: $PROJECT_DIR"
echo

# Confirm
read -p "Is this correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

echo
echo "Updating service files..."

# Update us30-momentum-scanner
if [ -f "/etc/systemd/system/us30-momentum-scanner.service" ]; then
    echo "  Updating us30-momentum-scanner.service..."
    sed -i "s|/home/ubuntu/trading-bot|$PROJECT_DIR|g" /etc/systemd/system/us30-momentum-scanner.service
    sed -i "s|User=ubuntu|User=$ACTUAL_USER|g" /etc/systemd/system/us30-momentum-scanner.service
    sed -i "s|/home/ubuntu/trading-bot/venv/bin/python3|/usr/bin/python3|g" /etc/systemd/system/us30-momentum-scanner.service
    echo "  ✓ Updated us30-momentum-scanner.service"
fi

# Reload systemd
echo
echo "Reloading systemd..."
systemctl daemon-reload
echo "✓ Systemd reloaded"

echo
echo "=========================================="
echo "Service Paths Updated!"
echo "=========================================="
echo
echo "Next steps:"
echo
echo "1. Restart the fixed service:"
echo "   sudo systemctl restart us30-momentum-scanner"
echo
echo "2. Check status:"
echo "   sudo systemctl status us30-momentum-scanner"
echo
echo "3. View logs:"
echo "   sudo journalctl -u us30-momentum-scanner -f"
echo

