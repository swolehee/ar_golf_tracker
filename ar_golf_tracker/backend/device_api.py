"""Device management API endpoints for cross-device sync.

Provides endpoints for device registration, device-specific preferences,
and cross-device synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .api import get_current_user, get_db, check_rate_limit
from .database import CloudDatabase
from .device_manager import DeviceManager


# Create router for device endpoints
router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


# Pydantic models

class DeviceRegister(BaseModel):
    """Device registration request."""
    device_id: str = Field(..., description="Unique device identifier")
    device_type: str = Field(..., description="Device type: AR_GLASSES, MOBILE_IOS, MOBILE_ANDROID, WEB")
    device_name: Optional[str] = Field(None, description="User-friendly device name")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device metadata")


class DeviceResponse(BaseModel):
    """Device information response."""
    device_uuid: str
    device_id: str
    device_type: str
    device_name: Optional[str]
    last_sync_at: Optional[datetime]
    last_active_at: datetime
    device_preferences: Dict[str, Any]


class DevicePreferencesUpdate(BaseModel):
    """Device preferences update request."""
    preferences: Dict[str, Any] = Field(..., description="Device-specific preferences")


class SyncStatusResponse(BaseModel):
    """Sync status response."""
    total_rounds: int
    synced_rounds: int
    pending_rounds: int
    total_shots: int
    synced_shots: int
    pending_shots: int


class EntityToSync(BaseModel):
    """Entity that needs to be synced."""
    entity_id: str
    updated_at: datetime


class EntitiesToSyncResponse(BaseModel):
    """Response with entities to sync."""
    entity_type: str
    entities: List[EntityToSync]


# Device management endpoints

@router.post("/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    device_data: DeviceRegister,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Register or update a device for the authenticated user.
    
    This endpoint should be called when a device first connects or
    when device information needs to be updated.
    
    Args:
        device_data: Device registration data
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Device information including UUID
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    # Validate device type
    valid_types = ['AR_GLASSES', 'MOBILE_IOS', 'MOBILE_ANDROID', 'WEB']
    if device_data.device_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid device type. Must be one of: {', '.join(valid_types)}"
        )
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    # Register device
    device_uuid = device_manager.register_device(
        user_id=current_user["id"],
        device_id=device_data.device_id,
        device_type=device_data.device_type,
        device_name=device_data.device_name,
        device_info=device_data.device_info
    )
    
    # Get device information
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_data.device_id
    )
    
    return DeviceResponse(**device_info)


@router.get("", response_model=List[DeviceResponse])
async def get_devices(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get all active devices for the authenticated user.
    
    Args:
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of user's devices
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    devices = device_manager.get_user_devices(current_user["id"])
    
    return [DeviceResponse(**device) for device in devices]


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get information about a specific device.
    
    Args:
        device_id: Device identifier
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Device information
        
    Raises:
        HTTPException: If device not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse(**device_info)


@router.put("/{device_id}/preferences")
async def update_device_preferences(
    device_id: str,
    preferences_data: DevicePreferencesUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Update device-specific preferences.
    
    Device preferences override user preferences for that specific device.
    Common preferences include:
    - distance_unit: 'YARDS' or 'METERS'
    - auto_sync: boolean
    - power_saving_mode: boolean (for AR glasses)
    - notification_enabled: boolean (for mobile)
    
    Args:
        device_id: Device identifier
        preferences_data: Device preferences
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If device not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    # Verify device belongs to user
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update preferences
    device_manager.update_device_preferences(
        device_uuid=device_info['device_uuid'],
        preferences=preferences_data.preferences
    )
    
    return {
        "success": True,
        "message": "Device preferences updated",
        "device_id": device_id
    }


@router.get("/{device_id}/preferences")
async def get_device_preferences(
    device_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get effective preferences for a device.
    
    Returns merged user and device-specific preferences,
    with device preferences taking precedence.
    
    Args:
        device_id: Device identifier
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Effective preferences
        
    Raises:
        HTTPException: If device not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    # Verify device exists
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get effective preferences
    preferences = device_manager.get_effective_preferences(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    return {
        "device_id": device_id,
        "preferences": preferences
    }


@router.delete("/{device_id}")
async def deactivate_device(
    device_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Deactivate a device (soft delete).
    
    The device will no longer appear in the active devices list
    and will not receive sync updates.
    
    Args:
        device_id: Device identifier
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If device not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    # Verify device belongs to user
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Deactivate device
    device_manager.deactivate_device(device_info['device_uuid'])
    
    return {
        "success": True,
        "message": "Device deactivated",
        "device_id": device_id
    }


# Cross-device sync endpoints

@router.get("/{device_id}/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    device_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get sync status for a device.
    
    Shows how many entities are synced vs pending for this device.
    
    Args:
        device_id: Device identifier
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Sync status information
        
    Raises:
        HTTPException: If device not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    # Verify device belongs to user
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get sync status
    sync_status = device_manager.get_sync_status(
        device_uuid=device_info['device_uuid'],
        user_id=current_user["id"]
    )
    
    return SyncStatusResponse(**sync_status)


@router.get("/{device_id}/sync/pending", response_model=List[EntitiesToSyncResponse])
async def get_pending_sync(
    device_id: str,
    request: Request,
    since: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Get entities that need to be synced to a device.
    
    Returns rounds and shots that have been updated since the last
    sync to this device.
    
    Args:
        device_id: Device identifier
        request: FastAPI request object
        since: Optional timestamp to filter entities updated after this time
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of entities to sync (rounds and shots)
        
    Raises:
        HTTPException: If device not found
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    # Verify device belongs to user
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get pending entities
    pending_rounds = device_manager.get_entities_to_sync(
        device_uuid=device_info['device_uuid'],
        user_id=current_user["id"],
        entity_type='round',
        since=since
    )
    
    pending_shots = device_manager.get_entities_to_sync(
        device_uuid=device_info['device_uuid'],
        user_id=current_user["id"],
        entity_type='shot',
        since=since
    )
    
    return [
        EntitiesToSyncResponse(
            entity_type='round',
            entities=[EntityToSync(**e) for e in pending_rounds]
        ),
        EntitiesToSyncResponse(
            entity_type='shot',
            entities=[EntityToSync(**e) for e in pending_shots]
        )
    ]


@router.post("/{device_id}/sync/complete")
async def mark_sync_complete(
    device_id: str,
    entity_type: str,
    entity_ids: List[str],
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: CloudDatabase = Depends(get_db)
):
    """Mark entities as synced to a device.
    
    Should be called by the device after successfully receiving
    and storing the synced data.
    
    Args:
        device_id: Device identifier
        entity_type: Type of entity ('round' or 'shot')
        entity_ids: List of entity IDs that were synced
        request: FastAPI request object
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If device not found or invalid entity type
    """
    # Check rate limit
    check_rate_limit(request, current_user["id"])
    
    # Validate entity type
    if entity_type not in ['round', 'shot']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid entity type. Must be 'round' or 'shot'"
        )
    
    conn = db.connect()
    device_manager = DeviceManager(conn)
    
    # Verify device belongs to user
    device_info = device_manager.get_device_by_id(
        user_id=current_user["id"],
        device_id=device_id
    )
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Log sync for each entity
    for entity_id in entity_ids:
        device_manager.log_device_sync(
            device_uuid=device_info['device_uuid'],
            entity_type=entity_type,
            entity_id=entity_id,
            sync_direction='FROM_CLOUD'
        )
    
    # Update device sync timestamp
    device_manager.update_device_sync_timestamp(device_info['device_uuid'])
    
    return {
        "success": True,
        "message": f"Marked {len(entity_ids)} {entity_type}(s) as synced",
        "device_id": device_id,
        "synced_count": len(entity_ids)
    }
