# -*- coding: utf-8 -*-

import os
import logging
from typing import List, Tuple

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import joblib
from lightgbm import LGBMRanker

from ml.user_profile import build_user_profiles
from ml.features import build_features
from backend.utils.search import user_category_score, user_price_affinity
from backend.services.db_product_service import get_products_df
from backend.services.db_event_service import get_events_df


logger = logging.getLogger(__name__)


MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ranking_model.pkl",
)


REQUIRED_PRODUCT_COLUMNS = [
    "product_id",
    "created_at",
    "popularity",
    "rating",
    "category",
    "price",
]

REQUIRED_EVENT_COLUMNS = [
    "product_id",
    "user_id",
    "event",
]


EVENT_WEIGHTS = {
    "click": 1,
    "add_to_cart": 2,
}


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_dataframe(df: pd.DataFrame, name: str, required_columns: List[str]) -> None:
    if df.empty:
        raise ValueError(f"{name} data is empty")

    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"{name} data is missing required columns: {', '.join(missing)}"
        )


# ---------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------

def load_products() -> pd.DataFrame:
    products = get_products_df()
    validate_dataframe(products, "Products", REQUIRED_PRODUCT_COLUMNS)
    products["created_at"] = pd.to_datetime(products["created_at"])
    return products


def load_events() -> pd.DataFrame:
    events = get_events_df()
    validate_dataframe(events, "Events", REQUIRED_EVENT_COLUMNS)
    return events


def build_training_data(
    products: pd.DataFrame,
    events: pd.DataFrame,
) -> Tuple[List, List, List]:
    """
    Build LightGBM ranking training data:
    X: feature vectors
    y: relevance labels
    group: group sizes (per user)
    """
    user_profiles = build_user_profiles()
    product_index = products.set_index("product_id").to_dict("index")

    X, y, group = [], [], []
    filtered_events = 0

    for user_id, user_events in events.groupby("user_id"):
        user_X, user_y = [], []

        for _, e in user_events.iterrows():
            product = product_index.get(e.product_id)
            if product is None:
                filtered_events += 1
                continue

            profile = user_profiles.get(e.user_id)

            features = build_features(
                popularity=product["popularity"],
                rating=product["rating"],
                created_at=product["created_at"],
                category_score=user_category_score(profile, product["category"]),
                price_affinity=user_price_affinity(profile, product["price"]),
            )

            weight = EVENT_WEIGHTS.get(e.event, 0)

            user_X.append(features)
            user_y.append(weight)

        if user_X:
            X.extend(user_X)
            y.extend(user_y)
            group.append(len(user_X))

    if not X or not y or not group:
        raise RuntimeError(
            f"No training data produced. Filtered events: {filtered_events}/{len(events)}"
        )

    return X, y, group


# ---------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------

def train_and_save_model(X, y, group) -> None:
    logger.info(
        "Training ranking model with %d samples and %d groups",
        len(X),
        len(group),
    )

    model = LGBMRanker(
        n_estimators=100,
        random_state=42,
    )
    model.fit(X, y, group=group)

    joblib.dump(model, MODEL_PATH)
    logger.info("Model saved to %s", MODEL_PATH)


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------

def run_training_pipeline() -> None:
    logger.info("Loading data from database")

    products = load_products()
    events = load_events()

    logger.info(
        "Loaded %d products and %d events",
        len(products),
        len(events),
    )

    X, y, group = build_training_data(products, events)
    train_and_save_model(X, y, group)


# ---------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        run_training_pipeline()
        logger.info("Ranking model training completed successfully")
    except Exception:
        logger.exception("Ranking model training failed")
        raise


if __name__ == "__main__":
    main()
