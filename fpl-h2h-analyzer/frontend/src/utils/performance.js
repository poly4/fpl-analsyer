// Performance optimization utilities

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