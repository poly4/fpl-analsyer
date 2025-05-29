import React, { createContext, useContext, useState, useEffect } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { alpha } from '@mui/material/styles';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

const createAppTheme = (mode) => {
  const isDark = mode === 'dark';
  
  // First create a base theme to get default shadows
  const baseTheme = createTheme({
    palette: {
      mode,
    },
  });
  
  return createTheme({
    ...baseTheme,
    palette: {
      mode,
      primary: {
        main: isDark ? '#BB86FC' : '#6200EE',
        light: isDark ? '#DFBBFF' : '#9C4DCC',
        dark: isDark ? '#985EFF' : '#3700B3',
        contrastText: isDark ? '#000000' : '#FFFFFF',
      },
      secondary: {
        main: isDark ? '#03DAC6' : '#018786',
        light: isDark ? '#66FFF9' : '#4DB6AC',
        dark: isDark ? '#00A693' : '#00695C',
        contrastText: isDark ? '#000000' : '#FFFFFF',
      },
      success: {
        main: isDark ? '#4CAF50' : '#2E7D32',
        light: isDark ? '#81C784' : '#4CAF50',
        dark: isDark ? '#2E7D32' : '#1B5E20',
      },
      warning: {
        main: isDark ? '#FF9800' : '#F57C00',
        light: isDark ? '#FFB74D' : '#FF9800',
        dark: isDark ? '#F57C00' : '#E65100',
      },
      error: {
        main: isDark ? '#F44336' : '#D32F2F',
        light: isDark ? '#E57373' : '#F44336',
        dark: isDark ? '#D32F2F' : '#B71C1C',
      },
      background: {
        default: isDark ? '#121212' : '#FAFAFA',
        paper: isDark ? '#1E1E1E' : '#FFFFFF',
        surface: isDark ? '#2C2C2C' : '#F5F5F5',
      },
      text: {
        primary: isDark ? '#FFFFFF' : '#212121',
        secondary: isDark ? '#B0B0B0' : '#757575',
        disabled: isDark ? '#6C6C6C' : '#BDBDBD',
      },
      divider: isDark ? '#424242' : '#E0E0E0',
      // Glassmorphism colors
      glass: {
        background: isDark 
          ? alpha('#1E1E1E', 0.8)
          : alpha('#FFFFFF', 0.8),
        border: isDark 
          ? alpha('#FFFFFF', 0.1)
          : alpha('#000000', 0.1),
        shadow: isDark
          ? '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
          : '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 700,
        letterSpacing: '-0.01562em',
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
        letterSpacing: '-0.00833em',
      },
      h3: {
        fontSize: '1.75rem',
        fontWeight: 600,
        letterSpacing: '0em',
      },
      h4: {
        fontSize: '1.5rem',
        fontWeight: 600,
        letterSpacing: '0.00735em',
      },
      h5: {
        fontSize: '1.25rem',
        fontWeight: 500,
        letterSpacing: '0em',
      },
      h6: {
        fontSize: '1.125rem',
        fontWeight: 500,
        letterSpacing: '0.0075em',
      },
      body1: {
        fontSize: '1rem',
        fontWeight: 400,
        letterSpacing: '0.00938em',
        lineHeight: 1.5,
      },
      body2: {
        fontSize: '0.875rem',
        fontWeight: 400,
        letterSpacing: '0.01071em',
        lineHeight: 1.43,
      },
      caption: {
        fontSize: '0.75rem',
        fontWeight: 400,
        letterSpacing: '0.03333em',
        lineHeight: 1.66,
      },
    },
    shape: {
      borderRadius: 12,
    },
    // Use default Material-UI shadows
    // shadows: isDark ? [
      'none',
      '0px 2px 1px -1px rgba(0,0,0,0.2),0px 1px 1px 0px rgba(0,0,0,0.14),0px 1px 3px 0px rgba(0,0,0,0.12)',
      '0px 3px 1px -2px rgba(0,0,0,0.2),0px 2px 2px 0px rgba(0,0,0,0.14),0px 1px 5px 0px rgba(0,0,0,0.12)',
      '0px 3px 3px -2px rgba(0,0,0,0.2),0px 3px 4px 0px rgba(0,0,0,0.14),0px 1px 8px 0px rgba(0,0,0,0.12)',
      '0px 2px 4px -1px rgba(0,0,0,0.2),0px 4px 5px 0px rgba(0,0,0,0.14),0px 1px 10px 0px rgba(0,0,0,0.12)',
      '0px 3px 5px -1px rgba(0,0,0,0.2),0px 5px 8px 0px rgba(0,0,0,0.14),0px 1px 14px 0px rgba(0,0,0,0.12)',
      '0px 3px 5px -1px rgba(0,0,0,0.2),0px 6px 10px 0px rgba(0,0,0,0.14),0px 1px 18px 0px rgba(0,0,0,0.12)',
      '0px 4px 5px -2px rgba(0,0,0,0.2),0px 7px 10px 1px rgba(0,0,0,0.14),0px 2px 16px 1px rgba(0,0,0,0.12)',
      '0px 5px 5px -3px rgba(0,0,0,0.2),0px 8px 10px 1px rgba(0,0,0,0.14),0px 3px 14px 2px rgba(0,0,0,0.12)',
      '0px 5px 6px -3px rgba(0,0,0,0.2),0px 9px 12px 1px rgba(0,0,0,0.14),0px 3px 16px 2px rgba(0,0,0,0.12)',
      '0px 6px 6px -3px rgba(0,0,0,0.2),0px 10px 14px 1px rgba(0,0,0,0.14),0px 4px 18px 3px rgba(0,0,0,0.12)',
      '0px 6px 7px -4px rgba(0,0,0,0.2),0px 11px 15px 1px rgba(0,0,0,0.14),0px 4px 20px 3px rgba(0,0,0,0.12)',
      '0px 7px 8px -4px rgba(0,0,0,0.2),0px 12px 17px 2px rgba(0,0,0,0.14),0px 5px 22px 4px rgba(0,0,0,0.12)',
      '0px 7px 8px -4px rgba(0,0,0,0.2),0px 13px 19px 2px rgba(0,0,0,0.14),0px 5px 24px 4px rgba(0,0,0,0.12)',
      '0px 7px 9px -4px rgba(0,0,0,0.2),0px 14px 21px 2px rgba(0,0,0,0.14),0px 5px 26px 4px rgba(0,0,0,0.12)',
      '0px 8px 9px -5px rgba(0,0,0,0.2),0px 15px 22px 2px rgba(0,0,0,0.14),0px 6px 28px 5px rgba(0,0,0,0.12)',
      '0px 8px 10px -5px rgba(0,0,0,0.2),0px 16px 24px 2px rgba(0,0,0,0.14),0px 6px 30px 5px rgba(0,0,0,0.12)',
      '0px 8px 11px -5px rgba(0,0,0,0.2),0px 17px 26px 2px rgba(0,0,0,0.14),0px 6px 32px 5px rgba(0,0,0,0.12)',
      '0px 9px 11px -5px rgba(0,0,0,0.2),0px 18px 28px 2px rgba(0,0,0,0.14),0px 7px 34px 6px rgba(0,0,0,0.12)',
      '0px 9px 12px -6px rgba(0,0,0,0.2),0px 19px 29px 2px rgba(0,0,0,0.14),0px 7px 36px 6px rgba(0,0,0,0.12)',
      '0px 10px 13px -6px rgba(0,0,0,0.2),0px 20px 31px 3px rgba(0,0,0,0.14),0px 8px 38px 7px rgba(0,0,0,0.12)',
      '0px 10px 13px -6px rgba(0,0,0,0.2),0px 21px 33px 3px rgba(0,0,0,0.14),0px 8px 40px 7px rgba(0,0,0,0.12)',
      '0px 10px 14px -6px rgba(0,0,0,0.2),0px 22px 35px 3px rgba(0,0,0,0.14),0px 8px 42px 7px rgba(0,0,0,0.12)',
      '0px 11px 14px -7px rgba(0,0,0,0.2),0px 23px 36px 3px rgba(0,0,0,0.14),0px 9px 44px 8px rgba(0,0,0,0.12)',
      '0px 11px 15px -7px rgba(0,0,0,0.2),0px 24px 38px 3px rgba(0,0,0,0.14),0px 9px 46px 8px rgba(0,0,0,0.12)',
    ] : undefined,
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarColor: isDark ? '#6b6b6b #2b2b2b' : '#c1c1c1 #f1f1f1',
            '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
              width: 8,
              height: 8,
            },
            '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
              borderRadius: 8,
              backgroundColor: isDark ? '#6b6b6b' : '#c1c1c1',
              minHeight: 24,
              border: '3px solid transparent',
              backgroundClip: 'content-box',
            },
            '&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus': {
              backgroundColor: isDark ? '#959595' : '#a8a8a8',
            },
            '&::-webkit-scrollbar-thumb:active, & *::-webkit-scrollbar-thumb:active': {
              backgroundColor: isDark ? '#959595' : '#a8a8a8',
            },
            '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover': {
              backgroundColor: isDark ? '#959595' : '#a8a8a8',
            },
            '&::-webkit-scrollbar-corner, & *::-webkit-scrollbar-corner': {
              backgroundColor: isDark ? '#2b2b2b' : '#f1f1f1',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backdropFilter: 'blur(10px)',
            background: isDark 
              ? alpha('#1E1E1E', 0.8)
              : alpha('#FFFFFF', 0.8),
            border: `1px solid ${isDark 
              ? alpha('#FFFFFF', 0.1)
              : alpha('#000000', 0.1)}`,
            transition: 'all 0.3s ease-in-out',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: isDark
                ? '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
                : '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backdropFilter: 'blur(10px)',
            background: isDark 
              ? alpha('#1E1E1E', 0.9)
              : alpha('#FFFFFF', 0.9),
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: 12,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-1px)',
            },
          },
          contained: {
            boxShadow: isDark
              ? '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
              : '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            '&:hover': {
              boxShadow: isDark
                ? '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
                : '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            fontWeight: 500,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'scale(1.05)',
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 12,
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'translateY(-1px)',
              },
              '&.Mui-focused': {
                transform: 'translateY(-1px)',
                boxShadow: isDark
                  ? '0 4px 6px -1px rgba(187, 134, 252, 0.3)'
                  : '0 4px 6px -1px rgba(98, 0, 238, 0.3)',
              },
            },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backdropFilter: 'blur(20px)',
            background: isDark 
              ? alpha('#1E1E1E', 0.8)
              : alpha('#FFFFFF', 0.8),
            borderBottom: `1px solid ${isDark 
              ? alpha('#FFFFFF', 0.1)
              : alpha('#000000', 0.1)}`,
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-1px)',
            },
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            backdropFilter: 'blur(20px)',
            background: isDark 
              ? alpha('#1E1E1E', 0.95)
              : alpha('#FFFFFF', 0.95),
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backdropFilter: 'blur(10px)',
            background: isDark 
              ? alpha('#2C2C2C', 0.9)
              : alpha('#424242', 0.9),
            border: `1px solid ${isDark 
              ? alpha('#FFFFFF', 0.2)
              : alpha('#FFFFFF', 0.1)}`,
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            overflow: 'hidden',
          },
        },
      },
      MuiCircularProgress: {
        styleOverrides: {
          root: {
            animationDuration: '1.4s',
          },
        },
      },
    },
    transitions: {
      duration: {
        shortest: 150,
        shorter: 200,
        short: 250,
        standard: 300,
        complex: 375,
        enteringScreen: 225,
        leavingScreen: 195,
      },
      easing: {
        easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
        easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
        easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
        sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
      },
    },
  });
};

