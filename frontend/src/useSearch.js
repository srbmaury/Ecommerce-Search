import { useState, useEffect, useCallback, useMemo } from 'react';
import { searchProducts, fetchRecommendations } from './api';

export function useSearch(user, showToast) {
    // Search state
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null); // IMPORTANT: null vs []
    const [filteredResults, setFilteredResults] = useState([]);
    const [recent, setRecent] = useState([]);
    const [recommended, setRecommended] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [recsLoading, setRecsLoading] = useState(false);

    // Filter & pagination state
    const [categoryFilter, setCategoryFilter] = useState('');
    const [minPrice, setMinPrice] = useState('');
    const [maxPrice, setMaxPrice] = useState('');
    const [sortBy, setSortBy] = useState('');
    const [currentPage, setCurrentPage] = useState(1);

    const ITEMS_PER_PAGE = 12;
    const categories = ['Audio', 'Electronics', 'Computers', 'Photography', 'Accessories', 'Gaming', 'Networking', 'Smart Home', 'Storage'];

    // Search function
    const search = useCallback(async (e) => {
        e.preventDefault();
        if (!user?.user_id) return;
        setSearchLoading(true);
        setCurrentPage(1);
        try {
            const data = await searchProducts(query, user.user_id);
            let products = Array.isArray(data) ? data : (data.products || []);
            setResults(products);
            if (data.intent) {
                const { suggested_category, suggested_sort, suggested_min_price, suggested_max_price, detected } = data.intent;
                const newCategory = (suggested_category && products.some(p => p.category === suggested_category)) ? suggested_category : '';
                const newSort = suggested_sort || '';
                const newMinPrice = suggested_min_price ? String(suggested_min_price) : '';
                const newMaxPrice = suggested_max_price ? String(suggested_max_price) : '';
                setCategoryFilter(newCategory);
                setSortBy(newSort);
                setMinPrice(newMinPrice);
                setMaxPrice(newMaxPrice);
                const actionableIntents = (detected || []).filter(i => i !== 'category');
                if (actionableIntents.length > 0) {
                    const intentMsg = actionableIntents.map(i => i.replace('_', ' ')).join(', ');
                    showToast(`Applied: ${intentMsg}`, 'success');
                }
            }
        } catch {
            showToast('Network error. Please check your connection.');
        } finally {
            setSearchLoading(false);
        }
    }, [query, user?.user_id, showToast]);

    // Apply filters and sorting to results
    useEffect(() => {
        if (!results) return;
        let filtered = [...results];

        // Category filter
        if (categoryFilter) {
            filtered = filtered.filter(p => p.category === categoryFilter);
        }

        // Price range filter
        if (minPrice) {
            filtered = filtered.filter(p => p.price >= parseFloat(minPrice));
        }
        if (maxPrice) {
            filtered = filtered.filter(p => p.price <= parseFloat(maxPrice));
        }

        // Sorting
        if (sortBy === 'price_asc') {
            filtered.sort((a, b) => a.price - b.price);
        } else if (sortBy === 'price_desc') {
            filtered.sort((a, b) => b.price - a.price);
        } else if (sortBy === 'rating') {
            filtered.sort((a, b) => b.rating - a.rating);
        } else if (sortBy === 'popularity') {
            filtered.sort((a, b) => b.popularity - a.popularity);
        }

        setFilteredResults(filtered);
        setCurrentPage(1);
    }, [results, categoryFilter, minPrice, maxPrice, sortBy]);

    // Fetch recommendations when user changes
    useEffect(() => {
        if (!user) return;
        setRecsLoading(true);
        fetchRecommendations(user.user_id)
            .then((d) => {
                setRecent(d.recent || []);
                setRecommended(d.similar || []);
            })
            .catch(() => {
                setRecent([]);
                setRecommended([]);
            })
            .finally(() => setRecsLoading(false));
    }, [user]);

    // Pagination calculations
    const totalPages = useMemo(() => Math.ceil(filteredResults.length / ITEMS_PER_PAGE), [filteredResults.length]);
    const paginatedResults = useMemo(() =>
        filteredResults.slice(
            (currentPage - 1) * ITEMS_PER_PAGE,
            currentPage * ITEMS_PER_PAGE
        ), [filteredResults, currentPage]
    );

    return {
        // Search state
        query,
        setQuery,
        results,
        filteredResults,
        recent,
        recommended,
        searchLoading,
        recsLoading,

        // Filter state
        categoryFilter,
        setCategoryFilter,
        minPrice,
        setMinPrice,
        maxPrice,
        setMaxPrice,
        sortBy,
        setSortBy,
        currentPage,
        setCurrentPage,

        // Constants
        ITEMS_PER_PAGE,
        categories,

        // Computed values
        totalPages,
        paginatedResults,

        // Functions
        search
    };
}