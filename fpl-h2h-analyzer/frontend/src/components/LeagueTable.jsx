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
  Chip,
  Badge
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { motion, AnimatePresence } from 'framer-motion';
import { EmojiEvents, TrendingUp, TrendingDown, Remove } from '@mui/icons-material';
import { GlassCard, AnimatedNumber, glassMixins } from './modern';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  '&.MuiTableCell-head': {
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    color: '#fff',
    fontWeight: 600,
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '16px',
    fontSize: '0.875rem',
    letterSpacing: '0.5px',
    textTransform: 'uppercase',
  },
  '&.MuiTableCell-body': {
    fontSize: 14,
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
    padding: '12px 16px',
    color: 'rgba(255, 255, 255, 0.9)',
  },
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  position: 'relative',
  transition: 'all 0.3s ease',
  background: 'transparent',
  '&:hover': {
    background: 'rgba(255, 255, 255, 0.03)',
    transform: 'translateX(4px)',
    '& .rank-badge': {
      transform: 'scale(1.1)',
    }
  },
  // Highlight top 3 positions with gradient borders
  '&.position-1': {
    '&::before': {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      width: '4px',
      background: 'linear-gradient(180deg, #FFD700 0%, #FFA500 100%)', // Gold gradient
      borderRadius: '0 4px 4px 0',
    }
  },
  '&.position-2': {
    '&::before': {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      width: '4px',
      background: 'linear-gradient(180deg, #E5E5E5 0%, #B8B8B8 100%)', // Silver gradient
      borderRadius: '0 4px 4px 0',
    }
  },
  '&.position-3': {
    '&::before': {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      width: '4px',
      background: 'linear-gradient(180deg, #CD7F32 0%, #A0522D 100%)', // Bronze gradient
      borderRadius: '0 4px 4px 0',
    }
  },
}));

// Animation variants
const tableVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
  }
};

const rowVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: { 
    opacity: 1, 
    x: 0,
    transition: {
      type: 'spring',
      stiffness: 100
    }
  }
};

// Position badge component
const PositionBadge = ({ rank }) => {
  const getColor = () => {
    if (rank === 1) return 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)';
    if (rank === 2) return 'linear-gradient(135deg, #E5E5E5 0%, #B8B8B8 100%)';
    if (rank === 3) return 'linear-gradient(135deg, #CD7F32 0%, #A0522D 100%)';
    return 'rgba(255, 255, 255, 0.1)';
  };

  const getIcon = () => {
    if (rank <= 3) return <EmojiEvents sx={{ fontSize: 16 }} />;
    return null;
  };

  return (
    <Box
      className="rank-badge"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 40,
        height: 32,
        background: getColor(),
        borderRadius: '16px',
        color: rank <= 3 ? '#000' : '#fff',
        fontWeight: 700,
        fontSize: '0.875rem',
        gap: 0.5,
        px: 1.5,
        transition: 'transform 0.3s ease',
      }}
    >
      {getIcon()}
      {rank}
    </Box>
  );
};

