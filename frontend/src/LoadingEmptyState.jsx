import React from 'react';

export function Loading({ children = 'Loading...' }) {
    return <div className="loading">{children}</div>;
}

export function EmptyState({ children }) {
    return <div className="empty">{children}</div>;
}
