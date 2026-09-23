import pytest
from fastapi.testclient import TestClient
from src.main import app, tasks

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_tasks():
    tasks.clear()
    # Reset counter by re-importing or just assuming the logic will handle it if we fix the ID logic.
    # Given the simplicity, just resetting the list is enough for tests to be isolated enough, 
    # but the id_counter in main.py will keep increasing.
    # Let's adjust the test to just accept incrementing IDs.

def test_create_task():
    response = client.post("/tasks", json={"title": "Test Task", "status": "pending"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "pending"

def test_create_task_invalid_status():
    response = client.post("/tasks", json={"title": "Test Task", "status": "invalid"})
    assert response.status_code == 422

def test_create_task_missing_title():
    response = client.post("/tasks", json={"description": "No title"})
    assert response.status_code == 422

def test_update_task():
    create_response = client.post("/tasks", json={"title": "Old Title"})
    task_id = create_response.json()["id"]
    
    response = client.put(f"/tasks/{task_id}", json={"title": "New Title", "status": "completed"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["status"] == "completed"

def test_update_nonexistent_task():
    response = client.put("/tasks/999", json={"title": "New Title"})
    assert response.status_code == 404

def test_delete_task():
    create_response = client.post("/tasks", json={"title": "To Delete"})
    task_id = create_response.json()["id"]
    
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404

def test_delete_nonexistent_task():
    response = client.delete("/tasks/999")
    assert response.status_code == 404
