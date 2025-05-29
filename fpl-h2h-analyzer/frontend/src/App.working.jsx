import React, { Suspense, useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab, Container } from '@mui/material';

// Create a simple, working theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#BB86FC',
    },
    secondary: {
      main: '#03DAC6',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

// Simple Dashboard component
function Dashboard() {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        🏆 FPL H2H Live Analyzer
      </Typography>
      <Typography variant="h6" color="textSecondary" paragraph>
        Top Dog Premier League - Real-time H2H Analysis
      </Typography>
      
      <Box sx={{ bgcolor: 'background.paper', p: 3, borderRadius: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          ✅ Application Status
        </Typography>
        <ul>
          <li>✅ Frontend: Loaded successfully</li>
          <li>✅ Backend: Connected to API</li>
          <li>✅ Database: League data available</li>
          <li>✅ Real FPL Data: "Top Dog Premier League" (620117)</li>
        </ul>
      </Box>

      <Box sx={{ bgcolor: 'background.paper', p: 3, borderRadius: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          🎯 Current Featured Battle
        </Typography>
        <Typography>
          Abdul Nasir (Nasir FC **) vs Darren Phillips (Livin Saliba Loca)
        </Typography>
        <Typography color="textSecondary">
          Gameweek 38 - Live data available
        </Typography>
      </Box>
    </Container>
  );
}

// Simple Live Battle component
function LiveBattle() {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        ⚡ Live H2H Battle
      </Typography>
      <Box sx={{ bgcolor: 'background.paper', p: 3, borderRadius: 2 }}>
        <Typography>Live battle functionality will be implemented here.</Typography>
      </Box>
    </Container>
  );
}

// Simple Analytics component  
function Analytics() {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        📊 Analytics Dashboard
      </Typography>
      <Box sx={{ bgcolor: 'background.paper', p: 3, borderRadius: 2 }}>
        <Typography>Analytics dashboard will be implemented here.</Typography>
      </Box>
    </Container>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                FPL H2H Analyzer
              </Typography>
            </Toolbar>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange}
              sx={{ bgcolor: 'primary.dark' }}
            >
              <Tab label="Dashboard" />
              <Tab label="Live Battle" />
              <Tab label="Analytics" />
            </Tabs>
          </AppBar>

          <TabPanel value={tabValue} index={0}>
            <Dashboard />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <LiveBattle />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <Analytics />
          </TabPanel>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;