"""
Authentication routes with session management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta, datetime
from typing import Optional
import sys, os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from Login.auth import create_access_token, verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from . import schemas, models
from .database import get_db_dependency
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", response_model=schemas.UserResponse)
async def register_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db_dependency)
):
    db_user_result = await db.execute(select(models.User).where(models.User.username == user.username))
    if db_user_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")

    if user.email:
        db_email_result = await db.execute(select(models.User).where(models.User.email == user.email))
        if db_email_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_dependency)
):
    result = await db.execute(select(models.User).where(models.User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(current_user: schemas.UserInDB = Depends(get_current_user)):
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.UserInDB = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
async def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: schemas.UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_dependency)
):
    db_user_result = await db.execute(select(models.User).where(models.User.id == current_user.id))
    db_user = db_user_result.scalar_one_or_none()

    for field, value in user_update.dict(exclude_unset=True).items():
        if field == "password":
            value = get_password_hash(value)
            field = "hashed_password"
        setattr(db_user, field, value)

    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/preferences", response_model=schemas.UserPreferenceResponse)
async def create_user_preferences(
    preferences: schemas.UserPreferenceCreate,
    current_user: schemas.UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_dependency)
):
    existing_result = await db.execute(
        select(models.UserPreference).where(models.UserPreference.user_id == current_user.id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        for field, value in preferences.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    db_preferences = models.UserPreference(user_id=current_user.id, **preferences.dict())
    db.add(db_preferences)
    await db.commit()
    await db.refresh(db_preferences)
    return db_preferences


@router.get("/preferences", response_model=Optional[schemas.UserPreferenceResponse])
async def get_user_preferences(
    current_user: schemas.UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_dependency)
):
    result = await db.execute(
        select(models.UserPreference).where(models.UserPreference.user_id == current_user.id)
    )
    return result.scalar_one_or_none()


@router.get("/debug-token")
async def debug_token(token: str = Depends(oauth2_scheme)):
    try:
        from Login.auth import SECRET_KEY, ALGORITHM
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"success": True, "payload": payload, "secret_key_prefix": SECRET_KEY[:10]}
    except Exception as e:
        return {"success": False, "error": str(e)}