import React, { useEffect, useRef } from 'react';
import { formatPrice, getCategoryColor, getCategoryEmoji } from './utils';
import StarRating from './StarRating';
import ProductReviews from './ProductReviews';

export default function ProductModal({ product, onClose, onCartUpdate, cartQuantity = 0, user }) {
    const firstFocusRef = useRef(null);
    const modalRef = useRef(null);

    useEffect(() => {
        if (!product) return;
        firstFocusRef.current?.focus();

        const handleKeyDown = (e) => {
            if (e.key !== 'Tab' || !modalRef.current) return;
            const focusable = modalRef.current.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.shiftKey) {
                if (document.activeElement === first) { e.preventDefault(); last.focus(); }
            } else {
                if (document.activeElement === last) { e.preventDefault(); first.focus(); }
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [product]);

    if (!product) return null;

    const accentColor = getCategoryColor(product.category);
    const emoji = getCategoryEmoji(product.category);

    const handleAdd = () => onCartUpdate?.(1, product);
    const handleRemove = () => onCartUpdate?.(-1, product);

    return (
        <div className="modal-overlay" onClick={onClose} aria-hidden="true">
            <div
                className="product-modal"
                role="dialog"
                aria-modal="true"
                aria-label={product.title}
                ref={modalRef}
                onClick={e => e.stopPropagation()}
            >
                <button className="modal-close" onClick={onClose} ref={firstFocusRef}>✕</button>
                <div className="modal-hero" style={{ background: `${accentColor}18` }}>
                    <span className="modal-hero-emoji">{emoji}</span>
                    <div className="modal-hero-bar" style={{ background: accentColor }} />
                </div>
                <span className="modal-category">{product.category}</span>
                <h2>{product.title}</h2>
                <div className="modal-price">${formatPrice(product.price)}</div>
                <div className="modal-meta">
                    <StarRating rating={product.rating} />
                    <span className="modal-popularity">🔥 {product.popularity} popularity</span>
                </div>
                <p className="modal-description">{product.description}</p>

                <div className="modal-cart-row">
                    {cartQuantity === 0 ? (
                        <button className="modal-add-btn" onClick={handleAdd}>
                            Add to Cart
                        </button>
                    ) : (
                        <div className="quantity-controls">
                            <button className="qty-btn qty-btn-decrement" onClick={handleRemove}>−</button>
                            <span className="qty-value">{cartQuantity}</span>
                            <button className="qty-btn qty-btn-increment" onClick={handleAdd}>+</button>
                        </div>
                    )}
                </div>

                <ProductReviews productId={product.product_id} user={user} />
            </div>
        </div>
    );
}
