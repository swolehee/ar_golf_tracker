"""REST API for AR Golf Tracker cloud backend.

Provides authentication, data synchronization, and retrieval endpoints.
Supports TLS 1.3 for secure data transmission.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
import uuid
from collections import defaultdict
import time

from .database import CloudDatabase
from .conflict_resolver import ConflictResolver
from .config import APIConfig


# Configuration
SECRET_KEY = APIConfig.SECRET_KEY
ALGORITHM = APIConfig.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = APIConfig.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = APIConfig.REFRESH_TOKEN_EXPIRE_DAYS

# Rate limiting configuration
RATE_LIMIT_REQUESTS = APIConfig.RATE_LIMIT_REQUESTS
RATE_LIMIT_WINDOW = APIConfig.RATE_LIMIT_WINDOW

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# FastAPI app
app = FastAPI(
    title="AR Golf Tracker API",
    description="Cloud backend API for AR Golf Tracker system with TLS 1.3 support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=APIConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting storage (in-memory, use Redis in production)
rate_limit_storage: Dict[str, List[float]] = defaultdict(list)


# Pydantic models for request/response

class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request."""
    refresh_token: str


class SyncRound(BaseModel):
    """Round data for synchronization."""
    id: str
    course_id: Optional[str] = None
    course_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    weather_conditions: Optional[Dict[str, Any]] = None


class SyncShot(BaseModel):
    """Shot data for synchronization."""
    id: str
    round_id: str
    hole_number: int
    swing_number: int
    club_type: str
    shot_time: datetime
    gps_lat: float
    gps_lon: float
    gps_accuracy: float
    gps_altitude: Optional[float] = None
    distance_yards: Optional[float] = None
    distance_accuracy: Optional[str] = None
    notes: Optional[str] = None


class SyncResult(BaseModel):
    """Synchronization result."""
    success: bool
    synced_count: int
    failed_count: int
    conflicts: List[Dict[str, Any]] = []


class RoundResponse(BaseModel):
    """Round data response."""
    id: str
    course_id: Optional[str]
    course_name: str
    start_time: datetime
    end_time: Optional[datetime]
    weather_conditions: Optional[Dict[str, Any]]


class ShotResponse(BaseModel):
    """Shot data response."""
    id: str
    round_id: str
    hole_number: int
    swing_number: int
    club_type: str
    shot_time: datetime
    gps_lat: float
    gps_lon: float
    gps_accuracy: float
    gps_altitude: Optional[float]
    distance_yards: Optional[float]
    distance_accuracy: Optional[str]
    notes: Optional[str]


class CourseSearchResponse(BaseModel):
    """Course search result."""
    id: str
    name: str
    distance_meters: float


class CourseResponse(BaseModel):
    """Course details response."""
    id: str
    name: str
    address: Optional[str]
    total_holes: int
    par: int
    yardage: int
    rating: Optional[float]
    slope: Optional[int]


class HoleResponse(BaseModel):
    """Hole details response."""
    id: str
    hole_number: int
    par: int
    yardage: int
    tee_box_lat: float
    tee_box_lon: float
    green_lat: float
    green_lon: float


# Database dependency
def get_db() -> CloudDatabase:
    """Get database connection."""
    db = CloudDatabase()
    try:
        db.connect()
        yield db
    finally:
        db.close()


# Rate limiting middleware
def check_rate_limit(request: Request, user_id: str) -> None:
    """Check if user has exceeded rate limit.
    
    Args:
        request: FastAPI request object
        user_id: User ID for rate limiting
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    current_time = time.time()
    user_requests = rate_limit_storage[user_id]
    
    # Remove requests outside the time window
    user_requests[:] = [req_time for req_time in user_requests 
                        if current_time - req_time < RATE_LIMIT_WINDOW]
    
    # Check if limit exceeded
    if len(user_requests) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
        )
    
    # Add current request
    user_requests.append(current_time)


# Authentication utilities

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: CloudDatabase = Depends(get_db)
) -> dict:
    """Get current authenticated user from token."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Verify user exists in database
    conn = db.connect()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
    
    return {"id": str(user[0]), "email": user[1]}


# Authentication endpoints

