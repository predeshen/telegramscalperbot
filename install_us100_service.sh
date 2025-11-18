#!/bin/bash
# Quick installer for US100 scanner service

set -e

echo "=========================================="
echo "US100/NASDAQ Scanner Service Installation"
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
    echo "Please specify the user to run service as:"
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
    echo "Installation cancelled"
    exit 1
fi

# Check if main_us100.py exists
if [ ! -f "$PROJECT_DIR/main_us100.py" ]; then
    echo "❌ Error: main_us100.py not found in $PROJECT_DIR"
    exit 1
fi

echo "✓ Found main_us100.py"

# Check Python
echo
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"

# Create service file with correct paths
echo
echo "Creating service file..."
cat > /tmp/btc-us100-scanner.service << EOF
[Unit]
Description=US100/NASDAQ Trading Scanner
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 $PROJECT_DIR/main_us100.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=us100-scanner

# Resource limits
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# Copy to systemd directory
cp /tmp/btc-us100-scanner.service /etc/systemd/system/btc-us100-scanner.service
rm /tmp/btc-us100-scanner.service

echo "✓ Service file created"

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
echo "US100/NASDAQ Scanner service installed successfully!"
echo
echo "Next steps:"
echo
echo "1. Make sure .env file has Telegram credentials:"
echo "   nano $PROJECT_DIR/.env"
echo
echo "2. Enable service to start on boot:"
echo "   sudo systemctl enable btc-us100-scanner"
echo
echo "3. Start the service:"
echo "   sudo systemctl start btc-us100-scanner"
echo
echo "4. Check status:"
echo "   sudo systemctl status btc-us100-scanner"
echo
echo "5. View logs:"
echo "   sudo journalctl -u btc-us100-scanner -f"
echo "   OR"
echo "   tail -f $PROJECT_DIR/logs/us100_scanner.log"
echo
echo "Quick commands:"
echo "  Start:   sudo systemctl start btc-us100-scanner"
echo "  Stop:    sudo systemctl stop btc-us100-scanner"
echo "  Restart: sudo systemctl restart btc-us100-scanner"
echo "  Status:  sudo systemctl status btc-us100-scanner"
echo "  Logs:    sudo journalctl -u btc-us100-scanner -f"
echo

