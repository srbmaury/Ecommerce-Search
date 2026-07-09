
import API_BASE_URL from './config';

function authHeaders(token) {
    return token ? { Authorization: `Bearer ${token}` } : {};
}

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

// Fired when an authenticated call comes back 401 (missing/expired/invalid
// token) so the app can log the user out and return them to the login
// screen, instead of leaving them on a dashboard that just keeps failing.
// Not used for 403 (valid session, insufficient permission) or for the
// login/signup endpoints themselves, which 401 for "wrong password".
let unauthorizedHandler = null;

export function setUnauthorizedHandler(fn) {
    unauthorizedHandler = fn;
}

async function handleAuthedResponse(res, fallbackMessage) {
    if (res.status === 401 && unauthorizedHandler) {
        unauthorizedHandler();
    }
    return handleResponse(res, fallbackMessage);
}

// API utility for recommendations
export async function fetchRecommendations(token) {
    const res = await fetch(buildUrl('/recommendations'), { headers: authHeaders(token) });
    return handleAuthedResponse(res, 'Failed to fetch recommendations');
}

// Search products
export async function searchProducts(query, token, options = {}) {
    const { cursor = 0, limit, signal } = options;
    const res = await fetch(buildUrl('/search', {
        q: query,
        cursor,
        limit,
    }), { signal, headers: authHeaders(token) });
    return handleResponse(res, 'Failed to search products');
}

// Cart APIs
export async function fetchCart(token) {
    const res = await fetch(buildUrl('/cart'), { headers: authHeaders(token) });
    return handleAuthedResponse(res, 'Failed to fetch cart');
}

export async function updateCart(token, productId, quantity) {
    const res = await fetch(`${API_BASE_URL}/cart/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
        body: JSON.stringify({ product_id: productId, quantity })
    });
    return handleAuthedResponse(res, 'Failed to update cart');
}

export async function clearCart(token) {
    const res = await fetch(`${API_BASE_URL}/cart/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    });
    return handleAuthedResponse(res, 'Failed to clear cart');
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

// Analytics API (admin-only: requires a valid session token)
export async function fetchAnalytics(token) {
    const res = await fetch(`${API_BASE_URL}/analytics`, {
        headers: authHeaders(token),
    });
    return handleAuthedResponse(res, 'Failed to fetch analytics');
}

// Event logging
export async function logEvent(eventType, productId, query, token) {
    const res = await fetch(`${API_BASE_URL}/event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
        body: JSON.stringify({
            query: query || '',
            product_id: productId,
            event: eventType
        })
    });
    return handleResponse(res, 'Failed to log event');
}

// Reviews APIs
export async function fetchProductReviews(productId) {
    const res = await fetch(buildUrl(`/products/${productId}/reviews`));
    return handleResponse(res, 'Failed to fetch reviews');
}

export async function submitProductReview(productId, rating, comment, token) {
    const res = await fetch(`${API_BASE_URL}/products/${productId}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
        body: JSON.stringify({ rating, comment })
    });
    return handleAuthedResponse(res, 'Failed to submit review');
}

export async function deleteProductReview(productId, token) {
    const res = await fetch(`${API_BASE_URL}/products/${productId}/reviews`, {
        method: 'DELETE',
        headers: authHeaders(token),
    });
    return handleAuthedResponse(res, 'Failed to delete review');
}

// Admin Product Management APIs
export async function fetchAdminProducts(token, { search, cursor, limit } = {}) {
    const res = await fetch(buildUrl('/admin/products', { q: search, cursor, limit }), {
        headers: authHeaders(token),
    });
    return handleAuthedResponse(res, 'Failed to fetch products');
}

export async function createAdminProduct(payload, token) {
    const res = await fetch(`${API_BASE_URL}/admin/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
        body: JSON.stringify(payload)
    });
    return handleAuthedResponse(res, 'Failed to create product');
}

export async function updateAdminProduct(productId, payload, token) {
    const res = await fetch(`${API_BASE_URL}/admin/products/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
        body: JSON.stringify(payload)
    });
    return handleAuthedResponse(res, 'Failed to update product');
}

export async function deleteAdminProduct(productId, token) {
    const res = await fetch(`${API_BASE_URL}/admin/products/${productId}`, {
        method: 'DELETE',
        headers: authHeaders(token),
    });
    return handleAuthedResponse(res, 'Failed to delete product');
}

// Admin Cache Management APIs
export async function fetchAdminCacheDashboard(token) {
    const res = await fetch(buildUrl('/admin/cache/dashboard'), {
        headers: authHeaders(token),
    });
    return handleAuthedResponse(res, 'Failed to fetch admin cache dashboard');
}

export async function invalidateCacheEndpoint(endpoint, token) {
    const res = await fetch(`${API_BASE_URL}/admin/cache/${endpoint}`, {
        method: 'POST',
        headers: authHeaders(token),
    });
    return handleAuthedResponse(res, 'Failed to invalidate cache');
}

export async function resetCacheStats(token) {
    const res = await fetch(`${API_BASE_URL}/admin/cache/reset-stats`, {
        method: 'POST',
        headers: authHeaders(token),
    });
    return handleAuthedResponse(res, 'Failed to reset cache stats');
}