@app.post("/api/v1/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: CloudDatabase = Depends(get_db)):
    """Register a new user.
    
    Args:
        user_data: User registration data
        db: Database connection
        
    Returns:
        Authentication tokens
        
    Raises:
        HTTPException: If email already exists
    """
    conn = db.connect()
    
    # Check if user already exists
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = get_password_hash(user_data.password)
    
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (id, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (user_id, user_data.email, password_hash)
        )
    conn.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@app.post("/api/v1/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: CloudDatabase = Depends(get_db)):
    """Authenticate user and return tokens.
    
    Args:
        user_data: User login credentials
        db: Database connection
        
    Returns:
        Authentication tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    conn = db.connect()
    
    # Get user from database
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE email = %s",
            (user_data.email,)
        )
        user = cursor.fetchone()
    
    if not user or not verify_password(user_data.password, user[1]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = str(user[0])
    
    # Create tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token.
    
    Args:
        token_data: Refresh token
        
    Returns:
        New authentication tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    payload = decode_token(token_data.refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(access_token=access_token, refresh_token=refresh_token)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Sync endpoints

@app.post("/api/v1/sync/rounds", response_model=SyncResult)
async def sync_rounds(
    rounds: List[SyncRound],
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Synchronize round data from AR glasses to cloud.
    
    Supports batch processing for bulk uploads. Uses last-write-wins
    conflict resolution based on timestamps.
    
    Args:
        rounds: List of rounds to synchronize
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Synchronization result with counts and conflicts
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    conflict_resolver = ConflictResolver(conn)
    synced_count = 0
    failed_count = 0
    conflicts = []
    
    for round_data in rounds:
        try:
            with conn.cursor() as cursor:
                # Check if round already exists
                cursor.execute(
                    "SELECT updated_at FROM user_rounds WHERE id = %s AND user_id = %s",
                    (round_data.id, current_user["id"])
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Resolve conflict using conflict resolver
                    resolution = conflict_resolver.resolve_round_conflict(
                        round_id=round_data.id,
                        user_id=current_user["id"],
                        incoming_data=round_data.dict(),
                        existing_updated_at=existing[0]
                    )
                    
                    conflicts.append({
                        "round_id": round_data.id,
                        "resolution": resolution["conflict_info"]["resolution"],
                        "message": f"Round updated with latest data (last-write-wins)"
                    })
                    
                    # Update existing round
                    cursor.execute(
                        """
                        UPDATE user_rounds
                        SET course_id = %s, course_name = %s, start_time = %s,
                            end_time = %s, weather_conditions = %s, sync_status = 'SYNCED'
                        WHERE id = %s AND user_id = %s
                        """,
                        (
                            round_data.course_id,
                            round_data.course_name,
                            round_data.start_time,
                            round_data.end_time,
                            round_data.weather_conditions,
                            round_data.id,
                            current_user["id"]
                        )
                    )
                else:
                    # Insert new round
                    cursor.execute(
                        """
                        INSERT INTO user_rounds 
                        (id, user_id, course_id, course_name, start_time, end_time, 
                         weather_conditions, sync_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'SYNCED')
                        """,
                        (
                            round_data.id,
                            current_user["id"],
                            round_data.course_id,
                            round_data.course_name,
                            round_data.start_time,
                            round_data.end_time,
                            round_data.weather_conditions
                        )
                    )
            
            conn.commit()
            synced_count += 1
            
        except Exception as e:
            conn.rollback()
            failed_count += 1
            conflicts.append({
                "round_id": round_data.id,
                "resolution": "failed",
                "message": str(e)
            })
    
    return SyncResult(
        success=failed_count == 0,
        synced_count=synced_count,
        failed_count=failed_count,
        conflicts=conflicts
    )


@app.post("/api/v1/sync/shots", response_model=SyncResult)
async def sync_shots(
    shots: List[SyncShot],
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Synchronize shot data from AR glasses to cloud.
    
    Supports batch processing for bulk uploads. Uses last-write-wins
    conflict resolution based on timestamps.
    
    Args:
        shots: List of shots to synchronize
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Synchronization result with counts and conflicts
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    conflict_resolver = ConflictResolver(conn)
    synced_count = 0
    failed_count = 0
    conflicts = []
    
    for shot_data in shots:
        try:
            with conn.cursor() as cursor:
                # Verify round belongs to user
                cursor.execute(
                    "SELECT id FROM user_rounds WHERE id = %s AND user_id = %s",
                    (shot_data.round_id, current_user["id"])
                )
                if not cursor.fetchone():
                    failed_count += 1
                    conflicts.append({
                        "shot_id": shot_data.id,
                        "resolution": "failed",
                        "message": "Round not found or does not belong to user"
                    })
                    continue
                
                # Check if shot already exists
                cursor.execute(
                    """
                    SELECT s.updated_at 
                    FROM user_shots s
                    JOIN user_rounds r ON s.round_id = r.id
                    WHERE s.id = %s AND r.user_id = %s
                    """,
                    (shot_data.id, current_user["id"])
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Resolve conflict using conflict resolver
                    resolution = conflict_resolver.resolve_shot_conflict(
                        shot_id=shot_data.id,
                        user_id=current_user["id"],
                        incoming_data=shot_data.dict(),
                        existing_updated_at=existing[0]
                    )
                    
                    conflicts.append({
                        "shot_id": shot_data.id,
                        "resolution": resolution["conflict_info"]["resolution"],
                        "message": f"Shot updated with latest data (last-write-wins)"
                    })
                    
                    # Update existing shot
                    cursor.execute(
                        """
                        UPDATE user_shots
                        SET hole_number = %s, swing_number = %s, club_type = %s,
                            shot_time = %s, gps_origin = ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                            gps_accuracy = %s, gps_altitude = %s, distance_yards = %s,
                            distance_accuracy = %s, notes = %s, sync_status = 'SYNCED'
                        WHERE id = %s
                        """,
                        (
                            shot_data.hole_number,
                            shot_data.swing_number,
                            shot_data.club_type,
                            shot_data.shot_time,
                            shot_data.gps_lon,
                            shot_data.gps_lat,
                            shot_data.gps_accuracy,
                            shot_data.gps_altitude,
                            shot_data.distance_yards,
                            shot_data.distance_accuracy,
                            shot_data.notes,
                            shot_data.id
                        )
                    )
                else:
                    # Insert new shot
                    cursor.execute(
                        """
                        INSERT INTO user_shots
                        (id, round_id, hole_number, swing_number, club_type, shot_time,
                         gps_origin, gps_accuracy, gps_altitude, distance_yards,
                         distance_accuracy, notes, sync_status)
                        VALUES (%s, %s, %s, %s, %s, %s, 
                                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                                %s, %s, %s, %s, %s, 'SYNCED')
                        """,
                        (
                            shot_data.id,
                            shot_data.round_id,
                            shot_data.hole_number,
                            shot_data.swing_number,
                            shot_data.club_type,
                            shot_data.shot_time,
                            shot_data.gps_lon,
                            shot_data.gps_lat,
                            shot_data.gps_accuracy,
                            shot_data.gps_altitude,
                            shot_data.distance_yards,
                            shot_data.distance_accuracy,
                            shot_data.notes
                        )
                    )
            
            conn.commit()
            synced_count += 1
            
        except Exception as e:
            conn.rollback()
            failed_count += 1
            conflicts.append({
                "shot_id": shot_data.id,
                "resolution": "failed",
                "message": str(e)
            })
    
    return SyncResult(
        success=failed_count == 0,
        synced_count=synced_count,
        failed_count=failed_count,
        conflicts=conflicts
    )


@app.get("/api/v1/sync/status")
async def get_sync_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get synchronization status for user's data.
    
    Args:
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Sync status summary
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    
    with conn.cursor() as cursor:
        # Count rounds by sync status
        cursor.execute(
            """
            SELECT sync_status, COUNT(*) 
            FROM user_rounds 
            WHERE user_id = %s 
            GROUP BY sync_status
            """,
            (current_user["id"],)
        )
        rounds_status = dict(cursor.fetchall())
        
        # Count shots by sync status
        cursor.execute(
            """
            SELECT s.sync_status, COUNT(*) 
            FROM user_shots s
            JOIN user_rounds r ON s.round_id = r.id
            WHERE r.user_id = %s 
            GROUP BY s.sync_status
            """,
            (current_user["id"],)
        )
        shots_status = dict(cursor.fetchall())
    
    return {
        "rounds": rounds_status,
        "shots": shots_status,
        "last_checked": datetime.utcnow().isoformat()
    }


# Data retrieval endpoints

@app.get("/api/v1/rounds", response_model=List[RoundResponse])
async def get_rounds(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get list of rounds for authenticated user.
    
    Args:
        request: FastAPI request object
        limit: Maximum number of rounds to return
        offset: Number of rounds to skip
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of rounds
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, course_id, course_name, start_time, end_time, weather_conditions
            FROM user_rounds
            WHERE user_id = %s
            ORDER BY start_time DESC
            LIMIT %s OFFSET %s
            """,
            (current_user["id"], limit, offset)
        )
        rounds = cursor.fetchall()
    
    return [
        RoundResponse(
            id=str(row[0]),
            course_id=str(row[1]) if row[1] else None,
            course_name=row[2],
            start_time=row[3],
            end_time=row[4],
            weather_conditions=row[5]
        )
        for row in rounds
    ]


@app.get("/api/v1/rounds/{round_id}", response_model=RoundResponse)
async def get_round(
    round_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get details of a specific round.
    
    Args:
        round_id: Round ID
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Round details
        
    Raises:
        HTTPException: If round not found or doesn't belong to user
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, course_id, course_name, start_time, end_time, weather_conditions
            FROM user_rounds
            WHERE id = %s AND user_id = %s
            """,
            (round_id, current_user["id"])
        )
        round_data = cursor.fetchone()
    
    if not round_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round not found"
        )
    
    return RoundResponse(
        id=str(round_data[0]),
        course_id=str(round_data[1]) if round_data[1] else None,
        course_name=round_data[2],
        start_time=round_data[3],
        end_time=round_data[4],
        weather_conditions=round_data[5]
    )


@app.get("/api/v1/rounds/{round_id}/shots", response_model=List[ShotResponse])
async def get_round_shots(
    round_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get all shots for a specific round.
    
    Args:
        round_id: Round ID
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of shots for the round
        
    Raises:
        HTTPException: If round not found or doesn't belong to user
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    
    # Verify round belongs to user
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM user_rounds WHERE id = %s AND user_id = %s",
            (round_id, current_user["id"])
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Round not found"
            )
    
    # Get shots
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                id, round_id, hole_number, swing_number, club_type, shot_time,
                ST_Y(gps_origin::geometry) as lat,
                ST_X(gps_origin::geometry) as lon,
                gps_accuracy, gps_altitude, distance_yards, distance_accuracy, notes
            FROM user_shots
            WHERE round_id = %s
            ORDER BY shot_time
            """,
            (round_id,)
        )
        shots = cursor.fetchall()
    
    return [
        ShotResponse(
            id=str(row[0]),
            round_id=str(row[1]),
            hole_number=row[2],
            swing_number=row[3],
            club_type=row[4],
            shot_time=row[5],
            gps_lat=row[6],
            gps_lon=row[7],
            gps_accuracy=row[8],
            gps_altitude=row[9],
            distance_yards=row[10],
            distance_accuracy=row[11],
            notes=row[12]
        )
        for row in shots
    ]


@app.get("/api/v1/courses/search", response_model=List[CourseSearchResponse])
async def search_courses(
    lat: float,
    lon: float,
    radius: int = 1000,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Search for courses near a GPS location.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default 1000)
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of nearby courses with distances
    """
    # Check rate limit
    if request:
        check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM find_courses_near_location(%s, %s, %s)",
            (lat, lon, radius)
        )
        courses = cursor.fetchall()
    
    return [
        CourseSearchResponse(
            id=str(row[0]),
            name=row[1],
            distance_meters=row[2]
        )
        for row in courses
    ]


@app.get("/api/v1/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get details of a specific course.
    
    Args:
        course_id: Course ID
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Course details
        
    Raises:
        HTTPException: If course not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, address, total_holes, par, yardage, rating, slope
            FROM courses
            WHERE id = %s
            """,
            (course_id,)
        )
        course = cursor.fetchone()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return CourseResponse(
        id=str(course[0]),
        name=course[1],
        address=course[2],
        total_holes=course[3],
        par=course[4],
        yardage=course[5],
        rating=course[6],
        slope=course[7]
    )


