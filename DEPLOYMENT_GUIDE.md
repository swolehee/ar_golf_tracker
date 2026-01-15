# AR Golf Tracker - Deployment & Next Steps Guide

## Overview

This guide walks you through deploying the AR Golf Tracker system to production and conducting user acceptance testing with real hardware.

---

## Current Status

✅ **Software Development Complete**
- All core functionality implemented and tested
- 332 tests passing (100% pass rate)
- All correctness properties validated
- Ready for hardware integration

⏭️ **Next Phase: Hardware Integration & UAT**

---

## Phase 1: Local Development Testing

### Run the System Locally

#### 1. Start the Backend Server

```bash
# From the project root
cd ar_golf_tracker/backend
python server.py
```

The backend API will start on `http://localhost:5000`

#### 2. Test the Mobile App Components

```bash
# Run the mobile app example
python ar_golf_tracker/mobile_app/example_usage.py

# Test map visualization
python ar_golf_tracker/mobile_app/map_example.py
```

#### 3. Simulate AR Glasses Recording

```bash
# Create a test recording session
python -c "
from ar_golf_tracker.ar_glasses.shot_recorder import ShotRecorder
from ar_golf_tracker.ar_glasses.database import ARGlassesDatabase

# Initialize components
db = ARGlassesDatabase(':memory:')
recorder = ShotRecorder(db)

# Start a round
round_id = recorder.start_round('Test Course', 1)
print(f'Started round: {round_id}')

# Simulate recording shots
# (In production, this would be triggered by actual hardware)
"
```

#### 4. Run All Tests

```bash
# Verify everything still works
pytest tests/ -v

# Run specific test suites
pytest tests/test_integration_e2e.py -v
pytest tests/test_backend_api.py -v
pytest tests/test_mobile_app/ -v
```

---

## Phase 2: Production Database Setup

### PostgreSQL with PostGIS

#### 1. Install PostgreSQL with PostGIS

**macOS:**
```bash
brew install postgresql postgis
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib postgis
sudo systemctl start postgresql
```

#### 2. Create Production Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database and enable PostGIS
CREATE DATABASE ar_golf_tracker;
\c ar_golf_tracker
CREATE EXTENSION postgis;

# Create user
CREATE USER ar_golf_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ar_golf_tracker TO ar_golf_user;
```

#### 3. Initialize Schema

```bash
# Run the backend schema
psql -U ar_golf_user -d ar_golf_tracker -f ar_golf_tracker/backend/schema.sql
```

#### 4. Load Course Data

```bash
# Load sample courses
python ar_golf_tracker/backend/sample_courses.py

# Or import real course data from a golf course database provider
# (e.g., Golf Course Database API, OpenStreetMap golf courses)
```

#### 5. Update Configuration

Create `ar_golf_tracker/backend/config.py` with production settings:

```python
import os

