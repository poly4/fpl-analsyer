import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pickle
import json
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

from app.services.live_data_v2 import LiveDataService
from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)


@dataclass
class MLPrediction:
    """Machine learning prediction result"""
    player_id: int
    gameweek: int
    predicted_points: float
    confidence: float
    feature_importance: Dict[str, float]
    model_version: str
    predicted_at: datetime


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_name: str
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Squared Error
    r2: float   # R-squared
    accuracy_within_2: float  # Percentage of predictions within 2 points
    last_trained: datetime
    training_samples: int
    features_used: List[str]


@dataclass
class FeatureSet:
    """Feature set for ML model"""
    # Player stats
    total_points: float
    minutes: float
    goals_scored: float
    assists: float
    clean_sheets: float
    goals_conceded: float
    own_goals: float
    penalties_saved: float
    penalties_missed: float
    yellow_cards: float
    red_cards: float
    saves: float
    bonus: float
    bps: float
    influence: float
    creativity: float
    threat: float
    ict_index: float
    
    # Form metrics
    form: float
    form_5: float  # Last 5 gameweeks
    form_3: float  # Last 3 gameweeks
    
    # Fixture data
    fixture_difficulty: float
    is_home: bool
    opponent_strength: float
    
    # Historical performance
    avg_points_home: float
    avg_points_away: float
    avg_points_vs_opponent: float
    
    # Team context
    team_form: float
    team_goals_scored: float
    team_goals_conceded: float
    
    # Position and role
    position: int  # 1=GK, 2=DEF, 3=MID, 4=FWD
    price: float
    ownership: float
    
    # Season context
    gameweek: int
    season_progress: float  # 0.0 to 1.0
    

