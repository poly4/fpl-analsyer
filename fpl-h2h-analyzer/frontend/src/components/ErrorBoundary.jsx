import React from 'react';
import { Box, Typography, Button, Paper, Alert } from '@mui/material';
import { Refresh, Home } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    
    // Log specific component stack
    console.error('Component stack:', errorInfo.componentStack);
    
    this.setState({
      error,
      errorInfo,
      errorCount: this.state.errorCount + 1
    });

    // Log to monitoring service if available
    if (window.gtag) {
      window.gtag('event', 'exception', {
        description: error.toString(),
        fatal: false,
      });
    }
  }

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
  };

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, errorCount } = this.state;
      const errorMessage = error?.message || 'Unknown error occurred';
      
      // Check for specific error types
      let specificMessage = '';
      let suggestion = '';
      
      if (errorMessage.includes('WebGL') || errorMessage.includes('THREE')) {
        specificMessage = '3D visualization error';
        suggestion = 'Your browser may not support WebGL. Try using a different browser or disabling 3D features.';
      } else if (errorMessage.includes('fetch') || errorMessage.includes('network')) {
        specificMessage = 'Network connection error';
        suggestion = 'Please check your internet connection and try again.';
      } else if (errorMessage.includes('undefined') || errorMessage.includes('null')) {
        specificMessage = 'Data loading error';
        suggestion = 'The requested data may not be available. Please try refreshing or selecting different options.';
      } else if (errorMessage.includes('WebSocket')) {
        specificMessage = 'Real-time connection error';
        suggestion = 'Live updates are temporarily unavailable. The app will continue to work with periodic updates.';
      }

      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            p: 3,
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              maxWidth: 600,
              width: '100%',
              textAlign: 'center',
            }}
          >
            <Typography variant="h5" gutterBottom color="error">
              {specificMessage || 'Something went wrong'}
            </Typography>
            
            {suggestion && (
              <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
                {suggestion}
              </Alert>
            )}
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {errorMessage}
            </Typography>
            
            {errorCount > 2 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Multiple errors detected. Consider refreshing the entire page.
              </Alert>
            )}
            
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={this.handleReset}
                sx={{ mt: 2 }}
              >
                Try Again
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Home />}
                onClick={() => window.location.href = '/'}
                sx={{ mt: 2 }}
              >
                Go to Dashboard
              </Button>
            </Box>
            
            {import.meta.env.MODE === 'development' && errorInfo && (
              <details style={{ marginTop: '20px', textAlign: 'left' }}>
                <summary style={{ cursor: 'pointer' }}>Error Details (Dev Only)</summary>
                <pre style={{ 
                  fontSize: '12px', 
                  overflow: 'auto',
                  backgroundColor: '#f5f5f5',
                  padding: '10px',
                  borderRadius: '4px',
                  marginTop: '10px'
                }}>
                  {error && error.toString()}
                  {errorInfo.componentStack}
                </pre>
              </details>
            )}
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;