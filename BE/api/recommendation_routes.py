"""
Recommendation API Routes
Uses your existing algorithm with real database data
"""
import sys
import os
import json
import random
import asyncio
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any

from Vectorization.vectorize import build_yelp_user_vectors, cat_to_index, build_click_vector, find_neighbors, aggregate_neighbor_vector, rank_restaurants
from sqlalchemy.ext.asyncio import AsyncSession
from . import schemas
from .dependencies import get_current_user
from .database import get_async_db
from .models import UserClick, UserLocation, UserSwipe
from sqlalchemy import select

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# ---------------------------------------------------------------------------
# Module-level cache — loaded once at startup, reused on every request
# ---------------------------------------------------------------------------
_business_index: dict = {}
_business_names: dict = {}
_yelp_user_vectors = None
_cat_to_index = None


def load_indexes():
    """
    Load all heavy data files and precompute Yelp user vectors once at startup.
    Called from main.py lifespan / startup event.
    """
    global _business_index, _business_names, _yelp_user_vectors, _cat_to_index

    base_dir = os.path.dirname(os.path.dirname(__file__))
    business_index_path  = os.path.join(base_dir, "data_extraction", "complete_business_index.json")
    category_review_path = os.path.join(base_dir, "data_extraction", "category_review_index.json")
    business_names_path  = os.path.join(base_dir, "data_extraction", "yelp_business_food_only.jsonl")

    print("Loading recommendation indexes...")

    with open(business_index_path, "r", encoding="utf-8") as f:
        _business_index = json.load(f)

    with open(category_review_path, "r", encoding="utf-8") as f:
        category_review_index = json.load(f)

    _cat_to_index = cat_to_index
    _yelp_user_vectors = build_yelp_user_vectors(category_review_index, cat_to_index)

    try:
        with open(business_names_path, "r", encoding="utf-8") as f:
            for line in f:
                business = json.loads(line.strip())
                bid  = business.get("business_id")
                name = business.get("name")
                if bid and name and bid in _business_index:
                    _business_names[bid] = name
    except FileNotFoundError:
        print("Warning: business names file not found — will use IDs as fallback names")

    print(f"Indexes loaded: {len(_business_index)} businesses, {len(_business_names)} names")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def get_user_clicks_from_database(user_id: str, limit: int = 100) -> List[str]:
    """Get real user clicks from the database."""
    async with get_async_db() as db:
        result = await db.execute(
            select(UserClick.business_id)
            .where(UserClick.user_id == user_id)
            .order_by(UserClick.clicked_at.desc())
            .limit(limit)
        )
        return [str(click) for click in result.scalars().all()]


async def get_user_swipes_from_database(user_id: str, limit: int = 100) -> List[str]:
    """Get right-swiped restaurants from the database."""
    async with get_async_db() as db:
        result = await db.execute(
            select(UserSwipe.business_id)
            .where(UserSwipe.user_id == user_id)
            .order_by(UserSwipe.swiped_at.desc())
            .limit(limit)
        )
        return [str(swipe) for swipe in result.scalars().all()]


async def get_user_city(user_id) -> Optional[str]:
    """Get the user's most recently recorded city."""
    async with get_async_db() as db:
        result = await db.execute(
            select(UserLocation.city)
            .where(UserLocation.user_id == user_id)
            .order_by(UserLocation.recorded_at.desc())
            .limit(1)
        )
        row = result.fetchone()
        return row[0] if row else None


# ---------------------------------------------------------------------------
# Algorithm helper
# ---------------------------------------------------------------------------

