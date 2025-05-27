"""
Unit tests for all FPL API endpoints
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.live_data_v2 import LiveDataService
from app.services.rate_limiter import RequestPriority


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter client"""
    mock_client = Mock()
    mock_client.request = AsyncMock()
    mock_client.start = AsyncMock()
    mock_client.stop = AsyncMock()
    mock_client.get_metrics = Mock(return_value={
        "total_requests": 0,
        "successful_requests": 0,
        "rate_limited_requests": 0
    })
    return mock_client


@pytest.fixture
async def live_data_service(mock_rate_limiter):
    """Create LiveDataService with mocked dependencies"""
    with patch('app.services.live_data_v2.RateLimitedFPLClient', return_value=mock_rate_limiter):
        service = LiveDataService()
        await service._ensure_initialized()
        yield service
        await service.close()


class TestMasterDataEndpoints:
    """Test master data endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_bootstrap_static(self, live_data_service, mock_rate_limiter):
        """Test bootstrap static endpoint"""
        mock_data = {
            "events": [{"id": 1, "name": "Gameweek 1"}],
            "teams": [{"id": 1, "name": "Arsenal"}],
            "elements": [{"id": 1, "web_name": "Salah"}]
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_bootstrap_static()
        
        assert result == mock_data
        mock_rate_limiter.request.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_event_status(self, live_data_service, mock_rate_limiter):
        """Test event status endpoint"""
        mock_data = {
            "status": [{"event": 1, "bonus_added": True}],
            "leagues": "Updated"
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_event_status()
        
        assert result == mock_data
        assert mock_rate_limiter.request.call_args[1]['priority'] == RequestPriority.CRITICAL


class TestPlayerEndpoints:
    """Test player-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_element_summary(self, live_data_service, mock_rate_limiter):
        """Test element summary endpoint"""
        mock_data = {
            "fixtures": [],
            "history": [],
            "history_past": []
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_element_summary(1)
        
        assert result == mock_data
        assert "element-summary/1" in mock_rate_limiter.request.call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_get_dream_team(self, live_data_service, mock_rate_limiter):
        """Test dream team endpoint"""
        mock_data = {
            "team": [{"element": 1, "points": 10}],
            "top_player": {"id": 1, "points": 10}
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_dream_team(1)
        
        assert result == mock_data
        assert "dream-team/1" in mock_rate_limiter.request.call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_get_set_piece_notes(self, live_data_service, mock_rate_limiter):
        """Test set piece notes endpoint"""
        mock_data = {
            "teams": [{"id": 1, "notes": []}]
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_set_piece_notes()
        
        assert result == mock_data
        assert mock_rate_limiter.request.call_args[1]['priority'] == RequestPriority.LOW


class TestManagerEndpoints:
    """Test manager-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_manager_cup(self, live_data_service, mock_rate_limiter):
        """Test manager cup endpoint"""
        mock_data = {
            "cup_league": None,
            "matches": [],
            "status": {"qualification_state": None}
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_manager_cup(123)
        
        assert result == mock_data
        assert "entry/123/cup" in mock_rate_limiter.request.call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_get_manager_transfers(self, live_data_service, mock_rate_limiter):
        """Test manager transfers endpoint"""
        mock_data = [
            {"element_in": 1, "element_out": 2, "event": 1}
        ]
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_manager_transfers(123)
        
        assert result == mock_data
        assert "entry/123/transfers" in mock_rate_limiter.request.call_args[0][0]


class TestLeagueEndpoints:
    """Test league-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_classic_league_standings(self, live_data_service, mock_rate_limiter):
        """Test classic league standings endpoint"""
        mock_data = {
            "league": {"id": 1, "name": "Test League"},
            "standings": {"results": [], "has_next": False}
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_classic_league_standings(1, 1, 1)
        
        assert result == mock_data
        assert "leagues-classic/1/standings" in mock_rate_limiter.request.call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_get_league_entries_and_h2h_matches(self, live_data_service, mock_rate_limiter):
        """Test league entries and H2H matches endpoint"""
        mock_data = {
            "league_entries": [],
            "matches": []
        }
        mock_rate_limiter.request.return_value = mock_data
        
        result = await live_data_service.get_league_entries_and_h2h_matches(1)
        
        assert result == mock_data
        assert "leagues-entries-and-h2h-matches/league/1" in mock_rate_limiter.request.call_args[0][0]


class TestPaginationHelpers:
    """Test pagination helper methods"""
    
    @pytest.mark.asyncio
    async def test_get_all_h2h_matches(self, live_data_service, mock_rate_limiter):
        """Test paginated H2H matches retrieval"""
        # Mock paginated responses
        page1 = {"results": [{"id": 1}, {"id": 2}], "has_next": True}
        page2 = {"results": [{"id": 3}], "has_next": False}
        
        mock_rate_limiter.request.side_effect = [page1, page2]
        
        result = await live_data_service.get_all_h2h_matches(1)
        
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[2]["id"] == 3
        
    @pytest.mark.asyncio
    async def test_get_all_classic_league_standings(self, live_data_service, mock_rate_limiter):
        """Test paginated classic league standings retrieval"""
        # Mock paginated responses
        page1 = {
            "league": {"id": 1, "name": "Test"},
            "standings": {"results": [{"id": 1}, {"id": 2}], "has_next": True}
        }
        page2 = {
            "standings": {"results": [{"id": 3}], "has_next": False}
        }
        
        mock_rate_limiter.request.side_effect = [page1, page2]
        
        result = await live_data_service.get_all_classic_league_standings(1)
        
        assert result["league"]["name"] == "Test"
        assert len(result["standings"]["results"]) == 3


class TestCacheTTL:
    """Test cache TTL configuration"""
    
    def test_cache_ttl_live_data(self, live_data_service):
        """Test TTL for live data endpoints"""
        assert live_data_service._get_cache_ttl("event/1/live") == 30
        assert live_data_service._get_cache_ttl("event-status") == 30
        
    def test_cache_ttl_volatile_data(self, live_data_service):
        """Test TTL for volatile data endpoints"""
        assert live_data_service._get_cache_ttl("entry/1/event/1/picks") == 60
        assert live_data_service._get_cache_ttl("entry/1/transfers-latest") == 60
        
    def test_cache_ttl_static_data(self, live_data_service):
        """Test TTL for static data endpoints"""
        assert live_data_service._get_cache_ttl("bootstrap-static") == 1800
        assert live_data_service._get_cache_ttl("fixtures") == 1800
        assert live_data_service._get_cache_ttl("team/set-piece-notes") == 7200
        
    def test_cache_ttl_league_data(self, live_data_service):
        """Test TTL for league data endpoints"""
        assert live_data_service._get_cache_ttl("leagues-classic/1/standings") == 300
        assert live_data_service._get_cache_ttl("leagues-h2h/1/standings") == 300


class TestErrorHandling:
    """Test error handling in endpoints"""
    
    @pytest.mark.asyncio
    async def test_bootstrap_dynamic_not_implemented(self, live_data_service):
        """Test bootstrap dynamic returns None (auth required)"""
        result = await live_data_service.get_bootstrap_dynamic(123)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_endpoint_error_handling(self, live_data_service, mock_rate_limiter):
        """Test error handling for failed requests"""
        mock_rate_limiter.request.side_effect = Exception("API Error")
        
        result = await live_data_service.get_manager_info(123)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])