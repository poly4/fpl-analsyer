import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence, useAnimation } from 'framer-motion';
import { Box, IconButton } from '@mui/material';
import { CheckCircle, TrendingUp, EmojiEvents } from '@mui/icons-material';
import { 
  hoverScale, 
  animateNumber, 
  successPulse, 
  successBounce,
  createParticles,
  ANIMATION_DURATION 
} from '../utils/animations';

// Animated button with press effect
export const AnimatedButton = ({ children, onClick, variant = 'primary', ...props }) => {
  const handleClick = (e) => {
    // Create ripple effect
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    button.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
    
    if (onClick) onClick(e);
  };

  return (
    <motion.button
      className={`animated-button ${variant}`}
      onClick={handleClick}
      whileHover={{ scale: 1.05, boxShadow: '0 5px 20px rgba(102, 126, 234, 0.4)' }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      {...props}
    >
      {children}
      <style jsx>{`
        .animated-button {
          position: relative;
          overflow: hidden;
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        
        .animated-button.primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }
        
        .ripple {
          position: absolute;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.5);
          transform: scale(0);
          animation: ripple 0.6s ease-out;
        }
        
        @keyframes ripple {
          to {
            transform: scale(4);
            opacity: 0;
          }
        }
      `}</style>
    </motion.button>
  );
};

// Animated number counter
export const AnimatedNumber = ({ 
  value, 
  duration = 1, 
  prefix = '', 
  suffix = '', 
  decimals = 0,
  celebrate = false 
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);
  const controls = useAnimation();

  useEffect(() => {
    let startTime;
    let animationFrame;
    
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
      
      // Easing function
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const currentValue = easeOutQuart * value;
      
      setDisplayValue(currentValue);
      
      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      } else {
        if (celebrate && value > 0) {
          setShowCelebration(true);
          controls.start('animate');
          setTimeout(() => setShowCelebration(false), 2000);
        }
      }
    };
    
    animationFrame = requestAnimationFrame(animate);
    
    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [value, duration, celebrate, controls]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{ position: 'relative', display: 'inline-block' }}
    >
      <motion.span
        animate={controls}
        variants={celebrate ? successPulse : {}}
        style={{ fontSize: 'inherit', fontWeight: 'inherit' }}
      >
        {prefix}{displayValue.toFixed(decimals)}{suffix}
      </motion.span>
      
      {showCelebration && (
        <AnimatePresence>
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            style={{
              position: 'absolute',
              top: '-40px',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 10
            }}
          >
            <EmojiEvents style={{ color: '#ffd700', fontSize: '2rem' }} />
          </motion.div>
        </AnimatePresence>
      )}
    </motion.div>
  );
};

// Card hover transform
export const AnimatedCard = ({ children, delay = 0, ...props }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      whileHover={{
        y: -5,
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)',
        transition: { duration: 0.3 }
      }}
      style={{
        position: 'relative',
        transformStyle: 'preserve-3d',
        ...props.style
      }}
      {...props}
    >
      <motion.div
        animate={{ rotateX: isHovered ? 5 : 0, rotateY: isHovered ? 5 : 0 }}
        transition={{ duration: 0.3 }}
      >
        {children}
      </motion.div>
    </motion.div>
  );
};

// Success celebration component
export const SuccessCelebration = ({ show, message = 'Success!' }) => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    if (show) {
      const newParticles = createParticles(window.innerWidth / 2, window.innerHeight / 2, 30);
      setParticles(newParticles);
      
      setTimeout(() => setParticles([]), 2000);
    }
  }, [show]);

  return (
    <AnimatePresence>
      {show && (
        <>
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 9999,
              background: 'rgba(0, 0, 0, 0.8)',
              borderRadius: '20px',
              padding: '40px',
              textAlign: 'center'
            }}
          >
            <motion.div
              animate={successBounce.animate}
              style={{ marginBottom: '20px' }}
            >
              <CheckCircle style={{ fontSize: '4rem', color: '#00ff88' }} />
            </motion.div>
            <motion.h2
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              style={{ color: 'white', marginBottom: 0 }}
            >
              {message}
            </motion.h2>
          </motion.div>
          
          {/* Particles */}
          {particles.map(particle => (
            <motion.div
              key={particle.id}
              initial={particle.initial}
              animate={particle.animate}
              transition={particle.transition}
              style={{
                position: 'fixed',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#00ff88',
                zIndex: 9998
              }}
            />
          ))}
        </>
      )}
    </AnimatePresence>
  );
};

// Loading skeleton with shimmer
export const AnimatedSkeleton = ({ width = '100%', height = 20, variant = 'text' }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{
        width,
        height: variant === 'text' ? height : 'auto',
        borderRadius: variant === 'circular' ? '50%' : variant === 'rectangular' ? '8px' : '4px',
        background: 'linear-gradient(90deg, #1a1a2e 25%, #2a2a3e 50%, #1a1a2e 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite'
      }}
    >
      {variant === 'rectangular' && (
        <div style={{ paddingTop: height, width: '100%' }} />
      )}
      
      <style jsx>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </motion.div>
  );
};

// Morphing score indicator
export const AnimatedScoreChange = ({ oldScore, newScore, showDiff = true }) => {
  const diff = newScore - oldScore;
  const isPositive = diff > 0;
  
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <AnimatedNumber value={newScore} duration={0.5} />
      
      {showDiff && diff !== 0 && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            color: isPositive ? '#00ff88' : '#ff4757',
            fontSize: '0.875rem',
            fontWeight: 600
          }}
        >
          <TrendingUp 
            style={{ 
              fontSize: '1rem',
              transform: isPositive ? 'none' : 'rotate(180deg)' 
            }} 
          />
          {Math.abs(diff)}
        </motion.div>
      )}
    </Box>
  );
};

// Page transition wrapper
export const AnimatedPage = ({ children, variant = 'fade' }) => {
  const pageVariants = {
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 }
    },
    slideLeft: {
      initial: { x: '100%', opacity: 0 },
      animate: { x: 0, opacity: 1 },
      exit: { x: '-100%', opacity: 0 }
    },
    slideUp: {
      initial: { y: '100%', opacity: 0 },
      animate: { y: 0, opacity: 1 },
      exit: { y: '-100%', opacity: 0 }
    }
  };

  return (
    <motion.div
      variants={pageVariants[variant]}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      style={{ width: '100%', height: '100%' }}
    >
      {children}
    </motion.div>
  );
};

export default {
  AnimatedButton,
  AnimatedNumber,
  AnimatedCard,
  SuccessCelebration,
  AnimatedSkeleton,
  AnimatedScoreChange,
  AnimatedPage
};