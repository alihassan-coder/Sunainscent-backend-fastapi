from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from config.database import get_database
from validation.contact_models import (
    ContactMessage, 
    ContactMessageResponse, 
    ContactMessageUpdate,
    ContactStats
)
from utils.auth import get_current_admin

router = APIRouter(prefix="/contact", tags=["Contact"])


@router.post("/", response_model=dict)
async def submit_contact_message(
    contact: ContactMessage,
    db = Depends(get_database)
):
    """Submit a new contact message (public endpoint)"""
    
    contact_doc = {
        **contact.dict(),
        "created_at": datetime.utcnow(),
        "is_read": False,
        "admin_notes": None
    }
    
    result = await db.contact_messages.insert_one(contact_doc)
    
    return {
        "message": "Contact message submitted successfully",
        "id": str(result.inserted_id),
        "status": "success"
    }


@router.get("/messages", response_model=List[ContactMessageResponse])
async def get_all_contact_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_read: Optional[bool] = None,
    search: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Get all contact messages (admin only)"""
    
    # Build query
    query = {}
    
    if is_read is not None:
        query["is_read"] = is_read
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"subject": {"$regex": search, "$options": "i"}},
            {"message": {"$regex": search, "$options": "i"}}
        ]
    
    # Execute query
    cursor = db.contact_messages.find(query).skip(skip).limit(limit).sort("created_at", -1)
    messages = await cursor.to_list(length=limit)
    
    return [ContactMessageResponse.from_mongo(message) for message in messages]


@router.get("/messages/{message_id}", response_model=ContactMessageResponse)
async def get_contact_message(
    message_id: str,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Get a specific contact message by ID (admin only)"""
    
    if not ObjectId.is_valid(message_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID"
        )
    
    message = await db.contact_messages.find_one({"_id": ObjectId(message_id)})
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    
    return ContactMessageResponse.from_mongo(message)


@router.put("/messages/{message_id}", response_model=ContactMessageResponse)
async def update_contact_message(
    message_id: str,
    message_update: ContactMessageUpdate,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Update a contact message (admin only)"""
    
    if not ObjectId.is_valid(message_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID"
        )
    
    # Get existing message
    existing_message = await db.contact_messages.find_one({"_id": ObjectId(message_id)})
    if not existing_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    
    # Update only provided fields
    update_data = {k: v for k, v in message_update.dict().items() if v is not None}
    
    if update_data:
        await db.contact_messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": update_data}
        )
    
    # Return updated message
    updated_message = await db.contact_messages.find_one({"_id": ObjectId(message_id)})
    return ContactMessageResponse.from_mongo(updated_message)


@router.delete("/messages/{message_id}")
async def delete_contact_message(
    message_id: str,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Delete a contact message (admin only)"""
    
    if not ObjectId.is_valid(message_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID"
        )
    
    result = await db.contact_messages.delete_one({"_id": ObjectId(message_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    
    return {"message": "Contact message deleted successfully"}


@router.get("/stats", response_model=ContactStats)
async def get_contact_stats(
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Get contact message statistics (admin only)"""
    
    # Get current time references
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = now - timedelta(days=7)
    
    # Run aggregation queries
    total_messages = await db.contact_messages.count_documents({})
    unread_messages = await db.contact_messages.count_documents({"is_read": False})
    messages_today = await db.contact_messages.count_documents({
        "created_at": {"$gte": today_start}
    })
    messages_this_week = await db.contact_messages.count_documents({
        "created_at": {"$gte": week_start}
    })
    
    return ContactStats(
        total_messages=total_messages,
        unread_messages=unread_messages,
        messages_today=messages_today,
        messages_this_week=messages_this_week
    )


@router.post("/messages/{message_id}/mark-read")
async def mark_message_as_read(
    message_id: str,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Mark a contact message as read (admin only)"""
    
    if not ObjectId.is_valid(message_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID"
        )
    
    result = await db.contact_messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"is_read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    
    return {"message": "Message marked as read"}


@router.post("/messages/mark-all-read")
async def mark_all_messages_as_read(
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Mark all contact messages as read (admin only)"""
    
    result = await db.contact_messages.update_many(
        {"is_read": False},
        {"$set": {"is_read": True}}
    )
    
    return {
        "message": f"Marked {result.modified_count} messages as read",
        "modified_count": result.modified_count
    }