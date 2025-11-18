#!/bin/bash
# Install Trading Scanners as Systemd Services
# Run with: sudo bash deployment/install_services.sh

set -e

echo "=========================================="
echo "Trading Scanners - Systemd Service Installation"
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

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"

# Check dependencies
echo
echo "Checking dependencies..."
cd "$PROJECT_DIR"
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# Install dependencies as the actual user
echo "Installing Python dependencies..."
sudo -u "$ACTUAL_USER" python3 -m pip install --break-system-packages -r requirements.txt --quiet 2>/dev/null || echo "⚠️  Skipping pip install (packages may already be installed)"
echo "✓ Dependencies check complete"

# Check .env file
echo
echo "Checking environment configuration..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating template .env file..."
    cat > "$PROJECT_DIR/.env" << 'EOF'
TELEGRAM_BOT_TOKEN=8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M
TELEGRAM_CHAT_ID=your_chat_id_here
EOF
    chown "$ACTUAL_USER:$ACTUAL_USER" "$PROJECT_DIR/.env"
    echo "✓ Created .env template"
    echo "⚠️  IMPORTANT: Edit .env and add your Telegram chat ID!"
else
    echo "✓ .env file exists"
fi

# Create logs directory
echo
echo "Setting up log directory..."
mkdir -p "$PROJECT_DIR/logs"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$PROJECT_DIR/logs"
echo "✓ Log directory ready"

# Update service files with correct paths and user
echo
echo "Configuring service files..."
for service_file in "$SCRIPT_DIR"/*.service; do
    if [ -f "$service_file" ]; then
        service_name=$(basename "$service_file")
        echo "  Processing $service_name..."
        
        # Create temporary file with updated paths
        sed -e "s|/home/ubuntu/telegramscalperbot|$PROJECT_DIR|g" \
            -e "s|User=ubuntu|User=$ACTUAL_USER|g" \
            -e "s|Group=ubuntu|Group=$ACTUAL_USER|g" \
            "$service_file" > "/tmp/$service_name"
        
        # Copy to systemd directory
        cp "/tmp/$service_name" "/etc/systemd/system/$service_name"
        rm "/tmp/$service_name"
        
        echo "  ✓ Installed $service_name"
    fi
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
echo "Available services:"
echo
echo "Legacy Single-Symbol Scanners:"
echo "  • btc-scalp-scanner.service"
echo "  • btc-swing-scanner.service"
echo "  • gold-scalp-scanner.service"
echo "  • gold-swing-scanner.service"
echo "  • us30-scalp-scanner.service"
echo "  • us30-swing-scanner.service"
echo "  • us30-momentum-scanner.service"
echo "  • btc-us100-scanner.service"
echo
echo "Multi-Symbol Scanners (Recommended):"
echo "  • multi-crypto-scalp-scanner.service   (BTC, ETH, SOL - 1m/5m/15m)"
echo "  • multi-crypto-swing-scanner.service   (BTC, ETH - 15m/1h/4h/1d)"
echo "  • multi-fx-scalp-scanner.service       (EUR/USD, GBP/USD - 5m/15m/1h)"
echo "  • multi-mixed-scanner.service          (BTC, ETH, EUR/USD - 15m/1h/4h)"
echo
echo "Next steps:"
echo
echo "1. Edit .env file with your Telegram credentials:"
echo "   nano $PROJECT_DIR/.env"
echo
echo "2. Enable services to start on boot (choose legacy OR multi-symbol):"
echo
echo "   Legacy scanners:"
echo "   sudo systemctl enable btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner btc-us100-scanner"
echo
echo "   Multi-symbol scanners (recommended):"
echo "   sudo systemctl enable multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner"
echo
echo "3. Start services:"
echo
echo "   Legacy scanners:"
echo "   sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner btc-us100-scanner"
echo
echo "   Multi-symbol scanners (recommended):"
echo "   sudo systemctl start multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner"
echo
echo "4. Check status:"
echo "   sudo systemctl status multi-crypto-scalp-scanner"
echo
echo "5. View logs:"
echo "   sudo journalctl -u multi-crypto-scalp-scanner -f"
echo "   OR"
echo "   tail -f $PROJECT_DIR/logs/multi_crypto_scalp.log"
echo
echo "Quick commands:"
echo "  Start all legacy:  sudo systemctl start btc-*-scanner gold-*-scanner us30-*-scanner"
echo "  Start all multi:   sudo systemctl start multi-*-scanner"
echo "  Stop all:          sudo systemctl stop btc-*-scanner gold-*-scanner us30-*-scanner multi-*-scanner"
echo "  Status all:        sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner multi-*-scanner"
echo
echo "Note: btc-us100-scanner is included in btc-*-scanner pattern"
echo
echo "For more information, see: deployment/INSTALL_SERVICES.md"
echo
