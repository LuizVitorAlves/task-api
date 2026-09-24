import sqlite3
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from fastapi import FastAPI, HTTPException, Response
from src.schemas import TaskUpdate, TaskStatus

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: TaskStatus

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING

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

@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
        (task.title, task.description, task.status)
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {**task.model_dump(), "id": task_id}

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [dict(t) for t in tasks]

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(task)

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate):
    # Validation
    if task_update.title is not None and len(task_update.title.strip()) == 0:
        raise HTTPException(status_code=422, detail="Title cannot be empty")
    if "title" in task_update.model_dump(exclude_unset=True) and task_update.title is None:
        raise HTTPException(status_code=422, detail="Title cannot be set to null")

    conn = get_db()
    # Check if exists
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Filter out None values
    update_data = {k: v for k, v in task_update.model_dump(exclude_unset=True).items() if v is not None}
    
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

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
