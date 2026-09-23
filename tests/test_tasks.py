import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"title": "Test Task", "description": "Description"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["id"] == 1

def test_get_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_task():
    # First create
    client.post("/tasks", json={"title": "Test Task", "description": "Description"})
    
    response = client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"
