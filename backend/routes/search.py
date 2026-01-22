from flask import Blueprint, request, jsonify
from backend.search import search_products
from backend.user_manager import load_users
from backend.utils.sanitize import sanitize_user_id

bp = Blueprint("search", __name__)

@bp.route("/search")
def search():
    query = request.args.get("q")
    raw_user_id = request.args.get("user_id")

    if not query:
        return jsonify({"error": "query required"}), 400

    user_id = sanitize_user_id(raw_user_id)
    if raw_user_id and user_id is None:
        return jsonify({"error": "invalid user_id"}), 400

    cluster = None
    group = "A"

    try:
        if user_id:
            users = load_users()
            user = next((u for u in users if u["user_id"] == user_id), None)
            if user:
                cluster = user.get("cluster")
                group = user.get("group", "A")
    except Exception:
        # If user lookup fails, proceed with defaults (cluster=None, group="A")
        pass

    return jsonify(search_products(query, user_id, cluster=cluster, ab_group=group))
