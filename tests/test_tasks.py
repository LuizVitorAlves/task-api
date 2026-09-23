import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import sqlite3
from fastapi.testclient import TestClient
from src.main import app, DB_NAME

@pytest.fixture(autouse=True)
def setup_db():
    # Use a temporary database for testing
    old_db = DB_NAME
    temp_db = "test_tasks.db"
    
    # We need to monkeypatch the DB_NAME in src.main
    import src.main
    src.main.DB_NAME = temp_db
    
    # Initialize
    src.main.init_db()
    
    yield
    
    # Cleanup
    if os.path.exists(temp_db):
        os.remove(temp_db)
    src.main.DB_NAME = old_db

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"title": "Test Task", "status": "pending"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data

def test_persistence_across_requests():
    # This test verifies that we can read back what we just wrote
    response = client.post("/tasks", json={"title": "Persistence Test"})
    task_id = response.json()["id"]
    
    # The client might be the same instance, but the DB is what matters.
    # To be sure, let's verify directly with sqlite
    conn = sqlite3.connect("test_tasks.db")
    conn.row_factory = sqlite3.Row
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    assert task is not None
    assert task["title"] == "Persistence Test"
    conn.close()

def test_get_tasks():
    client.post("/tasks", json={"title": "Task 1"})
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_update_task():
    # Setup
    create_res = client.post("/tasks", json={"title": "Task Update Test"})
    task_id = create_res.json()["id"]
    
    # Update
    update_res = client.put(f"/tasks/{task_id}", json={"title": "Updated Title", "status": "completed"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title"
    assert update_res.json()["status"] == "completed"

def test_delete_task():
    create_res = client.post("/tasks", json={"title": "Task Delete Test"})
    task_id = create_res.json()["id"]
    
    # Delete
    del_res = client.delete(f"/tasks/{task_id}")
    assert del_res.status_code == 204
    
    # Verify deletion
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 404

def test_validation():
    # Invalid status
    response = client.post("/tasks", json={"title": "Bad Status", "status": "invalid"})
    assert response.status_code == 422
    
    # Empty title
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422
