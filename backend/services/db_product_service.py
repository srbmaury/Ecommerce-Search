from backend.services.product.shared import serialize_product, DEFAULT_LIMIT
from backend.services.product.read import get_all_products, get_products_by_ids, get_product_by_id
from backend.services.product.dataframe import get_products_df
from backend.services.product.search import search_products_by_category, get_popular_products
from backend.services.product.update import update_product_popularity
from backend.services.product.create import create_product
