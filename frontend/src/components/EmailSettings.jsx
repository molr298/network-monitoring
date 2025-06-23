import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Button,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Snackbar,
  Alert,
} from '@mui/material';

const EmailSettings = ({ open, onClose }) => {
  const [settings, setSettings] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    recipients: '',
  });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    if (open) {
      axios.get('/api/config/email')
        .then(response => {
          setSettings(response.data);
        })
        .catch(error => {
          console.error('Failed to fetch email settings:', error);
          setSnackbar({ open: true, message: 'Failed to load settings.', severity: 'error' });
        });
    }
  }, [open]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setSettings(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    axios.post('/api/config/email', settings)
      .then(response => {
        setSnackbar({ open: true, message: response.data.message, severity: 'success' });
        onClose();
      })
      .catch(error => {
        console.error('Failed to save email settings:', error);
        setSnackbar({ open: true, message: 'Failed to save settings.', severity: 'error' });
      });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleTestEmail = () => {
    // First, save the current settings to ensure the test uses the latest data
    axios.post('/api/config/email', settings)
      .then(() => {
        // Then, send the test email
        return axios.post('/api/config/email/test');
      })
      .then(response => {
        setSnackbar({ open: true, message: response.data.message, severity: 'success' });
      })
      .catch(error => {
        const errorMessage = error.response?.data?.detail || 'Failed to send test email.';
        setSnackbar({ open: true, message: errorMessage, severity: 'error' });
      });
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
        <DialogTitle>Email Notification Settings</DialogTitle>
        <DialogContent>
          <TextField
            name="smtp_host"
            label="SMTP Host"
            value={settings.smtp_host}
            onChange={handleChange}
            fullWidth
            margin="dense"
          />
          <TextField
            name="smtp_port"
            label="SMTP Port"
            type="number"
            value={settings.smtp_port}
            onChange={handleChange}
            fullWidth
            margin="dense"
          />
          <TextField
            name="smtp_user"
            label="SMTP Username"
            value={settings.smtp_user}
            onChange={handleChange}
            fullWidth
            margin="dense"
          />
          <TextField
            name="smtp_password"
            label="SMTP Password"
            type="password"
            value={settings.smtp_password}
            onChange={handleChange}
            fullWidth
            margin="dense"
          />
          <TextField
            name="recipients"
            label="Recipients (comma-separated)"
            value={settings.recipients}
            onChange={handleChange}
            fullWidth
            margin="dense"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleTestEmail} sx={{ mr: 'auto' }}>Send Test Email</Button>
          <Button onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default EmailSettings;
