# PostgreSQL Database Setup - Quick Start

## ✅ Migration Complete!

Your e-commerce search application has been successfully migrated to use PostgreSQL/Neon database instead of CSV/JSON files.

## 🚀 Quick Setup

### 1. Install Dependencies (if not already done)
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Your Database

#### Option A: Use Neon PostgreSQL (Recommended for Production)

1. Sign up at https://neon.tech (free tier available)
2. Create a new project
3. Copy your connection string
4. Create a `.env` file:

```bash
cp .env.example .env
```

5. Edit `.env` and set your DATABASE_URL:

```env
DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-2.aws.neon.tech/dbname?sslmode=require
```

#### Option B: Use SQLite (For Local Development)

Leave `.env` empty or set:

```env
DATABASE_URL=sqlite:///data/ecommerce.db
```

### 3. Migrate Your Data

Run the migration script to transfer existing CSV/JSON data to the database:

```bash
source venv/bin/activate
python migrate_to_db.py
```

This will automatically:
- ✓ Create all database tables (users, products, search_events)
- ✓ Migrate products from `data/products.csv`
- ✓ Migrate users from `backend/users.json`
- ✓ Migrate search events from `data/search_events.csv`

### 4. Start the Application

```bash
source venv/bin/activate
python -m backend.app
```

The application will automatically:
- Initialize the database connection
- Create tables if they don't exist
- Start the Flask server on port 5000

## 📁 What Changed?

### Before (File-based)
- ❌ `backend/users.json` - User data
- ❌ `data/products.csv` - Product catalog
- ❌ `data/search_events.csv` - Event logs
- ❌ File locks for concurrency
- ❌ CSV injection concerns

### After (Database)
- ✅ PostgreSQL/SQLite with SQLAlchemy ORM
- ✅ Proper database transactions
- ✅ Foreign key relationships
- ✅ Indexes for performance
- ✅ Scalable and production-ready

## 🔧 New Database Modules

- **`backend/models.py`** - SQLAlchemy models (User, Product, SearchEvent)
- **`backend/database.py`** - Database initialization and migration
- **`backend/db_user_manager.py`** - User CRUD operations
- **`backend/db_product_service.py`** - Product operations
- **`backend/db_event_service.py`** - Event logging and queries

## 🔄 Migration Commands

### Fresh Migration (if database is empty)
```bash
python migrate_to_db.py
```

### Force Re-migration (clears and re-imports)
```bash
python migrate_to_db.py --force
```

## 🗄️ Database Schema

### Users Table
```sql
- id (Primary Key)
- user_id (Unique, e.g., "u1")
- username (Unique)
- password_hash (bcrypt)
- group (A/B testing: "A" or "B")
- cluster (recommendations cluster)
- cart (JSON: {product_id: quantity})
- created_at, updated_at
```

### Products Table
```sql
- id (Primary Key)
- product_id (Unique)
- title, description, category
- price, rating, review_count
- popularity (for ranking)
- created_at, updated_at
```

### Search Events Table
```sql
- id (Primary Key)
- user_id (Foreign Key → users.user_id)
- query, product_id
- event_type (click, add_to_cart, search)
- timestamp, group, position
```

## 🧪 Testing the Setup

### Check Database Connection
```bash
source venv/bin/activate
python -c "from backend.database import init_db; init_db(); print('✅ Database connected!')"
```

### Run Migration
```bash
python migrate_to_db.py
```

### Start Application
```bash
python -m backend.app
```

Visit: http://localhost:5000

## 📚 Documentation

See [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) for detailed documentation including:
- Complete migration guide
- Database schema details
- Troubleshooting tips
- Production deployment guide
- API changes and backward compatibility

## ⚠️ Important Notes

1. **Keep Backups**: The CSV/JSON files are preserved as backups
2. **Connection String**: For Neon, ensure `sslmode=require` is in the URL
3. **Environment**: Use `.env` file for configuration (never commit it!)
4. **Virtual Environment**: Always activate with `source venv/bin/activate`

## 🐛 Troubleshooting

### "No module named 'backend.models'"
- Ensure you're in the project root directory
- Activate virtual environment: `source venv/bin/activate`

### "Connection refused" or "Could not connect"
- Check DATABASE_URL in `.env`
- For Neon: Verify connection string is correct
- For SQLite: Ensure `data/` directory exists

### Migration fails
- Run with `--force` flag to clear and retry
- Check CSV/JSON files exist and are readable
- Check database permissions

## 🎉 You're All Set!

Your application now uses a proper database system that:
- ✅ Scales better than files
- ✅ Handles concurrent requests properly
- ✅ Provides data integrity and relationships
- ✅ Works with Neon's serverless PostgreSQL
- ✅ Falls back to SQLite for development

For questions or issues, see [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) or check the logs.
