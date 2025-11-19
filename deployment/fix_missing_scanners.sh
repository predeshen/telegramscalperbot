#!/bin/bash
# Fix Missing Scanner Services - Reinstall with correct paths
# Run with: sudo bash deployment/fix_missing_scanners.sh

set -e

echo "=========================================="
echo "Fixing Missing Scanner Services"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run as root (use sudo)"
  exit 1
fi

# Detect project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Configuration:"
echo "  Project Directory: $PROJECT_DIR"
echo

# Stop the services first
echo "Stopping services..."
systemctl stop multi-crypto-scanner us100-scanner 2>/dev/null || true
sleep 2

# Fix permissions on project directory
echo "Fixing directory permissions..."
chmod -R 755 "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR/logs"
chmod -R 755 "$PROJECT_DIR/config"
echo "✓ Permissions fixed"

# Reinstall service files with correct paths
echo
echo "Reinstalling service files..."

# Process multi-crypto-scanner.service
sed -e "s|/home/ubuntu/telegramscalperbot|$PROJECT_DIR|g" \
    "$SCRIPT_DIR/multi-crypto-scanner.service" > /etc/systemd/system/multi-crypto-scanner.service
echo "✓ Installed multi-crypto-scanner.service"

# Process us100-scanner.service
sed -e "s|/home/ubuntu/telegramscalperbot|$PROJECT_DIR|g" \
    "$SCRIPT_DIR/us100-scanner.service" > /etc/systemd/system/us100-scanner.service
echo "✓ Installed us100-scanner.service"

# Reload systemd
echo
echo "Reloading systemd daemon..."
systemctl daemon-reload
echo "✓ Systemd reloaded"

# Start the services
echo
echo "Starting services..."
systemctl start multi-crypto-scanner us100-scanner
sleep 3

# Check status
echo
echo "Checking service status..."
systemctl status multi-crypto-scanner us100-scanner

echo
echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
echo
echo "View logs:"
echo "  sudo journalctl -u multi-crypto-scanner -f"
echo "  sudo journalctl -u us100-scanner -f"
echo
