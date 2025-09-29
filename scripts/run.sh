#!/bin/bash

# run.sh - Wrapper script to run Django management commands with proper environment
# Usage: ./scripts/run.sh [command] [args...]
# Examples:
#   ./scripts/run.sh runserver
#   ./scripts/run.sh migrate
#   ./scripts/run.sh test
#   ./scripts/run.sh seed

set -e  # Exit on any error

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo " Virtual environment not found. Run ./scripts/venv-setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  .env file not found. Using default settings."
fi

# Set default Django settings module
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-kastoma_backend.settings.dev}

# Function to run Django management commands
run_django_command() {
    python manage.py "$@"
}

# Function to run the development server
run_server() {
    echo "🚀 Starting Kastoma Backend development server..."
    echo "📍 Settings: $DJANGO_SETTINGS_MODULE"
    echo "📍 Server will be available at: http://localhost:8000"
    echo "📍 API docs will be available at: http://localhost:8000/api/docs/"
    echo ""
    python manage.py runserver 0.0.0.0:8000
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    python -m pytest "$@"
}

# Function to run linting
run_lint() {
    echo "🔍 Running code quality checks..."
    echo "Running ruff..."
    ruff check .
    echo "Running black..."
    black --check .
    echo "Running isort..."
    isort --check-only .
}

# Function to format code
run_format() {
    echo "🎨 Formatting code..."
    black .
    isort .
    ruff check --fix .
}

# Function to seed database with sample data
run_seed() {
    echo "🌱 Seeding database with sample data..."
    run_django_command seed_products
}

# Function to show help
show_help() {
    echo "Kastoma Backend Management Script"
    echo ""
    echo "Usage: ./scripts/run.sh [command] [args...]"
    echo ""
    echo "Available commands:"
    echo "  runserver         Start the development server"
    echo "  migrate           Run database migrations"
    echo "  makemigrations    Create new migrations"
    echo "  createsuperuser   Create a Django superuser"
    echo "  collectstatic     Collect static files"
    echo "  shell             Open Django shell"
    echo "  test              Run tests with pytest"
    echo "  lint              Run code quality checks (ruff, black, isort)"
    echo "  format            Format code with black, isort, and ruff"
    echo "  seed              Seed database with sample data"
    echo "  help              Show this help message"
    echo ""
    echo "Any other arguments are passed directly to Django's manage.py"
    echo ""
    echo "Examples:"
    echo "  ./scripts/run.sh runserver"
    echo "  ./scripts/run.sh migrate"
    echo "  ./scripts/run.sh test products.tests"
    echo "  ./scripts/run.sh createsuperuser"
}

# Main script logic
case "${1:-help}" in
    "runserver")
        run_server
        ;;
    "test")
        shift
        run_tests "$@"
        ;;
    "lint")
        run_lint
        ;;
    "format")
        run_format
        ;;
    "seed")
        run_seed
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        # Pass all arguments to Django management command
        run_django_command "$@"
        ;;
esac