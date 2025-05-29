import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab } from '@mui/material';
import { glassMixins } from './styles/themes';

// Simple working version with proper Material-UI theme
function SimpleApp() {
  console.log('🚀 Simple App starting...');
  
  const [currentPage, setCurrentPage] = useState(0);
  
  // Create a proper Material-UI dark theme
  const theme = createTheme({
    palette: {
      mode: 'dark',
      primary: {
        main: '#667eea',
      },
      secondary: {
        main: '#f093fb',
      },
      background: {
        default: '#0a0a0f',
        paper: '#1a1a2e',
      },
    },
    typography: {
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
  });
  
  const handlePageChange = (event, newValue) => {
    setCurrentPage(newValue);
  };
  
  useEffect(() => {
    console.log('✅ Simple App mounted successfully');
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {/* Modern Glassmorphic Header */}
        <AppBar 
          position="static" 
          elevation={0}
          sx={{
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(30px)',
            WebkitBackdropFilter: 'blur(30px)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
          }}
        >
          <Toolbar sx={{ py: 1.5 }}>
            <Typography 
              variant="h5" 
              component="div" 
              sx={{ 
                fontWeight: 700,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                flexGrow: 1
              }}
            >
              🏆 FPL H2H Analyzer Pro
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Navigation Tabs */}
        <Box sx={{ px: 3, pt: 2 }}>
          <Tabs
            value={currentPage}
            onChange={handlePageChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              '& .MuiTab-root': {
                color: 'rgba(255, 255, 255, 0.7)',
                '&:hover': {
                  color: '#fff',
                  background: 'rgba(255, 255, 255, 0.05)'
                }
              },
              '& .Mui-selected': {
                color: '#fff !important',
              },
            }}
          >
            <Tab label="👥 Manager Comparison" />
            <Tab label="⚡ All Battles" />
            <Tab label="🏆 League Table" />
            <Tab label="📊 Analytics" />
          </Tabs>
        </Box>

        {/* Main Content */}
        <Box sx={{ flex: 1, p: 3 }}>
          <Box
            sx={{
              p: 4,
              textAlign: 'center',
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '16px',
              boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
            }}
          >
            <Typography variant="h4" sx={{ mb: 2, color: '#fff' }}>
              🎉 Modern UI is Working!
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.7)', mb: 2 }}>
              Selected tab: {['Manager Comparison', 'All Battles', 'League Table', 'Analytics'][currentPage]}
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
              ✅ Dark theme with glassmorphic effects<br/>
              ✅ Gradient text headers<br/>
              ✅ Modern navigation tabs<br/>
              ✅ Material-UI integration working
            </Typography>
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default SimpleApp;