import React, { useEffect, useState, useRef, memo } from 'react';
import { Box, Typography, LinearProgress, Chip, Card, CardContent, IconButton, Collapse } from '@mui/material';
import { ExpandMore, ExpandLess, Speed, Memory, Network, Timer } from '@mui/icons-material';
import { 
  RenderTimeTracker, 
  APIPerformanceMonitor, 
  FPSMonitor,
  monitorMemoryUsage,
  perfMark,
  perfMeasure 
} from '../utils/performance';

// Global performance trackers
const renderTracker = new RenderTimeTracker();
const apiMonitor = new APIPerformanceMonitor();
const fpsMonitor = new FPSMonitor();

const PerformanceMonitor = memo(({ show = false }) => {
  const [metrics, setMetrics] = useState({
    fps: 0,
    memory: { used: 0, limit: 0, percent: 0 },
    loadTime: 0,
    renderTime: 0,
    apiCalls: [],
    bundleSize: 0,
    vitals: {},
    slowComponents: {}
  });
  const [expanded, setExpanded] = useState(false);
  const intervalRef = useRef();
  
  useEffect(() => {
    if (!show) return;

    // Initialize FPS monitoring
    fpsMonitor.start();

    // Initialize memory monitoring
    monitorMemoryUsage((memInfo) => {
      setMetrics(prev => ({
        ...prev,
        memory: {
          used: Math.round(memInfo.usedJSHeapSize / 1048576),
          limit: Math.round(memInfo.jsHeapSizeLimit / 1048576),
          percent: memInfo.percentUsed
        }
      }));
    });

    // Update metrics periodically
    intervalRef.current = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        fps: fpsMonitor.getFPS(),
        slowComponents: renderTracker.getReport(),
        vitals: getWebVitals()
      }));
    }, 1000);

    // Track bundle size on load
    trackBundleSize();

    // Measure initial load time
    if (window.performance && window.performance.timing) {
      const loadTime = window.performance.timing.loadEventEnd - 
                      window.performance.timing.navigationStart;
      setMetrics(prev => ({ ...prev, loadTime }));
    }

    // Expose performance utils globally for debugging
    window.__performanceMonitor = {
      renderTracker,
      apiMonitor,
      fpsMonitor,
      getMetrics: () => metrics,
      mark: perfMark,
      measure: perfMeasure
    };

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [show]);

  const getWebVitals = () => {
    if (!window.performance) return {};
    
    const navigation = performance.getEntriesByType('navigation')[0];
    if (navigation) {
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      };
    }
    return {};
  };

  const trackBundleSize = () => {
    if (window.performance && window.performance.getEntriesByType) {
      const resources = window.performance.getEntriesByType('resource');
      const jsResources = resources.filter(r => r.name.endsWith('.js'));
      const totalSize = jsResources.reduce((acc, r) => acc + (r.transferSize || 0), 0);
      setMetrics(prev => ({ ...prev, bundleSize: totalSize }));
    }
  };
  
  if (!show) return null;
  
  const getFPSColor = (fps) => {
    if (fps >= 50) return 'success';
    if (fps >= 30) return 'warning';
    return 'error';
  };

  const getMemoryColor = (percent) => {
    if (percent >= 80) return 'error';
    if (percent >= 60) return 'warning';
    return 'success';
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (ms) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getPerformanceStatus = () => {
    const { fps, memory, vitals } = metrics;
    
    if (fps < 30 || memory.percent > 90 || vitals.firstContentfulPaint > 3000) {
      return { level: 'error', label: 'Poor' };
    }
    if (fps < 50 || memory.percent > 70 || vitals.firstContentfulPaint > 2000) {
      return { level: 'warning', label: 'Fair' };
    }
    return { level: 'success', label: 'Good' };
  };

  const performanceStatus = getPerformanceStatus();
  
  return (
    <Card 
      sx={{ 
        position: 'fixed', 
        bottom: 16, 
        right: 16, 
        width: expanded ? 350 : 250,
        zIndex: 9999,
        opacity: 0.95,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        transition: 'all 0.3s ease'
      }}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Speed color={performanceStatus.level} />
            <Typography variant="subtitle2">
              Performance: {performanceStatus.label}
            </Typography>
          </Box>
          <IconButton 
            size="small" 
            onClick={() => setExpanded(!expanded)}
            sx={{ ml: 1 }}
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
        
        {/* Essential Metrics */}
        <Box sx={{ mb: expanded ? 2 : 0 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Timer sx={{ fontSize: 16 }} /> FPS
            </Typography>
            <Chip 
              label={`${metrics.fps}`} 
              size="small" 
              color={getFPSColor(metrics.fps)}
              variant="outlined"
            />
          </Box>
          
          {metrics.memory.limit > 0 && (
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Memory sx={{ fontSize: 16 }} /> Memory
                </Typography>
                <Typography variant="body2" color={getMemoryColor(metrics.memory.percent)}>
                  {metrics.memory.used}MB
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={metrics.memory.percent}
                color={getMemoryColor(metrics.memory.percent)}
                sx={{ height: 4, borderRadius: 2 }}
              />
            </Box>
          )}
        </Box>

        {/* Expanded Metrics */}
        <Collapse in={expanded}>
          <Box>
            {/* Bundle Size */}
            {metrics.bundleSize > 0 && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Bundle Size</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {formatBytes(metrics.bundleSize)}
                </Typography>
              </Box>
            )}

            {/* Load Time */}
            {metrics.loadTime > 0 && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Load Time</Typography>
                <Typography variant="body2" color={metrics.loadTime > 3000 ? 'error' : 'text.secondary'}>
                  {formatTime(metrics.loadTime)}
                </Typography>
              </Box>
            )}

            {/* Web Vitals */}
            {Object.keys(metrics.vitals).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>Web Vitals</Typography>
                {metrics.vitals.firstContentfulPaint && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption">FCP</Typography>
                    <Typography variant="caption">
                      {formatTime(metrics.vitals.firstContentfulPaint)}
                    </Typography>
                  </Box>
                )}
                {metrics.vitals.domContentLoaded && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption">DCL</Typography>
                    <Typography variant="caption">
                      {formatTime(metrics.vitals.domContentLoaded)}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}

            {/* Slow Components */}
            {Object.keys(metrics.slowComponents).length > 0 && (
              <Box>
                <Typography variant="body2" fontWeight="bold" gutterBottom>Slow Components</Typography>
                {Object.entries(metrics.slowComponents)
                  .filter(([_, data]) => data.average > 16)
                  .slice(0, 3)
                  .map(([component, data]) => (
                    <Box key={component} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="caption" noWrap sx={{ maxWidth: 200 }}>
                        {component}
                      </Typography>
                      <Typography variant="caption" color="warning.main">
                        {data.average.toFixed(1)}ms
                      </Typography>
                    </Box>
                  ))}
              </Box>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
});

PerformanceMonitor.displayName = 'PerformanceMonitor';

// Performance decorator for components
export const withPerformanceTracking = (WrappedComponent) => {
  const WithPerformanceTracking = (props) => {
    const componentName = WrappedComponent.displayName || WrappedComponent.name || 'Unknown';
    
    useEffect(() => {
      perfMark(`${componentName}-start`);
      renderTracker.startTracking(componentName);
      
      return () => {
        renderTracker.endTracking(componentName);
        perfMark(`${componentName}-end`);
        perfMeasure(`${componentName}-render`, `${componentName}-start`, `${componentName}-end`);
      };
    });

    return <WrappedComponent {...props} />;
  };

  WithPerformanceTracking.displayName = `withPerformanceTracking(${WrappedComponent.displayName || WrappedComponent.name})`;
  return WithPerformanceTracking;
};

export default PerformanceMonitor;