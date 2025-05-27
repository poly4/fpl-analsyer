/**
 * FPL API Client with TypeScript support
 */

import { 
  BootstrapStatic, 
  Manager, 
  ManagerHistory, 
  ManagerPicks,
  LiveGameweekData,
  Fixture,
  H2HLeagueStandings,
  H2HMatch,
  ClassicLeagueStandings,
  Transfer,
  ElementSummary,
  DreamTeam,
  EventStatus,
  SetPieceNotes,
  ManagerCup,
  LeagueEntriesAndH2HMatches
} from '../types/fpl-api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class FPLApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchApi<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Master Data Endpoints
  async getBootstrapStatic(): Promise<BootstrapStatic> {
    // This endpoint is not exposed through our API yet
    // TODO: Add to backend
    throw new Error('Bootstrap static endpoint not implemented');
  }

  async getEventStatus(): Promise<EventStatus> {
    return this.fetchApi<EventStatus>('/event-status');
  }

  // Live Data Endpoints
  async getLiveGameweekData(gameweek: number): Promise<LiveGameweekData> {
    // This endpoint is not exposed directly
    // TODO: Add to backend
    throw new Error('Live gameweek data endpoint not implemented');
  }

  async getCurrentGameweek(): Promise<{ gameweek: number }> {
    return this.fetchApi<{ gameweek: number }>('/gameweek/current');
  }

  // Player Endpoints
  async getElementSummary(playerId: number): Promise<ElementSummary> {
    return this.fetchApi<ElementSummary>(`/player/${playerId}/summary`);
  }

  async getDreamTeam(gameweek: number): Promise<DreamTeam> {
    return this.fetchApi<DreamTeam>(`/dream-team/${gameweek}`);
  }

  async getSetPieceNotes(): Promise<SetPieceNotes> {
    return this.fetchApi<SetPieceNotes>('/set-piece-notes');
  }

  // Manager Endpoints
  async getManagerInfo(managerId: number): Promise<Manager> {
    return this.fetchApi<Manager>(`/manager/${managerId}`);
  }

  async getManagerHistory(managerId: number): Promise<ManagerHistory> {
    return this.fetchApi<ManagerHistory>(`/manager/${managerId}/history`);
  }

  async getManagerPicks(managerId: number, gameweek: number): Promise<ManagerPicks> {
    // This endpoint is not exposed directly
    // TODO: Add to backend
    throw new Error('Manager picks endpoint not implemented');
  }

  async getManagerTransfers(managerId: number): Promise<Transfer[]> {
    return this.fetchApi<Transfer[]>(`/manager/${managerId}/transfers`);
  }

  async getManagerTransfersLatest(managerId: number): Promise<Transfer[]> {
    return this.fetchApi<Transfer[]>(`/manager/${managerId}/transfers/latest`);
  }

  async getManagerCup(managerId: number): Promise<ManagerCup> {
    return this.fetchApi<ManagerCup>(`/manager/${managerId}/cup`);
  }

  // League Endpoints
  async getClassicLeagueStandings(
    leagueId: number, 
    pageStandings: number = 1, 
    pageNewEntries: number = 1
  ): Promise<ClassicLeagueStandings> {
    const params = new URLSearchParams({
      page_standings: pageStandings.toString(),
      page_new_entries: pageNewEntries.toString()
    });
    return this.fetchApi<ClassicLeagueStandings>(`/league/classic/${leagueId}/standings?${params}`);
  }

  async getH2HLeagueStandings(leagueId: number, page: number = 1): Promise<H2HLeagueStandings> {
    // This uses our existing endpoint
    return this.fetchApi<H2HLeagueStandings>(`/league/${leagueId}/overview`);
  }

  async getLeagueEntriesAndH2HMatches(leagueId: number): Promise<LeagueEntriesAndH2HMatches> {
    return this.fetchApi<LeagueEntriesAndH2HMatches>(`/league/${leagueId}/entries-and-h2h-matches`);
  }

  async getH2HMatches(leagueId: number, gameweek?: number): Promise<{ battles: any[] }> {
    const params = gameweek ? `?gameweek=${gameweek}` : '';
    return this.fetchApi<{ battles: any[] }>(`/h2h/live-battles/${leagueId}${params}`);
  }

  // Fixture Endpoints
  async getFixtures(gameweek?: number): Promise<Fixture[]> {
    // This endpoint is not exposed directly
    // TODO: Add to backend
    throw new Error('Fixtures endpoint not implemented');
  }

  // Rate Limiter Metrics
  async getRateLimiterMetrics(): Promise<any> {
    return this.fetchApi<any>('/rate-limiter/metrics');
  }

  // Health Check
  async getHealthStatus(): Promise<any> {
    return this.fetchApi<any>('/health');
  }
}

// Export singleton instance
export const fplApiClient = new FPLApiClient();

// Export class for testing
export default FPLApiClient;