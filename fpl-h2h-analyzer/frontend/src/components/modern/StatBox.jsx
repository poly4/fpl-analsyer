import React from 'react';
import { Box, Typography, Avatar, Chip } from '@mui/material';
import { motion } from 'framer-motion';
import GlassCard from './GlassCard';
import AnimatedNumber from './AnimatedNumber';
import { animations } from '../../styles/themes';

/**
 * StatBox - Modern KPI display component with glassmorphism
 * Perfect for displaying key statistics, scores, and metrics
 */
const StatBox = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = 'primary',
  variant = 'default',
  size = 'medium',
  animate = true,
  interactive = false,
  gradient = false,
  badge,
  loading = false,
  onClick,
  className = '',
  sx = {},
  ...props
}) => {

  // Size configurations
  const sizeConfig = {
    small: {
      padding: 2,
      iconSize: 32,
      titleSize: '0.875rem',
      valueSize: '1.5rem',
      subtitleSize: '0.75rem',
    },
    medium: {
      padding: 3,
      iconSize: 40,
      titleSize: '1rem',
      valueSize: '2rem',
      subtitleSize: '0.875rem',
    },
    large: {
      padding: 4,
      iconSize: 48,
      titleSize: '1.125rem',
      valueSize: '2.5rem',
      subtitleSize: '1rem',
    }
  };

  const config = sizeConfig[size];

  // Color configurations
  const colorConfig = {
    primary: {
      iconBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      iconColor: '#ffffff',
      valueColor: '#667eea',
      accentColor: 'rgba(102, 126, 234, 0.1)',
    },
    success: {
      iconBg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      iconColor: '#ffffff', 
      valueColor: '#00ff88',
      accentColor: 'rgba(0, 255, 136, 0.1)',
    },
    warning: {
      iconBg: 'linear-gradient(135deg, #ffd93d 0%, #ff9500 100%)',
      iconColor: '#000000',
      valueColor: '#ffd93d',
      accentColor: 'rgba(255, 217, 61, 0.1)',
    },
    danger: {
      iconBg: 'linear-gradient(135deg, #ff4757 0%, #ff3838 100%)',
      iconColor: '#ffffff',
      valueColor: '#ff4757',
      accentColor: 'rgba(255, 71, 87, 0.1)',
    },
    neutral: {
      iconBg: 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
      iconColor: '#ffffff',
      valueColor: 'rgba(255, 255, 255, 0.9)',
      accentColor: 'rgba(116, 185, 255, 0.1)',
    }
  };

  const colors = colorConfig[color];

  // Trend indicators
  const getTrendIcon = () => {
    if (!trend) return null;
    
    const trendConfig = {
      up: { icon: '↗️', color: '#00ff88' },
      down: { icon: '↘️', color: '#ff4757' },
      stable: { icon: '➡️', color: '#ffd93d' },
    };

    const config = trendConfig[trend];
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
        <span style={{ fontSize: '0.8rem' }}>{config.icon}</span>
        {trendValue && (
          <Typography 
            variant="caption" 
            sx={{ 
              color: config.color,
              fontWeight: 600,
              fontSize: '0.75rem'
            }}
          >
            {trendValue}
          </Typography>
        )}
      </Box>
    );
  };

  // Variant styles
  const variantStyles = {
    default: {
      background: 'rgba(255, 255, 255, 0.05)',
    },
    elevated: {
      background: 'rgba(255, 255, 255, 0.08)',
      boxShadow: '0 12px 40px rgba(31, 38, 135, 0.2)',
    },
    minimal: {
      background: 'rgba(255, 255, 255, 0.02)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
    },
    highlighted: {
      background: `linear-gradient(135deg, ${colors.accentColor}, rgba(255, 255, 255, 0.05))`,
      border: `1px solid ${colors.valueColor}40`,
    },
    gradient: {
      background: colors.iconBg,
      color: colors.iconColor,
    }
  };

  // Animation variants
  const cardVariants = {
    hidden: { opacity: 0, scale: 0.9, y: 20 },
    visible: { 
      opacity: 1, 
      scale: 1, 
      y: 0,
      transition: {
        duration: 0.5,
        ease: animations.easing.easeOut
      }
    },
    hover: interactive ? {
      scale: 1.02,
      y: -4,
      transition: {
        duration: 0.2,
        ease: animations.easing.easeOut
      }
    } : {}
  };

  const contentVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.3 }
    }
  };

  return (
    <motion.div
      variants={cardVariants}
      initial={animate ? "hidden" : false}
      animate={animate ? "visible" : false}
      whileHover={interactive ? "hover" : undefined}
      className={className}
    >
      <GlassCard
        variant="default"
        interactive={interactive}
        hover={interactive}
        padding={config.padding}
        onClick={onClick}
        sx={{
          ...variantStyles[variant],
          position: 'relative',
          overflow: 'visible',
          ...sx
        }}
        {...props}
      >
        <motion.div
          variants={contentVariants}
          initial={animate ? "hidden" : false}
          animate={animate ? "visible" : false}
        >
          {/* Header with title and badge */}
          <motion.div variants={itemVariants}>
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'flex-start',
              mb: 2 
            }}>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: config.titleSize,
                  fontWeight: 500,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}
              >
                {title}
              </Typography>
              
              {badge && (
                <Chip 
                  label={badge}
                  size="small"
                  sx={{
                    background: colors.accentColor,
                    color: colors.valueColor,
                    border: `1px solid ${colors.valueColor}40`,
                    height: 20,
                    fontSize: '0.7rem',
                    fontWeight: 600
                  }}
                />
              )}
            </Box>
          </motion.div>

          {/* Main content area */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Icon */}
            {icon && (
              <motion.div variants={itemVariants}>
                <Avatar
                  sx={{
                    width: config.iconSize,
                    height: config.iconSize,
                    background: colors.iconBg,
                    color: colors.iconColor,
                    fontSize: `${config.iconSize * 0.5}px`,
                    fontWeight: 600,
                    border: '2px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
                  }}
                >
                  {icon}
                </Avatar>
              </motion.div>
            )}

            {/* Value and content */}
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <motion.div variants={itemVariants}>
                {loading ? (
                  <Box 
                    sx={{ 
                      width: '80%', 
                      height: config.valueSize,
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '4px',
                      animation: 'pulse 1.5s ease-in-out infinite'
                    }} 
                  />
                ) : (
                  <AnimatedNumber
                    value={value}
                    variant="counter"
                    fontSize={config.valueSize}
                    fontWeight={700}
                    color={variant === 'gradient' ? colors.iconColor : colors.valueColor}
                    gradient={gradient}
                    sx={{ display: 'block' }}
                  />
                )}
              </motion.div>

              {/* Subtitle and trend */}
              {(subtitle || trend) && (
                <motion.div variants={itemVariants}>
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    mt: 0.5 
                  }}>
                    {subtitle && (
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          color: 'rgba(255, 255, 255, 0.6)',
                          fontSize: config.subtitleSize,
                          fontWeight: 400
                        }}
                      >
                        {subtitle}
                      </Typography>
                    )}
                    {getTrendIcon()}
                  </Box>
                </motion.div>
              )}
            </Box>
          </Box>

          {/* Optional highlight glow effect */}
          {variant === 'highlighted' && (
            <Box
              sx={{
                position: 'absolute',
                top: -2,
                left: -2,
                right: -2,
                bottom: -2,
                background: `linear-gradient(135deg, ${colors.valueColor}20, transparent)`,
                borderRadius: 'inherit',
                filter: 'blur(8px)',
                opacity: 0.6,
                zIndex: -1,
                pointerEvents: 'none',
              }}
            />
          )}
        </motion.div>
      </GlassCard>
    </motion.div>
  );
};

// Preset components for common FPL use cases
export const ScoreBox = (props) => (
  <StatBox 
    icon="🎯"
    color="primary"
    size="large"
    variant="elevated"
    gradient
    {...props} 
  />
);

export const RankBox = (props) => (
  <StatBox 
    icon="🏆"
    color="warning"
    size="medium"
    variant="highlighted"
    {...props} 
  />
);

export const PointsBox = (props) => (
  <StatBox 
    icon="⚡"
    color="success"
    size="medium"
    variant="default"
    {...props} 
  />
);

export const WinRateBox = (props) => (
  <StatBox 
    icon="📊"
    color="neutral"
    size="small"
    variant="minimal"
    {...props} 
  />
);

export const LiveStatBox = ({ isLive = false, ...props }) => (
  <StatBox 
    variant={isLive ? "highlighted" : "default"}
    badge={isLive ? "LIVE" : undefined}
    animate
    {...props} 
  />
);

export default StatBox;