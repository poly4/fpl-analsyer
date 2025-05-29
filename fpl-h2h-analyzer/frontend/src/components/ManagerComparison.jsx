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
  Badge
} from '@mui/material';
import {
  EmojiEvents,
  SwapHoriz,
  TrendingUp,
  SportsSoccer,
  Timeline,
  Shield,
  Star,
  LocalFireDepartment
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { fplApi } from '../services/api';
import { H2HComparisonSkeleton } from './Skeletons';
import { useOptimizedAPI } from '../hooks/useOptimizedAPI';
import cacheService from '../services/cache';

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
      id={`comparison-tabpanel-${index}`}
      aria-labelledby={`comparison-tab-${index}`}
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

function ManagerComparison({ manager1, manager2, leagueId }) {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [battleData, setBattleData] = useState(null);
  const [manager1Info, setManager1Info] = useState(null);
  const [manager2Info, setManager2Info] = useState(null);

  useEffect(() => {
    fetchComparisonData();
  }, [manager1, manager2]);

  const fetchComparisonData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check cache first
      const cacheKey = `h2h_comparison_${manager1.entry}_${manager2.entry}`;
      const cached = cacheService.get(cacheKey);
      
      if (cached) {
        setBattleData(cached.battle);
        setManager1Info(cached.m1Info);
        setManager2Info(cached.m2Info);
        setLoading(false);
        return;
      }

      // Fetch battle analysis and manager details in parallel
      const [battle, m1Info, m2Info] = await Promise.all([
        fplApi.getBattleDetails(manager1.entry, manager2.entry),
        fplApi.getManagerInfo(manager1.entry),
        fplApi.getManagerInfo(manager2.entry)
      ]);
      
      setBattleData(battle);
      setManager1Info(m1Info);
      setManager2Info(m2Info);
      
      // Cache the results
      cacheService.set(cacheKey, {
        battle,
        m1Info,
        m2Info
      }, 'h2h_analytics');

    } catch (err) {
      console.error('Error fetching comparison data:', err);
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
      {/* Modern Battle Summary with Glassmorphism */}
      <GlassCard 
        variant="elevated" 
        gradient="linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)"
        sx={{ mb: 3 }}
      >
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Chip 
            label={`GAMEWEEK ${battleData.gameweek}`}
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
                      boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)'
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
                    background: manager1Winning && !isDraw ? 
                      'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)' : 
                      'inherit',
                    WebkitBackgroundClip: manager1Winning && !isDraw ? 'text' : 'inherit',
                    WebkitTextFillColor: manager1Winning && !isDraw ? 'transparent' : 'inherit',
                    backgroundClip: manager1Winning && !isDraw ? 'text' : 'inherit',
                  }}
                >
                  {manager1.player_name}
                </Typography>
                
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.7)',
                    mb: 2 
                  }}
                >
                  {manager1.entry_name}
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
                
                {battleData.manager1?.score?.chip && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.3, type: 'spring' }}
                  >
                    <Chip 
                      icon={<LocalFireDepartment />}
                      label={battleData.manager1.score.chip.toUpperCase()} 
                      size="small" 
                      sx={{ 
                        mt: 2,
                        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        color: '#fff',
                        fontWeight: 600,
                        '& .MuiChip-icon': {
                          color: '#fff'
                        }
                      }}
                    />
                  </motion.div>
                )}
              </Box>
            </motion.div>
          </Grid>
          
          <Grid item xs={12} md={2}>
            <Box textAlign="center">
              <motion.div
                animate={{ 
                  rotate: [0, 180, 360],
                  transition: { duration: 2, repeat: Infinity, ease: "linear" }
                }}
                style={{ display: 'inline-block' }}
              >
                <SwapHoriz 
                  sx={{ 
                    fontSize: 40, 
                    color: 'rgba(255, 255, 255, 0.3)',
                    mb: 1
                  }} 
                />
              </motion.div>
              
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
                <Typography 
                  variant="body1" 
                  sx={{ 
                    color: '#ffd93d',
                    fontWeight: 600
                  }}
                >
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
                      boxShadow: '0 8px 32px rgba(240, 147, 251, 0.3)'
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
                    background: !manager1Winning && !isDraw ? 
                      'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)' : 
                      'inherit',
                    WebkitBackgroundClip: !manager1Winning && !isDraw ? 'text' : 'inherit',
                    WebkitTextFillColor: !manager1Winning && !isDraw ? 'transparent' : 'inherit',
                    backgroundClip: !manager1Winning && !isDraw ? 'text' : 'inherit',
                  }}
                >
                  {manager2.player_name}
                </Typography>
                
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.7)',
                    mb: 2 
                  }}
                >
                  {manager2.entry_name}
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
                
                {battleData.manager2?.score?.chip && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.3, type: 'spring' }}
                  >
                    <Chip 
                      icon={<LocalFireDepartment />}
                      label={battleData.manager2.score.chip.toUpperCase()} 
                      size="small" 
                      sx={{ 
                        mt: 2,
                        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        color: '#fff',
                        fontWeight: 600,
                        '& .MuiChip-icon': {
                          color: '#fff'
                        }
                      }}
                    />
                  </motion.div>
                )}
              </Box>
            </motion.div>
          </Grid>
        </Grid>
      </GlassCard>

      {/* Detailed Comparison Tabs with Glassmorphism */}
      <GlassCard sx={{ width: '100%' }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="fullWidth"
          sx={{
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            '& .MuiTab-root': {
              color: 'rgba(255, 255, 255, 0.7)',
              transition: 'all 0.3s ease',
              '&:hover': {
                color: '#fff',
                background: 'rgba(255, 255, 255, 0.05)'
              }
            },
            '& .Mui-selected': {
              color: '#fff !important',
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
            },
            '& .MuiTabs-indicator': {
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              height: 3,
              borderRadius: '3px 3px 0 0'
            }
          }}
        >
          <Tab icon={<EmojiEvents />} label="Head to Head" />
          <Tab icon={<SportsSoccer />} label="Squad Comparison" />
          <Tab icon={<SwapHoriz />} label="Transfer Analysis" />
          <Tab icon={<Timeline />} label="Performance Trends" />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <motion.div variants={cardVariants}>
                <GlassCard>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 600,
                      mb: 3,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}
                  >
                    Overall H2H Record
                  </Typography>
                  
                  <Box display="flex" justifyContent="space-around" gap={2}>
                    <StatBox
                      title={`${manager1.player_name} Wins`}
                      value={manager1.matches_won}
                      variant="success"
                      icon={<EmojiEvents />}
                      size="small"
                    />
                    <StatBox
                      title="Draws"
                      value={manager1.matches_drawn}
                      variant="warning"
                      icon={<SwapHoriz />}
                      size="small"
                    />
                    <StatBox
                      title={`${manager2.player_name} Wins`}
                      value={manager1.matches_lost}
                      variant="error"
                      icon={<EmojiEvents />}
                      size="small"
                    />
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <motion.div variants={cardVariants}>
                <GlassCard>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 600,
                      mb: 3,
                      background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}
                  >
                    Season Performance
                  </Typography>
                  
                  <List dense sx={{ '& .MuiListItem-root': { px: 2, py: 1.5, borderRadius: 2, mb: 1, background: 'rgba(255, 255, 255, 0.02)' } }}>
                    <ListItem>
                      <ListItemText 
                        primary={
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', mb: 0.5 }}>
                            League Position
                          </Typography>
                        }
                        secondary={
                          <Box display="flex" gap={2}>
                            <Chip 
                              label={`${manager1.player_name}: #${manager1.rank}`}
                              size="small"
                              sx={{ 
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                color: '#fff',
                                fontWeight: 600
                              }}
                            />
                            <Chip 
                              label={`${manager2.player_name}: #${manager2.rank}`}
                              size="small"
                              sx={{ 
                                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                                color: '#fff',
                                fontWeight: 600
                              }}
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', mb: 0.5 }}>
                            Total Points (H2H)
                          </Typography>
                        }
                        secondary={
                          <Box display="flex" gap={2} mt={1}>
                            <Box>
                              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
                                {manager1.player_name}
                              </Typography>
                              <AnimatedNumber value={manager1.total} format="number" />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
                                {manager2.player_name}
                              </Typography>
                              <AnimatedNumber value={manager2.total} format="number" />
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', mb: 0.5 }}>
                            Points For
                          </Typography>
                        }
                        secondary={
                          <Box display="flex" gap={2} mt={1}>
                            <Box>
                              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
                                {manager1.player_name}
                              </Typography>
                              <AnimatedNumber value={manager1.points_for} format="number" />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
                                {manager2.player_name}
                              </Typography>
                              <AnimatedNumber value={manager2.points_for} format="number" />
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  </List>
                </GlassCard>
              </motion.div>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <motion.div variants={cardVariants}>
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 600,
                mb: 3,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              Differential Players
            </Typography>
            
            {battleData.differentials && battleData.differentials.length > 0 ? (
              <ModernTable
                columns={[
                  { id: 'name', label: 'Player', sortable: true },
                  { id: 'team', label: 'Team', sortable: true },
                  { id: 'owner', label: 'Owned By', sortable: false },
                  { id: 'points', label: 'Points', align: 'right', sortable: true }
                ]}
                data={battleData.differentials.map((diff, index) => ({
                  id: index,
                  name: diff.name || `Player ${diff.player_id}`,
                  team: diff.team || 'Unknown',
                  owner: (
                    <Chip 
                      label={diff.owner === manager1.entry ? manager1.player_name : manager2.player_name}
                      size="small"
                      sx={{
                        background: diff.owner === manager1.entry ? 
                          'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 
                          'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        color: '#fff',
                        fontWeight: 600
                      }}
                    />
                  ),
                  points: (
                    <AnimatedNumber 
                      value={diff.points} 
                      format="number"
                      sx={{ fontWeight: 700, fontSize: '1.1rem' }}
                    />
                  )
                }))}
                defaultSort={{ column: 'points', direction: 'desc' }}
              />
            ) : (
              <GlassCard>
                <Typography 
                  variant="body1" 
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.5)',
                    textAlign: 'center',
                    py: 4
                  }}
                >
                  No differential players in current gameweek
                </Typography>
              </GlassCard>
            )}
          </motion.div>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Recent Transfers
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {manager1.player_name}
                  </Typography>
                  {battleData.manager1?.transfers ? (
                    <List dense>
                      {battleData.manager1.transfers.slice(0, 5).map((transfer, idx) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={`GW${transfer.gameweek}: ${transfer.player_out_name} → ${transfer.player_in_name}`}
                            secondary={`Cost: ${transfer.cost || 0}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No recent transfers
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {manager2.player_name}
                  </Typography>
                  {battleData.manager2?.transfers ? (
                    <List dense>
                      {battleData.manager2.transfers.slice(0, 5).map((transfer, idx) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={`GW${transfer.gameweek}: ${transfer.player_out_name} → ${transfer.player_in_name}`}
                            secondary={`Cost: ${transfer.cost || 0}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No recent transfers
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Season Performance Metrics
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            {[
              { label: 'Average Points', m1: manager1.points_for ? (manager1.points_for / manager1.matches_played).toFixed(1) : 'N/A', m2: manager2.points_for ? (manager2.points_for / manager2.matches_played).toFixed(1) : 'N/A' },
              { label: 'Win Rate', m1: manager1.matches_played ? `${((manager1.matches_won / manager1.matches_played) * 100).toFixed(0)}%` : 'N/A', m2: manager2.matches_played ? `${((manager2.matches_won / manager2.matches_played) * 100).toFixed(0)}%` : 'N/A' },
              { label: 'Total Matches', m1: manager1.matches_played, m2: manager2.matches_played },
            ].map((metric, idx) => (
              <Grid item xs={12} key={idx}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {metric.label}
                  </Typography>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="h6">{manager1.player_name}: {metric.m1}</Typography>
                    <Typography variant="h6">{manager2.player_name}: {metric.m2}</Typography>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
      </GlassCard>
    </motion.div>
  );
}

export default ManagerComparison;