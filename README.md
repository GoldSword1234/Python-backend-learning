# Python Backend API

A RESTful API built with FastAPI and PostgreSQL, supporting GET, POST, and PUT operations.

## Features

- FastAPI framework for high performance
- PostgreSQL database integration with SQLAlchemy ORM
- CRUD operations (Create, Read, Update)
- Data validation with Pydantic models
- Database migrations with Alembic
- Environment configuration
- Error handling and logging

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd python-backendapi
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   copy .env.example .env
   # Edit .env with your PostgreSQL connection details
   ```

5. **Set up PostgreSQL database:**
   - Install PostgreSQL
   - Create a database
   - Update .env with your database credentials

6. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Start the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Users API

- `GET /users/` - Get all users
- `GET /users/{user_id}` - Get user by ID
- `POST /users/` - Create a new user
- `PUT /users/{user_id}` - Update user by ID

### Example Usage

```bash
# Get all users
curl -X GET "http://localhost:8000/users/"

# Get user by ID
curl -X GET "http://localhost:8000/users/1"

# Create new user
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "age": 30}'

# Update user
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith", "email": "johnsmith@example.com", "age": 31}'
```

## Interactive API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
python-backendapi/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── database.py       # Database configuration
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── crud.py          # Database operations
│   └── routers/
│       ├── __init__.py
│       └── users.py     # User endpoints
├── alembic/             # Database migrations
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```