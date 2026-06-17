import React, { useState, useCallback } from 'react';
import { formatPrice } from './utils';

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
    // Track which product_id has a pending cart update for visual feedback
    const [pending, setPending] = useState(new Set());

    const handleQty = useCallback(async (delta, item) => {
        setPending(prev => new Set(prev).add(item.product_id));
        try {
            await onCartUpdate(delta, item);
        } finally {
            setPending(prev => {
                const next = new Set(prev);
                next.delete(item.product_id);
                return next;
            });
        }
    }, [onCartUpdate]);

    const handleRemove = useCallback((item) => {
        handleQty(-item.quantity, item);
    }, [handleQty]);

    return (
        <>
            <div
                className={`cart-overlay${show ? ' cart-overlay-visible' : ''}`}
                onClick={onClose}
            />
            <div className={`cart-drawer${show ? ' cart-drawer-open' : ''}`}>
                <div className="cart-header">
                    <h3>🛒 Cart ({cartCount})</h3>
                    <button className="cart-close" onClick={onClose}>✕</button>
                </div>

                <div className="cart-body">
                    {cartLoading && !cartLoadedOnce ? (
                        <div className="loading">Loading cart...</div>
                    ) : cart.length === 0 ? (
                        <div className="empty-state">
                            <span className="empty-state-icon">🛒</span>
                            <p>Your cart is empty</p>
                        </div>
                    ) : (
                        <div className="cart-items">
                            {cart.map((item) => {
                                const isPending = pending.has(item.product_id);
                                return (
                                    <div key={item.product_id} className={`cart-item${isPending ? ' cart-item-pending' : ''}`}>
                                        <div className="cart-item-info" onClick={() => onProductClick(item)}>
                                            <div className="cart-item-title">{item.title}</div>
                                            <div className="cart-item-price">${formatPrice(item.price)} each</div>
                                            {item.quantity > 1 && (
                                                <div className="cart-item-subtotal">
                                                    Subtotal: ${formatPrice(item.price * item.quantity)}
                                                </div>
                                            )}
                                        </div>
                                        <div className="cart-item-actions">
                                            <div className="cart-item-qty">
                                                <button
                                                    className="qty-btn qty-btn-decrement"
                                                    onClick={() => handleQty(-1, item)}
                                                    disabled={isPending}
                                                >−</button>
                                                <span className="qty-value">
                                                    {isPending ? <span className="spinner" /> : item.quantity}
                                                </span>
                                                <button
                                                    className="qty-btn qty-btn-increment"
                                                    onClick={() => handleQty(1, item)}
                                                    disabled={isPending}
                                                >+</button>
                                            </div>
                                            <button
                                                className="cart-item-remove"
                                                onClick={() => handleRemove(item)}
                                                disabled={isPending}
                                                title="Remove item"
                                            >Remove</button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {cart.length > 0 && (
                    <div className="cart-footer">
                        <div className="cart-total">
                            Total: <strong>${formatPrice(cartTotal)}</strong>
                        </div>
                        <button
                            className="cart-clear-btn"
                            onClick={onClearCart}
                            disabled={clearCartLoading}
                        >
                            {clearCartLoading && <span className="spinner" />}
                            {clearCartLoading ? 'Clearing...' : 'Clear Cart'}
                        </button>
                    </div>
                )}
            </div>
        </>
    );
}
