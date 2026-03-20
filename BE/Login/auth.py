from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import os

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key") # Use environment variables in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        print(f"Verifying token: {token[:20]}...")  # Debug: show first 20 chars
        print(f"Using SECRET_KEY: {SECRET_KEY[:10]}...")  # Debug: show first 10 chars of secret
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Token payload: {payload}")  # Debug: show decoded payload
        
        username: str = payload.get("sub")
        if username is None:
            print("No 'sub' field in token payload")  # Debug
            raise credentials_exception
            
        print(f"Extracted username: {username}")  # Debug
        return username # lookup username from db here if needed later on
    except JWTError as e:
        print(f"JWT Error: {e}")  # Debug: show actual JWT error
        raise credentials_exception
    except Exception as e:
        print(f"General error in verify_token: {e}")  # Debug: catch any other errors
        raise credentials_exception
