import React, { useState, useEffect } from 'react';
import {
  BottomNavigation,
  BottomNavigationAction,
  Paper,
  Badge,
  useTheme,
  SwipeableDrawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  IconButton,
  Typography,
  Box,
  Avatar,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Fab,
  Slide,
  useMediaQuery
} from '@mui/material';
import {
  Home,
  Analytics,
  Notifications,
  Settings,
  Menu,
  Close,
  Dashboard,
  Timeline,
  SportsSoccer,
  TrendingUp,
  Psychology,
  Casino,
  ExpandMore,
  DarkMode,
  LightMode,
  Accessibility,
  Language,
  Speed,
  Info,
  Feedback,
  Help
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
// Removed custom theme import - using Material-UI theme directly

const navigationItems = [
  {
    label: 'Dashboard',
    value: 'dashboard',
    icon: <Dashboard />,
    badge: null
  },
  {
    label: 'Analytics',
    value: 'analytics', 
    icon: <Analytics />,
    badge: null
  },
  {
    label: 'Live',
    value: 'live',
    icon: <SportsSoccer />,
    badge: 3
  },
  {
    label: 'Simulator',
    value: 'simulator',
    icon: <Psychology />,
    badge: null
  }
];

const drawerItems = [
  {
    category: 'Main',
    items: [
      { label: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
      { label: 'H2H Battles', icon: <SportsSoccer />, path: '/battles' },
      { label: 'Analytics', icon: <Analytics />, path: '/analytics' },
      { label: 'Live Updates', icon: <Timeline />, path: '/live' },
    ]
  },
  {
    category: 'Tools', 
    items: [
      { label: 'Match Simulator', icon: <Psychology />, path: '/simulator' },
      { label: 'Strategy Advisor', icon: <TrendingUp />, path: '/strategy' },
      { label: 'Scenario Analysis', icon: <Casino />, path: '/scenarios' },
    ]
  },
  {
    category: 'Settings',
    items: [
      { label: 'Preferences', icon: <Settings />, path: '/settings' },
      { label: 'Notifications', icon: <Notifications />, path: '/notifications' },
      { label: 'About', icon: <Info />, path: '/about' },
      { label: 'Help', icon: <Help />, path: '/help' },
    ]
  }
];

const TouchGesture = ({ children, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown }) => {
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);
  
  const minSwipeDistance = 50;
  
  const onTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    });
  };
  
  const onTouchMove = (e) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    });
  };
  
  const onTouchEndHandler = () => {
    if (!touchStart || !touchEnd) return;
    
    const deltaX = touchStart.x - touchEnd.x;
    const deltaY = touchStart.y - touchEnd.y;
    
    const isLeftSwipe = deltaX > minSwipeDistance;
    const isRightSwipe = deltaX < -minSwipeDistance;
    const isUpSwipe = deltaY > minSwipeDistance;
    const isDownSwipe = deltaY < -minSwipeDistance;
    
    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft();
    } else if (isRightSwipe && onSwipeRight) {
      onSwipeRight();
    } else if (isUpSwipe && onSwipeUp) {
      onSwipeUp();
    } else if (isDownSwipe && onSwipeDown) {
      onSwipeDown();
    }
  };
  
  return (
    <div
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEndHandler}
      style={{ width: '100%', height: '100%' }}
    >
      {children}
    </div>
  );
};

