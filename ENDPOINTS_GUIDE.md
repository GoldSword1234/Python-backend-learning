# How to Add Endpoints to Your FastAPI Backend

Your FastAPI backend is now running successfully! Here are all the different ways you can add endpoints:

## 🚀 Server is Running
- **URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📍 Available Endpoints

### 1. **Main App Endpoints** (defined in `main.py`)
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /hello/{name}` - Example greeting endpoint
- `POST /echo` - Example echo endpoint

### 2. **Users Endpoints** (PostgreSQL database)
- `GET /api/v1/users/` - Get all users with pagination
- `GET /api/v1/users/{user_id}` - Get user by ID
- `POST /api/v1/users/` - Create new user
- `PUT /api/v1/users/{user_id}` - Update user

### 3. **Products Endpoints** (in-memory storage)
- `GET /api/v1/products/` - Get all products with filtering
- `GET /api/v1/products/{product_id}` - Get product by ID
- `POST /api/v1/products/` - Create new product
- `PUT /api/v1/products/{product_id}` - Update product
- `DELETE /api/v1/products/{product_id}` - Delete product

### 4. **Examples/Tasks Endpoints** (comprehensive examples)
- `GET /api/v1/examples/` - Overview of example endpoints
- `GET /api/v1/examples/tasks` - Get tasks with filtering and pagination
- `GET /api/v1/examples/tasks/{task_id}` - Get task by ID
- `POST /api/v1/examples/tasks` - Create new task
- `PUT /api/v1/examples/tasks/{task_id}` - Update entire task
- `PATCH /api/v1/examples/tasks/{task_id}` - Partially update task
- `DELETE /api/v1/examples/tasks/{task_id}` - Delete task
- `POST /api/v1/examples/batch` - Create multiple tasks
- `GET /api/v1/examples/search` - Search tasks

## 🛠️ How to Add New Endpoints

### Method 1: Add to Main App (Quick & Simple)

Add directly to `app/main.py`:

```python
@app.get("/your-endpoint")
async def your_function():
    return {"message": "Hello from your endpoint"}

@app.post("/data")
async def receive_data(data: dict):
    return {"received": data}
```

### Method 2: Create New Router File (Recommended)

1. **Create a new router file** (e.g., `app/routers/your_feature.py`):

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/your-feature",
    tags=["your-feature"],
)

class YourModel(BaseModel):
    name: str
    value: int

@router.get("/")
async def get_items():
    return {"items": []}

@router.post("/")
async def create_item(item: YourModel):
    return {"created": item}
```

2. **Import and include in `main.py`**:

```python
from .routers import your_feature

app.include_router(your_feature.router, prefix="/api/v1")
```

### Method 3: Extend Existing Routers

Add new endpoints to existing router files like `users.py`, `products.py`, or `examples.py`.

## 📊 Endpoint Examples by HTTP Method

### GET Endpoints
```python
# Simple GET
@router.get("/items")
async def get_items():
    return {"items": []}

# GET with path parameter
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

# GET with query parameters
@router.get("/search")
async def search(q: str, limit: int = 10):
    return {"query": q, "limit": limit}
```

### POST Endpoints
```python
# POST with JSON body
@router.post("/items")
async def create_item(item: dict):
    return {"created": item}

# POST with Pydantic model
class Item(BaseModel):
    name: str
    price: float

@router.post("/items-typed")
async def create_typed_item(item: Item):
    return {"created": item}
```

### PUT/PATCH/DELETE Endpoints
```python
# PUT (full update)
@router.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"updated": item_id, "data": item}

# PATCH (partial update)
@router.patch("/items/{item_id}")
async def patch_item(item_id: int, updates: dict):
    return {"patched": item_id, "updates": updates}

# DELETE
@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"deleted": item_id}
```

## 🔧 Advanced Features

### 1. Request Validation with Pydantic
```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)
```

### 2. Query Parameters with Validation
```python
from fastapi import Query

@router.get("/items")
async def get_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: str = Query(None, description="Filter by category")
):
    return {"skip": skip, "limit": limit, "category": category}
```

### 3. Path Parameters with Validation
```python
from fastapi import Path

@router.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(..., description="The ID of the item", ge=1)
):
    return {"item_id": item_id}
```

### 4. Response Models
```python
class ItemResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    return ItemResponse(id=item_id, name="Example", created_at=datetime.now())
```

### 5. Error Handling
```python
from fastapi import HTTPException, status

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id > 1000:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return {"item_id": item_id}
```

## 🧪 Test Your Endpoints

1. **Visit the interactive docs**: http://localhost:8000/docs
2. **Try the endpoints manually**:
   ```bash
   # Test GET
   curl http://localhost:8000/health
   
   # Test POST
   curl -X POST http://localhost:8000/api/v1/products/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Product", "price": 29.99, "category": "Test"}'
   ```

3. **Use the browser** for GET endpoints:
   - http://localhost:8000/hello/YourName
   - http://localhost:8000/api/v1/products/

## 📁 File Structure
```
app/
├── __init__.py
├── main.py              # Main FastAPI app + simple endpoints
├── database.py          # Database configuration
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic schemas
├── crud.py             # Database operations
└── routers/
    ├── __init__.py
    ├── users.py        # User endpoints (with database)
    ├── products.py     # Product endpoints (in-memory)
    └── examples.py     # Comprehensive examples
```

Your API is now fully functional with comprehensive examples of all endpoint types! 🎉