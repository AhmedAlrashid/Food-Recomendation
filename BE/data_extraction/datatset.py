import json
from os import getcwd
from buisiness_cleaning import FOOD_CATEGORIES

# ---------------- CONFIG ----------------
INPUT_PATH = "BE/data_extraction/yelp_business_food_only.jsonl"
INPUT_PATH_REVIEWS = "BE/data_extraction/Yelp-JSON/yelp_academic_dataset_review.json" 
INPUT_PATH_BUSINESS_INDEX = "BE/data_extraction/index/complete_business_index.json"
OUTPUT_DIR = "BE/data_extraction/index"
BUFFER_SIZE = 15_000
# ----------------------------------------

def build_reviews_indexes():
    category_reviews_index = {} # Category -> {uid: # of reviews, ...}
    business_index = {} # Loaded index with bid -> categories

    with open(INPUT_PATH_BUSINESS_INDEX, "r", encoding="utf-8") as file:
        business_index = json.load(file)

    with open(INPUT_PATH_REVIEWS, "r", encoding="utf-8") as file:
        for line in file:
            review = json.loads(line)
            
            # Get values from review object
            uid = review.get("user_id")
            bid = review.get("business_id")
            star_rating = review.get("stars")
            # Gets all the categories related to the business
            try:
                categories = business_index[bid]
            except KeyError:
                pass

            if (star_rating >= 4.0):
                for category in categories:
                    # Creates new category if it doesn't exist in the dict
                    if category not in category_reviews_index.keys():
                        category_reviews_index[category] = {uid: 1}
                    else: 
                        if uid not in category_reviews_index[category].keys():
                            category_reviews_index[category][uid] = 1
                        else:
                            category_reviews_index[category][uid]+=1

    sorted_index = {}

    # Sort the dict before writing json to file
    for category, user_counts in category_reviews_index.items():
        sorted_items = sorted(user_counts.items(), key=lambda item: item[1], reverse=True)
        sorted_index[category] = dict(sorted_items)

    if category_reviews_index:
        write_category_review_index(sorted_index)
            
            
def build_indexes():
    complete_business_index = {}
    category_index = {}   # category -> [bid(city,state), ...]
    business_index = {}   # bid -> [category, ...]


    cat_file_id = 0
    biz_file_id = 0

    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        for line in file:
            business = json.loads(line)

            bid = business.get("business_id")
            raw_categories = business.get("categories")

            if not bid or not raw_categories:
                continue

            city = business.get("city", "")
            state = business.get("state", "")

            # clean + filter categories
            categories = []
            for c in raw_categories.split(","):
                c = c.strip()
                if c in FOOD_CATEGORIES:
                    categories.append(c)

            if not categories:
                continue

            # ---------- BUSINESS → CATEGORIES ----------
            business_index[bid] = categories

            complete_business_index[bid] = categories

            # ---------- CATEGORY → BUSINESSES ----------
            for cat in categories:
                if cat not in category_index:
                    category_index[cat] = []

                category_index[cat].append(f"{bid}({city},{state})")

            # ---------- FLUSH WHEN FULL ----------
            if len(category_index) >= BUFFER_SIZE:
                write_category_index(category_index, cat_file_id)
                category_index.clear()
                cat_file_id += 1

            if len(business_index) >= BUFFER_SIZE:
                write_business_index(business_index, biz_file_id)
                business_index.clear()
                biz_file_id += 1

    # ---------- FINAL FLUSH ----------
    if category_index:
        write_category_index(category_index, cat_file_id)

    if business_index:
        write_business_index(business_index, biz_file_id)

    if complete_business_index:
        write_complete_business_index(complete_business_index)


# ---------------- WRITERS ----------------

def write_category_index(index, file_id):
    path = f"{OUTPUT_DIR}/category_index_{file_id:03d}.txt"

    with open(path, "w", encoding="utf-8") as out:
        for category, businesses in index.items():
            line = category + "|" + ";".join(businesses)
            out.write(line + "\n")


def write_business_index(index, file_id):
    path = f"{OUTPUT_DIR}/business_index_{file_id:03d}.txt"

    with open(path, "w", encoding="utf-8") as out:
        for bid, categories in index.items():
            line = bid + "|" + ",".join(categories)
            out.write(line + "\n")

def write_category_review_index(index):
    path = f"{OUTPUT_DIR}/category_review_index.json"

    with open(path, 'w', encoding='utf-8') as out:
        json.dump(index, out, indent=4)    

def write_complete_business_index(index):
    path = f"{OUTPUT_DIR}/complete_business_index.json"

    with open(path, 'w', encoding='utf-8') as out:
        json.dump(index, out, indent=4)


# ---------------- RUN ----------------
if __name__ == "__main__":
    build_indexes()
    build_reviews_indexes()
