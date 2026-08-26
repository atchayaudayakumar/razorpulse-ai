from fastapi import FastAPI

from backend.config import APP_NAME, APP_ENV
from backend.database import Base, engine
from backend import models


# Create all database tables defined in models.py
Base.metadata.create_all(bind=engine)


# Create the FastAPI application
app = FastAPI(
    title=APP_NAME,
    description="AI-powered revenue recovery agent",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "app": APP_NAME,
        "environment": APP_ENV,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }