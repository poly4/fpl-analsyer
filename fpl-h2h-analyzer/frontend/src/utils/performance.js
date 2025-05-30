// Performance optimization utilities
import { getCLS, getFID, getLCP, getTTFB, getFCP } from 'web-vitals';

// Web Vitals tracking
export const trackWebVitals = (onPerfEntry) => {
  if (onPerfEntry && typeof onPerfEntry === 'function') {
    getCLS(onPerfEntry);
    getFID(onPerfEntry);
    getLCP(onPerfEntry);
    getTTFB(onPerfEntry);
    getFCP(onPerfEntry);
  }
};

// Performance metrics logger
export const logPerformanceMetrics = () => {
  trackWebVitals((metric) => {
    console.log(`[Performance] ${metric.name}:`, metric.value);
    
    // Send to analytics service if available
    if (window.gtag) {
      window.gtag('event', metric.name, {
        value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
        metric_id: metric.id,
        metric_value: metric.value,
        metric_delta: metric.delta,
      });
    }
  });
};

// Component render time tracker
export class RenderTimeTracker {
  constructor() {
    this.startTimes = new Map();
    this.renderTimes = new Map();
  }

  startTracking(componentName) {
    this.startTimes.set(componentName, performance.now());
  }

  endTracking(componentName) {
    const startTime = this.startTimes.get(componentName);
    if (startTime) {
      const renderTime = performance.now() - startTime;
      const times = this.renderTimes.get(componentName) || [];
      times.push(renderTime);
      this.renderTimes.set(componentName, times);
      
      if (renderTime > 16) { // More than one frame
        console.warn(`[Performance] ${componentName} render took ${renderTime.toFixed(2)}ms`);
      }
      
      return renderTime;
    }
  }

  getAverageRenderTime(componentName) {
    const times = this.renderTimes.get(componentName) || [];
    if (times.length === 0) return 0;
    return times.reduce((a, b) => a + b, 0) / times.length;
  }

  getReport() {
    const report = {};
    this.renderTimes.forEach((times, component) => {
      report[component] = {
        count: times.length,
        average: this.getAverageRenderTime(component),
        max: Math.max(...times),
        min: Math.min(...times),
      };
    });
    return report;
  }
}

// API performance monitor
export class APIPerformanceMonitor {
  constructor() {
    this.requests = new Map();
  }

  startRequest(url) {
    const id = `${url}-${Date.now()}`;
    this.requests.set(id, {
      url,
      startTime: performance.now(),
    });
    return id;
  }

  endRequest(id, status) {
    const request = this.requests.get(id);
    if (request) {
      const duration = performance.now() - request.startTime;
      this.requests.delete(id);
      
      // Log slow requests
      if (duration > 1000) {
        console.warn(`[API Performance] Slow request to ${request.url}: ${duration.toFixed(2)}ms`);
      }
      
      return {
        url: request.url,
        duration,
        status,
      };
    }
  }
}

// FPS monitor for animations
export class FPSMonitor {
  constructor() {
    this.lastTime = performance.now();
    this.frames = 0;
    this.fps = 0;
  }

  start() {
    const measure = () => {
      const now = performance.now();
      this.frames++;
      
      if (now >= this.lastTime + 1000) {
        this.fps = Math.round((this.frames * 1000) / (now - this.lastTime));
        this.lastTime = now;
        this.frames = 0;
        
        if (this.fps < 50) {
          console.warn(`[Performance] Low FPS: ${this.fps}`);
        }
      }
      
      requestAnimationFrame(measure);
    };
    
    requestAnimationFrame(measure);
  }

  getFPS() {
    return this.fps;
  }
}

// Memory usage monitor
export const monitorMemoryUsage = (callback) => {
  if (performance.memory) {
    const checkMemory = () => {
      const memInfo = {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
        percentUsed: (performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100
      };
      
      if (memInfo.percentUsed > 80) {
        console.warn('[Memory] High memory usage:', memInfo);
      }
      
      if (callback) callback(memInfo);
    };
    
    setInterval(checkMemory, 30000); // Check every 30 seconds
    checkMemory(); // Initial check
  }
};

// Bundle size tracking
export const trackBundleSize = () => {
  if (window.performance && window.performance.getEntriesByType) {
    const resources = window.performance.getEntriesByType('resource');
    const jsResources = resources.filter(r => r.name.endsWith('.js'));
    const cssResources = resources.filter(r => r.name.endsWith('.css'));
    
    const totalJSSize = jsResources.reduce((acc, r) => acc + r.transferSize, 0);
    const totalCSSSize = cssResources.reduce((acc, r) => acc + r.transferSize, 0);
    
    console.log('[Bundle Size]', {
      js: `${(totalJSSize / 1024).toFixed(2)} KB`,
      css: `${(totalCSSSize / 1024).toFixed(2)} KB`,
      total: `${((totalJSSize + totalCSSSize) / 1024).toFixed(2)} KB`
    });
  }
};

// Debounce function for expensive operations
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Throttle function for frequent events
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// Memoization for expensive calculations
export const memoize = (fn) => {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };
};

