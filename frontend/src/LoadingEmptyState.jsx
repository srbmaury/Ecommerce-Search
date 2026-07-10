import React from 'react';

export function Loading({ children = 'Loading...' }) {
    return <div className="loading">{children}</div>;
}

export function EmptyState({ children, icon = '📭' }) {
    return (
        <div className="empty-state">
            <span className="empty-state-icon">{icon}</span>
            <p>{children}</p>
        </div>
    );
}

function SkeletonCard() {
    return (
        <div className="product-card skeleton-card" aria-hidden="true">
            <div className="pc-accent-bar skeleton-shimmer" />
            <div className="pc-body">
                <div className="skeleton-shimmer skeleton-category-chip" />
                <div className="skeleton-shimmer skeleton-title-line" />
                <div className="skeleton-shimmer skeleton-title-line skeleton-title-short" />
                <div className="skeleton-shimmer skeleton-stars-row" />
                <div className="skeleton-shimmer skeleton-price-line" />
                <div className="skeleton-shimmer skeleton-action-btn" />
            </div>
        </div>
    );
}

export function SkeletonGrid({ count = 8 }) {
    return (
        <div className="grid skeleton-grid">
            {Array.from({ length: count }, (_, i) => <SkeletonCard key={i} />)}
        </div>
    );
}
