// Global state
let currentUser = null;
let currentQuery = null;

// DOM Elements
const authBox = document.getElementById('auth-box');
const app = document.getElementById('app');
const authForm = document.getElementById('auth-form');
const authTitle = document.getElementById('auth-title');
const toggleText = document.getElementById('toggle-text');
const toggleAuth = document.getElementById('toggle-auth');
const authError = document.getElementById('auth-error');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const results = document.getElementById('results');
const empty = document.getElementById('empty');
const logoutBtn = document.getElementById('logoutBtn');
const analyticsBtn = document.getElementById('analyticsBtn');
const usernameDisplay = document.getElementById('username-display');
const groupDisplay = document.getElementById('group-display');
const recommendationsSection = document.getElementById('recommendations-section');
const recentProducts = document.getElementById('recent-products');
const similarProducts = document.getElementById('similar-products');

// Check for existing session
const savedUser = localStorage.getItem('user');
if (savedUser) {
    currentUser = JSON.parse(savedUser);
    showApp();
}

// Auth toggle (Signup <-> Login)
let isSignup = true;
toggleAuth.addEventListener('click', (e) => {
    e.preventDefault();
    isSignup = !isSignup;
    authTitle.textContent = isSignup ? 'Sign Up' : 'Log In';
    authForm.querySelector('button').textContent = isSignup ? 'Sign Up' : 'Log In';
    toggleText.textContent = isSignup ? 'Already have an account?' : "Don't have an account?";
    toggleAuth.textContent = isSignup ? 'Log In' : 'Sign Up';
    authError.style.display = 'none';
});

// Auth form submission
authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    authError.style.display = 'none';

    try {
        const endpoint = isSignup ? '/signup' : '/login';
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Authentication failed');
        }

        // Success
        currentUser = {
            user_id: data.user_id,
            username: data.username,
            group: data.group || 'A'
        };
        localStorage.setItem('user', JSON.stringify(currentUser));
        showApp();
    } catch (error) {
        authError.textContent = error.message;
        authError.style.display = 'block';
    }
});

// Show main app
function showApp() {
    authBox.style.display = 'none';
    app.style.display = 'block';
    usernameDisplay.textContent = currentUser.username;
    groupDisplay.textContent = currentUser.group;
    loadRecommendations();
}

// Logout
logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('user');
    currentUser = null;
    location.reload();
});

// Analytics button
analyticsBtn.addEventListener('click', () => {
    window.open(`${API_BASE_URL}/analytics`, '_blank');
});

// Search
searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    currentQuery = query;
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/search?q=${encodeURIComponent(query)}&user_id=${currentUser.user_id}`
        );
        const data = await response.json();
        
        console.log('Search response:', data);
        
        if (data.error) {
            throw new Error(data.error);
        }

        // Handle both data.products and direct array response
        const products = Array.isArray(data) ? data : (data.products || []);
        displayResults(products);
    } catch (error) {
        console.error('Search error:', error);
        displayResults([]);
    }
}

function displayResults(products) {
    results.innerHTML = '';
    
    if (products.length === 0) {
        results.style.display = 'none';
        empty.style.display = 'block';
        return;
    }

    results.style.display = 'grid';
    empty.style.display = 'none';

    products.forEach(product => {
        const card = createProductCard(product);
        results.appendChild(card);
    });
}

function createProductCard(product, isRecommendation = false) {
    const card = document.createElement('div');
    card.className = 'card';
    
    const title = document.createElement('h3');
    title.textContent = product.title;
    
    const price = document.createElement('div');
    price.className = 'price';
    price.textContent = `$${product.price.toFixed(2)}`;
    
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = `${product.category} • Rating: ${product.rating}`;
    
    const addBtn = document.createElement('button');
    addBtn.className = 'add-to-cart';
    addBtn.textContent = 'Add to Cart';
    
    addBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        addToCart(product.product_id, addBtn);
    });
    
    // Log click event (only for search results, not recommendations)
    if (!isRecommendation) {
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('add-to-cart')) {
                logEvent('click', product.product_id, currentQuery);
            }
        });
    }
    
    card.appendChild(title);
    card.appendChild(price);
    card.appendChild(meta);
    card.appendChild(addBtn);
    
    return card;
}

async function addToCart(productId, button) {
    try {
        const response = await fetch(`${API_BASE_URL}/cart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                product_id: productId
            })
        });

        if (response.ok) {
            button.textContent = '✓ Added';
            button.disabled = true;
            
            // Also log the event
            await logEvent('add_to_cart', productId, currentQuery);
            
            // Reload recommendations
            setTimeout(() => loadRecommendations(), 500);
        }
    } catch (error) {
        console.error('Add to cart error:', error);
    }
}

async function logEvent(eventType, productId, query) {
    try {
        await fetch(`${API_BASE_URL}/event`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                query: query || '',
                product_id: productId,
                event: eventType
            })
        });
    } catch (error) {
        console.error('Log event error:', error);
    }
}

async function loadRecommendations() {
    if (!currentUser) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/recommendations?user_id=${currentUser.user_id}`
        );
        const data = await response.json();

        if (data.error) {
            return;
        }

        const hasRecent = data.recent && data.recent.length > 0;
        const hasSimilar = data.similar && data.similar.length > 0;

        if (hasRecent || hasSimilar) {
            recommendationsSection.style.display = 'block';
            
            recentProducts.innerHTML = '';
            if (hasRecent) {
                data.recent.forEach(product => {
                    const card = createProductCard(product, true);
                    card.style.minWidth = '200px';
                    card.style.maxWidth = '220px';
                    recentProducts.appendChild(card);
                });
            } else {
                recentProducts.innerHTML = '<p style="color: #999; font-size: 14px;">No recent products</p>';
            }

            similarProducts.innerHTML = '';
            if (hasSimilar) {
                data.similar.forEach(product => {
                    const card = createProductCard(product, true);
                    card.style.minWidth = '200px';
                    card.style.maxWidth = '220px';
                    similarProducts.appendChild(card);
                });
            } else {
                similarProducts.innerHTML = '<p style="color: #999; font-size: 14px;">No recommendations yet</p>';
            }
        }
    } catch (error) {
        console.error('Recommendations error:', error);
    }
}
