import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, IconButton, Typography } from '@mui/material';
import { 
  DragIndicator, 
  Fullscreen, 
  FullscreenExit,
  Close,
  Settings 
} from '@mui/icons-material';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import { glassMixins, animations } from '../../styles/themes';

/**
 * BentoGrid - Modern responsive grid layout system
 * Features drag-and-drop, responsive sizing, and glassmorphic styling
 */
const BentoGrid = ({
  children,
  columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 6 },
  gap = 3,
  padding = 3,
  enableDragDrop = true,
  enableFullscreen = true,
  animate = true,
  className = '',
  sx = {},
  onLayoutChange,
  ...props
}) => {
  const [items, setItems] = useState([]);
  const [fullscreenItem, setFullscreenItem] = useState(null);
  const gridRef = useRef(null);

  // Initialize items from children
  useEffect(() => {
    const childArray = React.Children.toArray(children);
    const initialItems = childArray.map((child, index) => ({
      id: child.props?.id || `item-${index}`,
      content: child,
      size: child.props?.size || 'medium',
      order: child.props?.order || index,
    }));
    setItems(initialItems);
  }, [children]);

  // Handle reordering
  const handleReorder = (newOrder) => {
    setItems(newOrder);
    if (onLayoutChange) {
      onLayoutChange(newOrder.map(item => ({ id: item.id, order: item.order })));
    }
  };

  // Grid container styles
  const gridStyles = {
    display: 'grid',
    gap: gap * 8,
    padding: padding * 8,
    gridTemplateColumns: {
      xs: `repeat(${columns.xs}, 1fr)`,
      sm: `repeat(${columns.sm}, 1fr)`,
      md: `repeat(${columns.md}, 1fr)`,
      lg: `repeat(${columns.lg}, 1fr)`,
      xl: `repeat(${columns.xl}, 1fr)`,
    },
    ...sx
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.9, y: 20 },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: animations.easing.easeOut
      }
    }
  };

  if (enableDragDrop) {
    return (
      <motion.div
        ref={gridRef}
        variants={containerVariants}
        initial={animate ? "hidden" : false}
        animate={animate ? "visible" : false}
        className={className}
      >
        <Reorder.Group
          axis="xy"
          values={items}
          onReorder={handleReorder}
          style={{ ...gridStyles, listStyle: 'none', margin: 0, padding: padding * 8 }}
        >
          <AnimatePresence>
            {items.map((item) => (
              <BentoItem
                key={item.id}
                item={item}
                itemVariants={itemVariants}
                enableFullscreen={enableFullscreen}
                onFullscreen={() => setFullscreenItem(item)}
                animate={animate}
              />
            ))}
          </AnimatePresence>
        </Reorder.Group>

        {/* Fullscreen overlay */}
        <AnimatePresence>
          {fullscreenItem && (
            <FullscreenOverlay
              item={fullscreenItem}
              onClose={() => setFullscreenItem(null)}
            />
          )}
        </AnimatePresence>
      </motion.div>
    );
  }

  // Non-draggable grid
  return (
    <motion.div
      variants={containerVariants}
      initial={animate ? "hidden" : false}
      animate={animate ? "visible" : false}
      className={className}
    >
      <Box sx={gridStyles}>
        {items.map((item, index) => (
          <motion.div
            key={item.id}
            variants={itemVariants}
            custom={index}
            style={getItemStyles(item.size)}
          >
            {item.content}
          </motion.div>
        ))}
      </Box>
    </motion.div>
  );
};

/**
 * BentoItem - Individual grid item with drag handle and controls
 */
