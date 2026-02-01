# Ecommerce Search Engine

## Live Demo
🔗 **https://srbmaury.pythonanywhere.com**

## Project Structure
**[Visualize the whole project structure here](https://yaml-visualizer.netlify.app/shared/kj3DX-KHCs)**

## Project Overview
A personalized ecommerce search engine with user authentication, event logging, ML-based ranking, user clustering, full-text search (PostgreSQL tsvector), Redis caching, and background job processing via message queue (RQ).

## Tech Stack
- **Backend:** Flask, Flask-CORS, SQLAlchemy, Redis, RQ (Redis Queue)
- **Database:** PostgreSQL (Neon, with tsvector full-text search) / SQLite (local)
- **Frontend:** React, Vite, TailwindCSS-inspired styling
- **ML:** scikit-learn, pandas, NumPy, joblib
- **Caching:** Redis (product, session, and query cache)
- **Message Queue:** RQ (Redis Queue) for background jobs (model retrain, clustering, analytics)

---

## Setup Instructions

### 0. (Recommended) Use Python 3.11 and a Virtual Environment
**Important:** This project is not compatible with Python 3.13. Use Python 3.11 (or 3.10/3.12 if all packages support it).

Install Python 3.11 (macOS/Homebrew):
```bash
brew install python@3.11
```

Create and activate a virtual environment:

For macOS/Linux:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Once activated, continue with the steps below.

### 1. Install Requirements
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment & Services

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Set the following variables in `.env`:
- `DATABASE_URL` (PostgreSQL recommended, supports tsvector full-text search)
- `REDIS_URL` (e.g. `redis://localhost:6379/0`)
- Other secrets as needed

#### Option A: Use Neon PostgreSQL (Recommended for Production)
- Sign up at [neon.tech](https://neon.tech)
- Create a project, copy connection string
- Edit `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-2.aws.neon.tech/dbname?sslmode=require
   REDIS_URL=redis://localhost:6379/0
   ```

#### Option B: Use SQLite (Local Only)
- Set:
   ```env
   DATABASE_URL=sqlite:///data/ecommerce.db
   REDIS_URL=redis://localhost:6379/0
   ```

### 3. Initialize Database & Redis
- Tables are created automatically on first backend run
- Redis must be running for caching and background jobs

### 4. Populate the Database
- Use the fake data generator for testing:
  ```bash
  # Terminal 1: Start backend
  python -m backend.app
  # Terminal 2: Generate data
  python -m ml.generate_fake_data
  ```
- Or load your own product data using a custom script (see example in previous README)

### 5. Background Jobs & Model Training
- RQ worker must be running for background jobs:
   ```bash
   python -m backend.worker
   ```
- Train ranking model:
   ```bash
   python -m ml.train_ranker
   ```
- Cluster users:
   ```bash
   python -m ml.assign_user_clusters
   ```

### 6. Run the Backend Server
```bash
python -m backend.app
```
- Flask server starts at http://127.0.0.1:5000
- Redis and RQ worker must be running for full functionality

### 7. Run the Frontend
```bash
cd frontend
npm install
npm run dev
```
- Frontend available at http://localhost:5173

---

---
## Full-Text Search (PostgreSQL tsvector)
- Product search uses PostgreSQL's tsvector for fast, fuzzy, and ranked full-text queries
- For large catalogs, tsvector enables scalable search and filtering

---

## Features

### Core Features
- **Signup/Login:** Persistent user authentication with hashed passwords
- **Event Logging:** All clicks and cart actions logged
- **ML Ranking:** Personalized product ranking (user profile, cluster, recent activity)
- **User Clustering:** Segment-based recommendations
- **A/B Testing:** Random assignment to personalized or popularity-based group
- **Full-Text Search:** Fast, fuzzy, ranked search via PostgreSQL tsvector
- **Redis Caching:** Product, session, and query cache for performance
- **Background Jobs:** Model retrain, clustering, analytics via RQ worker
- **Recent Usage Boost:** Recently interacted products boosted in results
- **Auto-Retrain:** Model and clusters retrain automatically (event count/time)

### Search & Discovery
- **Search Filters:** Category, price range
- **Sort Options:** Price, rating, popularity
- **Pagination:** 12 items per page
- **Product Detail Modal:** Full product info
- **Full-Text Search:** tsvector-powered, fuzzy and ranked

### Shopping Cart
- **Add to Cart:** From search, recommendations, or modal
- **Cart Display:** Item count, total price
- **Remove/Clear Items:** Individual or all
- **Persistent Cart:** Cart data stored per user

### Dynamic Popularity
- **Click Tracking:** +1 popularity per click
- **Add to Cart Tracking:** +3 popularity per add-to-cart

### User Experience
- **Loading States:** Visual feedback
- **Toast Notifications:** Success/error messages
- **Recommendations:** Personalized suggestions
- **Recently Viewed:** Quick access to recent products

### Analytics
- **Live Dashboard:** `/analytics` for CTR, conversion, clusters, queries
- **CLI Analytics:** `python ml/analytics.py` for A/B group performance
- **Background Jobs:** Analytics updates via RQ worker
- Provides a live dashboard with charts for group metrics, CTR, conversion, user clusters, and top queries.
- Uses [recharts](https://recharts.org/) for data visualization.

---


## Updating Clusters & Model
- **Model:** Auto-retrain after 500 events or 24h
- **Clusters:** Auto-update after 200 events or 6h
- **User Profiles:** Refresh every 5 minutes
- **Manual retrain:**
   ```bash
   python -m ml.train_ranker
   python -m ml.assign_user_clusters
   ```

---

## File Structure
- `backend/` - Flask API, database, Redis, RQ worker
   - `models.py` - SQLAlchemy models
   - `database.py` - DB init, tsvector setup
   - `worker.py` - RQ worker for background jobs
   - `controllers/` - Business logic (auth, cart, events, recommendations, search, analytics)
   - `routes/` - API routes
   - `services/` - Utilities (retrain triggers, user profiles, analytics, Redis cache)
   - `utils/` - Config, database, search, sanitize
- `frontend/` - React/Vite UI
- `ml/` - Model training, clustering, analytics
- `data/` - SQLite DB (local)

---

## Troubleshooting
- Ensure all dependencies (Python, Node, Redis, PostgreSQL) are installed and running
- If you add new users/events, wait for auto-retrain or run scripts manually
- Check terminal output for errors
- Redis must be running for caching and background jobs
---

## Next Steps
1. Use the app: sign up, log in, search, click, add to cart
2. Wait for backend auto-retrain or run model/cluster scripts manually
3. Run analytics:
    ```bash
    python -m ml.analytics
    ```
    to compare A/B group performance
4. Analyze results and iterate on ranking, clustering, or UI
5. (Optional) Deploy backend and frontend for real users

---

## Deployment (PythonAnywhere or VPS)
1. **Clone the repository:**
   ```bash
   git clone https://github.com/srbmaury/Ecommerce-Search.git
   cd Ecommerce-Search
   ```
2. **Set up environment:**
   - Create `.env` with `DATABASE_URL` and `REDIS_URL`
   - Tables and tsvector columns are created automatically
3. **Set up WSGI configuration:**
   - Source: `/home/YOUR_USERNAME/Ecommerce-Search`
   - WSGI file: `from backend.app import create_app`
   - Application: `application = create_app()`
4. **Start Redis and RQ worker:**
   - Redis must be running
   - Start worker: `python -m backend.worker`
5. **Frontend serving:**
   - Static files from `frontend/dist/`
   - Flask serves via `static_folder` config
6. **Reload web app** after changes

---

## Performance & Optimization

### Caching & Performance
- **Redis Cache:** Products, sessions, queries cached for 5 minutes
- **Connection Pooling:** PostgreSQL pool (size: 5, max overflow: 10)
- **Efficient Queries:** Indexed columns, batch ops
- **Background Jobs:** RQ worker for retrain, clustering, analytics

### Database Indexes
- User: `user_id`, `username`, `cluster`
- Product: `id`, `category`, `popularity`, composite `(category, price)`, tsvector for search
- CartItem: `id`, `user_id`, `product_id`
- SearchEvent: `user_id`, `event_type`, `timestamp`, `group`, composite indexes

### Scalability
- Event table grows large: archive old events (>6 months)
- Full-text search (tsvector) for large catalogs

---

## Security Notes

### Current Implementation
- ✅ Password hashing (bcrypt)
- ✅ Input validation & sanitization
- ✅ SQL injection protection (SQLAlchemy)
- ✅ Foreign key constraints (CASCADE)
- ✅ Environment-based config (`.env`)
- ✅ Redis for session and cache
- ✅ RQ for background jobs

### Production Recommendations
- 🔒 Rate limiting for auth endpoints (`flask-limiter` recommended)
- 🔒 Use HTTPS
- 🔒 Secure session cookies (`SESSION_COOKIE_SECURE=True`)
- 🔒 CSRF protection for state-changing ops
- 🔒 Request logging & monitoring
- 🔒 Regular DB backups & credential rotation

---

