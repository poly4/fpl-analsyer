import React, { lazy, Suspense, useState, useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab, useMediaQuery } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { initializePerformanceMonitoring, prefetchRoutes } from './utils/performance';

// Initialize performance monitoring
if (typeof window !== 'undefined') {
  initializePerformanceMonitoring();
  
  // Prefetch likely routes
  prefetchRoutes([
    '/api/league/620117',
    '/api/gameweek/current',
    '/api/bootstrap-static'
  ]);
}

// Debug logging
console.log('🚀 Full FPL H2H Analyzer loading...');
console.log('📍 Window location:', window.location.href);
console.log('🏠 Base URL:', import.meta.env.VITE_API_URL || '/api');

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

// Import providers that are known to work
import AccessibilityProvider from './components/AccessibilityProvider';
import PerformanceMonitor from './components/PerformanceMonitor';
import ErrorBoundary from './components/ErrorBoundary';

// Import navigation components
import MobileNavigation from './components/MobileNavigation';
import WebSocketStatus from './components/WebSocketStatus';

// Import loading components
import { PageSkeleton } from './components/Skeletons';

// Lazy load pages for optimal code splitting with error handling
const Dashboard = lazy(() => import('./pages/Dashboard').catch(err => {
  console.error('Failed to load Dashboard:', err);
  return { default: () => <div style={{padding: '20px'}}>Dashboard temporarily unavailable</div> };
}));

const LiveH2HBattle = lazy(() => import('./components/LiveH2HBattle').catch(err => {
  console.error('Failed to load LiveH2HBattle:', err);
  return { default: () => <div style={{padding: '20px'}}>Live H2H Battle temporarily unavailable</div> };
}));

const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard').catch(err => {
  console.error('Failed to load AnalyticsDashboard:', err);
  return { default: () => <div style={{padding: '20px'}}>Analytics Dashboard temporarily unavailable</div> };
}));

const PredictiveSimulator = lazy(() => import('./components/PredictiveSimulator').catch(err => {
  console.error('Failed to load PredictiveSimulator:', err);
  return { default: () => <div style={{padding: '20px'}}>Predictive Simulator temporarily unavailable</div> };
}));

const ServiceWorkerManager = lazy(() => import('./components/ServiceWorkerManager').catch(err => {
  console.error('Failed to load ServiceWorkerManager:', err);
  return { default: () => <div>ServiceWorker unavailable</div> };
}));

// Animation variants for Framer Motion
const headerVariants = {
  hidden: { opacity: 0, y: -20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut"
    }
  }
};

const tabVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: {
      duration: 0.3,
      ease: "easeInOut"
    }
  },
  hover: {
    scale: 1.02,
    transition: { duration: 0.2 }
  }
};

const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

// Enhanced loading component with skeleton
const PageLoader = () => (
  <Box sx={{ p: 3 }}>
    <PageSkeleton />
  </Box>
);