const BentoItem = ({ 
  item, 
  itemVariants, 
  enableFullscreen, 
  onFullscreen,
  animate 
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [showControls, setShowControls] = useState(false);

  const itemStyles = {
    ...glassMixins.glassCard,
    ...getItemStyles(item.size),
    position: 'relative',
    overflow: 'hidden',
    cursor: isDragging ? 'grabbing' : 'grab',
    transition: 'all 0.3s ease-out',
    
    '&:hover': {
      ...glassMixins.glassCard['&:hover'],
      transform: isDragging ? 'scale(1.05)' : 'translateY(-2px)',
    }
  };

  return (
    <Reorder.Item
      value={item}
      dragListener={false}
      dragControls={undefined}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={() => setIsDragging(false)}
      whileDrag={{ scale: 1.05, zIndex: 1000 }}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(false)}
    >
      <motion.div
        variants={itemVariants}
        layoutId={item.id}
        style={itemStyles}
      >
        {/* Drag handle and controls */}
        <AnimatePresence>
          {showControls && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                position: 'absolute',
                top: 8,
                right: 8,
                display: 'flex',
                gap: 4,
                zIndex: 10
              }}
            >
              <IconButton
                size="small"
                sx={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(10px)',
                  color: 'rgba(255, 255, 255, 0.8)',
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.2)',
                  }
                }}
              >
                <DragIndicator fontSize="small" />
              </IconButton>
              
              {enableFullscreen && (
                <IconButton
                  size="small"
                  onClick={onFullscreen}
                  sx={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    color: 'rgba(255, 255, 255, 0.8)',
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.2)',
                    }
                  }}
                >
                  <Fullscreen fontSize="small" />
                </IconButton>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <Box sx={{ position: 'relative', zIndex: 1, height: '100%' }}>
          {item.content}
        </Box>

        {/* Drag indicator overlay */}
        {isDragging && (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(102, 126, 234, 0.1)',
              border: '2px dashed rgba(102, 126, 234, 0.5)',
              borderRadius: 'inherit',
              pointerEvents: 'none',
            }}
          />
        )}
      </motion.div>
    </Reorder.Item>
  );
};

/**
 * FullscreenOverlay - Fullscreen view for grid items
 */
const FullscreenOverlay = ({ item, onClose }) => {
  useEffect(() => {
    // Lock body scroll when fullscreen
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}
      onClick={onClose}
    >
      <motion.div
        layoutId={item.id}
        style={{
          width: '90%',
          height: '90%',
          maxWidth: '1400px',
          maxHeight: '900px',
          ...glassMixins.glassModal,
          padding: 32,
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            background: 'rgba(255, 255, 255, 0.1)',
            color: 'rgba(255, 255, 255, 0.9)',
            '&:hover': {
              background: 'rgba(255, 255, 255, 0.2)',
            }
          }}
        >
          <FullscreenExit />
        </IconButton>

        <Box sx={{ height: '100%', overflow: 'auto' }}>
          {item.content}
        </Box>
      </motion.div>
    </motion.div>
  );
};

/**
 * Get grid item styles based on size
 */
const getItemStyles = (size) => {
  const sizeMap = {
    small: {
      gridColumn: 'span 1',
      gridRow: 'span 1',
      minHeight: 200,
    },
    medium: {
      gridColumn: 'span 2',
      gridRow: 'span 1',
      minHeight: 250,
    },
    large: {
      gridColumn: 'span 2',
      gridRow: 'span 2',
      minHeight: 400,
    },
    wide: {
      gridColumn: 'span 3',
      gridRow: 'span 1',
      minHeight: 250,
    },
    tall: {
      gridColumn: 'span 1',
      gridRow: 'span 2',
      minHeight: 400,
    },
    hero: {
      gridColumn: 'span 4',
      gridRow: 'span 2',
      minHeight: 500,
    }
  };

  return sizeMap[size] || sizeMap.medium;
};

/**
 * BentoCard - Pre-styled card for use in BentoGrid
 */
export const BentoCard = ({
  id,
  size = 'medium',
  order,
  title,
  subtitle,
  icon,
  children,
  gradient = false,
  interactive = false,
  ...props
}) => {
  return (
    <Box
      id={id}
      size={size}
      order={order}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
      {...props}
    >
      {(title || subtitle || icon) && (
        <Box sx={{ mb: 2 }}>
          {icon && (
            <Box sx={{ mb: 1 }}>
              {icon}
            </Box>
          )}
          {title && (
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 600,
                background: gradient ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'inherit',
                WebkitBackgroundClip: gradient ? 'text' : 'inherit',
                WebkitTextFillColor: gradient ? 'transparent' : 'inherit',
                backgroundClip: gradient ? 'text' : 'inherit',
              }}
            >
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography 
              variant="body2" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.7)',
                mt: 0.5 
              }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
      )}
      
      <Box sx={{ flex: 1, minHeight: 0 }}>
        {children}
      </Box>
    </Box>
  );
};

// Export size constants
export const BENTO_SIZES = {
  SMALL: 'small',
  MEDIUM: 'medium',
  LARGE: 'large',
  WIDE: 'wide',
  TALL: 'tall',
  HERO: 'hero'
};

export default BentoGrid;