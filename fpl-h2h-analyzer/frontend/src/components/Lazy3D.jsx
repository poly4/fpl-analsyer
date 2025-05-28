import React, { lazy, Suspense } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

// Lazy load Three.js components
export const LazyCanvas = lazy(() => 
  import('@react-three/fiber').then(module => ({ default: module.Canvas }))
);

export const LazyOrbitControls = lazy(() => 
  import('@react-three/drei').then(module => ({ default: module.OrbitControls }))
);

export const LazyStats = lazy(() => 
  import('@react-three/drei').then(module => ({ default: module.Stats }))
);

export const LazyEnvironment = lazy(() => 
  import('@react-three/drei').then(module => ({ default: module.Environment }))
);

export const LazyPerspectiveCamera = lazy(() => 
  import('@react-three/drei').then(module => ({ default: module.PerspectiveCamera }))
);

// 3D Scene loading component
export const Scene3DLoader = ({ message = 'Loading 3D Scene...' }) => (
  <Box
    sx={{
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      textAlign: 'center',
      zIndex: 1000
    }}
  >
    <CircularProgress size={60} thickness={4} />
    <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
      {message}
    </Typography>
  </Box>
);

// 3D Scene wrapper with loading state
export const Lazy3DScene = ({ children, width = '100%', height = '400px', loadingMessage }) => (
  <Box sx={{ position: 'relative', width, height, bgcolor: 'background.paper' }}>
    <Suspense fallback={<Scene3DLoader message={loadingMessage} />}>
      {children}
    </Suspense>
  </Box>
);

// Utility to lazy load Three.js objects
export const lazyThree = (importFn) => lazy(() => 
  importFn().then(module => ({ 
    default: module.default || module 
  }))
);