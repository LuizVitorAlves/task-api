# Task API

## Overview
A simple Task management API built with FastAPI and SQLite.

## How to run
1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `uvicorn src.main:app --reload`
3. The API will be available at `http://127.0.0.1:8000`

## Authentication
The API uses **HTTP Basic Authentication**.
- **Username**: Configure via environment variable `API_USERNAME` (defaults to `admin`)
- **Password**: Configure via environment variable `API_PASSWORD` (defaults to `password123`)

## Endpoints

### Create Task
`POST /tasks`
- **Request Body**: `{"title": "string", "description": "string", "status": "pending" | "completed"}`
- **Auth**: Required

### List Tasks
`GET /tasks`
- **Auth**: Required

### Get Task
`GET /tasks/{task_id}`
- **Auth**: Required

### Update Task
`PUT /tasks/{task_id}`
- **Request Body**: `{"title": "string", "description": "string", "status": "pending" | "completed"}` (all fields optional)
- **Auth**: Required

### Delete Task
`DELETE /tasks/{task_id}`
- **Auth**: Required

## Error Responses
- `401 Unauthorized`: Invalid credentials.
- `404 Not Found`: Task does not exist.
- `422 Unprocessable Entity`: Validation error (e.g., empty title, invalid status).
