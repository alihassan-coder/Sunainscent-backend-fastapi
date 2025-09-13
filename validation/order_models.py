from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """Individual item in an order"""
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name at time of order")
    price: float = Field(..., gt=0, description="Price per item at time of order")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    
    @property
    def subtotal(self) -> float:
        return self.price * self.quantity


class ShippingAddress(BaseModel):
    """Shipping address information"""
    full_name: str = Field(..., min_length=2, max_length=100)
    street_address: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class OrderCreate(BaseModel):
    """Model for creating a new order"""
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_name: str = Field(..., min_length=2, max_length=100, description="Customer full name")
    items: List[OrderItem] = Field(..., min_items=1, description="List of items in the order")
    shipping_address: ShippingAddress = Field(..., description="Shipping address")
    notes: Optional[str] = Field(None, max_length=500, description="Order notes")
    
    @property
    def total_amount(self) -> float:
        return sum(item.subtotal for item in self.items)
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "items": [
                    {
                        "product_id": "64f8b123456789abcdef0123",
                        "product_name": "Premium Scent",
                        "price": 29.99,
                        "quantity": 2
                    }
                ],
                "shipping_address": {
                    "full_name": "John Doe",
                    "street_address": "123 Main St, Apt 4B",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA",
                    "phone": "+1234567890"
                },
                "notes": "Please handle with care"
            }
        }


class OrderResponse(BaseModel):
    """Response model for orders"""
    id: str = Field(..., description="Unique order identifier")
    order_number: str = Field(..., description="Human-readable order number")
    customer_email: str
    customer_name: str
    items: List[OrderItem]
    shipping_address: ShippingAddress
    status: OrderStatus
    total_amount: float
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_mongo(cls, order_doc):
        """Convert MongoDB document to OrderResponse"""
        return cls(
            id=str(order_doc["_id"]),
            order_number=order_doc["order_number"],
            customer_email=order_doc["customer_email"],
            customer_name=order_doc["customer_name"],
            items=order_doc["items"],
            shipping_address=order_doc["shipping_address"],
            status=order_doc["status"],
            total_amount=order_doc["total_amount"],
            notes=order_doc.get("notes"),
            admin_notes=order_doc.get("admin_notes"),
            created_at=order_doc["created_at"],
            updated_at=order_doc["updated_at"]
        )


class OrderUpdate(BaseModel):
    """Model for updating order (admin only)"""
    status: Optional[OrderStatus] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)


class OrderStats(BaseModel):
    """Statistics model for orders"""
    total_orders: int
    pending_orders: int
    orders_today: int
    orders_this_week: int
    total_revenue: float
    revenue_this_month: float