class ProductionConfig:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 
        'postgresql://ar_golf_user:password@localhost/ar_golf_tracker')
    
    # API
    SECRET_KEY = os.getenv('SECRET_KEY', 'generate-a-secure-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'generate-another-secure-key')
    
    # Rate limiting
    RATE_LIMIT = '100/minute'
    
    # Encryption
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Generate with encryption.py
```

---

## Phase 3: Cloud Deployment

### Option A: AWS Deployment

#### 1. Backend API (AWS Lambda + API Gateway)

```bash
# Install AWS SAM CLI
brew install aws-sam-cli

# Create SAM template (example)
cat > template.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  ARGolfTrackerAPI:
    Type: AWS::Serverless::Function
    Properties:
      Handler: ar_golf_tracker.backend.server.lambda_handler
      Runtime: python3.12
      Environment:
        Variables:
          DATABASE_URL: !Ref DatabaseURL
          SECRET_KEY: !Ref SecretKey
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY

  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      Engine: postgres
      EngineVersion: '15.4'
      DBInstanceClass: db.t3.micro
      AllocatedStorage: 20
      MasterUsername: ar_golf_user
      MasterUserPassword: !Ref DBPassword
EOF

# Deploy
sam build
sam deploy --guided
```

#### 2. Database (AWS RDS PostgreSQL with PostGIS)

```bash
# Enable PostGIS extension via RDS parameter group
aws rds create-db-parameter-group \
  --db-parameter-group-name postgis-enabled \
  --db-parameter-group-family postgres15 \
  --description "PostgreSQL with PostGIS"

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier ar-golf-tracker-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username ar_golf_user \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20 \
  --db-parameter-group-name postgis-enabled
```

#### 3. Mobile App Backend (Optional: AWS Amplify)

```bash
# Initialize Amplify for mobile app
amplify init
amplify add api
amplify push
```

### Option B: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ar_golf_tracker/ ./ar_golf_tracker/
COPY setup.py .

# Install package
RUN pip install -e .

# Expose port
EXPOSE 5000

# Run server
CMD ["python", "ar_golf_tracker/backend/server.py"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://ar_golf_user:password@db:5432/ar_golf_tracker
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db

  db:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_USER=ar_golf_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=ar_golf_tracker
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./ar_golf_tracker/backend/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

#### 3. Deploy

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend python ar_golf_tracker/backend/sample_courses.py
```

---

## Phase 4: AR Glasses Hardware Integration

### Supported AR Platforms

The system is designed to work with:
- **Meta Quest 3** (recommended for development)
- **Meta Quest Pro**
- **Apple Vision Pro** (requires Swift/SwiftUI wrapper)
- **Magic Leap 2**
- **Microsoft HoloLens 2**

### Integration Steps

#### 1. Choose Your AR Platform

For **Meta Quest** (most accessible):

```bash
# Install Meta Quest SDK
# Download from: https://developer.oculus.com/downloads/

# Install Unity (if using Unity for AR development)
# Or use native Android development with Meta XR SDK
```

#### 2. Create AR Application Wrapper

The Python backend needs to be wrapped in a native AR application:

**Option A: Unity + Python Backend**
- Use Unity for AR rendering and UI
- Call Python backend via REST API
- Use Unity's AR Foundation + Meta XR SDK

**Option B: Native Android + Python**
- Build Android app with Meta XR SDK
- Embed Python using Chaquopy or call REST API
- Use Android Camera2 API for club recognition

**Option C: React Native + AR**
- Use React Native with ViroReact or AR.js
- Call Python backend via REST API
- Easier for mobile developers

#### 3. Integrate Hardware Sensors

Map AR glasses sensors to Python services:

```python
# Example integration pseudocode

# GPS from AR glasses
gps_service = GPSTrackingService()
ar_glasses.on_gps_update(lambda lat, lon, alt: 
    gps_service.update_position(lat, lon, alt))

# Camera for club recognition
club_service = ClubRecognitionService()
ar_glasses.on_camera_frame(lambda frame:
    club_service.process_frame(frame))

# IMU for swing detection
swing_service = SwingDetectionService()
ar_glasses.on_imu_data(lambda accel, gyro:
    swing_service.process_imu_data(accel, gyro))
```

#### 4. Test on Device

```bash
# Build and deploy to AR glasses
# (Platform-specific commands)

# For Meta Quest via ADB:
adb install -r your_ar_app.apk
adb logcat | grep ARGolfTracker
```

---

## Phase 5: Mobile App Development

### Option A: React Native (Recommended)

#### 1. Initialize React Native Project

```bash
npx react-native init ARGolfTrackerMobile
cd ARGolfTrackerMobile
```

#### 2. Install Dependencies

```bash
npm install @react-navigation/native @react-navigation/stack
npm install react-native-maps
npm install axios
npm install @react-native-async-storage/async-storage
```

#### 3. Integrate Python Backend

```javascript
// api/client.js
import axios from 'axios';

const API_BASE_URL = 'https://your-backend-url.com/api/v1';

export const getRounds = async (userId) => {
  const response = await axios.get(`${API_BASE_URL}/rounds`, {
    params: { user_id: userId }
  });
  return response.data;
};

export const getRoundShots = async (roundId) => {
  const response = await axios.get(`${API_BASE_URL}/rounds/${roundId}/shots`);
  return response.data;
};
```

#### 4. Implement UI Components

Use the Python implementations as reference:
- `ar_golf_tracker/mobile_app/round_list_view.py` → React Native component
- `ar_golf_tracker/mobile_app/map_visualization.py` → React Native Maps
- `ar_golf_tracker/mobile_app/shot_detail_view.py` → Detail screen

### Option B: Native iOS (Swift)

```bash
# Create Xcode project
# Integrate with Python backend via REST API
# Use MapKit for map visualization
```

### Option C: Native Android (Kotlin)

```bash
# Create Android Studio project
# Integrate with Python backend via Retrofit
# Use Google Maps SDK for map visualization
```

---

## Phase 6: User Acceptance Testing

### UAT Checklist

#### Pre-UAT Setup
- [ ] Deploy backend to cloud (AWS/Docker)
- [ ] Set up PostgreSQL with PostGIS
- [ ] Load golf course database (at least 10 local courses)
- [ ] Build AR glasses application
- [ ] Build mobile companion app
- [ ] Create test user accounts

#### UAT Test Scenarios

**Scenario 1: Complete Round Recording**
1. Put on AR glasses
2. Start new round at known golf course
3. Verify course auto-detection
4. Play hole 1 (4-5 shots)
5. Verify club recognition for each shot
6. Verify swing detection (no practice swings recorded)
7. Check shot distances on AR display
8. Move to hole 2, verify auto-transition
9. Complete 9 holes
10. Review round on mobile app

**Scenario 2: Offline Operation**
1. Enable airplane mode on AR glasses
2. Record 3 holes offline
3. Verify shots saved locally
4. Disable airplane mode
5. Verify automatic sync to cloud
6. Check mobile app shows all shots

**Scenario 3: Multi-Device Sync**
1. Record round on AR glasses
2. Open mobile app on phone
3. Verify round appears
4. Open mobile app on tablet
5. Verify same data appears
6. Delete shot on phone
7. Verify deletion syncs to tablet

#### Success Criteria

- [ ] Club recognition accuracy > 90%
- [ ] Swing detection accuracy > 95%
- [ ] GPS accuracy ≤ 10m
- [ ] Distance calculation within 5% of actual
- [ ] Battery life > 4 hours (18 holes)
- [ ] Sync latency < 10 seconds
- [ ] No data loss during offline operation
- [ ] User satisfaction score > 4/5

---

## Phase 7: Monitoring & Maintenance

### Set Up Monitoring

#### 1. Application Performance Monitoring

```bash
# Install New Relic or DataDog
pip install newrelic

# Add to server.py
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')
```

#### 2. Error Tracking

```bash
# Install Sentry
pip install sentry-sdk

# Add to server.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

#### 3. Metrics Dashboard

Track key metrics:
- API response times
- Sync success rate
- GPS accuracy distribution
- Club recognition confidence scores
- Active users
- Rounds recorded per day

### Maintenance Tasks

**Daily:**
- Monitor error logs
- Check sync queue health
- Verify API uptime

**Weekly:**
- Review user feedback
- Analyze accuracy metrics
- Update course database

**Monthly:**
- Review and optimize database queries
- Update ML models (club recognition, swing detection)
- Security patches and dependency updates

---

## Troubleshooting

### Common Issues

#### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
pip install -r requirements.txt

# Check database connection
psql -U ar_golf_user -d ar_golf_tracker -c "SELECT version();"
```

#### Tests failing
```bash
# Run specific test to see error
pytest tests/test_backend_api.py::test_name -v -s

# Check database schema
pytest tests/test_course_service.py -v  # Requires PostgreSQL
```

#### AR glasses can't connect to backend
- Verify network connectivity
- Check firewall rules
- Verify API endpoint URL
- Check authentication tokens

#### GPS accuracy issues
- Ensure clear sky view
- Wait for GPS lock (30-60 seconds)
- Check GPS permissions
- Verify PostGIS spatial queries

---

## Next Steps Summary

1. **Immediate (Week 1-2)**
   - Set up PostgreSQL with PostGIS locally
   - Deploy backend to cloud (AWS/Docker)
   - Load golf course database

2. **Short-term (Week 3-4)**
   - Choose AR platform (Meta Quest recommended)
   - Build AR application wrapper
   - Integrate hardware sensors

3. **Medium-term (Week 5-8)**
   - Build mobile companion app
   - Conduct internal testing
   - Fix bugs and optimize

4. **Long-term (Week 9-12)**
   - User acceptance testing on golf courses
   - Gather feedback and iterate
   - Prepare for production launch

---

## Resources

### Documentation
- Meta Quest Development: https://developer.oculus.com/
- PostGIS Documentation: https://postgis.net/documentation/
- React Native: https://reactnative.dev/
- AWS Deployment: https://aws.amazon.com/getting-started/

### Golf Course Data
- OpenStreetMap Golf Courses: https://www.openstreetmap.org/
- Golf Course Database APIs: (commercial providers)

### Support
- GitHub Issues: (your repository)
- Documentation: See README.md and TASK_18_INTEGRATION_TEST_REPORT.md

---

## Questions?

If you need help with any specific step, ask about:
- "How do I deploy to AWS?"
- "How do I integrate with Meta Quest?"
- "How do I build the mobile app?"
- "How do I load golf course data?"

The system is production-ready from a software perspective. The main work ahead is hardware integration and field testing!
