/**
 * 2025 Modern Design System for FPL H2H Analyzer
 * Comprehensive glassmorphism theme with advanced color palette
 */

// Core Color Palette - 2025 Specification
export const colors = {
  // Base Dark Theme
  dark: {
    bg: '#0a0a0f',
    surface: '#1a1a2e', 
    elevated: '#16213e',
    paper: '#1e1e2e',
  },
  
  // Glassmorphism Colors
  glass: {
    bg: 'rgba(255, 255, 255, 0.05)',
    bgHover: 'rgba(255, 255, 255, 0.08)',
    bgActive: 'rgba(255, 255, 255, 0.12)',
    border: 'rgba(255, 255, 255, 0.1)',
    borderHover: 'rgba(255, 255, 255, 0.2)',
    shadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
    shadowHover: '0 12px 40px rgba(31, 38, 135, 0.2)',
    shadowLarge: '0 20px 60px rgba(0, 0, 0, 0.5)',
  },
  
  // Primary Gradients
  gradients: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    warning: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    danger: 'linear-gradient(135deg, #ff4757 0%, #ff3838 100%)',
    neutral: 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
    // Special FPL gradients
    captain: 'linear-gradient(135deg, #ffd93d 0%, #ff9500 100%)',
    differential: 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)',
    prediction: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
  },
  
  // Semantic Colors
  semantic: {
    // FPL-specific colors
    win: '#00ff88',
    draw: '#ffd93d', 
    loss: '#ff4757',
    captain: '#ffd93d',
    viceCaptain: '#74b9ff',
    differential: '#00ff88',
    
    // Standard semantic colors
    success: '#2ed573',
    warning: '#ffa502',
    danger: '#ff3838',
    info: '#3742fa',
    
    // Data visualization colors
    viz: {
      primary: '#667eea',
      secondary: '#f093fb',
      tertiary: '#4facfe',
      quaternary: '#ffd93d',
      quinary: '#ff4757',
      senary: '#2ed573',
    }
  },
  
  // Text Colors with proper contrast
  text: {
    primary: 'rgba(255, 255, 255, 0.95)',
    secondary: 'rgba(255, 255, 255, 0.75)',
    tertiary: 'rgba(255, 255, 255, 0.6)',
    disabled: 'rgba(255, 255, 255, 0.4)',
    inverse: 'rgba(0, 0, 0, 0.87)',
    
    // Gradient text effects
    gradient: {
      primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      success: 'linear-gradient(135deg, #00ff88 0%, #00d4aa 100%)',
      warning: 'linear-gradient(135deg, #ffd93d 0%, #ff9500 100%)',
    }
  },
  
  // Background overlays
  backdrop: {
    modal: 'rgba(0, 0, 0, 0.5)',
    drawer: 'rgba(0, 0, 0, 0.6)',
    loading: 'rgba(10, 10, 15, 0.8)',
  }
};

// Typography System
export const typography = {
  fontFamily: {
    primary: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    mono: '"JetBrains Mono", "Fira Code", "Consolas", monospace',
  },
  
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px  
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
    '6xl': '3.75rem', // 60px
  },
  
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },
  
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
  
  letterSpacing: {
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
  }
};

// Spacing System (8px base unit)
export const spacing = {
  px: '1px',
  0: '0',
  0.5: '0.125rem', // 2px
  1: '0.25rem',    // 4px
  1.5: '0.375rem', // 6px
  2: '0.5rem',     // 8px
  2.5: '0.625rem', // 10px
  3: '0.75rem',    // 12px
  3.5: '0.875rem', // 14px
  4: '1rem',       // 16px
  5: '1.25rem',    // 20px
  6: '1.5rem',     // 24px
  7: '1.75rem',    // 28px
  8: '2rem',       // 32px
  9: '2.25rem',    // 36px
  10: '2.5rem',    // 40px
  11: '2.75rem',   // 44px
  12: '3rem',      // 48px
  14: '3.5rem',    // 56px
  16: '4rem',      // 64px
  20: '5rem',      // 80px
  24: '6rem',      // 96px
  28: '7rem',      // 112px
  32: '8rem',      // 128px
};

// Border Radius System
export const borderRadius = {
  none: '0',
  sm: '0.25rem',   // 4px
  base: '0.5rem',  // 8px
  md: '0.75rem',   // 12px
  lg: '1rem',      // 16px
  xl: '1.5rem',    // 24px
  '2xl': '2rem',   // 32px
  '3xl': '3rem',   // 48px
  full: '9999px',
};

