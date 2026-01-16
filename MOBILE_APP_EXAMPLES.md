# Mobile App Examples Guide

This guide explains how to run the mobile app example scripts.

## Option 1: Demo with Mock Data (Recommended for Quick Testing)

Run the demo version that uses mock data and doesn't require a backend:

```bash
python ar_golf_tracker/mobile_app/example_usage_demo.py
```

This will demonstrate:
- Round list workflow with 10 mock rounds
- Round detail view with shot data
- Filtering and sorting functionality
- Club usage statistics
- Hole-by-hole breakdown

## Option 2: Full Example with Backend API

To run the full example that connects to the backend API:

### Step 1: Start the Backend Server

In one terminal, start the backend server:

```bash
python ar_golf_tracker/backend/server.py --reload
```

The server will start on `http://localhost:8000`

### Step 2: Update the Example Script

Edit `ar_golf_tracker/mobile_app/example_usage.py` and change the API URL from:

```python
api_client = APIClient(base_url="https://api.argolftracker.com")
```

to:

```python
api_client = APIClient(base_url="http://localhost:8000")
```

### Step 3: Run the Example

In another terminal:

```bash
python ar_golf_tracker/mobile_app/example_usage.py
```

Note: You'll need to have user accounts and data in the backend database for this to work properly.

## What the Examples Demonstrate

### Round List Workflow
- Fetching rounds from the API
- Displaying round summaries
- Filtering by course
- Sorting by date
- Selecting a round for details

### Round Detail Workflow
- Fetching detailed round information
- Displaying course information
- Showing club usage statistics
- Calculating average distances by club
- Hole-by-hole breakdown

### Filtering and Sorting
- Getting unique courses
- Filtering rounds by course
- Sorting rounds by date (ascending/descending)

## Troubleshooting

### Connection Errors

If you see errors like:
```
Failed to resolve 'api.argolftracker.com'
```

This means the example is trying to connect to a non-existent domain. Use the demo version instead, or follow Option 2 to run with a local backend.

### Missing Data

If the backend is running but you see empty results, you may need to:
1. Create sample data using the backend API
2. Check that the database is properly initialized
3. Verify authentication credentials
