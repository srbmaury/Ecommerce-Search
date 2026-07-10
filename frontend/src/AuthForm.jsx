import React from 'react';
import AuthLeftPanel from './AuthLeftPanel';

export default function AuthForm({
    isSignup,
    username,
    password,
    email,
    authError,
    authSuccess,
    authLoading,
    onUsernameChange,
    onPasswordChange,
    onEmailChange,
    onSubmit,
    onToggleMode,
    onForgotPassword
}) {
    return (
        <div className="auth-page">
            <AuthLeftPanel />
            <div className="auth-right">
                <div className="auth-card">
                    <h2>{isSignup ? 'Create an account' : 'Welcome back'}</h2>
                    <form onSubmit={onSubmit}>
                        <input
                            placeholder={isSignup ? 'Username' : 'Username or Email'}
                            value={username}
                            onChange={onUsernameChange}
                            autoComplete="username"
                            required
                            minLength={3}
                        />
                        {isSignup && (
                            <input
                                type="email"
                                placeholder="Email (optional, for password recovery)"
                                value={email || ''}
                                onChange={onEmailChange}
                                autoComplete="email"
                            />
                        )}
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={onPasswordChange}
                            autoComplete={isSignup ? 'new-password' : 'current-password'}
                            required
                            minLength={8}
                        />
                        <button type="submit" disabled={authLoading}>
                            {authLoading ? 'Loading...' : (isSignup ? 'Sign Up' : 'Log In')}
                        </button>
                        {authSuccess && <div className="auth-success">{authSuccess}</div>}
                        {authError && <div className="auth-error">{authError}</div>}
                    </form>
                    {!isSignup && (
                        <p className="forgot-password">
                            <span onClick={onForgotPassword}>Forgot password?</span>
                        </p>
                    )}
                    <p className="auth-toggle">
                        {isSignup ? (
                            <>Already have an account? <span onClick={onToggleMode}>Log In</span></>
                        ) : (
                            <>Don&apos;t have an account? <span onClick={onToggleMode}>Sign Up</span></>
                        )}
                    </p>
                </div>
            </div>
        </div>
    );
}
