import sys
import os
import pytest
from fastapi.testclient import TestClient
import src.main
from src.main import app
import importlib

@pytest.fixture
def client():
    # Use a unique database for each test to ensure isolation
    temp_db = f"test_tasks_{os.urandom(4).hex()}.db"
    
    # Backup original DB_NAME
    old_db = src.main.DB_NAME
    src.main.DB_NAME = temp_db
    
    # Initialize
    if os.path.exists(temp_db):
        os.remove(temp_db)
    src.main.init_db()
    
    # Provide the client with auth
    client = TestClient(app)
    client.auth = ("admin", "password123")
    
    yield client, temp_db
    
    # Cleanup
    if os.path.exists(temp_db):
        os.remove(temp_db)
    src.main.DB_NAME = old_db

def test_create_task(client):
    c, _ = client
    response = c.post("/tasks", json={"title": "Test Task", "status": "pending"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data

def test_create_task_without_title(client):
    c, _ = client
    response = c.post("/tasks", json={"status": "pending"})
    assert response.status_code == 422

def test_create_task_with_invalid_status(client):
    c, _ = client
    response = c.post("/tasks", json={"title": "Test Task", "status": "invalid"})
    assert response.status_code == 422

def test_authentication_failure(client):
    c, _ = client
    c.auth = ("invalid", "credentials")
    response = c.post("/tasks", json={"title": "Test Task", "status": "pending"})
    assert response.status_code == 401

def test_get_task_by_id_success(client):
    c, _ = client
    # Create
    create_res = c.post("/tasks", json={"title": "Find Me", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Get
    get_res = c.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["title"] == "Find Me"
    assert data["id"] == task_id

def test_get_task_by_id_not_found(client):
    c, _ = client
    # Get non-existent
    get_res = c.get("/tasks/9999")
    assert get_res.status_code == 404

def test_update_task_not_found(client):
    c, _ = client
    # PUT non-existent
    update_res = c.put("/tasks/9999", json={"title": "New Title"})
    assert update_res.status_code == 404

def test_persistence_across_app_restarts(client):
    c, db_file = client
    # 1. Create a task
    response = c.post("/tasks", json={"title": "Persistence Test", "status": "pending"})
    task_id = response.json()["id"]
    
    # 2. Reload/Simulate restart by re-instantiating the client
    # The database file remains the same.
    new_client = TestClient(app)
    new_client.auth = ("admin", "password123")
    
    # 3. Retrieve the task
    get_res = new_client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Persistence Test"

def test_update_task_validation(client):
    c, _ = client
    # Setup
    create_res = c.post("/tasks", json={"title": "Task Update Test", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Test valid update
    update_res = c.put(f"/tasks/{task_id}", json={"title": "New Title"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "New Title"

def test_list_tasks(client):
    c, _ = client
    c.post("/tasks", json={"title": "Task 1", "status": "pending"})
    c.post("/tasks", json={"title": "Task 2", "status": "pending"})
    
    get_res = c.get("/tasks")
    assert get_res.status_code == 200
    tasks = get_res.json()
    assert len(tasks) >= 2
    assert any(task["title"] == "Task 1" for task in tasks)
    assert any(task["title"] == "Task 2" for task in tasks)