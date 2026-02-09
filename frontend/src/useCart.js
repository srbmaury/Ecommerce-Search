import { useState, useRef, useEffect, useCallback } from 'react';
import { fetchCart, updateCart, clearCart } from './api';

export function useCart(user, showToast) {
    const [cart, setCart] = useState([]);
    const [cartCount, setCartCount] = useState(0);
    const [cartTotal, setCartTotal] = useState(0);
    const [showCart, setShowCart] = useState(false);
    const [cartLoading, setCartLoading] = useState(false);
    const [cartLoadedOnce, setCartLoadedOnce] = useState(false);
    const [clearCartLoading, setClearCartLoading] = useState(false);

    // Helper to get quantity for a product from cart
    const getCartQuantity = (productId) => {
        const item = cart.find(item => item.product_id === productId);
        return item ? item.quantity : 0;
    };

    // Debounced cart update logic
    const cartUpdateQueue = useRef({});
    const cartUpdateTimers = useRef({});

    // Recalculate cart count and total whenever cart items change
    useEffect(() => {
        const newCount = cart.reduce((sum, item) => sum + item.quantity, 0);
        const newTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        setCartCount(newCount);
        setCartTotal(newTotal);
    }, [cart]);

    const fetchCartData = useCallback(async (isInitial = false) => {
        if (!user) return;
        if (isInitial) setCartLoading(true);
        try {
            const data = await fetchCart(user.user_id);
            setCart(data.items || []);
            setCartCount(data.count || 0);
            setCartTotal(data.total || 0);
            setCartLoadedOnce(true);
        } finally {
            if (isInitial) setCartLoading(false);
        }
    }, [user]);

    const handleCartUpdate = (delta, product) => {
        const productId = product.product_id;

        setCart(prevCart => {
            const idx = prevCart.findIndex(item => item.product_id === productId);

            if (idx === -1 && delta > 0) {
                // Adding new product to cart
                return [...prevCart, {
                    product_id: productId,
                    title: product.title,
                    price: product.price,
                    category: product.category,
                    quantity: delta
                }];
            } else if (idx !== -1) {
                // Updating existing product
                const updated = [...prevCart];
                const newQuantity = Math.max(0, updated[idx].quantity + delta);

                if (newQuantity === 0) {
                    // Remove item if quantity becomes 0
                    return updated.filter((_, i) => i !== idx);
                } else {
                    // Update quantity
                    updated[idx] = { ...updated[idx], quantity: newQuantity };
                    return updated;
                }
            }
            return prevCart;
        });
        cartUpdateQueue.current[productId] = (cartUpdateQueue.current[productId] || 0) + delta;
        if (cartUpdateTimers.current[productId]) {
            clearTimeout(cartUpdateTimers.current[productId]);
        }
        cartUpdateTimers.current[productId] = setTimeout(() => {
            const netQuantity = cartUpdateQueue.current[productId];
            delete cartUpdateQueue.current[productId];
            delete cartUpdateTimers.current[productId];
            if (netQuantity === 0) return;
            updateCart(user.user_id, productId, netQuantity)
                .then(() => fetchCartData())
                .catch(err => {
                    if (showToast) showToast(err.message || 'Cart update failed', 'error');
                    fetchCartData();
                });
        }, 300);
    };

    useEffect(() => {
        if (!user) return;
        fetchCartData(true);
    }, [user, fetchCartData]);

    const clearCartHandler = async () => {
        setClearCartLoading(true);
        try {
            await clearCart(user.user_id);
            await fetchCartData();
        } finally {
            setClearCartLoading(false);
        }
    };

    return {
        cart,
        cartCount,
        cartTotal,
        showCart,
        setShowCart,
        cartLoading,
        cartLoadedOnce,
        clearCartLoading,
        getCartQuantity,
        handleCartUpdate,
        clearCartHandler,
        fetchCartData
    };
}
