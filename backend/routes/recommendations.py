from flask import Blueprint, request, jsonify
import pandas as pd
from utils.data_paths import get_data_path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from backend.utils.csv_lock import csv_lock
from ml.vectorizer import build_vectorizer

bp = Blueprint("recommendations", __name__)

# Load products and build TF-IDF vectorizer once at module load time
products = pd.read_csv(get_data_path("products.csv"))
texts = (products["title"] + " " + products["description"]).tolist()
vectorizer, tfidf = build_vectorizer(texts)

@bp.route("/recommendations")
def recommendations():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    try:
        with csv_lock:
            events = pd.read_csv(get_data_path("search_events.csv"))
        user_events = events[
            (events.user_id == user_id) &
            (events.event.isin(["click", "add_to_cart"]))
        ].sort_values("timestamp", ascending=False)
        recent_ids = user_events.product_id.astype(int).unique()[:5]
    except Exception:
        # If events file doesn't exist or has no user history, return empty recommendations
        recent_ids = []

    recent = products[products.product_id.isin(recent_ids)].to_dict("records")

    similar = []
    if len(recent_ids):
        idxs = products[products.product_id.isin(recent_ids)].index
        user_vec = tfidf[idxs].mean(axis=0)
        if hasattr(user_vec, "toarray"):
            user_vec = user_vec.toarray()
        else:
            user_vec = np.asarray(user_vec)
        if hasattr(tfidf, "toarray"):
            tfidf_arr = tfidf.toarray()
        else:
            tfidf_arr = np.asarray(tfidf)
        sims = cosine_similarity(user_vec, tfidf_arr).flatten()

        seen = set(recent_ids)
        for i in sims.argsort()[::-1]:
            pid = int(products.iloc[i].product_id)
            if pid not in seen:
                similar.append(products.iloc[i].to_dict())
            if len(similar) == 5:
                break

    return jsonify({"recent": recent, "similar": similar})
