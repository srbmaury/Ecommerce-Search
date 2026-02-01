import { useState, useEffect } from 'react';
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
    onProductClick,
    cartQuantity = 0
}) {
    const [added, setAdded] = useState(cartQuantity > 0);
    const [quantity, setQuantity] = useState(cartQuantity);

    // Sync local state with prop changes (when cart is updated externally)
    useEffect(() => {
        setQuantity(cartQuantity);
        setAdded(cartQuantity > 0);
    }, [cartQuantity]);

    const addToCart = async (e) => {
        e.stopPropagation();
        // Optimistic UI update
        let newQuantity;
        if (!added) {
            setAdded(true);
            setQuantity(1);
            newQuantity = 1;
        } else {
            setQuantity(prev => {
                newQuantity = prev + 1;
                return newQuantity;
            });
        }
        if (onCartUpdate) onCartUpdate(1); // +1 delta

        // Async backend update
        try {
            const res = await fetch(`${API_BASE_URL}/cart`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    product_id: product.product_id,
                    query: query || ''
                })
            });
            const data = await res.json();
            if (!res.ok) {
                // Revert optimistic update if backend fails
                setQuantity(prev => (prev > 1 ? prev - 1 : 0));
                if (newQuantity <= 1) setAdded(false);
                if (res.status === 404) {
                    alert('Session expired. Please login again.');
                    localStorage.removeItem('user');
                    window.location.reload();
                    return;
                }
                alert(data.error || 'Failed to add to cart');
            }
        } catch {
            setQuantity(prev => (prev > 1 ? prev - 1 : 0));
            if (newQuantity <= 1) setAdded(false);
            alert('Network error. Please try again.');
        }
    };

    const decrementCart = async (e) => {
        e.stopPropagation();
        // Optimistic UI update
        let newQuantity;
        setQuantity(prev => {
            newQuantity = prev - 1;
            return Math.max(0, newQuantity);
        });
        if (quantity <= 1) {
            setAdded(false);
        }
        if (onCartUpdate) onCartUpdate(-1); // -1 delta

        // Async backend update
        try {
            await fetch(`${API_BASE_URL}/cart/remove`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    product_id: product.product_id
                })
            });
        } catch {
            // Optionally revert UI or show error
        }
    };

    const onClick = async (e) => {
        if (e.target.tagName === 'BUTTON') return;
        // Optimistic UI: call onProductClick immediately
        if (onProductClick) onProductClick(product);
        // Async backend update
        if (!isRecommendation) {
            logEvent('click', product.product_id, query, userId);
        }
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

            {!added ? (
                <button
                    className="pc-btn"
                    onClick={addToCart}
                >
                    Add to Cart
                </button>
            ) : (
                <div className="quantity-controls" onClick={(e) => e.stopPropagation()} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    padding: '8px'
                }}>
                    <button
                        onClick={decrementCart}
                        style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            border: '2px solid #4CAF50',
                            background: 'white',
                            color: '#4CAF50',
                            fontSize: '18px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        −
                    </button>
                    <span style={{
                        fontSize: '16px',
                        fontWeight: 'bold',
                        minWidth: '30px',
                        textAlign: 'center'
                    }}>
                        {quantity}
                    </span>
                    <button
                        onClick={addToCart}
                        style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            border: '2px solid #4CAF50',
                            background: '#4CAF50',
                            color: 'white',
                            fontSize: '18px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        +
                    </button>
                </div>
            )}
        </div>
    );
}
