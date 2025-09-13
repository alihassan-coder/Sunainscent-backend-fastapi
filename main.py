from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from config.database import connect_to_mongo, close_mongo_connection
from config.settings import get_settings
from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.contact import router as contact_router
from routes.orders import router as orders_router
from routes.admin import router as admin_router

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Sunainscent E-commerce API",
    description="Backend API for Sunainscent e-commerce platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()

# Include routers
app.include_router(auth_router, prefix=settings.api_v1_str)
app.include_router(products_router, prefix=settings.api_v1_str)
app.include_router(contact_router, prefix=settings.api_v1_str)
app.include_router(orders_router, prefix=settings.api_v1_str)
app.include_router(admin_router, prefix=settings.api_v1_str)

@app.get("/")
async def read_root():
    return {"message": "Welcome to Sunainscent Backend!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
