#!/bin/bash
set -e

echo "🚀 Setting up Browser Agent..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo ""

# Initialize ConnectOnion project
echo "🔧 Initializing ConnectOnion project..."
if [ ! -d .co ]; then
    co init
    echo ""
    echo "✅ Project initialized!"
else
    echo "   Project already initialized (found .co directory)"
fi
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install
echo ""

# Setup ConnectOnion authentication
echo "🔐 Setting up ConnectOnion authentication..."
echo "   This will open a browser for authentication."
echo ""

if [ ! -f .env ] || ! grep -q "OPENONION_API_KEY" .env 2>/dev/null; then
    co auth
    echo ""
    echo "✅ Authentication complete!"
else
    echo "   Authentication already configured (found .env)"
fi

echo ""
echo "✨ Setup complete! You can now run:"
echo ""
echo "   python agent.py \"Go to google.com\"   # Run a task"
echo ""
