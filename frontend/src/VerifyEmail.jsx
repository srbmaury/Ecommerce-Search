import React, { useState, useEffect } from 'react';
import { verifyEmail } from './api';
import AuthLeftPanel from './AuthLeftPanel';

export default function VerifyEmail({ token, onSuccess, onBack }) {
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        if (!token) {
            setLoading(false);
            setError('No verification token provided');
            return;
        }

        const verify = async () => {
            try {
                const data = await verifyEmail(token);
                setMessage(data.message);
                setTimeout(() => { onSuccess?.(); }, 2000);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        verify();
    }, [token, onSuccess]);

    return (
        <div className="auth-page">
            <AuthLeftPanel />
            <div className="auth-right">
                <div className="auth-card">
                    <h2>Email Verification</h2>
                    {loading && (
                        <div className="auth-loading">Verifying your email...</div>
                    )}
                    {message && (
                        <div className="auth-success">
                            <p>{message}</p>
                            <p>Redirecting to login...</p>
                        </div>
                    )}
                    {error && (
                        <>
                            <div className="auth-error">{error}</div>
                            <p className="auth-toggle">
                                <span onClick={onBack}>Back to Login</span>
                            </p>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
