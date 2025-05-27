import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Grid, 
  Button, 
  Chip,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Avatar
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { fplApi } from '../services/api';

function ManagerSelector({ leagueId, onCompare }) {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedManagers, setSelectedManagers] = useState([]);

  useEffect(() => {
    fetchLeagueData();
  }, [leagueId]);

  const fetchLeagueData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const overview = await fplApi.getLeagueOverview(leagueId);
      
      if (overview.standings && overview.standings.standings) {
        const managersList = overview.standings.standings.results || [];
        setManagers(managersList);
      } else {
        setError('No standings data found');
      }
    } catch (err) {
      console.error('Error fetching league data:', err);
      setError(err.message || 'Failed to load league data');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectManager = (manager) => {
    if (selectedManagers.find(m => m.entry === manager.entry)) {
      // Deselect if already selected
      setSelectedManagers(selectedManagers.filter(m => m.entry !== manager.entry));
    } else if (selectedManagers.length < 2) {
      // Select if less than 2 selected
      setSelectedManagers([...selectedManagers, manager]);
    } else {
      // Replace the first selected if 2 already selected
      setSelectedManagers([selectedManagers[1], manager]);
    }
  };

  const handleCompare = () => {
    if (selectedManagers.length === 2) {
      onCompare(selectedManagers[0], selectedManagers[1]);
    }
  };

  const isSelected = (manager) => {
    return selectedManagers.some(m => m.entry === manager.entry);
  };

  const getSelectionOrder = (manager) => {
    const index = selectedManagers.findIndex(m => m.entry === manager.entry);
    return index >= 0 ? index + 1 : null;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          Select Two Managers to Compare
        </Typography>
        {selectedManagers.length === 2 && (
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleCompare}
            size="large"
          >
            Compare Selected Managers
          </Button>
        )}
      </Box>

      {selectedManagers.length > 0 && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
          <Typography variant="subtitle1" gutterBottom>
            Selected Managers:
          </Typography>
          <Box display="flex" gap={2}>
            {selectedManagers.map((manager, index) => (
              <Chip
                key={manager.entry}
                label={`${index + 1}. ${manager.player_name} - ${manager.entry_name}`}
                onDelete={() => handleSelectManager(manager)}
                color="primary"
                icon={<Avatar sx={{ width: 24, height: 24 }}>{index + 1}</Avatar>}
              />
            ))}
          </Box>
        </Paper>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox"></TableCell>
              <TableCell>Rank</TableCell>
              <TableCell>Manager</TableCell>
              <TableCell>Team Name</TableCell>
              <TableCell align="center">Points</TableCell>
              <TableCell align="center">W</TableCell>
              <TableCell align="center">D</TableCell>
              <TableCell align="center">L</TableCell>
              <TableCell align="center">PF</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {managers.map((manager) => {
              const selected = isSelected(manager);
              const order = getSelectionOrder(manager);
              
              return (
                <TableRow 
                  key={manager.entry}
                  hover
                  onClick={() => handleSelectManager(manager)}
                  sx={{ 
                    cursor: 'pointer',
                    bgcolor: selected ? 'action.selected' : 'inherit',
                    '&:hover': {
                      bgcolor: selected ? 'action.selected' : 'action.hover'
                    }
                  }}
                >
                  <TableCell padding="checkbox">
                    {selected && (
                      <Avatar 
                        sx={{ 
                          width: 30, 
                          height: 30, 
                          bgcolor: 'primary.main',
                          fontSize: '0.875rem'
                        }}
                      >
                        {order}
                      </Avatar>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      #{manager.rank}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {manager.player_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {manager.entry_name}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" fontWeight="bold">
                      {manager.total}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" color="success.main">
                      {manager.matches_won}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" color="warning.main">
                      {manager.matches_drawn}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" color="error.main">
                      {manager.matches_lost}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2">
                      {manager.points_for}
                    </Typography>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {managers.length === 0 && (
        <Typography variant="body1" color="text.secondary" textAlign="center" mt={4}>
          No managers found in this league.
        </Typography>
      )}
    </Box>
  );
}

export default ManagerSelector;