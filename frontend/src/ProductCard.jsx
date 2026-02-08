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
        if (onCartUpdate) onCartUpdate(1, product.product_id);
    };

    const handleRemoveFromCart = (e) => {
        e.stopPropagation();
        if (onCartUpdate) onCartUpdate(-1, product.product_id);
    };

    const onClick = async (e) => {
        if (e.target.tagName === 'BUTTON') return;
        if (onProductClick) onProductClick(product);
        console.log('ProductCard clicked:', { isRecommendation, productId: product.product_id, userId, query });
        if (!isRecommendation) {
            try {
                console.log('Logging click event for product:', product.product_id);
                await logEvent('click', product.product_id, query, userId);
                console.log('Click event logged successfully');
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
                    }}>{cartQuantity}</span>
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
