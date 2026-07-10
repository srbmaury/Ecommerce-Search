"""Tests for ml/features.py — feature vector construction and normalization."""

import math
from datetime import datetime, timezone, timedelta

import numpy as np
import pytest

from ml.features import (
    build_features,
    freshness_score,
    MAX_POPULARITY,
    MAX_RATING,
    FRESHNESS_DECAY_DAYS,
    _LOG_MAX_POPULARITY,
)


# ---- freshness_score ----

class TestFreshnessScore:
    def test_brand_new_product_is_one(self):
        now = datetime.now(timezone.utc)
        assert freshness_score(now) == pytest.approx(1.0)

    def test_product_older_than_decay_window_is_zero(self):
        old = datetime.now(timezone.utc) - timedelta(days=FRESHNESS_DECAY_DAYS + 1)
        assert freshness_score(old) == 0.0

    def test_product_at_half_decay_is_half(self):
        half = datetime.now(timezone.utc) - timedelta(days=FRESHNESS_DECAY_DAYS / 2)
        score = freshness_score(half)
        assert 0.45 < score < 0.55

    def test_naive_datetime_treated_as_utc(self):
        # Should not raise; naive datetimes get UTC tzinfo attached
        naive = datetime.utcnow() - timedelta(days=10)
        score = freshness_score(naive)
        assert 0.0 <= score <= 1.0

    def test_future_datetime_clamps_to_one(self):
        future = datetime.now(timezone.utc) + timedelta(days=10)
        assert freshness_score(future) == pytest.approx(1.0)


# ---- build_features ----

class TestBuildFeatures:
    def _features(self, popularity=100, rating=4.0, days_old=30,
                  category_score=0.5, price_affinity=0.5):
        created = datetime.now(timezone.utc) - timedelta(days=days_old)
        return build_features(popularity, rating, created, category_score, price_affinity)

    def test_output_shape(self):
        f = self._features()
        assert f.shape == (5,)

    def test_output_dtype_is_float32(self):
        f = self._features()
        assert f.dtype == np.float32

    def test_all_values_in_unit_interval(self):
        f = self._features()
        assert np.all(f >= 0.0) and np.all(f <= 1.0)

    def test_zero_popularity_maps_to_zero(self):
        f = self._features(popularity=0)
        assert f[0] == pytest.approx(0.0)

    def test_max_popularity_maps_to_one(self):
        f = self._features(popularity=MAX_POPULARITY)
        assert f[0] == pytest.approx(1.0, abs=1e-4)

    def test_popularity_uses_log_transform(self):
        # Log transform: doubling popularity should not double the feature
        f_low = self._features(popularity=100)
        f_high = self._features(popularity=10_000)
        ratio = f_high[0] / f_low[0]
        # With log1p: log1p(10000)/log1p(100) ≈ 2.14, not 100
        assert ratio < 10

    def test_negative_popularity_treated_as_zero(self):
        f = self._features(popularity=-50)
        assert f[0] == pytest.approx(0.0)

    def test_max_rating_maps_to_one(self):
        f = self._features(rating=MAX_RATING)
        assert f[1] == pytest.approx(1.0)

    def test_zero_rating_maps_to_zero(self):
        f = self._features(rating=0.0)
        assert f[1] == pytest.approx(0.0)

    def test_rating_above_max_clamps_to_one(self):
        f = self._features(rating=10.0)
        assert f[1] == pytest.approx(1.0)

    def test_category_score_clamped_above_one(self):
        created = datetime.now(timezone.utc)
        f = build_features(100, 3.0, created, category_score=1.5, price_affinity=0.5)
        assert f[3] == pytest.approx(1.0)

    def test_category_score_clamped_below_zero(self):
        created = datetime.now(timezone.utc)
        f = build_features(100, 3.0, created, category_score=-0.3, price_affinity=0.5)
        assert f[3] == pytest.approx(0.0)

    def test_price_affinity_clamped(self):
        created = datetime.now(timezone.utc)
        f = build_features(100, 3.0, created, category_score=0.5, price_affinity=2.0)
        assert f[4] == pytest.approx(1.0)

    def test_freshness_decreases_with_age(self):
        f_new = self._features(days_old=0)
        f_old = self._features(days_old=200)
        assert f_new[2] > f_old[2]
