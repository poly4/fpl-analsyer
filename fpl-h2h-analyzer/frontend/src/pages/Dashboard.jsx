import React, { useState } from 'react';
import { Box, Typography, Tabs, Tab, Button, IconButton } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import LiveBattles from '../components/LiveBattles.jsx';
import ManagerSelector from '../components/ManagerSelector.jsx';
import ManagerComparison from '../components/ManagerComparison.jsx';

function Dashboard() {
  const [tabValue, setTabValue] = useState(0);
  const [selectedManagers, setSelectedManagers] = useState(null);
  const [comparisonMode, setComparisonMode] = useState(false);
  
  // Default league ID - this should come from config or user selection
  const LEAGUE_ID = 620117;

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

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        {comparisonMode && (
          <IconButton onClick={handleBackToSelection} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
        )}
        <Typography variant="h4">
          FPL H2H {comparisonMode ? 'Manager Comparison' : 'Live Battle Analyzer'}
        </Typography>
      </Box>
      
      {!comparisonMode && (
        <>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="dashboard tabs">
              <Tab label="Manager Comparison" />
              <Tab label="All Battles" />
              <Tab label="League Table" />
              <Tab label="Analytics" />
            </Tabs>
          </Box>
          <Box sx={{ p: 3 }}>
            {tabValue === 0 && (
              <ManagerSelector 
                leagueId={LEAGUE_ID} 
                onCompare={handleCompare}
              />
            )}
            {tabValue === 1 && <LiveBattles />}
            {tabValue === 2 && <Typography>League Table Content - Coming Soon</Typography>}
            {tabValue === 3 && <Typography>Analytics Content - Coming Soon</Typography>}
          </Box>
        </>
      )}
      
      {comparisonMode && selectedManagers && (
        <Box sx={{ p: 3 }}>
          <ManagerComparison 
            manager1={selectedManagers.manager1}
            manager2={selectedManagers.manager2}
            leagueId={LEAGUE_ID}
            onBack={handleBackToSelection}
          />
        </Box>
      )}
    </Box>
  );
}

export default Dashboard;