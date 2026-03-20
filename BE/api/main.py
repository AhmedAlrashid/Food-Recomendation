"""
Main FastAPI application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .auth_routes import router as auth_router
from .places_routes import router as places_router
from .tracking_routes import router as tracking_router
from .recommendation_routes import router as recommendation_router, load_indexes

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load recommendation indexes once when the server starts
    try:
        load_indexes()
    except Exception as e:
        print(f"Warning: Could not load recommendation indexes: {e}")
    yield
    # Nothing to clean up


app = FastAPI(
    title="Food Recommendation API",
    description="A FastAPI application for food recommendations with Google Places integration",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(places_router)
app.include_router(tracking_router)
app.include_router(recommendation_router)


@app.get("/")
def read_root():
    return {
        "message": "Food Recommendation API",
        "version": "1.0.0",
        "status":  "running",
        "endpoints": {
            "authentication": "/auth",
            "places":         "/places",
            "docs":           "/docs",
            "redoc":          "/redoc",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)