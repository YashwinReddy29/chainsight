# FastAPI Authentication Service

A secure authentication service built with FastAPI, JWT tokens, and PostgreSQL.

## Features

- User registration with email and username validation
- JWT-based authentication
- Password hashing with bcrypt
- PostgreSQL database integration
- Token-based authorization
- Protected endpoints

## Tech Stack

- **FastAPI**: Modern web framework for building APIs
- **python-jose**: JWT token creation and validation
- **passlib + bcrypt**: Secure password hashing
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Relational database
- **Pydantic**: Data validation

## Prerequisites

- Python 3.8+
- PostgreSQL 12+

## Installation

1. Clone the repository and navigate to the auth-service directory:
```bash
cd auth-service
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database:
```bash
# Create database
createdb authdb

# Or using psql
psql -U postgres
CREATE DATABASE authdb;
```

5. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Generate a secure secret key:
```bash
openssl rand -hex 32
```

## Configuration

Edit the `.env` file with your settings:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/authdb
SECRET_KEY=your-generated-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Running the Service

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Public Endpoints

#### Register User
```http
POST /register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

#### Login (Get Token)
```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=securepassword123
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Protected Endpoints

#### Get Current User
```http
GET /users/me
Authorization: Bearer <access_token>
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Usage Example

### Using cURL

1. Register a new user:
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123",
    "full_name": "Test User"
  }'
```

2. Login to get token:
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

3. Access protected endpoint:
```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer <your_access_token>"
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(f"{BASE_URL}/register", json={
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123",
    "full_name": "Test User"
})
print(response.json())

# Login
response = requests.post(f"{BASE_URL}/token", data={
    "username": "testuser",
    "password": "testpass123"
})
token = response.json()["access_token"]

# Get current user
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
print(response.json())
```

## Security Considerations

1. **Secret Key**: Always use a strong, randomly generated secret key in production
2. **HTTPS**: Use HTTPS in production to encrypt token transmission
3. **Token Expiration**: Tokens expire after 30 minutes by default
4. **Password Requirements**: Minimum 8 characters required
5. **Database Credentials**: Never commit database credentials to version control

## Database Schema

### Users Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key |
| email | String | Unique, Not Null |
| username | String | Unique, Not Null |
| full_name | String | Nullable |
| hashed_password | String | Not Null |
| is_active | Boolean | Default: True |
| created_at | DateTime | Auto-generated |
| updated_at | DateTime | Auto-updated |

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8 .
```

## Production Deployment

1. Set strong `SECRET_KEY`
2. Use production-grade PostgreSQL instance
3. Enable HTTPS
4. Set appropriate `ACCESS_TOKEN_EXPIRE_MINUTES`
5. Use environment variables for all sensitive data
6. Enable CORS if needed for frontend integration
7. Set up proper logging and monitoring

## License

MIT License