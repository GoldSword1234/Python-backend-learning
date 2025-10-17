from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")
    bio: Optional[str] = Field(None, max_length=1000, description="User's biography")

class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass

class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    email: Optional[str] = Field(None, description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")
    bio: Optional[str] = Field(None, max_length=1000, description="User's biography")

class User(UserBase):
    """Schema for returning user data."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")

class UserList(BaseModel):
    """Schema for returning a list of users."""
    users: list[User]

    total: int = Field(..., description="Total number of users")

class UserSummary(BaseModel):
    """Schema for returning basic user data (id, name, email only)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's full name")
    age: Optional[int] = Field(None, description="User's age")
    bio: Optional[str] = Field(None, description="User's biography")
    email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")

class UserSummaryList(BaseModel):
    """Schema for returning a list of basic user data."""
    users: list[UserSummary]

    
    total: int = Field(..., description="Total number of users")


class UserCreateResponse(BaseModel):
    """Schema for user creation response with custom field order."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    age: Optional[int] = Field(None, description="User's age")
    bio: Optional[str] = Field(None, description="User's biography")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")

# Authentication schemas
class UserLogin(BaseModel):
    """Schema for user login."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")

class UserRegister(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")
    bio: Optional[str] = Field(None, max_length=1000, description="User's biography")

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class TokenData(BaseModel):
    """Schema for token data."""
    email: Optional[str] = None

# Product schemas
class ProductBase(BaseModel):
    """Base product schema with common fields."""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")
    price: float = Field(..., gt=0, description="Product price in dollars")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass

class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")
    price: Optional[float] = Field(None, gt=0, description="Product price in dollars")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    in_stock: Optional[bool] = Field(None, description="Whether product is in stock")

class Product(ProductBase):
    """Schema for returning product data."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Product's unique identifier")
    created_at: datetime = Field(..., description="When the product was created")
    updated_at: datetime = Field(..., description="When the product was last updated")

class ProductList(BaseModel):
    """Schema for returning a list of products."""
    products: list[Product]
    total: int = Field(..., description="Total number of products")