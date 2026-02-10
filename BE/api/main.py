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
def places(query: str = "restaurants in Irvine"):
    #asdf
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": KEY}

    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(400, detail=data.get("error_message"))
    
    results = data.get("results", [])

    return {"results": results}