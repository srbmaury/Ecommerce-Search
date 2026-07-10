import { useState, useEffect } from 'react';
import { login, signup } from './api';

function readUser() {
    try {
        const saved = sessionStorage.getItem('user');
        return saved ? JSON.parse(saved) : null;
    } catch {
        sessionStorage.removeItem('user');
        return null;
    }
}

export function useAuth() {
    const [user, setUser] = useState(readUser);
    const [isSignup, setIsSignup] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [authError, setAuthError] = useState('');
    const [authSuccess, setAuthSuccess] = useState('');
    const [authLoading, setAuthLoading] = useState(false);
    const [authView, setAuthView] = useState('auth');

    useEffect(() => {
        if (user) sessionStorage.setItem('user', JSON.stringify(user));
    }, [user]);

    const logout = () => {
        sessionStorage.removeItem('user');
        setUser(null);
    };

    const handleAuthSubmit = async (e) => {
        e.preventDefault();
        setAuthError('');
        setAuthSuccess('');
        setAuthLoading(true);
        try {
            if (isSignup) {
                const data = await signup(username, password, email || null);
                if (data.token) {
                    // No email verification pending — log the user in directly
                    // instead of making them re-enter credentials on a second screen.
                    setUser(data);
                    setUsername('');
                    setPassword('');
                    setEmail('');
                } else {
                    setAuthSuccess('Account created! Check your email to verify before logging in.');
                    setIsSignup(false);
                    setUsername('');
                    setPassword('');
                    setEmail('');
                }
            } else {
                const data = await login(username, password);
                setUser(data);
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
        authSuccess,
        authLoading,
        setAuthLoading,
        authView,
        setAuthView,
        handleAuthSubmit,
        logout
    };
}
