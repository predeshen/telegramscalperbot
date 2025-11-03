#!/bin/bash
# BTC Scalping Scanner - Installation Script for Linux
# Run with: sudo bash install.sh

set -e

echo "=========================================="
echo "BTC Scalping Scanner - Installation"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (use sudo)"
  exit 1
fi

# Variables
INSTALL_DIR="/opt/btc-scanner"
CONFIG_DIR="/etc/btc-scanner"
LOG_DIR="/var/log/btc-scanner"
SERVICE_FILE="/etc/systemd/system/btc-scanner.service"
USER="btc-scanner"
GROUP="btc-scanner"

echo "Installation directory: $INSTALL_DIR"
echo "Configuration directory: $CONFIG_DIR"
echo "Log directory: $LOG_DIR"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

if [ "$(echo "$PYTHON_VERSION < 3.9" | bc)" -eq 1 ]; then
    echo "Error: Python 3.9 or higher is required"
    exit 1
fi

# Install system dependencies
echo ""
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv

# Create user and group
echo ""
echo "Creating user and group..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$USER"
    echo "User $USER created"
else
    echo "User $USER already exists"
fi

# Create directories
echo ""
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# Copy application files
echo ""
echo "Copying application files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cp -r "$PROJECT_ROOT/src" "$INSTALL_DIR/"
cp "$PROJECT_ROOT/main.py" "$INSTALL_DIR/"
cp "$PROJECT_ROOT/requirements.txt" "$INSTALL_DIR/"

# Copy config template if not exists
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp "$PROJECT_ROOT/config/config.json" "$CONFIG_DIR/"
    echo "Config template copied to $CONFIG_DIR/config.json"
    echo "⚠️  IMPORTANT: Edit $CONFIG_DIR/config.json with your settings!"
else
    echo "Config file already exists at $CONFIG_DIR/config.json"
fi

# Create symlink to config
ln -sf "$CONFIG_DIR/config.json" "$INSTALL_DIR/config.json"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
cd "$INSTALL_DIR"
pip3 install -r requirements.txt

# Set permissions
echo ""
echo "Setting permissions..."
chown -R "$USER:$GROUP" "$INSTALL_DIR"
chown -R "$USER:$GROUP" "$LOG_DIR"
chmod 755 "$INSTALL_DIR"
chmod 755 "$LOG_DIR"
chmod 600 "$CONFIG_DIR/config.json"

# Install systemd service
echo ""
echo "Installing systemd service..."
cp "$SCRIPT_DIR/btc-scanner.service" "$SERVICE_FILE"

# Update service file with correct paths
sed -i "s|/opt/btc-scanner|$INSTALL_DIR|g" "$SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration: sudo nano $CONFIG_DIR/config.json"
echo "2. Update SMTP and Telegram credentials"
echo "3. Enable service: sudo systemctl enable btc-scanner"
echo "4. Start service: sudo systemctl start btc-scanner"
echo "5. Check status: sudo systemctl status btc-scanner"
echo "6. View logs: sudo journalctl -u btc-scanner -f"
echo ""
echo "For Telegram alerts:"
echo "- Create bot with @BotFather on Telegram"
echo "- Get your chat ID from @userinfobot"
echo "- Update config.json with bot_token and chat_id"
echo "- Set 'enabled': true in telegram section"
echo ""
