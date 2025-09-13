from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from config.database import get_database
from validation.user_models import UserCreate, UserLogin, UserResponse, Token, UserInDB
from utils.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db = Depends(get_database)):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user document
    user_doc = {
        "email": user.email,
        "hashed_password": hashed_password,
        "first_name": user.first_name,
        "phone": user.phone,
        "created_at": datetime.utcnow()
    }
    
    # Insert user into database
    result = await db.users.insert_one(user_doc)
    
    # Retrieve created user
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    return UserResponse.from_mongo(created_user)

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db = Depends(get_database)):
    """Login user and return JWT token"""
    
    # Find user by email
    user = await db.users.find_one({"email": user_credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserInDB = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        phone=current_user.phone,
        created_at=current_user.created_at,
        is_admin=current_user.is_admin
    )

@router.get("/verify-token")
async def verify_token(current_user: UserInDB = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "user": current_user.email}