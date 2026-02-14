import React from 'react';

export default function AuthForm({
    isSignup,
    username,
    password,
    email,
    authError,
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
            <h1 className="auth-heading">Welcome to Ecommerce Search</h1>
            <div className="auth-card">
                <h2>{isSignup ? 'Sign Up' : 'Log In'}</h2>
                <form onSubmit={onSubmit}>
                    <input
                        placeholder="Username"
                        value={username}
                        onChange={onUsernameChange}
                    />
                    {isSignup && (
                        <input
                            type="email"
                            placeholder="Email (optional, for password recovery)"
                            value={email || ''}
                            onChange={onEmailChange}
                        />
                    )}
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={onPasswordChange}
                    />
                    <button type="submit" disabled={authLoading}>
                        {authLoading ? 'Loading...' : (isSignup ? 'Sign Up' : 'Log In')}
                    </button>
                    {authError && <div className="auth-error">{authError}</div>}
                </form>
                {!isSignup && (
                    <p className="forgot-password">
                        <span onClick={onForgotPassword}>Forgot password?</span>
                    </p>
                )}
                <p className="auth-toggle">
                    {isSignup ? (
                        <>
                            Already have an account?{' '}
                            <span onClick={onToggleMode}>Log In</span>
                        </>
                    ) : (
                        <>
                            Don&apos;t have an account?{' '}
                            <span onClick={onToggleMode}>Sign Up</span>
                        </>
                    )}
                </p>
            </div>
        </div>
    );
}
