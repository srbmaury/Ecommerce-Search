import numpy as np
from datetime import datetime, timezone
from typing import Union


# ---- Feature scaling constants (explicit & documented) ----
# Observed product popularity in this dataset ranges ~500-240,000 (avg ~95k).
# The old ceiling of 10,000 sat below almost every product, so popularity_norm
# clamped to 1.0 for most of the catalog and stopped differentiating results.
# 300,000 leaves headroom above the observed max so log1p scaling stays
# meaningful across the real range.
MAX_POPULARITY = 300_000
MAX_RATING = 5.0
FRESHNESS_DECAY_DAYS = 365

# Log-scale anchor: log1p(MAX_POPULARITY) so all values map to [0, 1]
_LOG_MAX_POPULARITY = np.log1p(MAX_POPULARITY)


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

    popularity uses log1p transform so viral products don't all look identical
    at the MAX_POPULARITY ceiling.
    """
    popularity_norm = min(1.0, np.log1p(max(popularity, 0)) / _LOG_MAX_POPULARITY)
    rating_norm = min(max(rating, 0), MAX_RATING) / MAX_RATING

    return np.array(
        [
            float(popularity_norm),
            rating_norm,
            freshness_score(created_at),
            float(min(1.0, max(0.0, category_score))),  # clamp to [0, 1]
            float(min(1.0, max(0.0, price_affinity))),  # clamp to [0, 1]
        ],
        dtype=np.float32,
    )
