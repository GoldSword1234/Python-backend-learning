from fastapi import APIRouter, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/examples",
    tags=["examples"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models for request/response
class Task(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: bool = False
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    created_at: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")

# In-memory storage
tasks_db: List[Task] = []
task_counter = 0

# 1. Basic GET endpoint
@router.get("/", summary="Welcome to examples")
async def get_examples():
    """Get information about available example endpoints."""
    return {
        "message": "Example endpoints",
        "endpoints": {
            "tasks": "/api/v1/examples/tasks",
            "search": "/api/v1/examples/search",
            "upload": "/api/v1/examples/upload",
            "batch": "/api/v1/examples/batch"
        }
    }

# 2. GET with path parameters
@router.get("/tasks/{task_id}", response_model=Task, summary="Get task by ID")
async def get_task(
    task_id: int = Path(..., description="The ID of the task to retrieve", ge=1)
):
    """Get a specific task by ID."""
    task = next((t for t in tasks_db if t.id == task_id), None)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    return task

# 3. GET with query parameters
@router.get("/tasks", response_model=List[Task], summary="Get all tasks")
async def get_tasks(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(10, description="Maximum number of tasks to return", ge=1, le=100),
    offset: int = Query(0, description="Number of tasks to skip", ge=0)
):
    """Get all tasks with optional filtering and pagination."""
    filtered_tasks = tasks_db.copy()
    
    if completed is not None:
        filtered_tasks = [t for t in filtered_tasks if t.completed == completed]
    
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.priority == priority]
    
    # Apply pagination
    paginated_tasks = filtered_tasks[offset:offset + limit]
    
    return paginated_tasks

# 4. POST endpoint with Pydantic model
@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, summary="Create new task")
async def create_task(task: Task):
    """Create a new task."""
    global task_counter
    task_counter += 1
    
    new_task = Task(
        id=task_counter,
        title=task.title,
        description=task.description,
        completed=task.completed,
        priority=task.priority,
        created_at=datetime.now()
    )
    
    tasks_db.append(new_task)
    logger.info(f"Created task with ID: {task_counter}")
    
    return new_task

# 5. PUT endpoint for full updates
@router.put("/tasks/{task_id}", response_model=Task, summary="Update entire task")
async def update_task(
    task_id: int = Path(..., description="The ID of the task to update", ge=1),
    task_update: Task = Body(..., description="Updated task data")
):
    """Update an entire task."""
    task_index = next((i for i, t in enumerate(tasks_db) if t.id == task_id), None)
    
    if task_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # Keep original ID and created_at
    original_task = tasks_db[task_index]
    task_update.id = original_task.id
    task_update.created_at = original_task.created_at
    
    tasks_db[task_index] = task_update
    logger.info(f"Updated task with ID: {task_id}")
    
    return task_update

# 6. PATCH endpoint for partial updates
@router.patch("/tasks/{task_id}", response_model=Task, summary="Partially update task")
async def patch_task(
    task_id: int = Path(..., description="The ID of the task to update", ge=1),
    task_update: TaskUpdate = Body(..., description="Partial task update data")
):
    """Partially update a task."""
    task_index = next((i for i, t in enumerate(tasks_db) if t.id == task_id), None)
    
    if task_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # Update only provided fields
    current_task = tasks_db[task_index]
    update_data = task_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_task, field, value)
    
    logger.info(f"Partially updated task with ID: {task_id}")
    return current_task

# 7. DELETE endpoint
@router.delete("/tasks/{task_id}", summary="Delete task")
async def delete_task(
    task_id: int = Path(..., description="The ID of the task to delete", ge=1)
):
    """Delete a task."""
    task_index = next((i for i, t in enumerate(tasks_db) if t.id == task_id), None)
    
    if task_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    deleted_task = tasks_db.pop(task_index)
    logger.info(f"Deleted task with ID: {task_id}")
    
    return {"message": "Task deleted successfully", "deleted_task": deleted_task}

# 8. POST endpoint with multiple body parameters
@router.post("/batch", summary="Create multiple tasks")
async def create_batch_tasks(
    tasks: List[Task] = Body(..., description="List of tasks to create"),
    notify: bool = Body(False, description="Whether to send notifications")
):
    """Create multiple tasks at once."""
    global task_counter
    created_tasks = []
    
    for task in tasks:
        task_counter += 1
        new_task = Task(
            id=task_counter,
            title=task.title,
            description=task.description,
            completed=task.completed,
            priority=task.priority,
            created_at=datetime.now()
        )
        tasks_db.append(new_task)
        created_tasks.append(new_task)
    
    logger.info(f"Created {len(created_tasks)} tasks in batch")
    
    response = {
        "message": f"Created {len(created_tasks)} tasks successfully",
        "tasks": created_tasks,
        "notification_sent": notify
    }
    
    return response

# 9. GET endpoint that returns different status codes
@router.get("/search", summary="Search tasks")
async def search_tasks(
    q: str = Query(..., description="Search query", min_length=1),
    in_title: bool = Query(True, description="Search in task titles"),
    in_description: bool = Query(True, description="Search in task descriptions")
):
    """Search for tasks by query string."""
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    results = []
    query_lower = q.lower()
    
    for task in tasks_db:
        match = False
        if in_title and task.title and query_lower in task.title.lower():
            match = True
        if in_description and task.description and query_lower in task.description.lower():
            match = True
        
        if match:
            results.append(task)
    
    if not results:
        return {
            "message": "No tasks found matching your search",
            "query": q,
            "results": []
        }
    
    return {
        "message": f"Found {len(results)} matching tasks",
        "query": q,
        "results": results
    }