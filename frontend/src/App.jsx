import { useState, useEffect, useRef } from 'react';
import ProductCard from './ProductCard';
import './App.css';
import {
	fetchRecommendations,
	searchProducts,
	fetchCart,
	addToCart,
	removeFromCart,
	clearCart,
	login,
	signup
} from './api';
import AnalyticsDashboard from './AnalyticsDashboard';


export default function App() {
	const [showAnalytics, setShowAnalytics] = useState(false);
	const [user, setUser] = useState(() => {
		const saved = localStorage.getItem('user');
		return saved ? JSON.parse(saved) : null;
	});

	const [isSignup, setIsSignup] = useState(true);
	const [username, setUsername] = useState('');
	const [password, setPassword] = useState('');

	useEffect(() => {
		if (user) localStorage.setItem('user', JSON.stringify(user));
	}, [user]);

	const logout = () => {
		localStorage.removeItem('user');
		setUser(null);
	};

	/* ---------- SEARCH ---------- */
	const [query, setQuery] = useState('');
	const [results, setResults] = useState(null); // IMPORTANT: null vs []
	const [filteredResults, setFilteredResults] = useState([]);
	const [recent, setRecent] = useState([]);
	const [recommended, setRecommended] = useState([]);
	const [searchLoading, setSearchLoading] = useState(false);
	const [recsLoading, setRecsLoading] = useState(false);
	const [cart, setCart] = useState([]);
	const [cartCount, setCartCount] = useState(0);
	const [cartTotal, setCartTotal] = useState(0);
	const [showCart, setShowCart] = useState(false);
	const [cartLoading, setCartLoading] = useState(false);
	const [cartLoadedOnce, setCartLoadedOnce] = useState(false);

	/* ---------- FILTERS & SORT ---------- */
	const [categoryFilter, setCategoryFilter] = useState('');
	const [minPrice, setMinPrice] = useState('');
	const [maxPrice, setMaxPrice] = useState('');
	const [sortBy, setSortBy] = useState('');
	const [currentPage, setCurrentPage] = useState(1);
	const ITEMS_PER_PAGE = 12;

	const categories = ['Audio', 'Electronics', 'Computers', 'Photography', 'Accessories', 'Gaming', 'Networking', 'Smart Home', 'Storage'];

	/* ---------- TOAST ---------- */
	const [toast, setToast] = useState(null);
	const showToast = (message, type = 'error') => {
		setToast({ message, type });
		setTimeout(() => setToast(null), 3000);
	};

	/* ---------- PRODUCT DETAIL MODAL ---------- */
	const [selectedProduct, setSelectedProduct] = useState(null);

	const search = async (e) => {
		e.preventDefault();
		setSearchLoading(true);
		setCurrentPage(1);
		try {
			const data = await searchProducts(query, user.user_id);
			let products = Array.isArray(data) ? data : (data.products || []);
			setResults(products);
			if (data.intent) {
				const { suggested_category, suggested_sort, suggested_min_price, suggested_max_price, detected } = data.intent;
				const newCategory = (suggested_category && products.some(p => p.category === suggested_category)) ? suggested_category : '';
				const newSort = suggested_sort || '';
				const newMinPrice = suggested_min_price ? String(suggested_min_price) : '';
				const newMaxPrice = suggested_max_price ? String(suggested_max_price) : '';
				setCategoryFilter(newCategory);
				setSortBy(newSort);
				setMinPrice(newMinPrice);
				setMaxPrice(newMaxPrice);
				const actionableIntents = (detected || []).filter(i => i !== 'category');
				if (actionableIntents.length > 0) {
					const intentMsg = actionableIntents.map(i => i.replace('_', ' ')).join(', ');
					showToast(`Applied: ${intentMsg}`, 'success');
				}
			}
		} catch {
			showToast('Network error. Please check your connection.');
		} finally {
			setSearchLoading(false);
		}
	};

	// Apply filters and sorting to results
	useEffect(() => {
		if (!results) return;
		let filtered = [...results];

		// Category filter
		if (categoryFilter) {
			filtered = filtered.filter(p => p.category === categoryFilter);
		}

		// Price range filter
		if (minPrice) {
			filtered = filtered.filter(p => p.price >= parseFloat(minPrice));
		}
		if (maxPrice) {
			filtered = filtered.filter(p => p.price <= parseFloat(maxPrice));
		}

		// Sorting
		if (sortBy === 'price_asc') {
			filtered.sort((a, b) => a.price - b.price);
		} else if (sortBy === 'price_desc') {
			filtered.sort((a, b) => b.price - a.price);
		} else if (sortBy === 'rating') {
			filtered.sort((a, b) => b.rating - a.rating);
		} else if (sortBy === 'popularity') {
			filtered.sort((a, b) => b.popularity - a.popularity);
		}

		setFilteredResults(filtered);
		setCurrentPage(1);
	}, [results, categoryFilter, minPrice, maxPrice, sortBy]);

	// Pagination
	const totalPages = Math.ceil(filteredResults.length / ITEMS_PER_PAGE);
	const paginatedResults = filteredResults.slice(
		(currentPage - 1) * ITEMS_PER_PAGE,
		currentPage * ITEMS_PER_PAGE
	);

	const fetchCartData = async (isInitial = false) => {
		if (!user) return;
		if (isInitial) setCartLoading(true);
		try {
			const data = await fetchCart(user.user_id);
			setCart(data.items || []);
			setCartCount(data.count || 0);
			setCartTotal(data.total || 0);
			setCartLoadedOnce(true);
		} finally {
			if (isInitial) setCartLoading(false);
		}
	};

	// Helper to get quantity for a product from cart
	const getCartQuantity = (productId) => {
		const item = cart.find(item => item.product_id === productId);
		return item ? item.quantity : 0;
	};

	// Optimistic cart update for ProductCard and everywhere
	// Debounce batching for cart API updates
	const cartUpdateQueue = useRef([]);
	const cartUpdateTimer = useRef(null);

	const handleCartUpdate = (delta, productId) => {
		setCart(prevCart => {
			const idx = prevCart.findIndex(item => item.product_id === productId);
			const allProducts = [...filteredResults, ...recent, ...recommended];
			const product = allProducts.find(p => p.product_id === productId);
			if (idx === -1 && delta > 0 && product) {
				return [...prevCart, { ...product, quantity: 1 }];
			} else if (idx !== -1) {
				const updated = [...prevCart];
				updated[idx] = { ...updated[idx], quantity: Math.max(0, updated[idx].quantity + delta) };
				return updated.filter(item => item.quantity > 0);
			}
			return prevCart;
		});

		// Add update to queue
		cartUpdateQueue.current.push({ delta, productId });
		if (cartUpdateTimer.current) clearTimeout(cartUpdateTimer.current);
		cartUpdateTimer.current = setTimeout(() => {
			const updates = cartUpdateQueue.current;
			cartUpdateQueue.current = [];
			const netChanges = {};
			updates.forEach(({ delta, productId }) => {
				netChanges[productId] = (netChanges[productId] || 0) + delta;
			});
			// Build batch actions
			const actions = [];
			Object.entries(netChanges).forEach(([productId, netDelta]) => {
				if (netDelta === 0) return;
				const actionType = netDelta > 0 ? 'add' : 'remove';
				const absDelta = Math.abs(netDelta);
				for (let i = 0; i < absDelta; i++) {
					actions.push({ action: actionType, product_id: productId });
				}
			});
			if (actions.length === 0) return;
			import('./api').then(({ batchCart }) => {
				batchCart(user.user_id, actions)
					.then(() => fetchCartData())
					.catch(err => {
						showToast(err.message || 'Cart update failed', 'error');
						fetchCartData();
					});
			});
		}, 1000);
	};

	useEffect(() => {
		if (!user) return;
		setRecsLoading(true);
		fetchRecommendations(user.user_id)
			.then((d) => {
				setRecent(d.recent || []);
				setRecommended(d.similar || []);
			})
			.catch((err) => {
				setRecent([]);
				setRecommended([]);
			})
			.finally(() => setRecsLoading(false));
		fetchCartData(true); // initial load
	}, [user]);

	const removeFromCartHandler = async (productId) => {
		await removeFromCart(user.user_id, productId);
		fetchCartData();
	};

	const clearCartHandler = async () => {
		await clearCart(user.user_id);
		fetchCartData();
	};

	const handleAuthSubmit = async (e) => {
		e.preventDefault();
		setAuthError("");
		setAuthLoading(true);
		try {
			const data = isSignup
				? await signup(username, password)
				: await login(username, password);
			setUser(data);
		} catch (err) {
			setAuthError(err.message || 'Network error. Please try again.');
		} finally {
			setAuthLoading(false);
		}
	};

	/* ---------- AUTH UI ---------- */
	const [authError, setAuthError] = useState("");
	const [authLoading, setAuthLoading] = useState(false);
	if (!user) {
		return (
			<div className="auth-page">
				<h1 className="auth-heading">Welcome to Ecommerce Search</h1>

				<div className="auth-card">
					<h2>{isSignup ? 'Sign Up' : 'Log In'}</h2>

					<form onSubmit={handleAuthSubmit}>
						<input
							placeholder="Username"
							value={username}
							onChange={(e) => setUsername(e.target.value)}
						/>
						<input
							type="password"
							placeholder="Password"
							value={password}
							onChange={(e) => setPassword(e.target.value)}
						/>

						<button type="submit" disabled={authLoading}>
							{authLoading ? 'Loading...' : (isSignup ? 'Sign Up' : 'Log In')}
						</button>

						{authError && <div className="auth-error">{authError}</div>}
					</form>

					<p className="auth-toggle">
						{isSignup ? (
							<>
								Already have an account?{' '}
								<span onClick={() => setIsSignup(false)}>Log In</span>
							</>
						) : (
							<>
								Don&apos;t have an account?{' '}
								<span onClick={() => setIsSignup(true)}>Sign Up</span>
							</>
						)}
					</p>
				</div>
			</div>

		);
	}

	/* ---------- DASHBOARD ---------- */

	return (
		<div className="app">
			<header className="topbar">
				<button
					className="analytics-btn"
					onClick={() => setShowAnalytics(true)}
				>
					📊 Analytics Dashboard
				</button>
				<div className="topbar-right">
					<button
						className="cart-btn"
						onClick={() => { setShowCart(!showCart); if (!showCart) fetchCart(user.user_id); }}
					>
						🛒 Cart ({cartCount})
					</button>
					<button
						className="logout-btn"
						onClick={logout}
					>
						Logout
					</button>
				</div>
			</header>

			<div className="heading-container">
				<h1>🛍️ Ecommerce Search Engine</h1>
				<p className='main-heading'>
					Welcome, <strong>{user.username}</strong>! You are in Group <strong>{user.group}</strong>
				</p>
			</div>

			{/* Analytics Dashboard Modal */}
			{showAnalytics && (
				<div className="modal-overlay" onClick={() => setShowAnalytics(false)}>
					<div className="analytics-modal" onClick={e => e.stopPropagation()} style={{ background: '#f9f9f9', borderRadius: 16, padding: 24, maxWidth: 1300, margin: '40px auto', boxShadow: '0 4px 24px #0001', position: 'relative' }}>
						<button className="modal-close" style={{ position: 'absolute', top: 16, right: 16, fontSize: 24, background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setShowAnalytics(false)}>✕</button>
						<AnalyticsDashboard />
					</div>
				</div>
			)}

			{/* Cart Modal */}
			{showCart && (
				<div className="cart-modal">
					<div className="cart-header">
						<h3>🛒 Your Cart ({cartCount} items)</h3>
						<button className="cart-close" onClick={() => setShowCart(false)}>✕</button>
					</div>
					{cartLoading && !cartLoadedOnce ? (
						<div className="loading">Loading cart...</div>
					) : cart.length === 0 ? (
						<div className="empty">Your cart is empty.</div>
					) : (
						<>
							<div className="cart-items">
								{cart.map((item, idx) => (
									<div key={idx} className="cart-item">
										<div className="cart-item-info" onClick={() => { setSelectedProduct(item); }} style={{ flex: 1 }}>
											<div className="cart-item-title">{item.title}</div>
											<div className="cart-item-price">${item.price?.toFixed(2)} each</div>
											{item.quantity > 1 && <div style={{ fontSize: '0.9em', color: '#666', marginTop: '4px' }}>Subtotal: ${(item.price * item.quantity).toFixed(2)}</div>}
										</div>
										<div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
											<button
												onClick={() => handleCartUpdate(-1, item.product_id)}
												style={{
													width: '28px',
													height: '28px',
													borderRadius: '50%',
													border: '2px solid #f44336',
													background: 'white',
													color: '#f44336',
													fontSize: '16px',
													cursor: 'pointer',
													display: 'flex',
													alignItems: 'center',
													justifyContent: 'center'
												}}
											>
												−
											</button>
											<span style={{ fontSize: '16px', fontWeight: 'bold', minWidth: '25px', textAlign: 'center' }}>
												{item.quantity}
											</span>
											<button
												onClick={() => handleCartUpdate(1, item.product_id)}
												style={{
													width: '28px',
													height: '28px',
													borderRadius: '50%',
													border: '2px solid #4CAF50',
													background: '#4CAF50',
													color: 'white',
													fontSize: '16px',
													cursor: 'pointer',
													display: 'flex',
													alignItems: 'center',
													justifyContent: 'center'
												}}
											>
												+
											</button>
										</div>
									</div>
								))}
							</div>
							<div className="cart-footer">
								<div className="cart-total">Total: <strong>${cartTotal.toFixed(2)}</strong></div>
								<button className="cart-clear-btn" onClick={clearCartHandler}>Clear Cart</button>
							</div>
						</>
					)}
				</div>
			)}

			{/* Toast Notification */}
			{toast && (
				<div className={`toast toast-${toast.type}`}>
					{toast.message}
				</div>
			)}

			{/* Product Detail Modal */}
			{selectedProduct && (
				<div className="modal-overlay" onClick={() => setSelectedProduct(null)}>
					<div className="product-modal" onClick={(e) => e.stopPropagation()}>
						<button className="modal-close" onClick={() => setSelectedProduct(null)}>✕</button>
						<h2>{selectedProduct.title}</h2>
						<div className="modal-price">${selectedProduct.price?.toFixed(2)}</div>
						<div className="modal-meta">
							<span className="modal-category">{selectedProduct.category}</span>
							<span className="modal-rating">⭐ {selectedProduct.rating}</span>
							<span className="modal-popularity">🔥 {selectedProduct.popularity} popularity</span>
						</div>
						<p className="modal-description">{selectedProduct.description}</p>
						<div className="modal-actions">
							{/* Cart controls removed from product modal as requested */}
						</div>
					</div>
				</div>
			)}

			{/* ✅ WHITE CONTENT CARD */}
			<main className="container">
				<form className="search-bar global-search" onSubmit={search}>
					<input
						value={query}
						onChange={(e) => setQuery(e.target.value)}
						placeholder="Search products"
						disabled={searchLoading}
					/>
					<button disabled={searchLoading}>
						{searchLoading ? 'Searching...' : 'Search'}
					</button>
				</form>
				<div className="products">
					{/* ---------- SEARCH RESULTS ---------- */}
					{searchLoading && (
						<section>
							<h3>Search Results</h3>
							<div className="loading">Searching...</div>
						</section>
					)}
					{!searchLoading && results !== null && (
						<section>
							<h3>Search Results ({filteredResults.length} products)</h3>

							{/* Filters and Sort */}
							<div className="filters-bar">
								<select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
									<option value="">All Categories</option>
									{categories.map(cat => (
										<option key={cat} value={cat}>{cat}</option>
									))}
								</select>
								<input
									type="number"
									placeholder="Min $"
									value={minPrice}
									onChange={(e) => setMinPrice(e.target.value)}
									className="price-input"
								/>
								<input
									type="number"
									placeholder="Max $"
									value={maxPrice}
									onChange={(e) => setMaxPrice(e.target.value)}
									className="price-input"
								/>
								<select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
									<option value="">Sort by</option>
									<option value="price_asc">Price: Low to High</option>
									<option value="price_desc">Price: High to Low</option>
									<option value="rating">Rating</option>
									<option value="popularity">Popularity</option>
								</select>
							</div>

							{filteredResults.length === 0 ? (
								<div className="empty">
									No products found. Try adjusting filters!
								</div>
							) : (
								<>
									<div className="grid">
										{paginatedResults.map((p) => (
											<ProductCard
												key={p.product_id}
												product={p}
												userId={user.user_id}
												query={query}
												onCartUpdate={handleCartUpdate}
												onProductClick={setSelectedProduct}
												cartQuantity={getCartQuantity(p.product_id)}
											/>
										))}
									</div>
									<div className="pagination">
										<button
											onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
											disabled={currentPage === 1}
										>
											← Prev
										</button>
										<span>Page {currentPage} of {totalPages}</span>
										<button
											onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
											disabled={currentPage === totalPages}
										>
											Next →
										</button>
									</div>
								</>
							)}
						</section>
					)}

					{/* ---------- RECENTLY VIEWED ---------- */}
					<section>
						<h3>Recently Viewed</h3>
						{recsLoading ? (
							<div className="loading">Loading...</div>
						) : (
							<div className="grid">
								{recent.length === 0 ? (
									<div className="empty">No recent products.</div>
								) : (
									recent.map((p) => (
										<ProductCard
											key={p.product_id}
											product={p}
											userId={user.user_id}
											query=""
											onCartUpdate={handleCartUpdate}
											onProductClick={setSelectedProduct}
											cartQuantity={getCartQuantity(p.product_id)}
										/>
									))
								)}
							</div>
						)}
					</section>

					{/* ---------- RECOMMENDED ---------- */}
					<section>
						<h3>Recommended For You</h3>
						{recsLoading ? (
							<div className="loading">Loading...</div>
						) : (
							<div className="grid">
								{recommended.length === 0 ? (
									<div className="empty">No recommendations yet.</div>
								) : (
									recommended.map((p) => (
										<ProductCard
											key={p.product_id}
											product={p}
											userId={user.user_id}
											query=""
											isRecommendation
											onCartUpdate={handleCartUpdate}
											onProductClick={setSelectedProduct}
											cartQuantity={getCartQuantity(p.product_id)}
										/>
									))
								)}
							</div>
						)}
					</section>
				</div>
			</main>
		</div>
	);
}
