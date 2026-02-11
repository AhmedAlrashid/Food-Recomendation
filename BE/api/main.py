from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests, os

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
        "results": results[:limit]
    }

#python -m uvicorn main:app --reload