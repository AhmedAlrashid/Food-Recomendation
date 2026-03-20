"""
Google Places API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import requests
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import schemas, models
from .database import get_db_dependency
from .dependencies import get_current_user

load_dotenv()
KEY = os.getenv("GOOGLE_API_KEY")

if not KEY:
    print("⚠️  WARNING: Google API Key not set - Places search will not work")
    KEY = None

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/search")
def search_places(
    query: str = "restaurants",
    place_type: Optional[str] = None,
    keyword: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: int = 16000,
    minprice: Optional[int] = None,
    maxprice: Optional[int] = None,
    opennow: bool = True,
    limit: int = 20,
    page_token: Optional[str] = None
):
    if not KEY:
        raise HTTPException(status_code=503, detail="Google Places API is not configured.")

    try:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": KEY,
            "pagetoken": page_token,
            "location": f"{lat},{lng}" if lat and lng else None,
            "type": place_type,
            "keyword": keyword,
            "minprice": minprice,
            "maxprice": maxprice,
            "opennow": opennow,
        }
        if lat and lng:
            params["radius"] = min(radius, 50000)
        params = {k: v for k, v in params.items() if v is not None}

        res = requests.get(url, params=params, timeout=5)
        data = res.json()
    except Exception as e:
        raise HTTPException(500, detail=str(e))

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(400, detail=data.get("error_message"))

    results = data.get("results", [])[:limit]
    full_results = []

    for place in results:
        place_id = place.get("place_id")
        try:
            details_res = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={
                    "place_id": place_id,
                    "fields": "website,formatted_phone_number,international_phone_number,reviews,opening_hours,url,price_level,editorial_summary",
                    "key": KEY,
                },
                timeout=5,
            )
            details_data = details_res.json().get("result", {})
            place["website"]                    = details_data.get("website")
            place["phone_number"]               = details_data.get("formatted_phone_number")
            place["international_phone_number"] = details_data.get("international_phone_number")
            place["reviews"]                    = details_data.get("reviews")
            place["opening_hours"]              = details_data.get("opening_hours")
            place["google_maps_url"]            = details_data.get("url")
            place["price_level"]                = details_data.get("price_level")
            place["editorial_summary"]          = details_data.get("editorial_summary")
        except Exception:
            pass
        full_results.append(place)

    return {
        "results": full_results,
        "next_page_token": data.get("next_page_token"),
        "status": data.get("status"),
    }


@router.post("/favorites")
async def add_favorite(
    favorite: schemas.FavoriteRestaurantCreate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    existing_result = await db.execute(
        select(models.FavoriteRestaurant).where(
            models.FavoriteRestaurant.user_id == current_user.id,
            models.FavoriteRestaurant.place_id == favorite.place_id
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(400, detail="Restaurant already in favorites")

    db_favorite = models.FavoriteRestaurant(user_id=current_user.id, **favorite.dict())
    db.add(db_favorite)
    await db.commit()
    await db.refresh(db_favorite)
    return {"message": "Added to favorites", "favorite": db_favorite}


@router.get("/favorites", response_model=list[schemas.FavoriteRestaurantResponse])
async def get_favorites(
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    result = await db.execute(
        select(models.FavoriteRestaurant).where(
            models.FavoriteRestaurant.user_id == current_user.id
        )
    )
    return result.scalars().all()


@router.delete("/favorites/{place_id}")
async def remove_favorite(
    place_id: str,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    result = await db.execute(
        select(models.FavoriteRestaurant).where(
            models.FavoriteRestaurant.user_id == current_user.id,
            models.FavoriteRestaurant.place_id == place_id
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(404, detail="Favorite not found")

    await db.delete(favorite)
    await db.commit()
    return {"message": "Removed from favorites"}