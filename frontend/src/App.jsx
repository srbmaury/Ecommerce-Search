import { useState, useEffect } from 'react';
import ProductCard from './ProductCard';
import './App.css';
import API_BASE_URL from './config';

export default function App() {
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
		// Reset filters before applying intent
		setCategoryFilter('');
		setMinPrice('');
		setMaxPrice('');
		setSortBy('');
		try {
			const res = await fetch(
				`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&user_id=${user.user_id}`
			);
			if (!res.ok) {
				showToast('Search failed. Please try again.');
				return;
			}
			const data = await res.json();
			let products = Array.isArray(data) ? data : (data.products || []);
			setResults(products);

			// Auto-apply intent suggestions
			if (data.intent) {
				const { suggested_category, suggested_sort, suggested_min_price, suggested_max_price, detected } = data.intent;

				// Only auto-apply category if products exist with that category
				if (suggested_category && products.some(p => p.category === suggested_category)) {
					setCategoryFilter(suggested_category);
				}
				if (suggested_sort) setSortBy(suggested_sort);
				if (suggested_min_price) setMinPrice(String(suggested_min_price));
				if (suggested_max_price) setMaxPrice(String(suggested_max_price));

				// Show toast only for actionable intents (sort or price filters, not just category)
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

	const fetchCart = async () => {
		if (!user) return;
		setCartLoading(true);
		try {
			const res = await fetch(`${API_BASE_URL}/cart?user_id=${user.user_id}`);
			const data = await res.json();
			setCart(data.items || []);
			setCartCount(data.count || 0);
			setCartTotal(data.total || 0);
		} finally {
			setCartLoading(false);
		}
	};

	useEffect(() => {
		if (!user) return;
		setRecsLoading(true);
		fetch(`${API_BASE_URL}/recommendations?user_id=${user.user_id}`)
			.then((r) => r.json())
			.then((d) => {
				setRecent(d.recent || []);
				setRecommended(d.similar || []);
			})
			.finally(() => setRecsLoading(false));
		fetchCart();
	}, [user]);

	const removeFromCart = async (productId) => {
		await fetch(`${API_BASE_URL}/cart/remove`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ user_id: user.user_id, product_id: productId })
		});
		fetchCart();
	};

	const clearCart = async () => {
		await fetch(`${API_BASE_URL}/cart/clear`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ user_id: user.user_id })
		});
		fetchCart();
	};

	const handleAuthSubmit = async (e) => {
		e.preventDefault();
		setAuthError("");
		setAuthLoading(true);

		try {
			const res = await fetch(
				`${API_BASE_URL}${isSignup ? '/signup' : '/login'}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ username, password })
				}
			);

			const data = await res.json();

			if (!res.ok) {
				setAuthError(data.error || 'Authentication failed');
				return;
			}

			setUser(data);
		} catch {
			setAuthError('Network error. Please try again.');
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
					onClick={() => window.open(`${API_BASE_URL}/analytics`, '_blank')}
				>
					Analytics
				</button>
				<div className="topbar-right">
					<button
						className="cart-btn"
						onClick={() => { setShowCart(!showCart); if (!showCart) fetchCart(); }}
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

			{/* Cart Modal */}
			{showCart && (
				<div className="cart-modal">
					<div className="cart-header">
						<h3>🛒 Your Cart ({cartCount} items)</h3>
						<button className="cart-close" onClick={() => setShowCart(false)}>✕</button>
					</div>
					{cartLoading ? (
						<div className="loading">Loading cart...</div>
					) : cart.length === 0 ? (
						<div className="empty">Your cart is empty.</div>
					) : (
						<>
							<div className="cart-items">
								{cart.map((item, idx) => (
									<div key={idx} className="cart-item">
										<div className="cart-item-info" onClick={() => { setSelectedProduct(item); }}>
											<div className="cart-item-title">{item.title}</div>
											<div className="cart-item-price">${item.price?.toFixed(2)}</div>
										</div>
										<button className="cart-item-remove" onClick={() => removeFromCart(item.product_id)}>✕</button>
									</div>
								))}
							</div>
							<div className="cart-footer">
								<div className="cart-total">Total: <strong>${cartTotal.toFixed(2)}</strong></div>
								<button className="cart-clear-btn" onClick={clearCart}>Clear Cart</button>
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
							<button
								className="modal-add-btn"
								onClick={async () => {
									await fetch(`${API_BASE_URL}/cart`, {
										method: 'POST',
										headers: { 'Content-Type': 'application/json' },
										body: JSON.stringify({ user_id: user.user_id, product_id: selectedProduct.product_id })
									});
									fetchCart();
									showToast('Added to cart!', 'success');
								}}
							>
								Add to Cart
							</button>
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
												onCartUpdate={fetchCart}
												onProductClick={setSelectedProduct}
											/>
										))}
									</div>

									{/* Pagination */}
									{totalPages > 1 && (
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
									)}
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
											onCartUpdate={fetchCart}
											onProductClick={setSelectedProduct}
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
											isRecommendation
											onCartUpdate={fetchCart}
											onProductClick={setSelectedProduct}
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
