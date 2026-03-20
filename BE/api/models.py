"""
Database models
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=False), nullable=False)
    created_at = Column(DateTime(timezone=False), default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cuisine_type = Column(String(100), nullable=True)
    price_level = Column(Integer, nullable=True)  # 0-4 for Google Places
    dietary_restrictions = Column(Text, nullable=True)  # JSON string for flexibility
    preferred_radius = Column(Integer, default=5000)  # in meters
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FavoriteRestaurant(Base):
    __tablename__ = "favorite_restaurants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    place_id = Column(String(100), nullable=False)  # Google Places place_id
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    cuisine_type = Column(String(100), nullable=True)
    rating = Column(Float, nullable=True)
    price_level = Column(Integer, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Nullable for anonymous searches
    query = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    radius = Column(Integer, nullable=True)
    cuisine_type = Column(String(100), nullable=True)
    price_level = Column(Integer, nullable=True)
    results_count = Column(Integer, default=0)
    searched_at = Column(DateTime(timezone=True), server_default=func.now())

class UserClick(Base):
    __tablename__ = "user_clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(String(100), nullable=False)  # Google Places place_id or business identifier
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    clicked_at = Column(DateTime(timezone=False), server_default=func.now())

class UserLocation(Base):
    __tablename__ = "user_location"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    city = Column(String(100), nullable=True)  # Primary focus - city name
    state = Column(String(50), nullable=True)  # State/province
    country = Column(String(50), nullable=True)  # Country
    recorded_at = Column(DateTime(timezone=False), server_default=func.now())

class UserSwipe(Base):
    __tablename__ = "user_swipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(String(100), nullable=False)
    swiped_at = Column(DateTime(timezone=False), server_default=func.now())
