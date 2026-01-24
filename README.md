# Kastoma — E-Commerce API Backend

A Django REST Framework backend for an e-commerce platform with product catalog, user management, and order processing.

## Quick start

```bash
# Clone and enter repository
git clone https://github.com/ZEZE1020/alx-project-nexus-kastoma-api.git
cd alx-project-nexus-kastoma-api

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment example and edit .env
cp .env.example .env
# Edit .env to set SECRET_KEY, DATABASE_URL, and other settings

# Apply migrations and create a superuser
python manage.py migrate
python manage.py createsuperuser

# Optional: generate test tokens (if provided)
python generate_tokens.py

# Start development server
python manage.py runserver
```

## Features

- Django 4.2 + Django REST Framework
- JWT authentication
- Product catalog with categories, variants, and reviews
- Shopping cart and order processing
- Filtering, pagination, and search
- Docker-ready with example compose files
- Automated tests and CI configuration

## Project layout (top-level)

- kastoma_backend/         — Django project settings and configuration
- core/                    — Shared utilities and core functionality
- users/                   — Authentication and user profiles
- products/                — Product catalog, models, and APIs
- orders/                  — Cart, checkout, and order processing
- docs/                    — Documentation and schema files
- development-tools/       — Postman collections and test utilities
- Dockerfile, docker-compose.yml, requirements.txt, manage.py

For full structure and detailed docs, see the docs/ directory and development-tools/.

## Configuration

Environment variables (examples)

```bash
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgresql://user:password@localhost:5432/kastoma_db

# JWT settings (example)
JWT_ACCESS_TOKEN_LIFETIME=5    # minutes
JWT_REFRESH_TOKEN_LIFETIME=1   # days
API_VERSION=v1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## Docker (development)

```bash
# Start development containers
docker-compose up -d

# View logs
docker-compose logs -f
```

Use docker-compose.prod.yml for production orchestration.

## API (key endpoints)

Authentication:
- POST /api/v1/auth/register/      — Register user
- POST /api/v1/auth/login/         — Login and obtain JWT tokens
- POST /api/v1/auth/refresh/       — Refresh token
- POST /api/v1/auth/password-reset/ — Password reset flow

Products:
- GET  /api/v1/products/           — List products (filtering, search, pagination)
- GET  /api/v1/products/{id}/      — Product details (variants, reviews)
- GET  /api/v1/categories/         — Category list

Orders & Cart:
- GET  /api/v1/cart/               — Get cart contents
- POST /api/v1/cart/add_item/      — Add item to cart
- POST /api/v1/orders/             — Create order from cart
- GET  /api/v1/orders/             — Order history

Docs and testing:
- GET /api/docs/                   — Swagger/OpenAPI (if configured)
- Postman collections in development-tools/postman/

## Testing

Run the test suite:

```bash
pytest
```

Utilities:
- python generate_tokens.py         — Generate test JWT tokens (if included)
- python test_api.py                — Script for API testing (if included)

## Contributing

Contributions are welcome. Please fork the repository, create a feature branch, and open a pull request with a clear description of changes and tests where applicable.

## Where to find more documentation

- docs/ — architecture, schema, and guides
- development-tools/postman/ — API collections and environment files
- development-tools/testing/ — extended test scripts

## License

Include your license here (e.g., MIT). If there is already a LICENSE file in the repo, use that.