// Component-specific error boundary wrapper
const ComponentErrorBoundary = ({ children, name }) => {
  return (
    <ErrorBoundary>
      {children}
    </ErrorBoundary>
  );
};

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
          transition={{
            duration: 0.4,
            ease: "easeOut"
          }}
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
  const [darkMode, setDarkMode] = useState(() => {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode !== null) {
      return JSON.parse(savedMode);
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const theme = createModernTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Handle page change
  const handlePageChange = (event, newValue) => {
    setCurrentPage(newValue);
  };

  // Toggle theme
  const toggleTheme = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', JSON.stringify(newMode));
  };

  useEffect(() => {
    console.log('✅ App mounted successfully');
  }, []);

  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AccessibilityProvider onToggleTheme={toggleTheme}>
          <PerformanceMonitor />
          <Router>
            <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              {/* Modern Glassmorphic Header */}
              <motion.div
                variants={headerVariants}
                initial="hidden"
                animate="visible"
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
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.05)',
                    }
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
                            fontWeight: 500,
                            background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                            ml: 1,
                            opacity: 0.8
                          }}
                        >
                          2025
                        </Box>
                      </Typography>
                    </motion.div>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <WebSocketStatus />
                    </Box>
                  </Toolbar>
                  
                  {/* Modern Glass Navigation Pills */}
                  {!isMobile && (
                    <motion.div
                      variants={staggerContainer}
                      initial="hidden"
                      animate="visible"
                    >
                      <Box 
                        sx={{ 
                          px: 3, 
                          pb: 2,
                          display: 'flex',
                          justifyContent: 'center'
                        }}
                      >
                        <Tabs 
                          value={currentPage} 
                          onChange={handlePageChange}
                          sx={{
                            minHeight: 48,
                            '& .MuiTabs-indicator': {
                              display: 'none', // Hide default indicator
                            },
                            '& .MuiTab-root': {
                              background: 'rgba(255, 255, 255, 0.05)',
                              backdropFilter: 'blur(10px)',
                              WebkitBackdropFilter: 'blur(10px)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                              borderRadius: '20px',
                              minHeight: 40,
                              minWidth: 120,
                              margin: '0 6px',
                              fontWeight: 500,
                              fontSize: '0.9rem',
                              textTransform: 'none',
                              letterSpacing: '0.5px',
                              color: 'rgba(255, 255, 255, 0.8)',
                              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                              '&:hover': {
                                background: 'rgba(255, 255, 255, 0.08)',
                                transform: 'translateY(-1px) scale(1.02)',
                                color: 'rgba(255, 255, 255, 0.95)',
                                boxShadow: '0 8px 25px rgba(102, 126, 234, 0.2)',
                              },
                              '&.Mui-selected': {
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                color: '#ffffff',
                                boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
                                transform: 'translateY(-1px)',
                                border: '1px solid transparent',
                                '&:hover': {
                                  background: 'linear-gradient(135deg, #7c8cff 0%, #8a5bb8 100%)',
                                  transform: 'translateY(-2px) scale(1.02)',
                                }
                              }
                            }
                          }}
                        >
                          <motion.div variants={tabVariants}>
                            <Tab 
                              label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <span>📊</span>
                                  <span>Dashboard</span>
                                </Box>
                              } 
                            />
                          </motion.div>
                          <motion.div variants={tabVariants}>
                            <Tab 
                              label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <span>⚡</span>
                                  <span>Live Battle</span>
                                </Box>
                              } 
                            />
                          </motion.div>
                          <motion.div variants={tabVariants}>
                            <Tab 
                              label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <span>📈</span>
                                  <span>Analytics</span>
                                </Box>
                              } 
                            />
                          </motion.div>
                          <motion.div variants={tabVariants}>
                            <Tab 
                              label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <span>🎯</span>
                                  <span>Simulator</span>
                                </Box>
                              } 
                            />
                          </motion.div>
                        </Tabs>
                      </Box>
                    </motion.div>
                  )}
                </AppBar>
              </motion.div>

              {/* Main content area */}
              <Box 
                component="main"
                sx={{ 
                  flexGrow: 1,
                  overflow: 'auto',
                  bgcolor: 'background.default'
                }}
              >
                {/* Dashboard Tab */}
                <TabPanel value={currentPage} index={0}>
                  <ComponentErrorBoundary name="Dashboard">
                    <Suspense fallback={<PageLoader />}>
                      <Dashboard />
                    </Suspense>
                  </ComponentErrorBoundary>
                </TabPanel>

                {/* Live H2H Battle Tab */}
                <TabPanel value={currentPage} index={1}>
                  <ComponentErrorBoundary name="LiveH2HBattle">
                    <Suspense fallback={<PageLoader />}>
                      <LiveH2HBattle />
                    </Suspense>
                  </ComponentErrorBoundary>
                </TabPanel>

                {/* Analytics Dashboard Tab */}
                <TabPanel value={currentPage} index={2}>
                  <ComponentErrorBoundary name="AnalyticsDashboard">
                    <Suspense fallback={<PageLoader />}>
                      <AnalyticsDashboard />
                    </Suspense>
                  </ComponentErrorBoundary>
                </TabPanel>

                {/* Predictive Simulator Tab */}
                <TabPanel value={currentPage} index={3}>
                  <ComponentErrorBoundary name="PredictiveSimulator">
                    <Suspense fallback={<PageLoader />}>
                      <PredictiveSimulator />
                    </Suspense>
                  </ComponentErrorBoundary>
                </TabPanel>

                {/* Service Worker Manager (invisible) */}
                <Suspense fallback={null}>
                  <ServiceWorkerManager />
                </Suspense>
              </Box>

              {/* Mobile Navigation */}
              {isMobile && (
                <MobileNavigation 
                  currentPage={currentPage}
                  onPageChange={handlePageChange}
                />
              )}
            </Box>
          </Router>
        </AccessibilityProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;