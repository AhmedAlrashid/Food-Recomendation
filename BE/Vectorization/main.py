import json
import numpy as np
import random
from typing import Dict, List, Tuple
import sys
import os
import asyncio
import uuid

# Add paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_extraction")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

from vectorize import (
    cat_to_index,
    build_click_vector,
    build_yelp_user_vectors,
    find_neighbors,
    aggregate_neighbor_vector,
    rank_restaurants,
    build_restaurant_vector
)
from buisiness_cleaning import FOOD_CATEGORIES

# Database imports
from database import get_async_db
from models import User, UserClick
from sqlalchemy import select

class RestaurantRecommendationSystem:
    def __init__(self):
        self.business_index = {}
        self.business_names = {}
        self.category_review_index = {}
        self.yelp_user_vectors = {}
        self.load_indexes()
        
    def load_indexes(self):
        """Load the business and category review indexes from the data files."""
        # Business Index Path: business_id -> [categories]
        business_index_path = os.path.join("..", "data_extraction", "complete_business_index.json")
        
        # Category Review Index Path: category -> {user_id: review_count}
        category_review_path = os.path.join("..", "data_extraction", "category_review_index.json")
        
        print(f"Expected Business Index Path: {business_index_path}")
        print(f"Expected Category Review Index Path: {category_review_path}")
        
        # Load business index (must exist)
        try:
            with open(business_index_path, 'r', encoding='utf-8') as f:
                self.business_index = json.load(f)
            print(f"Loaded business index with {len(self.business_index)} businesses")
        except FileNotFoundError:
            print(f"Business index not found at {business_index_path}")
            print("   Run 'python BE/data_extraction/datatset.py' to build indexes first")
            raise FileNotFoundError(f"Required business index file not found: {business_index_path}")
            
        # Load category review index (must exist for recommendations)
        try:
            with open(category_review_path, 'r', encoding='utf-8') as f:
                self.category_review_index = json.load(f)
            print(f" Loaded category review index with {len(self.category_review_index)} categories")
        except FileNotFoundError:
            print(f" Category review index not found at {category_review_path}")
            print("   Run 'python BE/data_extraction/datatset.py' to build indexes first")
            raise FileNotFoundError(f"Required category review index file not found: {category_review_path}")
        
        # Build Yelp user vectors from the category review index
        self.yelp_user_vectors = build_yelp_user_vectors(self.category_review_index, cat_to_index)
        print(f" Built vectors for {len(self.yelp_user_vectors)} Yelp users")
        
        # Load business names
        self.load_business_names()
        
    def load_business_names(self):
        """Load business names from the JSONL file."""
        business_data_path = os.path.join("..", "data_extraction", "yelp_business_food_only.jsonl")
        
        print(f"Loading business names from: {business_data_path}")
        
        count = 0
        try:
            with open(business_data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    business = json.loads(line.strip())
                    bid = business.get('business_id')
                    name = business.get('name')
                    
                    if bid and name and bid in self.business_index:
                        self.business_names[bid] = name
                        count += 1
                        
            print(f" Loaded {count} business names")
            
        except FileNotFoundError:
            print(f" Business data file not found at {business_data_path}")
            print("   Business names will show as IDs")



    async def get_user_clicks_from_database(self, user_id: str, limit: int = 100) -> List[str]:
        """
        Get real user clicks from database instead of simulating them.
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of recent clicks to retrieve
            
        Returns:
            List of business IDs the user has actually clicked
        """
        async for db in get_async_db():
            try:
                result = await db.execute(
                    select(UserClick.business_id)
                    .where(UserClick.user_id == user_id)
                    .order_by(UserClick.clicked_at.desc())
                    .limit(limit)
                )
                clicks = result.scalars().all()
                return [str(click) for click in clicks]
            finally:
                await db.close()

    async def get_all_users_with_clicks(self) -> List[str]:
        """Get all user IDs that have click history."""
        async for db in get_async_db():
            try:
                result = await db.execute(
                    select(UserClick.user_id).distinct()
                )
                user_ids = result.scalars().all()
                return [str(uid) for uid in user_ids]
            finally:
                await db.close()

    def get_recommendations_for_user(self, user_clicks: List[str], top_k: int = 10) -> List[Tuple[str, float, List[str]]]:
        """
        Get restaurant recommendations for a simulated user.
        
        Args:
            user_clicks: List of business IDs the user has clicked
            top_k: Number of recommendations to return
            
        Returns:
            List of tuples (business_id, score, categories)
        """
        # Build user vector from clicks
        user_vector = build_click_vector(user_clicks, self.business_index, cat_to_index)
        
        # Find similar users from Yelp data
        neighbors = find_neighbors(user_vector, self.yelp_user_vectors, k=5)
        
        # Aggregate neighbor preferences
        if neighbors:
            aggregated_vector = aggregate_neighbor_vector(neighbors, self.yelp_user_vectors)
        else:
            aggregated_vector = user_vector
        
        # Rank all restaurants
        ranked_restaurants = rank_restaurants(aggregated_vector, self.business_index, cat_to_index)
        
        # Filter out restaurants user has already clicked and add category info
        recommendations = []
        for bid, score in ranked_restaurants:
            if bid not in user_clicks and len(recommendations) < top_k:
                categories = self.business_index[bid]
                recommendations.append((bid, score, categories))
        
        return recommendations

    def create_diverse_user_profiles(self) -> List[Dict]:
        """Create 4 different user profiles with distinct preferences."""
        
        user_profiles = [
            {
                "name": "Pizza & Italian Lover",
                "description": "Loves Italian food, pizza, and classic comfort food",
                "preferences": ["Italian", "Pizza", "Pasta", "Comfort Food", "American (Traditional)"]
            },
            {
                "name": "Asian Cuisine Explorer", 
                "description": "Enjoys diverse Asian cuisines and sushi",
                "preferences": ["Japanese", "Chinese", "Thai", "Korean", "Sushi Bars", "Ramen", "Vietnamese"]
            },
            {
                "name": "Health-Conscious Foodie",
                "description": "Prefers healthy, fresh, and vegetarian options",
                "preferences": ["Vegetarian", "Vegan", "Salads", "Juice Bars & Smoothies", "Mediterranean", "Greek"]
            },
            {
                "name": "Spicy Food Enthusiast",
                "description": "Loves spicy and bold flavors from various cultures",
                "preferences": ["Mexican", "Indian", "Thai", "Korean", "Middle Eastern", "Caribbean", "Hot Pot"]
            }
        ]
        
        return user_profiles

    async def run_with_real_users(self):
        """Run the recommendation system with real users from the database."""
        print(" Starting Restaurant Recommendation with Real Users")
        print("=" * 60)
        
        # Get users with click history from database
        users_with_clicks = await self.get_all_users_with_clicks()
        
        if not users_with_clicks:
            print("⚠️  No users with click history found in database")
            print("   Add some click data first using the /tracking/click API")
            return
            
        print(f"📊 Found {len(users_with_clicks)} users with click history")
        
        # Process first few users (limit for demo)
        for i, user_id in enumerate(users_with_clicks[:5], 1):
            print(f"\n USER {i}: {user_id}")
            
            # Get real user clicks from database
            user_clicks = await self.get_user_clicks_from_database(user_id)
            print(f"📊 User has {len(user_clicks)} restaurant clicks")
            
            if not user_clicks:
                print("   No clicks found for this user")
                continue
            
            # Use your existing algorithm to get recommendations
            recommendations = self.get_recommendations_for_user(user_clicks, top_k=10)
            
            print(f"\n TOP 10 RESTAURANT RECOMMENDATIONS:")
            print("-" * 50)
            
            for rank, (bid, score, categories) in enumerate(recommendations, 1):
                # Use actual restaurant name if available, otherwise fallback to business ID
                display_name = self.business_names.get(bid, f"Business {bid[:8]}...")
                print(f"{rank:2d}. {display_name}")
                print(f"    Score: {score:.4f}")
                print(f"    Categories: {', '.join(categories[:3])}{'...' if len(categories) > 3 else ''}")
                print()
            
            if not recommendations:
                print(" No recommendations could be generated for this user")
            
            print("=" * 60)

async def main():
    """Main function to run the restaurant recommendation system with real database users."""
    
    print(" Food Recommendation System")
    print(" Using Real User Data from Database")
    print("\n Expected Index Paths:")
    print("   - Business Index: BE/data_extraction/complete_business_index.json")
    print("   - Category Reviews: BE/data_extraction/category_review_index.json")
    print("\n" + "=" * 70)
    
    try:
        # Initialize the recommendation system
        rec_system = RestaurantRecommendationSystem()
        
        # Run with real users from database
        await rec_system.run_with_real_users()
         
        print("\n System Complete!")
        print("\n Summary:")
        print(f"   - Total Businesses in Index: {len(rec_system.business_index)}")
        print(f"   - Total Food Categories: {len(FOOD_CATEGORIES)}")
        print(f"   - Yelp Users with Vectors: {len(rec_system.yelp_user_vectors)}")
        print(f"   - Using Real User Click Data from Database")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure your database is running and contains user click data")

# API Integration Function
async def get_recommendations_for_user_api(user_id: str, top_k: int = 10) -> Dict:
    """
    API function to get recommendations for a specific user.
    Uses your existing algorithm with real database data.
    
    Args:
        user_id: UUID string of the user
        top_k: Number of recommendations to return
        
    Returns:
        Dictionary with recommendations in API format
    """
    try:
        # Initialize your recommendation system
        rec_system = RestaurantRecommendationSystem()
        
        # Get user's click history from database
        user_clicks = await rec_system.get_user_clicks_from_database(user_id)
        
        if not user_clicks:
            return {
                "success": False,
                "message": "No click history found for user",
                "recommendations": []
            }
        
        # Use your existing algorithm
        recommendations = rec_system.get_recommendations_for_user(user_clicks, top_k)
        
        # Format for API response
        formatted_recs = []
        for business_id, score, categories in recommendations:
            business_name = rec_system.business_names.get(business_id, f"Restaurant {business_id[:8]}...")
            formatted_recs.append({
                "business_id": business_id,
                "name": business_name,
                "score": round(float(score), 4),
                "categories": categories,
                "reason": f"Based on your preferences for {', '.join(categories[:2])}"
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "total_recommendations": len(formatted_recs),
            "recommendations": formatted_recs,
            "user_click_count": len(user_clicks)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "recommendations": []
        }

