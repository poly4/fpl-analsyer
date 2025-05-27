// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const API_ENDPOINTS = {
  // League endpoints
  LEAGUE_OVERVIEW: (leagueId) => `/api/league/${leagueId}/overview`,
  LEAGUE_STANDINGS: (leagueId) => `/api/league/standings/${leagueId}`,
  
  // H2H endpoints
  LIVE_BATTLES: (leagueId) => `/api/h2h/live-battles/${leagueId}`,
  BATTLE_DETAILS: (manager1Id, manager2Id) => `/api/h2h/battle/${manager1Id}/${manager2Id}`,
  
  // Manager endpoints
  MANAGER_INFO: (managerId) => `/api/manager/${managerId}`,
  MANAGER_HISTORY: (managerId) => `/api/manager/${managerId}/history`,
  MANAGER_PICKS: (managerId, gameweek) => `/api/manager/${managerId}/gw/${gameweek}/picks`,
  
  // Gameweek endpoints
  CURRENT_GAMEWEEK: '/api/gameweek/current',
  
  // WebSocket endpoints
  WS_BATTLE: (manager1Id, manager2Id) => `/ws/h2h-battle/${manager1Id}/${manager2Id}`,
};

export const fetchAPI = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }
  
  return response.json();
};