// Animation System
export const animations = {
  // Timing functions
  easing: {
    ease: [0.25, 0.1, 0.25, 1],
    easeIn: [0.4, 0, 1, 1],
    easeOut: [0, 0, 0.2, 1],
    easeInOut: [0.4, 0, 0.2, 1],
    spring: [0.68, -0.55, 0.265, 1.55],
    bounce: [0.68, -0.55, 0.265, 1.55],
  },
  
  // Duration scale
  duration: {
    instant: 0,
    fast: 150,      // Quick feedback
    normal: 300,    // Standard transitions
    slow: 500,      // Complex animations
    slower: 800,    // Page transitions
    slowest: 1200,  // Loading animations
  },
  
  // Stagger delays
  stagger: {
    children: 50,   // List items
    cards: 100,     // Card grids
    sections: 150,  // Page sections
    tabs: 80,       // Navigation tabs
  },
  
  // Common animation variants for Framer Motion
  variants: {
    fadeIn: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 }
    },
    slideUp: {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 }
    },
    slideDown: {
      hidden: { opacity: 0, y: -20 },
      visible: { opacity: 1, y: 0 }
    },
    slideLeft: {
      hidden: { opacity: 0, x: 20 },
      visible: { opacity: 1, x: 0 }
    },
    slideRight: {
      hidden: { opacity: 0, x: -20 },
      visible: { opacity: 1, x: 0 }
    },
    scale: {
      hidden: { opacity: 0, scale: 0.95 },
      visible: { opacity: 1, scale: 1 }
    },
    staggerContainer: {
      hidden: {},
      visible: {
        transition: {
          staggerChildren: 0.1
        }
      }
    }
  }
};

// Glassmorphism Mixins
export const glassMixins = {
  // Primary glass container
  glass: {
    background: colors.glass.bg,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)', // Safari support
    border: `1px solid ${colors.glass.border}`,
    borderRadius: borderRadius.xl,
    boxShadow: colors.glass.shadow,
    transition: 'all 0.3s ease-out',
    
    '&:hover': {
      background: colors.glass.bgHover,
      border: `1px solid ${colors.glass.borderHover}`,
      boxShadow: colors.glass.shadowHover,
      transform: 'translateY(-2px)',
    }
  },
  
  // Glass card variant
  glassCard: {
    background: colors.glass.bg,
    backdropFilter: 'blur(15px)',
    WebkitBackdropFilter: 'blur(15px)',
    border: `1px solid ${colors.glass.border}`,
    borderRadius: borderRadius.lg,
    boxShadow: colors.glass.shadow,
    transition: 'all 0.3s ease-out',
    
    '&:hover': {
      background: colors.glass.bgHover,
      transform: 'translateY(-1px)',
      boxShadow: colors.glass.shadowHover,
    }
  },
  
  // Glass navigation
  glassNav: {
    background: 'rgba(255, 255, 255, 0.03)',
    backdropFilter: 'blur(30px)',
    WebkitBackdropFilter: 'blur(30px)',
    border: `1px solid ${colors.glass.border}`,
    borderRadius: borderRadius.full,
    boxShadow: colors.glass.shadow,
    transition: 'all 0.3s ease-out',
    
    '&:hover': {
      background: colors.glass.bgHover,
      border: `1px solid ${colors.glass.borderHover}`,
    },
    
    '&.active': {
      background: colors.gradients.primary,
      border: '1px solid transparent',
      boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
    }
  },
  
  // Glass modal
  glassModal: {
    background: 'rgba(26, 26, 46, 0.9)',
    backdropFilter: 'blur(30px)',
    WebkitBackdropFilter: 'blur(30px)',
    border: `1px solid ${colors.glass.border}`,
    borderRadius: borderRadius['2xl'],
    boxShadow: colors.glass.shadowLarge,
  },
  
  // Glass button
  glassButton: {
    background: colors.glass.bg,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    border: `1px solid ${colors.glass.borderHover}`,
    borderRadius: borderRadius.md,
    color: colors.text.primary,
    transition: 'all 0.3s ease-out',
    
    '&:hover': {
      background: colors.glass.bgHover,
      transform: 'translateY(-2px)',
      boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
    },
    
    '&:active': {
      transform: 'translateY(0)',
    }
  },
  
  // Glass status indicator
  glassStatus: {
    background: colors.glass.bg,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    border: `1px solid ${colors.glass.borderHover}`,
    borderRadius: borderRadius.md,
    padding: `${spacing[2]} ${spacing[4]}`,
    display: 'flex',
    alignItems: 'center',
    gap: spacing[2],
    transition: 'all 0.3s ease-out',
  }
};

