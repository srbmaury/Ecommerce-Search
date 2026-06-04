import React from 'react';

export default function Header({
    onShowAnalytics,
    onShowCart,
    cartCount,
    onLogout,
    fetchCart,
    user
}) {
    return (
        <header className="topbar">
            {onShowAnalytics && (
                <button
                    className="analytics-btn"
                    onClick={onShowAnalytics}
                >
                    📊 Analytics Dashboard
                </button>
            )}
            <div className="topbar-right">
                <button
                    className="cart-btn"
                    onClick={() => { onShowCart(); if (fetchCart && user) fetchCart(user.user_id); }}
                >
                    🛒 Cart ({cartCount})
                </button>
                <button
                    className="logout-btn"
                    onClick={onLogout}
                >
                    Logout
                </button>
            </div>
        </header>
    );
}
