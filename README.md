
# Setup and Run Instructions for SWAPI Service
From within the swapi-service directory
```bash
docker compose up --build
```

Then access the API documentation at http://localhost:8000/docs

## API Endpoints description

The service provides the following endpoints:

### Default
- `POST /populatedb` - Populate Database Endpoint
  - Fetches data from the Star Wars API (SWAPI) and populates the local database
  - Imports characters, films, and starships data
  - Returns status of the population process
  - Should be called once to initialize the database with SWAPI data.
- `GET /health` - Health Check
  - Returns the current status of the service and its dependencies
  - Response includes database connectivity status
  - Returns HTTP 200 for healthy service

### Characters
- `GET /characters/` - Get paginated list of all characters
  - **Pagination**: Use `offset` (default: 0) and `limit` (default: 10, max: 100) parameters
  - **Filter**: Use `name` parameter to filter characters by name

### Films
- `GET /films/` - Get All Films
  - **Pagination**: Use `offset` (default: 0) and `limit` (default: 10, max: 100) parameters
  - **Filter**: Use `title` parameter to filter characters by title

### Starships
- `GET /starships/` - Get All Starships
  - **Pagination**: Use `offset` (default: 0) and `limit` (default: 10, max: 100) parameters
  - **Filter**: Use `name` parameter to filter characters by name


## Testing
Execute the tests using the following command from within the `swapi-service` directory:

```bash
docker compose exec fastapi uv run pytest
```

- A test coverage report is already in the docs folder as `coverage_report.md`.

## API Structure

```
src/
├── alembic/                    # Database migrations
│   ├── env.py                 # Alembic environment configuration
│   ├── script.py.mako         # Migration script template
│   └── versions/              # Migration files
├── api/
│   ├── config/                # Application configuration
│   │   ├── logging.py         # Logging configuration
│   │   └── settings.py        # Application settings
│   ├── core/                  # Core application components
│   │   ├── base_repository.py # Base repository class
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── lifespan.py       # Application lifespan events
│   │   ├── middleware.py     # Custom middleware
│   │   ├── schemas.py        # Core schemas
│   │   ├── pagination/       # Pagination utilities
│   │   │   ├── schemas.py    # Pagination schemas
│   │   │   └── service.py    # Pagination service
│   │   └── populatedb/       # Database population functionality
│   │       ├── routes.py     # Population endpoints
│   │       ├── schemas.py    # Population schemas
│   │       └── service.py    # Population service
│   ├── domains/              # Domain-driven design modules
│   │   ├── associations.py   # Database table associations
│   │   ├── characters/       # Characters domain
│   │   │   ├── models.py     # Character database models
│   │   │   ├── repository.py # Character data access
│   │   │   ├── routes.py     # Character API endpoints
│   │   │   ├── schemas.py    # Character request/response schemas
│   │   │   └── service.py    # Character business logic
│   │   ├── films/            # Films domain
│   │   │   ├── models.py     # Film database models
│   │   │   ├── repository.py # Film data access
│   │   │   ├── routes.py     # Film API endpoints
│   │   │   ├── schemas.py    # Film request/response schemas
│   │   │   └── service.py    # Film business logic
│   │   └── starships/        # Starships domain
│   │       ├── models.py     # Starship database models
│   │       ├── repository.py # Starship data access
│   │       ├── routes.py     # Starship API endpoints
│   │       ├── schemas.py    # Starship request/response schemas
│   │       └── service.py    # Starship business logic
│   ├── main.py               # FastAPI application entry point
│   ├── storage/              # Database connection and configuration
│   │   └── postgres.py       # PostgreSQL connection setup
│   └── utils/                # Utility functions
│       ├── healthcheck.py    # Health check utilities
│       └── url_helpers.py    # URL manipulation helpers
└── alembic.ini              # Alembic configuration file
```

### Architecture Overview

- **Domains**: Each entity (Characters, Films, Starships) has its own domain with models, repository, service, schemas, and routes
- **Repository Pattern**: Data access layer that abstracts database operations
- **Service Layer**: Business logic and coordination between repositories and external services
- **Schema Layer**: Pydantic models for request/response validation and serialization
- **Core**: Shared utilities, base classes, and cross-cutting concerns

## Test Structure

```
tests/
├── conftest.py                # Pytest configuration and fixtures
└── unit/                      # Unit tests
    ├── config/
    │   └── test_logging.py     # Logging configuration tests
    ├── core/                   # Core component tests
    │   ├── pagination/
    │   │   └── test_service.py # Pagination service tests
    │   ├── populatedb/
    │   │   └── test_service.py # Database population tests
    │   ├── test_lifespan.py    # Application lifespan tests
    │   └── test_middleware.py  # Middleware tests
    ├── domains/                # Domain-specific tests
    │   ├── characters/
    │   │   ├── test_repository.py # Character repository tests
    │   │   └── test_service.py    # Character service tests
    │   ├── films/
    │   │   ├── test_repository.py # Film repository tests
    │   │   └── test_service.py    # Film service tests
    │   └── starships/
    │       ├── test_repository.py # Starship repository tests
    │       └── test_service.py    # Starship service tests
    ├── storage/
    │   └── test_postgres.py    # Database connection tests
    └── utils/
        ├── test_healthcheck.py # Health check utility tests
        └── test_url_helpers.py # URL helper utility tests
```

### Test Organization

- **Mirror Structure**: Unit tests mirror the source code structure for easy navigation
- **Unit Tests**: Test individual components in isolation (services, repositories, utilities)
