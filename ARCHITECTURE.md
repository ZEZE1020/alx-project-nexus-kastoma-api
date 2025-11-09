# Kastoma API - Architectural Deep Dive

This document provides a detailed overview of the architectural design, implementation, and technical decisions behind the Kastoma E-Commerce API.

## System Architecture Overview

Kastoma implements a **3-tier layered architecture** with **domain-driven design** principles, ensuring maintainability, scalability, and testability required for enterprise-grade applications.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                                 │
│  🌐 Web Apps    📱 Mobile Apps    🖥️ Desktop    🔌 Third-party  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/HTTPS + JWT
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API LAYER (Django REST Framework)           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Users     │ │  Products   │ │   Orders    │ │    Core     ││
│  │   Module    │ │   Module    │ │   Module    │ │   Module    ││
│  │             │ │             │ │             │ │             ││
│  │ • Auth      │ │ • Profile   │ │ • Catalog   │ │ • Cart      │ │ • Health    ││
│  │ • Wishlist  │ │ • Reviews   │ │ • Checkout  │ │ • Settings  ││
│  │             │ │ • Variants  │ │ • Payments  │ │ • Analytics ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │ ORM/Database Connections
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │  PostgreSQL │ │    Redis    │ │   Static    │ │    Media    ││
│  │  (Primary   │ │  (Caching)  │ │   Files     │ │   Storage   ││
│  │  Database)  │ │             │ │             │ │             ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Design Patterns & Principles

#### 1. **Domain-Driven Design (DDD)**
- **Bounded Contexts**: Each app (users, products, orders) represents a distinct business domain
- **Aggregate Roots**: User, Product, Order serve as primary entities managing related data
- **Value Objects**: Price, Address, and other immutable data structures
- **Domain Services**: Complex business logic encapsulated in dedicated service classes

#### 2. **API-First Architecture**
- **RESTful Design**: Resource-based URLs with proper HTTP verbs
- **Versioning Strategy**: URL-based versioning (`/api/v1/`) for backward compatibility
- **Content Negotiation**: JSON responses with proper HTTP status codes
- **Stateless Design**: JWT tokens eliminate server-side session management

#### 3. **Layered Architecture**
```
┌─────────────────┐
│   Views Layer   │ ← HTTP Request/Response handling
├─────────────────┤
│ Serializers     │ ← Data validation and transformation
├─────────────────┤
│ Business Logic  │ ← Domain rules and processing
├─────────────────┤
│   Models        │ ← Data persistence and relationships
├─────────────────┤
│   Database      │ ← Data storage and retrieval
└─────────────────┘
```

#### 4. **Security-First Design**
- **Authentication**: JWT with configurable expiration and refresh tokens
- **Authorization**: Permission-based access control for resources
- **Input Validation**: Comprehensive data validation at serializer level
- **CORS Management**: Configurable cross-origin policies
- **Security Headers**: XSS protection, CSRF tokens, and content security policies

### Database Design Architecture

#### Entity Relationship Model
The database follows **normalized design** with strategic **denormalization** for performance:

```
Users Domain:          Products Domain:         Orders Domain:
┌─────────────┐       ┌─────────────┐          ┌─────────────┐
│    User     │       │  Category   │          │    Cart     │
│             │       │             │          │             │
├─────────────┤       ├─────────────┤          ├─────────────┤
│ UserProfile │       │   Product   │          │  CartItem   │
│             │       │             │          │             │
├─────────────┤       ├─────────────┤          ├─────────────┤
│  Wishlist   │       │ ProductVar  │          │    Order    │
│             │       │             │          │             │
├─────────────┤       ├─────────────┤          ├─────────────┤
│WishlistItem │       │ProductImage │          │  OrderItem  │
│             │       │             │          │             │
└─────────────┘       ├─────────────┤          ├─────────────┤
                      │ProductReview│          │   Coupon    │
                      │             │          │             │
                      ├─────────────┤          ├─────────────┤
                      │StockMovement│          │CouponUsage  │
                      └─────────────┘          └─────────────┘
```

#### Key Architectural Decisions

1. **UUID Primary Keys**: Enhanced security and distributed system compatibility
2. **Soft Deletes**: PROTECT constraints maintain data integrity for historical records
3. **Audit Trails**: Comprehensive change tracking for inventory and orders
4. **JSON Fields**: Flexible product attributes without schema changes
5. **Optimized Indexing**: Strategic indexes for common query patterns

### Technology Stack Rationale

#### Backend Framework
- **Django 4.2 LTS**: Long-term support, mature ecosystem, enterprise-grade security
- **Django REST Framework 3.14**: Industry-standard API toolkit with excellent documentation
- **Python 3.12**: Latest stable Python with performance improvements

#### Database Strategy
- **PostgreSQL**: Production database with advanced features (JSON, full-text search)
- **SQLite**: Development database for rapid iteration
- **Database Migrations**: Version-controlled schema changes

#### Authentication & Security
- **djangorestframework-simplejwt**: Secure, stateless authentication
- **CORS Headers**: Configurable cross-origin resource sharing
- **Django Security**: Built-in protection against common vulnerabilities

#### Development & Operations
- **Docker**: Containerization for consistent environments
- **GitHub Actions**: Automated CI/CD with testing and deployment
- **Health Checks**: Monitoring endpoints for production observability

