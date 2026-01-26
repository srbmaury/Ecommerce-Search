from backend.search import search_products, search_by_category
from backend.db_user_manager import get_user_by_id
from backend.utils.sanitize import sanitize_user_id
from backend.intent import detect_intent


def search_controller(query, raw_user_id):
    if not query:
        return {"error": "query required"}, 400

    user_id = sanitize_user_id(raw_user_id)
    if raw_user_id and user_id is None:
        return {"error": "invalid user_id"}, 400

    # ---- intent detection ----
    intent = detect_intent(query)

    is_brand_search = "brand" in intent["intents"]
    search_query = query if is_brand_search else intent["clean_query"]

    cluster = None
    group = "A"

    # ---- user context ----
    try:
        if user_id:
            user = get_user_by_id(user_id)
            if user:
                cluster = user.cluster
                group = user.group or "A"
    except Exception:
        pass

    # ---- primary search ----
    products = search_products(
        search_query,
        user_id,
        cluster=cluster,
        ab_group=group
    )

    # ---- category fallback ----
    if len(products) < 5 and intent["suggested_category"]:
        category_products = search_by_category(
            intent["suggested_category"],
            user_id,
            cluster=cluster,
            ab_group=group
        )

        existing_ids = {p["product_id"] for p in products}
        for cp in category_products:
            if cp["product_id"] not in existing_ids:
                products.append(cp)

    return {
        "products": products,
        "intent": {
            "detected": intent["intents"],
            "suggested_category": intent["suggested_category"],
            "suggested_sort": intent["suggested_sort"],
            "suggested_min_price": intent["suggested_min_price"],
            "suggested_max_price": intent["suggested_max_price"],
        }
    }, 200
