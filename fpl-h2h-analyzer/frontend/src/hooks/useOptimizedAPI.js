import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { debounce, cacheAPI } from '../utils/performance';

export const useOptimizedAPI = (url, options = {}) => {
  const {
    enabled = true,
    cacheKey = url,
    cacheTTL = 300000, // 5 minutes
    debounceMs = 0,
    onSuccess,
    onError,
    retryCount = 3,
    retryDelay = 1000
  } = options;
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  
  const fetchData = useCallback(async (attempt = 0) => {
    if (!enabled || !url) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Check cache first
      const cached = await cacheAPI.get(cacheKey);
      if (cached) {
        setData(cached);
        setLoading(false);
        onSuccess?.(cached);
        return;
      }
      
      // Create abort controller for this request
      abortControllerRef.current = new AbortController();
      
      const response = await axios.get(url, {
        signal: abortControllerRef.current.signal
      });
      
      // Cache the response
      await cacheAPI.set(cacheKey, response.data, cacheTTL);
      
      setData(response.data);
      onSuccess?.(response.data);
    } catch (err) {
      if (axios.isCancel(err)) {
        console.log('Request cancelled:', url);
        return;
      }
      
      // Retry logic
      if (attempt < retryCount - 1) {
        console.log(`Retrying request (${attempt + 1}/${retryCount}):`, url);
        retryTimeoutRef.current = setTimeout(() => {
          fetchData(attempt + 1);
        }, retryDelay * Math.pow(2, attempt)); // Exponential backoff
      } else {
        setError(err);
        onError?.(err);
      }
    } finally {
      setLoading(false);
    }
  }, [url, enabled, cacheKey, cacheTTL, retryCount, retryDelay, onSuccess, onError]);
  
  // Debounced fetch if needed
  const debouncedFetch = useCallback(
    debounceMs > 0 ? debounce(fetchData, debounceMs) : fetchData,
    [fetchData, debounceMs]
  );
  
  useEffect(() => {
    debouncedFetch();
    
    return () => {
      // Cleanup: cancel ongoing requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [debouncedFetch]);
  
  const refetch = useCallback(() => {
    // Clear cache and refetch
    cacheAPI.set(cacheKey, null, 0);
    fetchData();
  }, [cacheKey, fetchData]);
  
  const mutate = useCallback((newData) => {
    setData(newData);
    if (newData) {
      cacheAPI.set(cacheKey, newData, cacheTTL);
    }
  }, [cacheKey, cacheTTL]);
  
  return {
    data,
    loading,
    error,
    refetch,
    mutate
  };
};

// Hook for paginated data
export const usePaginatedAPI = (baseUrl, options = {}) => {
  const {
    pageSize = 20,
    initialPage = 1,
    ...apiOptions
  } = options;
  
  const [page, setPage] = useState(initialPage);
  const [allData, setAllData] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  
  const url = `${baseUrl}?page=${page}&size=${pageSize}`;
  
  const { data, loading, error, refetch } = useOptimizedAPI(url, {
    ...apiOptions,
    onSuccess: (responseData) => {
      if (page === 1) {
        setAllData(responseData.items || []);
      } else {
        setAllData(prev => [...prev, ...(responseData.items || [])]);
      }
      setHasMore(responseData.hasMore || false);
      apiOptions.onSuccess?.(responseData);
    }
  });
  
  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
    }
  }, [loading, hasMore]);
  
  const reset = useCallback(() => {
    setPage(1);
    setAllData([]);
    setHasMore(true);
  }, []);
  
  return {
    data: allData,
    loading,
    error,
    hasMore,
    loadMore,
    refetch,
    reset,
    page
  };
};

// Hook for real-time data with WebSocket fallback
export const useRealtimeAPI = (url, wsUrl, options = {}) => {
  const { data, loading, error, refetch } = useOptimizedAPI(url, options);
  const [realtimeData, setRealtimeData] = useState(null);
  const wsRef = useRef(null);
  
  useEffect(() => {
    if (!wsUrl || !data) return;
    
    // Initialize WebSocket connection
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onmessage = (event) => {
        const update = JSON.parse(event.data);
        setRealtimeData(update);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Fallback to polling
        const pollInterval = setInterval(refetch, 30000); // Poll every 30s
        return () => clearInterval(pollInterval);
      };
    } catch (err) {
      console.error('WebSocket connection failed:', err);
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [wsUrl, data, refetch]);
  
  return {
    data: realtimeData || data,
    loading,
    error,
    refetch,
    isRealtime: !!realtimeData
  };
};