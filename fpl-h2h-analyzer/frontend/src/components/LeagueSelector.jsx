import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Alert,
  IconButton,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Add,
  Delete,
  Sports,
  Edit
} from '@mui/icons-material';

function LeagueSelector({ currentLeagueId, onLeagueChange }) {
  const [open, setOpen] = useState(false);
  const [leagueId, setLeagueId] = useState('');
  const [leagueName, setLeagueName] = useState('');
  const [error, setError] = useState('');
  
  // Default popular leagues
  const DEFAULT_LEAGUES = [
    { id: '620117', name: 'Top Dog Premier League', addedAt: new Date().toISOString() },
    { id: '820754', name: 'Popular League 820754', addedAt: new Date().toISOString() }
  ];

  // Get saved leagues from localStorage
  const getSavedLeagues = () => {
    const saved = localStorage.getItem('fpl_saved_leagues');
    if (saved) {
      const parsedLeagues = JSON.parse(saved);
      // Merge with default leagues, avoiding duplicates
      const mergedLeagues = [...DEFAULT_LEAGUES];
      parsedLeagues.forEach(league => {
        if (!mergedLeagues.some(l => l.id === league.id)) {
          mergedLeagues.push(league);
        }
      });
      return mergedLeagues;
    }
    return DEFAULT_LEAGUES;
  };
  
  const [savedLeagues, setSavedLeagues] = useState(getSavedLeagues());

  const handleOpen = () => {
    setOpen(true);
    setError('');
  };

  const handleClose = () => {
    setOpen(false);
    setLeagueId('');
    setLeagueName('');
    setError('');
  };

  const handleSaveLeague = () => {
    if (!leagueId) {
      setError('Please enter a league ID');
      return;
    }
    
    if (!leagueId.match(/^\d+$/)) {
      setError('League ID must be a number');
      return;
    }
    
    const newLeague = {
      id: leagueId,
      name: leagueName || `League ${leagueId}`,
      addedAt: new Date().toISOString()
    };
    
    // Check if league already exists
    if (savedLeagues.some(league => league.id === leagueId)) {
      setError('This league is already saved');
      return;
    }
    
    const updatedLeagues = [...savedLeagues, newLeague];
    setSavedLeagues(updatedLeagues);
    localStorage.setItem('fpl_saved_leagues', JSON.stringify(updatedLeagues));
    
    // Automatically select the new league
    onLeagueChange(leagueId);
    handleClose();
  };

  const handleSelectLeague = (leagueId) => {
    onLeagueChange(leagueId);
    setOpen(false);
  };

  const handleDeleteLeague = (leagueId) => {
    const updatedLeagues = savedLeagues.filter(league => league.id !== leagueId);
    setSavedLeagues(updatedLeagues);
    localStorage.setItem('fpl_saved_leagues', JSON.stringify(updatedLeagues));
    
    // If we deleted the current league, clear selection
    if (currentLeagueId === leagueId) {
      onLeagueChange(null);
    }
  };

  const getCurrentLeagueName = () => {
    const currentLeague = savedLeagues.find(league => league.id === currentLeagueId);
    return currentLeague?.name || `League ${currentLeagueId}`;
  };

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Chip
          icon={<Sports />}
          label={currentLeagueId ? getCurrentLeagueName() : 'No League Selected'}
          color={currentLeagueId ? 'primary' : 'default'}
          onClick={handleOpen}
          onDelete={currentLeagueId ? handleOpen : undefined}
          deleteIcon={<Edit />}
        />
        {!currentLeagueId && (
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleOpen}
            size="small"
          >
            Select League
          </Button>
        )}
      </Box>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          Manage FPL Leagues
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Add a new league or select from your saved leagues
            </Typography>
            
            {/* Add New League Form */}
            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Add New League
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <TextField
                  label="League ID"
                  value={leagueId}
                  onChange={(e) => setLeagueId(e.target.value)}
                  error={!!error}
                  helperText={error}
                  size="small"
                  fullWidth
                  placeholder="e.g. 620117"
                />
                <TextField
                  label="League Name (Optional)"
                  value={leagueName}
                  onChange={(e) => setLeagueName(e.target.value)}
                  size="small"
                  fullWidth
                  placeholder="e.g. My Work League"
                />
                <Button
                  variant="contained"
                  onClick={handleSaveLeague}
                  startIcon={<Add />}
                  sx={{ minWidth: 100 }}
                >
                  Add
                </Button>
              </Box>
            </Paper>

            {/* Saved Leagues List */}
            <Typography variant="subtitle2" gutterBottom>
              Your Leagues
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Select from popular leagues or add your own
            </Typography>
            {savedLeagues.length === 0 ? (
              <Alert severity="info">
                No saved leagues yet. Add your first league above!
              </Alert>
            ) : (
              <List>
                {savedLeagues.map((league) => (
                  <ListItem
                    key={league.id}
                    button
                    onClick={() => handleSelectLeague(league.id)}
                    selected={currentLeagueId === league.id}
                    sx={{
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1,
                      '&.Mui-selected': {
                        borderColor: 'primary.main',
                        bgcolor: 'primary.dark',
                      }
                    }}
                  >
                    <ListItemText
                      primary={league.name}
                      secondary={`ID: ${league.id}`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        aria-label="delete"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteLeague(league.id);
                        }}
                        size="small"
                      >
                        <Delete />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default LeagueSelector;