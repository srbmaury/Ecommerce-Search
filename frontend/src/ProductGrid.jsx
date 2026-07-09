import React from 'react';
import ProductCard from './ProductCard';

export default function ProductGrid({ products, token, query, onCartUpdate, onProductClick, getCartQuantity, isRecommendation }) {
    return (
        <div className="grid">
            {products.map((p) => (
                <ProductCard
                    key={p.product_id}
                    product={p}
                    token={token}
                    query={query}
                    isRecommendation={isRecommendation}
                    onCartUpdate={onCartUpdate}
                    onProductClick={onProductClick}
                    cartQuantity={getCartQuantity ? getCartQuantity(p.product_id) : 0}
                />
            ))}
        </div>
    );
}
