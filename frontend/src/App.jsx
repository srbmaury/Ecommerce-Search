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

	/* ---------- AUTH ---------- */
	const auth = async (e) => {
		e.preventDefault();
		const res = await fetch(
			`${API_BASE_URL}${isSignup ? '/signup' : '/login'}`,
			{
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password })
			}
		);
		const data = await res.json();
		if (res.ok) setUser(data);
	};

	const logout = () => {
		localStorage.removeItem('user');
		setUser(null);
	};

	/* ---------- SEARCH ---------- */
	const [query, setQuery] = useState('');
	const [results, setResults] = useState(null); // IMPORTANT: null vs []
	const [recent, setRecent] = useState([]);
	const [recommended, setRecommended] = useState([]);

	const search = async (e) => {
		e.preventDefault();
		const res = await fetch(
			`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&user_id=${user.user_id}`
		);
		const data = await res.json();
		// Handle both array and object response from backend
		let products = Array.isArray(data) ? data : (data.products || []);
		setResults(products);
	};

	useEffect(() => {
		if (!user) return;
		fetch(`${API_BASE_URL}/recommendations?user_id=${user.user_id}`)
			.then((r) => r.json())
			.then((d) => {
				setRecent(d.recent || []);
				setRecommended(d.similar || []);
			});
	}, [user]);

	const handleAuthSubmit = async (e) => {
		e.preventDefault();
		setAuthError("");

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
		}
	};

	/* ---------- AUTH UI ---------- */
	const [authError, setAuthError] = useState("");
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

						<button type="submit">
							{isSignup ? 'Sign Up' : 'Log In'}
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
				<button
					className="logout-btn"
					onClick={logout}
				>
					Logout
				</button>
			</header>

			<div className="heading-container">
				<h1>🛍️ Ecommerce Search Engine</h1>
				<p className='main-heading'>
					Welcome, <strong>{user.username}</strong>! You are in Group <strong>{user.group}</strong>
				</p>
			</div>

			{/* ✅ WHITE CONTENT CARD */}
			<main className="container">
				<form className="search-bar global-search" onSubmit={search}>
					<input
						value={query}
						onChange={(e) => setQuery(e.target.value)}
						placeholder="Search products"
					/>
					<button>Search</button>
				</form>
				<div className="products">
					{/* ---------- SEARCH RESULTS ---------- */}
					{results !== null && (
						<section>
							<h3>Search Results</h3>
							{results.length === 0 ? (
								<div className="empty">
									No products found. Try a different search!
								</div>
							) : (
								<div className="grid">
									{results.map((p) => (
										<ProductCard
											key={p.product_id}
											product={p}
											userId={user.user_id}
											query={query}
										/>
									))}
								</div>
							)}
						</section>
					)}

					{/* ---------- RECENTLY VIEWED ---------- */}
					<section>
						<h3>Recently Viewed</h3>
						<div className="grid">
							{recent.length === 0 ? (
								<div className="empty">No recent products.</div>
							) : (
								recent.map((p) => (
									<ProductCard
										key={p.product_id}
										product={p}
										userId={user.user_id}
									/>
								))
							)}
						</div>
					</section>

					{/* ---------- RECOMMENDED ---------- */}
					<section>
						<h3>Recommended For You</h3>
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
									/>
								))
							)}
						</div>
					</section>
				</div>
			</main>
		</div>
	);
}
