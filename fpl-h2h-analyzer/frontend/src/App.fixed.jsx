import React, { lazy, Suspense, useState, useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab, useMediaQuery } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

// Debug logging
console.log('🚀 Full FPL H2H Analyzer loading...');

// Import providers that are known to work
import ErrorBoundary from './components/ErrorBoundary';

// Import navigation components  
import WebSocketStatus from './components/WebSocketStatus';

// Import loading components
import { PageSkeleton } from './components/Skeletons';

// Lazy load pages for optimal code splitting with error handling
const Dashboard = lazy(() => import('./pages/Dashboard').catch(err => {
  console.error('Failed to load Dashboard:', err);
  return { default: () => <div style={{padding: '20px', color: '#fff'}}>Dashboard temporarily unavailable</div> };
}));

const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard').catch(err => {
  console.error('Failed to load AnalyticsDashboard:', err);
  return { default: () => <div style={{padding: '20px', color: '#fff'}}>Analytics Dashboard temporarily unavailable</div> };
}));

const RateLimitMonitor = lazy(() => import('./components/RateLimitMonitor').catch(err => {
  console.error('Failed to load RateLimitMonitor:', err);
  return { default: () => <div style={{padding: '20px', color: '#fff'}}>Rate Limit Monitor temporarily unavailable</div> };
}));

// Create a proper Material-UI dark theme with all required color properties
const createModernTheme = () => createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#667eea',
      light: '#9aa7ff',
      dark: '#3f51b5',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#f093fb',
      light: '#ff6bcf',
      dark: '#c762c8',
      contrastText: '#ffffff',
    },
    background: {
      default: '#0a0a0f',
      paper: '#1a1a2e',
    },
    text: {
      primary: 'rgba(255, 255, 255, 0.95)',
      secondary: 'rgba(255, 255, 255, 0.75)',
      disabled: 'rgba(255, 255, 255, 0.4)',
    },
    error: {
      main: '#ff4757',
      light: '#ff6b7a',
      dark: '#cc3a47',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#ffd93d',
      light: '#ffe066',
      dark: '#ccad31',
      contrastText: '#000000',
    },
    info: {
      main: '#3742fa',
      light: '#5a67fb',
      dark: '#2c35c8',
      contrastText: '#ffffff',
    },
    success: {
      main: '#00ff88',
      light: '#33ff9f',
      dark: '#00cc6d',
      contrastText: '#000000',
    },
    divider: 'rgba(255, 255, 255, 0.1)',
    action: {
      active: 'rgba(255, 255, 255, 0.56)',
      hover: 'rgba(255, 255, 255, 0.04)',
      selected: 'rgba(255, 255, 255, 0.08)',
      disabled: 'rgba(255, 255, 255, 0.26)',
      disabledBackground: 'rgba(255, 255, 255, 0.12)',
      focus: 'rgba(255, 255, 255, 0.12)'
    }
  },
  typography: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h5: {
      fontWeight: 700,
    }
  },
});

// Enhanced Tab Panel Component with animations
const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`tabpanel-${index}`}
    aria-labelledby={`tab-${index}`}
    {...other}
  >
    <AnimatePresence mode="wait">
      {value === index && (
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <Box sx={{ minHeight: '60vh', p: { xs: 2, md: 3 } }}>
            {children}
          </Box>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

// Main App Component
function App() {
  console.log('🎯 App component rendering...');
  
  const [currentPage, setCurrentPage] = useState(0);
  const theme = createModernTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Handle page change
  const handlePageChange = (event, newValue) => {
    setCurrentPage(newValue);
  };

  useEffect(() => {
    console.log('✅ App mounted successfully');
  }, []);

  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            {/* Modern Glassmorphic Header */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            >
              <AppBar 
                position="static" 
                elevation={0}
                sx={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  backdropFilter: 'blur(30px)',
                  WebkitBackdropFilter: 'blur(30px)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 0,
                  boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
                }}
              >
                <Toolbar sx={{ py: 1.5 }}>
                  <motion.div style={{ flexGrow: 1 }}>
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
                        letterSpacing: '-0.5px'
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
                  </motion.div>
                  
                  {/* WebSocket Status */}
                  <WebSocketStatus />
                </Toolbar>
              </AppBar>
            </motion.div>

            {/* Glass Navigation Tabs */}
            <Box 
              sx={{ 
                px: 3, 
                pt: 2,
                background: 'rgba(255, 255, 255, 0.02)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
              }}
            >
              <Tabs
                value={currentPage}
                onChange={handlePageChange}
                variant={isMobile ? "scrollable" : "fullWidth"}
                scrollButtons="auto"
                sx={{
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                  '& .MuiTab-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                    transition: 'all 0.3s ease',
                    fontWeight: 500,
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    py: 2,
                    px: 3,
                    borderRadius: '12px 12px 0 0',
                    margin: '0 4px',
                    '&:hover': {
                      color: '#fff',
                      background: 'rgba(255, 255, 255, 0.05)',
                      transform: 'translateY(-1px)',
                    }
                  },
                  '& .Mui-selected': {
                    color: '#fff !important',
                    background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
                    boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
                    transform: 'translateY(-1px)',
                    border: '1px solid transparent',
                  },
                  '& .MuiTabs-indicator': {
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    height: 3,
                    borderRadius: '3px 3px 0 0'
                  }
                }}
              >
                <Tab label="👥 Manager Comparison" />
                <Tab label="📊 Analytics Dashboard" />
                <Tab label="💻 System Health" />
              </Tabs>
            </Box>

            {/* Content Area with Animations */}
            <Box sx={{ flex: 1 }}>
              <TabPanel value={currentPage} index={0}>
                <Suspense fallback={<PageSkeleton />}>
                  <Dashboard />
                </Suspense>
              </TabPanel>
              
              <TabPanel value={currentPage} index={1}>
                <Suspense fallback={<PageSkeleton />}>
                  <AnalyticsDashboard />
                </Suspense>
              </TabPanel>
              
              <TabPanel value={currentPage} index={2}>
                <Suspense fallback={<PageSkeleton />}>
                  <RateLimitMonitor />
                </Suspense>
              </TabPanel>
            </Box>
          </Box>
        </Router>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;