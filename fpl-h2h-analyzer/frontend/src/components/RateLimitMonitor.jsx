import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Tooltip,
  IconButton,
  Divider
} from '@mui/material';
import {
  Speed as SpeedIcon,
  CloudQueue as QueueIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const MetricCard = styled(Card)(({ theme }) => ({
  height: '100%',
  background: theme.palette.mode === 'dark' 
    ? 'linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%)'
    : 'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)',
  '&:hover': {
    transform: 'translateY(-2px)',
    transition: 'transform 0.2s ease-in-out',
  }
}));

const TokenBar = styled(LinearProgress)(({ theme }) => ({
  height: 10,
  borderRadius: 5,
  '& .MuiLinearProgress-bar': {
    borderRadius: 5,
    background: 'linear-gradient(90deg, #4caf50 0%, #8bc34a 100%)',
  }
}));

function RateLimitMonitor() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/rate-limit/metrics');
      if (!response.ok) {
        throw new Error('Failed to fetch rate limit metrics');
      }
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching rate limit metrics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    
    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, 2000); // Update every 2 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getHealthColor = (metrics) => {
    if (!metrics) return 'default';
    
    if (metrics.consecutive_429s > 3) return 'error';
    if (metrics.rate_limited_requests > metrics.successful_requests * 0.1) return 'warning';
    if (metrics.success_rate < 0.9) return 'warning';
    return 'success';
  };

  const getHealthIcon = (metrics) => {
    const color = getHealthColor(metrics);
    switch (color) {
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'success':
        return <SuccessIcon color="success" />;
      default:
        return <SpeedIcon />;
    }
  };

  if (loading && !metrics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !metrics) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h5">Rate Limit Monitor</Typography>
          {metrics && (
            <Chip
              icon={getHealthIcon(metrics)}
              label={getHealthColor(metrics).toUpperCase()}
              color={getHealthColor(metrics)}
              size="small"
            />
          )}
        </Box>
        <Box>
          <Tooltip title={autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}>
            <IconButton 
              onClick={() => setAutoRefresh(!autoRefresh)}
              color={autoRefresh ? "primary" : "default"}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {metrics && (
        <Grid container spacing={3}>
          {/* Token Status */}
          <Grid item xs={12} md={6}>
            <MetricCard>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Token Bucket Status</Typography>
                  <SpeedIcon color="primary" />
                </Box>
                
                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2" color="text.secondary">
                      Available Tokens
                    </Typography>
                    <Typography variant="body2">
                      {Math.floor(metrics.available_tokens)} / {metrics.token_capacity}
                    </Typography>
                  </Box>
                  <TokenBar 
                    variant="determinate" 
                    value={(metrics.available_tokens / metrics.token_capacity) * 100}
                  />
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Requests/min
                    </Typography>
                    <Typography variant="h6">
                      {metrics.requests_per_minute.toFixed(1)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Avg Wait Time
                    </Typography>
                    <Typography variant="h6">
                      {metrics.average_wait_time.toFixed(2)}s
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </MetricCard>
          </Grid>

          {/* Request Statistics */}
          <Grid item xs={12} md={6}>
            <MetricCard>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Request Statistics</Typography>
                  <TimelineIcon color="primary" />
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <SuccessIcon color="success" fontSize="small" />
                      <Typography variant="body2" color="text.secondary">
                        Successful
                      </Typography>
                    </Box>
                    <Typography variant="h6" color="success.main">
                      {metrics.successful_requests}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <WarningIcon color="warning" fontSize="small" />
                      <Typography variant="body2" color="text.secondary">
                        Rate Limited
                      </Typography>
                    </Box>
                    <Typography variant="h6" color="warning.main">
                      {metrics.rate_limited_requests}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <ErrorIcon color="error" fontSize="small" />
                      <Typography variant="body2" color="text.secondary">
                        Failed
                      </Typography>
                    </Box>
                    <Typography variant="h6" color="error.main">
                      {metrics.failed_requests}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Success Rate
                    </Typography>
                    <Typography variant="h6" color={metrics.success_rate > 0.9 ? "success.main" : "warning.main"}>
                      {(metrics.success_rate * 100).toFixed(1)}%
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </MetricCard>
          </Grid>

          {/* Queue Status */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Request Queue Status</Typography>
                <QueueIcon color="primary" />
              </Box>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {metrics.current_queue_size}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Queued
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={9}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Queue by Priority
                  </Typography>
                  <Grid container spacing={2}>
                    {Object.entries(metrics.queue_sizes_by_priority).map(([priority, size]) => (
                      <Grid item xs={6} md={3} key={priority}>
                        <Chip
                          label={`${priority}: ${size}`}
                          color={
                            priority === 'CRITICAL' ? 'error' :
                            priority === 'HIGH' ? 'warning' :
                            priority === 'MEDIUM' ? 'info' : 'default'
                          }
                          variant="outlined"
                          sx={{ width: '100%' }}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </Grid>
              </Grid>

              {metrics.consecutive_429s > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Alert severity="warning">
                    Consecutive 429 errors: {metrics.consecutive_429s}
                    {metrics.consecutive_429s > 3 && 
                      " - Consider reducing request rate or increasing cache TTL"}
                  </Alert>
                </>
              )}
            </Paper>
          </Grid>

          {/* Uptime */}
          <Grid item xs={12}>
            <Box textAlign="center">
              <Typography variant="body2" color="text.secondary">
                Rate Limiter Uptime
              </Typography>
              <Typography variant="h6">
                {Math.floor(metrics.uptime_seconds / 60)} minutes {Math.floor(metrics.uptime_seconds % 60)} seconds
              </Typography>
            </Box>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}

export default RateLimitMonitor;