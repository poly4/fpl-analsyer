import React, { useState, lazy, Suspense } from 'react';
import { Box, Typography, Tabs, Tab, Button, IconButton, Skeleton } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

// Eagerly load frequently used components
import ManagerSelector from '../components/ManagerSelector.jsx';
import LeagueSelector from '../components/LeagueSelector.jsx';

// Lazy load heavy components
const LiveBattles = lazy(() => import('../components/LiveBattles.jsx'));
const ManagerComparison = lazy(() => import('../components/ManagerComparison.jsx'));
const LeagueTable = lazy(() => import('../components/LeagueTable.jsx'));
const Analytics = lazy(() => import('../components/Analytics.jsx'));
const AnalyticsDashboard = lazy(() => import('../components/AnalyticsDashboard.jsx'));
const RateLimitMonitor = lazy(() => import('../components/RateLimitMonitor.jsx'));

// Component loading skeleton
const ComponentLoader = ({ height = 400 }) => (
  <Box sx={{ width: '100%' }}>
    <Skeleton variant="rectangular" height={height} sx={{ mb: 2 }} />
    <Skeleton variant="text" sx={{ fontSize: '1rem' }} />
    <Skeleton variant="text" sx={{ fontSize: '1rem' }} />
    <Skeleton variant="text" sx={{ fontSize: '1rem', width: '60%' }} />
  </Box>
);

function Dashboard() {
  const [tabValue, setTabValue] = useState(0);
  const [selectedManagers, setSelectedManagers] = useState(null);
  const [comparisonMode, setComparisonMode] = useState(false);
  
  // Get saved league from localStorage or use default
  const getInitialLeagueId = () => {
    const saved = localStorage.getItem('fpl_current_league');
    return saved || '620117'; // Default to Top Dog Premier League
  };
  
  const [leagueId, setLeagueId] = useState(() => {
    const initialId = getInitialLeagueId();
    // Save default to localStorage if using default
    if (!localStorage.getItem('fpl_current_league') && initialId === '620117') {
      localStorage.setItem('fpl_current_league', initialId);
    }
    return initialId;
  });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    // Reset comparison mode when switching tabs
    setComparisonMode(false);
    setSelectedManagers(null);
  };

  const handleCompare = (manager1, manager2) => {
    setSelectedManagers({ manager1, manager2 });
    setComparisonMode(true);
  };

  const handleBackToSelection = () => {
    setComparisonMode(false);
    setSelectedManagers(null);
  };

  const handleLeagueChange = (newLeagueId) => {
    setLeagueId(newLeagueId);
    localStorage.setItem('fpl_current_league', newLeagueId);
    // Reset states when league changes
    setSelectedManagers(null);
    setComparisonMode(false);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {comparisonMode && (
            <IconButton onClick={handleBackToSelection} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
          )}
          <Typography variant="h4">
            FPL H2H {comparisonMode ? 'Manager Comparison' : 'Live Battle Analyzer'}
          </Typography>
        </Box>
        <LeagueSelector 
          currentLeagueId={leagueId} 
          onLeagueChange={handleLeagueChange} 
        />
      </Box>
      
      {!comparisonMode && (
        <>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="dashboard tabs">
              <Tab label="Manager Comparison" />
              <Tab label="All Battles" />
              <Tab label="League Table" />
              <Tab label="Analytics" />
              <Tab label="Advanced Analytics" />
              <Tab label="System Health" />
            </Tabs>
          </Box>
          <Box sx={{ p: 3 }}>
            <Suspense fallback={<ComponentLoader />}>
              {tabValue === 0 && leagueId && (
                <ManagerSelector 
                  leagueId={leagueId} 
                  onCompare={handleCompare}
                />
              )}
              {tabValue === 1 && leagueId && <LiveBattles leagueId={leagueId} />}
              {tabValue === 2 && leagueId && <LeagueTable leagueId={leagueId} />}
              {tabValue === 3 && leagueId && <Analytics leagueId={leagueId} />}
              {tabValue === 4 && <AnalyticsDashboard />}
              {tabValue === 5 && <RateLimitMonitor />}
              {!leagueId && tabValue < 4 && (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="textSecondary">
                    Please select a league to view this content
                  </Typography>
                </Box>
              )}
            </Suspense>
          </Box>
        </>
      )}
      
      {comparisonMode && selectedManagers && (
        <Box sx={{ p: 3 }}>
          <Suspense fallback={<ComponentLoader height={600} />}>
            <ManagerComparison 
              manager1={selectedManagers.manager1}
              manager2={selectedManagers.manager2}
              leagueId={leagueId}
              onBack={handleBackToSelection}
            />
          </Suspense>
        </Box>
      )}
    </Box>
  );
}

export default Dashboard;