/**
 * Frontend cache service for FPL data
 * Implements TTL-based caching with different durations for different data types
 */

class CacheService {
  constructor() {
    this.cache = new Map();
    this.cacheConfig = {
      // Manager data - 24 hours
      manager_history: 24 * 60 * 60 * 1000,
      manager_info: 24 * 60 * 60 * 1000,
      
      // Live data - 30 seconds during matches
      live_data: 30 * 1000,
      live_battles: 30 * 1000,
      
      // League data - 1 hour
      league_standings: 60 * 60 * 1000,
      league_overview: 60 * 60 * 1000,
      
      // Analytics - 5 minutes
      h2h_analytics: 5 * 60 * 1000,
      predictions: 5 * 60 * 1000,
      
      // Static data - 24 hours
      bootstrap: 24 * 60 * 60 * 1000,
      fixtures: 24 * 60 * 60 * 1000,
      
      // Default - 5 minutes
      default: 5 * 60 * 1000
    };
    
    // Set up periodic cleanup
    this.startCleanup();
  }
  
  /**
   * Generate cache key from request details
   */
  generateKey(endpoint, params = {}) {
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${key}=${params[key]}`)
      .join('&');
    return `${endpoint}${sortedParams ? '?' + sortedParams : ''}`;
  }
  
  /**
   * Get TTL for specific data type
   */
  getTTL(dataType) {
    return this.cacheConfig[dataType] || this.cacheConfig.default;
  }
  
  /**
   * Set data in cache with TTL
   */
  set(key, data, dataType = 'default') {
    const ttl = this.getTTL(dataType);
    const expiresAt = Date.now() + ttl;
    
    this.cache.set(key, {
      data,
      expiresAt,
      dataType,
      cachedAt: Date.now()
    });
  }
  
  /**
   * Get data from cache if not expired
   */
  get(key) {
    const cached = this.cache.get(key);
    
    if (!cached) return null;
    
    if (Date.now() > cached.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  /**
   * Check if data exists and is valid
   */
  has(key) {
    const cached = this.cache.get(key);
    return cached && Date.now() <= cached.expiresAt;
  }
  
  /**
   * Invalidate specific cache entry
   */
  invalidate(key) {
    this.cache.delete(key);
  }
  
  /**
   * Invalidate all cache entries matching pattern
   */
  invalidatePattern(pattern) {
    const regex = new RegExp(pattern);
    for (const [key] of this.cache) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }
  
  /**
   * Clear all cache
   */
  clear() {
    this.cache.clear();
  }
  
  /**
   * Get cache statistics
   */
  getStats() {
    let valid = 0;
    let expired = 0;
    let totalSize = 0;
    
    const now = Date.now();
    
    for (const [key, value] of this.cache) {
      if (now <= value.expiresAt) {
        valid++;
      } else {
        expired++;
      }
      
      // Rough size estimation
      totalSize += JSON.stringify(value.data).length;
    }
    
    return {
      totalEntries: this.cache.size,
      validEntries: valid,
      expiredEntries: expired,
      approximateSizeKB: Math.round(totalSize / 1024)
    };
  }
  
  /**
   * Clean up expired entries periodically
   */
  startCleanup() {
    setInterval(() => {
      const now = Date.now();
      for (const [key, value] of this.cache) {
        if (now > value.expiresAt) {
          this.cache.delete(key);
        }
      }
    }, 60 * 1000); // Run every minute
  }
  
  /**
   * Batch get multiple keys
   */
  batchGet(keys) {
    const results = {};
    for (const key of keys) {
      const data = this.get(key);
      if (data) {
        results[key] = data;
      }
    }
    return results;
  }
  
  /**
   * Preload common data
   */
  async preload(apiClient, leagueId) {
    try {
      // Preload league standings
      const standings = await apiClient.getLeagueStandings(leagueId);
      if (standings) {
        const key = this.generateKey(`league/${leagueId}/standings`);
        this.set(key, standings, 'league_standings');
      }
      
      // Preload current gameweek
      const currentGW = await apiClient.getCurrentGameweek();
      if (currentGW) {
        const key = this.generateKey('bootstrap/current-gameweek');
        this.set(key, currentGW, 'bootstrap');
      }
      
      return true;
    } catch (error) {
      console.error('Cache preload error:', error);
      return false;
    }
  }
}

// Create singleton instance
const cacheService = new CacheService();

// Export cache-aware fetch wrapper
export const cachedFetch = async (url, options = {}, dataType = 'default') => {
  const key = cacheService.generateKey(url, options.params);
  
  // Check cache first
  const cached = cacheService.get(key);
  if (cached) {
    return { data: cached, fromCache: true };
  }
  
  // Fetch if not cached
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Cache successful response
    cacheService.set(key, data, dataType);
    
    return { data, fromCache: false };
  } catch (error) {
    // If offline, try to return stale cached data
    const staleData = cacheService.cache.get(key);
    if (staleData) {
      console.warn('Returning stale cached data due to fetch error');
      return { data: staleData.data, fromCache: true, stale: true };
    }
    
    throw error;
  }
};

export default cacheService;