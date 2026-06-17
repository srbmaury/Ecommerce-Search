import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

const ChartCard = ({ title, children }) => (
    <div className="chart-card">
        <h4 className="chart-card-title">{title}</h4>
        <ResponsiveContainer width="100%" height={220}>
            {children}
        </ResponsiveContainer>
    </div>
);

export const GroupMetricsChart = ({ data }) => (
    <ChartCard title="Searches · Clicks · Add to Cart by Group">
        <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="searches" stroke="#6366f1" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="clicks" stroke="#10b981" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="add_to_cart" stroke="#f59e0b" strokeWidth={2} dot={false} />
        </LineChart>
    </ChartCard>
);

export const ConversionChart = ({ data }) => (
    <ChartCard title="CTR & Conversion by Group">
        <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="CTR" fill="#6366f1" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Conversion" fill="#10b981" radius={[4, 4, 0, 0]} />
        </BarChart>
    </ChartCard>
);

export const ClusterChart = ({ data }) => (
    <ChartCard title="User Clusters">
        <PieChart>
            <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={{ fontSize: 12 }}
            >
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
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis dataKey="name" type="category" width={80} interval={0} tick={{ fontSize: 10 }} />
            <Tooltip />
            <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
        </BarChart>
    </ChartCard>
);
