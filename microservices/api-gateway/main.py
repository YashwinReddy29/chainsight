"""
API Gateway - Central Entry Point for Microservices
Routes requests to appropriate services and handles cross-cutting concerns
"""
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import httpx
import os
from datetime import datetime

app = FastAPI(title="API Gateway", version="1.0.0")
security = HTTPBearer()

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8002")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class DataRecordCreate(BaseModel):
    name: str
    value: float
    category: str


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    services: dict


async def forward_auth_header(credentials: HTTPAuthCredentials = Depends(security)):
    """Extract and forward authorization header"""
    return f"Bearer {credentials.credentials}"


# Auth Service Routes
@app.post("/api/auth/register")
async def register(user: UserCreate):
    """Register a new user via auth service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/register",
                json=user.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", "Registration failed")
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )


@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Login user via auth service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/login",
                json=user.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", "Login failed")
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )


@app.get("/api/auth/verify")
async def verify_token(auth_header: str = Depends(forward_auth_header)):
    """Verify token via auth service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Token verification failed"
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )


# Data Service Routes
@app.post("/api/data/records")
async def create_record(
    record: DataRecordCreate,
    auth_header: str = Depends(forward_auth_header)
):
    """Create a data record via data service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DATA_SERVICE_URL}/records",
                json=record.model_dump(),
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", "Failed to create record")
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Data service unavailable"
            )


@app.get("/api/data/records")
async def get_records(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    auth_header: str = Depends(forward_auth_header)
):
    """Get data records via data service"""
    async with httpx.AsyncClient() as client:
        try:
            params = {"skip": skip, "limit": limit}
            if category:
                params["category"] = category
            
            response = await client.get(
                f"{DATA_SERVICE_URL}/records",
                params=params,
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to fetch records"
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Data service unavailable"
            )


@app.get("/api/data/records/{record_id}")
async def get_record(
    record_id: int,
    auth_header: str = Depends(forward_auth_header)
):
    """Get a specific data record via data service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DATA_SERVICE_URL}/records/{record_id}",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", "Record not found")
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Data service unavailable"
            )


@app.get("/api/data/analysis")
async def analyze_data(auth_header: str = Depends(forward_auth_header)):
    """Get data analysis via data service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DATA_SERVICE_URL}/analysis",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to analyze data"
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Data service unavailable"
            )


@app.delete("/api/data/records/{record_id}")
async def delete_record(
    record_id: int,
    auth_header: str = Depends(forward_auth_header)
):
    """Delete a data record via data service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{DATA_SERVICE_URL}/records/{record_id}",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", "Failed to delete record")
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Data service unavailable"
            )


@app.get("/health", response_model=HealthStatus)
async def health():
    """Comprehensive health check for all services"""
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        # Check auth service
        try:
            auth_response = await client.get(f"{AUTH_SERVICE_URL}/health", timeout=5.0)
            services_status["auth-service"] = {
                "status": "healthy" if auth_response.status_code == 200 else "unhealthy",
                "response_time_ms": auth_response.elapsed.total_seconds() * 1000
            }
        except httpx.RequestError:
            services_status["auth-service"] = {"status": "unavailable"}
        
        # Check data service
        try:
            data_response = await client.get(f"{DATA_SERVICE_URL}/health", timeout=5.0)
            services_status["data-service"] = {
                "status": "healthy" if data_response.status_code == 200 else "unhealthy",
                "response_time_ms": data_response.elapsed.total_seconds() * 1000
            }
        except httpx.RequestError:
            services_status["data-service"] = {"status": "unavailable"}
    
    overall_status = "healthy" if all(
        s.get("status") == "healthy" for s in services_status.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_status
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth/*",
            "data": "/api/data/*",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