const FloatingActionButton = ({ onClick, icon, color = 'primary' }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  if (!isMobile) return null;
  
  return (
    <motion.div
      initial={{ scale: 0, rotate: -180 }}
      animate={{ scale: 1, rotate: 0 }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      style={{
        position: 'fixed',
        bottom: 90,
        right: 16,
        zIndex: 1000
      }}
    >
      <Fab
        color={color}
        onClick={onClick}
        sx={{
          backdropFilter: 'blur(10px)',
          background: theme.palette.mode === 'dark' 
            ? 'rgba(187, 134, 252, 0.8)'
            : 'rgba(98, 0, 238, 0.8)',
        }}
      >
        {icon}
      </Fab>
    </motion.div>
  );
};

export default function MobileNavigation({ currentPage, onPageChange }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifications, setNotifications] = useState(3);
  const [showFab, setShowFab] = useState(true);
  
  // Hide/show elements based on scroll
  useEffect(() => {
    let lastScrollY = window.scrollY;
    
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const scrollingDown = currentScrollY > lastScrollY;
      
      setShowFab(!scrollingDown || currentScrollY < 100);
      lastScrollY = currentScrollY;
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  if (!isMobile) {
    return null;
  }
  
  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };
  
  const handleNavigationChange = (event, newValue) => {
    onPageChange(newValue);
  };
  
  const handleMenuItemClick = (path) => {
    onPageChange(path.replace('/', ''));
    setDrawerOpen(false);
  };
  
  const getTotalBadgeCount = () => {
    return navigationItems.reduce((total, item) => total + (item.badge || 0), 0);
  };
  
  return (
    <>
      {/* Floating Action Button */}
      <AnimatePresence>
        {showFab && (
          <FloatingActionButton
            onClick={handleDrawerToggle}
            icon={<Menu />}
            color="primary"
          />
        )}
      </AnimatePresence>
      
      {/* Bottom Navigation */}
      <Slide direction="up" in={showFab} mountOnEnter unmountOnExit>
        <Paper
          sx={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            zIndex: 1000,
            backdropFilter: 'blur(20px)',
            background: theme.palette.mode === 'dark' 
              ? 'rgba(30, 30, 30, 0.8)'
              : 'rgba(255, 255, 255, 0.8)',
            borderTop: `1px solid ${theme.palette.divider}`,
          }}
          elevation={8}
        >
          <TouchGesture onSwipeUp={() => setDrawerOpen(true)}>
            <BottomNavigation
              value={currentPage}
              onChange={handleNavigationChange}
              showLabels
              sx={{
                background: 'transparent',
                '& .MuiBottomNavigationAction-root': {
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                  },
                  '&.Mui-selected': {
                    transform: 'translateY(-2px)',
                  },
                },
              }}
            >
              {navigationItems.map((item) => (
                <BottomNavigationAction
                  key={item.value}
                  label={item.label}
                  value={item.value}
                  icon={
                    item.badge ? (
                      <Badge badgeContent={item.badge} color="error">
                        {item.icon}
                      </Badge>
                    ) : (
                      item.icon
                    )
                  }
                />
              ))}
            </BottomNavigation>
          </TouchGesture>
        </Paper>
      </Slide>
      
      {/* Side Drawer */}
      <SwipeableDrawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onOpen={() => setDrawerOpen(true)}
        disableSwipeToOpen
        PaperProps={{
          sx: {
            width: 280,
            backdropFilter: 'blur(20px)',
            background: theme.palette.mode === 'dark'
              ? 'rgba(30, 30, 30, 0.95)'
              : 'rgba(255, 255, 255, 0.95)',
          }
        }}
      >
        <TouchGesture onSwipeLeft={() => setDrawerOpen(false)}>
          <Box sx={{ width: 280 }}>
            {/* Header */}
            <Box
              sx={{
                p: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: `1px solid ${theme.palette.divider}`,
              }}
            >
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                  <SportsSoccer />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    FPL H2H
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Analyzer Pro
                  </Typography>
                </Box>
              </Box>
              
              <IconButton onClick={() => setDrawerOpen(false)}>
                <Close />
              </IconButton>
            </Box>
            
            {/* Quick Stats */}
            <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
              <Box display="flex" gap={1} mb={1}>
                <Chip 
                  label={`${getTotalBadgeCount()} Updates`} 
                  size="small" 
                  color="primary"
                  variant="outlined"
                />
                <Chip 
                  label="Online" 
                  size="small" 
                  color="success"
                  variant="outlined"
                />
              </Box>
              <Typography variant="caption" color="text.secondary">
                Last updated: {new Date().toLocaleTimeString()}
              </Typography>
            </Box>
            
            {/* Navigation Items */}
            {drawerItems.map((category, categoryIndex) => (
              <Accordion 
                key={category.category}
                defaultExpanded={categoryIndex === 0}
                elevation={0}
                sx={{ 
                  background: 'transparent',
                  '&:before': { display: 'none' }
                }}
              >
                <AccordionSummary 
                  expandIcon={<ExpandMore />}
                  sx={{ 
                    minHeight: 48,
                    '& .MuiAccordionSummary-content': { 
                      margin: '8px 0' 
                    }
                  }}
                >
                  <Typography variant="subtitle2" fontWeight="bold">
                    {category.category}
                  </Typography>
                </AccordionSummary>
                
                <AccordionDetails sx={{ pt: 0 }}>
                  <List dense>
                    {category.items.map((item) => {
                      const isSelected = currentPage === item.path.replace('/', '');
                      
                      return (
                        <motion.div
                          key={item.label}
                          whileHover={{ x: 4 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <ListItemButton
                            selected={isSelected}
                            onClick={() => handleMenuItemClick(item.path)}
                            sx={{
                              borderRadius: 2,
                              mb: 0.5,
                              transition: 'all 0.2s ease-in-out',
                              '&.Mui-selected': {
                                bgcolor: theme.palette.primary.main + '20',
                                '&:hover': {
                                  bgcolor: theme.palette.primary.main + '30',
                                },
                              },
                            }}
                          >
                            <ListItemIcon
                              sx={{
                                color: isSelected 
                                  ? theme.palette.primary.main 
                                  : theme.palette.text.secondary,
                                minWidth: 40,
                              }}
                            >
                              {item.icon}
                            </ListItemIcon>
                            <ListItemText 
                              primary={item.label}
                              primaryTypographyProps={{
                                fontWeight: isSelected ? 600 : 400,
                                color: isSelected 
                                  ? theme.palette.primary.main 
                                  : theme.palette.text.primary,
                              }}
                            />
                          </ListItemButton>
                        </motion.div>
                      );
                    })}
                  </List>
                </AccordionDetails>
              </Accordion>
            ))}
            
            <Divider sx={{ my: 2 }} />
            
            {/* Theme and Accessibility Controls */}
            <Box sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                Preferences
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={theme.palette.mode === 'dark'}
                    onChange={() => {}} // Placeholder - theme switching handled by parent
                    icon={<LightMode fontSize="small" />}
                    checkedIcon={<DarkMode fontSize="small" />}
                  />
                }
                label="Dark Mode"
                sx={{ mb: 1, display: 'flex', justifyContent: 'space-between' }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={false} // Placeholder for high contrast
                    onChange={() => {}} // Placeholder - accessibility handled by parent
                    icon={<Accessibility fontSize="small" />}
                    checkedIcon={<Accessibility fontSize="small" />}
                  />
                }
                label="High Contrast"
                sx={{ mb: 1, display: 'flex', justifyContent: 'space-between' }}
              />
            </Box>
            
            {/* Footer */}
            <Box
              sx={{
                mt: 'auto',
                p: 2,
                borderTop: `1px solid ${theme.palette.divider}`,
                textAlign: 'center',
              }}
            >
              <Typography variant="caption" color="text.secondary">
                FPL H2H Analyzer v2.0
              </Typography>
              <br />
              <Typography variant="caption" color="text.secondary">
                Built with ❤️ for FPL managers
              </Typography>
            </Box>
          </Box>
        </TouchGesture>
      </SwipeableDrawer>
    </>
  );
}