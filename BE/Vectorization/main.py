import json
import numpy as np
import random
from typing import Dict, List, Tuple
import sys
import os

# Add paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_extraction")))

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

class RestaurantRecommendationSystem:
    def __init__(self):
        self.business_index = {}
        self.category_review_index = {}
        self.yelp_user_vectors = {}
        self.load_indexes()
        
    def load_indexes(self):
        """Load the business and category review indexes from the data files."""
        # Business Index Path: business_id -> [categories]
        business_index_path = os.path.join("..", "data_extraction", "index", "complete_business_index.json")
        
        # Category Review Index Path: category -> {user_id: review_count}
        category_review_path = os.path.join("..", "data_extraction", "category_reviews_index.json")
        
        print(f"Expected Business Index Path: {business_index_path}")
        print(f"Expected Category Review Index Path: {category_review_path}")
        
        try:
            with open(business_index_path, 'r', encoding='utf-8') as f:
                self.business_index = json.load(f)
            print(f"Loaded business index with {len(self.business_index)} businesses")
        except FileNotFoundError:
            print(f"Business index not found at {business_index_path}")
            print("   You'll need to build this index first using your data extraction pipeline")
            # Create mock data for demonstration
            self.business_index = self._create_mock_business_index()
            
        try:
            with open(category_review_path, 'r', encoding='utf-8') as f:
                self.category_review_index = json.load(f)
            print(f"Loaded category review index with {len(self.category_review_index)} categories")
        except FileNotFoundError:
            print(f" Category review index not found at {category_review_path}")
            print("   You'll need to build this index first using your data extraction pipeline")
            # Create mock data for demonstration
            self.category_review_index = self._create_mock_category_index()
        
        # Build Yelp user vectors from the category review index
        self.yelp_user_vectors = build_yelp_user_vectors(self.category_review_index, cat_to_index)
        print(f"✅ Built vectors for {len(self.yelp_user_vectors)} Yelp users")

    def _create_mock_business_index(self) -> Dict[str, List[str]]:
        """Create mock business data for demonstration purposes."""
        print("🔧 Creating mock business data...")
        
        # Convert FOOD_CATEGORIES set to list for sampling
        categories_list = list(FOOD_CATEGORIES)
        
        mock_businesses = {}
        business_names = [
            "Tony's Pizza Palace", "Sakura Sushi", "El Mariachi Grill", "Burger Heaven",
            "Golden Dragon Chinese", "Pasta Bella", "Spice Route Indian", "BBQ Kingdom",
            "The French Bistro", "Taco Fiesta", "Noodle House", "Steakhouse Prime",
            "Mediterranean Delight", "Coffee Corner Cafe", "Sweet Treats Bakery",
            "Ocean's Bounty Seafood", "Punjab Palace", "Little Italy", "Seoul Kitchen",
            "Bangkok Street Food", "German Beer Garden", "Cuban Flavors", "Vegan Garden",
            "The Breakfast Club", "Midnight Diner", "Farm Fresh Market", "Artisan Chocolates",
            "Ramen-Ya", "Falafel King", "Texas BBQ Pit", "Greek Taverna"
        ]
        
        for i, name in enumerate(business_names):
            bid = f"business_{i+1:03d}"
            # Each business gets 1-4 random categories
            num_cats = random.randint(1, 4)
            business_categories = random.sample(categories_list, num_cats)
            mock_businesses[bid] = business_categories
            
        return mock_businesses

    def _create_mock_category_index(self) -> Dict[str, Dict[str, int]]:
        """Create mock category review data for demonstration."""
        print("🔧 Creating mock category review data...")
        
        mock_index = {}
        
        # Create mock users for each category
        for category in list(FOOD_CATEGORIES)[:20]:  # Use first 20 categories
            mock_index[category] = {}
            # Each category has 5-15 users with varying review counts
            num_users = random.randint(5, 15)
            for i in range(num_users):
                user_id = f"yelp_user_{category.lower().replace(' ', '_')}_{i+1:02d}"
                review_count = random.randint(1, 25)  # 1-25 reviews per category
                mock_index[category][user_id] = review_count
                
        return mock_index

    def simulate_user_preferences(self, primary_categories: List[str], num_clicks: int = 20) -> List[str]:
        """
        Simulate a user's clicking behavior based on their preferences.
        
        Args:
            primary_categories: List of categories the user prefers
            num_clicks: Number of restaurants the user has clicked on
            
        Returns:
            List of business IDs representing user's click history
        """
        user_clicks = []
        
        # Find businesses that match the user's preferred categories
        matching_businesses = []
        for bid, categories in self.business_index.items():
            if any(cat in categories for cat in primary_categories):
                # Add business multiple times if it matches multiple preferences
                weight = sum(1 for cat in categories if cat in primary_categories)
                matching_businesses.extend([bid] * weight)
        
        if not matching_businesses:
            print(f" No businesses found for categories {primary_categories}")
            return []
        
        # Simulate clicks with some preference weighting
        for _ in range(num_clicks):
            # 80% chance to click preferred categories, 20% chance for exploration
            if random.random() < 0.8 and matching_businesses:
                clicked_business = random.choice(matching_businesses)
            else:
                clicked_business = random.choice(list(self.business_index.keys()))
            
            user_clicks.append(clicked_business)
        
        return user_clicks

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

    def run_simulation(self):
        """Run the complete user simulation and recommendation system."""
        print(" Starting Restaurant Recommendation Simulation")
        print("=" * 60)
        
        user_profiles = self.create_diverse_user_profiles()
        
        for i, profile in enumerate(user_profiles, 1):
            print(f"\n USER {i}: {profile['name']}")
            print(f" {profile['description']}")
            print(f" Preferred Categories: {', '.join(profile['preferences'])}")
            
            # Simulate user clicks
            user_clicks = self.simulate_user_preferences(profile['preferences'], num_clicks=25)
            print(f"📊 Simulated {len(user_clicks)} restaurant visits")
            
            # Get recommendations
            recommendations = self.get_recommendations_for_user(user_clicks, top_k=10)
            
            print(f"\n TOP 10 RESTAURANT RECOMMENDATIONS:")
            print("-" * 50)
            
            for rank, (bid, score, categories) in enumerate(recommendations, 1):
                # Create a display name from business ID
                display_name = bid.replace('business_', 'Restaurant #')
                print(f"{rank:2d}. {display_name}")
                print(f"    Score: {score:.4f}")
                print(f"    Categories: {', '.join(categories[:3])}{'...' if len(categories) > 3 else ''}")
                print()
            
            if not recommendations:
                print(" No recommendations could be generated for this user")
            
            print("=" * 60)

def main():
    """Main function to run the restaurant recommendation system."""
    
    print(" Food Recommendation System")
    print(" Simulating Users and Generating Recommendations")
    print("\n Expected Index Paths:")
    print("   - Business Index: BE/data_extraction/index/complete_business_index.json")
    print("   - Category Reviews: BE/data_extraction/category_reviews_index.json")
    print("\n" + "=" * 70)
    
    # Initialize the recommendation system
    rec_system = RestaurantRecommendationSystem()
    
    # Run the simulation
    rec_system.run_simulation()
     
    print("\n Simulation Complete!")
    print("\n Summary:")
    print(f"   - Total Businesses in Index: {len(rec_system.business_index)}")
    print(f"   - Total Food Categories: {len(FOOD_CATEGORIES)}")
    print(f"   - Yelp Users with Vectors: {len(rec_system.yelp_user_vectors)}")
    print(f"   - User Profiles Simulated: 4")

if __name__ == "__main__":
    main()
