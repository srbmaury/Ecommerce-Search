import { logEvent } from './api';
import { formatPrice, getCategoryColor, getCategoryEmoji } from './utils';
import StarRating from './StarRating';

export default function ProductCard({
    product,
    token,
    query,
    isRecommendation,
    onCartUpdate,
    onProductClick,
    cartQuantity = 0
}) {
    const accentColor = getCategoryColor(product.category);
    const emoji = getCategoryEmoji(product.category);

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
                await logEvent('click', product.product_id, query, token);
            } catch (err) {
                console.error('Failed to log click event:', err);
            }
        }
    };

    return (
        <div className="product-card" onClick={onClick}>
            <div className="pc-hero" style={{ background: `${accentColor}18` }}>
                <span className="pc-hero-emoji">{emoji}</span>
                <div className="pc-accent-bar" style={{ background: accentColor }} />
            </div>
            <div className="pc-body">
                {product.category && (
                    <span className="pc-category" style={{ color: accentColor, background: `${accentColor}18` }}>
                        {product.category}
                    </span>
                )}
                <div className="pc-title">{product.title}</div>
                <StarRating rating={product.rating} />
                <div className="pc-price">${formatPrice(product.price)}</div>
                {cartQuantity === 0 ? (
                    <button className="pc-btn" onClick={handleAddToCart}>
                        Add to Cart
                    </button>
                ) : (
                    <div className="quantity-controls" onClick={e => e.stopPropagation()}>
                        <button onClick={handleRemoveFromCart} className="qty-btn qty-btn-decrement">−</button>
                        <span className="qty-value">{cartQuantity}</span>
                        <button onClick={handleAddToCart} className="qty-btn qty-btn-increment">+</button>
                    </div>
                )}
            </div>
        </div>
    );
}
