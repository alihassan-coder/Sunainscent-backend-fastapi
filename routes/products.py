from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from config.database import get_database
from validation.product_models import ProductCreate, ProductUpdate, ProductResponse
from validation.user_models import UserInDB
from utils.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Create a new product (requires authentication)"""
    
    product_doc = {
        **product.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.products.insert_one(product_doc)
    created_product = await db.products.find_one({"_id": result.inserted_id})
    
    return ProductResponse.from_mongo(created_product)

@router.get("/", response_model=List[ProductResponse])
async def get_all_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db = Depends(get_database)
):
    """Get all active products (public endpoint)"""
    
    # Build query
    query = {"is_active": True}
    
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Execute query
    cursor = db.products.find(query).skip(skip).limit(limit).sort("created_at", -1)
    products = await cursor.to_list(length=limit)
    
    return [ProductResponse.from_mongo(product) for product in products]

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db = Depends(get_database)):
    """Get a specific product by ID (public endpoint)"""
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    product = await db.products.find_one({
        "_id": ObjectId(product_id),
        "is_active": True
    })
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse.from_mongo(product)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update a product (requires authentication)"""
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    # Get existing product
    existing_product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update only provided fields
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_data}
    )
    
    # Return updated product
    updated_product = await db.products.find_one({"_id": ObjectId(product_id)})
    return ProductResponse.from_mongo(updated_product)

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete a product (soft delete by setting is_active to False)"""
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    result = await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"message": "Product deleted successfully"}

@router.get("/categories/list")
async def get_categories(db = Depends(get_database)):
    """Get all unique product categories"""
    
    categories = await db.products.distinct("category", {"is_active": True})
    return {"categories": categories}