// Movement indicator
const MovementIndicator = ({ movement }) => {
  if (movement === 0) return <Remove sx={{ color: 'rgba(255, 255, 255, 0.3)', fontSize: 16 }} />;
  if (movement > 0) return (
    <Box sx={{ display: 'flex', alignItems: 'center', color: '#00ff88' }}>
      <TrendingUp sx={{ fontSize: 16 }} />
      <Typography variant="caption" sx={{ ml: 0.5 }}>{movement}</Typography>
    </Box>
  );
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', color: '#ff4757' }}>
      <TrendingDown sx={{ fontSize: 16 }} />
      <Typography variant="caption" sx={{ ml: 0.5 }}>{Math.abs(movement)}</Typography>
    </Box>
  );
};

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
      console.log('[LeagueTable] API response:', data);
      console.log('[LeagueTable] Standings data:', data.standings?.standings?.results);
      console.log('[LeagueTable] First team PA:', data.standings?.standings?.results?.[0]?.points_against);
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* League Header with Glassmorphism */}
      {leagueInfo && (
        <GlassCard 
          variant="elevated"
          gradient="linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)"
          sx={{ mb: 3 }}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography 
                variant="h5" 
                sx={{ 
                  fontWeight: 700,
                  mb: 1,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                {leagueInfo.name}
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Chip 
                  label={`H2H League`}
                  size="small"
                  sx={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: '#fff',
                    fontWeight: 500
                  }}
                />
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                  {standings.length} Managers
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
                  Created {new Date(leagueInfo.created).toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
            <Chip 
              icon={leagueInfo.closed ? null : <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: '#00ff88', mr: 0.5 }} />}
              label={leagueInfo.closed ? "Season Ended" : "Active"} 
              sx={{
                background: leagueInfo.closed ? 
                  'rgba(255, 255, 255, 0.1)' : 
                  'linear-gradient(135deg, rgba(0, 255, 136, 0.2) 0%, rgba(0, 212, 170, 0.2) 100%)',
                border: '1px solid',
                borderColor: leagueInfo.closed ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 255, 136, 0.3)',
                color: leagueInfo.closed ? 'rgba(255, 255, 255, 0.7)' : '#00ff88',
                fontWeight: 600,
                letterSpacing: '0.5px'
              }}
            />
          </Box>
        </GlassCard>
      )}

      {/* Standings Table with Glassmorphism */}
      <GlassCard sx={{ overflow: 'hidden', p: 0 }}>
        <TableContainer sx={{ ...glassMixins.glass, background: 'transparent' }}>
          <Table sx={{ minWidth: 650 }} aria-label="league table">
            <TableHead>
              <TableRow>
                <StyledTableCell width="100">Rank</StyledTableCell>
                <StyledTableCell>Manager</StyledTableCell>
                <StyledTableCell>Team Name</StyledTableCell>
                <StyledTableCell align="center">P</StyledTableCell>
                <StyledTableCell align="center">W</StyledTableCell>
                <StyledTableCell align="center">D</StyledTableCell>
                <StyledTableCell align="center">L</StyledTableCell>
                <StyledTableCell align="center">PF</StyledTableCell>
                <StyledTableCell align="center">PA</StyledTableCell>
                <StyledTableCell align="center">Pts</StyledTableCell>
              </TableRow>
            </TableHead>
            <motion.tbody
              variants={tableVariants}
              initial="hidden"
              animate="visible"
            >
              {standings.map((team, index) => {
                const position = index + 1;
                const previousPosition = team.last_rank || position;
                const movement = previousPosition - position;
                
                return (
                  <motion.tr
                    key={team.entry}
                    variants={rowVariants}
                    component={StyledTableRow}
                    className={getPositionClassName(position)}
                  >
                    <StyledTableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <PositionBadge rank={position} />
                        <MovementIndicator movement={movement} />
                      </Box>
                    </StyledTableCell>
                    <StyledTableCell>
                      <Box display="flex" alignItems="center">
                        <Badge
                          overlap="circular"
                          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                          badgeContent={
                            position <= 3 ? 
                            <Box sx={{ 
                              width: 12, 
                              height: 12, 
                              borderRadius: '50%',
                              background: position === 1 ? '#FFD700' : position === 2 ? '#C0C0C0' : '#CD7F32',
                              border: '2px solid rgba(0, 0, 0, 0.2)'
                            }} /> : null
                          }
                        >
                          <Avatar 
                            sx={{ 
                              width: 40, 
                              height: 40, 
                              mr: 2, 
                              fontSize: 16,
                              background: `linear-gradient(135deg, ${
                                position === 1 ? '#FFD700 0%, #FFA500 100%' :
                                position === 2 ? '#E5E5E5 0%, #B8B8B8 100%' :
                                position === 3 ? '#CD7F32 0%, #A0522D 100%' :
                                'rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%'
                              })`,
                              fontWeight: 700,
                              color: position <= 3 ? '#000' : '#fff'
                            }}
                          >
                            {team.player_name ? team.player_name.charAt(0).toUpperCase() : 'M'}
                          </Avatar>
                        </Badge>
                        <Box>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontWeight: 600,
                              color: '#fff'
                            }}
                          >
                            {team.player_name || `Manager ${team.entry}`}
                          </Typography>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              color: 'rgba(255, 255, 255, 0.5)',
                              fontSize: '0.7rem'
                            }}
                          >
                            ID: {team.entry}
                          </Typography>
                        </Box>
                      </Box>
                    </StyledTableCell>
                    <StyledTableCell>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: 500,
                          color: 'rgba(255, 255, 255, 0.9)'
                        }}
                      >
                        {team.entry_name || 'Unknown Team'}
                      </Typography>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <AnimatedNumber value={team.matches_played || 0} format="number" />
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Box sx={{ color: '#00ff88' }}>
                        <AnimatedNumber value={team.matches_won || 0} format="number" />
                      </Box>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Box sx={{ color: '#ffd93d' }}>
                        <AnimatedNumber value={team.matches_drawn || 0} format="number" />
                      </Box>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Box sx={{ color: '#ff4757' }}>
                        <AnimatedNumber value={team.matches_lost || 0} format="number" />
                      </Box>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <AnimatedNumber value={team.points_for || 0} format="number" />
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <AnimatedNumber value={team.points_against || 0} format="number" />
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Box
                        sx={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          minWidth: 48,
                          height: 32,
                          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
                          borderRadius: '16px',
                          fontWeight: 700,
                          fontSize: '0.875rem',
                          color: '#fff',
                          border: '1px solid rgba(255, 255, 255, 0.1)'
                        }}
                      >
                        {team.total || 0}
                      </Box>
                    </StyledTableCell>
                  </motion.tr>
                );
              })}
            </motion.tbody>
          </Table>
        </TableContainer>
      </GlassCard>

      {standings.length === 0 && (
        <GlassCard>
          <Box textAlign="center" py={6}>
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.5)',
                fontWeight: 500
              }}
            >
              No standings data available
            </Typography>
          </Box>
        </GlassCard>
      )}
    </motion.div>
  );
}

export default LeagueTable;