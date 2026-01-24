import pandas as pd
from utils.data_paths import get_data_path


def get_products_df():
    """Load products DataFrame, returns empty DataFrame on error."""
    try:
        return pd.read_csv(get_data_path("products.csv"))
    except Exception:
        return pd.DataFrame()


def update_product_popularity(product_id, points):
    """Update product popularity score by given points."""
    try:
        products_path = get_data_path("products.csv")
        df = pd.read_csv(products_path)
        mask = df["product_id"] == int(product_id)
        if mask.any():
            df.loc[mask, "popularity"] += points
            df.to_csv(products_path, index=False)
    except Exception:
        pass
