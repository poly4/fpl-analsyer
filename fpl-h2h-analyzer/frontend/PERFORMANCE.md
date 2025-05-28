# Frontend Performance Optimizations

This document outlines all the performance optimizations implemented in the FPL H2H Analyzer frontend.

## 1. Build Optimizations

### Vite Configuration
- **Compression**: Gzip and Brotli compression for all text-based assets
- **Tree Shaking**: Removes unused code from the bundle
- **Code Splitting**: Separates vendor, UI library, charting, and 3D libraries
- **Minification**: Terser with console.log removal in production
- **Asset Optimization**: Inline small assets (<4KB), organize larger assets

### Bundle Analysis
- Run `npm run build` to generate a bundle analysis report at `dist/stats.html`

## 2. Code Splitting & Lazy Loading

### Route-based Code Splitting
```jsx
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));
```

### Component-level Lazy Loading
- Heavy components (charts, 3D scenes) are lazy loaded
- Use `LazyChartWrapper` for Recharts components
- Use `Lazy3DScene` for Three.js components

## 3. Progressive Web App (PWA)

### Service Worker Features
- **Offline Support**: App works offline with cached resources
- **Network-First API Caching**: API responses cached for 24 hours
- **Cache-First Images**: Images cached for 30 days
- **Auto Updates**: Service worker updates automatically

### Installation
Users can install the app as a PWA on their devices for native-like experience.

## 4. Web Workers

### Heavy Calculations
- Complex FPL calculations run in a separate thread
- Prevents UI blocking during data processing
- Available calculations:
  - Expected points calculation
  - Team statistics analysis
  - Differential opportunities
  - Match outcome simulation

### Usage
```jsx
import { useWorker } from './hooks/useWorker';

const { calculateTeamStats } = useWorker();
const stats = await calculateTeamStats(teamData, players);
```

## 5. Loading States & Skeletons

### Available Skeletons
- `BattleCardSkeleton`: For match cards
- `ManagerCardSkeleton`: For manager information
- `LeagueTableSkeleton`: For league standings
- `ChartSkeleton`: For chart placeholders
- `AnalyticsDashboardSkeleton`: For dashboard loading

### Usage
```jsx
import { BattleCardSkeleton } from './components/Skeletons';

{loading ? <BattleCardSkeleton /> : <BattleCard data={data} />}
```

## 6. Image Optimization

### Lazy Loading Images
```jsx
import LazyImage from './components/LazyImage';

<LazyImage 
  src="/path/to/image.jpg" 
  alt="Description"
  width={300}
  height={200}
/>
```

Features:
- Intersection Observer for viewport detection
- Placeholder while loading
- Smooth fade-in transition
- Error handling with fallback

## 7. API Optimization

### Optimized Hooks
```jsx
import { useOptimizedAPI } from './hooks/useOptimizedAPI';

const { data, loading, error, refetch } = useOptimizedAPI('/api/data', {
  cacheKey: 'unique-key',
  cacheTTL: 300000, // 5 minutes
  debounceMs: 500,
  retryCount: 3
});
```

Features:
- Client-side caching with Cache API
- Automatic retries with exponential backoff
- Request debouncing
- Request cancellation on unmount

## 8. Performance Utilities

### Debouncing
```jsx
import { debounce } from './utils/performance';

const handleSearch = debounce((query) => {
  // Search logic
}, 300);
```

### Throttling
```jsx
import { throttle } from './utils/performance';

const handleScroll = throttle(() => {
  // Scroll logic
}, 100);
```

### Memoization
```jsx
import { memoize } from './utils/performance';

const expensiveCalculation = memoize((data) => {
  // Complex calculation
});
```

## 9. Performance Monitoring

### Enable Performance Monitor
```jsx
import PerformanceMonitor from './components/PerformanceMonitor';

<PerformanceMonitor show={true} />
```

Displays:
- FPS (Frames Per Second)
- Memory usage
- Initial load time

## 10. Best Practices

### Do's
- Use lazy loading for heavy components
- Implement loading skeletons for all async content
- Cache API responses appropriately
- Use Web Workers for complex calculations
- Debounce user input handlers
- Optimize images with lazy loading

### Don'ts
- Don't import large libraries in the main bundle
- Avoid inline functions in render methods
- Don't fetch data without caching
- Avoid blocking the main thread with calculations

## Measuring Performance

### Lighthouse
Run Lighthouse audit in Chrome DevTools for comprehensive performance metrics.

### Web Vitals
Key metrics to monitor:
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

### Custom Metrics
Use the performance utilities to measure specific operations:
```jsx
import { perfMark, perfMeasure } from './utils/performance';

perfMark('operation-start');
// ... operation code ...
perfMark('operation-end');
perfMeasure('operation-duration', 'operation-start', 'operation-end');
```