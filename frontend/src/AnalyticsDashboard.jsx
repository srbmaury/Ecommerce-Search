import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { fetchAnalytics } from './api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28BFE', '#FF6F91', '#00B8A9', '#FFD166'];

export default function AnalyticsDashboard() {
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

  // Prepare data for charts
  const summaryArr = Object.entries(summary).map(([group, s]) => ({ name: `Group ${group}`, ...s }));
  const clusterArr = Object.entries(clusterCounts).map(([cluster, count]) => ({ name: `Cluster ${cluster}`, value: count }));
  const queriesArr = Object.entries(topQueries).map(([query, count]) => ({ name: query, value: count }));

  if (loading) return <div style={{ textAlign: 'center', padding: 40 }}>Loading analytics...</div>;
  if (error) return <div style={{ color: 'red', textAlign: 'center', padding: 40 }}>{error}</div>;

  const chartCardStyle = {
    flex: '1 1 300px',
    maxWidth: '100%',
    minWidth: '280px',
    height: 300,
    background: '#fff',
    borderRadius: 12,
    boxShadow: '0 2px 8px #eee',
    padding: 16,
    boxSizing: 'border-box'
  };

  return (
    <div style={{ padding: '16px 8px' }}>
      <h2 style={{ textAlign: 'center', marginBottom: 24, fontSize: '1.5rem' }}>📊 Analytics Dashboard</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center' }}>
        {/* Group Metrics Line Chart */}
        <div style={chartCardStyle}>
          <h4 style={{ textAlign: 'center', fontSize: '0.9rem', margin: '0 0 8px 0' }}>Searches, Clicks, Add to Cart by Group</h4>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={summaryArr}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="searches" stroke="#8884d8" />
              <Line type="monotone" dataKey="clicks" stroke="#00C49F" />
              <Line type="monotone" dataKey="add_to_cart" stroke="#FFBB28" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {/* CTR & Conversion Bar Chart */}
        <div style={chartCardStyle}>
          <h4 style={{ textAlign: 'center', fontSize: '0.9rem', margin: '0 0 8px 0' }}>CTR & Conversion by Group</h4>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={summaryArr}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="CTR" fill="#A28BFE" />
              <Bar dataKey="Conversion" fill="#FF6F91" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {/* Cluster Pie Chart */}
        <div style={chartCardStyle}>
          <h4 style={{ textAlign: 'center', fontSize: '0.9rem', margin: '0 0 8px 0' }}>User Clusters</h4>
          <ResponsiveContainer width="100%" height="85%">
            <PieChart>
              <Pie data={clusterArr} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} fill="#8884d8" label={{ fontSize: 11 }}>
                {clusterArr.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {/* Top Queries Bar Chart */}
        <div style={chartCardStyle}>
          <h4 style={{ textAlign: 'center', fontSize: '0.9rem', margin: '0 0 8px 0' }}>Top Search Queries</h4>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={queriesArr} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="name" type="category" width={80} interval={0} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#00B8A9" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
