import React, { useEffect, useState, useMemo } from 'react';
import { Typography, Box } from '@mui/material';
import { motion, useSpring, useTransform } from 'framer-motion';

/**
 * AnimatedNumber - Smooth number counter with various animation styles
 * Perfect for displaying live scores, statistics, and KPIs
 */
const AnimatedNumber = ({
  value = 0,
  duration = 1000,
  format = 'number',
  prefix = '',
  suffix = '',
  decimals = 0,
  separator = ',',
  color = 'inherit',
  fontSize = 'inherit',
  fontWeight = 600,
  variant = 'counter',
  gradient = false,
  className = '',
  sx = {},
  onComplete = () => {},
  ...props
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  // Spring animation for smooth transitions
  const springValue = useSpring(0, {
    damping: 30,
    stiffness: 150,
    restDelta: 0.001
  });

  // Transform spring value to displayed number
  const transformedValue = useTransform(springValue, (latest) => {
    return Math.round(latest * Math.pow(10, decimals)) / Math.pow(10, decimals);
  });

  // Update spring when value changes
  useEffect(() => {
    if (typeof value === 'number' && !isNaN(value)) {
      setIsAnimating(true);
      springValue.set(value);
      
      // Complete callback after animation
      const timeout = setTimeout(() => {
        setIsAnimating(false);
        onComplete();
      }, duration);
      
      return () => clearTimeout(timeout);
    }
  }, [value, springValue, duration, onComplete]);

  // Subscribe to spring value changes
  useEffect(() => {
    const unsubscribe = transformedValue.onChange((latest) => {
      setDisplayValue(latest);
    });
    return unsubscribe;
  }, [transformedValue]);

  // Format number based on type
  const formatNumber = useMemo(() => {
    const num = displayValue;
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        }).format(num);
        
      case 'percentage':
        return `${num.toFixed(decimals)}%`;
        
      case 'compact':
        return new Intl.NumberFormat('en-US', {
          notation: 'compact',
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        }).format(num);
        
      case 'ordinal':
        const pr = new Intl.PluralRules('en-US', { type: 'ordinal' });
        const suffixes = {
          one: 'st',
          two: 'nd',
          few: 'rd',
          other: 'th',
        };
        return `${Math.round(num)}${suffixes[pr.select(Math.round(num))]}`;
        
      case 'time':
        const minutes = Math.floor(num / 60);
        const seconds = Math.floor(num % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
      default:
        // Standard number formatting with thousand separators
        return num.toLocaleString('en-US', {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        });
    }
  }, [displayValue, format, decimals]);

  // Animation variants for different styles
  const variants = {
    counter: {
      hidden: { opacity: 0, scale: 0.8 },
      visible: { 
        opacity: 1, 
        scale: 1,
        transition: { duration: 0.3 }
      },
      pulse: {
        scale: [1, 1.1, 1],
        transition: { duration: 0.4 }
      }
    },
    score: {
      hidden: { opacity: 0, y: 20 },
      visible: { 
        opacity: 1, 
        y: 0,
        transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] }
      },
      update: {
        scale: [1, 1.2, 1],
        color: ['inherit', '#00ff88', 'inherit'],
        transition: { duration: 0.6 }
      }
    },
    odometer: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 },
      flip: {
        rotateX: [0, -90, 0],
        transition: { duration: 0.6 }
      }
    },
    glow: {
      hidden: { opacity: 0, filter: 'brightness(1)' },
      visible: { 
        opacity: 1, 
        filter: 'brightness(1)',
        transition: { duration: 0.3 }
      },
      highlight: {
        filter: ['brightness(1)', 'brightness(1.5)', 'brightness(1)'],
        transition: { duration: 0.8 }
      }
    }
  };

  // Style configurations
  const getStyles = () => {
    const baseStyles = {
      fontWeight,
      fontSize,
      color: gradient ? 'transparent' : color,
      lineHeight: 1,
      fontFeatureSettings: '"tnum"', // Tabular numbers for consistent width
      
      ...(gradient && {
        background: typeof gradient === 'string' 
          ? gradient 
          : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      }),
      
      ...sx
    };

    return baseStyles;
  };

  // Trigger pulse animation on value change
  const [key, setKey] = useState(0);
  useEffect(() => {
    if (variant === 'counter' || variant === 'score') {
      setKey(prev => prev + 1);
    }
  }, [value, variant]);

  return (
    <motion.div
      key={key}
      variants={variants[variant]}
      initial="hidden"
      animate="visible"
      whileHover={variant === 'glow' ? 'highlight' : undefined}
      className={className}
    >
      <Typography
        component="span"
        sx={getStyles()}
        {...props}
      >
        {prefix}
        {formatNumber}
        {suffix}
      </Typography>
      
      {/* Optional pulse effect for updates */}
      {isAnimating && (variant === 'counter' || variant === 'score') && (
        <motion.div
          initial={{ scale: 1, opacity: 0.6 }}
          animate={{ scale: 1.3, opacity: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(circle, rgba(102, 126, 234, 0.3) 0%, transparent 70%)',
            borderRadius: '50%',
            pointerEvents: 'none',
          }}
        />
      )}
    </motion.div>
  );
};

// Preset components for common use cases
export const ScoreCounter = (props) => (
  <AnimatedNumber 
    variant="score"
    fontSize="2.5rem"
    fontWeight={700}
    gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    {...props} 
  />
);

export const PointsDisplay = (props) => (
  <AnimatedNumber 
    variant="counter"
    fontSize="1.5rem"
    fontWeight={600}
    suffix=" pts"
    {...props} 
  />
);

export const RankDisplay = (props) => (
  <AnimatedNumber 
    variant="counter"
    format="ordinal"
    fontSize="1.2rem"
    fontWeight={500}
    prefix="#"
    {...props} 
  />
);

export const PercentageDisplay = (props) => (
  <AnimatedNumber 
    variant="glow"
    format="percentage"
    decimals={1}
    fontSize="1.1rem"
    fontWeight={500}
    {...props} 
  />
);

export const CompactNumber = (props) => (
  <AnimatedNumber 
    variant="counter"
    format="compact"
    fontSize="1rem"
    fontWeight={500}
    {...props} 
  />
);

export const LiveScore = ({ value, isLive = false, ...props }) => (
  <Box sx={{ position: 'relative', display: 'inline-block' }}>
    <AnimatedNumber 
      value={value}
      variant="score"
      fontSize="3rem"
      fontWeight={800}
      gradient={isLive ? "linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)" : undefined}
      {...props} 
    />
    {isLive && (
      <motion.div
        animate={{ opacity: [1, 0.3, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
        style={{
          position: 'absolute',
          top: -4,
          right: -4,
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: '#00ff88',
          boxShadow: '0 0 10px rgba(0, 255, 136, 0.5)',
        }}
      />
    )}
  </Box>
);

export default AnimatedNumber;