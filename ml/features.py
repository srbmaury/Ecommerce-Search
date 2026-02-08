import numpy as np
from datetime import datetime, timezone
from typing import Union


# ---- Feature scaling constants (explicit & documented) ----
MAX_POPULARITY = 10_000
MAX_RATING = 5.0
FRESHNESS_DECAY_DAYS = 365


def freshness_score(created_at: datetime) -> float:
    """
    Compute freshness score in [0, 1] based on product age.

    New items → 1.0
    Older than FRESHNESS_DECAY_DAYS → 0.0
    """
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_old = max(0, (now - created_at).days)

    return max(0.0, 1.0 - days_old / FRESHNESS_DECAY_DAYS)


def build_features(
    popularity: Union[int, float],
    rating: Union[int, float],
    created_at: datetime,
    category_score: float,
    price_affinity: float,
) -> np.ndarray:
    """
    Build normalized feature vector for ranking / ML models.
    """
    popularity_norm = min(max(popularity, 0), MAX_POPULARITY) / MAX_POPULARITY
    rating_norm = min(max(rating, 0), MAX_RATING) / MAX_RATING

    return np.array(
        [
            popularity_norm,
            rating_norm,
            freshness_score(created_at),
            float(category_score),
            float(price_affinity),
        ],
        dtype=np.float32,
    )
