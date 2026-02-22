import { logEvent } from './api';

export default function ProductCard({
    product,
    userId,
    query,
    isRecommendation,
    onCartUpdate,
    onProductClick,
    cartQuantity = 0
}) {
    // Cart controls are now fully controlled by cartQuantity prop
    const handleAddToCart = (e) => {
        e.stopPropagation();
        if (onCartUpdate) onCartUpdate(1, product);
    };

    const handleRemoveFromCart = (e) => {
        e.stopPropagation();
        if (onCartUpdate) onCartUpdate(-1, product);
    };

    const onClick = async (e) => {
        if (e.target.tagName === 'BUTTON') return;
        if (onProductClick) onProductClick(product);
        if (!isRecommendation) {
            try {
                await logEvent('click', product.product_id, query, userId);
            } catch (err) {
                console.error('Failed to log click event:', err);
            }
        }
    };

    return (
        <div className="product-card" onClick={onClick}>
            <div className="pc-title">{product.title}</div>
            <div className="pc-price">${product.price?.toFixed(2)}</div>
            <div className="pc-meta">{product.category} • Rating: {product.rating}</div>
            {cartQuantity === 0 ? (
                <button className="pc-btn" onClick={handleAddToCart}>
                    Add to Cart
                </button>
            ) : (
                <div className="quantity-controls" onClick={e => e.stopPropagation()}>
                    <button
                        onClick={handleRemoveFromCart}
                        className="qty-btn qty-btn-decrement"
                    >
                        −
                    </button>
                    <span className="qty-value">{cartQuantity}</span>
                    <button
                        onClick={handleAddToCart}
                        className="qty-btn qty-btn-increment"
                    >
                        +
                    </button>
                </div>
            )}
        </div>
    );
}
