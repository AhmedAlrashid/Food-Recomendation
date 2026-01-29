import json
from buisiness_cleaning import FOOD_CATEGORIES

# ---------------- CONFIG ----------------
INPUT_PATH = r"BE\data_extraction\yelp_business_food_only.jsonl"
OUTPUT_DIR = r"BE\data_extraction"
BUFFER_SIZE = 15_000
# ----------------------------------------


def build_indexes():
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


# ---------------- WRITERS ----------------

def write_category_index(index, file_id):
    path = f"{OUTPUT_DIR}/index/category_index_{file_id:03d}.txt"

    with open(path, "w", encoding="utf-8") as out:
        for category, businesses in index.items():
            line = category + "|" + ";".join(businesses)
            out.write(line + "\n")


def write_business_index(index, file_id):
    path = f"{OUTPUT_DIR}/index/business_index_{file_id:03d}.txt"

    with open(path, "w", encoding="utf-8") as out:
        for bid, categories in index.items():
            line = bid + "|" + ",".join(categories)
            out.write(line + "\n")


# ---------------- RUN ----------------
if __name__ == "__main__":
    build_indexes()
