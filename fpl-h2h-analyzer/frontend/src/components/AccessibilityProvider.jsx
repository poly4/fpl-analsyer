import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Slider,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  Snackbar,
  Fab,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Accessibility,
  VolumeUp,
  ZoomIn,
  ZoomOut,
  KeyboardArrowUp,
  Keyboard,
  TouchApp,
  RecordVoiceOver,
  Close
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

const AccessibilityContext = createContext();

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

// Screen Reader Announcer
const ScreenReaderAnnouncer = () => {
  const [announcements, setAnnouncements] = useState([]);
  
  useEffect(() => {
    const handleAnnouncement = (event) => {
      setAnnouncements(prev => [...prev, {
        id: Date.now(),
        message: event.detail.message,
        priority: event.detail.priority || 'polite'
      }]);
    };
    
    window.addEventListener('announce', handleAnnouncement);
    return () => window.removeEventListener('announce', handleAnnouncement);
  }, []);
  
  useEffect(() => {
    if (announcements.length > 0) {
      const timer = setTimeout(() => {
        setAnnouncements(prev => prev.slice(1));
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [announcements]);
  
  return (
    <>
      {announcements.map(announcement => (
        <div
          key={announcement.id}
          aria-live={announcement.priority}
          aria-atomic="true"
          style={{
            position: 'absolute',
            left: '-10000px',
            width: '1px',
            height: '1px',
            overflow: 'hidden'
          }}
        >
          {announcement.message}
        </div>
      ))}
    </>
  );
};

// Skip Links Component
const SkipLinks = () => {
  const [visible, setVisible] = useState(false);
  
  const skipLinks = [
    { href: '#main-content', label: 'Skip to main content' },
    { href: '#navigation', label: 'Skip to navigation' },
    { href: '#search', label: 'Skip to search' },
    { href: '#footer', label: 'Skip to footer' }
  ];
  
  return (
    <Box
      sx={{
        position: 'fixed',
        top: -100,
        left: 0,
        zIndex: 9999,
        '&:focus-within': {
          top: 0
        }
      }}
    >
      {skipLinks.map((link, index) => (
        <Button
          key={index}
          component="a"
          href={link.href}
          variant="contained"
          color="primary"
          sx={{
            margin: 1,
            '&:focus': {
              position: 'relative',
              zIndex: 10000
            }
          }}
          onFocus={() => setVisible(true)}
          onBlur={() => setVisible(false)}
        >
          {link.label}
        </Button>
      ))}
    </Box>
  );
};

// Focus Management
const useFocusManagement = () => {
  const focusableElements = useRef(new Set());
  const currentFocusIndex = useRef(0);
  
  const registerFocusable = (element) => {
    if (element) {
      focusableElements.current.add(element);
    }
  };
  
  const unregisterFocusable = (element) => {
    focusableElements.current.delete(element);
  };
  
  const focusNext = () => {
    const elements = Array.from(focusableElements.current);
    if (elements.length === 0) return;
    
    currentFocusIndex.current = (currentFocusIndex.current + 1) % elements.length;
    elements[currentFocusIndex.current].focus();
  };
  
  const focusPrevious = () => {
    const elements = Array.from(focusableElements.current);
    if (elements.length === 0) return;
    
    currentFocusIndex.current = currentFocusIndex.current === 0 
      ? elements.length - 1 
      : currentFocusIndex.current - 1;
    elements[currentFocusIndex.current].focus();
  };
  
  const focusFirst = () => {
    const elements = Array.from(focusableElements.current);
    if (elements.length > 0) {
      currentFocusIndex.current = 0;
      elements[0].focus();
    }
  };
  
  const focusLast = () => {
    const elements = Array.from(focusableElements.current);
    if (elements.length > 0) {
      currentFocusIndex.current = elements.length - 1;
      elements[elements.length - 1].focus();
    }
  };
  
  return {
    registerFocusable,
    unregisterFocusable,
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast
  };
};

// Voice Commands
const useVoiceCommands = (enabled) => {
  const [isListening, setIsListening] = useState(false);
  const [speechRecognition, setSpeechRecognition] = useState(null);
  
  useEffect(() => {
    if (!enabled || !('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
      setIsListening(true);
      announceToScreenReader('Voice commands activated');
    };
    
    recognition.onend = () => {
      setIsListening(false);
      announceToScreenReader('Voice commands deactivated');
    };
    
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };
    
    recognition.onresult = (event) => {
      const command = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
      handleVoiceCommand(command);
    };
    
    setSpeechRecognition(recognition);
    
    return () => {
      if (recognition) {
        recognition.stop();
      }
    };
  }, [enabled]);
  
  const handleVoiceCommand = (command) => {
    const commands = {
      'go to dashboard': () => window.location.hash = '#/dashboard',
      'go to analytics': () => window.location.hash = '#/analytics',
      'go to battles': () => window.location.hash = '#/battles',
      'go to live': () => window.location.hash = '#/live',
      'scroll up': () => window.scrollTo({ top: 0, behavior: 'smooth' }),
      'scroll down': () => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }),
      'toggle theme': () => {
        const event = new CustomEvent('toggleTheme');
        window.dispatchEvent(event);
      },
      'read page': () => {
        const content = document.querySelector('#main-content')?.textContent || '';
        speakText(content.substring(0, 500));
      },
      'stop listening': () => stopListening()
    };
    
    const matchedCommand = Object.keys(commands).find(cmd => command.includes(cmd));
    if (matchedCommand) {
      commands[matchedCommand]();
      announceToScreenReader(`Executed command: ${matchedCommand}`);
    } else {
      announceToScreenReader('Command not recognized');
    }
  };
  
  const startListening = () => {
    if (speechRecognition && enabled) {
      speechRecognition.start();
    }
  };
  
  const stopListening = () => {
    if (speechRecognition) {
      speechRecognition.stop();
    }
  };
  
  return {
    isListening,
    startListening,
    stopListening,
    isSupported: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
  };
};

// Text-to-Speech
const useSpeech = (enabled) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  const speakText = (text, options = {}) => {
    if (!enabled || !('speechSynthesis' in window)) {
      return;
    }
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = options.rate || 1;
    utterance.pitch = options.pitch || 1;
    utterance.volume = options.volume || 1;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    speechSynthesis.speak(utterance);
  };
  
  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };
  
  return {
    speakText,
    stopSpeaking,
    isSpeaking,
    isSupported: 'speechSynthesis' in window
  };
};

