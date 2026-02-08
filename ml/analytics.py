import pandas as pd
from backend.services.db_event_service import get_events_df


def ab_analytics() -> pd.DataFrame:
    """Analyze A/B test results from database and return metrics per group."""
    df = get_events_df()

    required_cols = {"group", "user_id", "event", "query"}
    if not required_cols.issubset(df.columns):
        raise ValueError("Missing required columns for A/B analytics")

    df = df.copy()
    df["is_search"] = df["query"].notna()
    df["is_click"] = df["event"] == "click"
    df["is_cart"] = df["event"] == "add_to_cart"

    summary = (
        df.groupby("group")
        .agg(
            users=("user_id", "nunique"),
            searches=("is_search", "sum"),
            clicks=("is_click", "sum"),
            add_to_cart=("is_cart", "sum"),
        )
        .assign(
            CTR=lambda x: (x["clicks"] / x["searches"]).fillna(0).round(3),
            Conversion=lambda x: (x["add_to_cart"] / x["searches"]).fillna(0).round(3),
        )
        .reset_index()
    )

    return summary


if __name__ == "__main__":
    ab_analytics()
