import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fplApi = {
  // Get current gameweek
  getCurrentGameweek: async () => {
    const response = await api.get('/gameweek/current');
    return response.data;
  },

  // Get league overview
  getLeagueOverview: async (leagueId) => {
    const response = await api.get(`/league/${leagueId}/overview`);
    return response.data;
  },

  // Get live H2H battles
  getLiveBattles: async (leagueId, gameweek = null) => {
    const params = gameweek ? { gameweek } : {};
    const response = await api.get(`/h2h/live-battles/${leagueId}`, { params });
    return response.data;
  },

  // Get H2H battle details
  getBattleDetails: async (manager1Id, manager2Id, gameweek = null) => {
    const params = gameweek ? { gameweek } : {};
    const response = await api.get(`/h2h/battle/${manager1Id}/${manager2Id}`, { params });
    return response.data;
  },

  // Get manager info
  getManagerInfo: async (managerId) => {
    const response = await api.get(`/manager/${managerId}`);
    return response.data;
  },

  // Get manager history
  getManagerHistory: async (managerId) => {
    const response = await api.get(`/manager/${managerId}/history`);
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