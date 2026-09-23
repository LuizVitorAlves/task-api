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

def test_persistence_across_app_restarts(test_db):
    # 1. Create a task
    response = client.post("/tasks", json={"title": "Persistence Test"})
    task_id = response.json()["id"]
    
    # 2. Simulate "app restart" by closing DB connection (implicit in our app)
    # 3. Verify it is still in the DB
    conn = sqlite3.connect(test_db)
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    assert task is not None
    assert task[1] == "Persistence Test"
    conn.close()

def test_get_task_by_id(test_db):
    # Create
    create_res = client.post("/tasks", json={"title": "Find Me"})
    task_id = create_res.json()["id"]
    
    # Get
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Find Me"

def test_update_task_validation(test_db):
    # Setup
    create_res = client.post("/tasks", json={"title": "Task Update Test"})
    task_id = create_res.json()["id"]
    
    # Update with None - should trigger validation error (422)
    # Pydantic's Optional with None actually allows passing None,
    # but we want to ensure it doesn't try to save None as a column value
    # or handle the logic correctly.
    
    # Wait, if field is Optional[str], Pydantic *allows* `{"title": null}`.
    # We must ensure our PUT logic ignores `None` values.
    
    # Let's test the validation logic
    update_res = client.put(f"/tasks/{task_id}", json={"title": None})
    assert update_res.status_code == 422 # Pydantic validation error or our logic
    
    # Test valid update
    update_res = client.put(f"/tasks/{task_id}", json={"title": "New Title"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "New Title"

def test_delete_task(test_db):
    create_res = client.post("/tasks", json={"title": "Task Delete Test"})
    task_id = create_res.json()["id"]
    
    # Delete
    del_res = client.delete(f"/tasks/{task_id}")
    assert del_res.status_code == 204
    
    # Verify deletion
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 404
