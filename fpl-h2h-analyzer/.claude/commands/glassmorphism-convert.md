# Glassmorphism Convert Command

**Purpose:** Apply glassmorphism effects to any component, transforming basic cards/containers into modern glass-like interfaces.

## Usage
```bash
> /glassmorphism-convert ComponentName
```

## Template Prompt

```
think hard and apply comprehensive glassmorphism effects to {ComponentName}:

## 1. Glass Container Transformation
```css
// Replace basic Paper/Card with glassmorphic styling
sx={{
  background: 'rgba(255, 255, 255, 0.05)',
  backdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  borderRadius: '16px',
  boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
  transition: 'all 0.3s ease-out',
  '&:hover': {
    background: 'rgba(255, 255, 255, 0.08)',
    transform: 'translateY(-2px)',
    boxShadow: '0 12px 40px rgba(31, 38, 135, 0.2)',
  }
}}
```

## 2. Glassmorphic Navigation Tabs
```css
// Transform MUI Tabs to glass pills
sx={{
  '& .MuiTab-root': {
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '25px',
    margin: '0 4px',
    minHeight: '40px',
    transition: 'all 0.3s ease-out',
    '&.Mui-selected': {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: '#fff',
      boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
    },
    '&:hover': {
      background: 'rgba(255, 255, 255, 0.08)',
      transform: 'scale(1.02)',
    }
  }
}}
```

## 3. Glass Status Indicators
```jsx
// WebSocket status with glass effect
const GlassStatusIndicator = ({ status, pulse = false }) => (
  <Box
    sx={{
      background: 'rgba(255, 255, 255, 0.1)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255, 255, 255, 0.2)',
      borderRadius: '12px',
      padding: '8px 16px',
      display: 'flex',
      alignItems: 'center',
      gap: 1,
      animation: pulse ? 'pulse 2s infinite' : 'none',
      '@keyframes pulse': {
        '0%': { opacity: 1 },
        '50%': { opacity: 0.7 },
        '100%': { opacity: 1 }
      }
    }}
  >
    <Circle sx={{ 
      fontSize: 8, 
      color: status === 'connected' ? '#00ff88' : '#ff4757' 
    }} />
    <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.9)' }}>
      {status}
    </Typography>
  </Box>
);
```

## 4. Glassmorphic Data Tables
```css
// Transform TableContainer
sx={{
  background: 'rgba(255, 255, 255, 0.03)',
  backdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  borderRadius: '16px',
  overflow: 'hidden',
  '& .MuiTableRow-root': {
    '&:hover': {
      background: 'rgba(255, 255, 255, 0.05)',
      transform: 'translateX(4px)',
      transition: 'all 0.3s ease-out',
    }
  },
  '& .MuiTableCell-root': {
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    background: 'transparent',
  }
}}
```

## 5. Glass Modal/Dialog Overlay
```css
// Modal backdrop with glass effect
sx={{
  '& .MuiBackdrop-root': {
    backdropFilter: 'blur(8px)',
    background: 'rgba(0, 0, 0, 0.5)',
  },
  '& .MuiDialog-paper': {
    background: 'rgba(26, 26, 46, 0.9)',
    backdropFilter: 'blur(30px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '20px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
  }
}}
```

## 6. Glassmorphic Buttons
```css
// Glass button effects
sx={{
  background: 'rgba(255, 255, 255, 0.1)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255, 255, 255, 0.2)',
  borderRadius: '12px',
  color: 'rgba(255, 255, 255, 0.9)',
  transition: 'all 0.3s ease-out',
  '&:hover': {
    background: 'rgba(255, 255, 255, 0.15)',
    transform: 'translateY(-2px)',
    boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
  },
  '&:active': {
    transform: 'translateY(0)',
  }
}}
```

## 7. Implementation Checklist

### Visual Requirements:
- [ ] Apply backdrop-filter: blur(20px) to main containers
- [ ] Use rgba() backgrounds with 0.05-0.1 alpha
- [ ] Add subtle borders with rgba(255,255,255,0.1)
- [ ] Implement smooth transitions (300ms ease-out)
- [ ] Add hover effects with transform and glow
- [ ] Ensure proper contrast for accessibility

### Animation Requirements:
- [ ] Smooth hover transitions with scale/translate
- [ ] Staggered animations for multiple elements
- [ ] Pulse effects for status indicators
- [ ] Gentle shadow animations on interaction
- [ ] Smooth opacity changes for state transitions

### Responsive Requirements:
- [ ] Glass effects work on mobile devices
- [ ] Proper fallbacks for browsers without backdrop-filter
- [ ] Touch-friendly hover states for mobile
- [ ] Optimized blur radius for different screen sizes

### Performance Requirements:
- [ ] Use will-change: transform for animated elements
- [ ] Optimize backdrop-filter usage (not too many layers)
- [ ] Ensure 60fps animations
- [ ] Add proper GPU acceleration hints

## Browser Compatibility
```css
/* Fallback for browsers without backdrop-filter support */
@supports not (backdrop-filter: blur(20px)) {
  .glass-container {
    background: rgba(26, 26, 46, 0.95) !important;
  }
}
```

Remember to test glassmorphism effects in different lighting conditions and ensure accessibility standards are maintained.
```

## Example Usage

### Input:
```bash
> /glassmorphism-convert WebSocketStatus
```

### Expected Action:
Claude will transform the WebSocketStatus component with:
- Glass container with backdrop blur
- Smooth pulse animation for connection status
- Hover effects with glow and transform
- Proper fallbacks for older browsers