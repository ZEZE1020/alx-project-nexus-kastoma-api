#!/bin/bash

# venv-setup.sh - Set up Python virtual environment and install dependencies
# Usage: ./scripts/venv-setup.sh

set -e  # Exit on any error

echo " Setting up Kastoma Backend Environment..."

# Check if Python 3.13+ is available
if ! command -v python3.13 &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo " Python 3 is not installed. Please install Python 3.13+ first."
        exit 1
    fi
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3.13"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo " Using Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo " Creating virtual environment..."
    $PYTHON_CMD -m venv venv
else
    echo " Virtual environment already exists"
fi

# Activate virtual environment
echo " Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo " Creating .env file from template..."
    cp .env.example .env
    echo "Warning: Please edit .env file with your actual configuration before running the server"
else
    echo "Success: .env file already exists"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Run migrations: ./scripts/run.sh migrate"
echo "3. Create superuser: ./scripts/run.sh createsuperuser"
echo "4. Seed sample data: ./scripts/run.sh seed"
echo "5. Start server: ./scripts/run.sh runserver"
echo ""
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"