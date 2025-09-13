import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def get_database():
    if mongodb.database is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available. Please check MongoDB configuration."
        )
    return mongodb.database

async def connect_to_mongo():
    """Create database connection"""
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        logger.warning("MONGODB_URL environment variable is not set")
        return
    
    # Check if URL has placeholder credentials
    if "<db_username>" in mongodb_url or "<db_password>" in mongodb_url:
        logger.warning("MongoDB URL contains placeholder credentials. Please update .env file with real credentials.")
        logger.info("Server will start without database connection. Update .env and restart to connect to MongoDB.")
        return
    
    try:
        mongodb.client = AsyncIOMotorClient(
            mongodb_url,
            server_api=ServerApi('1'),
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
        )
        # Test the connection
        await mongodb.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas!")
        
        # Get database name from URL or use default
        mongodb.database = mongodb.client.sunainscent
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        logger.info("Server will continue without database connection. Please check your MongoDB credentials.")

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed")