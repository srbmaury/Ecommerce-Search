import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { searchProducts, fetchRecommendations } from './api';
import { useApiToast } from './useApiToast';

export function useSearch(user, showToast) {
    const { toastApiError } = useApiToast(showToast);

    // Search state
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null); // IMPORTANT: null vs []
    const [filteredResults, setFilteredResults] = useState([]);
    const [recent, setRecent] = useState([]);
    const [recommended, setRecommended] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [recsLoading, setRecsLoading] = useState(!!user);
    const [appliedIntent, setAppliedIntent] = useState(null);

    // Filter & pagination state
    const [categoryFilter, setCategoryFilter] = useState('');
    const [minPrice, setMinPrice] = useState('');
    const [maxPrice, setMaxPrice] = useState('');
    const [sortBy, setSortBy] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [nextCursor, setNextCursor] = useState(null);
    const [hasMoreResults, setHasMoreResults] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);

    // Abort controller for cancelling in-flight searches
    const searchAbortRef = useRef(null);

    const ITEMS_PER_PAGE = 12;
    const SEARCH_PAGE_SIZE = 60;
    const categories = ['Audio', 'Electronics', 'Computers', 'Photography', 'Accessories', 'Gaming', 'Networking', 'Smart Home', 'Storage'];

    const loadSearchPage = useCallback(async (cursor, append = false, signal = undefined) => {
        const data = await searchProducts(query, user.user_id, {
            cursor,
            limit: SEARCH_PAGE_SIZE,
            signal,
        });

        const products = Array.isArray(data) ? data : (data.products || []);

        if (append) {
            setResults(prev => {
                const existing = Array.isArray(prev) ? prev : [];
                const existingIds = new Set(existing.map(p => p.product_id));
                const merged = [...existing];
                products.forEach((product) => {
                    if (!existingIds.has(product.product_id)) {
                        merged.push(product);
                    }
                });
                return merged;
            });
        } else {
            setResults(products);
        }

        const pagination = data.pagination || {};
        setNextCursor(pagination.next_cursor ?? null);
        setHasMoreResults(Boolean(pagination.has_more));

        return data;
    }, [query, user?.user_id]);

    // Search function
    const search = useCallback(async (e) => {
        e.preventDefault();
        if (!user?.user_id) return;
        // Normalize: trim, collapse whitespace, cap at 256 chars
        const normalized = query.trim().replace(/\s+/g, ' ').slice(0, 256);
        if (!normalized) return;
        if (normalized !== query) setQuery(normalized);

        // Cancel any previous in-flight search to prevent stale results
        if (searchAbortRef.current) {
            searchAbortRef.current.abort();
        }
        searchAbortRef.current = new AbortController();
        const { signal } = searchAbortRef.current;

        setSearchLoading(true);
        setCurrentPage(1);
        setNextCursor(null);
        setHasMoreResults(false);
        try {
            const data = await loadSearchPage(0, false, signal);
            let products = Array.isArray(data) ? data : (data.products || []);
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
                // Build an appliedIntent summary for inline display below the search bar
                const chips = [];
                if (newCategory) chips.push({ label: newCategory, kind: 'category' });
                if (newSort === 'price_asc') chips.push({ label: 'Price: low to high', kind: 'sort' });
                if (newSort === 'price_desc') chips.push({ label: 'Price: high to low', kind: 'sort' });
                if (newSort === 'rating') chips.push({ label: 'Top rated', kind: 'sort' });
                if (suggested_max_price) chips.push({ label: `Under $${suggested_max_price}`, kind: 'price' });
                if (suggested_min_price) chips.push({ label: `Over $${suggested_min_price}`, kind: 'price' });
                setAppliedIntent(chips.length > 0 ? chips : null);
            } else {
                setAppliedIntent(null);
            }
        } catch (error) {
            if (error.name === 'AbortError') return; // Superseded by a newer search
            toastApiError(error);
        } finally {
            setSearchLoading(false);
        }
    }, [user?.user_id, showToast, loadSearchPage, toastApiError, query]);

    useEffect(() => {
        if (!results || results.length === 0) return;
        if (!hasMoreResults || nextCursor === null || searchLoading || isLoadingMore) return;

        const requiredCount = currentPage * ITEMS_PER_PAGE;
        if (filteredResults.length >= requiredCount) return;

        let cancelled = false;

        const loadMore = async () => {
            setIsLoadingMore(true);
            try {
                await loadSearchPage(nextCursor, true);
            } catch (error) {
                if (!cancelled) {
                    toastApiError(error, 'Failed to load more results');
                }
            } finally {
                if (!cancelled) {
                    setIsLoadingMore(false);
                }
            }
        };

        loadMore();

        return () => {
            cancelled = true;
        };
    }, [
        currentPage,
        results,
        filteredResults,
        hasMoreResults,
        nextCursor,
        searchLoading,
        isLoadingMore,
        loadSearchPage,
        toastApiError,
    ]);

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
            .catch((error) => {
                toastApiError(error, 'Failed to load recommendations');
                setRecent([]);
                setRecommended([]);
            })
            .finally(() => setRecsLoading(false));
    }, [user, toastApiError]);

    // Pagination calculations
    const totalPages = useMemo(() => {
        const loadedPages = Math.ceil(filteredResults.length / ITEMS_PER_PAGE);
        const minimumPages = Math.max(1, loadedPages);
        return hasMoreResults ? minimumPages + 1 : minimumPages;
    }, [filteredResults.length, hasMoreResults]);
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
        hasMoreResults,
        isLoadingMore,

        // Functions
        search,
        appliedIntent,
    };
}
