"""
Export products from database to CSV file.
This is useful for backing up products or moving them between databases.
"""
import sys
import os
import csv
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from backend.database import init_db, get_db_session
from backend.models import Product

def export_products_to_csv(output_file="data/products_backup.csv"):
    """Export all products from database to CSV."""
    print("🔧 Initializing database connection...")
    init_db()
    
    session = get_db_session()
    try:
        products = session.query(Product).all()
        
        if not products:
            print("❌ No products found in database!")
            return
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'product_id', 'title', 'description', 'category', 
                'price', 'rating', 'review_count', 'popularity', 'created_at'
            ])
            
            # Write products
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
                    product.created_at
                ])
        
        print(f"✅ Exported {len(products)} products to {output_file}")
        
    except Exception as e:
        print(f"❌ Error exporting products: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Export products from database to CSV')
    parser.add_argument('--output', '-o', default='data/products_backup.csv',
                       help='Output CSV file path (default: data/products_backup.csv)')
    args = parser.parse_args()
    
    export_products_to_csv(args.output)
