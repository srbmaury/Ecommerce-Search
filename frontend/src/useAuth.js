import { useState, useEffect } from 'react';
import { login, signup } from './api';

export function useAuth() {
    const [user, setUser] = useState(() => {
        const saved = localStorage.getItem('user');
        return saved ? JSON.parse(saved) : null;
    });
    const [isSignup, setIsSignup] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [authError, setAuthError] = useState('');
    const [authLoading, setAuthLoading] = useState(false);

    useEffect(() => {
        if (user) localStorage.setItem('user', JSON.stringify(user));
    }, [user]);

    const logout = () => {
        localStorage.removeItem('user');
        setUser(null);
    };

    const handleAuthSubmit = async (e) => {
        e.preventDefault();
        setAuthError("");
        setAuthLoading(true);
        try {
            const data = isSignup
                ? await signup(username, password)
                : await login(username, password);
            setUser(data);
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
        authError,
        setAuthError,
        authLoading,
        setAuthLoading,
        handleAuthSubmit,
        logout
    };
}
