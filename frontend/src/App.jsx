import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';
import { useCart } from './useCart';
import { useSearch } from './useSearch';
import AuthForm from './AuthForm';
import ForgotPassword from './ForgotPassword';
import ResetPassword from './ResetPassword';
import VerifyEmail from './VerifyEmail';
import CartModal from './CartModal';
import ProductModal from './ProductModal';
import Header from './Header';
import Toast from './Toast';
import FiltersBar from './FiltersBar';
import ProductGrid from './ProductGrid';
import { Loading, EmptyState, SkeletonGrid } from './LoadingEmptyState';
import AdminCacheManager from './AdminCacheManager';
import './App.css';
import AnalyticsDashboard from './AnalyticsDashboard';

function getGreeting() {
	const h = new Date().getHours();
	if (h < 12) return 'Good morning';
	if (h < 17) return 'Good afternoon';
	return 'Good evening';
}

export default function App() {
	const initialRouteState = (() => {
		const params = new URLSearchParams(window.location.search);
		const routeToken = params.get('token');
		const path = window.location.pathname;

		if (path.includes('reset-password') && routeToken) {
			return { token: routeToken, view: 'reset-password' };
		}

		if (path.includes('verify-email') && routeToken) {
			return { token: routeToken, view: 'verify-email' };
		}

		return { token: null, view: 'auth' };
	})();

	const [showAnalytics, setShowAnalytics] = useState(false);
	const {
		user,
		isSignup,
		setIsSignup,
		username,
		setUsername,
		password,
		setPassword,
		email,
		setEmail,
		authError,
		authSuccess,
		authLoading,
		authView,
		setAuthView,
		handleAuthSubmit,
		logout
	} = useAuth();

	const [urlToken, setUrlToken] = useState(initialRouteState.token);

	useEffect(() => {
		if (initialRouteState.view !== 'auth') {
			setAuthView(initialRouteState.view);
		}
	}, [initialRouteState.view, setAuthView]);

	const clearUrlAndGoToAuth = () => {
		window.history.pushState({}, '', '/');
		setUrlToken(null);
		setAuthView('auth');
		setIsSignup(false); // Always go to login view, not signup
	};

	/* ---------- TOAST ---------- */
	const [toast, setToast] = useState(null);
	const toastTimeoutRef = useRef(null);
	const showToast = useCallback((message, type = 'error') => {
		setToast({ message, type });
		if (toastTimeoutRef.current) {
			clearTimeout(toastTimeoutRef.current);
		}
		toastTimeoutRef.current = setTimeout(() => setToast(null), 3000);
	}, []);

	useEffect(() => {
		return () => {
			if (toastTimeoutRef.current) {
				clearTimeout(toastTimeoutRef.current);
			}
		};
	}, []);

	/* ---------- SEARCH ---------- */
	const {
		query,
		setQuery,
		results,
		filteredResults,
		recent,
		recommended,
		searchLoading,
		recsLoading,
		categoryFilter,
		setCategoryFilter,
		minPrice,
		setMinPrice,
		maxPrice,
		setMaxPrice,
		sortBy,
		setSortBy,
		currentPage,
		setCurrentPage,
		categories,
		totalPages,
		paginatedResults,
		hasMoreResults,
		isLoadingMore,
		search,
		appliedIntent,
	} = useSearch(user, showToast);

	const clearFilters = useCallback(() => {
		setCategoryFilter('');
		setMinPrice('');
		setMaxPrice('');
		setSortBy('');
	}, [setCategoryFilter, setMinPrice, setMaxPrice, setSortBy]);

	/* ---------- CART ---------- */
	const {
		cart,
		cartCount,
		cartTotal,
		showCart,
		setShowCart,
		cartLoading,
		cartLoadedOnce,
		clearCartLoading,
		getCartQuantity,
		handleCartUpdate,
		clearCartHandler
	} = useCart(user, showToast);

	/* ---------- PRODUCT DETAIL MODAL ---------- */
	const [selectedProduct, setSelectedProduct] = useState(null);

	/* ---------- DOCUMENT TITLE ---------- */
	useEffect(() => {
		const base = 'Ecommerce-Search';
		if (selectedProduct) {
			document.title = `${selectedProduct.title} — ${base}`;
		} else if (results !== null && query.trim()) {
			document.title = `${query.trim()} — ${base}`;
		} else {
			document.title = base;
		}
	}, [selectedProduct, results, query]);

	/* ---------- ESC KEY ---------- */
	useEffect(() => {
		const onKeyDown = (e) => {
			if (e.key !== 'Escape') return;
			if (showCart) { setShowCart(false); return; }
			if (selectedProduct) { setSelectedProduct(null); return; }
			if (showAnalytics) setShowAnalytics(false);
		};
		document.addEventListener('keydown', onKeyDown);
		return () => document.removeEventListener('keydown', onKeyDown);
	}, [showCart, selectedProduct, showAnalytics]);

	if (!user) {
		// Handle different auth views
		if (authView === 'forgot-password') {
			return (
				<ForgotPassword
					onBack={() => setAuthView('auth')}
				/>
			);
		}
		if (authView === 'reset-password') {
			return (
				<ResetPassword
					token={urlToken}
					onSuccess={clearUrlAndGoToAuth}
					onBack={clearUrlAndGoToAuth}
				/>
			);
		}
		if (authView === 'verify-email') {
			return (
				<VerifyEmail
					token={urlToken}
					onSuccess={clearUrlAndGoToAuth}
					onBack={clearUrlAndGoToAuth}
				/>
			);
		}
		return (
			<AuthForm
				isSignup={isSignup}
				username={username}
				password={password}
				email={email}
				authError={authError}
				authSuccess={authSuccess}
				authLoading={authLoading}
				onUsernameChange={e => setUsername(e.target.value)}
				onPasswordChange={e => setPassword(e.target.value)}
				onEmailChange={e => setEmail(e.target.value)}
				onSubmit={handleAuthSubmit}
				onToggleMode={() => setIsSignup(s => !s)}
				onForgotPassword={() => setAuthView('forgot-password')}
			/>
		);
	}

	/* ---------- DASHBOARD ---------- */

	return (
		<div className="app">
			<Header
				onShowAnalytics={() => setShowAnalytics(true)}
				onShowCart={() => setShowCart(!showCart)}
				cartCount={cartCount}
				onLogout={logout}
				user={user}
			/>

			<div className="heading-container">
				<h1>{getGreeting()}, {user.username}!</h1>
				<p className='main-heading'>Discover great products, tailored for you.</p>
			</div>

			{/* Analytics Dashboard Modal */}
			{showAnalytics && (
				<div className="modal-overlay" onClick={() => setShowAnalytics(false)}>
					<div className="analytics-modal" onClick={e => e.stopPropagation()}>
						<button className="modal-close" onClick={() => setShowAnalytics(false)}>✕</button>
						<AnalyticsDashboard user={user} />
					</div>
				</div>
			)}

			{/* Cart Modal */}
			<CartModal
				show={showCart}
				cart={cart}
				cartCount={cartCount}
				cartTotal={cartTotal}
				cartLoading={cartLoading}
				cartLoadedOnce={cartLoadedOnce}
				clearCartLoading={clearCartLoading}
				onClose={() => setShowCart(false)}
				onCartUpdate={handleCartUpdate}
				onClearCart={clearCartHandler}
				onProductClick={setSelectedProduct}
			/>

			{/* Toast Notification */}
			<Toast toast={toast} />
			{/* Admin Cache Manager (only visible to admins) */}
			<AdminCacheManager user={user} />
			{/* Product Detail Modal */}
			<ProductModal
				product={selectedProduct}
				onClose={() => setSelectedProduct(null)}
				onCartUpdate={handleCartUpdate}
				cartQuantity={selectedProduct ? getCartQuantity(selectedProduct.product_id) : 0}
			/>

			<main className="container">
				<form className="search-bar global-search" onSubmit={search}>
					<input
						value={query}
						onChange={(e) => setQuery(e.target.value)}
						placeholder="Search for laptops, headphones, cameras..."
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
							<h3>🔍 Search Results</h3>
							<Loading>Searching...</Loading>
						</section>
					)}
					{!searchLoading && results !== null && (
						<section>
							<h3>🔍 Search Results ({filteredResults.length} products)</h3>
							{appliedIntent && appliedIntent.length > 0 && (
								<div className="intent-chips">
									<span className="intent-chips-label">Interpreted as:</span>
									{appliedIntent.map((chip, i) => (
										<span key={i} className={`intent-chip intent-chip-${chip.kind}`}>{chip.label}</span>
									))}
								</div>
							)}

							{/* Filters and Sort */}
							<FiltersBar
								categoryFilter={categoryFilter}
								setCategoryFilter={setCategoryFilter}
								categories={categories}
								minPrice={minPrice}
								setMinPrice={setMinPrice}
								maxPrice={maxPrice}
								setMaxPrice={setMaxPrice}
								sortBy={sortBy}
								setSortBy={setSortBy}
								onClearFilters={clearFilters}
							/>

							{filteredResults.length === 0 ? (
								<EmptyState icon="🔍">No products found. Try adjusting your filters!</EmptyState>
							) : (
								<>
									<ProductGrid
										products={paginatedResults}
										userId={user.user_id}
										query={query}
										onCartUpdate={handleCartUpdate}
										onProductClick={setSelectedProduct}
										getCartQuantity={getCartQuantity}
									/>
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
											disabled={isLoadingMore || (!hasMoreResults && currentPage === totalPages)}
										>
											{isLoadingMore ? 'Loading…' : 'Next →'}
										</button>
									</div>
								</>
							)}
						</section>
					)}

					{/* ---------- RECENTLY VIEWED ---------- */}
					<section>
						<h3>🕐 Recently Viewed</h3>
						{recsLoading ? (
							<SkeletonGrid count={8} />
						) : (
							recent.length === 0 ? (
								<EmptyState icon="👀">No recently viewed products yet.</EmptyState>
							) : (
								<ProductGrid
									products={recent}
									userId={user.user_id}
									query=""
									onCartUpdate={handleCartUpdate}
									onProductClick={setSelectedProduct}
									getCartQuantity={getCartQuantity}
								/>
							)
						)}
					</section>

					{/* ---------- RECOMMENDED ---------- */}
					<section>
						<h3>✨ Recommended For You</h3>
						{recsLoading ? (
							<SkeletonGrid count={8} />
						) : (
							recommended.length === 0 ? (
								<EmptyState icon="✨">No recommendations yet — search for a few products first!</EmptyState>
							) : (
								<ProductGrid
									products={recommended}
									userId={user.user_id}
									query=""
									isRecommendation
									onCartUpdate={handleCartUpdate}
									onProductClick={setSelectedProduct}
									getCartQuantity={getCartQuantity}
								/>
							)
						)}
					</section>
				</div>
			</main>
		</div>
	);
}
