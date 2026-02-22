
import API_BASE_URL from './config';

const ADMIN_API_KEY = import.meta.env.VITE_ADMIN_API_KEY || '';

function buildUrl(path, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            searchParams.set(key, String(value));
        }
    });
    const query = searchParams.toString();
    return `${API_BASE_URL}${path}${query ? `?${query}` : ''}`;
}

async function parseJsonSafe(res) {
    try {
        return await res.json();
    } catch {
        return {};
    }
}

async function handleResponse(res, fallbackMessage) {
    const data = await parseJsonSafe(res);
    if (!res.ok) {
        throw new Error(data.error || data.message || fallbackMessage);
    }
    return data;
}

// API utility for recommendations
export async function fetchRecommendations(userId) {
    const res = await fetch(buildUrl('/recommendations', { user_id: userId }));
    return handleResponse(res, 'Failed to fetch recommendations');
}

// Search products
export async function searchProducts(query, userId, options = {}) {
    const { cursor = 0, limit } = options;
    const res = await fetch(buildUrl('/search', {
        q: query,
        user_id: userId,
        cursor,
        limit,
    }));
    return handleResponse(res, 'Failed to search products');
}

// Cart APIs
export async function fetchCart(userId) {
    const res = await fetch(buildUrl('/cart', { user_id: userId }));
    return handleResponse(res, 'Failed to fetch cart');
}

export async function updateCart(userId, productId, quantity) {
    const res = await fetch(`${API_BASE_URL}/cart/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, product_id: productId, quantity })
    });
    return handleResponse(res, 'Failed to update cart');
}

export async function clearCart(userId) {
    const res = await fetch(`${API_BASE_URL}/cart/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    return handleResponse(res, 'Failed to clear cart');
}

// Auth APIs
export async function login(username, password) {
    const res = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    return handleResponse(res, 'Login failed');
}

export async function signup(username, password, email = null) {
    const body = { username, password };
    if (email) body.email = email;

    const res = await fetch(`${API_BASE_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    return handleResponse(res, 'Signup failed');
}

// Email verification
export async function verifyEmail(token) {
    const res = await fetch(`${API_BASE_URL}/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
    });
    return handleResponse(res, 'Verification failed');
}

export async function resendVerification(email) {
    const res = await fetch(`${API_BASE_URL}/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    return handleResponse(res, 'Failed to resend verification');
}

// Password reset
export async function forgotPassword(email) {
    const res = await fetch(`${API_BASE_URL}/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    return handleResponse(res, 'Request failed');
}

export async function resetPassword(token, password) {
    const res = await fetch(`${API_BASE_URL}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password })
    });
    return handleResponse(res, 'Reset failed');
}

// Analytics API
export async function fetchAnalytics() {
    const res = await fetch(`${API_BASE_URL}/analytics`);
    return handleResponse(res, 'Failed to fetch analytics');
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
    return handleResponse(res, 'Failed to log event');
}

// Admin Cache Management APIs
export async function fetchAdminCacheDashboard(userId) {
    const res = await fetch(buildUrl('/admin/cache/dashboard'), {
        headers: { 'X-User-ID': userId, 'X-Admin-API-Key': ADMIN_API_KEY }
    });
    return handleResponse(res, 'Failed to fetch admin cache dashboard');
}

export async function invalidateCacheEndpoint(endpoint, userId) {
    const res = await fetch(`${API_BASE_URL}/admin/cache/${endpoint}`, {
        method: 'POST',
        headers: { 'X-User-ID': userId, 'X-Admin-API-Key': ADMIN_API_KEY }
    });
    return handleResponse(res, 'Failed to invalidate cache');
}

export async function resetCacheStats(userId) {
    const res = await fetch(`${API_BASE_URL}/admin/cache/reset-stats`, {
        method: 'POST',
        headers: { 'X-User-ID': userId, 'X-Admin-API-Key': ADMIN_API_KEY }
    });
    return handleResponse(res, 'Failed to reset cache stats');
}
