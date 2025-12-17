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

# Copy Chrome profile for Chromium (only if not already exists)
if [ -d "./chromium_automation_profile" ]; then
    echo "📦 Chromium automation profile already exists (./chromium_automation_profile/)"
    echo "   To refresh cookies/sessions, delete it and re-run setup"
else
    echo "📦 Copying Chrome profile for Chromium automation..."
    echo "   This preserves your cookies and login sessions."
    echo ""

    # Detect Chrome profile path
    if [ "$(uname)" = "Darwin" ]; then
        CHROME_PROFILE="$HOME/Library/Application Support/Google/Chrome"
    elif [ "$(uname)" = "Linux" ]; then
        CHROME_PROFILE="$HOME/.config/google-chrome"
    else
        CHROME_PROFILE="$HOME/AppData/Local/Google/Chrome/User Data"
    fi

    # Copy to automation profile (exclude caches for speed)
    if [ -d "$CHROME_PROFILE" ]; then
        echo "   Copying from: $CHROME_PROFILE"
        rsync -a --exclude='*Cache*' --exclude='*cache*' \
              --exclude='Service Worker' --exclude='ShaderCache' \
              "$CHROME_PROFILE/" ./chromium_automation_profile/
        echo "   ✅ Profile copied to ./chromium_automation_profile/"
    else
        echo "   ⚠️  Chrome profile not found - you'll need to login manually"
    fi
fi

echo ""
echo "✨ Setup complete! You can now run:"
echo ""
echo "   python agent.py \"Go to google.com\"   # Run a task"
echo ""
echo "📝 Note: Your Chrome profile has been copied for automation."
echo "   To refresh cookies/sessions, re-run: ./setup.sh"
echo ""
