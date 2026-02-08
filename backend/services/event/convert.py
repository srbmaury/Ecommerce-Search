import pandas as pd

def _events_to_dataframe(events):
    if not events:
        return pd.DataFrame()

    return pd.DataFrame([
        {
            "user_id": e.user_id,
            "query": e.query,
            "product_id": e.product_id,
            "event": e.event_type,  # legacy name
            "event_type": e.event_type,
            "timestamp": e.timestamp,
            "group": e.group,
            "position": e.position,
        }
        for e in events
    ])
