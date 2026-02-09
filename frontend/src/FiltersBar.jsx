import React from 'react';

export default function FiltersBar({
    categoryFilter,
    setCategoryFilter,
    categories,
    minPrice,
    setMinPrice,
    maxPrice,
    setMaxPrice,
    sortBy,
    setSortBy
}) {
    return (
        <div className="filters-bar">
            <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
                <option value="">All Categories</option>
                {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                ))}
            </select>
            <input
                type="number"
                placeholder="Min $"
                value={minPrice}
                onChange={e => setMinPrice(e.target.value)}
                className="price-input"
            />
            <input
                type="number"
                placeholder="Max $"
                value={maxPrice}
                onChange={e => setMaxPrice(e.target.value)}
                className="price-input"
            />
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
                <option value="">Sort by</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="rating">Rating</option>
                <option value="popularity">Popularity</option>
            </select>
        </div>
    );
}
