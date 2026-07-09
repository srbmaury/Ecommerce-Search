import { useState, useEffect } from 'react';
import { fetchAdminCacheDashboard, invalidateCacheEndpoint, resetCacheStats } from './api';
import Toast from './Toast';

function AdminCacheManager({ user }) {
  const [isAdmin, setIsAdmin] = useState(!!user?.is_admin);
  const [showModal, setShowModal] = useState(false);
  const [cacheStats, setCacheStats] = useState(null);
  const [adminInfo, setAdminInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Dual check: session flag (fast) + API call (handles stale sessions)
  useEffect(() => {
    if (!user?.user_id) {
      setIsAdmin(false);
      return;
    }
    fetchAdminCacheDashboard(user.token)
      .then(data => {
        setIsAdmin(true);
        setAdminInfo(data.admin);
        setCacheStats(data.cache);
        setLastUpdated(new Date());
      })
      .catch(() => {
        // Keep the session-derived isAdmin value; only hide if session also says no
        if (!user.is_admin) setIsAdmin(false);
      });
  }, [user?.user_id]);

  if (!isAdmin) return null;

  const openModal = () => {
    setShowModal(true);
    setStatsLoading(true);
    fetchAdminCacheDashboard(user.token)
      .then(data => {
        setAdminInfo(data.admin);
        setCacheStats(data.cache);
        setLastUpdated(new Date());
      })
      .catch(err => console.error('Cache stats load failed:', err))
      .finally(() => setStatsLoading(false));
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const refreshStats = async () => {
    try {
      const data = await fetchAdminCacheDashboard(user.token);
      setCacheStats(data.cache);
      setLastUpdated(new Date());
      showToast('Stats refreshed', 'success');
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  const handleInvalidate = async (endpoint, label) => {
    setLoading(true);
    try {
      const data = await invalidateCacheEndpoint(endpoint, user.token);
      showToast(`${label}: ${data.status}`, 'success');
      await refreshStats();
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetStats = async () => {
    if (!confirm('Reset cache statistics? This cannot be undone.')) return;
    setLoading(true);
    try {
      await resetCacheStats(user.token);
      showToast('Cache statistics reset', 'success');
      setCacheStats({ hits: 0, misses: 0, invalidations: 0, hit_rate: 0 });
      setLastUpdated(new Date());
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const hitRate = cacheStats ? (cacheStats.hit_rate * 100).toFixed(1) : null;
  const isHealthy = cacheStats ? cacheStats.hit_rate > 0.8 : false;

  return (
    <>
      <button onClick={openModal} className="admin-toggle-btn" title="Cache Admin Panel">
        ⚙️
      </button>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="admin-cache-modal" onClick={e => e.stopPropagation()}>

            {/* Header — fixed, never scrolls */}
            <div className="admin-modal-header">
              <div>
                <h2>Cache Dashboard</h2>
                {adminInfo && (
                  <p className="admin-header-sub">{adminInfo.username} · {adminInfo.email}</p>
                )}
              </div>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>

            {/* Scrollable body */}
            <div className="admin-modal-body">

              {/* Stats */}
              <div className="cache-stats-section">
                <div className="stats-header">
                  <h3>Cache Performance</h3>
                  {cacheStats && (
                    <div className={`health-indicator ${isHealthy ? 'healthy' : 'warning'}`}>
                      <span className="health-dot"></span>
                      {isHealthy ? 'Healthy' : 'Monitor'}
                    </div>
                  )}
                </div>

                {statsLoading ? (
                  <div className="loading" style={{ minHeight: 80 }}>Loading stats...</div>
                ) : cacheStats ? (
                  <>
                    <div className="stats-grid">
                      <div className="stat-card">
                        <div className="stat-value hits">{cacheStats.hits || 0}</div>
                        <div className="stat-label">Hits</div>
                      </div>
                      <div className="stat-card">
                        <div className="stat-value misses">{cacheStats.misses || 0}</div>
                        <div className="stat-label">Misses</div>
                      </div>
                      <div className="stat-card">
                        <div className="stat-value hitrate">{hitRate}%</div>
                        <div className="stat-label">Hit Rate</div>
                      </div>
                      <div className="stat-card">
                        <div className="stat-value invalidations">{cacheStats.invalidations || 0}</div>
                        <div className="stat-label">Clears</div>
                      </div>
                    </div>
                    <div className="stats-footnote">
                      Lifetime totals · use "Reset Stats" to clear
                      {lastUpdated && <> · {lastUpdated.toLocaleTimeString()}</>}
                    </div>
                  </>
                ) : (
                  <div className="analytics-error">Could not load cache stats.</div>
                )}
              </div>

              {/* Actions */}
              <div className="cache-actions-section">
                <h3>Cache Control</h3>
                <div className="actions-grid">
                  <button
                    onClick={() => handleInvalidate('invalidate/all-search', 'Search Cache')}
                    disabled={loading}
                    className="action-btn invalidate-search"
                  >
                    <span className="action-icon">🔍</span>
                    <span className="action-label">Clear Search</span>
                    <span className="action-hint">Removes cached search results</span>
                  </button>
                  <button
                    onClick={() => handleInvalidate('invalidate/all-recommendations', 'Recommendations')}
                    disabled={loading}
                    className="action-btn invalidate-recs"
                  >
                    <span className="action-icon">💡</span>
                    <span className="action-label">Clear Recommendations</span>
                    <span className="action-hint">Removes cached suggestions</span>
                  </button>
                  <button
                    onClick={() => handleInvalidate('invalidate/all', 'All Caches')}
                    disabled={loading}
                    className="action-btn invalidate-all"
                  >
                    <span className="action-icon">🗑️</span>
                    <span className="action-label">Clear All</span>
                    <span className="action-hint">Empties the entire cache</span>
                  </button>
                  <button
                    onClick={refreshStats}
                    disabled={loading}
                    className="action-btn refresh"
                  >
                    <span className="action-icon">🔄</span>
                    <span className="action-label">Refresh</span>
                    <span className="action-hint">Reloads stats from Redis</span>
                  </button>
                  <button
                    onClick={handleResetStats}
                    disabled={loading}
                    className="action-btn reset"
                  >
                    <span className="action-icon">↺</span>
                    <span className="action-label">Reset Stats</span>
                    <span className="action-hint">Zeroes hit/miss counters</span>
                  </button>
                </div>
              </div>

            </div>

            {/* Footer — fixed, never scrolls */}
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
