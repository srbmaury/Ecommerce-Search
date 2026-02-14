
import API_BASE_URL from './config';

// API utility for recommendations
export async function fetchRecommendations(userId) {
    const res = await fetch(`${API_BASE_URL}/recommendations?user_id=${userId}`);
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

export async function updateCart(userId, productId, quantity) {
    const res = await fetch(`${API_BASE_URL}/cart/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, product_id: productId, quantity })
    });
    if (!res.ok) throw new Error('Failed to update cart');
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

export async function signup(username, password, email = null) {
    const body = { username, password };
    if (email) body.email = email;
    
    const res = await fetch(`${API_BASE_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
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

// Email verification
export async function verifyEmail(token) {
    const res = await fetch(`${API_BASE_URL}/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || 'Verification failed');
    }
    return data;
}

export async function resendVerification(email) {
    const res = await fetch(`${API_BASE_URL}/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || 'Failed to resend verification');
    }
    return data;
}

// Password reset
export async function forgotPassword(email) {
    const res = await fetch(`${API_BASE_URL}/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || 'Request failed');
    }
    return data;
}

export async function resetPassword(token, password) {
    const res = await fetch(`${API_BASE_URL}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password })
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || 'Reset failed');
    }
    return data;
}

// Analytics API
export async function fetchAnalytics() {
    const res = await fetch(`${API_BASE_URL}/analytics`);
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
