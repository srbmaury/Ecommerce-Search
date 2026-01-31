from backend.utils.search import search_products, search_by_category
from backend.services.db_user_manager import get_user_by_id
from backend.utils.sanitize import sanitize_user_id
from backend.utils.intent import detect_intent


def search_controller(query, raw_user_id):
    if not query:
        return {"error": "query required"}, 400

    user_id = sanitize_user_id(raw_user_id)
    if raw_user_id and user_id is None:
        return {"error": "invalid user_id"}, 400

    # ---- intent detection ----
    intent = detect_intent(query)
    search_query = intent["clean_query"]

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

    # ---- apply price filters ----
    min_price = intent["suggested_min_price"]
    max_price = intent["suggested_max_price"]
    
    if min_price is not None or max_price is not None:
        filtered_products = []
        for p in products:
            price = p.get("price", 0)
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            filtered_products.append(p)
        products = filtered_products

    # ---- apply sorting ----
    suggested_sort = intent["suggested_sort"]
    if suggested_sort == "price_asc":
        products.sort(key=lambda x: x.get("price", 0))
    elif suggested_sort == "price_desc":
        products.sort(key=lambda x: x.get("price", 0), reverse=True)
    elif suggested_sort == "rating":
        products.sort(key=lambda x: x.get("rating", 0), reverse=True)
    # Note: products are already sorted by score/popularity from search_products

    # Build list of detected intents for frontend
    detected_intents = []
    if intent["suggested_category"]:
        detected_intents.append("category")
    if intent["suggested_sort"]:
        detected_intents.append(intent["suggested_sort"])
    if intent["suggested_min_price"] or intent["suggested_max_price"]:
        detected_intents.append("price_filter")
    
    return {
        "products": products,
        "intent": {
            "detected": detected_intents,
            "suggested_category": intent["suggested_category"],
            "suggested_sort": intent["suggested_sort"],
            "suggested_min_price": intent["suggested_min_price"],
            "suggested_max_price": intent["suggested_max_price"],
        }
    }, 200
