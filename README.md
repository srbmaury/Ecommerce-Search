
# Ecommerce Search Engine

## Project Overview
A personalized ecommerce search engine with user authentication, event logging, ML-based ranking, and user clustering for segment-based recommendations.

---

## Setup Instructions

### 0. (Recommended) Use Python 3.11 and a Virtual Environment
**Important:** This project is not compatible with Python 3.13. Use Python 3.11 (or 3.10/3.12 if all packages support it).

Install Python 3.11 (macOS/Homebrew):
```
brew install python@3.11
```

Create and activate a virtual environment:

For macOS/Linux:
```
python3.11 -m venv venv
source venv/bin/activate
```

For Windows:
```
python -m venv venv
venv\Scripts\activate
```

Once activated, continue with the steps below.

### 1. Install Requirements
```
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. (Optional) Generate Synthetic Data
You can generate synthetic product and user/event data for testing and demos. These steps are optional, but useful for demo/testing:

#### a. Generate Products
Creates a new products CSV with random products.
```
python ml/generate_products.py [NUM_PRODUCTS]
```
Default is 1000 products if not specified.

#### b. Generate Fake Users & Events
Populates the backend via API with test users and search/click/cart events. **Backend server must be running!**
```
python ml/generate_fake_data.py
```
You can adjust user/event counts by editing the script variables.

### 3. Data Preparation
- Ensure `data/products.csv` and `data/search_events.csv` exist and are formatted as in the repo (or generate them above).
- The `search_events.csv` header should be:
  ```
  user_id,query,product_id,event,timestamp,group
  ```

### 4. Train the Ranking Model
```
python ml/train_ranker.py
```
- This will train the ML model and save it for use in ranking.

### 5. Cluster Users (User Segmentation)
```
python ml/assign_user_clusters.py
```
- This will assign each user to a cluster based on their click/category/price preferences.
- Clusters are stored in `backend/users.json` under the `cluster` key for each user.

### 6. Run the Backend Server
```
python -m backend.app
```
- The Flask server will start on http://127.0.0.1:5000

### 7. Run the Frontend
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
- **Signup/Login:** Persistent user authentication with hashed passwords.
- **Event Logging:** All clicks and add-to-cart actions are logged in `search_events.csv`.
- **ML Ranking:** Product ranking is personalized using user profile, cluster preferences, and recent user activity.
- **User Clustering:** Users are grouped by behavior for segment-based recommendations.
- **A/B Testing:** Users are randomly assigned to group A (full personalization) or B (popularity baseline) at signup. All events are logged with group for analytics.
- **Fuzzy Search:** Search results require at least one fuzzy-matched word from the query in the product title or description.
- **Recent Usage Boost:** Products you recently clicked or added to cart are boosted to the top of your search results.
- **Analytics:**
  - Click the **Analytics** button in the UI or visit `/analytics` to view live dashboard metrics (CTR, conversion, clusters, queries, etc.).
  - You can also run `python ml/analytics.py` for a CLI summary of A/B group performance.
- **Auto-Retrain:** The backend automatically retrains the model and re-clusters users every 24 hours while running.
- **Logout:** Top-right button to clear session.

---

## Updating Clusters
- Clusters and model are auto-updated every 24 hours while the backend is running.
- You can also manually re-run `python ml/assign_user_clusters.py` and `python ml/train_ranker.py` if needed.

## Updating the Model
- See above. Model retrains automatically every 24 hours, or you can run `python ml/train_ranker.py` manually.

---

## File Structure
- `backend/` - Flask API, user management, event logging
- `frontend/` - HTML/JS UI
- `ml/` - Model training, feature engineering, user clustering
- `data/` - Product and event data

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

## Credits
Built with Flask, scikit-learn, pandas, and vanilla JS/HTML.
