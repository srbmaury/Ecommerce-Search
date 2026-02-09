import { useState, useEffect, useMemo } from 'react';
import { fetchAnalytics } from './api';

export function useAnalytics() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [summary, setSummary] = useState({});
    const [clusterCounts, setClusterCounts] = useState({});
    const [topQueries, setTopQueries] = useState({});

    useEffect(() => {
        fetchAnalytics()
            .then(data => {
                if (data.error) throw new Error(data.error);
                setSummary(data.summary || {});
                setClusterCounts(data.cluster_counts || {});
                setTopQueries(data.top_queries || {});
                setLoading(false);
            })
            .catch(e => {
                setError(e.message);
                setLoading(false);
            });
    }, []);

    // Memoize data transformations for charts
    const chartData = useMemo(() => ({
        summaryArr: Object.entries(summary).map(([group, s]) => ({ name: `Group ${group}`, ...s })),
        clusterArr: Object.entries(clusterCounts).map(([cluster, count]) => ({ name: `Cluster ${cluster}`, value: count })),
        queriesArr: Object.entries(topQueries).map(([query, count]) => ({ name: query, value: count }))
    }), [summary, clusterCounts, topQueries]);

    return {
        loading,
        error,
        summary,
        clusterCounts,
        topQueries,
        chartData
    };
}