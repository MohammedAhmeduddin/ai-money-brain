# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-28

### Added

#### Backend Infrastructure

- FastAPI application with auto-generated API documentation (Swagger UI)
- PostgreSQL database with Docker Compose setup
- SQLAlchemy ORM with Alembic migrations
- Comprehensive environment configuration system
- CORS middleware for frontend integration

#### Database Models

- User model with UUID primary keys
- Transaction model for financial data
- Category model for budget tracking
- Insight model for AI-generated recommendations
- Rule model for automated alerts
- Alert model for notifications

#### Authentication System

- User registration endpoint (`/api/v1/auth/register`)
- User login endpoint (`/api/v1/auth/login`)
- JWT token generation and validation
- Bcrypt password hashing
- Protected route middleware
- Current user endpoint (`/api/v1/auth/me`)

#### Security

- JWT-based authentication
- Secure password hashing with bcrypt
- Email validation with pydantic
- Environment variable management
- Secure secret key generation

#### Developer Experience

- Comprehensive .gitignore for Python and Node
- Professional README with setup instructions
- Backend-specific documentation
- Test structure (unit, integration, e2e)
- Docker Compose for easy database setup

### Technical Details

- Python 3.9+
- FastAPI 0.109.0
- PostgreSQL 15
- SQLAlchemy 2.0
- Pydantic 2.5

---

## [Unreleased]

### Planned Features

- CSV upload and parsing
- AI transaction categorization
- Dashboard analytics API
- Rule engine for budget alerts
- AI chat copilot
- Frontend application (Next.js)
- Plaid integration