async def generate_recommendations_with_algorithm(user_id: str, top_k: int = 10) -> Dict:
    """Generate recommendations using the preloaded indexes."""
    try:

        if not _business_index or _yelp_user_vectors is None:
            return {
                "success": False,
                "error": "Indexes not loaded — server may still be starting up",
                "recommendations": [],
            }

        # Fetch both clicks and swipes in parallel
        user_clicks, user_swipes = await asyncio.gather(
            get_user_clicks_from_database(user_id),
            get_user_swipes_from_database(user_id),
        )

        if not user_clicks and not user_swipes:
            return {
                "success": False,
                "message": "No click history found for user",
                "recommendations": [],
            }

        import numpy as np

        # Build separate vectors — swipes weighted 3x clicks
        SWIPE_WEIGHT = 3.0
        click_vector = build_click_vector(user_clicks, _business_index, _cat_to_index) if user_clicks else np.zeros(len(_cat_to_index))
        swipe_vector = build_click_vector(user_swipes, _business_index, _cat_to_index) if user_swipes else np.zeros(len(_cat_to_index))

        # Combine: swipes dominate when present
        raw_vector = click_vector + SWIPE_WEIGHT * swipe_vector
        norm = np.linalg.norm(raw_vector)
        user_vector = raw_vector / norm if norm > 0 else raw_vector

        neighbors        = find_neighbors(user_vector, _yelp_user_vectors, k=5)
        aggregated_vector = (
            aggregate_neighbor_vector(neighbors, _yelp_user_vectors) if neighbors else user_vector
        )
        ranked_restaurants = rank_restaurants(aggregated_vector, _business_index, _cat_to_index)

        # Exclude anything the user has already seen (clicks + swipes)
        seen = set(user_clicks) | set(user_swipes)
        recommendations = []
        for business_id, score in ranked_restaurants:
            if business_id not in seen and len(recommendations) < top_k:
                categories    = _business_index[business_id]
                business_name = _business_names.get(business_id, f"Restaurant {business_id[:8]}...")
                recommendations.append({
                    "business_id": business_id,
                    "name":        business_name,
                    "score":       round(float(score), 4),
                    "categories":  categories,
                    "reason":      f"Based on your preferences for {', '.join(categories[:2])}",
                })

        return {
            "success":               True,
            "user_id":               user_id,
            "total_recommendations": len(recommendations),
            "recommendations":       recommendations,
            "user_click_count":      len(user_clicks),
            "user_swipe_count":      len(user_swipes),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "recommendations": []}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
    return {
        "status":  "healthy",
        "message": "Recommendations API is working",
        "indexes_loaded": len(_business_index) > 0,
    }


@router.get("/")
async def get_my_recommendations(
    top_k: int = 10,
    current_user: schemas.UserInDB = Depends(get_current_user),
):
    if top_k < 1 or top_k > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="top_k must be between 1 and 50")

    result = await generate_recommendations_with_algorithm(str(current_user.id), top_k)

    if not result["success"]:
        if "No click history" in result.get("message", ""):
            return {
                "success": True,
                "message": "No click history yet. Start clicking on restaurants to get personalized recommendations!",
                "recommendations": [],
                "user_id": str(current_user.id),
            }
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result


@router.get("/top20")
async def get_top_20_recommendations(
    current_user: schemas.UserInDB = Depends(get_current_user),
):
    result = await generate_recommendations_with_algorithm(str(current_user.id), 20)

    if not result["success"]:
        if "No click history" in result.get("message", ""):
            return {
                "success": True,
                "message": "No click history yet. Start clicking on restaurants to get personalized recommendations!",
                "recommendations": [],
                "user_id": str(current_user.id),
                "total_recommendations": 0,
            }
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return {**result, "message": "Top 20 recommendations based on your food preferences"}


@router.get("/random")
async def get_random_restaurants_from_city(
    count: int = 10,
    current_user: schemas.UserInDB = Depends(get_current_user),
):
    if count < 1 or count > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="count must be between 1 and 50")

    if not _business_index:
        raise HTTPException(status_code=500, detail="Business index not loaded")

    user_city = await get_user_city(current_user.id)

    all_businesses = list(_business_index.items())
    random.shuffle(all_businesses)
    selected = all_businesses[:count]

    formatted = [
        {
            "business_id": bid,
            "name":        _business_names.get(bid, f"Restaurant {bid[:8]}..."),
            "categories":  cats,
            "reason":      "Random selection from available restaurants",
        }
        for bid, cats in selected
    ]

    return {
        "success":           True,
        "user_id":           str(current_user.id),
        "user_city":         user_city,
        "total_restaurants": len(formatted),
        "restaurants":       formatted,
        "message":           f"Random restaurants" + (f" from {user_city}" if user_city else " from available selection"),
    }


@router.get("/user/{user_id}")
async def get_user_recommendations(
    user_id: str,
    top_k: int = 10,
    current_user: schemas.UserInDB = Depends(get_current_user),
):
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only view your own recommendations")

    result = await generate_recommendations_with_algorithm(user_id, top_k)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result

@router.get("/next")
async def get_next_restaurant(
    current_user: schemas.UserInDB = Depends(get_current_user),
):
    if not _business_index:
        raise HTTPException(status_code=500, detail="Business index not loaded")

    bid, cats = random.choice(list(_business_index.items()))
    return {
        "business_id": bid,
        "name": _business_names.get(bid, f"Restaurant {bid[:8]}..."),
        "categories": cats,
    }