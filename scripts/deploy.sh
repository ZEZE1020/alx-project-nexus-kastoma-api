#!/bin/bash

# Production deployment script for Kastoma API
# This script handles common deployment tasks for production environments

set -e  # Exit on error

echo "🚀 Starting Kastoma API deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not detected. Consider activating one."
fi

# Set production environment
export DJANGO_SETTINGS_MODULE=kastoma_backend.settings.prod

print_info "Using Django settings: $DJANGO_SETTINGS_MODULE"

# Check if required environment variables are set
required_vars=("SECRET_KEY" "DB_NAME" "DB_USER" "DB_PASSWORD" "ALLOWED_HOSTS")

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_info "Environment variables validated ✓"

# Install/update dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Run Django system checks
print_info "Running Django system checks..."
python manage.py check --deploy

# Check for pending migrations
print_info "Checking for pending migrations..."
if python manage.py showmigrations --list | grep -q '[ ]'; then
    print_warning "Pending migrations detected. Running migrations..."
    python manage.py migrate
else
    print_info "No pending migrations ✓"
fi

# Collect static files
print_info "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (interactive)
print_info "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. Please create one:')
    exit(1)
else:
    print('Superuser exists ✓')
" || {
    print_warning "No superuser found. Creating one..."
    python manage.py createsuperuser
}

# Run tests (optional, can be skipped with --skip-tests)
if [[ "$1" != "--skip-tests" ]]; then
    print_info "Running tests..."
    python manage.py test --verbosity=1
else
    print_warning "Skipping tests as requested"
fi

# Health check
print_info "Running health check..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kastoma_backend.settings.prod')
django.setup()

from django.test import Client
client = Client()
response = client.get('/health/')
if response.status_code == 200:
    print('Health check passed ✓')
else:
    print(f'Health check failed with status {response.status_code}')
    exit(1)
"

# Restart services (if using systemd)
if command -v systemctl > /dev/null 2>&1; then
    if systemctl is-active --quiet kastoma-api; then
        print_info "Restarting kastoma-api service..."
        sudo systemctl restart kastoma-api
    else
        print_warning "kastoma-api service not found or not running"
    fi
    
    if systemctl is-active --quiet nginx; then
        print_info "Reloading nginx..."
        sudo systemctl reload nginx
    else
        print_warning "nginx service not found or not running"
    fi
fi

print_info "✅ Deployment completed successfully!"
print_info "🌐 Your API should be available at your configured domain"
print_info "📊 Check the health endpoint: /health/"
print_info "📚 API documentation: /api/docs/"

echo ""
echo "Next steps:"
echo "1. Verify the application is running correctly"
echo "2. Check logs for any issues"
echo "3. Test critical API endpoints"
echo "4. Monitor system resources"