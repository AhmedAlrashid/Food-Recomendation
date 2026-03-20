"""
User tracking routes for clicks and location data
"""
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from . import schemas, models
from .database import get_db_dependency
from .dependencies import get_current_user

router = APIRouter(prefix="/tracking", tags=["tracking"])


async def reverse_geocode(lat: float, lng: float) -> dict:
    """Resolve lat/lng to city, state, country via Nominatim."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lng, "format": "json"},
                headers={"User-Agent": "your-app-name"},
            )
            data = response.json()
            address = data.get("address", {})
            return {
                "city": (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                ),
                "state":   address.get("state"),
                "country": address.get("country"),
            }
    except Exception:
        return {"city": None, "state": None, "country": None}


@router.post("/click", response_model=schemas.UserClickResponse)
async def record_user_click(
    click_data: schemas.UserClickCreate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    db_click = models.UserClick(
        user_id=current_user.id,
        business_id=click_data.business_id,
        lat=click_data.lat,
        lng=click_data.lng
    )
    db.add(db_click)
    await db.commit()
    await db.refresh(db_click)
    return db_click


@router.post("/location", response_model=schemas.UserLocationResponse)
async def record_user_location(
    location_data: schemas.UserLocationCreate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    # Reverse geocode server-side — frontend only needs to send lat/lng
    geo = await reverse_geocode(location_data.lat, location_data.lng)

    db_location = models.UserLocation(
        user_id=current_user.id,
        lat=location_data.lat,
        lng=location_data.lng,
        city=geo["city"],
        state=geo["state"],
        country=geo["country"],
    )
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location


@router.get("/clicks", response_model=List[schemas.UserClickResponse])
async def get_user_clicks(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    result = await db.execute(
        select(models.UserClick)
        .where(models.UserClick.user_id == current_user.id)
        .order_by(models.UserClick.clicked_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/locations", response_model=List[schemas.UserLocationResponse])
async def get_user_locations(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    result = await db.execute(
        select(models.UserLocation)
        .where(models.UserLocation.user_id == current_user.id)
        .order_by(models.UserLocation.recorded_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/clicks/business/{business_id}", response_model=List[schemas.UserClickResponse])
async def get_clicks_for_business(
    business_id: str,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    result = await db.execute(
        select(models.UserClick)
        .where(
            models.UserClick.user_id == current_user.id,
            models.UserClick.business_id == business_id
        )
        .order_by(models.UserClick.clicked_at.desc())
    )
    return result.scalars().all()


@router.get("/current-city", response_model=dict)
async def get_user_current_city(
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    result = await db.execute(
        select(models.UserLocation)
        .where(models.UserLocation.user_id == current_user.id)
        .order_by(models.UserLocation.recorded_at.desc())
        .limit(1)
    )
    location = result.scalar_one_or_none()

    if not location:
        return {"city": None, "state": None, "country": None, "message": "No location data found"}

    return {
        "city":        location.city,
        "state":       location.state,
        "country":     location.country,
        "lat":         location.lat,
        "lng":         location.lng,
        "recorded_at": location.recorded_at,
    }