# PostgreSQL Migration Guide

## Overview

This project has been migrated from CSV/JSON file storage to PostgreSQL database using SQLAlchemy ORM. The database can be hosted on Neon (recommended for production) or use SQLite for local development.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Create a `.env` file (or copy from `.env.example`):

```bash
cp .env.example .env
```

#### For Neon PostgreSQL (Production):

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy your connection string
4. Update `.env`:

```env
DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-2.aws.neon.tech/dbname?sslmode=require
```

#### For Local Development (SQLite):

Leave DATABASE_URL empty or set to SQLite:

```env
DATABASE_URL=sqlite:///data/ecommerce.db
```

### 3. Migrate Existing Data

Run the migration script to transfer data from CSV/JSON files to the database:

```bash
python migrate_to_db.py
```

This will:
- Create all necessary database tables
- Migrate products from `data/products.csv`
- Migrate users from `backend/users.json`
- Migrate search events from `data/search_events.csv`

To force re-migration (clears existing data):

```bash
python migrate_to_db.py --force
```

### 4. Run the Application

```bash
python -m backend.app
```

## Database Schema

### Users Table
- `id`: Primary key (auto-increment)
- `user_id`: Unique user identifier (e.g., "u1", "u2")
- `username`: Unique username
- `password_hash`: Bcrypt hashed password
- `group`: A/B testing group ("A" or "B")
- `cluster`: User cluster for recommendations (nullable)
- `cart`: JSON object with cart items `{product_id: quantity}`
- `created_at`, `updated_at`: Timestamps

### Products Table
- `id`: Primary key (auto-increment)
- `product_id`: Unique product identifier
- `title`: Product title
- `description`: Product description
- `category`: Product category
- `price`: Product price
- `rating`: Average rating
- `review_count`: Number of reviews
- `popularity`: Popularity score
- `created_at`, `updated_at`: Timestamps

### SearchEvents Table
- `id`: Primary key (auto-increment)
- `user_id`: Foreign key to users.user_id
- `query`: Search query text
- `product_id`: Product involved in event
- `event_type`: Event type (click, add_to_cart, search)
- `timestamp`: Event timestamp
- `group`: A/B group at time of event
- `position`: Position in search results (optional)

## Key Changes

### What Changed

1. **Data Storage**: CSV/JSON files → PostgreSQL database
2. **Data Access**: File I/O → SQLAlchemy ORM
3. **Concurrency**: File locks → Database transactions
4. **No more**: `csv_lock`, file-based operations, `users.json`, direct CSV access

### Backward Compatibility

The following functions are maintained for backward compatibility:
- `load_users()`: Returns users as list of dicts
- `save_users(users_list)`: Saves users from list format

However, new code should use the database service modules:
- `backend.db_user_manager`: User operations
- `backend.db_product_service`: Product operations
- `backend.db_event_service`: Event logging and retrieval

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (or empty for SQLite)
- `FLASK_DEBUG`: Enable Flask debug mode (0 or 1)
- `RUN_SCHEDULER`: Enable background scheduler (0 or 1)
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)

## Troubleshooting

### Connection Issues

If you see connection errors with Neon:
1. Check your connection string is correct
2. Ensure `sslmode=require` is in the URL
3. Check that your IP is allowed (Neon allows all by default)

### Migration Issues

If migration fails:
1. Check that CSV/JSON files exist and are readable
2. Use `--force` flag to clear and re-migrate
3. Check database permissions

### SQLAlchemy Errors

Common issues:
- **"Table already exists"**: Run migration with `--force` flag
- **"Connection pool exhausted"**: Check for unclosed sessions
- **"No such table"**: Run `create_tables()` or migration script

## Production Deployment

### Neon PostgreSQL Setup

1. Create a Neon project at [neon.tech](https://neon.tech)
2. Note your connection details
3. Set `DATABASE_URL` environment variable
4. Run migration: `python migrate_to_db.py`
5. Start application

### Performance Tips

1. **Connection Pooling**: Configured automatically by SQLAlchemy
2. **Indexes**: Already defined on frequently queried columns
3. **Batch Operations**: Used for bulk inserts during migration
4. **Query Optimization**: Use joins and filters efficiently

## File Organization

```
backend/
├── models.py              # SQLAlchemy models
├── database.py            # Database initialization and migration
├── db_user_manager.py     # User database operations
├── db_product_service.py  # Product database operations
├── db_event_service.py    # Event database operations
├── config.py              # Configuration (includes get_database_url)
└── controllers/           # Updated to use database services
```

## Legacy Files

After successful migration, these files are no longer used:
- `backend/user_manager.py`: Replaced by `db_user_manager.py`
- `backend/utils/csv_lock.py`: No longer needed
- `backend/users.json`: Data now in database
- `data/products.csv`: Data now in database  
- `data/search_events.csv`: Data now in database

**Keep them as backups, but the application uses the database.**

## Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Neon Documentation](https://neon.tech/docs)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
