import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  Box,
} from '@mui/material';
import { green, red, orange } from '@mui/material/colors';
import CloudIcon from '@mui/icons-material/Cloud';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';

const statusColors = {
  up: green[500],
  down: red[500],
  warning: orange[500],
};

const statusIcons = {
  up: <CloudIcon style={{ color: statusColors.up }} />,
  down: <ErrorIcon style={{ color: statusColors.down }} />,
  warning: <WarningIcon style={{ color: statusColors.warning }} />,
};

const HostStatus = ({ hosts }) => {
  return (
    <Box>
      <Typography component="h2" variant="h6" color="primary" gutterBottom>
        Host Status
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Host Name</TableCell>
              <TableCell>Last Check</TableCell>
              <TableCell>Issues</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {hosts.map((host) => (
              <TableRow key={host.host_id}>
                <TableCell>
                  <Chip 
                    icon={statusIcons[host.status] || statusIcons.warning}
                    label={host.status.toUpperCase()}
                    variant="outlined"
                    style={{
                      borderColor: statusColors[host.status] || statusColors.warning,
                      color: statusColors[host.status] || statusColors.warning,
                    }}
                  />
                </TableCell>
                <TableCell>{host.name}</TableCell>
                <TableCell>
                  {new Date(host.last_check).toLocaleString()}
                </TableCell>
                <TableCell>
                  {host.issues.length > 0 ? (
                    <Chip 
                      label={`${host.issues.length} issue(s)`} 
                      color="error" 
                      size="small" 
                    />
                  ) : (
                    'No issues'
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default HostStatus;
