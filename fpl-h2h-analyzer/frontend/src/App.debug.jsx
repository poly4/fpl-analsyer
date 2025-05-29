import React, { useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab } from '@mui/material';
import { createModernTheme, glassMixins } from './styles/themes';

// Debug version to isolate the issue
function DebugApp() {
  console.log('🐛 Debug App starting...');
  
  const [currentPage, setCurrentPage] = useState(0);
  const theme = createModernTheme('dark');
  
  console.log('🎨 Theme created:', theme);
  console.log('🌟 Glass mixins:', glassMixins);
  
  const handlePageChange = (event, newValue) => {
    setCurrentPage(newValue);
  };
  
  useEffect(() => {
    console.log('✅ Debug App mounted successfully');
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
            ...glassMixins.glass,
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(30px)',
            WebkitBackdropFilter: 'blur(30px)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 0,
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
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                letterSpacing: '-0.5px',
                flexGrow: 1
              }}
            >
              🏆 FPL H2H Analyzer Pro
              <Box
                component="span"
                sx={{
                  fontSize: '0.7rem',
                  background: 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  fontWeight: 600,
                  ml: 1
                }}
              >
                v6.0
              </Box>
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
                transition: 'all 0.3s ease',
                fontWeight: 500,
                '&:hover': {
                  color: '#fff',
                  background: 'rgba(255, 255, 255, 0.05)'
                }
              },
              '& .Mui-selected': {
                color: '#fff !important',
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
              },
              '& .MuiTabs-indicator': {
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                height: 3,
                borderRadius: '3px 3px 0 0'
              }
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
              ...glassMixins.glass,
              p: 4,
              textAlign: 'center',
              background: 'rgba(255, 255, 255, 0.05)',
            }}
          >
            <Typography variant="h4" sx={{ mb: 2, color: '#fff' }}>
              🎉 Modern UI is Working!
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              Selected tab: {currentPage + 1}
            </Typography>
            <Typography variant="body2" sx={{ mt: 2, color: 'rgba(255, 255, 255, 0.5)' }}>
              The glassmorphic design system is loading correctly.
            </Typography>
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default DebugApp;