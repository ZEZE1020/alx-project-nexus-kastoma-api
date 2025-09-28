# Kastoma E-Commerce API Backend

A production-ready Django REST Framework e-commerce backend with comprehensive product catalog, user management, and order processing capabilities.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd alx-capstone-kastoma-api

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py seed_products

# Run development server
python manage.py runserver
```

## 📋 Project Overview

Kastoma is a scalable e-commerce API built with Django REST Framework, designed for modern web and mobile applications requiring robust product catalog management, user authentication, and order processing.

## 🏗️ Architecture & Design Decisions

### Core Framework Choices

- **Django REST Framework**: Comprehensive API toolkit with built-in serialization, pagination, and filtering
- **JWT Authentication**: Stateless authentication suitable for mobile apps and SPAs
- **PostgreSQL/MySQL + SQLite**: Flexible database support for development and production environments
- **Docker**: Containerized deployment for consistent environments across development and production

### Project Structure Rationale

```
kastoma_backend/
├── settings/           # Environment-specific configurations (dev/prod separation)
├── api/               # Versioned API routing (v1, future v2/v3)
└── v1/               # API version 1 endpoints and logic
```

**Why this structure:**
- **Settings package**: Separates development and production configurations for better security
- **API versioning**: Enables backward compatibility when introducing breaking changes
- **Modular routing**: Clean separation between API versions and business logic

### Application Architecture

```
apps/
├── core/              # Shared utilities, health checks, and base functionality
├── users/             # Custom user model with email authentication
├── products/          # Product catalog with categories, variants, and reviews
└── orders/            # Order management and shopping cart functionality
```

**Design principles:**
- **Single responsibility**: Each app handles one business domain
- **Custom user model**: Email-based authentication instead of username for better UX
- **Extensible product system**: Supports variants, images, and customer reviews
- **Health monitoring**: Built-in health checks for production monitoring

## 🔧 Configuration Management

### Environment-Based Settings

- **Base settings**: Common configurations shared across all environments
- **Development settings**: Debug mode, console email backend, permissive CORS
- **Production settings**: Security hardening, file logging, database connection pooling

**Why separate settings:**
- Security isolation between environments
- Easy deployment configuration management
- Development productivity without compromising production security

### Key Configuration Features

- **Environment variables**: Sensitive data managed through environment variables
- **JWT configuration**: Configurable token lifetimes and security settings
- **CORS management**: Flexible cross-origin resource sharing for frontend integration
- **Logging system**: Structured logging with file rotation for production monitoring

## 🛡️ Security Implementation

### Authentication & Authorization

- **JWT tokens**: Stateless authentication with configurable expiration
- **Permission classes**: Role-based access control for different user types
- **Password validation**: Django's built-in password strength validation
- **HTTPS enforcement**: Configurable SSL/TLS security headers

### Production Security

- **Security middleware**: XSS protection, content type sniffing prevention
- **CORS configuration**: Restricted origins for production environments
- **Database security**: Connection pooling and SQL injection protection
- **Static file security**: Proper handling of static assets in production

## 📊 API Design Philosophy

### RESTful Principles

- **Resource-based URLs**: Clear, intuitive endpoint structure
- **HTTP methods**: Proper use of GET, POST, PUT, PATCH, DELETE
- **Status codes**: Meaningful HTTP status codes for different scenarios
- **Pagination**: Efficient handling of large datasets

### API Features

- **Filtering**: Advanced product filtering by price, category, availability
- **Search**: Full-text search across product names and descriptions
- **Sorting**: Flexible ordering of results
- **Documentation**: Auto-generated API documentation with Swagger/OpenAPI

## 🔍 Development Tools & Quality

### Code Quality

- **Linting**: Ruff for fast Python linting and formatting
- **Code formatting**: Black for consistent code style
- **Import sorting**: isort for organized imports
- **Pre-commit hooks**: Automated code quality checks before commits

### Testing Strategy

- **Unit tests**: Model, serializer, and business logic testing
- **Integration tests**: API endpoint testing with authentication
- **Coverage reporting**: Comprehensive test coverage tracking
- **CI/CD pipeline**: Automated testing and deployment workflows

## 🚀 Deployment & Operations

### Containerization

- **Multi-stage Docker**: Optimized image builds with separate build and runtime stages
- **Docker Compose**: Development and production environment orchestration
- **Health checks**: Built-in container health monitoring

### Production Features

- **Health endpoints**: `/health/`, `/health/detailed/`, `/health/ready/`, `/health/live/`
- **Static file handling**: Efficient static asset serving with WhiteNoise
- **Database migrations**: Safe, automated database schema updates
- **Logging**: Structured logging with file rotation and error tracking

### Monitoring & Observability

- **Health monitoring**: Multiple health check endpoints for different monitoring needs
- **Error tracking**: Optional Sentry integration for error reporting
- **Performance monitoring**: Database query optimization and response time tracking
- **Security monitoring**: Authentication failure tracking and rate limiting

## 📱 API Endpoints

### Core Endpoints

- `GET /health/` - Basic service health check
- `GET /api/docs/` - Interactive API documentation
- `POST /api/v1/auth/login/` - User authentication with JWT tokens
- `GET /api/v1/products/` - Product catalog with filtering and search

### Authentication Flow

- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - Login and token generation
- `POST /api/v1/auth/refresh/` - Token refresh
- `POST /api/v1/auth/password-reset/` - Password reset request

### Product Management

- `GET /api/v1/products/` - List products with filtering, search, pagination
- `GET /api/v1/products/{id}/` - Product details with reviews and variants
- `GET /api/v1/categories/` - Product categories with hierarchical structure
- `POST /api/v1/products/{id}/reviews/` - Add product review

## 🛠️ Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL or MySQL (production)
- Redis (optional, for caching)
- Docker (optional, for containerized development)

### Environment Variables

```bash
# Core settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=kastoma_dev
DB_USER=kastoma_user
DB_PASSWORD=your-password

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days
```

### Development Commands

```bash
# Database operations
python manage.py migrate
python manage.py seed_products
python manage.py createsuperuser

