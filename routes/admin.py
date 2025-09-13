from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from datetime import datetime, timedelta
from config.database import get_database
from validation.user_models import UserCreate, Token, UserInDB
from validation.contact_models import ContactStats
from validation.order_models import OrderStats
from validation.product_models import ProductResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/verify")
async def verify_admin_access(current_user: UserInDB = Depends(get_current_user)):
    """Verify admin access"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "message": "Admin access verified",
        "admin_email": current_user.email,
        "is_admin": current_user.is_admin
    }


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive dashboard statistics"""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get current time references
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = now - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1)
    
    # Product statistics
    total_products = await db.products.count_documents({"is_active": True})
    inactive_products = await db.products.count_documents({"is_active": False})
    
    # Order statistics
    total_orders = await db.orders.count_documents({})
    pending_orders = await db.orders.count_documents({"status": "pending"})
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
    
    monthly_revenue_pipeline = [
        {"$match": {"created_at": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
    ]
    monthly_revenue_result = await db.orders.aggregate(monthly_revenue_pipeline).to_list(1)
    revenue_this_month = monthly_revenue_result[0]["total"] if monthly_revenue_result else 0.0
    
    # Contact message statistics
    total_messages = await db.contact_messages.count_documents({})
    unread_messages = await db.contact_messages.count_documents({"is_read": False})
    messages_today = await db.contact_messages.count_documents({
        "created_at": {"$gte": today_start}
    })
    messages_this_week = await db.contact_messages.count_documents({
        "created_at": {"$gte": week_start}
    })
    
    # User statistics
    total_users = await db.users.count_documents({})
    users_today = await db.users.count_documents({
        "created_at": {"$gte": today_start}
    })
    users_this_week = await db.users.count_documents({
        "created_at": {"$gte": week_start}
    })
    
    # Recent activity - get latest orders and messages
    recent_orders = await db.orders.find({}).sort("created_at", -1).limit(5).to_list(5)
    recent_messages = await db.contact_messages.find({}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "overview": {
            "total_products": total_products,
            "inactive_products": inactive_products,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_users": total_users,
            "total_messages": total_messages,
            "unread_messages": unread_messages
        },
        "revenue": {
            "total_revenue": total_revenue,
            "revenue_this_month": revenue_this_month
        },
        "recent_activity": {
            "orders_today": orders_today,
            "orders_this_week": orders_this_week,
            "messages_today": messages_today,
            "messages_this_week": messages_this_week,
            "users_today": users_today,
            "users_this_week": users_this_week
        },
        "recent_orders": [
            {
                "id": str(order["_id"]),
                "order_number": order["order_number"],
                "customer_name": order["customer_name"],
                "customer_email": order["customer_email"],
                "total_amount": order["total_amount"],
                "status": order["status"],
                "created_at": order["created_at"]
            } for order in recent_orders
        ],
        "recent_messages": [
            {
                "id": str(msg["_id"]),
                "name": msg["name"],
                "email": msg["email"],
                "subject": msg["subject"],
                "is_read": msg.get("is_read", False),
                "created_at": msg["created_at"]
            } for msg in recent_messages
        ]
    }


@router.get("/products/stats")
async def get_product_stats(
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed product statistics"""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    total_products = await db.products.count_documents({"is_active": True})
    inactive_products = await db.products.count_documents({"is_active": False})
    
    # Get products by category
    category_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories = await db.products.aggregate(category_pipeline).to_list(100)
    
    # Get low stock products (assuming stock field exists)
    low_stock_pipeline = [
        {"$match": {"is_active": True, "stock": {"$lt": 10}}},
        {"$sort": {"stock": 1}},
        {"$limit": 10}
    ]
    low_stock = await db.products.aggregate(low_stock_pipeline).to_list(10)
    
    return {
        "total_active": total_products,
        "total_inactive": inactive_products,
        "categories": categories,
        "low_stock_products": [
            {
                "id": str(product["_id"]),
                "name": product["name"],
                "stock": product.get("stock", 0),
                "price": product["price"]
            } for product in low_stock
        ]
    }


@router.get("/users/stats")
async def get_user_stats(
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get user statistics"""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = now - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1)
    
    total_users = await db.users.count_documents({})
    users_today = await db.users.count_documents({
        "created_at": {"$gte": today_start}
    })
    users_this_week = await db.users.count_documents({
        "created_at": {"$gte": week_start}
    })
    users_this_month = await db.users.count_documents({
        "created_at": {"$gte": month_start}
    })
    
    # Get recent users
    recent_users = await db.users.find({}).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "total_users": total_users,
        "users_today": users_today,
        "users_this_week": users_this_week,
        "users_this_month": users_this_month,
        "recent_users": [
            {
                "id": str(user["_id"]),
                "email": user["email"],
                "first_name": user["first_name"],
                "created_at": user["created_at"]
            } for user in recent_users
        ]
    }


@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get analytics summary for charts and graphs"""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get last 30 days of orders and revenue
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_orders_pipeline = [
        {"$match": {"created_at": {"$gte": thirty_days_ago}}},
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"}, 
                    "day": {"$dayOfMonth": "$created_at"}
                },
                "orders": {"$sum": 1},
                "revenue": {"$sum": "$total_amount"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    daily_stats = await db.orders.aggregate(daily_orders_pipeline).to_list(100)
    
    # Get order status distribution
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    status_distribution = await db.orders.aggregate(status_pipeline).to_list(100)
    
    # Get top products by orders
    top_products_pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_name",
                "total_quantity": {"$sum": "$items.quantity"},
                "total_revenue": {"$sum": {"$multiply": ["$items.price", "$items.quantity"]}}
            }
        },
        {"$sort": {"total_quantity": -1}},
        {"$limit": 10}
    ]
    top_products = await db.orders.aggregate(top_products_pipeline).to_list(10)
    
    return {
        "daily_stats": [
            {
                "date": f"{stat['_id']['year']}-{stat['_id']['month']:02d}-{stat['_id']['day']:02d}",
                "orders": stat["orders"],
                "revenue": stat["revenue"]
            } for stat in daily_stats
        ],
        "order_status_distribution": status_distribution,
        "top_products": top_products
    }