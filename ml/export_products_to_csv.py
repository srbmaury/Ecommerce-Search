"""
Export products from database to a CSV file.

Useful for backups or migrating product data between databases.
"""

import sys
import os
import csv
import logging
from typing import List
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

load_dotenv()

from backend.database import init_db, get_db_session
from backend.models import Product


logger = logging.getLogger(__name__)


CSV_HEADERS = [
    "product_id",
    "title",
    "description",
    "category",
    "price",
    "rating",
    "review_count",
    "popularity",
    "created_at",
]


def fetch_products(session) -> List[Product]:
    """Fetch all products from the database."""
    return session.query(Product).all()


def write_products_to_csv(products: List[Product], output_file: str) -> None:
    """Write products to a CSV file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)

        for product in products:
            writer.writerow([
                product.id,
                product.title,
                product.description,
                product.category,
                product.price,
                product.rating,
                product.review_count,
                product.popularity,
                product.created_at,
            ])


def export_products_to_csv(output_file: str) -> int:
    """
    Export all products from the database to CSV.

    Returns:
        Number of products exported
    """
    logger.info("Initializing database connection")
    init_db()

    session = get_db_session()
    try:
        products = fetch_products(session)

        if not products:
            logger.warning("No products found in database")
            return 0

        logger.info("Fetched %d products", len(products))
        logger.info("Writing products to CSV: %s", output_file)

        write_products_to_csv(products, output_file)

        logger.info("Successfully exported %d products", len(products))
        return len(products)

    except Exception:
        logger.exception("Error exporting products to CSV")
        raise

    finally:
        session.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Export products from database to CSV"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/products_backup.csv",
        help="Output CSV file path",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    export_products_to_csv(args.output)


if __name__ == "__main__":
    main()
