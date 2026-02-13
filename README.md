# 🚀 Ecommerce Search Engine

## 🌐 Live Demo
🔗 **https://ecommerce-search.onrender.com/**

## 📂 Project Structure
**[Visualize the full project structure here](https://yaml-visualizer.netlify.app/shared/kj3DX-KHCs)**

## 🏗 High-Level System Architecture
The system follows a layered architecture with a React frontend, Flask backend, PostgreSQL database, Redis caching layer and an ML-powered ranking pipeline.
```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TB

    subgraph Frontend["Frontend (React/Vite)"]
        UI["User Interface (React Components)"]
        useAuth["useAuth Hook"]
        useSearch["useSearch Hook"]
        useCart["useCart Hook"]
        useAnalytics["useAnalytics Hook"]
        API_JS["api.js (HTTP Client)"]
    end

    subgraph Backend["Backend (Flask + Python)"]
        Routes["Routes Layer"]
        Controllers["Controllers Layer"]
        Services["Services Layer"]
        Utils["Utils (sanitize, search, intent, db helpers)"]
    end

    subgraph Cache["Cache Layer"]
        Redis["Redis (Upstash) - TTL 5 min"]
    end

    subgraph Database["PostgreSQL Database"]
        Users["users"]
        Products["products"]
        SearchEvents["search_events"]
        CartItems["cart_items"]
    end

    subgraph ML["ML Pipeline"]
        Retrain["Retrain Trigger"]
        Jobs["RQ Background Jobs"]
        Ranker["LightGBM Ranker"]
        Clustering["KMeans Clustering"]
        Profiles["User Profiles"]
        Vectorizer["TF-IDF Vectorizer"]
        Model["ranking_model.pkl"]
    end

    UI --> API_JS
    useAuth --> API_JS
    useSearch --> API_JS
    useCart --> API_JS
    useAnalytics --> API_JS

    API_JS --> Routes
    Routes --> Controllers
    Controllers --> Services
    Controllers --> Utils

    Services --> Database
    Services --> Redis
    Redis --> Services

    Controllers --> Retrain
    Retrain --> Jobs
    Jobs --> Ranker
    Jobs --> Clustering

    Ranker --> Database
    Clustering --> Database
    Profiles --> Database
    Vectorizer --> Database

    Ranker --> Model
```

---

# 📌 Overview

A production-ready, ML-powered ecommerce search engine designed to simulate real-world search, personalization, and ranking systems used in modern ecommerce platforms.

This system integrates:

- 🔐 Secure authentication with email verification  
- 📊 Event-driven analytics & A/B testing  
- 🧠 ML-based personalized ranking  
- 👥 User clustering for segmentation  
- 🔎 PostgreSQL `tsvector` full-text search  
- ⚡ Redis caching for performance  
- 🔄 Background job processing with RQ  

It is built to demonstrate **scalability, personalization, and system design best practices**.

---

# 🛠 Tech Stack

## Backend
- Flask
- Flask-CORS
- SQLAlchemy
- Redis
- RQ (Redis Queue)

## Database
- PostgreSQL (Neon – recommended for production, supports `tsvector`)
- SQLite (local development only)

## Frontend
- React
- Vite
- TailwindCSS-inspired UI

## Machine Learning
- scikit-learn
- pandas
- NumPy
- joblib

## Infrastructure
- Redis (caching + queue system)
- Background workers for async jobs

---

# ⚙️ Setup Guide

---

## 1️⃣ Python Environment (Required)

⚠️ **Python 3.11 is recommended.**  
This project is **not compatible with Python 3.13**.

### Install Python 3.11 (macOS/Homebrew)
```bash
brew install python@3.11
```

### Create Virtual Environment

**macOS / Linux**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

---

## 2️⃣ Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3️⃣ Configure Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

### Required Variables

```
DATABASE_URL=
REDIS_URL=
SECRET_KEY=
```

---

### 📌 Option A — PostgreSQL (Recommended)

1. Create a project at https://neon.tech  
2. Copy your connection string  
3. Update `.env`:

```env
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
REDIS_URL=redis://localhost:6379/0
```

---

### 📌 Option B — SQLite (Local Development Only)

```env
DATABASE_URL=sqlite:///data/ecommerce.db
REDIS_URL=redis://localhost:6379/0
```

---

## 4️⃣ Email Verification Configuration (Optional but Recommended)

To enable account verification & password reset:

```
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=yourpassword
EMAIL_USE_TLS=True
EMAIL_FROM=your@email.com
FRONTEND_URL=http://localhost:5173
```

Use a production SMTP provider:
- Gmail
- SendGrid
- Mailgun

---

## 5️⃣ Start Required Services

Ensure:

- PostgreSQL (if using)
- Redis server

are running.

---

## 6️⃣ Run the Backend
```bash
python -m backend.app
```

Backend runs at:
```
http://127.0.0.1:5000
```

Tables and `tsvector` columns auto-create on first run.

---

## 7️⃣ Populate Database (Optional for Testing)

### Generate Fake Data
```bash
python -m ml.generate_fake_data
```

Or import your own product dataset.

---

## 8️⃣ Start Background Worker (Required for Full Functionality)
```bash
python -m backend.worker
```

Handles:
- Model retraining
- User clustering
- Analytics updates

---

## 9️⃣ Train ML Models (Optional Manual Trigger)

```bash
python -m ml.train_ranker
python -m ml.assign_user_clusters
```

---

## 🔟 Run the Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:
```
http://localhost:5173
```

---

# 🔎 Full-Text Search (PostgreSQL `tsvector`)

- Ranked relevance scoring
- Fast fuzzy matching
- Indexed for scalability
- Handles large catalogs efficiently

---

# ✨ Features

---

## 🔐 Authentication & Security
- Signup/Login
- Email verification
- Password hashing (bcrypt)
- Password reset
- Input validation & sanitization
- SQL injection protection (ORM-based)

---

## 📊 Event Tracking
- Product clicks
- Add-to-cart events
- Search queries
- A/B group tagging
- Timestamp logging

---

## 🧠 Personalized Ranking
- ML ranking model
- User profile vectors
- Segment-based clustering
- Recent activity boost
- Popularity weighting

---

## 👥 User Clustering
- Behavior-based segmentation
- Automated updates
- Improves recommendation diversity

---

## 📈 A/B Testing
- Personalized vs Popularity ranking
- Performance comparison
- CLI-based analytics

Run:
```bash
python -m ml.analytics
```

---

## 📊 Analytics Dashboard

Route:
```
/analytics
```

Displays:
- CTR
- Conversion rate
- A/B performance
- Cluster distribution
- Top queries

---

## 🛒 Shopping Cart
- Add/remove items
- Persistent per-user storage
- Real-time totals
- Cart clearing

---

## ⚡ Performance Optimizations

### Caching
- Redis query cache (5 minutes)
- Product cache
- Session cache

### Database Optimization
- Indexed columns
- Composite indexes
- Connection pooling (5 pool / 10 overflow)
- Batch operations

### Auto-Retrain Triggers

| Component | Trigger |
|-----------|---------|
| Ranking Model | 500 events OR 24h |
| Clusters | 200 events OR 6h |
| User Profiles | Every 5 minutes |

---

# 🗂 File Structure

```
backend/
  models.py
  database.py
  worker.py
  controllers/
  routes/
  services/
  utils/

frontend/
ml/
data/
```

---

# 🚀 Deployment Guide (VPS / PythonAnywhere)

### 1️⃣ Clone Repository
```bash
git clone https://github.com/srbmaury/Ecommerce-Search.git
cd Ecommerce-Search
```

### 2️⃣ Configure `.env`
Set:
- DATABASE_URL
- REDIS_URL
- Email config (optional)

### 3️⃣ Configure WSGI
```python
from backend.app import create_app
application = create_app()
```

### 4️⃣ Start Redis & Worker
```bash
python -m backend.worker
```

### 5️⃣ Build Frontend
```bash
cd frontend
npm run build
```

Serve `frontend/dist` via Flask static config.

---

# 🔐 Security Notes

## Current Protections
- bcrypt password hashing
- ORM-based SQL injection protection
- Foreign key constraints
- Environment-based configuration
- Background job isolation

## Recommended for Production
- Rate limiting (flask-limiter)
- HTTPS only
- Secure cookies
- CSRF protection
- Monitoring & logging
- Credential rotation
- Automated backups

---

# 🧪 Suggested Workflow

1. Sign up and verify email  
2. Search products  
3. Click & add to cart  
4. Observe ranking behavior  
5. Run analytics CLI  
6. Retrain models  
7. Iterate on ranking logic  

---

# 📌 What This Project Demonstrates

- End-to-end full-stack architecture  
- Search engine design  
- Machine learning integration  
- Caching & asynchronous processing  
- A/B experimentation  
- Scalable backend patterns  

This project mirrors how modern ecommerce systems handle:

- Search relevance  
- Personalization  
- Data-driven iteration  
- Performance optimization  
- User segmentation  

---

# 🏁 Final Note

This is not just a demo app — it is a **system design exercise combining ML, backend engineering, search architecture, and scalability patterns**.

Built for learning, experimentation, and real-world production thinking.
