import { useState } from 'react';
import { useAuth } from './useAuth';
import { useCart } from './useCart';
import { useSearch } from './useSearch';
import AuthForm from './AuthForm';
import CartModal from './CartModal';
import ProductModal from './ProductModal';
import Header from './Header';
import Toast from './Toast';
import FiltersBar from './FiltersBar';
import ProductGrid from './ProductGrid';
import { Loading, EmptyState } from './LoadingEmptyState';
import './App.css';
import AnalyticsDashboard from './AnalyticsDashboard';

export default function App() {
	const [showAnalytics, setShowAnalytics] = useState(false);
	const {
		user,
		isSignup,
		setIsSignup,
		username,
		setUsername,
		password,
		setPassword,
		authError,
		authLoading,
		handleAuthSubmit,
		logout
	} = useAuth();

	/* ---------- TOAST ---------- */
	const [toast, setToast] = useState(null);
	const showToast = (message, type = 'error') => {
		setToast({ message, type });
		setTimeout(() => setToast(null), 3000);
	};

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
		search
	} = useSearch(user, showToast);

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
	if (!user) {
		return (
			<AuthForm
				isSignup={isSignup}
				username={username}
				password={password}
				authError={authError}
				authLoading={authLoading}
				onUsernameChange={e => setUsername(e.target.value)}
				onPasswordChange={e => setPassword(e.target.value)}
				onSubmit={handleAuthSubmit}
				onToggleMode={() => setIsSignup(s => !s)}
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
				<h1>🛍️ Ecommerce Search Engine</h1>
				<p className='main-heading'>
					Welcome, <strong>{user.username}</strong>! You are in Group <strong>{user.group}</strong>
				</p>
			</div>

			{/* Analytics Dashboard Modal */}
			{showAnalytics && (
				<div className="modal-overlay" onClick={() => setShowAnalytics(false)}>
					<div className="analytics-modal" onClick={e => e.stopPropagation()}>
						<button className="modal-close" onClick={() => setShowAnalytics(false)}>✕</button>
						<AnalyticsDashboard />
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

			{/* Product Detail Modal */}
			<ProductModal
				product={selectedProduct}
				onClose={() => setSelectedProduct(null)}
			/>

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
							<Loading>Searching...</Loading>
						</section>
					)}
					{!searchLoading && results !== null && (
						<section>
							<h3>Search Results ({filteredResults.length} products)</h3>

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
							/>

							{filteredResults.length === 0 ? (
								<EmptyState>No products found. Try adjusting filters!</EmptyState>
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
							<Loading />
						) : (
							recent.length === 0 ? (
								<EmptyState>No recent products.</EmptyState>
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
						<h3>Recommended For You</h3>
						{recsLoading ? (
							<Loading />
						) : (
							recommended.length === 0 ? (
								<EmptyState>No recommendations yet.</EmptyState>
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
