import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.db_event_service import get_events_df

def ab_analytics():
    """Analyze A/B test results from database."""
    df = get_events_df()
    if 'group' not in df.columns:
        print("No group column in events. Cannot compute A/B analytics.")
        return
    summary = {}
    for group in df['group'].unique():
        gdf = df[df['group'] == group]
        users = gdf['user_id'].nunique()
        clicks = (gdf['event'] == 'click').sum()
        carts = (gdf['event'] == 'add_to_cart').sum()
        searches = gdf['query'].notnull().sum()
        ctr = clicks / searches if searches else 0
        conversion = carts / searches if searches else 0
        summary[group] = {
            'users': users,
            'searches': searches,
            'clicks': clicks,
            'add_to_cart': carts,
            'CTR': round(ctr, 3),
            'Conversion': round(conversion, 3)
        }
    print("A/B Group Analytics:")
    for group, stats in summary.items():
        print(f"Group {group}: {stats}")

if __name__ == "__main__":
    ab_analytics()
