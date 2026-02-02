import { useState, useEffect } from 'react';
import { addToCart, removeFromCart, logEvent } from './api';

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

    const handleAddToCart = async (e) => {
        e.stopPropagation();
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
        if (onCartUpdate) onCartUpdate(1);
        try {
            await addToCart(userId, product.product_id, query || '');
        } catch (err) {
            setQuantity(prev => (prev > 1 ? prev - 1 : 0));
            if (newQuantity <= 1) setAdded(false);
            alert(err.message || 'Failed to add to cart');
        }
    };

    const handleRemoveFromCart = async (e) => {
        e.stopPropagation();
        let newQuantity;
        setQuantity(prev => {
            newQuantity = prev - 1;
            return Math.max(0, newQuantity);
        });
        if (quantity <= 1) {
            setAdded(false);
        }
        if (onCartUpdate) onCartUpdate(-1);
        try {
            await removeFromCart(userId, product.product_id);
        } catch {
            // Optionally revert UI or show error
        }
    };

    const onClick = async (e) => {
        if (e.target.tagName === 'BUTTON') return;
        if (onProductClick) onProductClick(product);
        if (!isRecommendation) {
            try {
                await logEvent('click', product.product_id, query, userId);
            } catch { }
        }
    };

    return (
        <div className="product-card" onClick={onClick}>
            <div className="pc-title">{product.title}</div>
            <div className="pc-price">${product.price?.toFixed(2)}</div>
            <div className="pc-meta">{product.category} • Rating: {product.rating}</div>
            {!added ? (
                <button className="pc-btn" onClick={handleAddToCart}>
                    Add to Cart
                </button>
            ) : (
                <div className="quantity-controls" onClick={e => e.stopPropagation()} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    padding: '8px'
                }}>
                    <button
                        onClick={handleRemoveFromCart}
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
                    }}>{quantity}</span>
                    <button
                        onClick={handleAddToCart}
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
