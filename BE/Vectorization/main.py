import json
import argparse
from typing import Dict, List, Tuple

from vectorize import build_yelp_user_vectors, rank_restaurants


def top10_for_all_users(yelp_user_vectors: Dict[str, List[float]],
                        business_index: Dict[str, List[str]],
                        cat_to_index: dict,
                        top_n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
    """Return top-N restaurant rankings for every user vector provided.

    Args:
        yelp_user_vectors: mapping uid -> normalized numpy vector
        business_index: mapping bid -> list of categories
        cat_to_index: mapping category -> index (used by vectorize)
        top_n: number of restaurants to return per user

    Returns:
        dict of uid -> list of (bid, score) tuples (score is Python float)
    """
    results = {}

    for uid, user_vec in yelp_user_vectors.items():
        ranked = rank_restaurants(user_vec, business_index, cat_to_index)
        # convert numpy floats to native floats for JSON safety
        results[uid] = [(bid, float(score)) for bid, score in ranked[:top_n]]

    return results


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)


def cli():
    p = argparse.ArgumentParser(description="Produce top-N restaurant rankings for many users")
    p.add_argument("--business-index", help="JSON file with business_index (bid -> [categories])")
    p.add_argument("--category-review-index", help="JSON file with category_review_index (category -> {uid: count})")
    p.add_argument("--yelp-vectors", help="Optional: JSON file with precomputed yelp user vectors (uid -> list<float>)")
    p.add_argument("--cat-to-index", help="JSON file with category->index mapping (optional)")
    p.add_argument("--top-n", type=int, default=10, help="Top-N restaurants to return per user")
    p.add_argument("--out", default="rankings.json", help="Output JSON file for rankings")

    args = p.parse_args()

    if args.yelp_vectors:
        yelp_vectors = load_json(args.yelp_vectors)
    else:
        if not args.category_review_index:
            raise SystemExit("Provide either --yelp-vectors or --category-review-index")
        category_review_index = load_json(args.category_review_index)
        # if cat_to_index is provided, load it; otherwise rely on vectorize to construct one
        if args.cat_to_index:
            cat_to_index = load_json(args.cat_to_index)
        else:
            # build_yelp_user_vectors requires a cat_to_index mapping; we derive it from the categories
            # by scanning business index if provided.
            if not args.business_index:
                raise SystemExit("--business-index is required when --cat-to-index is not provided")
            business_index = load_json(args.business_index)
            # derive a simple cat->index from all categories found in business_index
            cats = sorted({c for cats in business_index.values() for c in cats})
            cat_to_index = {c: i for i, c in enumerate(cats)}

        yelp_vectors = build_yelp_user_vectors(category_review_index, cat_to_index)

    if args.business_index:
        business_index = load_json(args.business_index)
    else:
        raise SystemExit("--business-index is required")

    results = top10_for_all_users(yelp_vectors, business_index, cat_to_index, top_n=args.top_n)

    save_json(args.out, results)
    print(f"Wrote rankings for {len(results)} users to {args.out}")


if __name__ == "__main__":
    cli()
