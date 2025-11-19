#!/bin/bash
# Fresh Installation Script for Trading Scanner System
# Installs all dependencies, creates directories, and enables all services on new VMs

set -e

echo "=========================================="
echo "Trading Scanner System - Fresh Install"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "This script must be run as root"
    exit 1
fi

# Update system packages
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Python and dependencies
echo "Installing Python and dependencies..."
apt-get install -y python3 python3-pip python3-venv git

# Create scanner user
echo "Creating scanner user..."
if ! id -u scanner > /dev/null 2>&1; then
    useradd -m -s /bin/bash scanner
    echo "Scanner user created"
else
    echo "Scanner user already exists"
fi

# Create directories
echo "Creating directories..."
mkdir -p /opt/trading-scanners
mkdir -p /etc/trading-scanners
mkdir -p /var/log/trading-scanners
mkdir -p /var/lib/trading-scanners

# Set permissions
chown -R scanner:scanner /opt/trading-scanners
chown -R scanner:scanner /etc/trading-scanners
chown -R scanner:scanner /var/log/trading-scanners
chown -R scanner:scanner /var/lib/trading-scanners

chmod 755 /opt/trading-scanners
chmod 755 /etc/trading-scanners
chmod 755 /var/log/trading-scanners
chmod 755 /var/lib/trading-scanners

# Copy application files
echo "Copying application files..."
cp -r . /opt/trading-scanners/
chown -R scanner:scanner /opt/trading-scanners

# Install Python dependencies
echo "Installing Python dependencies..."
cd /opt/trading-scanners
sudo -u scanner python3 -m pip install --user -r requirements.txt

# Copy configuration template
echo "Copying configuration template..."
if [ ! -f /etc/trading-scanners/config.json ]; then
    cp config/config.json /etc/trading-scanners/config.json
    chmod 600 /etc/trading-scanners/config.json
    chown scanner:scanner /etc/trading-scanners/config.json
    echo "Configuration template copied to /etc/trading-scanners/config.json"
    echo "⚠️  IMPORTANT: Edit /etc/trading-scanners/config.json with your API keys and credentials"
else
    echo "Configuration file already exists"
fi

# Create systemd service files
echo "Creating systemd service files..."

# BTC Scalp Scanner
cat > /etc/systemd/system/btc-scalp-scanner.service << 'EOF'
[Unit]
Description=BTC Scalp Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.btc_scalp_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# BTC Swing Scanner
cat > /etc/systemd/system/btc-swing-scanner.service << 'EOF'
[Unit]
Description=BTC Swing Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.btc_swing_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Gold Scalp Scanner
cat > /etc/systemd/system/gold-scalp-scanner.service << 'EOF'
[Unit]
Description=Gold Scalp Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.gold_scalp_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Gold Swing Scanner
cat > /etc/systemd/system/gold-swing-scanner.service << 'EOF'
[Unit]
Description=Gold Swing Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.gold_swing_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# US30 Scalp Scanner
cat > /etc/systemd/system/us30-scalp-scanner.service << 'EOF'
[Unit]
Description=US30 Scalp Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.us30_scalp_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# US30 Swing Scanner
cat > /etc/systemd/system/us30-swing-scanner.service << 'EOF'
[Unit]
Description=US30 Swing Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.us30_swing_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# US100 Scanner
cat > /etc/systemd/system/us100-scanner.service << 'EOF'
[Unit]
Description=US100 Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.us100_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Multi-Crypto Scanner
cat > /etc/systemd/system/multi-crypto-scanner.service << 'EOF'
[Unit]
Description=Multi-Crypto Scanner
After=network.target

[Service]
Type=simple
User=scanner
WorkingDirectory=/opt/trading-scanners
ExecStart=/usr/bin/python3 -m src.scanners.multi_crypto_scanner
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable btc-scalp-scanner
systemctl enable btc-swing-scanner
systemctl enable gold-scalp-scanner
systemctl enable gold-swing-scanner
systemctl enable us30-scalp-scanner
systemctl enable us30-swing-scanner
systemctl enable us100-scanner
systemctl enable multi-crypto-scanner

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano /etc/trading-scanners/config.json"
echo "2. Add your API keys and credentials"
echo "3. Start all scanners: systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner"
echo "4. Check status: systemctl status btc-scalp-scanner"
echo "5. View logs: journalctl -u btc-scalp-scanner -f"
echo ""
echo "All services are configured to start automatically on boot."
echo ""

