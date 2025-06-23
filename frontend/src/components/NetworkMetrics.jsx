import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  CircularProgress,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

const mockMetrics = [
  { time: '00:00', cpu: 25, memory: 45, networkIn: 400, networkOut: 200 },
  { time: '04:00', cpu: 30, memory: 50, networkIn: 350, networkOut: 250 },
  { time: '08:00', cpu: 50, memory: 60, networkIn: 800, networkOut: 500 },
  { time: '12:00', cpu: 65, memory: 70, networkIn: 1200, networkOut: 800 },
  { time: '16:00', cpu: 45, memory: 55, networkIn: 600, networkOut: 400 },
  { time: '20:00', cpu: 30, memory: 45, networkIn: 500, networkOut: 300 },
  { time: '23:59', cpu: 25, memory: 40, networkIn: 400, networkOut: 200 },
];

const NetworkMetrics = ({ hostId }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');
  const [metrics, setMetrics] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null); // Reset error on new fetch

    const formatTimestamp = (timestamp, range) => {
      const date = new Date(timestamp);
      if (range === '24h') {
        // Returns HH:mm format
        return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
      }
      // Returns "Mon Day" format for 7d and 30d
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const fetchMetrics = async () => {
      if (!hostId) return;
      try {
        const hours = timeRange === '24h' ? 24 : timeRange === '7d' ? 24 * 7 : 24 * 30;
        const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
        const response = await axios.get(`${apiBase}/api/metrics/${hostId}?hours=${hours}`);
        
        const bytesToGB = (bytes) => (bytes / (1024 ** 3)).toFixed(2);
        
        const data = response.data.map((r) => {
          const totalGB = r.memory_total ? parseFloat(bytesToGB(r.memory_total)) : null;
          return {
            time: formatTimestamp(r.timestamp, timeRange),
            cpu: r.cpu_usage,
            memoryBytes: r.memory_usage,
            memoryGB: parseFloat(bytesToGB(r.memory_usage)),
            memoryTotalGB: totalGB,
            networkIn: parseFloat((r.network_in / 1024).toFixed(2)),
            networkOut: parseFloat((r.network_out / 1024).toFixed(2)),
          };
        });
        setMetrics(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching metrics:', error);
        setLoading(false);
      }
    };

    setLoading(true);
    fetchMetrics();
  }, [hostId, timeRange]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleTimeRangeChange = (newRange) => {
    setTimeRange(newRange);
  };

  const renderChart = () => {
    if (loading) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={300}>
          <CircularProgress />
        </Box>
      );
    }

    if (metrics.length === 0) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={300}>
          <Typography color="textSecondary">No metrics available for this host.</Typography>
        </Box>
      );
    }

    const memoryCap = metrics.find(m => m.memoryTotalGB !== null)?.memoryTotalGB;

    return (
      <Box sx={{ width: '100%', height: 400, mt: 2 }}>
        <Tabs 
          value={timeRange} 
          onChange={(e, value) => handleTimeRangeChange(value)}
          sx={{ mb: 2 }}
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab label="24h" value="24h" />
          <Tab label="7d" value="7d" />
          <Tab label="30d" value="30d" />
        </Tabs>

        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
          sx={{ mb: 2 }}
        >
          <Tab label="CPU" />
          <Tab label="Memory" />
          <Tab label="Network" />
        </Tabs>

        {tabValue === 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis 
                label={{ value: 'Utilization (%)', angle: -90, position: 'insideLeft' }}
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="cpu" name="CPU Utilization (%)" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        )}

        {tabValue === 1 && (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis 
                label={{ value: 'Available (GB)', angle: -90, position: 'insideLeft' }}
                domain={[0, memoryCap || 16]}
                tickFormatter={(value) => `${value} GB`}
              />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="memoryGB" name="Available Memory (GB)" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        )}

        {tabValue === 2 && (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis
                label={{ value: 'KB/s', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => `${value} KB/s`}
              />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="networkIn" name="Network In" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Area type="monotone" dataKey="networkOut" name="Network Out" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Box>
    );
  };

  return (
    <Box>
      <Typography component="h2" variant="h6" color="primary" gutterBottom>
        Performance Metrics
      </Typography>
      {renderChart()}
      
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="CPU Utilization" 
            value={metrics.length > 0 ? `${metrics[metrics.length - 1].cpu}%` : 'N/A'} 
            trend={metrics.length > 1 ? metrics[metrics.length - 1].cpu - metrics[metrics.length - 2].cpu : 0}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="Available Memory" 
            value={metrics.length > 0 ? `${metrics[metrics.length - 1].memoryGB} GB` : 'N/A'} 
            trend={metrics.length > 1 ? metrics[metrics.length - 1].memoryGB - metrics[metrics.length - 2].memoryGB : 0}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="Network In" 
            value={metrics.length > 0 ? `${metrics[metrics.length - 1].networkIn} KB/s` : 'N/A'} 
            trend={metrics.length > 1 ? metrics[metrics.length - 1].networkIn - metrics[metrics.length - 2].networkIn : 0}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="Network Out"
            value={metrics.length > 0 ? `${metrics[metrics.length - 1].networkOut} KB/s` : 'N/A'}
            trend={metrics.length > 1 ? metrics[metrics.length - 1].networkOut - metrics[metrics.length - 2].networkOut : 0}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

const MetricCard = ({ title, value, trend }) => {
  const isPositive = trend >= 0;
  const trendText = trend !== 0 ? `${isPositive ? '+' : ''}${trend.toFixed(1)}` : '0.0';
  
  return (
    <Card>
      <CardContent>
        <Typography color="textSecondary" gutterBottom>
          {title}
        </Typography>
        <Typography variant="h5" component="div">
          {value}
        </Typography>
        <Typography 
          variant="body2" 
          color={trend === 0 ? 'textSecondary' : isPositive ? 'error' : 'success'}
          sx={{ mt: 1 }}
        >
          {trendText} {trend !== 0 && (isPositive ? '↑' : '↓')}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default NetworkMetrics;