class MLPredictor:
    """Machine learning predictor for FPL player performance"""
    
    def __init__(self, live_data_service: LiveDataService, cache: RedisCache):
        self.live_data_service = live_data_service
        self.cache = cache
        
        # Model configuration
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        }
        
        self.scaler = StandardScaler()
        self.trained_models = {}
        self.model_performance = {}
        self.feature_names = []
        
        # Training configuration
        self.min_training_samples = 1000
        self.retrain_interval = timedelta(days=7)  # Retrain weekly
        self.validation_split = 0.2
        
        # Model persistence
        self.model_dir = "ml_models"
        os.makedirs(self.model_dir, exist_ok=True)
        
    async def initialize(self):
        """Initialize ML predictor"""
        logger.info("Initializing ML predictor...")
        
        # Load existing models if available
        await self._load_models()
        
        # Check if retraining is needed
        if await self._should_retrain():
            logger.info("Retraining models...")
            await self.train_models()
        else:
            logger.info("Using existing trained models")
            
    async def predict_player_points(
        self, 
        player_id: int, 
        gameweek: int,
        model_name: str = 'random_forest'
    ) -> Optional[MLPrediction]:
        """Predict points for a specific player"""
        
        if model_name not in self.trained_models:
            logger.warning(f"Model {model_name} not trained")
            return None
            
        # Generate features for the player
        features = await self._generate_features(player_id, gameweek)
        if not features:
            return None
            
        # Convert to DataFrame
        feature_df = pd.DataFrame([asdict(features)])
        
        # Ensure feature order matches training
        feature_df = feature_df.reindex(columns=self.feature_names, fill_value=0)
        
        # Scale features
        scaled_features = self.scaler.transform(feature_df)
        
        # Make prediction
        model = self.trained_models[model_name]
        predicted_points = model.predict(scaled_features)[0]
        
        # Calculate confidence based on feature importance and model uncertainty
        confidence = await self._calculate_prediction_confidence(
            model, scaled_features, features
        )
        
        # Get feature importance
        feature_importance = dict(zip(
            self.feature_names, 
            model.feature_importances_
        ))
        
        return MLPrediction(
            player_id=player_id,
            gameweek=gameweek,
            predicted_points=max(0, predicted_points),  # Ensure non-negative
            confidence=confidence,
            feature_importance=feature_importance,
            model_version=f"{model_name}_v1",
            predicted_at=datetime.utcnow()
        )
        
    async def train_models(self, force_retrain: bool = False) -> Dict[str, ModelPerformance]:
        """Train or retrain ML models"""
        
        logger.info("Starting model training...")
        
        # Collect training data
        training_data = await self._collect_training_data()
        
        if len(training_data) < self.min_training_samples:
            logger.warning(f"Insufficient training data: {len(training_data)} samples (minimum: {self.min_training_samples})")
            return {}
            
        # Prepare data
        X, y, feature_names = await self._prepare_training_data(training_data)
        self.feature_names = feature_names
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.validation_split, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        performance_results = {}
        
        # Train each model
        for model_name, model in self.models.items():
            logger.info(f"Training {model_name}...")
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            
            # Calculate performance metrics
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            # Calculate accuracy within 2 points
            within_2 = np.mean(np.abs(y_test - y_pred) <= 2)
            
            performance = ModelPerformance(
                model_name=model_name,
                mae=mae,
                rmse=rmse,
                r2=r2,
                accuracy_within_2=within_2,
                last_trained=datetime.utcnow(),
                training_samples=len(training_data),
                features_used=feature_names
            )
            
            self.trained_models[model_name] = model
            self.model_performance[model_name] = performance
            performance_results[model_name] = performance
            
            logger.info(f"{model_name} performance: MAE={mae:.2f}, RMSE={rmse:.2f}, R2={r2:.3f}, Accuracy±2={within_2:.1%}")
            
        # Save models
        await self._save_models()
        
        logger.info("Model training completed")
        return performance_results
        
    async def _collect_training_data(self) -> List[Dict]:
        """Collect historical data for training"""
        
        # Try cache first
        cache_key = "ml_training_data"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        logger.info("Collecting training data from FPL API...")
        
        bootstrap = await self.live_data_service.get_bootstrap_static()
        current_gw = bootstrap["current_event"]
        
        training_data = []
        
        # Collect data for last 10 gameweeks (or available gameweeks)
        for gw in range(max(1, current_gw - 10), current_gw):
            try:
                # Get gameweek data
                gw_data = await self.live_data_service.get_live_gameweek_data(gw)
                if not gw_data:
                    continue
                    
                # Get fixtures for the gameweek
                fixtures = await self.live_data_service.get_fixtures(gw)
                
                # Process each player's performance
                for element_id, stats in gw_data.get("elements", {}).items():
                    try:
                        player_id = int(element_id)
                        points = stats.get("total_points", 0)
                        
                        # Generate features for this player/gameweek
                        features = await self._generate_historical_features(
                            player_id, gw, bootstrap, fixtures, stats
                        )
                        
                        if features:
                            training_sample = {
                                "player_id": player_id,
                                "gameweek": gw,
                                "actual_points": points,
                                "features": asdict(features)
                            }
                            training_data.append(training_sample)
                            
                    except (ValueError, KeyError) as e:
                        continue
                        
            except Exception as e:
                logger.error(f"Error collecting data for gameweek {gw}: {e}")
                continue
                
        # Cache for 1 hour
        await self.cache.set(cache_key, training_data, ttl=3600)
        
        logger.info(f"Collected {len(training_data)} training samples")
        return training_data
        
    async def _generate_features(self, player_id: int, gameweek: int) -> Optional[FeatureSet]:
        """Generate features for current prediction"""
        
        try:
            bootstrap = await self.live_data_service.get_bootstrap_static()
            
            # Find player in bootstrap
            player = None
            for element in bootstrap["elements"]:
                if element["id"] == player_id:
                    player = element
                    break
                    
            if not player:
                return None
                
            # Get fixtures
            fixtures = await self.live_data_service.get_fixtures(gameweek)
            
            # Generate features
            return await self._build_feature_set(
                player, gameweek, bootstrap, fixtures
            )
            
        except Exception as e:
            logger.error(f"Error generating features for player {player_id}, GW {gameweek}: {e}")
            return None
            
    async def _generate_historical_features(
        self, 
        player_id: int, 
        gameweek: int, 
        bootstrap: Dict, 
        fixtures: List, 
        stats: Dict
    ) -> Optional[FeatureSet]:
        """Generate features for historical training data"""
        
        try:
            # Find player in bootstrap
            player = None
            for element in bootstrap["elements"]:
                if element["id"] == player_id:
                    player = element
                    break
                    
            if not player:
                return None
                
            return await self._build_feature_set(
                player, gameweek, bootstrap, fixtures, historical_stats=stats
            )
            
        except Exception as e:
            logger.error(f"Error generating historical features: {e}")
            return None
            
    async def _build_feature_set(
        self, 
        player: Dict, 
        gameweek: int, 
        bootstrap: Dict, 
        fixtures: List,
        historical_stats: Optional[Dict] = None
    ) -> FeatureSet:
        """Build feature set from player and context data"""
        
        # Basic player stats
        stats = historical_stats or player
        
        # Find player's fixture for this gameweek
        fixture_difficulty = 3.0  # Default
        is_home = True
        opponent_strength = 3.0
        
        team_id = player["team"]
        for fixture in fixtures:
            if fixture["team_h"] == team_id:
                fixture_difficulty = fixture.get("team_h_difficulty", 3)
                is_home = True
                opponent_strength = self._get_team_strength(fixture["team_a"], bootstrap)
                break
            elif fixture["team_a"] == team_id:
                fixture_difficulty = fixture.get("team_a_difficulty", 3)
                is_home = False
                opponent_strength = self._get_team_strength(fixture["team_h"], bootstrap)
                break
                
        # Calculate form metrics
        form = float(stats.get("form", 0))
        form_5 = form  # Simplified - would need historical data
        form_3 = form
        
        # Team context
        team_form = self._get_team_form(team_id, bootstrap)
        
        # Historical averages (simplified)
        avg_points_home = float(stats.get("points_per_game", 0)) * 1.1  # Slight home advantage
        avg_points_away = float(stats.get("points_per_game", 0)) * 0.9
        avg_points_vs_opponent = float(stats.get("points_per_game", 0))
        
        return FeatureSet(
            # Player stats
            total_points=float(stats.get("total_points", 0)),
            minutes=float(stats.get("minutes", 0)),
            goals_scored=float(stats.get("goals_scored", 0)),
            assists=float(stats.get("assists", 0)),
            clean_sheets=float(stats.get("clean_sheets", 0)),
            goals_conceded=float(stats.get("goals_conceded", 0)),
            own_goals=float(stats.get("own_goals", 0)),
            penalties_saved=float(stats.get("penalties_saved", 0)),
            penalties_missed=float(stats.get("penalties_missed", 0)),
            yellow_cards=float(stats.get("yellow_cards", 0)),
            red_cards=float(stats.get("red_cards", 0)),
            saves=float(stats.get("saves", 0)),
            bonus=float(stats.get("bonus", 0)),
            bps=float(stats.get("bps", 0)),
            influence=float(stats.get("influence", 0)),
            creativity=float(stats.get("creativity", 0)),
            threat=float(stats.get("threat", 0)),
            ict_index=float(stats.get("ict_index", 0)),
            
            # Form metrics
            form=form,
            form_5=form_5,
            form_3=form_3,
            
            # Fixture data
            fixture_difficulty=fixture_difficulty,
            is_home=is_home,
            opponent_strength=opponent_strength,
            
            # Historical performance
            avg_points_home=avg_points_home,
            avg_points_away=avg_points_away,
            avg_points_vs_opponent=avg_points_vs_opponent,
            
            # Team context
            team_form=team_form,
            team_goals_scored=self._get_team_goals_scored(team_id, bootstrap),
            team_goals_conceded=self._get_team_goals_conceded(team_id, bootstrap),
            
            # Position and role
            position=player["element_type"],
            price=float(player.get("now_cost", 0)) / 10.0,
            ownership=float(player.get("selected_by_percent", 0)),
            
            # Season context
            gameweek=gameweek,
            season_progress=gameweek / 38.0
        )
        
    def _get_team_strength(self, team_id: int, bootstrap: Dict) -> float:
        """Get team strength rating"""
        for team in bootstrap["teams"]:
            if team["id"] == team_id:
                return (team.get("strength_overall_home", 1000) + 
                       team.get("strength_overall_away", 1000)) / 2000.0 * 5.0
        return 3.0
        
    def _get_team_form(self, team_id: int, bootstrap: Dict) -> float:
        """Get team form rating"""
        # Simplified - would calculate from recent results
        return 3.0
        
    def _get_team_goals_scored(self, team_id: int, bootstrap: Dict) -> float:
        """Get team goals scored"""
        # Simplified - would get from team stats
        return 1.5
        
    def _get_team_goals_conceded(self, team_id: int, bootstrap: Dict) -> float:
        """Get team goals conceded"""
        # Simplified - would get from team stats
        return 1.2
        
    async def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare training data for ML models"""
        
        features_list = []
        targets = []
        
        for sample in training_data:
            features_list.append(sample["features"])
            targets.append(sample["actual_points"])
            
        # Convert to DataFrame
        features_df = pd.DataFrame(features_list)
        
        # Get feature names
        feature_names = list(features_df.columns)
        
        # Convert to numpy arrays
        X = features_df.values
        y = np.array(targets)
        
        return X, y, feature_names
        
    async def _calculate_prediction_confidence(
        self, 
        model, 
        features: np.ndarray, 
        feature_set: FeatureSet
    ) -> float:
        """Calculate confidence score for prediction"""
        
        # Base confidence from model performance
        model_name = type(model).__name__.lower()
        if model_name in self.model_performance:
            base_confidence = self.model_performance[model_name].r2
        else:
            base_confidence = 0.5
            
        # Adjust based on data quality
        data_quality = 1.0
        
        # Reduce confidence for players with limited data
        if feature_set.minutes < 900:  # Less than 10 full games
            data_quality *= 0.8
            
        # Reduce confidence for extreme fixture difficulty
        if feature_set.fixture_difficulty >= 4:
            data_quality *= 0.9
            
        return min(1.0, base_confidence * data_quality)
        
    async def _should_retrain(self) -> bool:
        """Check if models should be retrained"""
        
        if not self.trained_models:
            return True
            
        # Check last training time
        for performance in self.model_performance.values():
            if datetime.utcnow() - performance.last_trained > self.retrain_interval:
                return True
                
        return False
        
    async def _save_models(self):
        """Save trained models to disk"""
        
        try:
            # Save models
            for name, model in self.trained_models.items():
                model_path = os.path.join(self.model_dir, f"{name}_model.pkl")
                joblib.dump(model, model_path)
                
            # Save scaler
            scaler_path = os.path.join(self.model_dir, "scaler.pkl")
            joblib.dump(self.scaler, scaler_path)
            
            # Save feature names
            features_path = os.path.join(self.model_dir, "feature_names.json")
            with open(features_path, 'w') as f:
                json.dump(self.feature_names, f)
                
            # Save performance metrics
            performance_path = os.path.join(self.model_dir, "performance.json")
            performance_dict = {
                name: {
                    "mae": perf.mae,
                    "rmse": perf.rmse,
                    "r2": perf.r2,
                    "accuracy_within_2": perf.accuracy_within_2,
                    "last_trained": perf.last_trained.isoformat(),
                    "training_samples": perf.training_samples
                }
                for name, perf in self.model_performance.items()
            }
            
            with open(performance_path, 'w') as f:
                json.dump(performance_dict, f, indent=2)
                
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            
    async def _load_models(self):
        """Load trained models from disk"""
        
        try:
            # Load feature names
            features_path = os.path.join(self.model_dir, "feature_names.json")
            if os.path.exists(features_path):
                with open(features_path, 'r') as f:
                    self.feature_names = json.load(f)
                    
            # Load scaler
            scaler_path = os.path.join(self.model_dir, "scaler.pkl")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                
            # Load models
            for name in self.models.keys():
                model_path = os.path.join(self.model_dir, f"{name}_model.pkl")
                if os.path.exists(model_path):
                    self.trained_models[name] = joblib.load(model_path)
                    
            # Load performance metrics
            performance_path = os.path.join(self.model_dir, "performance.json")
            if os.path.exists(performance_path):
                with open(performance_path, 'r') as f:
                    performance_dict = json.load(f)
                    
                for name, perf_data in performance_dict.items():
                    self.model_performance[name] = ModelPerformance(
                        model_name=name,
                        mae=perf_data["mae"],
                        rmse=perf_data["rmse"],
                        r2=perf_data["r2"],
                        accuracy_within_2=perf_data["accuracy_within_2"],
                        last_trained=datetime.fromisoformat(perf_data["last_trained"]),
                        training_samples=perf_data["training_samples"],
                        features_used=self.feature_names
                    )
                    
            logger.info(f"Loaded {len(self.trained_models)} trained models")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            
    async def get_model_performance(self) -> Dict[str, ModelPerformance]:
        """Get model performance metrics"""
        return self.model_performance.copy()
        
    async def predict_batch(
        self, 
        player_ids: List[int], 
        gameweek: int,
        model_name: str = 'random_forest'
    ) -> List[MLPrediction]:
        """Predict points for multiple players"""
        
        predictions = []
        
        for player_id in player_ids:
            prediction = await self.predict_player_points(player_id, gameweek, model_name)
            if prediction:
                predictions.append(prediction)
                
        return predictions