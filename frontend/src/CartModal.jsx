import React from 'react';

export default function CartModal({
    show,
    cart,
    cartCount,
    cartTotal,
    cartLoading,
    cartLoadedOnce,
    clearCartLoading,
    onClose,
    onCartUpdate,
    onClearCart,
    onProductClick
}) {
    if (!show) return null;
    return (
        <div className="cart-modal">
            <div className="cart-header">
                <h3>🛒 Your Cart ({cartCount} items)</h3>
                <button className="cart-close" onClick={onClose}>✕</button>
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
                                <div className="cart-item-info" onClick={() => onProductClick(item)} style={{ flex: 1 }}>
                                    <div className="cart-item-title">{item.title}</div>
                                    <div className="cart-item-price">${item.price?.toFixed(2)} each</div>
                                    {item.quantity > 1 && <div style={{ fontSize: '0.9em', color: '#666', marginTop: '4px' }}>Subtotal: ${(item.price * item.quantity).toFixed(2)}</div>}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <button
                                        onClick={() => onCartUpdate(-1, item)}
                                        style={{
                                            width: '28px', height: '28px', borderRadius: '50%', border: '2px solid #f44336', background: 'white', color: '#f44336', fontSize: '16px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center'
                                        }}
                                    >
                                        −
                                    </button>
                                    <span style={{ fontSize: '16px', fontWeight: 'bold', minWidth: '25px', textAlign: 'center' }}>{item.quantity}</span>
                                    <button
                                        onClick={() => onCartUpdate(1, item)}
                                        style={{
                                            width: '28px', height: '28px', borderRadius: '50%', border: '2px solid #4CAF50', background: '#4CAF50', color: 'white', fontSize: '16px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center'
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
                        <button className="cart-clear-btn" onClick={onClearCart} disabled={clearCartLoading}>
                            {clearCartLoading ? (
                                <span className="spinner" style={{ marginRight: 8, verticalAlign: 'middle' }}></span>
                            ) : null}
                            {clearCartLoading ? 'Clearing...' : 'Clear Cart'}
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
