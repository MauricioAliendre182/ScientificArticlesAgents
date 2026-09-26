#!/bin/bash
# Quick setup script for Scientific Articles Engine

set -e

echo "=================================="
echo "Scientific Articles Engine - Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "myenv" ]; then
    python3 -m venv myenv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -e . > /dev/null 2>&1
echo "✓ Dependencies installed"
echo ""

# Install development dependencies (optional)
read -p "Install development dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing development dependencies..."
    pip install -e ".[dev]" > /dev/null 2>&1
    echo "✓ Development dependencies installed"
    echo ""
fi

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY or ANTHROPIC_API_KEY"
    echo "   - DATABASE_PASSWORD (if using PostgreSQL)"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Setup database (optional)
read -p "Setup PostgreSQL database with Docker? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v docker-compose &> /dev/null; then
        echo "Starting PostgreSQL with Docker Compose..."
        docker-compose up -d postgres
        echo "✓ PostgreSQL started"
        echo ""
    else
        echo "✗ docker-compose not found. Please install Docker."
        echo ""
    fi
fi

# Run tests (optional)
read -p "Run tests to verify installation? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    pytest tests/unit/ -v
    echo "✓ Tests completed"
    echo ""
fi

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Customize config.yaml if needed"
echo "3. Run: source myenv/bin/activate"
echo "4. Test: scientific-articles-engine --help"
echo "5. Generate an article: scientific-articles-engine generate \"Your Topic\""
echo ""
echo "For more information, see README.md"