// Accessibility Panel
const AccessibilityPanel = ({ open, onClose }) => {
  const theme = useTheme();
  const { 
    settings, 
    updateSetting, 
    voiceCommands, 
    speech,
    announceToScreenReader 
  } = useAccessibility();
  
  const handleSettingChange = (setting, value) => {
    updateSetting(setting, value);
    announceToScreenReader(`${setting} ${value ? 'enabled' : 'disabled'}`);
  };
  
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="accessibility-dialog-title"
    >
      <DialogTitle id="accessibility-dialog-title">
        <Box display="flex" alignItems="center" gap={2}>
          <Accessibility />
          Accessibility Settings
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <List>
          <ListItem>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.screenReader}
                  onChange={(e) => handleSettingChange('screenReader', e.target.checked)}
                />
              }
              label="Enhanced Screen Reader Support"
              labelPlacement="start"
              sx={{ justifyContent: 'space-between', width: '100%' }}
            />
          </ListItem>
          
          <ListItem>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.keyboardNavigation}
                  onChange={(e) => handleSettingChange('keyboardNavigation', e.target.checked)}
                />
              }
              label="Enhanced Keyboard Navigation"
              labelPlacement="start"
              sx={{ justifyContent: 'space-between', width: '100%' }}
            />
          </ListItem>
          
          <ListItem>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.voiceCommands}
                  onChange={(e) => handleSettingChange('voiceCommands', e.target.checked)}
                />
              }
              label="Voice Commands"
              labelPlacement="start"
              sx={{ justifyContent: 'space-between', width: '100%' }}
            />
          </ListItem>
          
          <ListItem>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.textToSpeech}
                  onChange={(e) => handleSettingChange('textToSpeech', e.target.checked)}
                />
              }
              label="Text-to-Speech"
              labelPlacement="start"
              sx={{ justifyContent: 'space-between', width: '100%' }}
            />
          </ListItem>
          
          <Divider sx={{ my: 2 }} />
          
          <ListItem>
            <Box sx={{ width: '100%' }}>
              <Typography gutterBottom>Font Size</Typography>
              <Slider
                value={settings.fontSize}
                onChange={(e, value) => handleSettingChange('fontSize', value)}
                min={12}
                max={24}
                step={1}
                marks
                valueLabelDisplay="auto"
                aria-label="Font size"
              />
            </Box>
          </ListItem>
          
          <ListItem>
            <Box sx={{ width: '100%' }}>
              <Typography gutterBottom>Animation Speed</Typography>
              <Slider
                value={settings.animationSpeed}
                onChange={(e, value) => handleSettingChange('animationSpeed', value)}
                min={0}
                max={2}
                step={0.1}
                marks={[
                  { value: 0, label: 'Off' },
                  { value: 0.5, label: 'Slow' },
                  { value: 1, label: 'Normal' },
                  { value: 2, label: 'Fast' }
                ]}
                valueLabelDisplay="auto"
                aria-label="Animation speed"
              />
            </Box>
          </ListItem>
        </List>
        
        {settings.voiceCommands && voiceCommands.isSupported && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Voice commands available: "go to dashboard", "go to analytics", "scroll up", 
              "scroll down", "toggle theme", "read page", "stop listening"
            </Typography>
          </Alert>
        )}
        
        {voiceCommands.isListening && (
          <Alert severity="success" sx={{ mt: 1 }}>
            <Box display="flex" alignItems="center" gap={1}>
              <RecordVoiceOver />
              Listening for voice commands...
            </Box>
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        {settings.voiceCommands && voiceCommands.isSupported && (
          <Button
            variant="contained"
            onClick={voiceCommands.isListening ? voiceCommands.stopListening : voiceCommands.startListening}
            startIcon={<RecordVoiceOver />}
            color={voiceCommands.isListening ? "error" : "primary"}
          >
            {voiceCommands.isListening ? 'Stop Listening' : 'Start Voice Commands'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

// Floating Accessibility Button
const AccessibilityFab = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [panelOpen, setPanelOpen] = useState(false);
  const [showButton, setShowButton] = useState(true);
  
  useEffect(() => {
    let lastScrollY = window.scrollY;
    
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      setShowButton(currentScrollY < lastScrollY || currentScrollY < 100);
      lastScrollY = currentScrollY;
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  return (
    <>
      <AnimatePresence>
        {showButton && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            style={{
              position: 'fixed',
              bottom: isMobile ? 160 : 20,
              right: 20,
              zIndex: 1000
            }}
          >
            <Fab
              color="secondary"
              aria-label="Accessibility settings"
              onClick={() => setPanelOpen(true)}
              sx={{
                backdropFilter: 'blur(10px)',
                '&:hover': {
                  transform: 'scale(1.1)'
                }
              }}
            >
              <Accessibility />
            </Fab>
          </motion.div>
        )}
      </AnimatePresence>
      
      <AccessibilityPanel
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
      />
    </>
  );
};

// Utility function to announce to screen readers
const announceToScreenReader = (message, priority = 'polite') => {
  const event = new CustomEvent('announce', {
    detail: { message, priority }
  });
  window.dispatchEvent(event);
};

// Global speech function
window.speakText = (text) => {
  const event = new CustomEvent('speakText', {
    detail: { text }
  });
  window.dispatchEvent(event);
};

export const AccessibilityProvider = ({ children }) => {
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('accessibility-settings');
    return saved ? JSON.parse(saved) : {
      screenReader: false,
      keyboardNavigation: true,
      voiceCommands: false,
      textToSpeech: false,
      fontSize: 16,
      animationSpeed: 1
    };
  });
  
  const focusManagement = useFocusManagement();
  const voiceCommands = useVoiceCommands(settings.voiceCommands);
  const speech = useSpeech(settings.textToSpeech);
  
  useEffect(() => {
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));
  }, [settings]);
  
  useEffect(() => {
    // Apply font size
    document.documentElement.style.fontSize = `${settings.fontSize}px`;
  }, [settings.fontSize]);
  
  useEffect(() => {
    // Apply animation speed
    const speed = settings.animationSpeed === 0 ? 0 : 1 / settings.animationSpeed;
    document.documentElement.style.setProperty('--animation-duration-multiplier', speed);
  }, [settings.animationSpeed]);
  
  useEffect(() => {
    // Keyboard navigation
    if (!settings.keyboardNavigation) return;
    
    const handleKeyDown = (event) => {
      if (event.altKey) {
        switch (event.key) {
          case 'ArrowRight':
            event.preventDefault();
            focusManagement.focusNext();
            break;
          case 'ArrowLeft':
            event.preventDefault();
            focusManagement.focusPrevious();
            break;
          case 'Home':
            event.preventDefault();
            focusManagement.focusFirst();
            break;
          case 'End':
            event.preventDefault();
            focusManagement.focusLast();
            break;
        }
      }
      
      // Quick access keys
      if (event.ctrlKey && event.shiftKey) {
        switch (event.key) {
          case 'A':
            event.preventDefault();
            // Open accessibility panel
            const event2 = new CustomEvent('openAccessibilityPanel');
            window.dispatchEvent(event2);
            break;
          case 'V':
            event.preventDefault();
            if (settings.voiceCommands) {
              voiceCommands.isListening ? voiceCommands.stopListening() : voiceCommands.startListening();
            }
            break;
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [settings.keyboardNavigation, settings.voiceCommands, focusManagement, voiceCommands]);
  
  useEffect(() => {
    // Text-to-speech event listener
    const handleSpeakText = (event) => {
      if (settings.textToSpeech) {
        speech.speakText(event.detail.text);
      }
    };
    
    window.addEventListener('speakText', handleSpeakText);
    return () => window.removeEventListener('speakText', handleSpeakText);
  }, [settings.textToSpeech, speech]);
  
  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };
  
  const contextValue = {
    settings,
    updateSetting,
    focusManagement,
    voiceCommands,
    speech,
    announceToScreenReader
  };
  
  return (
    <AccessibilityContext.Provider value={contextValue}>
      <SkipLinks />
      <ScreenReaderAnnouncer />
      {children}
      <AccessibilityFab />
    </AccessibilityContext.Provider>
  );
};

export default AccessibilityProvider;
export { announceToScreenReader };