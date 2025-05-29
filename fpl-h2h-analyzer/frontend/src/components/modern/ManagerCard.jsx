import React from 'react';
import { Box, Typography, Avatar, Chip, IconButton } from '@mui/material';
import { motion } from 'framer-motion';
import { 
  MoreVert, 
  TrendingUp, 
  TrendingDown, 
  Remove,
  EmojiEvents
} from '@mui/icons-material';
import GlassCard from './GlassCard';
import { AnimatedNumber, LiveScore } from './AnimatedNumber';
import { BadgeCollection, PerformanceIndicator } from './PerformanceBadges';
import { glassMixins } from '../../styles/themes';

const ManagerCard = ({
  manager,
  rank = 1,
  isLive = false,
  showBadges = true,
  showPerformance = true,
  variant = 'default',
  onSelect,
  selected = false
}) => {
  const {
    player_name,
    entry_name,
    entry,
    total,
    points_for,
    matches_won,
    matches_drawn,
    matches_lost,
    badges = [],
    performance = 0,
    current_score = 0,
    rank_movement = 0,
    chip_used = null
  } = manager;

  const winRate = matches_won && (matches_won + matches_drawn + matches_lost) > 0
    ? Math.round((matches_won / (matches_won + matches_drawn + matches_lost)) * 100)
    : 0;

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        type: 'spring',
        duration: 0.6
      }
    },
    hover: {
      y: -4,
      transition: {
        type: 'spring',
        stiffness: 300
      }
    }
  };

  const getRankColor = () => {
    if (rank === 1) return 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)';
    if (rank === 2) return 'linear-gradient(135deg, #E5E5E5 0%, #B8B8B8 100%)';
    if (rank === 3) return 'linear-gradient(135deg, #CD7F32 0%, #A0522D 100%)';
    return 'rgba(255, 255, 255, 0.1)';
  };

  const getVariantGradient = () => {
    switch (variant) {
      case 'winner':
        return 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 212, 170, 0.1) 100%)';
      case 'loser':
        return 'linear-gradient(135deg, rgba(255, 71, 87, 0.1) 0%, rgba(255, 56, 56, 0.1) 100%)';
      case 'draw':
        return 'linear-gradient(135deg, rgba(255, 217, 61, 0.1) 0%, rgba(255, 149, 0, 0.1) 100%)';
      default:
        return 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)';
    }
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      onClick={onSelect}
      style={{ cursor: onSelect ? 'pointer' : 'default' }}
    >
      <GlassCard
        variant="elevated"
        gradient={getVariantGradient()}
        sx={{
          position: 'relative',
          overflow: 'visible',
          border: selected ? '2px solid rgba(102, 126, 234, 0.5)' : '1px solid rgba(255, 255, 255, 0.1)',
          transition: 'all 0.3s ease',
        }}
      >
        {/* Rank Badge */}
        <Box
          sx={{
            position: 'absolute',
            top: -12,
            left: 20,
            background: getRankColor(),
            borderRadius: '20px',
            px: 2,
            py: 0.5,
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
            border: '2px solid rgba(255, 255, 255, 0.2)',
          }}
        >
          {rank <= 3 && <EmojiEvents sx={{ fontSize: 16, color: rank === 1 ? '#000' : '#fff' }} />}
          <Typography
            variant="caption"
            sx={{
              fontWeight: 700,
              color: rank <= 3 ? '#000' : '#fff',
              fontSize: '0.75rem'
            }}
          >
            #{rank}
          </Typography>
          {rank_movement !== 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', ml: 0.5 }}>
              {rank_movement > 0 ? (
                <TrendingUp sx={{ fontSize: 14, color: '#00ff88' }} />
              ) : (
                <TrendingDown sx={{ fontSize: 14, color: '#ff4757' }} />
              )}
              <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
                {Math.abs(rank_movement)}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Menu Button */}
        <IconButton
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            color: 'rgba(255, 255, 255, 0.5)',
            '&:hover': {
              color: '#fff',
              background: 'rgba(255, 255, 255, 0.1)'
            }
          }}
        >
          <MoreVert fontSize="small" />
        </IconButton>

        {/* Manager Info */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, mt: 2 }}>
          <Avatar
            sx={{
              width: 56,
              height: 56,
              background: `linear-gradient(135deg, ${
                rank === 1 ? '#FFD700 0%, #FFA500 100%' :
                rank === 2 ? '#E5E5E5 0%, #B8B8B8 100%' :
                rank === 3 ? '#CD7F32 0%, #A0522D 100%' :
                'rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%'
              })`,
              fontSize: '1.5rem',
              fontWeight: 700,
              color: rank <= 3 ? '#000' : '#fff',
              border: '3px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
            }}
          >
            {player_name?.charAt(0) || 'M'}
          </Avatar>
          <Box sx={{ ml: 2, flex: 1 }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 0.5,
                color: '#fff'
              }}
            >
              {player_name || `Manager ${entry}`}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.875rem'
              }}
            >
              {entry_name}
            </Typography>
          </Box>
        </Box>

        {/* Stats Grid */}
        <Box 
          sx={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(3, 1fr)', 
            gap: 2,
            mb: 3
          }}
        >
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
              Total Points
            </Typography>
            <AnimatedNumber 
              value={total || 0} 
              format="number"
              sx={{ fontSize: '1.25rem', fontWeight: 700 }}
            />
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
              Win Rate
            </Typography>
            <AnimatedNumber 
              value={winRate} 
              format="percentage"
              sx={{ fontSize: '1.25rem', fontWeight: 700, color: '#00ff88' }}
            />
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
              Form
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5, mt: 0.5 }}>
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', background: '#00ff88' }} />
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', background: '#00ff88' }} />
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', background: '#ffd93d' }} />
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', background: '#ff4757' }} />
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', background: '#00ff88' }} />
            </Box>
          </Box>
        </Box>

        {/* Live Score (if applicable) */}
        {isLive && current_score > 0 && (
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)', mb: 1 }}>
              Live GW Score
            </Typography>
            <LiveScore
              value={current_score}
              isLive={true}
              gradient="linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)"
            />
            {chip_used && (
              <Chip
                label={chip_used.toUpperCase()}
                size="small"
                sx={{
                  mt: 1,
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  color: '#fff',
                  fontWeight: 600,
                  fontSize: '0.65rem'
                }}
              />
            )}
          </Box>
        )}

        {/* Performance Indicator */}
        {showPerformance && performance > 0 && (
          <Box sx={{ mb: 2 }}>
            <PerformanceIndicator performance={performance} size="small" />
          </Box>
        )}

        {/* Badges */}
        {showBadges && badges.length > 0 && (
          <Box sx={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', pt: 2 }}>
            <BadgeCollection badges={badges} size="small" maxDisplay={4} />
          </Box>
        )}
      </GlassCard>
    </motion.div>
  );
};

export default ManagerCard;