// Breakpoints for responsive design
export const breakpoints = {
  xs: '0px',
  sm: '600px',
  md: '900px',
  lg: '1200px',
  xl: '1536px',
};

// Z-index scale
export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
};

// CSS custom properties for dynamic theming
export const cssVariables = {
  '--glass-bg': colors.glass.bg,
  '--glass-bg-hover': colors.glass.bgHover,
  '--glass-border': colors.glass.border,
  '--glass-shadow': colors.glass.shadow,
  '--gradient-primary': colors.gradients.primary,
  '--gradient-secondary': colors.gradients.secondary,
  '--text-primary': colors.text.primary,
  '--text-secondary': colors.text.secondary,
  '--spacing-unit': '0.25rem', // 4px base unit
  '--border-radius-base': borderRadius.base,
  '--animation-duration': `${animations.duration.normal}ms`,
  '--animation-easing': 'cubic-bezier(0.4, 0, 0.2, 1)',
};

// Export theme object for Material-UI integration
export const createModernTheme = (mode = 'dark') => ({
  palette: {
    mode,
    primary: {
      main: '#667eea',
      light: '#9aa7ff',
      dark: '#3f4fb7',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#f093fb',
      light: '#ffc3ff',
      dark: '#bb63c8',
      contrastText: '#000000',
    },
    background: {
      default: colors.dark.bg,
      paper: colors.dark.surface,
    },
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
    },
    divider: colors.glass.border,
    success: {
      main: colors.semantic.success,
    },
    warning: {
      main: colors.semantic.warning,
    },
    error: {
      main: colors.semantic.danger,
    },
    info: {
      main: colors.semantic.info,
    },
  },
  typography: {
    fontFamily: typography.fontFamily.primary,
    h1: {
      fontSize: typography.fontSize['5xl'],
      fontWeight: typography.fontWeight.bold,
      lineHeight: typography.lineHeight.tight,
    },
    h2: {
      fontSize: typography.fontSize['4xl'],
      fontWeight: typography.fontWeight.bold,
      lineHeight: typography.lineHeight.tight,
    },
    h3: {
      fontSize: typography.fontSize['3xl'],
      fontWeight: typography.fontWeight.semibold,
      lineHeight: typography.lineHeight.tight,
    },
    h4: {
      fontSize: typography.fontSize['2xl'],
      fontWeight: typography.fontWeight.semibold,
      lineHeight: typography.lineHeight.normal,
    },
    h5: {
      fontSize: typography.fontSize.xl,
      fontWeight: typography.fontWeight.medium,
      lineHeight: typography.lineHeight.normal,
    },
    h6: {
      fontSize: typography.fontSize.lg,
      fontWeight: typography.fontWeight.medium,
      lineHeight: typography.lineHeight.normal,
    },
    body1: {
      fontSize: typography.fontSize.base,
      lineHeight: typography.lineHeight.normal,
    },
    body2: {
      fontSize: typography.fontSize.sm,
      lineHeight: typography.lineHeight.normal,
    },
    caption: {
      fontSize: typography.fontSize.xs,
      lineHeight: typography.lineHeight.normal,
    },
  },
  shape: {
    borderRadius: parseInt(borderRadius.lg),
  },
  spacing: 4, // 4px base unit
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        ':root': cssVariables,
        '*': {
          scrollbarWidth: 'thin',
          scrollbarColor: `${colors.glass.border} transparent`,
        },
        '*::-webkit-scrollbar': {
          width: '6px',
          height: '6px',
        },
        '*::-webkit-scrollbar-track': {
          background: 'transparent',
        },
        '*::-webkit-scrollbar-thumb': {
          background: colors.glass.border,
          borderRadius: borderRadius.full,
        },
        '*::-webkit-scrollbar-thumb:hover': {
          background: colors.glass.borderHover,
        },
      },
    },
  },
});

// Utility functions
export const utils = {
  // Add alpha to color
  alpha: (color, alpha) => {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`);
  },
  
  // Get glass styles
  getGlassStyles: (variant = 'glass') => glassMixins[variant],
  
  // Get animation variant
  getAnimation: (name) => animations.variants[name],
  
  // Get responsive value
  responsive: (values) => {
    const breakpointKeys = Object.keys(breakpoints);
    return breakpointKeys.reduce((acc, key, index) => {
      if (values[index] !== undefined) {
        acc[`@media (min-width: ${breakpoints[key]})`] = values[index];
      }
      return acc;
    }, {});
  },
};

export default {
  colors,
  typography,
  spacing,
  borderRadius,
  animations,
  glassMixins,
  breakpoints,
  zIndex,
  cssVariables,
  createModernTheme,
  utils,
};