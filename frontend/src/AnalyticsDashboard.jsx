import React from 'react';
import { useAnalytics } from './useAnalytics';
import { GroupMetricsChart, ConversionChart, ClusterChart, TopQueriesChart } from './AnalyticsCharts';

export default function AnalyticsDashboard({ user }) {
    const { loading, error, chartData } = useAnalytics(user?.token);

    if (loading) return <div className="loading">Loading analytics...</div>;
    if (error) return <div className="analytics-error">{error}</div>;

    const { summaryArr, clusterArr, queriesArr } = chartData;

    return (
        <div className="analytics-dashboard">
            <h2 className="analytics-dashboard-title">📊 Analytics Dashboard</h2>
            <div className="analytics-chart-grid">
                <GroupMetricsChart data={summaryArr} />
                <ConversionChart data={summaryArr} />
                <ClusterChart data={clusterArr} />
                <TopQueriesChart data={queriesArr} />
            </div>
        </div>
    );
}
