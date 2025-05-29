import React, { useState, lazy, Suspense, useEffect } from 'react';
import { Box, Typography, Tabs, Tab, Button, IconButton, Skeleton, Chip } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { motion, AnimatePresence } from 'framer-motion';

// Import modern components
import BentoGrid, { BentoCard, BENTO_SIZES } from '../components/modern/BentoGrid';
import { GlassCard, StatBox, AnimatedNumber, LiveScore } from '../components/modern';
import { glassMixins, animations } from '../styles/themes';

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

// Enhanced loading skeleton with glassmorphism
const ComponentLoader = ({ height = 400 }) => (
  <GlassCard variant="minimal" animate={false}>
    <Box sx={{ width: '100%', p: 3 }}>
      <Skeleton 
        variant="rectangular" 
        height={height} 
        sx={{ 
          mb: 2, 
          borderRadius: '12px',
          background: 'rgba(255, 255, 255, 0.05)'
        }} 
      />
      <Skeleton variant="text" sx={{ fontSize: '1rem', background: 'rgba(255, 255, 255, 0.05)' }} />
      <Skeleton variant="text" sx={{ fontSize: '1rem', background: 'rgba(255, 255, 255, 0.05)' }} />
      <Skeleton variant="text" sx={{ fontSize: '1rem', width: '60%', background: 'rgba(255, 255, 255, 0.05)' }} />
    </Box>
  </GlassCard>
);

// Animation variants
const pageVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.4,
      ease: animations.easing.easeOut
    }
  },
  exit: { 
    opacity: 0, 
    y: -20,
    transition: {
      duration: 0.3,
      ease: animations.easing.easeIn
    }
  }
};

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
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      style={{ width: '100%' }}
    >
      {/* Modern Header Section */}
      <GlassCard variant="minimal" padding={3} sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {comparisonMode && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
              >
                <IconButton 
                  onClick={handleBackToSelection} 
                  sx={{ 
                    background: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.15)',
                      transform: 'scale(1.05)'
                    }
                  }}
                >
                  <ArrowBackIcon />
                </IconButton>
              </motion.div>
            )}
            <Box>
              <Typography 
                variant="h4"
                sx={{ 
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  letterSpacing: '-0.5px'
                }}
              >
                {comparisonMode ? 'Manager Comparison' : 'Live Battle Analyzer'}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.7)',
                  mt: 0.5 
                }}
              >
                Real-time FPL H2H insights and analytics
              </Typography>
            </Box>
          </Box>
          <LeagueSelector 
            currentLeagueId={leagueId} 
            onLeagueChange={handleLeagueChange} 
          />
        </Box>
      </GlassCard>
      
      {!comparisonMode && (
        <>
          {/* Modern Tab Navigation */}
          <GlassCard variant="minimal" padding={0} sx={{ mb: 3 }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="dashboard tabs"
              sx={{
                '& .MuiTabs-indicator': {
                  display: 'none',
                },
                '& .MuiTab-root': {
                  ...glassMixins.glassNav,
                  minHeight: 48,
                  margin: '12px 6px',
                  fontWeight: 500,
                  fontSize: '0.9rem',
                  textTransform: 'none',
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
                  }
                },
                px: 2,
              }}
            >
              <Tab label="👥 Manager Comparison" />
              <Tab label="⚡ All Battles" />
              <Tab label="🏆 League Table" />
              <Tab label="📊 Analytics" />
              <Tab label="🎯 Advanced Analytics" />
              <Tab label="💻 System Health" />
            </Tabs>
          </GlassCard>

          {/* Content Area with Animations */}
          <AnimatePresence mode="wait">
            <motion.div
              key={tabValue}
              variants={pageVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
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
                  <GlassCard variant="minimal" sx={{ textAlign: 'center', py: 6 }}>
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        color: 'rgba(255, 255, 255, 0.7)',
                        mb: 2 
                      }}
                    >
                      Please select a league to view this content
                    </Typography>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        color: 'rgba(255, 255, 255, 0.5)' 
                      }}
                    >
                      Choose a league from the selector above to get started
                    </Typography>
                  </GlassCard>
                )}
              </Suspense>
            </motion.div>
          </AnimatePresence>
        </>
      )}
      
      {/* Enhanced Comparison Mode */}
      {comparisonMode && selectedManagers && (
        <AnimatePresence mode="wait">
          <motion.div
            variants={pageVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <Suspense fallback={<ComponentLoader height={600} />}>
              <ManagerComparison 
                manager1={selectedManagers.manager1}
                manager2={selectedManagers.manager2}
                leagueId={leagueId}
                onBack={handleBackToSelection}
              />
            </Suspense>
          </motion.div>
        </AnimatePresence>
      )}
    </motion.div>
  );
}

export default Dashboard;