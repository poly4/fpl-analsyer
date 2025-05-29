import React, { forwardRef } from 'react';
import { Card, CardContent, Box } from '@mui/material';
import { motion } from 'framer-motion';
import { glassMixins, animations } from '../../styles/themes';

/**
 * GlassCard - Modern glassmorphic card component
 * Base component for all card-based UI elements
 */
const GlassCard = forwardRef(({
  children,
  variant = 'default',
  hover = true,
  interactive = false,
  animate = true,
  padding = 3,
  borderRadius = 'lg',
  gradient = false,
  glowEffect = false,
  className = '',
  sx = {},
  onClick,
  ...props
}, ref) => {

  // Variant styles
  const variantStyles = {
    default: glassMixins.glassCard,
    glass: glassMixins.glass,
    nav: glassMixins.glassNav,
    modal: glassMixins.glassModal,
    button: glassMixins.glassButton,
    status: glassMixins.glassStatus,
    elevated: {
      ...glassMixins.glassCard,
      background: 'rgba(255, 255, 255, 0.08)',
      boxShadow: '0 12px 40px rgba(31, 38, 135, 0.2)',
    },
    minimal: {
      background: 'rgba(255, 255, 255, 0.02)',
      backdropFilter: 'blur(10px)',
      WebkitBackdropFilter: 'blur(10px)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '12px',
      transition: 'all 0.3s ease-out',
    },
    solid: {
      background: 'var(--dark-surface)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '16px',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
    }
  };

  // Border radius values
  const radiusMap = {
    none: '0',
    sm: '0.25rem',
    md: '0.75rem',
    lg: '1rem',
    xl: '1.5rem',
    '2xl': '2rem',
    full: '9999px'
  };

  // Animation variants
  const cardVariants = {
    hidden: { 
      opacity: 0, 
      scale: 0.95,
      y: 20 
    },
    visible: { 
      opacity: 1, 
      scale: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: animations.easing.easeOut
      }
    },
    hover: hover ? {
      scale: interactive ? 1.02 : 1.01,
      y: -2,
      transition: {
        duration: 0.2,
        ease: animations.easing.easeOut
      }
    } : {},
    tap: interactive ? {
      scale: 0.98,
      transition: {
        duration: 0.1
      }
    } : {}
  };

  // Combined styles
  const combinedStyles = {
    ...variantStyles[variant],
    borderRadius: radiusMap[borderRadius],
    cursor: interactive || onClick ? 'pointer' : 'default',
    position: 'relative',
    overflow: 'hidden',
    
    // Gradient overlay
    ...(gradient && {
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: typeof gradient === 'string' ? gradient : 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
        borderRadius: 'inherit',
        pointerEvents: 'none',
        zIndex: 0,
      }
    }),
    
    // Glow effect
    ...(glowEffect && {
      '&::after': {
        content: '""',
        position: 'absolute',
        top: -2,
        left: -2,
        right: -2,
        bottom: -2,
        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3))',
        borderRadius: 'inherit',
        filter: 'blur(8px)',
        opacity: 0,
        transition: 'opacity 0.3s ease-out',
        zIndex: -1,
      },
      '&:hover::after': hover ? {
        opacity: 1,
      } : {}
    }),
    
    // Interactive styles
    ...(interactive && {
      '&:hover': {
        ...variantStyles[variant]['&:hover'],
        transform: hover ? 'translateY(-2px) scale(1.02)' : 'translateY(-2px)',
      },
      '&:active': {
        transform: 'translateY(0) scale(0.98)',
      }
    }),
    
    // Custom styles
    ...sx
  };

  const MotionCard = motion(Card);

  const cardContent = (
    <CardContent 
      sx={{ 
        p: padding,
        '&:last-child': { pb: padding },
        position: 'relative',
        zIndex: 1,
      }}
    >
      {children}
    </CardContent>
  );

  // Render with or without animation
  if (animate) {
    return (
      <MotionCard
        ref={ref}
        className={className}
        sx={combinedStyles}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        whileHover="hover"
        whileTap="tap"
        onClick={onClick}
        {...props}
      >
        {cardContent}
      </MotionCard>
    );
  }

  return (
    <Card
      ref={ref}
      className={className}
      sx={combinedStyles}
      onClick={onClick}
      {...props}
    >
      {cardContent}
    </Card>
  );
});

GlassCard.displayName = 'GlassCard';

// Preset variants for common use cases
export const GlassContainer = (props) => (
  <GlassCard variant="glass" padding={4} borderRadius="xl" {...props} />
);

export const GlassButton = (props) => (
  <GlassCard 
    variant="button" 
    interactive 
    hover 
    padding={2} 
    borderRadius="md" 
    {...props} 
  />
);

export const GlassModal = (props) => (
  <GlassCard 
    variant="modal" 
    padding={4} 
    borderRadius="2xl" 
    animate={false} 
    {...props} 
  />
);

export const GlassStatus = (props) => (
  <GlassCard 
    variant="status" 
    padding={1.5} 
    borderRadius="md" 
    hover={false} 
    {...props} 
  />
);

export const MinimalCard = (props) => (
  <GlassCard 
    variant="minimal" 
    padding={3} 
    borderRadius="lg" 
    {...props} 
  />
);

export const ElevatedCard = (props) => (
  <GlassCard 
    variant="elevated" 
    padding={3} 
    borderRadius="xl" 
    glowEffect 
    {...props} 
  />
);

export default GlassCard;