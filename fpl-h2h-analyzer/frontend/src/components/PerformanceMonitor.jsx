import React, { useEffect, useState } from 'react';
import { Box, Typography, LinearProgress, Chip, Card, CardContent } from '@mui/material';

const PerformanceMonitor = ({ show = false }) => {
  const [metrics, setMetrics] = useState({
    fps: 0,
    memory: { used: 0, limit: 0 },
    loadTime: 0,
    renderTime: 0
  });
  
  useEffect(() => {
    if (!show) return;
    
    let frameCount = 0;
    let lastTime = performance.now();
    let rafId;
    
    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime >= lastTime + 1000) {
        setMetrics(prev => ({
          ...prev,
          fps: Math.round((frameCount * 1000) / (currentTime - lastTime))
        }));
        frameCount = 0;
        lastTime = currentTime;
      }
      
      // Measure memory if available
      if (performance.memory) {
        setMetrics(prev => ({
          ...prev,
          memory: {
            used: Math.round(performance.memory.usedJSHeapSize / 1048576),
            limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
          }
        }));
      }
      
      rafId = requestAnimationFrame(measureFPS);
    };
    
    // Measure initial load time
    if (window.performance && window.performance.timing) {
      const loadTime = window.performance.timing.loadEventEnd - 
                      window.performance.timing.navigationStart;
      setMetrics(prev => ({ ...prev, loadTime }));
    }
    
    measureFPS();
    
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [show]);
  
  if (!show) return null;
  
  const getFPSColor = (fps) => {
    if (fps >= 50) return 'success';
    if (fps >= 30) return 'warning';
    return 'error';
  };
  
  const getMemoryUsage = () => {
    if (metrics.memory.limit === 0) return 0;
    return (metrics.memory.used / metrics.memory.limit) * 100;
  };
  
  return (
    <Card 
      sx={{ 
        position: 'fixed', 
        bottom: 16, 
        right: 16, 
        width: 250,
        zIndex: 9999,
        opacity: 0.9
      }}
    >
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>
          Performance Monitor
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">FPS</Typography>
            <Chip 
              label={`${metrics.fps} fps`} 
              size="small" 
              color={getFPSColor(metrics.fps)}
            />
          </Box>
          
          {metrics.memory.limit > 0 && (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Memory</Typography>
                <Typography variant="body2">
                  {metrics.memory.used}MB / {metrics.memory.limit}MB
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getMemoryUsage()} 
                sx={{ mb: 1 }}
              />
            </>
          )}
          
          {metrics.loadTime > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2">Load Time</Typography>
              <Typography variant="body2">{metrics.loadTime}ms</Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default PerformanceMonitor;