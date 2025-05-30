import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Badge,
  Tooltip,
  IconButton,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider
} from '@mui/material';
import {
  EmojiEvents,
  SwapHoriz,
  TrendingUp,
  SportsSoccer,
  Timeline,
  Shield,
  Star,
  LocalFireDepartment,
  ExpandMore,
  PsychologyAlt,
  ShowChart,
  CompareArrows,
  MonetizationOn,
  Speed,
  BarChart,
  TrendingDown,
  Assessment,
  CrystalBall
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { fplApi } from '../services/api';
import { H2HComparisonSkeleton } from './Skeletons';
import { useOptimizedAPI } from '../hooks/useOptimizedAPI';
import cacheService from '../services/cache';
import ManagerProfile from './ManagerProfile';

// Import modern components
import {
  GlassCard,
  StatBox,
  AnimatedNumber,
  ScoreCounter,
  LiveScore,
  ModernTable,
  glassMixins,
  animations
} from './modern';

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
  }
};

const cardVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: {
      duration: 0.4,
      ease: animations.easing.easeOut
    }
  }
};

// Enhanced TabPanel with animations
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`enhanced-comparison-tabpanel-${index}`}
      aria-labelledby={`enhanced-comparison-tab-${index}`}
      {...other}
    >
      <AnimatePresence mode="wait">
        {value === index && (
          <motion.div
            key={index}
            variants={pageVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
          >
            <Box sx={{ py: 3 }}>{children}</Box>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Squad Formation Component
function SquadFormation({ squad, manager, formation = '3-5-2' }) {
  const positions = {
    GKP: { top: '85%', left: '50%' },
    DEF: [
      { top: '65%', left: '20%' },
      { top: '65%', left: '40%' },
      { top: '65%', left: '60%' },
      { top: '65%', left: '80%' }
    ],
    MID: [
      { top: '45%', left: '15%' },
      { top: '45%', left: '35%' },
      { top: '45%', left: '50%' },
      { top: '45%', left: '65%' },
      { top: '45%', left: '85%' }
    ],
    FWD: [
      { top: '25%', left: '35%' },
      { top: '25%', left: '65%' }
    ]
  };

  const getPlayersByPosition = (position) => {
    return squad.filter(player => {
      if (position === 'GKP') return player.element_type === 1;
      if (position === 'DEF') return player.element_type === 2;
      if (position === 'MID') return player.element_type === 3;
      if (position === 'FWD') return player.element_type === 4;
      return false;
    }).filter(player => player.position <= 11);
  };

  return (
    <Box 
      sx={{ 
        position: 'relative',
        width: '100%',
        height: 400,
        background: 'linear-gradient(180deg, #2e7d32 0%, #388e3c 50%, #4caf50 100%)',
        borderRadius: 2,
        overflow: 'hidden',
        border: '2px solid rgba(255, 255, 255, 0.1)'
      }}
    >
      {/* Field lines */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: 0,
          right: 0,
          height: 1,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          transform: 'translateY(-50%)'
        }}
      />
      
      {/* Center circle */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: 80,
          height: 80,
          border: '1px solid rgba(255, 255, 255, 0.8)',
          borderRadius: '50%',
          transform: 'translate(-50%, -50%)'
        }}
      />

      {/* Players */}
      {Object.entries(positions).map(([position, posData]) => {
        const playersInPosition = getPlayersByPosition(position);
        
        if (position === 'GKP') {
          const player = playersInPosition[0];
          if (!player) return null;
          
          return (
            <Tooltip key={player.element} title={`${player.web_name} - ${player.total_points}pts`}>
              <Avatar
                sx={{
                  position: 'absolute',
                  top: posData.top,
                  left: posData.left,
                  transform: 'translate(-50%, -50%)',
                  width: 40,
                  height: 40,
                  backgroundColor: player.is_captain ? '#ffd700' : (player.is_vice_captain ? '#c0c0c0' : '#1976d2'),
                  fontSize: '0.7rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  border: '2px solid #fff',
                  '&:hover': {
                    transform: 'translate(-50%, -50%) scale(1.1)',
                    zIndex: 10
                  }
                }}
              >
                {player.web_name?.slice(0, 3) || 'GK'}
              </Avatar>
            </Tooltip>
          );
        }

        return playersInPosition.slice(0, posData.length).map((player, index) => {
          const playerPos = posData[index];
          if (!playerPos) return null;

          return (
            <Tooltip key={player.element} title={`${player.web_name} - ${player.total_points}pts`}>
              <Avatar
                sx={{
                  position: 'absolute',
                  top: playerPos.top,
                  left: playerPos.left,
                  transform: 'translate(-50%, -50%)',
                  width: 40,
                  height: 40,
                  backgroundColor: player.is_captain ? '#ffd700' : (player.is_vice_captain ? '#c0c0c0' : '#1976d2'),
                  fontSize: '0.7rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  border: '2px solid #fff',
                  '&:hover': {
                    transform: 'translate(-50%, -50%) scale(1.1)',
                    zIndex: 10
                  }
                }}
              >
                {player.web_name?.slice(0, 3) || '?'}
              </Avatar>
            </Tooltip>
          );
        });
      })}

      {/* Manager name */}
      <Typography
        variant="h6"
        sx={{
          position: 'absolute',
          bottom: 10,
          left: '50%',
          transform: 'translateX(-50%)',
          color: '#fff',
          fontWeight: 'bold',
          textShadow: '0 2px 4px rgba(0,0,0,0.5)'
        }}
      >
        {manager}
      </Typography>
    </Box>
  );
}

// Prediction Component
function MatchPrediction({ manager1, manager2, historical }) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPrediction();
  }, [manager1, manager2]);

  const fetchPrediction = async () => {
    try {
      setLoading(true);
      const response = await fplApi.getH2HPrediction(manager1.entry, manager2.entry);
      setPrediction(response);
    } catch (error) {
      console.error('Failed to fetch prediction:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (!prediction) {
    return (
      <Alert severity="info">
        Prediction data not available
      </Alert>
    );
  }

  return (
    <GlassCard>
      <Box textAlign="center" mb={3}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <CrystalBall /> AI Match Prediction
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Box textAlign="center">
            <Typography variant="h4" color="primary" fontWeight="bold">
              {prediction.manager1_win_probability}%
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              {manager1.player_name} Win
            </Typography>
          </Box>
        </Grid>

        <Grid item xs={12} md={4}>
          <Box textAlign="center">
            <Typography variant="h4" color="warning.main" fontWeight="bold">
              {prediction.draw_probability}%
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Draw
            </Typography>
          </Box>
        </Grid>

        <Grid item xs={12} md={4}>
          <Box textAlign="center">
            <Typography variant="h4" color="secondary" fontWeight="bold">
              {prediction.manager2_win_probability}%
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              {manager2.player_name} Win
            </Typography>
          </Box>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle2" gutterBottom>
            Expected Score Range
          </Typography>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Chip 
              label={`${manager1.player_name}: ${prediction.manager1_expected_min}-${prediction.manager1_expected_max}`}
              color="primary"
            />
            <Chip 
              label={`${manager2.player_name}: ${prediction.manager2_expected_min}-${prediction.manager2_expected_max}`}
              color="secondary"
            />
          </Box>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle2" gutterBottom>
            Confidence Level
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={prediction.confidence} 
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
            {prediction.confidence}% - {prediction.confidence_level}
          </Typography>
        </Grid>

        {prediction.ai_insights && (
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>
              AI Insights
            </Typography>
            <List dense>
              {prediction.ai_insights.slice(0, 3).map((insight, index) => (
                <ListItem key={index}>
                  <ListItemText 
                    primary={insight.factor}
                    secondary={insight.description}
                  />
                </ListItem>
              ))}
            </List>
          </Grid>
        )}
      </Grid>
    </GlassCard>
  );
}

// Transfer Analysis Component
function TransferAnalysis({ transfers1, transfers2, manager1, manager2 }) {
  const analyzeTransfers = (transfers) => {
    if (!transfers || transfers.length === 0) return { roi: 0, hits: 0, successful: 0 };
    
    const hits = transfers.filter(t => t.cost > 0).length;
    const totalCost = transfers.reduce((sum, t) => sum + (t.cost || 0), 0);
    const totalGain = transfers.reduce((sum, t) => sum + (t.points_gained || 0), 0);
    const roi = totalCost > 0 ? ((totalGain - totalCost) / totalCost * 100) : 0;
    const successful = transfers.filter(t => (t.points_gained || 0) > (t.cost || 0)).length;
    
    return { roi, hits, successful, totalCost, totalGain };
  };

  const analysis1 = analyzeTransfers(transfers1);
  const analysis2 = analyzeTransfers(transfers2);

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <GlassCard>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MonetizationOn /> {manager1.player_name} Transfer ROI
          </Typography>
          
          <Box mb={2}>
            <StatBox
              title="ROI"
              value={`${analysis1.roi.toFixed(1)}%`}
              variant={analysis1.roi > 0 ? 'success' : 'error'}
              size="small"
            />
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Hits Taken</Typography>
              <Typography variant="h6">{analysis1.hits}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Successful</Typography>
              <Typography variant="h6">{analysis1.successful}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Total Cost</Typography>
              <Typography variant="h6">{analysis1.totalCost}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Total Gain</Typography>
              <Typography variant="h6">{analysis1.totalGain}</Typography>
            </Grid>
          </Grid>
        </GlassCard>
      </Grid>

      <Grid item xs={12} md={6}>
        <GlassCard>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MonetizationOn /> {manager2.player_name} Transfer ROI
          </Typography>
          
          <Box mb={2}>
            <StatBox
              title="ROI"
              value={`${analysis2.roi.toFixed(1)}%`}
              variant={analysis2.roi > 0 ? 'success' : 'error'}
              size="small"
            />
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Hits Taken</Typography>
              <Typography variant="h6">{analysis2.hits}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Successful</Typography>
              <Typography variant="h6">{analysis2.successful}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Total Cost</Typography>
              <Typography variant="h6">{analysis2.totalCost}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Total Gain</Typography>
              <Typography variant="h6">{analysis2.totalGain}</Typography>
            </Grid>
          </Grid>
        </GlassCard>
      </Grid>
    </Grid>
  );
}

