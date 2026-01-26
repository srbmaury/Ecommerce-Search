
# Ecommerce Search Engine

## Live Demo
🔗 **https://srbmaury.pythonanywhere.com**

## Project Overview
A personalized ecommerce search engine with user authentication, event logging, ML-based ranking, and user clustering for segment-based recommendations.

## Tech Stack
- **Backend:** Flask, Flask-CORS, SQLAlchemy
- **Database:** PostgreSQL (Neon) / SQLite
- **Frontend:** React, Vite, TailwindCSS-inspired styling
- **ML:** scikit-learn, pandas, NumPy, joblib

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

### 2. Configure Database

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

#### Option A: Use Neon PostgreSQL (Recommended for Production)
1. Sign up at [neon.tech](https://neon.tech) (free tier available)
2. Create a new project
3. Copy your connection string
4. Edit `.env` and set:
```env
DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-2.aws.neon.tech/dbname?sslmode=require
```

#### Option B: Use SQLite (For Local Development)
Leave `DATABASE_URL` empty or set to:
```env
DATABASE_URL=sqlite:///data/ecommerce.db
```

### 3. Initialize Database Tables

The database tables are created automatically when you start the backend server for the first time.

### 4. (Optional) Generate Synthetic Data

Generate synthetic user and event data for testing:

**Important:** Backend server must be running first!

```bash
# Terminal 1: Start backend
source venv/bin/activate
python -m backend.app

# Terminal 2: Generate data
source venv/bin/activate
python ml/generate_fake_data.py
```

This creates test users (testuser1-30) with search/click/cart events stored directly in the database.

### 5. Train the Ranking Model
```bash
python ml/train_ranker.py
```
- Trains the ML model using data from the database
- Saves the model for use in ranking

### 6. Cluster Users (User Segmentation)
```bash
python ml/assign_user_clusters.py
```
- Assigns each user to a cluster based on their behavior
- Clusters are stored in the database

### 7. Run the Backend Server
```bash
python -m backend.app
```
- The Flask server will start on http://127.0.0.1:5000
- Database connection is initialized automatically

### 8. Run the Frontend
**Important:** The frontend must be served via HTTP (not opened directly as a file://) to work with CORS and API calls.

#### Option A: Using VS Code Live Server (Recommended)
1. Install the "Live Server" extension in VS Code (by Ritwick Dey)
2. Right-click on `frontend/index.html` and select "Open with Live Server"
3. The frontend will open at `http://localhost:5500` or `http://127.0.0.1:5500`

#### Option B: Using Python's Built-in HTTP Server
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```
2. Start the HTTP server on port 5500:
   ```
   python -m http.server 5500
   ```
3. Open your browser and navigate to `http://localhost:5500`

#### Option C: Custom Port (Advanced)
If you need to use a different port, you'll need to update the CORS configuration:
1. Set the `ALLOWED_ORIGINS` environment variable:
   ```
   export ALLOWED_ORIGINS="http://localhost:YOUR_PORT,http://127.0.0.1:YOUR_PORT"
   ```
2. Restart the backend server

Once the frontend is running:
- Use the UI to sign up, log in, search, and interact with products.
- **Analytics Dashboard:**
  - Click the **Analytics** button (top-left) in the UI to open the live analytics dashboard, which is served by the backend at `/analytics`.
  - Alternatively, visit [http://localhost:5000/analytics](http://localhost:5000/analytics) in your browser to view A/B test metrics, CTR, conversion rates, cluster sizes, and top queries.

---

## Features

### Core Features
- **Signup/Login:** Persistent user authentication with hashed passwords stored in database.
- **Event Logging:** All clicks and add-to-cart actions are logged in the database.
- **ML Ranking:** Product ranking is personalized using user profile, cluster preferences, and recent user activity.
- **User Clustering:** Users are grouped by behavior for segment-based recommendations.
- **A/B Testing:** Users are randomly assigned to group A (full personalization) or B (popularity baseline) at signup.
- **Fuzzy Search:** Search results require at least one fuzzy-matched word from the query in the product title or description.
- **Recent Usage Boost:** Products you recently clicked or added to cart are boosted to the top of your search results.
- **Auto-Retrain:** The backend automatically retrains the model (every 500 events or 24h) and re-clusters users (every 200 events or 6h) while running.

### Search & Discovery
- **Search Filters:** Filter results by category and price range (min/max).
- **Sort Options:** Sort by price (low/high), rating, or popularity.
- **Pagination:** Browse large result sets with page navigation (12 items per page).
- **Product Detail Modal:** Click any product to view full details (title, price, category, rating, popularity, description).

### Shopping Cart
- **Add to Cart:** Add products from search results, recommendations, or product modal.
- **Cart Display:** View cart with item count and total price.
- **Remove Items:** Remove individual items from cart.
- **Clear Cart:** Clear all items at once.
- **Persistent Cart:** Cart data persists across sessions (stored in database).

### Dynamic Popularity
- **Click Tracking:** Product popularity increases by +1 on each click.
- **Add to Cart Tracking:** Product popularity increases by +3 on each add-to-cart action.

### User Experience
- **Loading States:** Visual feedback during search, auth, and data fetching.
- **Toast Notifications:** Success/error messages for user actions.
- **Recommendations:** Personalized product recommendations based on user behavior.
- **Recently Viewed:** Quick access to recently interacted products.

### Analytics
- Click the **Analytics** button in the UI or visit `/analytics` to view live dashboard metrics (CTR, conversion, clusters, queries, etc.).
- Run `python ml/analytics.py` for a CLI summary of A/B group performance.

---

## Updating Clusters & Model
- **Model:** Auto-retrains after 500 events or 24 hours (whichever comes first)
- **Clusters:** Auto-update after 200 events or 6 hours (whichever comes first)
- User profiles refresh every 5 minutes for near real-time personalization
- Manual retrain: `python ml/train_ranker.py` and `python ml/assign_user_clusters.py`

---

## File Structure
- `backend/` - Flask API with database integration
  - `models.py` - SQLAlchemy database models
  - `database.py` - Database initialization
  - `db_user_manager.py` - User database operations
  - `db_product_service.py` - Product database operations
  - `db_event_service.py` - Event database operations
  - `controllers/` - Business logic (auth, cart, events, recommendations, search, analytics)
  - `routes/` - API route definitions
  - `services/` - Shared utilities (retrain triggers, user profiles, analytics HTML)
- `frontend/` - React/Vite UI
- `ml/` - Model training, feature engineering, user clustering
- `data/` - SQLite database file (when using local development)

---

## Troubleshooting
- Ensure all dependencies are installed.
- If you add new users or events, you can wait for the next auto-retrain or run clustering/model scripts manually.
- If you see backend errors (e.g., IndentationError, SyntaxError), check for correct indentation and try re-running after fixing code.
- For any issues, check the terminal output for errors.
---

## Next Steps

1. Use the app as a user: sign up, log in, search, click, and add to cart.
2. Wait for the backend to auto-retrain (or run model/cluster scripts manually) as you generate more data.
3. Run analytics:
  ```
  python ml/analytics.py
  ```
  to compare A/B group performance (CTR, conversion, etc.).
4. Analyze results and iterate on ranking, clustering, or UI as needed.
5. (Optional) Deploy the backend and frontend for real users and collect more data.

---

## Deployment (PythonAnywhere)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/srbmaury/Ecommerce-Search.git
   cd Ecommerce-Search
   ```

2. **Set up database:**
   - Create a `.env` file with your DATABASE_URL
   - Tables are created automatically on first run

3. **Set up WSGI configuration:**
   - Source code: `/home/YOUR_USERNAME/Ecommerce-Search`
   - WSGI file should import: `from backend.app import create_app`
   - Application callable: `application = create_app()`

4. **Frontend serving:**
   - Static files are served from `frontend/dist/`
   - Flask handles this automatically via `static_folder` configuration

5. **Reload the web app** after any changes.

---

## Credits
Built with Flask, React, Vite, scikit-learn, and pandas.