### API Design Philosophy

#### RESTful Resource Design
```
Resources:
├── /auth/          ← Authentication endpoints
├── /users/         ← User management
├── /products/      ← Product catalog
├── /categories/    ← Product categorization
├── /orders/        ← Order processing
├── /cart/          ← Shopping cart
└── /health/        ← System monitoring
```

#### HTTP Method Conventions
- **GET**: Retrieve resources (safe, idempotent)
- **POST**: Create new resources
- **PUT**: Complete resource replacement
- **PATCH**: Partial resource updates
- **DELETE**: Resource removal

#### Response Format Standards
```json
{
  "success": true,
  "data": { /* resource data */ },
  "message": "Operation completed successfully",
  "errors": null,
  "pagination": {
    "count": 100,
    "next": "...",
    "previous": null,
    "page_size": 20
  }
}
```

### Scalability & Performance Architecture

#### Horizontal Scaling Ready
- **Stateless Design**: No server-side sessions enable load balancing
- **Database Connection Pooling**: Efficient resource utilization
- **API Versioning**: Backward compatibility during system evolution
- **Microservices Ready**: Modular design enables service extraction

#### Performance Optimizations
- **Database Query Optimization**: select_related and prefetch_related for efficient queries
- **Pagination**: Limit dataset sizes for improved response times
- **Caching Strategy**: Redis integration for frequently accessed data
- **Static File Optimization**: CDN-ready asset handling

#### Monitoring & Observability
- **Health Endpoints**: Multiple monitoring levels (basic, detailed, live, ready)
- **Structured Logging**: JSON logs with correlation IDs
- **Error Tracking**: Sentry integration for production error monitoring
- **Performance Metrics**: Response time and database query monitoring

## Configuration Management

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

## Security Implementation

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

## API Design Philosophy

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

## Development Tools & Quality Assurance

### Code Quality Standards
- **Ruff**: Lightning-fast Python linting and formatting
- **Type Hints**: Comprehensive type annotations for better code documentation
- **Docstrings**: Complete API documentation with examples
- **Import Organization**: isort for consistent import ordering

### Testing Strategy
- **Unit Tests**: Model, serializer, and business logic testing
- **Integration Tests**: End-to-end API workflow testing
- **Authentication Tests**: JWT token generation and validation
- **Performance Tests**: Database query optimization validation
- **Coverage Reporting**: 90%+ test coverage requirement

### CI/CD Pipeline (GitHub Actions)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Quality  │    │    Testing      │    │   Deployment    │
│                 │    │                 │    │                 │
│ • Ruff linting  │    │ • Unit tests    │    │ • Docker build  │
│ • Type checking │──→ │ • Integration   │──→ │ • Security scan │
│ • Import sort   │    │ • Coverage      │    │ • Production    │
│ • Security scan │    │ • Performance   │    │   deployment    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Production Deployment & Operations

### Containerization Strategy
- **Multi-stage Docker builds**: Optimized image sizes for production
- **Docker Compose**: Orchestrated development and production environments
- **Health checks**: Container-level monitoring and auto-recovery
- **Environment isolation**: Separate configurations for different stages

### Production Features
- **Health Monitoring**: `/health/`, `/health/detailed/`, `/health/ready/`, `/health/live/`
- **Static File Handling**: WhiteNoise for efficient asset serving
- **Database Migrations**: Zero-downtime schema updates
- **Structured Logging**: JSON logs with rotation and retention policies
- **Error Tracking**: Sentry integration for production error monitoring

### Security Implementation
- **JWT Authentication**: Stateless tokens with configurable expiration
- **Permission Classes**: Role-based access control (RBAC)
- **Input Validation**: Comprehensive data sanitization
- **CORS Configuration**: Restrictive cross-origin policies
- **Security Headers**: XSS, CSRF, and clickjacking protection

## API Documentation & Testing

### Interactive Documentation
- **Swagger/OpenAPI**: Auto-generated API documentation at `/api/docs/`
- **Postman Collections**: Ready-to-use API testing collections
- **Authentication Examples**: JWT token generation and usage guides

### Key API Endpoints

#### Authentication
```
POST /api/v1/auth/register/     # User registration
POST /api/v1/auth/login/        # JWT token authentication
POST /api/v1/auth/refresh/      # Token refresh
POST /api/v1/auth/password-reset/ # Password reset flow
```

#### Product Catalog
```
GET    /api/v1/products/        # List products with filtering
GET    /api/v1/products/{id}/   # Product details with variants
GET    /api/v1/categories/      # Hierarchical categories
POST   /api/v1/products/{id}/reviews/ # Customer reviews
```

#### Order Management
```
GET    /api/v1/cart/            # Shopping cart contents
POST   /api/v1/cart/add_item/   # Add items to cart
POST   /api/v1/orders/          # Create order from cart
GET    /api/v1/orders/          # Order history
PATCH  /api/v1/orders/{id}/     # Update order status
```

### API Testing Tools
```bash
# Generate JWT tokens for testing
python generate_tokens.py

# Test all API endpoints
python test_api.py

# Run comprehensive test suite
pytest

# API load testing
python development-tools/testing/test_core_comprehensive.py
```
