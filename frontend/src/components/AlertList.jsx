import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  CircularProgress,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Snackbar,
  Alert as MuiAlert,
  Stack,
  IconButton,
} from '@mui/material';
import {
  Warning, Error, Info, ReportProblem, CheckCircle, AutoFixHigh, ChevronRight, Email as EmailIcon
} from '@mui/icons-material';

const severityMap = {
  0: { label: 'Not classified', icon: <Info />, color: 'default' },
  1: { label: 'Information', icon: <Info color="info" />, color: 'info' },
  2: { label: 'Warning', icon: <Warning color="warning" />, color: 'warning' },
  3: { label: 'Average', icon: <ReportProblem sx={{ color: 'orange' }} />, color: 'secondary' },
  4: { label: 'High', icon: <Error color="error" />, color: 'error' },
  5: { label: 'Disaster', icon: <Error color="error" />, color: 'error' },
};

const AlertList = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [remediating, setRemediating] = useState(false);
  const [remediationResult, setRemediationResult] = useState(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
        const response = await axios.get(`${apiBase}/api/alerts`);
        setAlerts(response.data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyzeClick = async (alert) => {
    if (!alert.id) {
      console.error("Analysis failed: Alert ID is missing.");
      setAnalysis({ 
        error: true,
        analysis: "Failed to get AI analysis.", 
        recommendation: "Alert ID is missing. Cannot proceed."
      });
      setModalOpen(true);
      return;
    }
    setSelectedAlert(alert);
    setModalOpen(true);
    setAnalyzing(true);
    setAnalysis(null);
    try {
      const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
      const response = await axios.get(`${apiBase}/api/alerts/${alert.id}/analyze`);
      setAnalysis(response.data);
    } catch (err) {
      setAnalysis({
        analysis: 'Failed to get AI analysis.',
        recommendations: [err.response?.data?.detail || err.message],
        error: true,
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedAlert(null);
    setAnalysis(null);
    setRemediationResult(null);
  };

  if (loading && alerts.length === 0) {
    return <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>;
  }

  if (error) {
    return <Typography color="error" p={2}>Failed to load alerts: {error}</Typography>;
  }

  return (
    <>
      <Typography variant="h6" gutterBottom>
        System Alerts
      </Typography>
      <List dense>
        {alerts.length === 0 ? (
          <ListItem>
            <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
            <ListItemText primary="No active alerts." />
          </ListItem>
        ) : (
          alerts.map((alert) => (
            <ListItem
              key={alert.triggerid}
              secondaryAction={
                <Stack direction="column" spacing={0.5} alignItems="flex-end" sx={{ pr: 1 }}>
                  <IconButton color="primary" size="small" onClick={() => handleSendEmail(alert)} title="Send Email">
                    <EmailIcon />
                  </IconButton>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AutoFixHigh />}
                    onClick={() => handleAnalyzeClick(alert)}
>
                    Analyze
                  </Button>
                </Stack>
              }
            >
              <ListItemIcon sx={{ minWidth: 'auto', mr: 2, display: 'flex', alignItems: 'center' }}>
                  <Chip label={severityMap[alert.severity]?.label || 'Unknown'} color={severityMap[alert.severity]?.color || 'default'} size="small" />
                </ListItemIcon>
              <ListItemText primary={alert.name} secondary={`Host: ${alert.host}`} sx={{ pr: 12, flexGrow: 1 }} />
            </ListItem>
          ))
        )}
      </List>

      <Dialog open={modalOpen} onClose={handleCloseModal} fullWidth maxWidth="md">
        <DialogTitle>AI Analysis: {selectedAlert?.name}</DialogTitle>
        <DialogContent dividers>
          {analyzing ? (
            <Box display="flex" justifyContent="center" alignItems="center" sx={{ p: 4 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Analyzing with Gemini...</Typography>
            </Box>
          ) : analysis ? (
            <Box>
              <Typography variant="h6" gutterBottom>Analysis</Typography>
              <Typography paragraph sx={{ fontStyle: 'italic', color: 'text.secondary' }}>{analysis.analysis}</Typography>
              <Divider sx={{ my: 2 }} />

              {analysis.root_causes && (
                <>
                  <Typography variant="h6" gutterBottom>Potential Root Causes</Typography>
                  <List dense>
                    {analysis.root_causes.map((cause, i) => (
                      <ListItem key={i}>
                        <ListItemIcon sx={{minWidth: 32}}><ChevronRight /></ListItemIcon>
                        <ListItemText primary={cause} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
              <Divider sx={{ my: 2 }} />
              
              {analysis.recommendations && (
                <>
                  <Typography variant="h6" gutterBottom>Recommended Actions</Typography>
                  <List dense>
                    {analysis.recommendations.map((rec, i) => (
                      <ListItem key={i}>
                        <ListItemIcon sx={{minWidth: 32}}><ChevronRight /></ListItemIcon>
                        <ListItemText primary={rec} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
              {remediationResult && (
                <MuiAlert severity={remediationResult.success ? "success" : "error"} sx={{ mt: 2 }}>
                  {remediationResult.success ? `Remediation successful: ${JSON.stringify(remediationResult.data)}` : `Remediation failed: ${remediationResult.message}`}
                </MuiAlert>
              )}
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          {analysis && analysis.remediation && !remediationResult && (
            <Button 
              onClick={() => handleRemediateClick(analysis.remediation)} 
              color="primary"
              variant="contained"
              disabled={remediating}
              startIcon={remediating ? <CircularProgress size={20} /> : <AutoFixHigh />}
            >
              Run Remediation
            </Button>
          )}
          <Button onClick={handleCloseModal}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

  const handleSendEmail = async (alert) => {
    try {
      const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
      await axios.post(`${apiBase}/api/alerts/${alert.id}/email`);
      setRemediationResult({ success: true, data: { status: 'email_sent' } });
    } catch (err) {
      setRemediationResult({ success: false, message: err.response?.data?.detail || err.message });
    }
  };

  const handleRemediateClick = async (remediation) => {
    if (!selectedAlert || !remediation) return;

    setRemediating(true);
    setRemediationResult(null);
    try {
      const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
      const response = await axios.post(`${apiBase}/api/remediate`, {
        script_id: remediation.script_id,
        host_id: selectedAlert.hostid,
      });
      setRemediationResult({ success: true, data: response.data });
    } catch (err) {
      setRemediationResult({ success: false, message: err.response?.data?.detail || err.message });
    } finally {
      setRemediating(false);
    }
  };

export default AlertList;
