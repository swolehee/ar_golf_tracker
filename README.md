# AR Golf Tracker

Automatic golf shot tracking system using AR glasses (Meta AR or compatible devices).

## Overview

The AR Golf Tracker leverages AR glasses to automatically track golf shots during play by combining:
- Computer vision for club recognition
- Motion detection for swing tracking
- GPS tracking for position recording
- Automatic distance calculation between consecutive shots

## Project Structure

```
ar_golf_tracker/
├── ar_glasses/          # AR glasses edge device application
│   └── schema.sql       # SQLite schema for local storage
├── backend/             # Cloud backend service
│   └── schema.sql       # PostgreSQL + PostGIS schema
├── shared/              # Shared data models and utilities
│   └── models.py        # Core data models
└── __init__.py
```

## Components

### AR Glasses (Edge Device)
- Real-time club recognition using YOLO
- Swing detection using IMU sensors
- GPS position tracking
- Local SQLite storage for offline operation
- Automatic distance calculation between shots

### Cloud Backend
- REST API for data synchronization
- PostgreSQL with PostGIS for geographic data
- Course database with hole layouts
- User authentication and data management

### Mobile App
- Post-round shot visualization on course maps
- Statistics and performance analysis
- Round history and data management

## Setup

### Development Environment

1. Install Python 3.9 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

### Database Setup

#### SQLite (AR Glasses)
The SQLite database is automatically created on the AR glasses device using the schema in `ar_glasses/schema.sql`.

#### PostgreSQL (Cloud Backend)
1. Install PostgreSQL with PostGIS extension
2. Create a database:
```bash
createdb ar_golf_tracker
```
3. Run the schema:
```bash
psql ar_golf_tracker < ar_golf_tracker/backend/schema.sql
```

## Testing

Run tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=ar_golf_tracker
```

## Requirements

See `.kiro/specs/ar-golf-tracker/requirements.md` for detailed system requirements.

## Design

See `.kiro/specs/ar-golf-tracker/design.md` for architecture and design details.

## Implementation Tasks

See `.kiro/specs/ar-golf-tracker/tasks.md` for the implementation plan.
