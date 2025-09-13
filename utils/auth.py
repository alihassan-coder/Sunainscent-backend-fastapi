from datetime import datetime, timedelta
from typing import Optional
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import get_settings
from config.database import get_database
from validation.user_models import TokenData, UserInDB

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
security = HTTPBearer()

settings = get_settings()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_time)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

async def verify_token(token: str) -> TokenData:
    """Verify JWT token and extract payload"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    return token_data

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database)
) -> UserInDB:
    """Get current authenticated user"""
    token = credentials.credentials
    token_data = await verify_token(token)
    
    user = await db.users.find_one({"email": token_data.email})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is admin
    admin_email = os.getenv("ADMIN_EMAIL")
    is_admin = user["email"] == admin_email
    
    user_data = UserInDB.from_mongo(user)
    user_data.is_admin = is_admin
    
    return user_data

# Admin Authentication Functions
async def verify_admin_credentials(email: str, password: str) -> bool:
    """Verify admin credentials against environment variables"""
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    return email == admin_email and password == admin_password

async def create_admin_token(email: str) -> str:
    """Create JWT token for admin with special admin scope"""
    token_data = {
        "sub": email,
        "is_admin": True
    }
    return create_access_token(data=token_data)

async def verify_admin_token(token: str) -> dict:
    """Verify admin JWT token and extract payload"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin access required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        
        if email is None or not is_admin:
            raise credentials_exception
            
        return {"email": email, "is_admin": is_admin}
    except JWTError:
        raise credentials_exception

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated admin"""
    token = credentials.credentials
    admin_data = await verify_admin_token(token)
    return admin_data
