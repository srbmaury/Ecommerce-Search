import React, { useState, useEffect } from 'react';
import { verifyEmail } from './api';

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
                // Redirect after success
                setTimeout(() => {
                    onSuccess?.();
                }, 2000);
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
            <h1 className="auth-heading">Email Verification</h1>
            <div className="auth-card">
                {loading && (
                    <div className="auth-loading">
                        <p>Verifying your email...</p>
                    </div>
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
    );
}
