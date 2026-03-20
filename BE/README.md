# Food Recommendation Backend API

A FastAPI-based backend for a food recommendation system with Google Places integration and user management.

## 🏗 Project Structure

```
BE/
├── api/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI app
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── dependencies.py      # Shared dependencies
│   ├── auth_routes.py       # Authentication endpoints
│   ├── places_routes.py     # Google Places API endpoints
│   └── init_db.py          # Database initialization
├── Login/
│   └── auth.py             # JWT utilities
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── setup_database.py      # Database setup script
```

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Initialize Database**
   ```bash
   python setup_database.py
   ```

4. **Start the Server**
   ```bash
   uvicorn api.main:app --reload
   ```

5. **View API Documentation**
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🔧 Configuration

### Required Environment Variables

- `GOOGLE_API_KEY`: Your Google Places API key
- `SECRET_KEY`: JWT secret key (generate a strong random key)
- `DATABASE_URL`: Database connection string

### Database Configuration

The API supports multiple databases. Update your `DATABASE_URL` in `.env`:

**SQLite (Default - for development):**
```
DATABASE_URL=sqlite:///./food_recommendation.db
```

**PostgreSQL:**
```
DATABASE_URL=postgresql://username:password@localhost:5432/food_recommendation
```

**MySQL:**
```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/food_recommendation
```

## 📝 API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info
- `PUT /auth/me` - Update user info
- `POST /auth/preferences` - Set user preferences
- `GET /auth/preferences` - Get user preferences

### Places (`/places`)
- `GET /places/search` - Search restaurants (public)
- `POST /places/favorites` - Add to favorites (auth required)
- `GET /places/favorites` - Get user favorites (auth required)
- `DELETE /places/favorites/{place_id}` - Remove from favorites (auth required)

### Other
- `GET /` - API info
- `GET /health` - Health check

## 🗄 Database Schema

### Users
- User accounts with authentication
- Profile information and preferences

### User Preferences
- Cuisine types, price levels, dietary restrictions
- Default search radius

### Favorite Restaurants
- User's favorite places from Google Places
- Cached restaurant information

### Search History
- Track user search patterns (if authenticated)

## 🛠 Development

### Adding New Endpoints

1. Create a new router file in `/api/`
2. Define your endpoints using FastAPI
3. Include the router in `main.py`

### Database Changes

1. Update models in `models.py`
2. Update schemas in `schemas.py` 
3. Run the database setup script to apply changes

### Authentication

Authentication is handled via JWT tokens. Protected endpoints use the `get_current_active_user` dependency from `dependencies.py`.

## 🔒 Security Notes

- Always use HTTPS in production
- Set a strong `SECRET_KEY`
- Configure CORS origins appropriately
- Consider rate limiting for production use

## 📦 Dependencies

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **JWT**: Authentication tokens
- **Requests**: HTTP client for Google API
- **BCrypt**: Password hashing