"""
Data Service - Data Processing and Storage Microservice
Handles data operations using pandas and SQLAlchemy
"""
from typing import List, Optional
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import requests

app = FastAPI(title="Data Service", version="1.0.0")
security = HTTPBearer()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Auth service URL
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")


# Database Models
class DataRecord(Base):
    __tablename__ = "data_records"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    value = Column(Float)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)


Base.metadata.create_all(bind=engine)


# Pydantic Models
class DataRecordCreate(BaseModel):
    name: str
    value: float
    category: str


class DataRecordResponse(BaseModel):
    id: int
    name: str
    value: float
    category: str
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class DataAnalysis(BaseModel):
    total_records: int
    categories: List[str]
    statistics: dict


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    """Verify token with auth service"""
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/verify",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=5
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return response.json()
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )


@app.post("/records", response_model=DataRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    record: DataRecordCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Create a new data record"""
    db_record = DataRecord(
        name=record.name,
        value=record.value,
        category=record.category,
        created_by=user["user"]["sub"]
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/records", response_model=List[DataRecordResponse])
async def get_records(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Get all data records with optional filtering"""
    query = db.query(DataRecord)
    if category:
        query = query.filter(DataRecord.category == category)
    records = query.offset(skip).limit(limit).all()
    return records


@app.get("/records/{record_id}", response_model=DataRecordResponse)
async def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Get a specific data record"""
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    return record


@app.get("/analysis", response_model=DataAnalysis)
async def analyze_data(
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Analyze data using pandas"""
    records = db.query(DataRecord).all()
    
    if not records:
        return {
            "total_records": 0,
            "categories": [],
            "statistics": {}
        }
    
    # Convert to pandas DataFrame
    df = pd.DataFrame([{
        "id": r.id,
        "name": r.name,
        "value": r.value,
        "category": r.category,
        "created_at": r.created_at
    } for r in records])
    
    # Perform analysis
    statistics = {
        "mean_value": float(df["value"].mean()),
        "median_value": float(df["value"].median()),
        "std_value": float(df["value"].std()),
        "min_value": float(df["value"].min()),
        "max_value": float(df["value"].max()),
        "category_counts": df["category"].value_counts().to_dict()
    }
    
    return {
        "total_records": len(records),
        "categories": df["category"].unique().tolist(),
        "statistics": statistics
    }


@app.delete("/records/{record_id}")
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Delete a data record"""
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

# Made with Bob
