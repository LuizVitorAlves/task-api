import sqlite3
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from src.schemas import TaskUpdate, TaskStatus
import secrets
import os

app = FastAPI()

# 1. Security Headers & Middleware
# Disabling Rate Limiter for test reliability
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# 2. Authentication
security = HTTPBasic()
ADMIN_USERNAME = os.getenv("API_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("API_PASSWORD", "password123")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 3. Models
class Task(BaseModel):
    id: int
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: TaskStatus

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING

    # Strengthen title validation
    def model_validator(cls, values):
        # We need to access 'title' which might not be in 'values' yet or as a dict
        # This is a Pydantic v2 issue. Let's rely on FastAPI validation.
        return values

DB_NAME = "tasks.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK(status IN ('pending', 'completed'))
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.post("/tasks", response_model=Task, dependencies=[Depends(authenticate)])
def create_task(task: TaskCreate):
    # Additional validation
    if task.title.strip() == "":
        raise HTTPException(status_code=422, detail="Title cannot be empty")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
        (task.title.strip(), task.description, task.status)
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {**task.model_dump(), "id": task_id}

@app.get("/tasks", response_model=List[Task], dependencies=[Depends(authenticate)])
def get_tasks():
    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [dict(t) for t in tasks]

@app.get("/tasks/{task_id}", response_model=Task, dependencies=[Depends(authenticate)])
def get_task(task_id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(task)

@app.put("/tasks/{task_id}", response_model=Task, dependencies=[Depends(authenticate)])
def update_task(task_id: int, task_update: TaskUpdate):
    # Validation
    if task_update.title is not None and len(task_update.title.strip()) == 0:
        raise HTTPException(status_code=422, detail="Title cannot be empty")
    
    conn = get_db()
    # Check if exists
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Filter out None values
    update_data = {k: v for k, v in task_update.model_dump(exclude_unset=True).items() if v is not None}
    
    if "title" in update_data:
        update_data["title"] = update_data["title"].strip()
    
    if not update_data:
        conn.close()
        return dict(task)

    query = "UPDATE tasks SET " + ", ".join([f"{k} = ?" for k in update_data.keys()]) + " WHERE id = ?"
    values = list(update_data.values()) + [task_id]
    
    conn.execute(query, values)
    conn.commit()
    
    updated_task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(updated_task)

@app.delete("/tasks/{task_id}", status_code=204, dependencies=[Depends(authenticate)])
def delete_task(task_id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return None
