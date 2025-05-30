import axios from 'axios';
import cacheService from './cache';

const API_BASE_URL = '/api';

// Get performance monitor from window if available
const getAPIMonitor = () => window.__performanceUtils?.apiMonitor;

// Create axios instance with interceptors
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor for performance tracking
api.interceptors.request.use(
  (config) => {
    // Track API request start
    const monitor = getAPIMonitor();
    if (monitor) {
      config.metadata = { requestId: monitor.startRequest(config.url) };
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for performance tracking and caching
api.interceptors.response.use(
  (response) => {
    // Track API request end
    const monitor = getAPIMonitor();
    if (monitor && response.config.metadata?.requestId) {
      monitor.endRequest(response.config.metadata.requestId, response.status);
    }
    return response;
  },
  (error) => {
    // Track failed request
    const monitor = getAPIMonitor();
    if (monitor && error.config?.metadata?.requestId) {
      monitor.endRequest(error.config.metadata.requestId, error.response?.status || 0);
    }
    return Promise.reject(error);
  }
);

// Cache-aware API wrapper
const cachedApiCall = async (endpoint, dataType, fetchFn, forceRefresh = false) => {
  const cacheKey = cacheService.generateKey(endpoint);
  
  // Skip cache if forced refresh
  if (!forceRefresh) {
    const cached = cacheService.get(cacheKey);
    if (cached) {
      console.log(`[API] Cache hit: ${endpoint}`);
      return cached;
    }
  }
  
  // Fetch from API
  console.log(`[API] Fetching: ${endpoint}`);
  const data = await fetchFn();
  
  // Cache the response
  cacheService.set(cacheKey, data, dataType);
  
  return data;
};

export const fplApi = {
  // Get current gameweek
  getCurrentGameweek: async (forceRefresh = false) => {
    return cachedApiCall(
      '/gameweek/current',
      'default',
      async () => {
        const response = await api.get('/gameweek/current');
        return response.data;
      },
      forceRefresh
    );
  },

  // Get league overview
  getLeagueOverview: async (leagueId, forceRefresh = false) => {
    return cachedApiCall(
      `/league/${leagueId}/overview`,
      'league_overview',
      async () => {
        const response = await api.get(`/league/${leagueId}/overview`);
        return response.data;
      },
      forceRefresh
    );
  },

  // Get league standings (Top Dog Premier League uses H2H format)
  getLeagueStandings: async (leagueId, forceRefresh = false) => {
    return cachedApiCall(
      `/league/standings/${leagueId}`,
      'league_standings',
      async () => {
        const response = await api.get(`/league/standings/${leagueId}`);
        return response.data;
      },
      forceRefresh
    );
  },

  // Get live H2H battles
  getLiveBattles: async (leagueId, gameweek = null, forceRefresh = false) => {
    const params = gameweek ? { gameweek } : {};
    const endpoint = `/h2h/live-battles/${leagueId}${gameweek ? `?gameweek=${gameweek}` : ''}`;
    
    return cachedApiCall(
      endpoint,
      'live_battles',
      async () => {
        const response = await api.get(`/h2h/live-battles/${leagueId}`, { params });
        return response.data;
      },
      forceRefresh
    );
  },

  // Get H2H battle details
  getBattleDetails: async (manager1Id, manager2Id, gameweek = null, forceRefresh = false) => {
    const params = gameweek ? { gameweek } : {};
    const endpoint = `/h2h/battle/${manager1Id}/${manager2Id}${gameweek ? `?gameweek=${gameweek}` : ''}`;
    
    return cachedApiCall(
      endpoint,
      'live_data',
      async () => {
        const response = await api.get(`/h2h/battle/${manager1Id}/${manager2Id}`, { params });
        return response.data;
      },
      forceRefresh
    );
  },

  // Get manager info
  getManagerInfo: async (managerId, forceRefresh = false) => {
    return cachedApiCall(
      `/manager/${managerId}`,
      'manager_info',
      async () => {
        const response = await api.get(`/manager/${managerId}`);
        return response.data;
      },
      forceRefresh
    );
  },

  // Get manager history
  getManagerHistory: async (managerId, forceRefresh = false) => {
    return cachedApiCall(
      `/manager/${managerId}/history`,
      'manager_history',
      async () => {
        const response = await api.get(`/manager/${managerId}/history`);
        return response.data;
      },
      forceRefresh
    );
  },

  // Analytics endpoints
  getComprehensiveAnalysis: async (manager1Id, manager2Id) => {
    const response = await api.get(`/analytics/h2h/comprehensive/${manager1Id}/${manager2Id}`);
    return response.data;
  },

  getDifferentialAnalysis: async (manager1Id, manager2Id) => {
    const response = await api.get(`/analytics/h2h/differential/${manager1Id}/${manager2Id}`);
    return response.data;
  },

  getChipStrategy: async (managerId) => {
    const response = await api.get(`/analytics/chip-strategy/${managerId}`);
    return response.data;
  },

  getTransferROI: async (managerId) => {
    const response = await api.get(`/analytics/v2/transfer-roi/${managerId}`);
    return response.data;
  },

  // Live match tracking
  getLiveMatchData: async (manager1Id, manager2Id) => {
    const response = await api.get(`/analytics/v2/live-match/${manager1Id}/${manager2Id}`);
    return response.data;
  },

  // Rate limiter status
  getRateLimiterMetrics: async () => {
    const response = await api.get('/rate-limiter/metrics');
    return response.data;
  },
};

// WebSocket connection for live updates
export class BattleWebSocket {
  constructor(manager1Id, manager2Id, onUpdate) {
    this.ws = null;
    this.manager1Id = manager1Id;
    this.manager2Id = manager2Id;
    this.onUpdate = onUpdate;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/h2h-battle/${this.manager1Id}/${this.manager2Id}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (this.onUpdate) {
        this.onUpdate(data);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.reconnect();
    };
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => this.connect(), 3000);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default api;