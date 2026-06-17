import React from 'react';

export default function AuthLeftPanel() {
    return (
        <div className="auth-left">
            <div className="auth-brand-panel">
                <span className="auth-brand-icon">🛍️</span>
                <h1>Ecommerce-Search</h1>
                <p>ML-powered product discovery with personalized recommendations tailored just for you.</p>
                <div className="auth-features">
                    <div className="auth-feature-item">
                        <span className="auth-feature-check">✓</span>
                        Smart semantic search
                    </div>
                    <div className="auth-feature-item">
                        <span className="auth-feature-check">✓</span>
                        Personalized recommendations
                    </div>
                    <div className="auth-feature-item">
                        <span className="auth-feature-check">✓</span>
                        Real-time cart &amp; history
                    </div>
                </div>
            </div>
        </div>
    );
}
