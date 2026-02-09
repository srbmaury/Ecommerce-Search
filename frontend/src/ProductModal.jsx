import React from 'react';

export default function ProductModal({
    product,
    onClose
}) {
    if (!product) return null;
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="product-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>✕</button>
                <h2>{product.title}</h2>
                <div className="modal-price">${product.price?.toFixed(2)}</div>
                <div className="modal-meta">
                    <span className="modal-category">{product.category}</span>
                    <span className="modal-rating">⭐ {product.rating}</span>
                    <span className="modal-popularity">🔥 {product.popularity} popularity</span>
                </div>
                <p className="modal-description">{product.description}</p>
                <div className="modal-actions">
                    {/* Cart controls removed from product modal as requested */}
                </div>
            </div>
        </div>
    );
}