@app.get("/api/v1/courses/{course_id}/holes", response_model=List[HoleResponse])
async def get_course_holes(
    course_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get all holes for a specific course.
    
    Args:
        course_id: Course ID
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of holes for the course
        
    Raises:
        HTTPException: If course not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    
    # Verify course exists
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM courses WHERE id = %s", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
    
    # Get holes
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                id, hole_number, par, yardage,
                ST_Y(tee_box_location::geometry) as tee_lat,
                ST_X(tee_box_location::geometry) as tee_lon,
                ST_Y(green_location::geometry) as green_lat,
                ST_X(green_location::geometry) as green_lon
            FROM holes
            WHERE course_id = %s
            ORDER BY hole_number
            """,
            (course_id,)
        )
        holes = cursor.fetchall()
    
    return [
        HoleResponse(
            id=str(row[0]),
            hole_number=row[1],
            par=row[2],
            yardage=row[3],
            tee_box_lat=row[4],
            tee_box_lon=row[5],
            green_lat=row[6],
            green_lon=row[7]
        )
        for row in holes
    ]


# Conflict management endpoints

@app.get("/api/v1/conflicts")
async def get_conflicts(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get list of sync conflicts for authenticated user.
    
    Args:
        request: FastAPI request object
        limit: Maximum number of conflicts to return
        offset: Number of conflicts to skip
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of conflict records
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    conflict_resolver = ConflictResolver(conn)
    
    conflicts = conflict_resolver.get_user_conflicts(
        user_id=current_user["id"],
        limit=limit,
        offset=offset
    )
    
    return {
        "conflicts": conflicts,
        "total": len(conflicts),
        "limit": limit,
        "offset": offset
    }
