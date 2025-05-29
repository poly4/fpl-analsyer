import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Avatar,
  Divider,
  IconButton,
  Tooltip,
  Badge,
  Paper,
  Fade,
  Zoom,
  Collapse,
  Alert,
  Button,
  Stack,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  useTheme
} from '@mui/material';
import {
  SportsSoccer,
  AssistantPhoto,
  Shield,
  Warning,
  Star,
  TrendingUp,
  TrendingDown,
  Timer,
  NotificationsActive,
  PlayArrow,
  Stop,
  Refresh,
  EmojiEvents,
  LocalFireDepartment,
  Speed
} from '@mui/icons-material';
import { keyframes } from '@mui/system';
import io from 'socket.io-client';
import { motion, AnimatePresence } from 'framer-motion';

// Animation keyframes
const pulse = keyframes`
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
`;

const slideIn = keyframes`
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`;

const EventIcon = ({ type }) => {
  const iconMap = {
    goal: <SportsSoccer color="success" />,
    assist: <AssistantPhoto color="primary" />,
    clean_sheet: <Shield color="info" />,
    card: <Warning color="error" />,
    bonus: <Star color="warning" />,
    captain: <EmojiEvents color="secondary" />
  };
  return iconMap[type] || <SportsSoccer />;
};

const LiveEvent = ({ event, isViewer }) => {
  const theme = useTheme();
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(true);
  }, []);

  return (
    <Zoom in={show}>
      <Paper
        elevation={3}
        sx={{
          p: 2,
          mb: 1,
          background: isViewer
            ? `linear-gradient(135deg, ${theme.palette.success.light}20 0%, ${theme.palette.success.main}10 100%)`
            : `linear-gradient(135deg, ${theme.palette.error.light}20 0%, ${theme.palette.error.main}10 100%)`,
          border: `1px solid ${isViewer ? theme.palette.success.main : theme.palette.error.main}30`,
          animation: `${pulse} 2s ease-in-out`,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <Avatar
            sx={{
              bgcolor: isViewer ? theme.palette.success.main : theme.palette.error.main,
              width: 32,
              height: 32
            }}
          >
            <EventIcon type={event.type} />
          </Avatar>
          <Box flex={1}>
            <Typography variant="body2" fontWeight="bold">
              {event.player_name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {event.minute}' - {event.points} pts
            </Typography>
          </Box>
          <Chip
            label={`+${event.points}`}
            size="small"
            color={isViewer ? "success" : "error"}
            sx={{ fontWeight: 'bold' }}
          />
        </Stack>
      </Paper>
    </Zoom>
  );
};

const TeamFormation = ({ team, players, liveStats, isCaptain }) => {
  const theme = useTheme();
  const positions = {
    1: { top: '80%', left: '50%' }, // GK
    2: [ // DEF
      { top: '60%', left: '15%' },
      { top: '60%', left: '35%' },
      { top: '60%', left: '65%' },
      { top: '60%', left: '85%' },
    ],
    3: [ // MID
      { top: '35%', left: '20%' },
      { top: '35%', left: '40%' },
      { top: '35%', left: '60%' },
      { top: '35%', left: '80%' },
    ],
    4: [ // FWD
      { top: '10%', left: '35%' },
      { top: '10%', left: '65%' },
    ]
  };

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: 400,
        background: `linear-gradient(to bottom, ${theme.palette.success.dark}40, ${theme.palette.success.main}20)`,
        borderRadius: 2,
        overflow: 'hidden',
        border: `2px solid ${theme.palette.divider}`,
      }}
    >
      {/* Pitch lines */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: 0,
          right: 0,
          height: 2,
          bgcolor: 'white',
          opacity: 0.3,
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: '20%',
          left: '25%',
          right: '25%',
          height: '60%',
          border: '2px solid white',
          borderRadius: 1,
          opacity: 0.3,
        }}
      />

      {/* Players */}
      {players.map((player, index) => {
        const pos = player.element_type;
        const posIndex = players.filter(p => p.element_type === pos).indexOf(player);
        const position = Array.isArray(positions[pos]) ? positions[pos][posIndex] : positions[pos];
        const stats = liveStats[player.id] || {};
        const isActive = stats.minutes > 0;
        const hasScored = stats.goals > 0;
        const hasAssisted = stats.assists > 0;

        return (
          <motion.div
            key={player.id}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: index * 0.1 }}
            style={{
              position: 'absolute',
              ...position,
              transform: 'translate(-50%, -50%)'
            }}
          >
            <Tooltip
              title={
                <Box>
                  <Typography variant="body2">{player.web_name}</Typography>
                  <Typography variant="caption">Minutes: {stats.minutes || 0}</Typography>
                  <Typography variant="caption">Points: {stats.total_points || 0}</Typography>
                  {hasScored && <Typography variant="caption">Goals: {stats.goals}</Typography>}
                  {hasAssisted && <Typography variant="caption">Assists: {stats.assists}</Typography>}
                </Box>
              }
            >
              <Badge
                badgeContent={stats.total_points || 0}
                color={hasScored ? "success" : hasAssisted ? "primary" : "default"}
                invisible={!isActive}
              >
                <Avatar
                  sx={{
                    width: 48,
                    height: 48,
                    bgcolor: isActive ? theme.palette.primary.main : theme.palette.grey[400],
                    border: isCaptain(player.id) ? `3px solid ${theme.palette.warning.main}` : 'none',
                    animation: hasScored || hasAssisted ? `${pulse} 2s infinite` : 'none',
                  }}
                >
                  <Typography variant="caption" fontWeight="bold">
                    {player.web_name.substring(0, 3)}
                  </Typography>
                </Avatar>
              </Badge>
            </Tooltip>
          </motion.div>
        );
      })}
    </Box>
  );
};

