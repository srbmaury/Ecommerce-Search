import numpy as np
from datetime import datetime

def freshness_score(created_at):
    if created_at.tzinfo is not None and created_at.tzinfo.utcoffset(created_at) is not None:
        now = datetime.now(created_at.tzinfo)
    else:
        now = datetime.now()
    days_old = (now - created_at).days
    return max(0, 1 - days_old / 365)

def build_features(popularity, rating, created_at,
                   category_score, price_affinity):
    return np.array([
        popularity / 10000,
        rating / 5,
        freshness_score(created_at),
        category_score,
        price_affinity
    ])
