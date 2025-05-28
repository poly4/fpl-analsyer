import React, { lazy, Suspense, useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { Box, useMediaQuery } from '@mui/material';

// Import providers
import ThemeProvider from './components/ThemeProvider';
import AccessibilityProvider from './components/AccessibilityProvider';
import PerformanceMonitor from './components/PerformanceMonitor';

// Import navigation components
import MobileNavigation from './components/MobileNavigation';

// Import loading components
import { PageSkeleton } from './components/Skeletons';

// Lazy load pages for optimal code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const LiveH2HBattle = lazy(() => import('./components/LiveH2HBattle'));
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard'));
const PredictiveSimulator = lazy(() => import('./components/PredictiveSimulator'));
const ServiceWorkerManager = lazy(() => import('./components/ServiceWorkerManager'));

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
    // In production, you might want to log this to an error reporting service
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
            textAlign: 'center'
          }}
        >
          <h1>Oops! Something went wrong</h1>
          <p>We're sorry for the inconvenience. Please try refreshing the page.</p>
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

// Main App Layout Component
const AppLayout = ({ children, currentPage, onPageChange }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Skip to main content for accessibility */}
      <a 
        href="#main-content" 
        style={{
          position: 'absolute',
          left: '-10000px',
          top: 'auto',
          width: '1px',
          height: '1px',
          overflow: 'hidden'
        }}
        onFocus={(e) => {
          e.target.style.position = 'static';
          e.target.style.width = 'auto';
          e.target.style.height = 'auto';
        }}
        onBlur={(e) => {
          e.target.style.position = 'absolute';
          e.target.style.left = '-10000px';
          e.target.style.width = '1px';
          e.target.style.height = '1px';
        }}
      >
        Skip to main content
      </a>

      {/* Main content area */}
      <Box 
        component="main"
        id="main-content"
        sx={{ 
          flex: 1,
          pb: { xs: 8, md: 0 }, // Add bottom padding on mobile for navigation
        }}
      >
        {children}
      </Box>

      {/* Mobile Navigation */}
      <MobileNavigation 
        currentPage={currentPage}
        onPageChange={onPageChange}
      />
    </Box>
  );
};

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AccessibilityProvider>
          <PerformanceMonitor>
            <Router>
              <AppLayout currentPage={currentPage} onPageChange={handlePageChange}>
                <Suspense fallback={<PageLoader />}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    
                    <Route 
                      path="/dashboard" 
                      element={<Dashboard />} 
                    />
                    
                    <Route 
                      path="/analytics" 
                      element={<AnalyticsDashboard />} 
                    />
                    
                    <Route 
                      path="/live" 
                      element={
                        <LiveH2HBattle 
                          battle={{
                            manager1_id: 197050,
                            manager2_id: 3354300,
                            manager1_name: "Manager 1",
                            manager2_name: "Manager 2",
                            manager1_score: 45,
                            manager2_score: 52,
                            manager1_players: [],
                            manager2_players: []
                          }}
                          gameweek={38}
                          viewerId={197050}
                        />
                      } 
                    />
                    
                    <Route 
                      path="/simulator" 
                      element={
                        <PredictiveSimulator 
                          manager1Id={197050}
                          manager2Id={3354300}
                          gameweek={38}
                        />
                      } 
                    />
                    
                    {/* Fallback route */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Suspense>
                
                {/* Service Worker Manager */}
                <Suspense fallback={null}>
                  <ServiceWorkerManager />
                </Suspense>
              </AppLayout>
            </Router>
          </PerformanceMonitor>
        </AccessibilityProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;