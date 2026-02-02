
import API_BASE_URL from './config';

// API utility for recommendations
export async function fetchRecommendations(userId) {
    const res = await fetch(`${API_BASE_URL}/api/recommendations?user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    return res.json();
}

// Search products
export async function searchProducts(query, userId) {
    const res = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to search products');
    return res.json();
}

// Cart APIs
export async function fetchCart(userId) {
    const res = await fetch(`${API_BASE_URL}/cart?user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to fetch cart');
    return res.json();
}

export async function addToCart(userId, productId, query = '') {
    const res = await fetch(`${API_BASE_URL}/cart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, product_id: productId, query })
    });
    if (!res.ok) throw new Error('Failed to add to cart');
    return res.json();
}

export async function removeFromCart(userId, productId) {
    const res = await fetch(`${API_BASE_URL}/cart/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, product_id: productId })
    });
    if (!res.ok) throw new Error('Failed to remove from cart');
    return res.json();
}

export async function clearCart(userId) {
    const res = await fetch(`${API_BASE_URL}/cart/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    if (!res.ok) throw new Error('Failed to clear cart');
    return res.json();
}

// Auth APIs
export async function login(username, password) {
    const res = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    let data;
    try {
        data = await res.json();
    } catch (e) {
        data = {};
    }
    if (!res.ok) {
        throw new Error(data.error || 'Login failed');
    }
    return data;
}

export async function signup(username, password) {
    const res = await fetch(`${API_BASE_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    let data;
    try {
        data = await res.json();
    } catch (e) {
        data = {};
    }
    if (!res.ok) {
        throw new Error(data.error || 'Signup failed');
    }
    return data;
}

// Analytics API
export async function fetchAnalytics() {
    const res = await fetch(`${API_BASE_URL}/api/analytics`);
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
}

// Event logging
export async function logEvent(eventType, productId, query, userId) {
    const res = await fetch(`${API_BASE_URL}/event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            query: query || '',
            product_id: productId,
            event: eventType
        })
    });
    if (!res.ok) throw new Error('Failed to log event');
    return res.json();
}
