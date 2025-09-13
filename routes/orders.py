from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
from config.database import get_database
from validation.order_models import (
    OrderCreate, 
    OrderResponse, 
    OrderUpdate, 
    OrderStatus,
    OrderStats
)
from utils.auth import get_current_admin, get_current_user
from validation.user_models import UserInDB

router = APIRouter(prefix="/orders", tags=["Orders"])


def generate_order_number() -> str:
    """Generate a unique order number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(4).upper()
    return f"SUN-{timestamp}-{random_suffix}"


@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db = Depends(get_database)
):
    """Create a new order (public endpoint)"""
    
    # Generate order number
    order_number = generate_order_number()
    
    # Calculate total amount
    total_amount = sum(item.price * item.quantity for item in order.items)
    
    order_doc = {
        **order.dict(),
        "order_number": order_number,
        "total_amount": total_amount,
        "status": OrderStatus.PENDING,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "admin_notes": None
    }
    
    result = await db.orders.insert_one(order_doc)
    created_order = await db.orders.find_one({"_id": result.inserted_id})
    
    return OrderResponse.from_mongo(created_order)


@router.get("/", response_model=List[OrderResponse])
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    customer_email: Optional[str] = None,
    search: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Get all orders (admin only)"""
    
    # Build query
    query = {}
    
    if status:
        query["status"] = status
        
    if customer_email:
        query["customer_email"] = {"$regex": customer_email, "$options": "i"}
    
    if search:
        query["$or"] = [
            {"order_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"customer_email": {"$regex": search, "$options": "i"}},
            {"items.product_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Execute query
    cursor = db.orders.find(query).skip(skip).limit(limit).sort("created_at", -1)
    orders = await cursor.to_list(length=limit)
    
    return [OrderResponse.from_mongo(order) for order in orders]


@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get orders for the current authenticated user"""
    
    cursor = db.orders.find({
        "customer_email": current_user.email
    }).skip(skip).limit(limit).sort("created_at", -1)
    
    orders = await cursor.to_list(length=limit)
    
    return [OrderResponse.from_mongo(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str, 
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Get a specific order by ID (admin only)"""
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_mongo(order)


@router.get("/number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    db = Depends(get_database)
):
    """Get order by order number (public endpoint for order tracking)"""
    
    order = await db.orders.find_one({"order_number": order_number})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_mongo(order)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Update an order (admin only)"""
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    # Get existing order
    existing_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update only provided fields
    update_data = {k: v for k, v in order_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": update_data}
    )
    
    # Return updated order
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    return OrderResponse.from_mongo(updated_order)


@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Delete an order (admin only)"""
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    result = await db.orders.delete_one({"_id": ObjectId(order_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {"message": "Order deleted successfully"}


@router.get("/stats/overview", response_model=OrderStats)
async def get_order_stats(
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Get order statistics (admin only)"""
    
    # Get current time references
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = now - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1)
    
    # Basic counts
    total_orders = await db.orders.count_documents({})
    pending_orders = await db.orders.count_documents({"status": OrderStatus.PENDING})
    orders_today = await db.orders.count_documents({
        "created_at": {"$gte": today_start}
    })
    orders_this_week = await db.orders.count_documents({
        "created_at": {"$gte": week_start}
    })
    
    # Revenue calculations
    total_revenue_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
    ]
    total_revenue_result = await db.orders.aggregate(total_revenue_pipeline).to_list(1)
    total_revenue = total_revenue_result[0]["total"] if total_revenue_result else 0.0
    
    # Revenue this month
    monthly_revenue_pipeline = [
        {"$match": {"created_at": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
    ]
    monthly_revenue_result = await db.orders.aggregate(monthly_revenue_pipeline).to_list(1)
    revenue_this_month = monthly_revenue_result[0]["total"] if monthly_revenue_result else 0.0
    
    return OrderStats(
        total_orders=total_orders,
        pending_orders=pending_orders,
        orders_today=orders_today,
        orders_this_week=orders_this_week,
        total_revenue=total_revenue,
        revenue_this_month=revenue_this_month
    )


@router.post("/{order_id}/update-status")
async def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Update order status (admin only)"""
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    result = await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {"message": f"Order status updated to {new_status}"}


@router.get("/status/{status_type}")
async def get_orders_by_status(
    status_type: OrderStatus,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin),
    db = Depends(get_database)
):
    """Get orders by status (admin only)"""
    
    cursor = db.orders.find({
        "status": status_type
    }).skip(skip).limit(limit).sort("created_at", -1)
    
    orders = await cursor.to_list(length=limit)
    
    return {
        "status": status_type,
        "count": len(orders),
        "orders": [OrderResponse.from_mongo(order) for order in orders]
    }