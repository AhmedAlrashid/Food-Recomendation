import json
FOOD_CATEGORIES = {
    # Core
    "Restaurants",
    "Food",
    "Fast Food",
    "Food Trucks",
    "Pop-Up Restaurants",
    "Street Vendors",

    # Dining formats
    "Cafes",
    "Coffee & Tea",
    "Tea Rooms",
    "Breakfast & Brunch",
    "Bakeries",
    "Desserts",
    "Ice Cream & Frozen Yogurt",
    "Juice Bars & Smoothies",
    "Donuts",
    "Bagels",
    "Cupcakes",
    "Patisserie/Cake Shop",

    # Bars / nightlife food
    "Bars",
    "Pubs",
    "Sports Bars",
    "Wine Bars",
    "Beer Bar",
    "Cocktail Bars",
    "Dive Bars",
    "Lounges",
    "Brewpubs",
    "Breweries",
    "Gastropubs",

    # Cuisine styles
    "American (Traditional)",
    "American (New)",
    "Mexican",
    "Italian",
    "Chinese",
    "Japanese",
    "Thai",
    "Indian",
    "Vietnamese",
    "Korean",
    "Middle Eastern",
    "Mediterranean",
    "Greek",
    "Lebanese",
    "Turkish",
    "Persian/Iranian",
    "French",
    "Spanish",
    "Brazilian",
    "Argentine",
    "African",
    "Ethiopian",
    "Caribbean",
    "Cuban",
    "Peruvian",
    "Colombian",
    "Filipino",
    "Hawaiian",
    "German",
    "Irish",
    "British",
    "Russian",

    # Dish / specialization
    "Pizza",
    "Burgers",
    "Sandwiches",
    "Seafood",
    "Steakhouses",
    "Sushi Bars",
    "Ramen",
    "Dim Sum",
    "Hot Pot",
    "Barbeque",
    "Chicken Wings",
    "Cheesesteaks",
    "Falafel",
    "Kebab",
    "Tacos",
    "Tex-Mex",
    "Soul Food",
    "Comfort Food",
    "Gluten-Free",
    "Vegan",
    "Vegetarian",
    "Halal",
    "Kosher",

    # Markets / food retail
    "Grocery",
    "Ethnic Grocery",
    "International Grocery",
    "Specialty Food",
    "Food Court",
    "Farmers Market",
    "Seafood Markets",
    "Meat Shops",
    "Cheese Shops",
}

Buffer_size = 15_000
categories = set()

def getAllcategories():
    with open(r"BE\data_extraction\Yelp-JSON\yelp_academic_dataset_business.json", "r", encoding="utf-8") as file:
        for line in file:
            business = json.loads(line)

            raw_categories = business.get("categories")
            if raw_categories is None:
                continue

            loadedCategories = raw_categories.split(",")

            for category in loadedCategories:
                clean = category.strip()
                categories.add(clean)

    # print ALL unique categories
    print(sorted(categories))


def removeAnythingNotrelatedToResteraunts():
    businesses = []
    BATCH_SIZE = 15_000

    input_path = r"BE\data_extraction\Yelp-JSON\yelp_academic_dataset_business.json"
    output_path = r"BE\data_extraction\yelp_business_food_only.jsonl"

    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for line in infile:
            business = json.loads(line)

            raw_categories = business.get("categories")
            if raw_categories is None:
                continue

            loadedCategories = []
            for c in raw_categories.split(","):
                loadedCategories.append(c.strip())

            # CORRECT food check
            is_restaurant = False
            for cat in loadedCategories:
                if cat in FOOD_CATEGORIES:
                    is_restaurant = True
                    break

            if not is_restaurant:
                continue

            # buffer the ORIGINAL line
            businesses.append(line)

            # batch write
            if len(businesses) >= BATCH_SIZE:
                for record in businesses:
                    outfile.write(record)
                businesses.clear()

        # flush remaining
        for record in businesses:
            outfile.write(record)

if __name__ == "__main__":
    # Only run the full extraction when executed as a script.
    removeAnythingNotrelatedToResteraunts()