import sys
import os
import pytest
import sqlite3
from fastapi.testclient import TestClient
import src.main
from src.main import app

@pytest.fixture
def test_db():
    temp_db = "test_tasks.db"
    
    # Backup original DB_NAME
    old_db = src.main.DB_NAME
    src.main.DB_NAME = temp_db
    
    # Initialize
    if os.path.exists(temp_db):
        os.remove(temp_db)
    src.main.init_db()
    
    yield temp_db
    
    # Cleanup
    if os.path.exists(temp_db):
        os.remove(temp_db)
    src.main.DB_NAME = old_db

client = TestClient(app)

def test_create_task(test_db):
    response = client.post("/tasks", json={"title": "Test Task", "status": "pending"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data

def test_get_task_by_id_success(test_db):
    # Create
    create_res = client.post("/tasks", json={"title": "Find Me", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Get
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["title"] == "Find Me"
    assert data["id"] == task_id

def test_get_task_by_id_not_found(test_db):
    # Get non-existent
    get_res = client.get("/tasks/9999")
    assert get_res.status_code == 404

def test_update_task_not_found(test_db):
    # PUT non-existent
    update_res = client.put("/tasks/9999", json={"title": "New Title"})
    assert update_res.status_code == 404

def test_persistence_across_app_restarts(test_db):
    # 1. Create a task
    response = client.post("/tasks", json={"title": "Persistence Test", "status": "pending"})
    task_id = response.json()["id"]
    
    # 2. Verify it is still in the DB
    conn = sqlite3.connect(test_db)
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    assert task is not None
    assert task[1] == "Persistence Test"
    conn.close()

def test_update_task_validation(test_db):
    # Setup
    create_res = client.post("/tasks", json={"title": "Task Update Test", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Test valid update
    update_res = client.put(f"/tasks/{task_id}", json={"title": "New Title"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "New Title"

def test_delete_task(test_db):
    create_res = client.post("/tasks", json={"title": "Task Delete Test", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Delete
    del_res = client.delete(f"/tasks/{task_id}")
    assert del_res.status_code == 204
    
    # Verify deletion
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 404
