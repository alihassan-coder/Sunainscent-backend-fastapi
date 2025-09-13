from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class ContactMessage(BaseModel):
    """Contact form submission model"""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the person")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    subject: str = Field(..., min_length=5, max_length=200, description="Subject of the message")
    message: str = Field(..., min_length=10, max_length=2000, description="The actual message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "subject": "Product Inquiry",
                "message": "I would like to know more about your products."
            }
        }


class ContactMessageResponse(BaseModel):
    """Response model for contact message"""
    id: str = Field(..., description="Unique identifier")
    name: str
    email: str
    phone: Optional[str]
    subject: str
    message: str
    created_at: datetime
    is_read: bool = False
    admin_notes: Optional[str] = None
    
    @classmethod
    def from_mongo(cls, contact_doc):
        """Convert MongoDB document to ContactMessageResponse"""
        return cls(
            id=str(contact_doc["_id"]),
            name=contact_doc["name"],
            email=contact_doc["email"],
            phone=contact_doc.get("phone"),
            subject=contact_doc["subject"],
            message=contact_doc["message"],
            created_at=contact_doc["created_at"],
            is_read=contact_doc.get("is_read", False),
            admin_notes=contact_doc.get("admin_notes")
        )


class ContactMessageUpdate(BaseModel):
    """Model for updating contact message (admin only)"""
    is_read: Optional[bool] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)


class ContactStats(BaseModel):
    """Statistics model for contact messages"""
    total_messages: int
    unread_messages: int
    messages_today: int
    messages_this_week: int