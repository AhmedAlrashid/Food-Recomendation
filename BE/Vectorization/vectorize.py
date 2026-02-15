import sys
import os
import numpy as np

# Ensure parent BE folder and its data_extraction subfolder are importable
# (tests run from the Vectorization folder so adjust sys.path first)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_extraction")))

from buisiness_cleaning import FOOD_CATEGORIES

cat_to_index = {cat: i for i, cat in enumerate(FOOD_CATEGORIES)}

def l2_normalize(vec):
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def build_click_vector(user_clicks, business_index, cat_to_index):
    vec = np.zeros(len(cat_to_index))

    for bid in user_clicks:
        categories = business_index.get(bid, [])
        for cat in categories:
            if cat in cat_to_index:
                vec[cat_to_index[cat]] += 1

    return l2_normalize(vec)


def build_restaurant_vector(bid, business_index, cat_to_index):
    vec = np.zeros(len(cat_to_index))

    categories = business_index.get(bid, [])
    for cat in categories:
        if cat in cat_to_index:
            vec[cat_to_index[cat]] = 1

    return l2_normalize(vec)
def build_yelp_user_vectors(category_review_index, cat_to_index):
    user_vectors = {}

    for category, users in category_review_index.items():
        if category not in cat_to_index:
            continue

        cat_idx = cat_to_index[category]

        for uid, count in users.items():
            if uid not in user_vectors:
                user_vectors[uid] = np.zeros(len(cat_to_index))

            user_vectors[uid][cat_idx] = count

    # L2 normalize each user
    for uid in user_vectors:
        user_vectors[uid] = l2_normalize(user_vectors[uid])

    return user_vectors

def find_neighbors(my_vec, yelp_user_vectors, k=5):
    sims = []

    for uid, vec in yelp_user_vectors.items():
        score = np.dot(my_vec, vec)
        sims.append((uid, score))

    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:k]

def aggregate_neighbor_vector(neighbors, yelp_user_vectors):
    agg_vec = np.zeros(len(next(iter(yelp_user_vectors.values()))))

    for uid, sim in neighbors:
        agg_vec += sim * yelp_user_vectors[uid]

    return l2_normalize(agg_vec)


def similarity(user_vec, restaurant_vec):
    return np.dot(user_vec, restaurant_vec)


def rank_restaurants(user_vec, business_index, cat_to_index):
    scores = []

    for bid in business_index:
        rest_vec = build_restaurant_vector(bid, business_index, cat_to_index)
        score = np.dot(user_vec, rest_vec)
        scores.append((bid, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores