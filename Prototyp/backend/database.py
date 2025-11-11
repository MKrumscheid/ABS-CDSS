from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123@localhost:5432/abs_cdss")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class SavedTherapyRecommendation(Base):
    """Model for saved therapy recommendations"""
    __tablename__ = "saved_therapy_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Original request data
    request_data = Column(JSON)  
    
    # LLM response data
    therapy_recommendation = Column(JSON)  
    
    # Patient data 
    patient_data = Column(JSON, nullable=True) 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)