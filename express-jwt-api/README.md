# Express.js REST API with JWT Authentication

A secure REST API built with Express.js featuring JWT authentication, input validation with Joi, and MongoDB integration using Mongoose.

## Features

- ✅ JWT-based authentication with access and refresh tokens
- ✅ User registration and login
- ✅ Password hashing with bcryptjs
- ✅ Input validation using Joi
- ✅ MongoDB integration with Mongoose
- ✅ Protected routes with authentication middleware
- ✅ Role-based authorization
- ✅ Security headers with Helmet
- ✅ Rate limiting
- ✅ CORS enabled

## Tech Stack

- **Express.js** (4.18.2) - Web framework
- **Mongoose** (7.6.3) - MongoDB ODM
- **jsonwebtoken** (9.0.2) - JWT implementation
- **Joi** (17.11.0) - Input validation
- **bcryptjs** (2.4.3) - Password hashing
- **dotenv** (16.3.1) - Environment variables
- **cors** (2.8.5) - CORS middleware
- **helmet** (7.1.0) - Security headers
- **express-rate-limit** (7.1.5) - Rate limiting

## Installation

1. Clone the repository
2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Update the `.env` file with your configuration:
```env
PORT=3000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/express-jwt-api
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_REFRESH_SECRET=your-super-secret-refresh-key-change-this-in-production
```

5. Make sure MongoDB is running on your system

## Running the Application

### Development mode (with auto-reload):
```bash
npm run dev
```

### Production mode:
```bash
npm start
```

The server will start on `http://localhost:3000` (or the PORT specified in .env)

## API Endpoints

### Authentication Routes

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "Password123"
}
```

#### Login User
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "Password123"
}
```

### User Routes (Protected)

#### Get Current User Profile
```http
GET /api/users/profile
Authorization: Bearer <your-jwt-token>
```

#### Update User Profile
```http
PUT /api/users/profile
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

#### Get All Users (Admin Only)
```http
GET /api/users
Authorization: Bearer <admin-jwt-token>
```

#### Delete User (Admin Only)
```http
DELETE /api/users/:id
Authorization: Bearer <admin-jwt-token>
```

### Health Check
```http
GET /health
```

## Project Structure

```
express-jwt-api/
├── src/
│   ├── config/
│   │   └── database.js          # MongoDB connection
│   ├── middleware/
│   │   ├── auth.middleware.js   # JWT authentication
│   │   └── validation.middleware.js  # Joi validation
│   ├── models/
│   │   └── User.model.js        # User schema
│   ├── routes/
│   │   ├── auth.routes.js       # Authentication routes
│   │   └── user.routes.js       # User routes
│   ├── utils/
│   │   └── jwt.utils.js         # JWT utilities
│   └── server.js                # Express app setup
├── .env.example                 # Environment variables template
├── .gitignore
├── package.json
└── README.md
```

## Security Features

1. **Password Hashing**: Passwords are hashed using bcryptjs before storage
2. **JWT Authentication**: Secure token-based authentication
3. **Input Validation**: All inputs validated using Joi schemas
4. **Rate Limiting**: Prevents brute force attacks
5. **Helmet**: Sets security-related HTTP headers
6. **CORS**: Configurable cross-origin resource sharing

## Validation Rules

### Registration
- Name: 2-50 characters
- Email: Valid email format
- Password: Minimum 6 characters, must contain uppercase, lowercase, and number

### Login
- Email: Valid email format
- Password: Required

## Error Handling

The API returns consistent error responses:

```json
{
  "success": false,
  "message": "Error message",
  "errors": [
    {
      "field": "email",
      "message": "Email is required"
    }
  ]
}
```

## License

ISC