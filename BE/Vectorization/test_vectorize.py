import numpy as np
import pytest

from vectorize import (
    cat_to_index,
    l2_normalize,
    build_click_vector,
    build_restaurant_vector,
    build_yelp_user_vectors,
    find_neighbors,
    aggregate_neighbor_vector,
    rank_restaurants
)

# ------------------------
# Fake Category Space
# ------------------------

# Ensure test categories match FOOD_CATEGORIES used in vectorize
# If FOOD_CATEGORIES has more categories, this test still works,
# we just rely on known ones below.

# ------------------------
# Fake Business Index
# ------------------------

business_index = {
    "b1": ["Mexican"],
    "b2": ["Italian"],
    "b3": ["Mexican", "Cafe"],
    "b4": ["Japanese"]
}

# ------------------------
# Fake Yelp Category Review Index
# Category → {uid: count}
# ------------------------

category_review_index = {
    "Mexican": {
        "u1": 5,
        "u2": 3
    },
    "Italian": {
        "u1": 1,
        "u3": 4
    },
    "Cafe": {
        "u2": 2
    }
}

# ------------------------
# TEST 1: Yelp user vectors built correctly
# ------------------------

def test_build_yelp_user_vectors():
    yelp_vectors = build_yelp_user_vectors(category_review_index, cat_to_index)

    assert "u1" in yelp_vectors
    assert "u2" in yelp_vectors

    # All Yelp user vectors should be unit length
    for vec in yelp_vectors.values():
        assert np.isclose(np.linalg.norm(vec), 1.0)


# ------------------------
# TEST 2: Neighbor search finds most similar
# ------------------------

def test_find_neighbors():
    yelp_vectors = build_yelp_user_vectors(category_review_index, cat_to_index)

    # Simulate a user who clicks Mexican heavily
    user_clicks = ["b1", "b3", "b1"]
    my_vec = build_click_vector(user_clicks, business_index, cat_to_index)

    neighbors = find_neighbors(my_vec, yelp_vectors, k=1)

    # u1 and u2 both like Mexican, but u1 likes it more
    assert neighbors[0][0] in ["u1", "u2"]
    assert neighbors[0][1] > 0


# ------------------------
# TEST 3: Aggregation produces normalized vector
# ------------------------

def test_aggregate_neighbor_vector():
    yelp_vectors = build_yelp_user_vectors(category_review_index, cat_to_index)

    user_clicks = ["b1", "b3"]
    my_vec = build_click_vector(user_clicks, business_index, cat_to_index)

    neighbors = find_neighbors(my_vec, yelp_vectors, k=2)

    agg_vec = aggregate_neighbor_vector(neighbors, yelp_vectors)

    assert np.isclose(np.linalg.norm(agg_vec), 1.0)


# ------------------------
# TEST 4: Full Flow Ranking
# ------------------------

def test_full_pipeline_ranking():
    yelp_vectors = build_yelp_user_vectors(category_review_index, cat_to_index)

    user_clicks = ["b1", "b3", "b3"]
    my_vec = build_click_vector(user_clicks, business_index, cat_to_index)

    neighbors = find_neighbors(my_vec, yelp_vectors, k=2)

    final_vec = aggregate_neighbor_vector(neighbors, yelp_vectors)

    ranked = rank_restaurants(final_vec, business_index, cat_to_index)

    # Expect Mexican-related restaurants high
    assert ranked[0][0] in ["b1", "b3"]

    # Japanese-only restaurant should rank low
    assert ranked[-1][0] == "b4"


# ------------------------
# TEST 5: Edge Case – No Clicks
# ------------------------

def test_no_clicks_returns_zero_vector():
    yelp_vectors = build_yelp_user_vectors(category_review_index, cat_to_index)

    user_clicks = []
    my_vec = build_click_vector(user_clicks, business_index, cat_to_index)

    # Should be zero vector
    assert np.all(my_vec == 0)
