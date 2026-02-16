from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy_utils import database_exists, create_database
from datetime import datetime
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123")
DB_NAME = os.getenv("DB_NAME", "abs_cdss")

# Construct DATABASE_URL from components or use complete URL from env
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def init_database():
    """Initialize database - create if not exists"""
    try:
        if not database_exists(DATABASE_URL):
            print(f"Creating database: {DB_NAME}")
            create_database(DATABASE_URL)
            print(f"✅ Database '{DB_NAME}' created successfully")
        else:
            print(f"✅ Database '{DB_NAME}' already exists")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

# Initialize database before creating engine
init_database()

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