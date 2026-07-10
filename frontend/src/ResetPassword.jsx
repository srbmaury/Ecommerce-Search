import React, { useState } from 'react';
import { resetPassword } from './api';
import AuthLeftPanel from './AuthLeftPanel';

export default function ResetPassword({ token, onSuccess, onBack }) {
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const passwordsMatch = !confirmPassword || password === confirmPassword;

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setLoading(true);
        setError('');
        setMessage('');

        try {
            const data = await resetPassword(token, password);
            setMessage(data.message);
            setTimeout(() => { onSuccess?.(); }, 2000);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="auth-page">
                <AuthLeftPanel />
                <div className="auth-right">
                    <div className="auth-card">
                        <h2>Invalid Link</h2>
                        <p className="auth-error">
                            This password reset link is invalid or has expired.
                        </p>
                        <p className="auth-toggle">
                            <span onClick={onBack}>Back to Login</span>
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-page">
            <AuthLeftPanel />
            <div className="auth-right">
                <div className="auth-card">
                    <h2>Create New Password</h2>
                    <p className="auth-description">Enter your new password below.</p>
                    <form onSubmit={handleSubmit}>
                        <input
                            type="password"
                            placeholder="New password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            minLength={8}
                            autoComplete="new-password"
                        />
                        <input
                            type="password"
                            placeholder="Confirm new password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            minLength={8}
                            autoComplete="new-password"
                        />
                        {confirmPassword && !passwordsMatch && (
                            <div className="auth-hint">Passwords do not match</div>
                        )}
                        <button type="submit" disabled={loading || !!message || !passwordsMatch}>
                            {loading ? 'Resetting...' : 'Reset Password'}
                        </button>
                        {error && <div className="auth-error">{error}</div>}
                        {message && <div className="auth-success">{message}</div>}
                    </form>
                    <p className="auth-toggle">
                        <span onClick={onBack}>Back to Login</span>
                    </p>
                </div>
            </div>
        </div>
    );
}
