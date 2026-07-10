import React from 'react';

export default function Header({
    onShowAnalytics,
    onShowCart,
    cartCount,
    onLogout,
    user
}) {
    return (
        <header className="topbar">
            <div className="topbar-brand">
                <span className="brand-logo">🛍️</span>
                <span className="brand-name">Ecommerce-Search</span>
            </div>
            <div className="topbar-right">
                {onShowAnalytics && (
                    <button className="analytics-btn" onClick={onShowAnalytics}>
                        📊 Analytics
                    </button>
                )}
                <button
                    className="cart-btn"
                    onClick={onShowCart}
                >
                    🛒 Cart
                    {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
                </button>
                <button className="logout-btn" onClick={onLogout}>
                    Logout
                </button>
            </div>
        </header>
    );
}
