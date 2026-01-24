import { useState } from 'react';
import API_BASE_URL from './config';

async function logEvent(eventType, productId, query, userId) {
    try {
        await fetch(`${API_BASE_URL}/event`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                query: query || '',
                product_id: productId,
                event: eventType
            })
        });
    } catch { }
}

export default function ProductCard({
    product,
    userId,
    query,
    isRecommendation,
    onCartUpdate,
    onProductClick
}) {
    const [added, setAdded] = useState(false);

    const addToCart = async (e) => {
        e.stopPropagation();
        if (added) return;
        setAdded(true);

        await fetch(`${API_BASE_URL}/cart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                product_id: product.product_id
            })
        });

        if (onCartUpdate) onCartUpdate();
    };

    const onClick = async (e) => {
        if (e.target.tagName === 'BUTTON') return;
        if (!isRecommendation) {
            await logEvent('click', product.product_id, query, userId);
        }
        if (onProductClick) onProductClick(product);
    };

    return (
        <div className="product-card" onClick={onClick}>
            <div className="pc-title">{product.title}</div>

            <div className="pc-price">
                ${product.price?.toFixed(2)}
            </div>

            <div className="pc-meta">
                {product.category} • Rating: {product.rating}
            </div>

            <button
                className={`pc-btn${added ? ' added' : ''}`}
                onClick={addToCart}
                disabled={added}
            >
                {added ? 'Added' : 'Add to Cart'}
            </button>
        </div>
    );
}
