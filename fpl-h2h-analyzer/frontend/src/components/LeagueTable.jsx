import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Avatar,
  Chip
} from '@mui/material';
import { styled } from '@mui/material/styles';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  '&.MuiTableCell-head': {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    fontWeight: 'bold',
  },
  '&.MuiTableCell-body': {
    fontSize: 14,
  },
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
  },
  '&:hover': {
    backgroundColor: theme.palette.action.selected,
  },
  // Highlight top 3 positions
  '&.position-1': {
    borderLeft: `4px solid ${theme.palette.warning.main}`, // Gold
  },
  '&.position-2': {
    borderLeft: `4px solid #C0C0C0`, // Silver
  },
  '&.position-3': {
    borderLeft: `4px solid #CD7F32`, // Bronze
  },
}));

function LeagueTable({ leagueId = 620117 }) {
  const [standings, setStandings] = useState([]);
  const [leagueInfo, setLeagueInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLeagueData();
  }, [leagueId]);

  const fetchLeagueData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/league/${leagueId}/overview`);
      if (!response.ok) {
        throw new Error(`Failed to fetch league data: ${response.status}`);
      }

      const data = await response.json();
      setLeagueInfo(data.standings.league);
      setStandings(data.standings.standings.results || []);
    } catch (err) {
      console.error('Error fetching league data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getPositionColor = (position) => {
    if (position === 1) return 'warning'; // Gold
    if (position === 2) return 'default'; // Silver
    if (position === 3) return 'error'; // Bronze
    return 'default';
  };

  const getPositionClassName = (position) => {
    if (position === 1) return 'position-1';
    if (position === 2) return 'position-2';
    if (position === 3) return 'position-3';
    return '';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading league table...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Error loading league table: {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* League Header */}
      {leagueInfo && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="h5" gutterBottom>
                {leagueInfo.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                H2H League • {standings.length} Managers • Created {new Date(leagueInfo.created).toLocaleDateString()}
              </Typography>
            </Box>
            <Chip 
              label={leagueInfo.closed ? "Season Ended" : "Active"} 
              color={leagueInfo.closed ? "default" : "success"}
              variant="outlined"
            />
          </Box>
        </Paper>
      )}

      {/* Standings Table */}
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="league table">
          <TableHead>
            <TableRow>
              <StyledTableCell>Position</StyledTableCell>
              <StyledTableCell>Manager</StyledTableCell>
              <StyledTableCell>Team Name</StyledTableCell>
              <StyledTableCell align="center">Played</StyledTableCell>
              <StyledTableCell align="center">Won</StyledTableCell>
              <StyledTableCell align="center">Drawn</StyledTableCell>
              <StyledTableCell align="center">Lost</StyledTableCell>
              <StyledTableCell align="center">Points For</StyledTableCell>
              <StyledTableCell align="center">Points Against</StyledTableCell>
              <StyledTableCell align="center">Total</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {standings.map((team, index) => {
              const position = index + 1;
              return (
                <StyledTableRow 
                  key={team.entry} 
                  className={getPositionClassName(position)}
                >
                  <StyledTableCell>
                    <Box display="flex" alignItems="center">
                      <Chip 
                        label={position} 
                        size="small" 
                        color={getPositionColor(position)}
                        sx={{ minWidth: 32, fontWeight: 'bold' }}
                      />
                    </Box>
                  </StyledTableCell>
                  <StyledTableCell>
                    <Box display="flex" alignItems="center">
                      <Avatar sx={{ width: 32, height: 32, mr: 2, fontSize: 14 }}>
                        {team.player_name ? team.player_name.charAt(0).toUpperCase() : 'M'}
                      </Avatar>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {team.player_name || `Manager ${team.entry}`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {team.entry}
                        </Typography>
                      </Box>
                    </Box>
                  </StyledTableCell>
                  <StyledTableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {team.entry_name || 'Unknown Team'}
                    </Typography>
                  </StyledTableCell>
                  <StyledTableCell align="center">{team.matches_played || 0}</StyledTableCell>
                  <StyledTableCell align="center">{team.matches_won || 0}</StyledTableCell>
                  <StyledTableCell align="center">{team.matches_drawn || 0}</StyledTableCell>
                  <StyledTableCell align="center">{team.matches_lost || 0}</StyledTableCell>
                  <StyledTableCell align="center">{team.points_for || 0}</StyledTableCell>
                  <StyledTableCell align="center">{team.points_against || 0}</StyledTableCell>
                  <StyledTableCell align="center">
                    <Typography variant="body2" fontWeight="bold" color="primary">
                      {team.total || 0}
                    </Typography>
                  </StyledTableCell>
                </StyledTableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {standings.length === 0 && (
        <Box textAlign="center" py={6}>
          <Typography variant="h6" color="text.secondary">
            No standings data available
          </Typography>
        </Box>
      )}
    </Box>
  );
}

export default LeagueTable;