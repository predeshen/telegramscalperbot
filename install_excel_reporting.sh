#!/bin/bash
# Install Excel Reporting Dependencies

echo "=========================================="
echo "Installing Excel Reporting Dependencies"
echo "=========================================="

# Install openpyxl
echo ""
echo "📦 Installing openpyxl..."
pip3 install openpyxl>=3.1.0

if [ $? -eq 0 ]; then
    echo "✅ openpyxl installed successfully"
else
    echo "❌ Failed to install openpyxl"
    exit 1
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."
python3 -c "import openpyxl; print(f'✅ openpyxl version: {openpyxl.__version__}')"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Excel Reporting Ready!"
    echo "=========================================="
    echo ""
    echo "You can now restart your scanners:"
    echo "  ./stop_all_scanners.sh"
    echo "  ./start_all_scanners.sh --monitor"
else
    echo ""
    echo "❌ Installation verification failed"
    exit 1
fi