const LiveCommentary = ({ commentary }) => {
  const theme = useTheme();
  
  return (
    <AnimatePresence>
      {commentary.map((item, index) => (
        <motion.div
          key={index}
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 100, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Alert
            severity={item.tone === 'exciting' ? 'success' : item.tone === 'sympathetic' ? 'error' : 'info'}
            icon={item.impact > 70 ? <LocalFireDepartment /> : <Speed />}
            sx={{
              mb: 1,
              animation: item.impact > 70 ? `${pulse} 1s ease-in-out` : 'none',
            }}
          >
            <Typography variant="body2">
              <strong>{item.minute}'</strong> - {item.text}
            </Typography>
            {item.impact > 50 && (
              <Typography variant="caption" display="block" mt={0.5}>
                Impact: {item.impact}/100 {item.momentum && `• Momentum: ${item.momentum}`}
              </Typography>
            )}
          </Alert>
        </motion.div>
      ))}
    </AnimatePresence>
  );
};

export default function LiveH2HBattle({ battle, gameweek, viewerId }) {
  const theme = useTheme();
  const [socket, setSocket] = useState(null);
  const [liveData, setLiveData] = useState({
    manager1_score: battle.manager1_score,
    manager2_score: battle.manager2_score,
    manager1_live_score: battle.manager1_score,
    manager2_live_score: battle.manager2_score,
    events: [],
    commentary: [],
    liveStats: {},
    momentum: 'neutral'
  });
  const [isLive, setIsLive] = useState(false);
  const [showFormation, setShowFormation] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const commentaryRef = useRef(null);

  const isViewer = viewerId === battle.manager1_id || viewerId === battle.manager2_id;
  const viewerTeam = viewerId === battle.manager1_id ? 1 : viewerId === battle.manager2_id ? 2 : null;

  useEffect(() => {
    // Connect to WebSocket
    const ws = io(import.meta.env.VITE_WS_URL || 'ws://localhost:8000', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    ws.on('connect', () => {
      console.log('Connected to live updates');
      setIsLive(true);
      
      // Subscribe to this battle
      ws.emit('subscribe', {
        room: `h2h_${Math.min(battle.manager1_id, battle.manager2_id)}_${Math.max(battle.manager1_id, battle.manager2_id)}`,
        type: 'h2h_battle'
      });

      // Subscribe to gameweek updates
      ws.emit('subscribe', {
        room: `live_gw_${gameweek}`,
        type: 'gameweek'
      });
    });

    ws.on('h2h_update', (data) => {
      if (data.update.manager1_id === battle.manager1_id && data.update.manager2_id === battle.manager2_id) {
        setLiveData(prev => ({
          ...prev,
          ...data.update,
          events: [...prev.events, ...data.update.events],
          commentary: [...data.update.commentary, ...prev.commentary].slice(0, 10)
        }));

        // Auto-scroll commentary
        if (commentaryRef.current && autoRefresh) {
          commentaryRef.current.scrollTop = 0;
        }
      }
    });

    ws.on('live_events', (data) => {
      // Process events for players in this battle
      const relevantEvents = data.events.filter(event => {
        return battle.manager1_players.some(p => p.id === event.player_id) ||
               battle.manager2_players.some(p => p.id === event.player_id);
      });

      if (relevantEvents.length > 0) {
        setLiveData(prev => ({
          ...prev,
          events: [...prev.events, ...relevantEvents]
        }));
      }
    });

    ws.on('disconnect', () => {
      console.log('Disconnected from live updates');
      setIsLive(false);
    });

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [battle, gameweek, viewerId, autoRefresh]);

  const scoreDiff = liveData.manager1_live_score - liveData.manager2_live_score;
  const manager1Winning = scoreDiff > 0;
  const manager2Winning = scoreDiff < 0;
  const tied = scoreDiff === 0;

  const getMomentumIcon = () => {
    if (liveData.momentum === 'manager1') return <TrendingUp color="success" />;
    if (liveData.momentum === 'manager2') return <TrendingDown color="error" />;
    return <Timer color="action" />;
  };

  return (
    <Card elevation={3}>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Stack direction="row" spacing={2} alignItems="center">
            <Typography variant="h5" fontWeight="bold">
              Live H2H Battle
            </Typography>
            <Chip
              icon={isLive ? <PlayArrow /> : <Stop />}
              label={isLive ? "LIVE" : "OFFLINE"}
              color={isLive ? "success" : "default"}
              size="small"
              sx={{ animation: isLive ? `${pulse} 2s infinite` : 'none' }}
            />
          </Stack>
          <Stack direction="row" spacing={1}>
            <Tooltip title="Toggle Formation View">
              <IconButton onClick={() => setShowFormation(!showFormation)}>
                <Shield />
              </IconButton>
            </Tooltip>
            <Tooltip title="Toggle Auto-refresh">
              <IconButton
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? "primary" : "default"}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="Enable Notifications">
              <IconButton>
                <NotificationsActive />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {/* Live Scores */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={5}>
            <Paper
              elevation={manager1Winning ? 6 : 1}
              sx={{
                p: 3,
                textAlign: 'center',
                background: manager1Winning
                  ? `linear-gradient(135deg, ${theme.palette.success.light}20 0%, ${theme.palette.success.main}10 100%)`
                  : theme.palette.background.paper,
                border: manager1Winning ? `2px solid ${theme.palette.success.main}` : 'none',
                transition: 'all 0.3s ease',
              }}
            >
              <Typography variant="h6" gutterBottom>
                {battle.manager1_name}
              </Typography>
              <Typography
                variant="h2"
                fontWeight="bold"
                color={manager1Winning ? "success.main" : "text.primary"}
                sx={{
                  animation: liveData.manager1_live_score !== liveData.manager1_score
                    ? `${pulse} 1s ease-in-out`
                    : 'none'
                }}
              >
                {liveData.manager1_live_score}
              </Typography>
              {liveData.manager1_live_score !== liveData.manager1_score && (
                <Typography variant="caption" color="text.secondary">
                  ({liveData.manager1_score} + {liveData.manager1_live_score - liveData.manager1_score})
                </Typography>
              )}
            </Paper>
          </Grid>

          <Grid item xs={2}>
            <Box
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              height="100%"
            >
              <Typography variant="h4" color="text.secondary" gutterBottom>
                VS
              </Typography>
              <Chip
                icon={getMomentumIcon()}
                label={tied ? "TIED" : manager1Winning ? `+${Math.abs(scoreDiff)}` : `-${Math.abs(scoreDiff)}`}
                color={tied ? "default" : manager1Winning ? "success" : "error"}
                sx={{ fontWeight: 'bold' }}
              />
            </Box>
          </Grid>

          <Grid item xs={5}>
            <Paper
              elevation={manager2Winning ? 6 : 1}
              sx={{
                p: 3,
                textAlign: 'center',
                background: manager2Winning
                  ? `linear-gradient(135deg, ${theme.palette.error.light}20 0%, ${theme.palette.error.main}10 100%)`
                  : theme.palette.background.paper,
                border: manager2Winning ? `2px solid ${theme.palette.error.main}` : 'none',
                transition: 'all 0.3s ease',
              }}
            >
              <Typography variant="h6" gutterBottom>
                {battle.manager2_name}
              </Typography>
              <Typography
                variant="h2"
                fontWeight="bold"
                color={manager2Winning ? "error.main" : "text.primary"}
                sx={{
                  animation: liveData.manager2_live_score !== liveData.manager2_score
                    ? `${pulse} 1s ease-in-out`
                    : 'none'
                }}
              >
                {liveData.manager2_live_score}
              </Typography>
              {liveData.manager2_live_score !== liveData.manager2_score && (
                <Typography variant="caption" color="text.secondary">
                  ({liveData.manager2_score} + {liveData.manager2_live_score - liveData.manager2_score})
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Formation View */}
        <Collapse in={showFormation}>
          <Grid container spacing={3} mb={3}>
            <Grid item xs={6}>
              <Typography variant="h6" gutterBottom>
                {battle.manager1_name} Formation
              </Typography>
              <TeamFormation
                team={1}
                players={battle.manager1_players}
                liveStats={liveData.liveStats}
                isCaptain={(playerId) => battle.manager1_captain === playerId}
              />
            </Grid>
            <Grid item xs={6}>
              <Typography variant="h6" gutterBottom>
                {battle.manager2_name} Formation
              </Typography>
              <TeamFormation
                team={2}
                players={battle.manager2_players}
                liveStats={liveData.liveStats}
                isCaptain={(playerId) => battle.manager2_captain === playerId}
              />
            </Grid>
          </Grid>
          <Divider sx={{ my: 3 }} />
        </Collapse>

        {/* Live Commentary */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Live Commentary
          </Typography>
          <Box
            ref={commentaryRef}
            sx={{
              maxHeight: 300,
              overflowY: 'auto',
              bgcolor: theme.palette.background.default,
              borderRadius: 1,
              p: 2,
            }}
          >
            {liveData.commentary.length > 0 ? (
              <LiveCommentary commentary={liveData.commentary} />
            ) : (
              <Typography variant="body2" color="text.secondary" textAlign="center">
                Waiting for match events...
              </Typography>
            )}
          </Box>
        </Box>

        {/* Recent Events */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Recent Events
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                {battle.manager1_name} Events
              </Typography>
              {liveData.events
                .filter(e => battle.manager1_players.some(p => p.id === e.player_id))
                .slice(-3)
                .map((event, idx) => (
                  <LiveEvent key={idx} event={event} isViewer={viewerTeam === 1} />
                ))}
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                {battle.manager2_name} Events
              </Typography>
              {liveData.events
                .filter(e => battle.manager2_players.some(p => p.id === e.player_id))
                .slice(-3)
                .map((event, idx) => (
                  <LiveEvent key={idx} event={event} isViewer={viewerTeam === 2} />
                ))}
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
}