#!/bin/bash
# Quick setup script for Telegram Image Editor Bot

echo "🤖 Telegram Image Editor Bot Setup"
echo "=================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found! Install it first."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Create virtual env
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install deps
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check .env
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Creating from example..."
    cp .env.example .env
    echo ""
    echo "🔑 IMPORTANT: Edit .env file with your tokens!"
    echo ""
    echo "   1. TELEGRAM_BOT_TOKEN - Get from @BotFather on Telegram"
    echo "   2. HUGGINGFACE_TOKEN  - Get from https://huggingface.co/settings/tokens"
    echo ""
    echo "Run: nano .env"
    echo ""
else
    echo "✅ .env file found"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your tokens"
echo "2. Run: python bot.py"
echo ""
echo "For Koyeb deployment, see README.md"
echo ""
