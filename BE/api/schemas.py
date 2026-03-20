"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    id: uuid.UUID
    hashed_password: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserPreferenceBase(BaseModel):
    cuisine_type: Optional[str] = None
    price_level: Optional[int] = None
    dietary_restrictions: Optional[str] = None
    preferred_radius: Optional[int] = 5000


class UserPreferenceCreate(UserPreferenceBase):
    pass


class UserPreferenceResponse(UserPreferenceBase):
    id: int
    user_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FavoriteRestaurantBase(BaseModel):
    place_id: str
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cuisine_type: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None


class FavoriteRestaurantCreate(FavoriteRestaurantBase):
    pass


class FavoriteRestaurantResponse(FavoriteRestaurantBase):
    id: int
    user_id: uuid.UUID
    added_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PlaceSearchRequest(BaseModel):
    query: str = "restaurants"
    place_type: Optional[str] = None
    keyword: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius: int = 16000
    minprice: Optional[int] = None
    maxprice: Optional[int] = None
    opennow: bool = True
    limit: int = 20
    page_token: Optional[str] = None


class UserClickCreate(BaseModel):
    business_id: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class UserClickResponse(UserClickCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    clicked_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserLocationCreate(BaseModel):
    lat: float
    lng: float
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class UserLocationResponse(UserLocationCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserSwipeCreate(BaseModel):
    business_id: str

class UserSwipeResponse(UserSwipeCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    swiped_at: datetime
    model_config = ConfigDict(from_attributes=True)