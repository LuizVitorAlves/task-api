# Task Management API

A simple REST API for managing tasks with persistence.

## Requirements
- Python 3.9+
- FastAPI
- Uvicorn
- SQLite3 (standard library)

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the server:
   ```bash
   uvicorn src.main:app --reload
   ```

## API Usage

- `POST /tasks`: Create a new task (JSON: `{"title": "string", "description": "string", "status": "pending"|"completed"}`)
- `GET /tasks`: List all tasks
- `GET /tasks/{id}`: Get a specific task
- `PUT /tasks/{id}`: Update a task
- `DELETE /tasks/{id}`: Delete a task
