import React from 'react';
import { useAnalytics } from './useAnalytics';
import { GroupMetricsChart, ConversionChart, ClusterChart, TopQueriesChart } from './AnalyticsCharts';

export default function AnalyticsDashboard() {
    const { loading, error, chartData } = useAnalytics();

    if (loading) return <div style={{ textAlign: 'center', padding: 40 }}>Loading analytics...</div>;
    if (error) return <div style={{ color: 'red', textAlign: 'center', padding: 40 }}>{error}</div>;

    const { summaryArr, clusterArr, queriesArr } = chartData;

    return (
        <div style={{ padding: '16px 8px' }}>
            <h2 style={{ textAlign: 'center', marginBottom: 24, fontSize: '1.5rem' }}>📊 Analytics Dashboard</h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center' }}>
                <GroupMetricsChart data={summaryArr} />
                <ConversionChart data={summaryArr} />
                <ClusterChart data={clusterArr} />
                <TopQueriesChart data={queriesArr} />
            </div>
        </div>
    );
}
