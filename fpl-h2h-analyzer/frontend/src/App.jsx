import React, { lazy, Suspense, useState, useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab, useMediaQuery } from '@mui/material';

// Debug logging
console.log('🚀 Full FPL H2H Analyzer loading...');
console.log('📍 Window location:', window.location.href);
console.log('🏠 Base URL:', import.meta.env.VITE_API_URL || '/api');

// Import providers that are known to work
import AccessibilityProvider from './components/AccessibilityProvider';
import PerformanceMonitor from './components/PerformanceMonitor';

// Import navigation components
import MobileNavigation from './components/MobileNavigation';

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

// Create a working theme (simplified from the complex one that caused black screen)
const createAppTheme = (mode) => {
  return createTheme({
    palette: {
      mode,
      primary: {
        main: mode === 'dark' ? '#BB86FC' : '#6200EE',
      },
      secondary: {
        main: mode === 'dark' ? '#03DAC6' : '#018786',
      },
      background: {
        default: mode === 'dark' ? '#121212' : '#fafafa',
        paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
      },
    },
    shape: {
      borderRadius: 12,
    },
  });
};

// Enhanced loading component with skeleton
const PageLoader = () => (
  <Box sx={{ p: 3 }}>
    <PageSkeleton />
  </Box>
);

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            p: 3,
            textAlign: 'center',
          }}
        >
          <Typography variant="h4" gutterBottom>Oops! Something went wrong</Typography>
          <Typography variant="body1" gutterBottom>
            We're sorry for the inconvenience. Please try refreshing the page.
          </Typography>
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              marginTop: '20px',
              backgroundColor: '#6200EE',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            Refresh Page
          </button>
        </Box>
      );
    }
    return this.props.children;
  }
}

// Tab Panel Component
const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`tabpanel-${index}`}
    aria-labelledby={`tab-${index}`}
    {...other}
  >
    {value === index && (
      <Box sx={{ minHeight: '60vh' }}>
        {children}
      </Box>
    )}
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

  const theme = createAppTheme(darkMode ? 'dark' : 'light');
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
              {/* Header */}
              <AppBar position="static" elevation={0}>
                <Toolbar>
                  <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    🏆 FPL H2H Analyzer Pro
                  </Typography>
                </Toolbar>
                
                {/* Desktop Navigation */}
                {!isMobile && (
                  <Tabs 
                    value={currentPage} 
                    onChange={handlePageChange}
                    sx={{ bgcolor: 'primary.dark' }}
                    variant="fullWidth"
                  >
                    <Tab label="📊 Dashboard" />
                    <Tab label="⚡ Live Battle" />
                    <Tab label="📈 Analytics" />
                    <Tab label="🎯 Simulator" />
                  </Tabs>
                )}
              </AppBar>

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
                  <Suspense fallback={<PageLoader />}>
                    <Dashboard />
                  </Suspense>
                </TabPanel>

                {/* Live H2H Battle Tab */}
                <TabPanel value={currentPage} index={1}>
                  <Suspense fallback={<PageLoader />}>
                    <LiveH2HBattle />
                  </Suspense>
                </TabPanel>

                {/* Analytics Dashboard Tab */}
                <TabPanel value={currentPage} index={2}>
                  <Suspense fallback={<PageLoader />}>
                    <AnalyticsDashboard />
                  </Suspense>
                </TabPanel>

                {/* Predictive Simulator Tab */}
                <TabPanel value={currentPage} index={3}>
                  <Suspense fallback={<PageLoader />}>
                    <PredictiveSimulator />
                  </Suspense>
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