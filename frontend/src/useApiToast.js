import { useCallback } from 'react';

const DEFAULT_MESSAGE = 'Network error. Please check your connection.';

export function useApiToast(showToast) {
    const toastApiError = useCallback((error, fallbackMessage = DEFAULT_MESSAGE) => {
        const message = error?.message || fallbackMessage;
        if (showToast) {
            showToast(message, 'error');
        }
    }, [showToast]);

    return { toastApiError };
}
