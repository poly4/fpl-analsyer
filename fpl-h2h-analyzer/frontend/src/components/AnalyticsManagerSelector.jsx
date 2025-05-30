import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Autocomplete,
  TextField,
  CircularProgress,
  Avatar,
  Chip,
  Button,
  Grid,
  Alert,
} from '@mui/material';
import { Person as PersonIcon, CompareArrows as CompareIcon } from '@mui/icons-material';
import { GlassCard } from './modern';
import { useOptimizedAPI } from '../hooks/useOptimizedAPI';

const AnalyticsManagerSelector = ({ onSelectionChange, leagueId = 620117 }) => {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedManager1, setSelectedManager1] = useState(null);
  const [selectedManager2, setSelectedManager2] = useState(null);
  
  const { request } = useOptimizedAPI();

  useEffect(() => {
    fetchManagers();
  }, [leagueId]);

  const fetchManagers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await request(`/api/league/${leagueId}/overview`);
      const standings = response.standings?.standings?.results || [];
      
      // Transform standings data for autocomplete
      const managerList = standings.map(team => ({
        id: team.entry,
        name: team.player_name || `Manager ${team.entry}`,
        teamName: team.entry_name || 'Unknown Team',
        rank: team.rank,
        points: team.points_for,
        wins: team.matches_won,
        avatar: team.player_name ? team.player_name.charAt(0).toUpperCase() : 'M',
      }));
      
      setManagers(managerList);
    } catch (err) {
      console.error('Error fetching managers:', err);
      setError('Failed to load manager list');
    } finally {
      setLoading(false);
    }
  };

  const handleManager1Change = (event, newValue) => {
    setSelectedManager1(newValue);
    if (newValue && selectedManager2) {
      onSelectionChange(newValue.id, selectedManager2.id);
    }
  };

  const handleManager2Change = (event, newValue) => {
    setSelectedManager2(newValue);
    if (selectedManager1 && newValue) {
      onSelectionChange(selectedManager1.id, newValue.id);
    }
  };

  const handleQuickSelect = (type) => {
    if (managers.length === 0) return;
    
    let manager1, manager2;
    
    switch (type) {
      case 'top2':
        manager1 = managers[0];
        manager2 = managers[1];
        break;
      case 'topBottom':
        manager1 = managers[0];
        manager2 = managers[managers.length - 1];
        break;
      case 'rivals':
        // Select two managers with closest points
        const sortedByPoints = [...managers].sort((a, b) => b.points - a.points);
        let minDiff = Infinity;
        let rivalPair = [sortedByPoints[0], sortedByPoints[1]];
        
        for (let i = 0; i < sortedByPoints.length - 1; i++) {
          const diff = Math.abs(sortedByPoints[i].points - sortedByPoints[i + 1].points);
          if (diff < minDiff && diff > 0) {
            minDiff = diff;
            rivalPair = [sortedByPoints[i], sortedByPoints[i + 1]];
          }
        }
        
        manager1 = rivalPair[0];
        manager2 = rivalPair[1];
        break;
      default:
        return;
    }
    
    setSelectedManager1(manager1);
    setSelectedManager2(manager2);
    if (manager1 && manager2) {
      onSelectionChange(manager1.id, manager2.id);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
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
    <GlassCard sx={{ mb: 3 }}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Select Managers for Analysis
        </Typography>
        
        <Grid container spacing={3} alignItems="center" sx={{ mb: 2 }}>
          <Grid item xs={12} md={5}>
            <Autocomplete
              value={selectedManager1}
              onChange={handleManager1Change}
              options={managers}
              getOptionLabel={(option) => `${option.name} - ${option.teamName}`}
              renderOption={(props, option) => (
                <Box component="li" {...props} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ width: 32, height: 32, fontSize: 14 }}>
                    {option.avatar}
                  </Avatar>
                  <Box>
                    <Typography variant="body1">{option.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.teamName} • Rank #{option.rank}
                    </Typography>
                  </Box>
                </Box>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Manager 1"
                  placeholder="Search for a manager..."
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              )}
            />
          </Grid>
          
          <Grid item xs={12} md={2}>
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <CompareIcon sx={{ fontSize: 32, color: 'text.secondary' }} />
            </Box>
          </Grid>
          
          <Grid item xs={12} md={5}>
            <Autocomplete
              value={selectedManager2}
              onChange={handleManager2Change}
              options={managers}
              getOptionLabel={(option) => `${option.name} - ${option.teamName}`}
              getOptionDisabled={(option) => option.id === selectedManager1?.id}
              renderOption={(props, option) => (
                <Box component="li" {...props} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ width: 32, height: 32, fontSize: 14 }}>
                    {option.avatar}
                  </Avatar>
                  <Box>
                    <Typography variant="body1">{option.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.teamName} • Rank #{option.rank}
                    </Typography>
                  </Box>
                </Box>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Manager 2"
                  placeholder="Search for a manager..."
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              )}
            />
          </Grid>
        </Grid>
        
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
            Quick Select:
          </Typography>
          <Chip
            label="Top 2"
            onClick={() => handleQuickSelect('top2')}
            clickable
            size="small"
            color="primary"
            variant="outlined"
          />
          <Chip
            label="Top vs Bottom"
            onClick={() => handleQuickSelect('topBottom')}
            clickable
            size="small"
            color="secondary"
            variant="outlined"
          />
          <Chip
            label="Closest Rivals"
            onClick={() => handleQuickSelect('rivals')}
            clickable
            size="small"
            color="success"
            variant="outlined"
          />
        </Box>
        
        {selectedManager1 && selectedManager2 && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Selected for Analysis:
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip
                avatar={<Avatar>{selectedManager1.avatar}</Avatar>}
                label={`${selectedManager1.name} (Rank #${selectedManager1.rank})`}
                color="primary"
              />
              <Typography variant="body2">vs</Typography>
              <Chip
                avatar={<Avatar>{selectedManager2.avatar}</Avatar>}
                label={`${selectedManager2.name} (Rank #${selectedManager2.rank})`}
                color="secondary"
              />
            </Box>
          </Box>
        )}
      </Box>
    </GlassCard>
  );
};

export default AnalyticsManagerSelector;