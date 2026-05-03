# Microservices Architecture

A production-ready microservices architecture with three core services: Authentication, Data Processing, and API Gateway.

## Architecture Overview

```
┌─────────────────┐
│   API Gateway   │ :8000
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼────┐ ┌─▼──────────┐
│  Auth  │ │    Data    │
│Service │ │  Service   │
│ :8001  │ │   :8002    │
│(PyJWT) │ │(Pandas/SQL)│
└────────┘ └────────────┘
```

## Services

### 1. Auth Service (Port 8001)
**Purpose**: Handles user authentication and JWT token management

**Technologies**:
- FastAPI for REST API
- PyJWT for token generation/verification
- SHA-256 for password hashing

**Endpoints**:
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /verify` - Verify JWT token
- `GET /health` - Health check

### 2. Data Service (Port 8002)
**Purpose**: Manages data operations with analytics capabilities

**Technologies**:
- FastAPI for REST API
- Pandas for data analysis
- SQLAlchemy for database operations
- SQLite for data storage

**Endpoints**:
- `POST /records` - Create data record (requires auth)
- `GET /records` - List all records (requires auth)
- `GET /records/{id}` - Get specific record (requires auth)
- `GET /analysis` - Get data analytics (requires auth)
- `DELETE /records/{id}` - Delete record (requires auth)
- `GET /health` - Health check

### 3. API Gateway (Port 8000)
**Purpose**: Central entry point that routes requests to appropriate services

**Technologies**:
- FastAPI for REST API
- HTTPX for async HTTP requests
- CORS middleware for cross-origin requests

**Endpoints**:
- `POST /api/auth/register` - Routes to auth service
- `POST /api/auth/login` - Routes to auth service
- `GET /api/auth/verify` - Routes to auth service
- `POST /api/data/records` - Routes to data service
- `GET /api/data/records` - Routes to data service
- `GET /api/data/records/{id}` - Routes to data service
- `GET /api/data/analysis` - Routes to data service
- `DELETE /api/data/records/{id}` - Routes to data service
- `GET /health` - Aggregated health check
- `GET /` - API information

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker Compose

1. **Start all services**:
```bash
cd microservices
docker-compose up --build
```

2. **Access the services**:
- API Gateway: http://localhost:8000
- Auth Service: http://localhost:8001
- Data Service: http://localhost:8002

3. **Stop all services**:
```bash
docker-compose down
```

### Running Locally (Development)

#### Auth Service
```bash
cd auth-service
pip install -r requirements.txt
python main.py
```

#### Data Service
```bash
cd data-service
pip install -r requirements.txt
python main.py
```

#### API Gateway
```bash
cd api-gateway
pip install -r requirements.txt
python main.py
```

## Usage Examples

### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "username": "johndoe"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

### 3. Create Data Record
```bash
curl -X POST http://localhost:8000/api/data/records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Sales Q1",
    "value": 15000.50,
    "category": "revenue"
  }'
```

### 4. Get Data Analysis
```bash
curl -X GET http://localhost:8000/api/data/analysis \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Response:
```json
{
  "total_records": 10,
  "categories": ["revenue", "expenses"],
  "statistics": {
    "mean_value": 12500.75,
    "median_value": 11000.00,
    "std_value": 3500.25,
    "min_value": 5000.00,
    "max_value": 25000.00,
    "category_counts": {
      "revenue": 6,
      "expenses": 4
    }
  }
}
```

### 5. Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-03T07:25:00.000Z",
  "services": {
    "auth-service": {
      "status": "healthy",
      "response_time_ms": 15.2
    },
    "data-service": {
      "status": "healthy",
      "response_time_ms": 23.5
    }
  }
}
```

## Security Features

### Authentication
- JWT-based authentication with configurable expiration
- Secure password hashing using SHA-256
- Token verification on all protected endpoints

### API Gateway Security
- CORS middleware for cross-origin protection
- Bearer token authentication
- Request validation using Pydantic models

### Best Practices
- All dependencies pinned to exact versions
- Environment variables for sensitive configuration
- Health checks for service monitoring
- Proper error handling and status codes

## Configuration

### Environment Variables

**Auth Service**:
- `SECRET_KEY` - JWT signing key (default: "your-secret-key-change-in-production")
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 30)

**Data Service**:
- `DATABASE_URL` - Database connection string (default: "sqlite:///./data.db")
- `AUTH_SERVICE_URL` - Auth service URL (default: "http://localhost:8001")

**API Gateway**:
- `AUTH_SERVICE_URL` - Auth service URL (default: "http://localhost:8001")
- `DATA_SERVICE_URL` - Data service URL (default: "http://localhost:8002")

## Project Structure

```
microservices/
├── auth-service/
│   ├── main.py              # Auth service implementation
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Container configuration
├── data-service/
│   ├── main.py              # Data service implementation
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Container configuration
├── api-gateway/
│   ├── main.py              # API gateway implementation
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Container configuration
├── docker-compose.yml       # Multi-container orchestration
└── README.md               # This file
```

## Dependencies

All services use exact version pinning for security and reproducibility.

### Auth Service
- fastapi==0.109.2
- uvicorn==0.27.1
- pyjwt==2.8.0
- pydantic==2.6.1
- email-validator==2.1.0.post1

### Data Service
- fastapi==0.109.2
- uvicorn==0.27.1
- pandas==2.2.0
- sqlalchemy==2.0.25
- requests==2.31.0

### API Gateway
- fastapi==0.109.2
- uvicorn==0.27.1
- httpx==0.26.0
- pydantic==2.6.1
- email-validator==2.1.0.post1

## Monitoring and Health Checks

Each service exposes a `/health` endpoint for monitoring:
- Individual service health checks
- Aggregated health status via API Gateway
- Docker health checks configured in docker-compose.yml

## Development

### Adding New Endpoints

1. Add endpoint to the appropriate service
2. Update API Gateway to route to the new endpoint
3. Update this README with the new endpoint documentation

### Testing

Each service can be tested independently:

```bash
# Test auth service
curl http://localhost:8001/health

# Test data service
curl http://localhost:8002/health

# Test API gateway
curl http://localhost:8000/health
```

## Production Considerations

1. **Security**:
   - Change default SECRET_KEY
   - Use environment variables for all secrets
   - Implement rate limiting
   - Add API key authentication for service-to-service communication

2. **Database**:
   - Replace SQLite with PostgreSQL or MySQL
   - Implement database migrations
   - Add connection pooling

3. **Scalability**:
   - Deploy services independently
   - Use container orchestration (Kubernetes)
   - Implement service discovery
   - Add load balancing

4. **Monitoring**:
   - Add logging aggregation
   - Implement distributed tracing
   - Set up metrics collection
   - Configure alerting

## License

MIT License - See LICENSE file for details