# Development server
python manage.py runserver

# Testing
python manage.py test
pytest

# Code quality
ruff check .
black .
isort .
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

- **Code quality**: Automated linting, formatting, and import checking
- **Testing**: Unit and integration test execution with coverage reporting
- **Security scanning**: Dependency vulnerability scanning with safety and bandit
- **Docker builds**: Automated container image building and publishing
- **Deployment**: Automated deployment to staging and production environments

### Quality Gates

- All tests must pass before deployment
- Code coverage thresholds must be met
- Security scans must pass without high-severity issues
- Code must pass linting and formatting checks

## 📈 Scalability Considerations

### Database Optimization

- **Connection pooling**: Efficient database connection management
- **Query optimization**: N+1 query prevention with select_related and prefetch_related
- **Indexing**: Strategic database indexes for performance
- **Migration safety**: Zero-downtime database migrations

### Caching Strategy

- **Redis integration**: Optional Redis caching for improved performance
- **HTTP caching**: Proper cache headers for static content
- **Database query caching**: Frequently accessed data caching
- **Session management**: Efficient user session handling

### Performance Features

- **Pagination**: Efficient large dataset handling
- **Filtering**: Database-level filtering to reduce data transfer
- **Compression**: Response compression for reduced bandwidth usage
- **Static file optimization**: CDN-ready static asset handling

## 🤝 Contributing

### Development Workflow

1. Fork the repository and create a feature branch
2. Install pre-commit hooks: `pre-commit install`
3. Write tests for new functionality
4. Ensure all tests pass and coverage remains high
5. Submit a pull request with clear description

### Code Standards

- Follow PEP 8 style guidelines
- Write comprehensive docstrings for all functions and classes
- Include unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: `/api/docs/` for interactive API documentation
- **Health checks**: `/health/detailed/` for system status
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and community support
