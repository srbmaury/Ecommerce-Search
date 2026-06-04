import { useState, useEffect } from 'react';
import { login, signup } from './api';

export function useAuth() {
    const [user, setUser] = useState(() => {
        const saved = sessionStorage.getItem('user');
        return saved ? JSON.parse(saved) : null;
    });
    const [isSignup, setIsSignup] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [authError, setAuthError] = useState('');
    const [authLoading, setAuthLoading] = useState(false);
    const [authView, setAuthView] = useState('auth'); // 'auth', 'forgot-password', 'reset-password', 'verify-email'

    useEffect(() => {
        if (user) sessionStorage.setItem('user', JSON.stringify(user));
    }, [user]);

    const logout = () => {
        sessionStorage.removeItem('user');
        setUser(null);
    };

    const handleAuthSubmit = async (e) => {
        e.preventDefault();
        setAuthError("");
        setAuthLoading(true);
        try {
            if (isSignup) {
                await signup(username, password, email || null);
                // Don't auto-login after signup - user needs to verify email first
                if (email) {
                    setAuthError('Account created successfully! Please check your email to verify your account before logging in.');
                } else {
                    setAuthError('Account created successfully! You can now login with your credentials.');
                }
                setIsSignup(false); // Switch to login view
                setUsername('');
                setPassword('');
                setEmail('');
            } else {
                const data = await login(username, password);
                setUser(data); // Only login on successful login, not signup
            }
        } catch (err) {
            setAuthError(err.message || 'Network error. Please try again.');
        } finally {
            setAuthLoading(false);
        }
    };

    return {
        user,
        setUser,
        isSignup,
        setIsSignup,
        username,
        setUsername,
        password,
        setPassword,
        email,
        setEmail,
        authError,
        setAuthError,
        authLoading,
        setAuthLoading,
        authView,
        setAuthView,
        handleAuthSubmit,
        logout
    };
}
