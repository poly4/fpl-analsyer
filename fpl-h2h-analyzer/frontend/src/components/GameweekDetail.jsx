import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  IconButton,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
  useTheme,
  useMediaQuery,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Close as CloseIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  Star as CaptainIcon,
  Security as ViceCaptainIcon,
  SwapHoriz as SubIcon,
  SportsSoccer as SoccerIcon,
  Groups as DifferentialIcon,
  LocalFireDepartment as FireIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { GlassCard, StatBox, AnimatedNumber } from './modern';
import { motion, AnimatePresence } from 'framer-motion';
import { useOptimizedAPI } from '../hooks/useOptimizedAPI';

const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`gameweek-tabpanel-${index}`}
    aria-labelledby={`gameweek-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const positionMap = {
  1: 'GKP',
  2: 'DEF',
  3: 'MID',
  4: 'FWD',
};

const PlayerRow = ({ player, isDifferential, isAutosub, setPiece }) => {
  const theme = useTheme();
  
  return (
    <TableRow
      sx={{
        backgroundColor: isAutosub ? 'rgba(255, 152, 0, 0.1)' : 'transparent',
        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.05)' },
      }}
    >
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {player.is_captain && (
            <Tooltip title="Captain">
              <CaptainIcon sx={{ color: '#ffd700', fontSize: 20 }} />
            </Tooltip>
          )}
          {player.is_vice_captain && (
            <Tooltip title="Vice Captain">
              <ViceCaptainIcon sx={{ color: '#c0c0c0', fontSize: 20 }} />
            </Tooltip>
          )}
          <Typography variant="body2">
            {player.element_name || 'Unknown Player'}
          </Typography>
          {isDifferential && (
            <Tooltip title="Differential Pick">
              <DifferentialIcon sx={{ color: theme.palette.primary.main, fontSize: 16 }} />
            </Tooltip>
          )}
          {isAutosub && (
            <Tooltip title="Auto Substitution">
              <SubIcon sx={{ color: theme.palette.warning.main, fontSize: 16 }} />
            </Tooltip>
          )}
          {setPiece && (
            <Tooltip title={`Set Piece: ${setPiece}`}>
              <SportsSoccer sx={{ color: theme.palette.success.main, fontSize: 16 }} />
            </Tooltip>
          )}
        </Box>
      </TableCell>
      <TableCell align="center">
        <Chip
          label={positionMap[player.element_type] || 'N/A'}
          size="small"
          sx={{ minWidth: 45 }}
        />
      </TableCell>
      <TableCell align="center">
        <Typography
          variant="body2"
          sx={{
            fontWeight: player.points > 0 ? 'bold' : 'normal',
            color: player.points > 10 ? 'success.main' : 
                   player.points < 0 ? 'error.main' : 'text.primary',
          }}
        >
          {player.points || 0}
        </Typography>
      </TableCell>
      <TableCell align="center">
        <Typography variant="body2" color="text.secondary">
          £{(player.selling_price / 10).toFixed(1)}m
        </Typography>
      </TableCell>
      <TableCell align="center">
        <Typography variant="body2" color="text.secondary">
          {player.ownership ? `${player.ownership}%` : 'N/A'}
        </Typography>
      </TableCell>
    </TableRow>
  );
};

const GameweekDetail = ({ 
  manager1Id, 
  manager2Id, 
  gameweek, 
  open, 
  onClose,
  manager1Name,
  manager2Name,
}) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  const [tabValue, setTabValue] = useState(0);
  const [currentGW, setCurrentGW] = useState(gameweek);
  const [manager1Data, setManager1Data] = useState(null);
  const [manager2Data, setManager2Data] = useState(null);
  const [bootstrapData, setBootstrapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { request, cache } = useOptimizedAPI();

  useEffect(() => {
    if (open && manager1Id && manager2Id && currentGW) {
      fetchGameweekData();
    }
  }, [open, manager1Id, manager2Id, currentGW]);

  const fetchGameweekData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch bootstrap-static for player ownership data
      const bootstrap = await request('/api/bootstrap-static/');
      setBootstrapData(bootstrap);

      // Fetch both managers' picks for the gameweek
      const [picks1, picks2] = await Promise.all([
        request(`/api/entry/${manager1Id}/event/${currentGW}/picks/`),
        request(`/api/entry/${manager2Id}/event/${currentGW}/picks/`),
      ]);

      // Enhance picks with player data
      const enhancePicks = (picks) => {
        return {
          ...picks,
          picks: picks.picks.map(pick => {
            const player = bootstrap.elements.find(el => el.id === pick.element);
            return {
              ...pick,
              element_name: player ? `${player.first_name} ${player.second_name}` : 'Unknown',
              element_type: player?.element_type,
              ownership: player?.selected_by_percent,
              selling_price: pick.selling_price || player?.now_cost,
            };
          }),
        };
      };

      setManager1Data(enhancePicks(picks1));
      setManager2Data(enhancePicks(picks2));
    } catch (err) {
      console.error('Error fetching gameweek data:', err);
      setError('Failed to load gameweek data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGameweekChange = (direction) => {
    const newGW = currentGW + direction;
    if (newGW >= 1 && newGW <= 38) {
      setCurrentGW(newGW);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const getDifferentialPlayers = () => {
    if (!manager1Data || !manager2Data) return { onlyManager1: [], onlyManager2: [] };

    const manager1Players = new Set(manager1Data.picks.map(p => p.element));
    const manager2Players = new Set(manager2Data.picks.map(p => p.element));

    const onlyManager1 = manager1Data.picks
      .filter(p => !manager2Players.has(p.element))
      .map(p => p.element);
    
    const onlyManager2 = manager2Data.picks
      .filter(p => !manager1Players.has(p.element))
      .map(p => p.element);

    return { onlyManager1, onlyManager2 };
  };

  const calculateMetrics = (data) => {
    if (!data) return null;

    const startingXI = data.picks.slice(0, 11);
    const bench = data.picks.slice(11);
    
    const startingPoints = startingXI.reduce((sum, p) => sum + (p.points || 0), 0);
    const benchPoints = bench.reduce((sum, p) => sum + (p.points || 0), 0);
    const captainPoints = startingXI.find(p => p.is_captain)?.points || 0;
    const autosubPoints = data.automatic_subs?.reduce((sum, sub) => {
      const playerIn = data.picks.find(p => p.element === sub.element_in);
      return sum + (playerIn?.points || 0);
    }, 0) || 0;

    return {
      totalPoints: data.entry_history?.points || 0,
      startingPoints,
      benchPoints,
      captainPoints,
      autosubPoints,
      chipUsed: data.active_chip,
      transferCost: data.entry_history?.event_transfers_cost || 0,
    };
  };

  const renderSquadComparison = () => {
    if (!manager1Data || !manager2Data) return null;

    const differentials = getDifferentialPlayers();
    const metrics1 = calculateMetrics(manager1Data);
    const metrics2 = calculateMetrics(manager2Data);

    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="Total Points"
                value={`${metrics1?.totalPoints || 0} - ${metrics2?.totalPoints || 0}`}
                icon={<SoccerIcon />}
                trend={metrics1?.totalPoints > metrics2?.totalPoints ? 'up' : 
                       metrics1?.totalPoints < metrics2?.totalPoints ? 'down' : 'neutral'}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="Captain Points"
                value={`${metrics1?.captainPoints || 0} - ${metrics2?.captainPoints || 0}`}
                icon={<CaptainIcon />}
                subtitle="2x multiplier"
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="Bench Points"
                value={`${metrics1?.benchPoints || 0} - ${metrics2?.benchPoints || 0}`}
                icon={<TrendingDownIcon />}
                subtitle="Points left unused"
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="Differentials"
                value={`${differentials.onlyManager1.length} - ${differentials.onlyManager2.length}`}
                icon={<DifferentialIcon />}
                subtitle="Unique players"
              />
            </Grid>
          </Grid>
        </Grid>

        <Grid item xs={12} md={6}>
          <GlassCard>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                {manager1Name || 'Manager 1'} Squad
                {metrics1?.chipUsed && (
                  <Chip
                    label={metrics1.chipUsed.toUpperCase()}
                    color="primary"
                    size="small"
                    sx={{ ml: 2 }}
                  />
                )}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Player</TableCell>
                      <TableCell align="center">Pos</TableCell>
                      <TableCell align="center">Pts</TableCell>
                      <TableCell align="center">Price</TableCell>
                      <TableCell align="center">Own%</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {/* Starting XI */}
                    {manager1Data.picks.slice(0, 11).map((player) => (
                      <PlayerRow
                        key={player.element}
                        player={player}
                        isDifferential={differentials.onlyManager1.includes(player.element)}
                        isAutosub={manager1Data.automatic_subs?.some(
                          sub => sub.element_in === player.element
                        )}
                      />
                    ))}
                    {/* Bench */}
                    <TableRow>
                      <TableCell colSpan={5}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                          BENCH
                        </Typography>
                      </TableCell>
                    </TableRow>
                    {manager1Data.picks.slice(11).map((player) => (
                      <PlayerRow
                        key={player.element}
                        player={player}
                        isDifferential={differentials.onlyManager1.includes(player.element)}
                        isAutosub={false}
                      />
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          </GlassCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <GlassCard>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                {manager2Name || 'Manager 2'} Squad
                {metrics2?.chipUsed && (
                  <Chip
                    label={metrics2.chipUsed.toUpperCase()}
                    color="primary"
                    size="small"
                    sx={{ ml: 2 }}
                  />
                )}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Player</TableCell>
                      <TableCell align="center">Pos</TableCell>
                      <TableCell align="center">Pts</TableCell>
                      <TableCell align="center">Price</TableCell>
                      <TableCell align="center">Own%</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {/* Starting XI */}
                    {manager2Data.picks.slice(0, 11).map((player) => (
                      <PlayerRow
                        key={player.element}
                        player={player}
                        isDifferential={differentials.onlyManager2.includes(player.element)}
                        isAutosub={manager2Data.automatic_subs?.some(
                          sub => sub.element_in === player.element
                        )}
                      />
                    ))}
                    {/* Bench */}
                    <TableRow>
                      <TableCell colSpan={5}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                          BENCH
                        </Typography>
                      </TableCell>
                    </TableRow>
                    {manager2Data.picks.slice(11).map((player) => (
                      <PlayerRow
                        key={player.element}
                        player={player}
                        isDifferential={differentials.onlyManager2.includes(player.element)}
                        isAutosub={false}
                      />
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          </GlassCard>
        </Grid>
      </Grid>
    );
  };

  const renderDifferentials = () => {
    if (!manager1Data || !manager2Data) return null;

    const differentials = getDifferentialPlayers();
    
    const getDifferentialDetails = (playerIds, managerData) => {
      return playerIds.map(id => {
        const pick = managerData.picks.find(p => p.element === id);
        return pick;
      }).filter(Boolean);
    };

    const manager1Differentials = getDifferentialDetails(differentials.onlyManager1, manager1Data);
    const manager2Differentials = getDifferentialDetails(differentials.onlyManager2, manager2Data);

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <GlassCard>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                {manager1Name}'s Differential Picks
              </Typography>
              {manager1Differentials.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No differential players
                </Typography>
              ) : (
                <List>
                  {manager1Differentials.map((player) => (
                    <ListItem key={player.element}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                          {player.points || 0}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={player.element_name}
                        secondary={`${positionMap[player.element_type]} • £${(player.selling_price / 10).toFixed(1)}m • ${player.ownership}% owned`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          </GlassCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <GlassCard>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                {manager2Name}'s Differential Picks
              </Typography>
              {manager2Differentials.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No differential players
                </Typography>
              ) : (
                <List>
                  {manager2Differentials.map((player) => (
                    <ListItem key={player.element}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: theme.palette.secondary.main }}>
                          {player.points || 0}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={player.element_name}
                        secondary={`${positionMap[player.element_type]} • £${(player.selling_price / 10).toFixed(1)}m • ${player.ownership}% owned`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          </GlassCard>
        </Grid>

        <Grid item xs={12}>
          <GlassCard>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Differential Impact Analysis
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h3" color="primary.main">
                      {manager1Differentials.reduce((sum, p) => sum + (p.points || 0), 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {manager1Name}'s differential points
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h3" color="secondary.main">
                      {manager2Differentials.reduce((sum, p) => sum + (p.points || 0), 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {manager2Name}'s differential points
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </GlassCard>
        </Grid>
      </Grid>
    );
  };

  const renderAutoSubs = () => {
    if (!manager1Data || !manager2Data) return null;

    const hasAutoSubs = manager1Data.automatic_subs?.length > 0 || manager2Data.automatic_subs?.length > 0;

    if (!hasAutoSubs) {
      return (
        <Alert severity="info">
          No automatic substitutions were made in this gameweek.
        </Alert>
      );
    }

    return (
      <Grid container spacing={3}>
        {manager1Data.automatic_subs?.length > 0 && (
          <Grid item xs={12} md={6}>
            <GlassCard>
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  {manager1Name}'s Auto Substitutions
                </Typography>
                <List>
                  {manager1Data.automatic_subs.map((sub, index) => {
                    const playerOut = manager1Data.picks.find(p => p.element === sub.element_out);
                    const playerIn = manager1Data.picks.find(p => p.element === sub.element_in);
                    return (
                      <ListItem key={index}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'warning.main' }}>
                            <SubIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={`OUT: ${playerOut?.element_name || 'Unknown'} (${playerOut?.points || 0} pts)`}
                          secondary={`IN: ${playerIn?.element_name || 'Unknown'} (${playerIn?.points || 0} pts)`}
                        />
                      </ListItem>
                    );
                  })}
                </List>
              </Box>
            </GlassCard>
          </Grid>
        )}

        {manager2Data.automatic_subs?.length > 0 && (
          <Grid item xs={12} md={6}>
            <GlassCard>
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  {manager2Name}'s Auto Substitutions
                </Typography>
                <List>
                  {manager2Data.automatic_subs.map((sub, index) => {
                    const playerOut = manager2Data.picks.find(p => p.element === sub.element_out);
                    const playerIn = manager2Data.picks.find(p => p.element === sub.element_in);
                    return (
                      <ListItem key={index}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'warning.main' }}>
                            <SubIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={`OUT: ${playerOut?.element_name || 'Unknown'} (${playerOut?.points || 0} pts)`}
                          secondary={`IN: ${playerIn?.element_name || 'Unknown'} (${playerIn?.points || 0} pts)`}
                        />
                      </ListItem>
                    );
                  })}
                </List>
              </Box>
            </GlassCard>
          </Grid>
        )}
      </Grid>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          background: 'rgba(18, 18, 18, 0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              onClick={() => handleGameweekChange(-1)}
              disabled={currentGW <= 1}
              size="small"
            >
              <PrevIcon />
            </IconButton>
            <Typography variant="h5">
              Gameweek {currentGW}
            </Typography>
            <IconButton
              onClick={() => handleGameweekChange(1)}
              disabled={currentGW >= 38}
              size="small"
            >
              <NextIcon />
            </IconButton>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : (
          <>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
                <Tab label="Squad Comparison" icon={<SoccerIcon />} iconPosition="start" />
                <Tab label="Differentials" icon={<DifferentialIcon />} iconPosition="start" />
                <Tab label="Auto Subs" icon={<SubIcon />} iconPosition="start" />
              </Tabs>
            </Box>

            <AnimatePresence mode="wait">
              <motion.div
                key={tabValue}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <TabPanel value={tabValue} index={0}>
                  {renderSquadComparison()}
                </TabPanel>
                <TabPanel value={tabValue} index={1}>
                  {renderDifferentials()}
                </TabPanel>
                <TabPanel value={tabValue} index={2}>
                  {renderAutoSubs()}
                </TabPanel>
              </motion.div>
            </AnimatePresence>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default GameweekDetail;