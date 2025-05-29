import React from 'react';
import { Box, Typography } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import { createModernTheme } from './styles/themes';

// Minimal test app to debug loading issues
function TestApp() {
  console.log('🧪 Test App loading...');
  
  const theme = createModernTheme('dark');
  
  return (
    <ThemeProvider theme={theme}>
      <Box
        sx={{
          minHeight: '100vh',
          background: '#0a0a0f',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          padding: 4
        }}
      >
        <Typography 
          variant="h3" 
          sx={{ 
            fontWeight: 700,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            mb: 2
          }}
        >
          🏆 FPL H2H Analyzer Pro
        </Typography>
        
        <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
          ✅ Modern theme system is working
        </Typography>
        
        <Box
          sx={{
            mt: 3,
            p: 3,
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
          }}
        >
          <Typography variant="body2">
            🎨 Glassmorphic effects are working
          </Typography>
        </Box>
        
        <Typography variant="caption" sx={{ mt: 2, color: 'rgba(255, 255, 255, 0.5)' }}>
          If you can see this, the basic app structure is functional.
        </Typography>
      </Box>
    </ThemeProvider>
  );
}

export default TestApp;