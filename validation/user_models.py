from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=10)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    first_name: str
    phone: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_admin: Optional[bool] = False
    
    @classmethod
    def from_mongo(cls, data: dict) -> "UserResponse":
        """Convert MongoDB document to Pydantic model"""
        if data.get("_id"):
            data["_id"] = str(data["_id"])
        return cls(**data)

class UserInDB(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    first_name: str
    phone: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_admin: Optional[bool] = False
    
    @classmethod
    def from_mongo(cls, data: dict) -> "UserInDB":
        """Convert MongoDB document to Pydantic model"""
        if data.get("_id"):
            data["_id"] = str(data["_id"])
        return cls(**data)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
