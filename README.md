# Task Manager API

A simple Task Management API built with FastAPI and SQLite.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn src.main:app --reload
   ```

## Running Tests

To run the test suite, use `pytest`:
```bash
pytest tests/
```

## API Documentation

The API automatically generates documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

- `POST /tasks`: Create a new task.
  - Body: `{"title": "Task title", "description": "Optional description", "status": "pending"}` (status must be 'pending' or 'completed').
- `GET /tasks`: List all tasks.
- `GET /tasks/{task_id}`: Retrieve a specific task by ID.
- `PUT /tasks/{task_id}`: Update a task.
- `DELETE /tasks/{task_id}`: Delete a task.
