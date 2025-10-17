from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any
import logging

from ..security import get_current_user

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)

# In-memory storage for demo purposes (replace with database later)
products_db = [
    {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
    {"id": 2, "name": "Coffee Mug", "price": 12.99, "category": "Home"},
    {"id": 3, "name": "Book", "price": 24.99, "category": "Education"},
]

@router.get("/", summary="Get all products")
async def get_products(
    category: str = Query(None, description="Filter by category"),
    min_price: float = Query(None, description="Minimum price filter"),
    max_price: float = Query(None, description="Maximum price filter"),
    current_user: dict = Depends(get_current_user)
):
    """Get all products with optional filtering."""
    filtered_products = products_db.copy()
    
    if category:
        filtered_products = [p for p in filtered_products if p["category"].lower() == category.lower()]
    
    if min_price is not None:
        filtered_products = [p for p in filtered_products if p["price"] >= min_price]
    
    if max_price is not None:
        filtered_products = [p for p in filtered_products if p["price"] <= max_price]
    
    return {"products": filtered_products, "count": len(filtered_products)}

@router.get("/{product_id}", summary="Get product by ID")
async def get_product(
    product_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific product by ID."""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", summary="Create a new product")
async def create_product(
    product: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Create a new product."""
    # Generate new ID
    new_id = max([p["id"] for p in products_db], default=0) + 1
    
    new_product = {
        "id": new_id,
        "name": product.get("name", ""),
        "price": product.get("price", 0.0),
        "category": product.get("category", "")
    }
    
    products_db.append(new_product)
    logger.info(f"Created product with ID: {new_id}")
    
    return new_product

@router.put("/{product_id}", summary="Update product by ID")
async def update_product(
    product_id: int, 
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Update a product by ID."""
    product_index = next((i for i, p in enumerate(products_db) if p["id"] == product_id), None)
    
    if product_index is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update the product
    for key, value in updates.items():
        if key in ["name", "price", "category"]:
            products_db[product_index][key] = value
    
    logger.info(f"Updated product with ID: {product_id}")
    return products_db[product_index]

@router.delete("/{product_id}", summary="Delete product by ID")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a product by ID."""
    product_index = next((i for i, p in enumerate(products_db) if p["id"] == product_id), None)
    
    if product_index is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    deleted_product = products_db.pop(product_index)
    logger.info(f"Deleted product with ID: {product_id}")
    
    return {"message": "Product deleted successfully", "deleted_product": deleted_product}