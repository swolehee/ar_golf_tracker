# AR Golf Tracker Backend API

Cloud backend REST API for the AR Golf Tracker system.

## Overview

The backend API provides:
- JWT-based authentication (register, login, refresh)
- Data synchronization endpoints for rounds and shots
- Data retrieval endpoints for viewing historical data
- Course database queries
- Conflict resolution with last-write-wins strategy
- Rate limiting (100 requests/minute per user)

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Required packages:
- fastapi>=0.104.0
- uvicorn>=0.24.0
- pydantic>=2.5.0
- python-jose[cryptography]>=3.3.0
- passlib[bcrypt]>=1.7.4
- psycopg2-binary>=2.9.9

## Database Setup

1. Install PostgreSQL with PostGIS extension
2. Create database:
   ```sql
   CREATE DATABASE ar_golf_tracker;
   ```
3. Initialize schema:
   ```python
   from ar_golf_tracker.backend.database import CloudDatabase
   
   db = CloudDatabase(
       host="localhost",
       port=5432,
       database="ar_golf_tracker",
       user="postgres",
       password="your_password"
   )
   db.initialize_schema()
   ```

## Running the API

Start the development server:

```bash
uvicorn ar_golf_tracker.backend.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI): `http://localhost:8000/docs`

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token

### Data Synchronization

- `POST /api/v1/sync/rounds` - Sync round data from AR glasses
- `POST /api/v1/sync/shots` - Sync shot data from AR glasses
- `GET /api/v1/sync/status` - Get sync status

### Data Retrieval

- `GET /api/v1/rounds` - List user's rounds
- `GET /api/v1/rounds/{round_id}` - Get round details
- `GET /api/v1/rounds/{round_id}/shots` - Get shots for a round

### Course Database

- `GET /api/v1/courses/search?lat={lat}&lon={lon}&radius={meters}` - Search courses by location
- `GET /api/v1/courses/{course_id}` - Get course details
- `GET /api/v1/courses/{course_id}/holes` - Get holes for a course

### Conflict Management

- `GET /api/v1/conflicts` - Get list of sync conflicts

### Health Check

- `GET /health` - API health status

## Authentication Flow

1. Register a new user:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password123"}'
   ```

2. Login to get tokens:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password123"}'
   ```

3. Use access token in subsequent requests:
   ```bash
   curl -X GET http://localhost:8000/api/v1/rounds \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

## Conflict Resolution

The API uses a **last-write-wins** strategy for conflict resolution:

1. When syncing data that already exists in the database, the incoming data overwrites the existing data
2. All conflicts are logged to the `sync_conflicts` table for user review
3. Users can retrieve their conflict history via the `/api/v1/conflicts` endpoint

## Rate Limiting

- 100 requests per minute per user
- Rate limit applies to all authenticated endpoints
- Returns HTTP 429 when limit exceeded

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Access tokens expire after 30 minutes
- Refresh tokens expire after 7 days
- TLS 1.3 recommended for production
- CORS enabled (configure for production)

## Configuration

Update these settings for production:

1. Change `SECRET_KEY` in `api.py` (use environment variable)
2. Configure CORS allowed origins
3. Set up proper database credentials
4. Use Redis for rate limiting storage
5. Enable HTTPS/TLS

## Testing

Run tests:

```bash
pytest tests/test_backend_api.py -v
```

Note: Some tests require FastAPI and other dependencies to be installed.

## Production Deployment

Recommended setup:
- Use Gunicorn with Uvicorn workers
- Deploy behind Nginx reverse proxy
- Use managed PostgreSQL (AWS RDS, etc.)
- Use Redis for rate limiting
- Enable monitoring and logging
- Set up automated backups

Example production command:
```bash
gunicorn ar_golf_tracker.backend.api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```
