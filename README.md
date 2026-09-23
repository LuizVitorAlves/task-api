# Task API

## Running the API
```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## API Endpoints
- `POST /tasks`: Create a new task
- `GET /tasks`: List all tasks
- `GET /tasks/{task_id}`: Get a single task
- `PUT /tasks/{task_id}`: Update a task
- `DELETE /tasks/{task_id}`: Delete a task

## Statuses
- `pending`
- `completed`
