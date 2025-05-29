import React, { useState, useCallback } from 'react';
import { Box, Typography, IconButton, Menu, MenuItem, Tooltip } from '@mui/material';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import { 
  MoreVert, 
  Fullscreen, 
  FullscreenExit, 
  Refresh,
  Settings,
  Download,
  Share
} from '@mui/icons-material';
import { GlassCard, BentoGrid, glassMixins } from './modern';
import ChipStrategy from './analytics/ChipStrategy';
import DifferentialImpact from './analytics/DifferentialImpact';
import HistoricalPatterns from './analytics/HistoricalPatterns';
import LiveMatchTracker from './analytics/LiveMatchTracker';
import TransferROI from './analytics/TransferROI';
import PredictionGraphs from './analytics/PredictionGraphs';

// Card configurations
const CARD_CONFIGS = {
  chipStrategy: {
    id: 'chipStrategy',
    title: '🎯 Chip Strategy',
    component: ChipStrategy,
    size: 'medium',
    defaultExpanded: false
  },
  differentialImpact: {
    id: 'differentialImpact',
    title: '📊 Differential Impact',
    component: DifferentialImpact,
    size: 'large',
    defaultExpanded: false
  },
  historicalPatterns: {
    id: 'historicalPatterns',
    title: '📈 Historical Patterns',
    component: HistoricalPatterns,
    size: 'medium',
    defaultExpanded: false
  },
  liveMatchTracker: {
    id: 'liveMatchTracker',
    title: '⚡ Live Match Tracker',
    component: LiveMatchTracker,
    size: 'hero',
    defaultExpanded: true
  },
  transferROI: {
    id: 'transferROI',
    title: '💰 Transfer ROI',
    component: TransferROI,
    size: 'medium',
    defaultExpanded: false
  },
  predictionGraphs: {
    id: 'predictionGraphs',
    title: '🔮 Predictions',
    component: PredictionGraphs,
    size: 'large',
    defaultExpanded: false
  }
};

// Interactive card wrapper
const InteractiveCard = ({ 
  config, 
  isExpanded, 
  onToggleExpand, 
  onAction,
  data 
}) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const Component = config.component;

  const handleMenuOpen = (event) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleAction = (action) => {
    onAction(config.id, action);
    handleMenuClose();
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
      whileHover={{ y: -4 }}
      style={{ height: '100%' }}
    >
      <GlassCard
        variant="elevated"
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          cursor: 'move',
          '&:hover .card-actions': {
            opacity: 1
          }
        }}
      >
        {/* Card Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2,
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              fontSize: '1rem',
              color: '#fff'
            }}
          >
            {config.title}
          </Typography>
          
          <Box 
            className="card-actions"
            sx={{ 
              display: 'flex', 
              gap: 0.5,
              opacity: 0,
              transition: 'opacity 0.3s ease'
            }}
          >
            <Tooltip title="Refresh">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAction('refresh');
                }}
                sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
              >
                <Refresh fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title={isExpanded ? "Exit Fullscreen" : "Fullscreen"}>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleExpand();
                }}
                sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
              >
                {isExpanded ? <FullscreenExit fontSize="small" /> : <Fullscreen fontSize="small" />}
              </IconButton>
            </Tooltip>
            
            <IconButton
              size="small"
              onClick={handleMenuOpen}
              sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
            >
              <MoreVert fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {/* Card Content */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            '&::-webkit-scrollbar': {
              width: '6px',
            },
            '&::-webkit-scrollbar-track': {
              background: 'rgba(255, 255, 255, 0.05)',
            },
            '&::-webkit-scrollbar-thumb': {
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '3px',
            },
          }}
        >
          <Component data={data} />
        </Box>

        {/* Action Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              ...glassMixins.glass,
              background: 'rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              '& .MuiMenuItem-root': {
                color: '#fff',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.1)'
                }
              }
            }
          }}
        >
          <MenuItem onClick={() => handleAction('download')}>
            <Download fontSize="small" sx={{ mr: 1 }} />
            Download Data
          </MenuItem>
          <MenuItem onClick={() => handleAction('share')}>
            <Share fontSize="small" sx={{ mr: 1 }} />
            Share
          </MenuItem>
          <MenuItem onClick={() => handleAction('settings')}>
            <Settings fontSize="small" sx={{ mr: 1 }} />
            Settings
          </MenuItem>
        </Menu>
      </GlassCard>
    </motion.div>
  );
};

// Main interactive analytics component
const InteractiveAnalytics = ({ leagueId }) => {
  const [cardOrder, setCardOrder] = useState(Object.keys(CARD_CONFIGS));
  const [expandedCard, setExpandedCard] = useState(null);
  const [refreshKey, setRefreshKey] = useState({});

  const handleToggleExpand = useCallback((cardId) => {
    setExpandedCard(prev => prev === cardId ? null : cardId);
  }, []);

  const handleCardAction = useCallback((cardId, action) => {
    switch (action) {
      case 'refresh':
        setRefreshKey(prev => ({
          ...prev,
          [cardId]: Date.now()
        }));
        break;
      case 'download':
        // Implement download functionality
        console.log(`Download data for ${cardId}`);
        break;
      case 'share':
        // Implement share functionality
        console.log(`Share ${cardId}`);
        break;
      case 'settings':
        // Implement settings functionality
        console.log(`Open settings for ${cardId}`);
        break;
      default:
        break;
    }
  }, []);

  // Fullscreen view
  if (expandedCard) {
    const config = CARD_CONFIGS[expandedCard];
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1300,
          background: 'rgba(0, 0, 0, 0.9)',
          padding: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Box sx={{ width: '100%', height: '100%', maxWidth: 1400 }}>
          <InteractiveCard
            config={config}
            isExpanded={true}
            onToggleExpand={() => handleToggleExpand(expandedCard)}
            onAction={handleCardAction}
            data={{ leagueId, key: refreshKey[expandedCard] }}
          />
        </Box>
      </motion.div>
    );
  }

  // Grid view with drag and drop
  return (
    <Box>
      <Typography
        variant="h5"
        sx={{
          fontWeight: 700,
          mb: 3,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}
      >
        Interactive Analytics Dashboard
      </Typography>
      
      <Typography
        variant="body2"
        sx={{
          color: 'rgba(255, 255, 255, 0.5)',
          mb: 3
        }}
      >
        Drag cards to rearrange • Click fullscreen for detailed view • Hover for quick actions
      </Typography>

      <Reorder.Group
        axis="y"
        values={cardOrder}
        onReorder={setCardOrder}
        style={{ listStyle: 'none', padding: 0 }}
      >
        <BentoGrid>
          <AnimatePresence>
            {cardOrder.map((cardId) => {
              const config = CARD_CONFIGS[cardId];
              return (
                <Reorder.Item
                  key={cardId}
                  value={cardId}
                  style={{ gridColumn: `span ${config.size === 'hero' ? 3 : config.size === 'large' ? 2 : 1}` }}
                >
                  <InteractiveCard
                    config={config}
                    isExpanded={false}
                    onToggleExpand={() => handleToggleExpand(cardId)}
                    onAction={handleCardAction}
                    data={{ leagueId, key: refreshKey[cardId] }}
                  />
                </Reorder.Item>
              );
            })}
          </AnimatePresence>
        </BentoGrid>
      </Reorder.Group>
    </Box>
  );
};

export default InteractiveAnalytics;