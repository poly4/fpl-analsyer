import React, { lazy, Suspense } from 'react';
import { Skeleton } from '@mui/material';

// Lazy load Recharts components
export const LazyLineChart = lazy(() => 
  import('recharts').then(module => ({ default: module.LineChart }))
);

export const LazyBarChart = lazy(() => 
  import('recharts').then(module => ({ default: module.BarChart }))
);

export const LazyAreaChart = lazy(() => 
  import('recharts').then(module => ({ default: module.AreaChart }))
);

export const LazyPieChart = lazy(() => 
  import('recharts').then(module => ({ default: module.PieChart }))
);

export const LazyRadarChart = lazy(() => 
  import('recharts').then(module => ({ default: module.RadarChart }))
);

export const LazyComposedChart = lazy(() => 
  import('recharts').then(module => ({ default: module.ComposedChart }))
);

// Chart loading skeleton
export const ChartSkeleton = ({ width = '100%', height = 300 }) => (
  <Skeleton 
    variant="rectangular" 
    width={width} 
    height={height} 
    animation="wave"
    sx={{ borderRadius: 1 }}
  />
);

// Wrapper component for lazy charts
export const LazyChartWrapper = ({ children, width, height }) => (
  <Suspense fallback={<ChartSkeleton width={width} height={height} />}>
    {children}
  </Suspense>
);

// Export all Recharts components lazily
export * as RechartsLazy from 'recharts';