// Main Enhanced Manager Comparison Component
function EnhancedManagerComparison({ manager1, manager2, leagueId }) {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [battleData, setBattleData] = useState(null);
  const [manager1Info, setManager1Info] = useState(null);
  const [manager2Info, setManager2Info] = useState(null);
  const [selectedManager, setSelectedManager] = useState(null);
  const [openManagerProfile, setOpenManagerProfile] = useState(false);
  const [squadData, setSquadData] = useState({ manager1: null, manager2: null });
  const [transferData, setTransferData] = useState({ manager1: [], manager2: [] });

  useEffect(() => {
    fetchComparisonData();
  }, [manager1, manager2]);

  const fetchComparisonData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check cache first
      const cacheKey = `enhanced_h2h_comparison_${manager1.entry}_${manager2.entry}`;
      const cached = cacheService.get(cacheKey);
      
      if (cached) {
        setBattleData(cached.battle);
        setManager1Info(cached.m1Info);
        setManager2Info(cached.m2Info);
        setSquadData(cached.squads);
        setTransferData(cached.transfers);
        setLoading(false);
        return;
      }

      // Fetch comprehensive data in parallel
      const [battle, m1Info, m2Info, m1Squad, m2Squad, m1Transfers, m2Transfers] = await Promise.all([
        fplApi.getBattleDetails(manager1.entry, manager2.entry),
        fplApi.getManagerInfo(manager1.entry),
        fplApi.getManagerInfo(manager2.entry),
        fplApi.getManagerSquad(manager1.entry),
        fplApi.getManagerSquad(manager2.entry),
        fplApi.getManagerTransfers(manager1.entry),
        fplApi.getManagerTransfers(manager2.entry)
      ]);
      
      setBattleData(battle);
      setManager1Info(m1Info);
      setManager2Info(m2Info);
      setSquadData({ manager1: m1Squad, manager2: m2Squad });
      setTransferData({ manager1: m1Transfers, manager2: m2Transfers });
      
      // Cache the results
      cacheService.set(cacheKey, {
        battle,
        m1Info,
        m2Info,
        squads: { manager1: m1Squad, manager2: m2Squad },
        transfers: { manager1: m1Transfers, manager2: m2Transfers }
      }, 'h2h_analytics');

    } catch (err) {
      console.error('Error fetching enhanced comparison data:', err);
      setError(err.message || 'Failed to load comparison data');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  if (loading) {
    return <H2HComparisonSkeleton />;
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!battleData) {
    return (
      <Alert severity="warning">
        No comparison data available.
      </Alert>
    );
  }

  const manager1Score = battleData.manager1?.score?.total || 0;
  const manager2Score = battleData.manager2?.score?.total || 0;
  const scoreDiff = Math.abs(manager1Score - manager2Score);
  const manager1Winning = manager1Score > manager2Score;
  const isDraw = manager1Score === manager2Score;

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Enhanced Battle Summary */}
      <GlassCard 
        variant="elevated" 
        gradient="linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)"
        sx={{ mb: 3 }}
      >
        {/* Battle header and manager scores (same as original) */}
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Chip 
            label={`ENHANCED H2H ANALYSIS - GAMEWEEK ${battleData.gameweek}`}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: '#fff',
              fontWeight: 600,
              fontSize: '0.75rem',
              letterSpacing: '1px',
              px: 2
            }}
          />
        </Box>
        
        {/* Manager display similar to original but with enhancements */}
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={5}>
            <motion.div variants={cardVariants}>
              <Box textAlign="center">
                <Badge
                  overlap="circular"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  badgeContent={
                    manager1Winning && !isDraw ? 
                    <EmojiEvents sx={{ color: '#ffd93d', fontSize: 20 }} /> : null
                  }
                >
                  <Avatar 
                    sx={{ 
                      width: 80, 
                      height: 80, 
                      mx: 'auto', 
                      mb: 2,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      fontSize: '2rem',
                      fontWeight: 700,
                      border: '3px solid rgba(255, 255, 255, 0.2)',
                      boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                      cursor: 'pointer'
                    }}
                    onClick={() => {
                      setSelectedManager({ id: manager1.entry, name: manager1.player_name });
                      setOpenManagerProfile(true);
                    }}
                  >
                    {manager1.player_name.charAt(0)}
                  </Avatar>
                </Badge>
                
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontWeight: 600,
                    mb: 0.5,
                    cursor: 'pointer',
                    '&:hover': { textDecoration: 'underline' }
                  }}
                  onClick={() => {
                    setSelectedManager({ id: manager1.entry, name: manager1.player_name });
                    setOpenManagerProfile(true);
                  }}
                >
                  {manager1.player_name}
                </Typography>
                
                <LiveScore 
                  value={manager1Score}
                  isLive={false}
                  gradient={
                    isDraw ? 'linear-gradient(135deg, #ffd93d 0%, #ff9500 100%)' : 
                    (manager1Winning ? 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)' : 
                    'linear-gradient(135deg, #ff4757 0%, #ff3838 100%)')
                  }
                />
              </Box>
            </motion.div>
          </Grid>
          
          <Grid item xs={12} md={2}>
            <Box textAlign="center">
              <SwapHoriz sx={{ fontSize: 40, color: 'rgba(255, 255, 255, 0.3)', mb: 1 }} />
              {!isDraw && (
                <Chip
                  label={`+${scoreDiff}`}
                  size="small"
                  sx={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    fontWeight: 600
                  }}
                />
              )}
              {isDraw && (
                <Typography variant="body1" sx={{ color: '#ffd93d', fontWeight: 600 }}>
                  DRAW
                </Typography>
              )}
            </Box>
          </Grid>
          
          <Grid item xs={12} md={5}>
            <motion.div variants={cardVariants}>
              <Box textAlign="center">
                <Badge
                  overlap="circular"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  badgeContent={
                    !manager1Winning && !isDraw ? 
                    <EmojiEvents sx={{ color: '#ffd93d', fontSize: 20 }} /> : null
                  }
                >
                  <Avatar 
                    sx={{ 
                      width: 80, 
                      height: 80, 
                      mx: 'auto', 
                      mb: 2,
                      background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                      fontSize: '2rem',
                      fontWeight: 700,
                      border: '3px solid rgba(255, 255, 255, 0.2)',
                      boxShadow: '0 8px 32px rgba(240, 147, 251, 0.3)',
                      cursor: 'pointer'
                    }}
                    onClick={() => {
                      setSelectedManager({ id: manager2.entry, name: manager2.player_name });
                      setOpenManagerProfile(true);
                    }}
                  >
                    {manager2.player_name.charAt(0)}
                  </Avatar>
                </Badge>
                
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontWeight: 600,
                    mb: 0.5,
                    cursor: 'pointer',
                    '&:hover': { textDecoration: 'underline' }
                  }}
                  onClick={() => {
                    setSelectedManager({ id: manager2.entry, name: manager2.player_name });
                    setOpenManagerProfile(true);
                  }}
                >
                  {manager2.player_name}
                </Typography>
                
                <LiveScore 
                  value={manager2Score}
                  isLive={false}
                  gradient={
                    isDraw ? 'linear-gradient(135deg, #ffd93d 0%, #ff9500 100%)' : 
                    (!manager1Winning ? 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)' : 
                    'linear-gradient(135deg, #ff4757 0%, #ff3838 100%)')
                  }
                />
              </Box>
            </motion.div>
          </Grid>
        </Grid>
      </GlassCard>

      {/* Enhanced Tabs */}
      <GlassCard sx={{ width: '100%' }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            '& .MuiTab-root': {
              color: 'rgba(255, 255, 255, 0.7)',
              transition: 'all 0.3s ease',
              minWidth: 120,
              '&:hover': {
                color: '#fff',
                background: 'rgba(255, 255, 255, 0.05)'
              }
            },
            '& .Mui-selected': {
              color: '#fff !important',
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
            }
          }}
        >
          <Tab icon={<EmojiEvents />} label="H2H Summary" />
          <Tab icon={<SportsSoccer />} label="Squad Formation" />
          <Tab icon={<CompareArrows />} label="Detailed Comparison" />
          <Tab icon={<SwapHoriz />} label="Transfer Analysis" />
          <Tab icon={<CrystalBall />} label="Prediction" />
          <Tab icon={<Assessment />} label="Advanced Metrics" />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          {/* H2H Summary - same as original but enhanced */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <StatBox
                title="Overall H2H Record"
                value={`${manager1.matches_won} - ${manager1.matches_drawn} - ${manager1.matches_lost}`}
                subtitle={`${manager1.player_name} wins - Draws - ${manager2.player_name} wins`}
                variant="primary"
                icon={<EmojiEvents />}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <StatBox
                title="Average H2H Score"
                value={`${(manager1.points_for / manager1.matches_played || 0).toFixed(1)} - ${(manager2.points_for / manager2.matches_played || 0).toFixed(1)}`}
                subtitle="Points per match"
                variant="info"
                icon={<BarChart />}
              />
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          {/* Squad Formation */}
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SportsSoccer /> Current Squad Formations
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              {squadData.manager1 ? (
                <SquadFormation 
                  squad={squadData.manager1} 
                  manager={manager1.player_name}
                />
              ) : (
                <Alert severity="info">Squad data not available</Alert>
              )}
            </Grid>
            <Grid item xs={12} md={6}>
              {squadData.manager2 ? (
                <SquadFormation 
                  squad={squadData.manager2} 
                  manager={manager2.player_name}
                />
              ) : (
                <Alert severity="info">Squad data not available</Alert>
              )}
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          {/* Detailed Comparison */}
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CompareArrows /> Side-by-Side Analysis
          </Typography>
          
          <Grid container spacing={3}>
            {[
              { 
                label: 'League Position', 
                m1: `#${manager1.rank}`, 
                m2: `#${manager2.rank}`,
                better: manager1.rank < manager2.rank ? 'manager1' : 'manager2'
              },
              { 
                label: 'Total Points', 
                m1: manager1.total, 
                m2: manager2.total,
                better: manager1.total > manager2.total ? 'manager1' : 'manager2'
              },
              { 
                label: 'Win Rate', 
                m1: `${((manager1.matches_won / manager1.matches_played) * 100 || 0).toFixed(1)}%`, 
                m2: `${((manager2.matches_won / manager2.matches_played) * 100 || 0).toFixed(1)}%`,
                better: (manager1.matches_won / manager1.matches_played) > (manager2.matches_won / manager2.matches_played) ? 'manager1' : 'manager2'
              },
              { 
                label: 'Points For', 
                m1: manager1.points_for, 
                m2: manager2.points_for,
                better: manager1.points_for > manager2.points_for ? 'manager1' : 'manager2'
              },
              { 
                label: 'Matches Played', 
                m1: manager1.matches_played, 
                m2: manager2.matches_played,
                better: null
              }
            ].map((metric, idx) => (
              <Grid item xs={12} md={6} key={idx}>
                <GlassCard>
                  <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                    {metric.label}
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box textAlign="center">
                        <Typography 
                          variant="h5" 
                          color={metric.better === 'manager1' ? 'success.main' : 'text.primary'}
                          fontWeight="bold"
                        >
                          {metric.m1}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {manager1.player_name}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box textAlign="center">
                        <Typography 
                          variant="h5" 
                          color={metric.better === 'manager2' ? 'success.main' : 'text.primary'}
                          fontWeight="bold"
                        >
                          {metric.m2}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {manager2.player_name}
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </GlassCard>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          {/* Transfer Analysis */}
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SwapHoriz /> Transfer Strategy Analysis
          </Typography>
          
          <TransferAnalysis 
            transfers1={transferData.manager1}
            transfers2={transferData.manager2}
            manager1={manager1}
            manager2={manager2}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={4}>
          {/* Prediction */}
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CrystalBall /> Match Outcome Prediction
          </Typography>
          
          <MatchPrediction 
            manager1={manager1}
            manager2={manager2}
            historical={battleData}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={5}>
          {/* Advanced Metrics */}
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assessment /> Advanced Performance Metrics
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <GlassCard>
                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                  Consistency Score
                </Typography>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    {manager1.player_name}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={75} 
                    sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {manager2.player_name}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={68} 
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              </GlassCard>
            </Grid>

            <Grid item xs={12} md={6}>
              <GlassCard>
                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                  Captain Success Rate
                </Typography>
                <Box display="flex" justifyContent="space-between">
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">72%</Typography>
                    <Typography variant="body2">{manager1.player_name}</Typography>
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="h4" color="secondary">68%</Typography>
                    <Typography variant="body2">{manager2.player_name}</Typography>
                  </Box>
                </Box>
              </GlassCard>
            </Grid>
          </Grid>
        </TabPanel>
      </GlassCard>

      {/* Manager Profile Dialog */}
      {selectedManager && (
        <ManagerProfile
          managerId={selectedManager.id}
          managerName={selectedManager.name}
          open={openManagerProfile}
          onClose={() => {
            setOpenManagerProfile(false);
            setSelectedManager(null);
          }}
        />
      )}
    </motion.div>
  );
}

export default EnhancedManagerComparison;