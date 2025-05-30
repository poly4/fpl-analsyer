import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Tabs,
  Tab,
  Avatar,
  CircularProgress,
  Grid,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  IconButton,
  useTheme,
  useMediaQuery,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Close as CloseIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  SwapHoriz as TransferIcon,
  Star as StarIcon,
  EmojiEvents as TrophyIcon,
  Timeline as TimelineIcon,
  AttachMoney as MoneyIcon,
  Group as GroupIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';
import { GlassCard, StatBox, AnimatedNumber } from './modern';
import { motion, AnimatePresence } from 'framer-motion';
import { useOptimizedAPI } from '../hooks/useOptimizedAPI';

const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`manager-tabpanel-${index}`}
    aria-labelledby={`manager-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const chipColors = {
  wildcard: '#f44336',
  freehit: '#ff9800',
  bboost: '#2196f3',
  threexc: '#4caf50',
};

const chipNames = {
  wildcard: 'Wildcard',
  freehit: 'Free Hit',
  bboost: 'Bench Boost',
  threexc: 'Triple Captain',
};

const ManagerProfile = ({ managerId, open, onClose, managerName }) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  const [tabValue, setTabValue] = useState(0);
  const [managerData, setManagerData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [transfersData, setTransfersData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { request, cache } = useOptimizedAPI();

  useEffect(() => {
    if (open && managerId) {
      fetchManagerData();
    }
  }, [open, managerId]);

  const fetchManagerData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch all manager data in parallel
      const [basicInfo, history, transfers] = await Promise.all([
        request(`/api/entry/${managerId}/`),
        request(`/api/entry/${managerId}/history/`),
        request(`/api/entry/${managerId}/transfers/`),
      ]);

      setManagerData(basicInfo);
      setHistoryData(history);
      setTransfersData(transfers);
    } catch (err) {
      console.error('Error fetching manager data:', err);
      setError('Failed to load manager data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const formatCurrency = (value) => {
    return (value / 10).toFixed(1);
  };

  const getChipGameweek = (chipName) => {
    if (!historyData?.chips) return null;
    const chip = historyData.chips.find(c => c.name === chipName);
    return chip ? chip.event : null;
  };

  const renderOverview = () => {
    if (!managerData || !historyData) return null;

    const currentSeason = historyData.current?.[historyData.current.length - 1] || {};
    const previousSeasons = historyData.past || [];
    const chipsUsed = historyData.chips || [];

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <GlassCard>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  mx: 'auto',
                  mb: 2,
                  fontSize: '2.5rem',
                  bgcolor: theme.palette.primary.main,
                }}
              >
                {managerName?.charAt(0).toUpperCase()}
              </Avatar>
              <Typography variant="h5" gutterBottom>
                {managerData.player_first_name} {managerData.player_last_name}
              </Typography>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                {managerData.name}
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Chip
                  icon={<TrophyIcon />}
                  label={`Overall Rank: ${currentSeason.overall_rank?.toLocaleString() || 'N/A'}`}
                  color="primary"
                  sx={{ m: 0.5 }}
                />
                <Chip
                  icon={<GroupIcon />}
                  label={`${managerData.player_region_name}`}
                  sx={{ m: 0.5 }}
                />
              </Box>
            </Box>
          </GlassCard>
        </Grid>

        <Grid item xs={12} md={8}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="Total Points"
                value={currentSeason.total_points || 0}
                icon={<StarIcon />}
                trend={currentSeason.event_transfers > 0 ? 'up' : 'neutral'}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="Team Value"
                value={`£${formatCurrency(currentSeason.value || 1000)}m`}
                icon={<MoneyIcon />}
                subtitle={`Bank: £${formatCurrency(currentSeason.bank || 0)}m`}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="GW Rank"
                value={currentSeason.rank?.toLocaleString() || 'N/A'}
                icon={<TrendingUpIcon />}
                trend={currentSeason.rank_sort < 1000000 ? 'up' : 'down'}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatBox
                title="Transfers"
                value={currentSeason.event_transfers || 0}
                icon={<TransferIcon />}
                subtitle={`Cost: ${currentSeason.event_transfers_cost || 0}pts`}
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Chips Used
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {Object.keys(chipNames).map((chipKey) => {
                const gw = getChipGameweek(chipKey);
                return (
                  <Chip
                    key={chipKey}
                    label={gw ? `${chipNames[chipKey]} (GW${gw})` : chipNames[chipKey]}
                    sx={{
                      bgcolor: gw ? chipColors[chipKey] : 'grey.700',
                      color: 'white',
                      opacity: gw ? 1 : 0.5,
                    }}
                  />
                );
              })}
            </Box>
          </Box>
        </Grid>
      </Grid>
    );
  };

  const renderSeasonProgression = () => {
    if (!historyData?.current) return null;

    const rankData = historyData.current.map((gw) => ({
      gw: gw.event,
      rank: gw.overall_rank,
      points: gw.points,
      totalPoints: gw.total_points,
      value: gw.value / 10,
    }));

    const pointsData = historyData.current.map((gw) => ({
      gw: gw.event,
      points: gw.points,
      benchPoints: gw.points_on_bench,
      transfers: gw.event_transfers,
      transferCost: gw.event_transfers_cost,
    }));

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <GlassCard>
            <Typography variant="h6" gutterBottom sx={{ p: 2 }}>
              Rank Progression
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={rankData}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis dataKey="gw" stroke={theme.palette.text.primary} />
                <YAxis reversed stroke={theme.palette.text.primary} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="rank"
                  stroke={theme.palette.primary.main}
                  strokeWidth={2}
                  dot={{ fill: theme.palette.primary.main }}
                />
              </LineChart>
            </ResponsiveContainer>
          </GlassCard>
        </Grid>

        <Grid item xs={12} lg={6}>
          <GlassCard>
            <Typography variant="h6" gutterBottom sx={{ p: 2 }}>
              Points Per Gameweek
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={pointsData}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis dataKey="gw" stroke={theme.palette.text.primary} />
                <YAxis stroke={theme.palette.text.primary} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="points"
                  stackId="1"
                  stroke={theme.palette.success.main}
                  fill={theme.palette.success.main}
                  fillOpacity={0.6}
                />
                <Area
                  type="monotone"
                  dataKey="benchPoints"
                  stackId="1"
                  stroke={theme.palette.warning.main}
                  fill={theme.palette.warning.main}
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </GlassCard>
        </Grid>

        <Grid item xs={12}>
          <GlassCard>
            <Typography variant="h6" gutterBottom sx={{ p: 2 }}>
              Team Value Progression
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={rankData}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis dataKey="gw" stroke={theme.palette.text.primary} />
                <YAxis stroke={theme.palette.text.primary} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                  }}
                  formatter={(value) => `£${value}m`}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={theme.palette.secondary.main}
                  strokeWidth={2}
                  dot={{ fill: theme.palette.secondary.main }}
                />
              </LineChart>
            </ResponsiveContainer>
          </GlassCard>
        </Grid>
      </Grid>
    );
  };

  const renderTransfers = () => {
    if (!transfersData || transfersData.length === 0) {
      return (
        <Alert severity="info">No transfer history available for this manager.</Alert>
      );
    }

    // Group transfers by gameweek
    const transfersByGW = transfersData.reduce((acc, transfer) => {
      const gw = transfer.event;
      if (!acc[gw]) acc[gw] = [];
      acc[gw].push(transfer);
      return acc;
    }, {});

    // Calculate transfer metrics
    const transferMetrics = Object.entries(transfersByGW).map(([gw, transfers]) => {
      const totalCost = transfers.reduce((sum, t) => sum + (t.element_out_cost - t.element_in_cost), 0);
      return {
        gw: parseInt(gw),
        count: transfers.length,
        netSpend: totalCost / 10,
      };
    });

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <GlassCard>
            <Typography variant="h6" gutterBottom sx={{ p: 2 }}>
              Transfer History
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>GW</TableCell>
                    <TableCell>Player In</TableCell>
                    <TableCell>Player Out</TableCell>
                    <TableCell align="right">Price In</TableCell>
                    <TableCell align="right">Price Out</TableCell>
                    <TableCell align="right">Net</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transfersData.slice(0, 20).map((transfer, index) => (
                    <TableRow key={index}>
                      <TableCell>{transfer.event}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <TrendingUpIcon fontSize="small" color="success" />
                          {transfer.element_in_name || 'Unknown'}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <TrendingDownIcon fontSize="small" color="error" />
                          {transfer.element_out_name || 'Unknown'}
                        </Box>
                      </TableCell>
                      <TableCell align="right">£{(transfer.element_in_cost / 10).toFixed(1)}m</TableCell>
                      <TableCell align="right">£{(transfer.element_out_cost / 10).toFixed(1)}m</TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={transfer.element_out_cost > transfer.element_in_cost ? 'success.main' : 'error.main'}
                        >
                          {transfer.element_out_cost > transfer.element_in_cost ? '+' : ''}
                          £{((transfer.element_out_cost - transfer.element_in_cost) / 10).toFixed(1)}m
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {transfersData.length > 20 && (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Showing 20 of {transfersData.length} transfers
                </Typography>
              </Box>
            )}
          </GlassCard>
        </Grid>

        <Grid item xs={12} md={4}>
          <GlassCard>
            <Typography variant="h6" gutterBottom sx={{ p: 2 }}>
              Transfer Activity
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={transferMetrics}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis dataKey="gw" stroke={theme.palette.text.primary} />
                <YAxis stroke={theme.palette.text.primary} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                  }}
                />
                <Bar dataKey="count" fill={theme.palette.primary.main} />
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </Grid>
      </Grid>
    );
  };

  const renderHistoricalSeasons = () => {
    if (!historyData?.past || historyData.past.length === 0) {
      return (
        <Alert severity="info">No historical season data available for this manager.</Alert>
      );
    }

    return (
      <Grid container spacing={3}>
        {historyData.past.map((season, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <GlassCard>
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  {season.season_name}
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="Final Rank"
                      secondary={season.rank?.toLocaleString() || 'N/A'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Total Points"
                      secondary={season.total_points || 'N/A'}
                    />
                  </ListItem>
                </List>
              </Box>
            </GlassCard>
          </Grid>
        ))}
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
          <Typography variant="h5">
            Manager Profile
          </Typography>
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
                <Tab label="Overview" icon={<StarIcon />} iconPosition="start" />
                <Tab label="Season Progress" icon={<TimelineIcon />} iconPosition="start" />
                <Tab label="Transfers" icon={<TransferIcon />} iconPosition="start" />
                <Tab label="History" icon={<TrophyIcon />} iconPosition="start" />
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
                  {renderOverview()}
                </TabPanel>
                <TabPanel value={tabValue} index={1}>
                  {renderSeasonProgression()}
                </TabPanel>
                <TabPanel value={tabValue} index={2}>
                  {renderTransfers()}
                </TabPanel>
                <TabPanel value={tabValue} index={3}>
                  {renderHistoricalSeasons()}
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

export default ManagerProfile;