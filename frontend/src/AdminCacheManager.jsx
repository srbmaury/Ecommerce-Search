import { useState, useEffect } from 'react';
import { fetchAdminCacheDashboard, invalidateCacheEndpoint, resetCacheStats } from './api';
import Toast from './Toast';

/**
 * Admin Cache Management Modal
 * 
 * Only visible to users with email in ADMIN_EMAILS env var
 * Provides a professional interface for cache monitoring and management
 */
function AdminCacheManager({ user }) {
  const [isAdmin, setIsAdmin] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [cacheStats, setCacheStats] = useState(null);
  const [adminInfo, setAdminInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Check if user is admin and load initial data
  useEffect(() => {
    if (!user?.user_id) {
      setIsAdmin(false);
      setCacheStats(null);
      setAdminInfo(null);
      return;
    }

    const checkAdminStatus = async () => {
      try {
        const data = await fetchAdminCacheDashboard(user.user_id);
        setIsAdmin(true);
        setAdminInfo(data.admin);
        setCacheStats(data.cache);
        setLastUpdated(new Date());
      } catch (error) {
        // Suppress 403 errors - non-admins are expected to fail silently
        if (!error.message.includes('Admin access required')) {
          console.error('Admin check failed:', error);
        }
        setIsAdmin(false);
      }
    };

    checkAdminStatus();
  }, [user]);

  if (!isAdmin) {
    return null;
  }

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const refreshStats = async () => {
    try {
      const data = await fetchAdminCacheDashboard(user.user_id);
      setCacheStats(data.cache);
      setLastUpdated(new Date());
      showToast('✓ Stats refreshed', 'success');
    } catch (error) {
      showToast(`✗ ${error.message}`, 'error');
    }
  };

  const handleInvalidate = async (endpoint, label) => {
    setLoading(true);
    try {
      const data = await invalidateCacheEndpoint(endpoint, user.user_id);
      showToast(`✓ ${label}: ${data.status}`, 'success');
      await refreshStats();
    } catch (error) {
      showToast(`✗ ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetStats = async () => {
    if (!confirm('Reset cache statistics? This cannot be undone.')) return;

    setLoading(true);
    try {
      await resetCacheStats(user.user_id);
      showToast('✓ Cache statistics reset', 'success');
      setCacheStats({ hits: 0, misses: 0, invalidations: 0, hit_rate: 0 });
      setLastUpdated(new Date());
    } catch (error) {
      showToast(`✗ ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (!cacheStats) {
    return null;
  }

  const hitRate = (cacheStats.hit_rate * 100).toFixed(1);
  const isHealthy = cacheStats.hit_rate > 0.8;

  return (
    <>
      {/* Admin Button */}
      <button
        onClick={() => setShowModal(true)}
        className="admin-toggle-btn"
        title="Cache Admin Panel"
      >
        ⚙️
      </button>

      {/* Modal Overlay */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="admin-cache-modal" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="admin-modal-header">
              <h2>Cache Management Dashboard</h2>
              <button
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>

            {/* Admin Info */}
            {adminInfo && (
              <div className="admin-info-section">
                <p className="admin-label">Logged in as:</p>
                <div className="admin-user-info">
                  <span className="admin-username">{adminInfo.username}</span>
                  <span className="admin-email">{adminInfo.email}</span>
                </div>
              </div>
            )}

            {/* Cache Stats Section */}
            <div className="cache-stats-section">
              <div className="stats-header">
                <h3>Cache Performance</h3>
                <div className={`health-indicator ${isHealthy ? 'healthy' : 'warning'}`}>
                  <span className="health-dot"></span>
                  {isHealthy ? 'Healthy' : 'Monitor'}
                </div>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value hits">{cacheStats.hits || 0}</div>
                  <div className="stat-label">Cache Hits</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value misses">{cacheStats.misses || 0}</div>
                  <div className="stat-label">Cache Misses</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value hitrate">{hitRate}%</div>
                  <div className="stat-label">Hit Rate</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value invalidations">{cacheStats.invalidations || 0}</div>
                  <div className="stat-label">Invalidations</div>
                </div>
              </div>

              {lastUpdated && (
                <div className="last-updated">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </div>
              )}
            </div>

            {/* Actions Section */}
            <div className="cache-actions-section">
              <h3>Cache Control</h3>
              <div className="actions-grid">
                <button
                  onClick={() => handleInvalidate('invalidate/all-search', 'Search Cache')}
                  disabled={loading}
                  className="action-btn invalidate-search"
                >
                  <span className="action-icon">🔍</span>
                  <span>Clear Search</span>
                </button>
                <button
                  onClick={() => handleInvalidate('invalidate/all-recommendations', 'Recommendations')}
                  disabled={loading}
                  className="action-btn invalidate-recs"
                >
                  <span className="action-icon">💡</span>
                  <span>Clear Recommendations</span>
                </button>
                <button
                  onClick={() => handleInvalidate('invalidate/all', 'All Caches')}
                  disabled={loading}
                  className="action-btn invalidate-all"
                >
                  <span className="action-icon">🗑️</span>
                  <span>Clear All Caches</span>
                </button>
                <button
                  onClick={refreshStats}
                  disabled={loading}
                  className="action-btn refresh"
                >
                  <span className="action-icon">🔄</span>
                  <span>Refresh Stats</span>
                </button>
                <button
                  onClick={handleResetStats}
                  disabled={loading}
                  className="action-btn reset"
                >
                  <span className="action-icon">↺</span>
                  <span>Reset Stats</span>
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="admin-modal-footer">
              <p className="footer-text">Use cache operations sparingly to avoid performance impact</p>
            </div>
          </div>
        </div>
      )}

      {toast && <Toast toast={toast} />}
    </>
  );
}

export default AdminCacheManager;
