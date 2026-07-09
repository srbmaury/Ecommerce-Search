import { useState, useEffect, useCallback, useRef } from 'react';
import {
  fetchAdminProducts,
  createAdminProduct,
  updateAdminProduct,
  deleteAdminProduct,
} from './api';
import Toast from './Toast';

const EMPTY_FORM = { title: '', description: '', category: '', price: '' };
const PAGE_SIZE = 50;

function AdminProductManager({ user }) {
  const [isAdmin, setIsAdmin] = useState(!!user?.is_admin);
  const [showModal, setShowModal] = useState(false);
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [search, setSearch] = useState('');
  const [toast, setToast] = useState(null);

  const [createForm, setCreateForm] = useState(EMPTY_FORM);
  const [creating, setCreating] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState(EMPTY_FORM);
  const [savingEdit, setSavingEdit] = useState(false);

  useEffect(() => {
    if (!user?.user_id) {
      setIsAdmin(false);
      return;
    }
    fetchAdminProducts(user.token, { limit: 1 })
      .then(() => setIsAdmin(true))
      .catch(() => {
        if (!user.is_admin) setIsAdmin(false);
      });
  }, [user?.user_id]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loadProducts = useCallback(async (searchTerm, { append = false } = {}) => {
    append ? setLoadingMore(true) : setLoading(true);
    try {
      const cursor = append ? products.length : 0;
      const data = await fetchAdminProducts(user.token, { search: searchTerm, cursor, limit: PAGE_SIZE });
      setProducts(prev => append ? [...prev, ...(data.products || [])] : (data.products || []));
      setTotal(data.total || 0);
      setHasMore(!!data.has_more);
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      append ? setLoadingMore(false) : setLoading(false);
    }
  }, [user?.token, products.length]);

  // Debounce search input: reset to page 1 after the user pauses typing, so
  // each keystroke doesn't fire a request. Skipped on the render where the
  // modal just opened — openModal() already triggers that initial load.
  const searchDebounceRef = useRef(null);
  const wasOpenRef = useRef(false);
  useEffect(() => {
    if (!showModal) {
      wasOpenRef.current = false;
      return;
    }
    if (!wasOpenRef.current) {
      wasOpenRef.current = true;
      return;
    }
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(() => loadProducts(search), 300);
    return () => clearTimeout(searchDebounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, showModal]);

  if (!isAdmin) return null;

  const openModal = () => {
    setShowModal(true);
    loadProducts(search);
  };

  const handleLoadMore = () => loadProducts(search, { append: true });

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await createAdminProduct(
        { ...createForm, price: parseFloat(createForm.price) },
        user.token
      );
      showToast('Product created', 'success');
      setCreateForm(EMPTY_FORM);
      await loadProducts(search);
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (product) => {
    setEditingId(product.product_id);
    setEditForm({
      title: product.title || '',
      description: product.description || '',
      category: product.category || '',
      price: String(product.price ?? ''),
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm(EMPTY_FORM);
  };

  const handleSaveEdit = async (productId) => {
    setSavingEdit(true);
    try {
      await updateAdminProduct(
        productId,
        { ...editForm, price: parseFloat(editForm.price) },
        user.token
      );
      showToast('Product updated', 'success');
      cancelEdit();
      await loadProducts(search);
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async (product) => {
    if (!confirm(`Delete "${product.title}"? This cannot be undone.`)) return;
    try {
      await deleteAdminProduct(product.product_id, user.token);
      showToast('Product deleted', 'success');
      await loadProducts(search);
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  return (
    <>
      <button onClick={openModal} className="admin-toggle-btn admin-product-toggle-btn" title="Product Admin Panel">
        📦
      </button>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="admin-product-modal" onClick={e => e.stopPropagation()}>

            <div className="admin-modal-header">
              <div>
                <h2>Product Management</h2>
                <p className="admin-header-sub">{total} products{search.trim() ? ' matching search' : ''}</p>
              </div>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>

            <div className="admin-modal-body">
              <div className="product-create-section">
                <h3>Add Product</h3>
                <form className="product-form" onSubmit={handleCreate}>
                  <input
                    placeholder="Title"
                    value={createForm.title}
                    onChange={e => setCreateForm(f => ({ ...f, title: e.target.value }))}
                    required
                  />
                  <input
                    placeholder="Category"
                    value={createForm.category}
                    onChange={e => setCreateForm(f => ({ ...f, category: e.target.value }))}
                  />
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="Price"
                    value={createForm.price}
                    onChange={e => setCreateForm(f => ({ ...f, price: e.target.value }))}
                    required
                  />
                  <textarea
                    placeholder="Description"
                    rows={2}
                    value={createForm.description}
                    onChange={e => setCreateForm(f => ({ ...f, description: e.target.value }))}
                  />
                  <button type="submit" className="action-btn" disabled={creating}>
                    {creating ? 'Creating...' : 'Add Product'}
                  </button>
                </form>
              </div>

              <div className="product-list-section">
                <div className="stats-header">
                  <h3>Products</h3>
                  <input
                    className="product-search-input"
                    placeholder="Search by title/category..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                  />
                </div>

                {loading ? (
                  <div className="loading" style={{ minHeight: 80 }}>Loading products...</div>
                ) : products.length === 0 ? (
                  <div className="review-list-empty">No products found.</div>
                ) : (
                  <ul className="admin-product-list">
                    {products.map(product => (
                      <li key={product.product_id} className="admin-product-row">
                        {editingId === product.product_id ? (
                          <div className="product-form product-edit-form">
                            <input
                              value={editForm.title}
                              onChange={e => setEditForm(f => ({ ...f, title: e.target.value }))}
                            />
                            <input
                              value={editForm.category}
                              onChange={e => setEditForm(f => ({ ...f, category: e.target.value }))}
                            />
                            <input
                              type="number"
                              step="0.01"
                              min="0.01"
                              value={editForm.price}
                              onChange={e => setEditForm(f => ({ ...f, price: e.target.value }))}
                            />
                            <textarea
                              rows={2}
                              value={editForm.description}
                              onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))}
                            />
                            <div className="admin-product-row-actions">
                              <button
                                className="action-btn refresh"
                                disabled={savingEdit}
                                onClick={() => handleSaveEdit(product.product_id)}
                              >
                                {savingEdit ? 'Saving...' : 'Save'}
                              </button>
                              <button className="action-btn reset" onClick={cancelEdit}>Cancel</button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="admin-product-row-info">
                              <span className="admin-product-row-title">{product.title}</span>
                              <span className="admin-product-row-meta">
                                {product.category || 'Uncategorized'} · ${Number(product.price).toFixed(2)}
                              </span>
                            </div>
                            <div className="admin-product-row-actions">
                              <button className="action-btn refresh" onClick={() => startEdit(product)}>Edit</button>
                              <button className="action-btn invalidate-all" onClick={() => handleDelete(product)}>Delete</button>
                            </div>
                          </>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
                {hasMore && !loading && (
                  <button
                    className="action-btn reset load-more-btn"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                  >
                    {loadingMore ? 'Loading...' : `Load More (${products.length} of ${total})`}
                  </button>
                )}
              </div>
            </div>

            <div className="admin-modal-footer">
              <p className="footer-text">Changes take effect immediately and are visible in search results.</p>
            </div>

          </div>
        </div>
      )}

      {toast && <Toast toast={toast} />}
    </>
  );
}

export default AdminProductManager;
