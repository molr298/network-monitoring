import React, { useState, useEffect } from 'react';
import { 
  Container, 
  CssBaseline, 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { teal, deepOrange } from '@mui/material/colors';
import SettingsIcon from '@mui/icons-material/Settings';
import HostStatus from './components/HostStatus';
import NetworkMetrics from './components/NetworkMetrics';
import AlertList from './components/AlertList';
import AnomalyList from './components/AnomalyList';
import EmailSettings from './components/EmailSettings';
import axios from 'axios';

// Create a theme instance
const theme = createTheme({
  palette: {
    primary: teal,
    secondary: deepOrange,
    mode: 'light',
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  const [hosts, setHosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedHostId, setSelectedHostId] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    const fetchHosts = async () => {
      try {
        const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
        const [keysResp, statusResp] = await Promise.all([
          axios.get(`${apiBase}/api/hosts/metrics-keys`),
          axios.get(`${apiBase}/api/hosts/status`),
        ]);

        const statusMap = Object.fromEntries(
          statusResp.data.map((s) => [s.host_id, s])
        );

        const enriched = keysResp.data.map((h) => {
          const st = statusMap[h.host_id] || {};
          return {
            host_id: h.host_id,
            name: st.name || h.host_id,
            status: st.status || 'unknown',
            last_check: st.last_check || new Date().toISOString(),
            issues: st.issues || [],
            keys: h.keys,
          };
        });
        setHosts(enriched);
        if (enriched.length > 0) {
          setSelectedHostId(enriched[0].host_id);
        }
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchHosts();
  }, []);

  const handleHostChange = (event) => {
    setSelectedHostId(event.target.value);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Network Monitoring Dashboard
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            <IconButton color="inherit" onClick={() => setSettingsOpen(true)}>
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        <EmailSettings open={settingsOpen} onClose={() => setSettingsOpen(false)} />
        
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Box sx={{ mb: 3, maxWidth: 300 }}>
            <FormControl fullWidth>
              <InputLabel id="host-select-label">Select Host</InputLabel>
              <Select
                labelId="host-select-label"
                id="host-select"
                value={selectedHostId}
                label="Select Host"
                onChange={handleHostChange}
              >
                {hosts.map((host) => (
                  <MenuItem key={host.host_id} value={host.host_id}>
                    {host.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <Grid container spacing={3}>
            {/* Host Status */}
            <Grid item xs={12}>
              <HostStatus hosts={hosts} />
            </Grid>
            <Grid item xs={12}>
              <AnomalyList />
            </Grid>

            {/* Alerts */}
            <Grid item xs={12} md={4} lg={3}>
              <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
                <AlertList />
              </Paper>
            </Grid>

            {/* Network Metrics */}
            <Grid item xs={12} md={8} lg={9}>
              <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
                <NetworkMetrics hostId={selectedHostId} />
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