// Request idle callback polyfill
export const requestIdleCallback = 
  window.requestIdleCallback ||
  function (cb) {
    const start = Date.now();
    return setTimeout(() => {
      cb({
        didTimeout: false,
        timeRemaining: () => Math.max(0, 50 - (Date.now() - start))
      });
    }, 1);
  };

// Cancel idle callback polyfill
export const cancelIdleCallback = 
  window.cancelIdleCallback ||
  function (id) {
    clearTimeout(id);
  };

// Batch DOM updates
export const batchUpdate = (updates) => {
  requestIdleCallback(() => {
    requestAnimationFrame(() => {
      updates();
    });
  });
};

// Lazy load images in a container
export const lazyLoadImages = (container) => {
  const images = container.querySelectorAll('img[data-src]');
  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        imageObserver.unobserve(img);
      }
    });
  });
  
  images.forEach(img => imageObserver.observe(img));
};

// Preload critical resources
export const preloadResource = (url, as) => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = as;
  link.href = url;
  document.head.appendChild(link);
};

// Measure component render time
export const measureRenderTime = (componentName) => {
  const startTime = performance.now();
  return () => {
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    console.log(`${componentName} rendered in ${renderTime.toFixed(2)}ms`);
    
    // Send to analytics if needed
    if (window.gtag) {
      window.gtag('event', 'timing_complete', {
        name: componentName,
        value: Math.round(renderTime),
        event_category: 'Component Render'
      });
    }
  };
};

// Virtual scrolling helper
export const virtualScroll = (items, itemHeight, containerHeight) => {
  const totalHeight = items.length * itemHeight;
  const visibleCount = Math.ceil(containerHeight / itemHeight);
  
  return (scrollTop) => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + visibleCount + 1,
      items.length
    );
    
    return {
      visibleItems: items.slice(startIndex, endIndex),
      startIndex,
      endIndex,
      totalHeight,
      offsetY: startIndex * itemHeight
    };
  };
};

// Cache API wrapper
export const cacheAPI = {
  async get(key) {
    try {
      const cache = await caches.open('api-cache');
      const response = await cache.match(key);
      if (response) {
        const data = await response.json();
        if (data.expiry > Date.now()) {
          return data.value;
        }
        await cache.delete(key);
      }
    } catch (error) {
      console.error('Cache get error:', error);
    }
    return null;
  },
  
  async set(key, value, ttl = 3600000) { // 1 hour default
    try {
      const cache = await caches.open('api-cache');
      const data = {
        value,
        expiry: Date.now() + ttl
      };
      const response = new Response(JSON.stringify(data));
      await cache.put(key, response);
    } catch (error) {
      console.error('Cache set error:', error);
    }
  },
  
  async clear() {
    try {
      await caches.delete('api-cache');
    } catch (error) {
      console.error('Cache clear error:', error);
    }
  }
};

// Performance marks
export const perfMark = (name) => {
  if (performance.mark) {
    performance.mark(name);
  }
};

export const perfMeasure = (name, startMark, endMark) => {
  if (performance.measure) {
    try {
      performance.measure(name, startMark, endMark);
      const measure = performance.getEntriesByName(name)[0];
      console.log(`${name}: ${measure.duration.toFixed(2)}ms`);
      return measure.duration;
    } catch (error) {
      console.error('Performance measure error:', error);
    }
  }
  return 0;
};

// Prefetch likely navigations
export const prefetchRoutes = (routes) => {
  if ('prefetch' in HTMLLinkElement.prototype) {
    routes.forEach(route => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = route;
      document.head.appendChild(link);
    });
  }
};

// Performance optimization recommendations
export const getPerformanceRecommendations = () => {
  const recommendations = [];
  
  // Check for large images
  const images = document.querySelectorAll('img');
  images.forEach(img => {
    if (img.naturalWidth > 2000 || img.naturalHeight > 2000) {
      recommendations.push(`Large image detected: ${img.src}`);
    }
  });
  
  // Check for too many DOM nodes
  const nodeCount = document.querySelectorAll('*').length;
  if (nodeCount > 1500) {
    recommendations.push(`High DOM node count: ${nodeCount}. Consider virtualizing lists.`);
  }
  
  // Check for layout thrashing
  const reflows = performance.getEntriesByType('measure').filter(m => m.name.includes('reflow'));
  if (reflows.length > 10) {
    recommendations.push(`Multiple reflows detected (${reflows.length}). Batch DOM updates.`);
  }
  
  return recommendations;
};

// Initialize all performance monitors
export const initializePerformanceMonitoring = () => {
  // Track web vitals
  logPerformanceMetrics();
  
  // Monitor memory
  monitorMemoryUsage();
  
  // Track bundle size
  window.addEventListener('load', trackBundleSize);
  
  // Start FPS monitoring
  const fpsMonitor = new FPSMonitor();
  fpsMonitor.start();
  
  // Export for debugging
  window.__performanceUtils = {
    renderTracker: new RenderTimeTracker(),
    apiMonitor: new APIPerformanceMonitor(),
    fpsMonitor,
    getRecommendations: getPerformanceRecommendations
  };
  
  console.log('[Performance] Monitoring initialized. Access via window.__performanceUtils');
};