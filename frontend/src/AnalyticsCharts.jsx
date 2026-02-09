import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28BFE', '#FF6F91', '#00B8A9', '#FFD166'];

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

const ChartCard = ({ title, children }) => (
    <div style={chartCardStyle}>
        <h4 style={{ textAlign: 'center', fontSize: '0.9rem', margin: '0 0 8px 0' }}>
            {title}
        </h4>
        <ResponsiveContainer width="100%" height="85%">
            {children}
        </ResponsiveContainer>
    </div>
);

export const GroupMetricsChart = ({ data }) => (
    <ChartCard title="Searches, Clicks, Add to Cart by Group">
        <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="searches" stroke="#8884d8" />
            <Line type="monotone" dataKey="clicks" stroke="#00C49F" />
            <Line type="monotone" dataKey="add_to_cart" stroke="#FFBB28" />
        </LineChart>
    </ChartCard>
);

export const ConversionChart = ({ data }) => (
    <ChartCard title="CTR & Conversion by Group">
        <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="CTR" fill="#A28BFE" />
            <Bar dataKey="Conversion" fill="#FF6F91" />
        </BarChart>
    </ChartCard>
);

export const ClusterChart = ({ data }) => (
    <ChartCard title="User Clusters">
        <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} fill="#8884d8" label={{ fontSize: 11 }}>
                {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
            </Pie>
            <Tooltip />
        </PieChart>
    </ChartCard>
);

export const TopQueriesChart = ({ data }) => (
    <ChartCard title="Top Search Queries">
        <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis dataKey="name" type="category" width={80} interval={0} tick={{ fontSize: 10 }} />
            <Tooltip />
            <Bar dataKey="value" fill="#00B8A9" />
        </BarChart>
    </ChartCard>
);