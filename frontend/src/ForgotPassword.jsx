import React, { useState } from 'react';
import { forgotPassword } from './api';

export default function ForgotPassword({ onBack }) {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setMessage('');

        try {
            const data = await forgotPassword(email);
            setMessage(data.message);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <h1 className="auth-heading">Forgot Password</h1>
            <div className="auth-card">
                <h2>Reset Your Password</h2>
                <p className="auth-description">
                    Enter your email address and we&apos;ll send you a link to reset your password.
                </p>
                <form onSubmit={handleSubmit}>
                    <input
                        type="email"
                        placeholder="Email address"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                    <button type="submit" disabled={loading}>
                        {loading ? 'Sending...' : 'Send Reset Link'}
                    </button>
                    {error && <div className="auth-error">{error}</div>}
                    {message && <div className="auth-success">{message}</div>}
                </form>
                <p className="auth-toggle">
                    Remember your password?{' '}
                    <span onClick={onBack}>Back to Login</span>
                </p>
            </div>
        </div>
    );
}
