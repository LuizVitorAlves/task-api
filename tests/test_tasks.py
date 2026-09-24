import sys
import os
import pytest
from fastapi.testclient import TestClient
import src.main
from src.main import app

@pytest.fixture
def client():
    # Use a unique database for each test to ensure isolation
    temp_db = "test_tasks.db"
    
    # Backup original DB_NAME
    old_db = src.main.DB_NAME
    src.main.DB_NAME = temp_db
    
    # Initialize
    if os.path.exists(temp_db):
        os.remove(temp_db)
    src.main.init_db()
    
    # Provide the client
    yield TestClient(app)
    
    # Cleanup
    if os.path.exists(temp_db):
        os.remove(temp_db)
    src.main.DB_NAME = old_db

def test_create_task(client):
    response = client.post("/tasks", json={"title": "Test Task", "status": "pending"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data

def test_get_task_by_id_success(client):
    # Create
    create_res = client.post("/tasks", json={"title": "Find Me", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Get
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["title"] == "Find Me"
    assert data["id"] == task_id

def test_get_task_by_id_not_found(client):
    # Get non-existent
    get_res = client.get("/tasks/9999")
    assert get_res.status_code == 404

def test_update_task_not_found(client):
    # PUT non-existent
    update_res = client.put("/tasks/9999", json={"title": "New Title"})
    assert update_res.status_code == 404

def test_persistence_across_app_restarts(client):
    # 1. Create a task
    response = client.post("/tasks", json={"title": "Persistence Test", "status": "pending"})
    task_id = response.json()["id"]
    
    # 2. Simulate "app restart" by using the same client/app fixture,
    # as the fixture handles the DB lifecycle correctly.
    
    # 3. Retrieve the task
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Persistence Test"

def test_update_task_validation(client):
    # Setup
    create_res = client.post("/tasks", json={"title": "Task Update Test", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Test valid update
    update_res = client.put(f"/tasks/{task_id}", json={"title": "New Title"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "New Title"

def test_delete_task(client):
    create_res = client.post("/tasks", json={"title": "Task Delete Test", "status": "pending"})
    task_id = create_res.json()["id"]
    
    # Delete
    del_res = client.delete(f"/tasks/{task_id}")
    assert del_res.status_code == 204
    
    # Verify deletion
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 404

def test_list_tasks(client):
    client.post("/tasks", json={"title": "Task 1", "status": "pending"})
    client.post("/tasks", json={"title": "Task 2", "status": "completed"})
    
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2
    assert tasks[0]["title"] == "Task 1"
    assert tasks[1]["title"] == "Task 2"

def test_create_task_invalid_status(client):
    response = client.post("/tasks", json={"title": "Bad Task", "status": "invalid_status"})
    assert response.status_code == 422

def test_create_task_no_title(client):
    response = client.post("/tasks", json={"status": "pending"})
    assert response.status_code == 422
