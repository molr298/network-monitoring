import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  CircularProgress,
  Box,
} from '@mui/material';
import { format } from 'date-fns';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AnomalyList = () => {
  const [anomalies, setAnomalies] = useState([]);
  const [hostNames, setHostNames] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
        const [anomalyRes, hostsRes] = await Promise.all([
          axios.get(`${apiBase}/api/anomalies`),
          axios.get(`${apiBase}/api/hosts/status`),
        ]);
        setAnomalies(anomalyRes.data);
        const mapping = {};
        hostsRes.data.forEach((h) => {
          mapping[h.host_id] = h.name || h.host_id;
        });
        setHostNames(mapping);
      } catch (err) {
        setError('Failed to fetch anomalies.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Detected Anomalies
      </Typography>
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Host</TableCell>
              <TableCell>Metric</TableCell>
              <TableCell>Anomalous Value</TableCell>
              <TableCell>Reason</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {anomalies.length > 0 ? (
              anomalies.map((anomaly) => (
                <TableRow key={anomaly.id}>
                  <TableCell>{format(new Date(anomaly.timestamp), 'yyyy-MM-dd HH:mm:ss')}</TableCell>
                  <TableCell>{hostNames[anomaly.host_id] || anomaly.host_id}</TableCell>
                  <TableCell>{anomaly.item_key}</TableCell>
                  <TableCell>{anomaly.value.toFixed(2)}</TableCell>
                  <TableCell>{anomaly.reason}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No anomalies detected recently.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default AnomalyList;
