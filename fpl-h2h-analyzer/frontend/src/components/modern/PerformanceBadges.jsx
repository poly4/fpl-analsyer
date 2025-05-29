import React from 'react';
import { Box, Typography, Chip, Tooltip } from '@mui/material';
import { motion } from 'framer-motion';
import {
  EmojiEvents,
  LocalFireDepartment,
  TrendingUp,
  TrendingDown,
  Shield,
  Star,
  SportsSoccer,
  FlashOn,
  Whatshot,
  Psychology,
  Rocket,
  Timer
} from '@mui/icons-material';

// Badge configurations
const BADGE_CONFIGS = {
  // Performance badges
  topScorer: {
    icon: <SportsSoccer />,
    label: 'Top Scorer',
    description: 'Highest gameweek score',
    gradient: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
    color: '#000'
  },
  consistent: {
    icon: <Psychology />,
    label: 'Consistent',
    description: '5+ weeks above average',
    gradient: 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)',
    color: '#000'
  },
  hotStreak: {
    icon: <Whatshot />,
    label: 'Hot Streak',
    description: '3+ consecutive wins',
    gradient: 'linear-gradient(135deg, #ff6b6b 0%, #ff3838 100%)',
    color: '#fff'
  },
  comeback: {
    icon: <Rocket />,
    label: 'Comeback King',
    description: 'Won from 20+ points behind',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff'
  },
  earlyBird: {
    icon: <Timer />,
    label: 'Early Bird',
    description: 'Made transfers before deadline',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    color: '#fff'
  },
  // Chip usage badges
  tripleCaptain: {
    icon: <Star />,
    label: 'Triple Captain',
    description: 'Used Triple Captain chip',
    gradient: 'linear-gradient(135deg, #ffd93d 0%, #ff9500 100%)',
    color: '#000'
  },
  benchBoost: {
    icon: <FlashOn />,
    label: 'Bench Boost',
    description: 'Used Bench Boost chip',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    color: '#000'
  },
  freeHit: {
    icon: <LocalFireDepartment />,
    label: 'Free Hit',
    description: 'Used Free Hit chip',
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    color: '#000'
  },
  wildcard: {
    icon: <Shield />,
    label: 'Wildcard',
    description: 'Used Wildcard chip',
    gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    color: '#000'
  },
  // Achievement badges
  centurion: {
    icon: <EmojiEvents />,
    label: 'Centurion',
    description: 'Scored 100+ points',
    gradient: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
    color: '#000'
  },
  differential: {
    icon: <TrendingUp />,
    label: 'Differential Master',
    description: 'Owned <5% player who hauled',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff'
  },
  captaincy: {
    icon: <Star />,
    label: 'Captain Fantastic',
    description: 'Perfect captain choice',
    gradient: 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)',
    color: '#000'
  }
};

// Individual badge component
export const PerformanceBadge = ({ type, size = 'medium', showLabel = true, animate = true }) => {
  const config = BADGE_CONFIGS[type];
  if (!config) return null;

  const sizes = {
    small: { width: 32, height: 32, fontSize: 16, labelSize: '0.7rem' },
    medium: { width: 48, height: 48, fontSize: 20, labelSize: '0.75rem' },
    large: { width: 64, height: 64, fontSize: 28, labelSize: '0.875rem' }
  };

  const sizeConfig = sizes[size];

  const BadgeContent = (
    <Box
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: showLabel ? 1 : 0,
        background: config.gradient,
        borderRadius: showLabel ? '24px' : '50%',
        px: showLabel ? 2 : 0,
        py: showLabel ? 1 : 0,
        width: showLabel ? 'auto' : sizeConfig.width,
        height: showLabel ? 'auto' : sizeConfig.height,
        justifyContent: 'center',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
        border: '2px solid rgba(255, 255, 255, 0.2)',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%)',
          animation: animate ? 'shimmer 3s infinite' : 'none',
        },
        '@keyframes shimmer': {
          '0%': { left: '-100%' },
          '100%': { left: '100%' }
        }
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: config.color,
          '& svg': {
            fontSize: sizeConfig.fontSize
          }
        }}
      >
        {config.icon}
      </Box>
      {showLabel && (
        <Typography
          sx={{
            fontSize: sizeConfig.labelSize,
            fontWeight: 700,
            color: config.color,
            letterSpacing: '0.5px',
            textTransform: 'uppercase'
          }}
        >
          {config.label}
        </Typography>
      )}
    </Box>
  );

  if (animate) {
    return (
      <Tooltip title={config.description} arrow>
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: 'spring', duration: 0.6 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          style={{ display: 'inline-block' }}
        >
          {BadgeContent}
        </motion.div>
      </Tooltip>
    );
  }

  return (
    <Tooltip title={config.description} arrow>
      {BadgeContent}
    </Tooltip>
  );
};

// Badge collection component
export const BadgeCollection = ({ badges = [], size = 'small', maxDisplay = 5, animate = true }) => {
  const displayBadges = badges.slice(0, maxDisplay);
  const remainingCount = badges.length - maxDisplay;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
      {displayBadges.map((badge, index) => (
        <motion.div
          key={badge}
          initial={animate ? { opacity: 0, y: 20 } : {}}
          animate={animate ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: index * 0.1 }}
        >
          <PerformanceBadge type={badge} size={size} showLabel={false} animate={animate} />
        </motion.div>
      ))}
      {remainingCount > 0 && (
        <Chip
          label={`+${remainingCount}`}
          size="small"
          sx={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: '#fff',
            fontWeight: 600
          }}
        />
      )}
    </Box>
  );
};

// Performance indicator component
export const PerformanceIndicator = ({ performance, size = 'medium' }) => {
  const getConfig = () => {
    if (performance >= 90) return {
      label: 'Elite',
      gradient: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
      icon: <EmojiEvents />
    };
    if (performance >= 70) return {
      label: 'Excellent',
      gradient: 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)',
      icon: <TrendingUp />
    };
    if (performance >= 50) return {
      label: 'Good',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      icon: <Star />
    };
    return {
      label: 'Improving',
      gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      icon: <TrendingDown />
    };
  };

  const config = getConfig();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.05 }}
    >
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 1,
          background: config.gradient,
          borderRadius: '20px',
          px: 2,
          py: 1,
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
        }}
      >
        {config.icon}
        <Box>
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              fontSize: '0.7rem',
              opacity: 0.9,
              fontWeight: 500
            }}
          >
            Performance
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 700,
              fontSize: size === 'small' ? '0.875rem' : '1rem'
            }}
          >
            {performance}% • {config.label}
          </Typography>
        </Box>
      </Box>
    </motion.div>
  );
};

export { BADGE_CONFIGS };