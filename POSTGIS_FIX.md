# PostGIS Installation Fix for PostgreSQL 14

## Problem
PostGIS extension is not installed for your PostgreSQL 14 installation.

## Solution

Run these commands in your terminal:

```bash
# Install PostGIS for PostgreSQL 14
brew install postgis

# Restart PostgreSQL
brew services restart postgresql@14

# Verify PostGIS is available
psql ar_golf_tracker -c "CREATE EXTENSION postgis;"

# If successful, run the schema again
psql ar_golf_tracker < ar_golf_tracker/backend/schema.sql
```

## Alternative: Use Docker (Recommended for Development)

If the above doesn't work, use Docker which has PostGIS pre-configured:

```bash
# Stop local PostgreSQL
brew services stop postgresql@14

# Create docker-compose.yml (already in project root if you created it)
# Or create it now:
cat > docker-compose-db.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgis/postgis:14-3.3
    environment:
      - POSTGRES_USER=ar_golf_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=ar_golf_tracker
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

# Start PostgreSQL with PostGIS
docker-compose -f docker-compose-db.yml up -d

# Wait a few seconds for database to start
sleep 5

# Run schema
psql -h localhost -U ar_golf_user -d ar_golf_tracker < ar_golf_tracker/backend/schema.sql
# Password: password

# Load sample courses
python ar_golf_tracker/backend/sample_courses.py
```

## Verify Installation

```bash
# Connect to database
psql ar_golf_tracker

# Check PostGIS version
SELECT PostGIS_Version();

# List tables
\dt

# You should see: courses, holes, user_rounds, user_shots, sync_queue, devices
```

## Quick Test

```bash
# Run course service tests (these require PostGIS)
pytest tests/test_course_service.py -v
```

If tests pass, PostGIS is working correctly!
