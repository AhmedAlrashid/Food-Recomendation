"""
Database setup and initialization script
Run this script to set up your database and create initial tables
"""
import os
import sys
from dotenv import load_dotenv

# Add the api directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(current_dir, 'api')
sys.path.insert(0, api_dir)

# Load environment variables
load_dotenv()

def main():
    print("🍴 Food Recommendation API - Database Setup")
    print("=" * 50)
    
    # Check for required environment variables
    google_api_key = os.getenv('GOOGLE_API_KEY')
    secret_key = os.getenv('SECRET_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    print(f"Database URL: {database_url}")
    
    if not google_api_key:
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment variables")
        print("   Please add your Google Places API key to your .env file")
    else:
        print("✅ Google API Key found")
    
    if not secret_key:
        print("⚠️  WARNING: SECRET_KEY not found in environment variables")
        print("   Please add a secret key for JWT tokens to your .env file")
    else:
        print("✅ Secret Key found")
    
    print("\n📊 Creating database tables...")
    
    try:
        from api.init_db import create_tables
        create_tables()
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        print("Make sure your database connection is properly configured.")
        return False
    
    print("\n🚀 Setup complete!")
    print("\nNext steps:")
    print("1. Make sure your .env file has all required variables (see .env.example)")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Start the server: uvicorn api.main:app --reload")
    print("4. Visit http://localhost:8000/docs for interactive API documentation")
    
    return True

if __name__ == "__main__":
    main()