"""
Advanced Analytics Service
Integrates all analytics modules for comprehensive H2H analysis
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .analytics import (
    DifferentialImpactCalculator,
    HistoricalPatternAnalyzer,
    PredictiveScoringEngine,
    TransferStrategyAnalyzer,
    LiveMatchTracker,
    ChipStrategyAnalyzer
)

logger = logging.getLogger(__name__)


class AdvancedAnalyticsService:
    """
    Main service for advanced H2H analytics
    """
    
    def __init__(self, live_data_service):
        self.live_data_service = live_data_service
        
        # Initialize all analytics modules
        self.differential_calculator = DifferentialImpactCalculator()
        self.pattern_analyzer = HistoricalPatternAnalyzer()
        self.predictive_engine = PredictiveScoringEngine()
        self.transfer_analyzer = TransferStrategyAnalyzer()
        self.live_tracker = LiveMatchTracker()
        self.chip_analyzer = ChipStrategyAnalyzer()
        
        logger.info("Advanced Analytics Service initialized with all modules")
    
    async def get_comprehensive_h2h_analysis(
        self,
        manager1_id: int,
        manager2_id: int,
        gameweek: Optional[int] = None,
        include_predictions: bool = True,
        include_patterns: bool = True,
        include_live: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive H2H analysis using all analytics modules
        """
        try:
            # Get current gameweek if not specified
            if gameweek is None:
                gameweek = await self.live_data_service.get_current_gameweek()
            
            logger.info(f"Starting comprehensive analysis for {manager1_id} vs {manager2_id} GW{gameweek}")
            
            # Fetch all required data
            data = await self._fetch_comprehensive_data(
                manager1_id, manager2_id, gameweek
            )
            
            analysis = {
                "meta": {
                    "manager1_id": manager1_id,
                    "manager2_id": manager2_id,
                    "gameweek": gameweek,
                    "generated_at": datetime.now().isoformat(),
                    "modules_included": []
                }
            }
            
            # 1. Differential Impact Analysis
            logger.info("Calculating differential impact...")
            differential_analysis = await self.differential_calculator.calculate_differential_impact(
                data['manager1_picks'],
                data['manager2_picks'],
                data['live_data'],
                data['bootstrap_data'],
                fixtures=data['fixtures']
            )
            analysis['differential_analysis'] = differential_analysis
            analysis['meta']['modules_included'].append('differential_impact')
            
            # 2. Historical Pattern Analysis
            if include_patterns and data['h2h_history']:
                logger.info("Analyzing historical patterns...")
                pattern_analysis = await self.pattern_analyzer.analyze_historical_patterns(
                    manager1_id,
                    manager2_id,
                    data['h2h_history'],
                    data['manager1_history'],
                    data['manager2_history'],
                    gameweek
                )
                analysis['historical_patterns'] = pattern_analysis
                analysis['meta']['modules_included'].append('historical_patterns')
            
            # 3. Predictive Scoring
            if include_predictions:
                logger.info("Generating predictions...")
                prediction = await self.predictive_engine.predict_match_outcome(
                    data['manager1_picks'],
                    data['manager2_picks'],
                    data['live_data'],
                    data['bootstrap_data'],
                    data['fixtures'],
                    data.get('h2h_history'),
                    gameweek
                )
                analysis['prediction'] = self._serialize_prediction(prediction)
                analysis['meta']['modules_included'].append('predictive_scoring')
            
            # 4. Transfer Strategy Analysis
            logger.info("Analyzing transfer strategies...")
            m1_transfer_analysis = await self.transfer_analyzer.analyze_transfer_strategy(
                manager1_id,
                data['manager1_transfers'],
                data['manager1_history'],
                data['bootstrap_data'],
                data['fixtures']
            )
            
            m2_transfer_analysis = await self.transfer_analyzer.analyze_transfer_strategy(
                manager2_id,
                data['manager2_transfers'],
                data['manager2_history'],
                data['bootstrap_data'],
                data['fixtures']
            )
            
            analysis['transfer_analysis'] = {
                'manager1': m1_transfer_analysis,
                'manager2': m2_transfer_analysis
            }
            analysis['meta']['modules_included'].append('transfer_strategy')
            
            # 5. Chip Strategy Analysis
            logger.info("Analyzing chip strategies...")
            m1_chip_analysis = await self.chip_analyzer.analyze_chip_strategy(
                manager1_id,
                data['manager1_history'],
                data['fixtures'],
                gameweek,
                data.get('h2h_history'),
                data['bootstrap_data'],
                data.get('manager2_history')  # For opponent chip awareness
            )
            
            m2_chip_analysis = await self.chip_analyzer.analyze_chip_strategy(
                manager2_id,
                data['manager2_history'],
                data['fixtures'],
                gameweek,
                data.get('h2h_history'),
                data['bootstrap_data'],
                data.get('manager1_history')
            )
            
            analysis['chip_analysis'] = {
                'manager1': m1_chip_analysis,
                'manager2': m2_chip_analysis
            }
            analysis['meta']['modules_included'].append('chip_strategy')
            
            # 6. Live Match Tracking (if matches in progress)
            if include_live:
                logger.info("Getting live match status...")
                live_state = await self.live_tracker.track_live_match(
                    manager1_id,
                    manager2_id,
                    data['manager1_picks'],
                    data['manager2_picks'],
                    data['live_data'],
                    data['fixtures'],
                    data['bootstrap_data']
                )
                analysis['live_tracking'] = self._serialize_live_state(live_state)
                analysis['meta']['modules_included'].append('live_tracking')
            
            # 7. Generate executive summary
            analysis['executive_summary'] = await self._generate_executive_summary(analysis)
            
            logger.info("Comprehensive analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            raise
    
    async def get_differential_analysis(
        self,
        manager1_id: int,
        manager2_id: int,
        gameweek: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get just differential impact analysis"""
        data = await self._fetch_basic_data(manager1_id, manager2_id, gameweek)
        return await self.differential_calculator.calculate_differential_impact(
            data['manager1_picks'],
            data['manager2_picks'],
            data['live_data'],
            data['bootstrap_data'],
            fixtures=data.get('fixtures')
        )
    
    async def get_transfer_roi_analysis(
        self,
        manager_id: int
    ) -> Dict[str, Any]:
        """Get transfer ROI analysis for a single manager"""
        transfers = await self.live_data_service.get_manager_transfers(manager_id)
        history = await self.live_data_service.get_manager_history(manager_id)
        bootstrap = await self.live_data_service.get_bootstrap_static()
        fixtures = await self.live_data_service.get_fixtures()
        
        return await self.transfer_analyzer.analyze_transfer_strategy(
            manager_id, transfers, history, bootstrap, fixtures
        )
    
    async def get_live_match_state(
        self,
        manager1_id: int,
        manager2_id: int,
        gameweek: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get current live match state"""
        data = await self._fetch_basic_data(manager1_id, manager2_id, gameweek)
        live_state = await self.live_tracker.track_live_match(
            manager1_id,
            manager2_id,
            data['manager1_picks'],
            data['manager2_picks'],
            data['live_data'],
            data['fixtures'],
            data['bootstrap_data']
        )
        return self._serialize_live_state(live_state)
    
    async def start_live_tracking(
        self,
        manager1_id: int,
        manager2_id: int,
        callback
    ) -> str:
        """Start continuous live tracking"""
        return await self.live_tracker.start_continuous_tracking(
            manager1_id, manager2_id, callback
        )
    
    async def stop_live_tracking(self, tracking_id: str):
        """Stop live tracking"""
        await self.live_tracker.stop_tracking(tracking_id)
    
    async def _fetch_comprehensive_data(
        self,
        manager1_id: int,
        manager2_id: int,
        gameweek: int
    ) -> Dict[str, Any]:
        """Fetch all data needed for comprehensive analysis"""
        # Fetch in parallel for performance
        import asyncio
        
        tasks = {
            'bootstrap_data': self.live_data_service.get_bootstrap_static(),
            'live_data': self.live_data_service.get_live_gameweek_data(gameweek),
            'fixtures': self.live_data_service.get_fixtures(),
            'manager1_info': self.live_data_service.get_manager_info(manager1_id),
            'manager2_info': self.live_data_service.get_manager_info(manager2_id),
            'manager1_history': self.live_data_service.get_manager_history(manager1_id),
            'manager2_history': self.live_data_service.get_manager_history(manager2_id),
            'manager1_picks': self.live_data_service.get_manager_picks(manager1_id, gameweek),
            'manager2_picks': self.live_data_service.get_manager_picks(manager2_id, gameweek),
            'manager1_transfers': self.live_data_service.get_manager_transfers(manager1_id),
            'manager2_transfers': self.live_data_service.get_manager_transfers(manager2_id),
        }
        
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )
        
        data = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {key}: {result}")
                data[key] = None
            else:
                data[key] = result
        
        # Get H2H history (needs league context - simplified)
        # In real implementation, would fetch from league endpoint
        data['h2h_history'] = []
        
        return data
    
    async def _fetch_basic_data(
        self,
        manager1_id: int,
        manager2_id: int,
        gameweek: Optional[int]
    ) -> Dict[str, Any]:
        """Fetch basic data for simpler analyses"""
        if gameweek is None:
            gameweek = await self.live_data_service.get_current_gameweek()
        
        import asyncio
        
        tasks = {
            'bootstrap_data': self.live_data_service.get_bootstrap_static(),
            'live_data': self.live_data_service.get_live_gameweek_data(gameweek),
            'fixtures': self.live_data_service.get_fixtures(),
            'manager1_picks': self.live_data_service.get_manager_picks(manager1_id, gameweek),
            'manager2_picks': self.live_data_service.get_manager_picks(manager2_id, gameweek),
        }
        
        results = await asyncio.gather(*tasks.values())
        
        return dict(zip(tasks.keys(), results))
    
    def _serialize_prediction(self, prediction) -> Dict[str, Any]:
        """Serialize prediction object to dict"""
        return {
            'expected_scores': {
                'manager1': prediction.manager1_expected,
                'manager2': prediction.manager2_expected
            },
            'win_probabilities': {
                'manager1': prediction.manager1_win_prob,
                'manager2': prediction.manager2_win_prob,
                'draw': prediction.draw_prob
            },
            'confidence_intervals': {
                'manager1': prediction.manager1_range,
                'manager2': prediction.manager2_range
            },
            'decisive_players': prediction.decisive_players,
            'confidence_level': prediction.confidence_level,
            'volatility': prediction.volatility
        }
    
    def _serialize_live_state(self, live_state) -> Dict[str, Any]:
        """Serialize live match state to dict"""
        return {
            'gameweek': live_state.gameweek,
            'last_updated': live_state.last_updated.isoformat(),
            'scores': {
                'manager1': {
                    'current': live_state.manager1_score,
                    'projected': live_state.manager1_projected
                },
                'manager2': {
                    'current': live_state.manager2_score,
                    'projected': live_state.manager2_projected
                }
            },
            'advantage': {
                'current_leader': live_state.current_advantage,
                'margin': live_state.advantage_margin,
                'momentum': live_state.momentum
            },
            'fixture_status': live_state.fixtures_status,
            'key_players': {
                'manager1': [
                    {
                        'name': p.name,
                        'points': p.current_points,
                        'is_captain': p.is_captain.get('manager1', False),
                        'provisional_bonus': p.provisional_bonus
                    }
                    for p in live_state.manager1_players[:5]
                ],
                'manager2': [
                    {
                        'name': p.name,
                        'points': p.current_points,
                        'is_captain': p.is_captain.get('manager2', False),
                        'provisional_bonus': p.provisional_bonus
                    }
                    for p in live_state.manager2_players[:5]
                ]
            }
        }
    
    async def _generate_executive_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from all analyses"""
        summary = {
            'overall_advantage': None,
            'confidence': 0,
            'key_factors': [],
            'recommendations': []
        }
        
        # Determine overall advantage
        advantages = []
        
        # From predictions
        if 'prediction' in analysis:
            pred = analysis['prediction']
            if pred['win_probabilities']['manager1'] > pred['win_probabilities']['manager2']:
                advantages.append(('manager1', pred['win_probabilities']['manager1']))
            else:
                advantages.append(('manager2', pred['win_probabilities']['manager2']))
        
        # From differentials
        if 'differential_analysis' in analysis:
            diff = analysis['differential_analysis']
            net_adv = diff.get('total_differential_impact', {}).get('net_advantage', 0)
            if net_adv > 0:
                advantages.append(('manager1', 0.5 + abs(net_adv) / 100))
            elif net_adv < 0:
                advantages.append(('manager2', 0.5 + abs(net_adv) / 100))
        
        # From historical patterns
        if 'historical_patterns' in analysis:
            psych = analysis['historical_patterns'].get('psychological_analysis', {})
            if psych.get('edge_holder'):
                edge_score = psych.get('psychological_edge_score', 0)
                advantages.append((psych['edge_holder'], 0.5 + abs(edge_score) / 2))
        
        # Average advantages
        if advantages:
            m1_scores = [score for adv, score in advantages if adv == 'manager1']
            m2_scores = [score for adv, score in advantages if adv == 'manager2']
            
            m1_avg = sum(m1_scores) / len(m1_scores) if m1_scores else 0.5
            m2_avg = sum(m2_scores) / len(m2_scores) if m2_scores else 0.5
            
            if m1_avg > m2_avg:
                summary['overall_advantage'] = 'manager1'
                summary['confidence'] = m1_avg
            else:
                summary['overall_advantage'] = 'manager2'
                summary['confidence'] = m2_avg
        
        # Key factors
        if 'differential_analysis' in analysis:
            diff_impact = analysis['differential_analysis'].get('total_differential_impact', {})
            if abs(diff_impact.get('net_advantage', 0)) > 10:
                summary['key_factors'].append(
                    f"Significant differential advantage: {diff_impact.get('net_advantage', 0):+.1f} points"
                )
        
        if 'prediction' in analysis:
            pred = analysis['prediction']
            if pred['volatility'] > 0.7:
                summary['key_factors'].append("High volatility match - anything could happen")
        
        if 'historical_patterns' in analysis:
            patterns = analysis['historical_patterns'].get('discovered_patterns', [])
            for pattern in patterns[:2]:  # Top 2 patterns
                if pattern['impact'] == 'high':
                    summary['key_factors'].append(pattern['description'])
        
        # Recommendations
        if 'chip_analysis' in analysis:
            for manager in ['manager1', 'manager2']:
                chip_recs = analysis['chip_analysis'].get(manager, {}).get('recommendations', [])
                if chip_recs and chip_recs[0]['confidence'] > 0.7:
                    summary['recommendations'].append(
                        f"{manager}: Consider {chip_recs[0]['chip']} in GW{chip_recs[0]['recommended_gameweek']}"
                    )
        
        return summary