from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    image_url: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    stock_quantity: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_mongo(cls, data: dict) -> "ProductResponse":
        """Convert MongoDB document to Pydantic model"""
        if data.get("_id"):
            data["_id"] = str(data["_id"])
        return cls(**data)

class ProductInDB(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    stock_quantity: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_mongo(cls, data: dict) -> "ProductInDB":
        """Convert MongoDB document to Pydantic model"""
        if data.get("_id"):
            data["_id"] = str(data["_id"])
        return cls(**data)
