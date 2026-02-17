from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests, os, sys
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict

# Get the current directory of main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (the 'BE' folder)
parent_dir = os.path.dirname(current_dir)
# Add 'BE' to the system path so Python can find 'Login'
sys.path.append(parent_dir)

from Login.auth import create_access_token, verify_password, get_password_hash, verify_token


# Create FastAPI app instance
app = FastAPI()

# Configure CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
KEY = os.getenv("GOOGLE_API_KEY")

if not KEY:
    raise RuntimeError("Google API Key needs to be set ")


# Define a simple GET endpoint
@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/places")
def places(
        # Name, city, cuisine all handled by Google as one text query
        # name: str = None,
        # city: str = None,
        # cuisine: str = None
        query: str = "restaurants",
        place_type: str = None, #restaurant, cafe, bakery
        keyword: str = None, #cuisines like sushi and vegan
        lat: float = None,
        lng: float = None,
        radius: int = 16000, #is in meters
        minprice: int = None, # $ 0-4
        maxprice: int = None, # $$$$ 0-4
        opennow: bool = True,
        limit: int = 20,
        rankby: str = "prominence", # or distance from location but if so cannot specify radius
        page_token: str = None
    ):
    
    # Below was extra I tried if we need strict location filtering
    # use_nearby_search = lat is not None and lng is not None

    # if use_nearby_search: #doesn't allow query
    #     url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    #     params = {
    #         "location": f"{lat},{lng}" if lat and lng else None,
    #         "radius": min(radius, 50000), #google will return invalid request if too far
    #         "keyword": keyword,
    #         "type": place_type,
    #         "key": KEY,
    #         "keyword": keyword,
    #         "minprice": minprice,
    #         "maxprice": maxprice,
    #         "opennow": opennow,
    #         "rankby": rankby, 
    #         "pagetoken": page_token,
    #         }
    
    if rankby not in ("prominence", "distance"):
        raise HTTPException(400, detail="rankby must be 'prominence' or 'distance'")


    try:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": KEY,
            # below are optional
            "pagetoken": page_token,
            "location": f"{lat},{lng}" if lat and lng else None,
            "type": place_type,
            "keyword": keyword,
            "minprice": minprice,
            "maxprice": maxprice,
            "opennow": opennow,
            "rankby": rankby,
        }


        if lat and lng and rankby != "distance":
            params["radius"] = min(radius, 50000)

        params = {k: v for k, v in params.items() if v is not None}

        res = requests.get(url, params=params, timeout=5)
        data = res.json()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(400, detail=data.get("error_message"))
    
    results = data.get("results", [])

    return {
        "results": results[:limit],
        "next_page_token": data.get("next_page_token"),
        "status": data.get("status"),
    }

#python -m uvicorn main:app --reload

# Login ----------------------------------------------------------------------

"""
Dependencies needed:
pip install python-multipart
pip install "bcrypt==3.2.2" 
pip install passlib 
pip install "python-jose[cryptography]"
pip install pyjwt   
"""

# Pydantic models
class User(BaseModel):
    username: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Simulate a user database
fake_users_db: Dict[str, UserInDB] = {
    "testuser": UserInDB(username="testuser", hashed_password=get_password_hash("password123"))
}

# OAuth2PasswordBearer is used to extract the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # "login" is the URL of our login endpoint

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)
    # Lookup user from real db instead of mock fake_users_db
    if username not in fake_users_db: # <------------- Change to real db later
         raise credentials_exception
    return fake_users_db[username]


@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_in_db = fake_users_db.get(form_data.username) # <---------- Change to real db later
    if not user_in_db or not verify_password(form_data.password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user_in_db.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    # This endpoint is protected. 'current_user' is only available if a valid token is provided
    return {"username": current_user.username, "message": "You have access to a protected route!"}