export const ThemeProvider = ({ children }) => {
  const [themeMode, setThemeMode] = useState(() => {
    // Check for saved theme preference or default to system preference
    const savedTheme = localStorage.getItem('theme-mode');
    if (savedTheme) {
      return savedTheme;
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  });
  
  const [reducedMotion, setReducedMotion] = useState(() => {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });
  
  const [highContrast, setHighContrast] = useState(() => {
    return localStorage.getItem('high-contrast') === 'true';
  });
  
  useEffect(() => {
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => {
      if (!localStorage.getItem('theme-mode')) {
        setThemeMode(e.matches ? 'dark' : 'light');
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);
  
  useEffect(() => {
    // Listen for reduced motion preference changes
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e) => {
      setReducedMotion(e.matches);
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);
  
  useEffect(() => {
    // Save theme preference
    localStorage.setItem('theme-mode', themeMode);
  }, [themeMode]);
  
  useEffect(() => {
    // Save high contrast preference
    localStorage.setItem('high-contrast', highContrast.toString());
  }, [highContrast]);
  
  const toggleTheme = () => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light');
  };
  
  const toggleHighContrast = () => {
    setHighContrast(prev => !prev);
  };
  
  const theme = createAppTheme(themeMode);
  
  // Apply high contrast modifications
  if (highContrast) {
    theme.palette.text.primary = themeMode === 'dark' ? '#FFFFFF' : '#000000';
    theme.palette.text.secondary = themeMode === 'dark' ? '#E0E0E0' : '#424242';
    theme.palette.background.paper = themeMode === 'dark' ? '#000000' : '#FFFFFF';
    theme.palette.background.default = themeMode === 'dark' ? '#000000' : '#FFFFFF';
  }
  
  // Disable transitions if reduced motion is preferred
  if (reducedMotion) {
    theme.transitions.duration.shortest = 0;
    theme.transitions.duration.shorter = 0;
    theme.transitions.duration.short = 0;
    theme.transitions.duration.standard = 0;
    theme.transitions.duration.complex = 0;
    theme.transitions.duration.enteringScreen = 0;
    theme.transitions.duration.leavingScreen = 0;
  }
  
  const contextValue = {
    themeMode,
    toggleTheme,
    reducedMotion,
    highContrast,
    toggleHighContrast,
    isDark: themeMode === 'dark',
  };
  
  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;