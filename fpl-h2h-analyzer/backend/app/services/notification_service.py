import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from enum import Enum
import aioredis
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications available"""
    GOAL = "goal"
    ASSIST = "assist"
    BONUS_CHANGE = "bonus_change"
    RED_CARD = "red_card"
    INJURY = "injury"
    CAPTAIN_HAUL = "captain_haul"
    CAPTAIN_FAIL = "captain_fail"
    CLEAN_SHEET = "clean_sheet"
    CLEAN_SHEET_LOST = "clean_sheet_lost"
    PENALTY_SAVE = "penalty_save"
    PENALTY_MISS = "penalty_miss"
    OWN_GOAL = "own_goal"
    YELLOW_CARD = "yellow_card"
    SUBSTITUTION = "substitution"
    BATTLE_UPDATE = "battle_update"


class NotificationPriority(Enum):
    """Priority levels for notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationPreferences:
    """User notification preferences"""
    def __init__(self, preferences: Dict[str, Any] = None):
        if preferences is None:
            preferences = {}
        
        # Default preferences
        self.enabled = preferences.get('enabled', True)
        self.browser_push = preferences.get('browser_push', True)
        self.in_app = preferences.get('in_app', True)
        
        # Event-specific preferences
        self.events = {
            NotificationType.GOAL: preferences.get('goal', True),
            NotificationType.ASSIST: preferences.get('assist', True),
            NotificationType.BONUS_CHANGE: preferences.get('bonus_change', True),
            NotificationType.RED_CARD: preferences.get('red_card', True),
            NotificationType.INJURY: preferences.get('injury', True),
            NotificationType.CAPTAIN_HAUL: preferences.get('captain_haul', True),
            NotificationType.CAPTAIN_FAIL: preferences.get('captain_fail', True),
            NotificationType.CLEAN_SHEET: preferences.get('clean_sheet', True),
            NotificationType.CLEAN_SHEET_LOST: preferences.get('clean_sheet_lost', True),
            NotificationType.PENALTY_SAVE: preferences.get('penalty_save', True),
            NotificationType.PENALTY_MISS: preferences.get('penalty_miss', True),
            NotificationType.OWN_GOAL: preferences.get('own_goal', True),
            NotificationType.YELLOW_CARD: preferences.get('yellow_card', False),
            NotificationType.SUBSTITUTION: preferences.get('substitution', False),
            NotificationType.BATTLE_UPDATE: preferences.get('battle_update', True),
        }
        
        # Priority thresholds
        self.min_priority = NotificationPriority[preferences.get('min_priority', 'LOW')]
        
        # H2H specific settings
        self.only_my_players = preferences.get('only_my_players', False)
        self.include_opponent_players = preferences.get('include_opponent_players', True)
        self.captain_alerts_only = preferences.get('captain_alerts_only', False)
        
        # Timing preferences
        self.quiet_hours = preferences.get('quiet_hours', {
            'enabled': False,
            'start': '22:00',
            'end': '08:00'
        })


class Notification:
    """Represents a single notification"""
    def __init__(
        self,
        type: NotificationType,
        title: str,
        message: str,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        icon: Optional[str] = None,
        url: Optional[str] = None
    ):
        self.id = f"{datetime.utcnow().timestamp()}_{type.value}"
        self.type = type
        self.title = title
        self.message = message
        self.data = data
        self.priority = priority
        self.icon = icon or self._get_default_icon(type)
        self.url = url
        self.timestamp = datetime.utcnow()
        self.read = False
    
    def _get_default_icon(self, type: NotificationType) -> str:
        """Get default icon based on notification type"""
        icons = {
            NotificationType.GOAL: "⚽",
            NotificationType.ASSIST: "🅰️",
            NotificationType.BONUS_CHANGE: "🎯",
            NotificationType.RED_CARD: "🟥",
            NotificationType.INJURY: "🚑",
            NotificationType.CAPTAIN_HAUL: "©️✅",
            NotificationType.CAPTAIN_FAIL: "©️❌",
            NotificationType.CLEAN_SHEET: "🧤",
            NotificationType.CLEAN_SHEET_LOST: "💔",
            NotificationType.PENALTY_SAVE: "🥅",
            NotificationType.PENALTY_MISS: "❌",
            NotificationType.OWN_GOAL: "😱",
            NotificationType.YELLOW_CARD: "🟨",
            NotificationType.SUBSTITUTION: "🔄",
            NotificationType.BATTLE_UPDATE: "⚔️"
        }
        return icons.get(type, "📢")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'priority': self.priority.value,
            'icon': self.icon,
            'url': self.url,
            'timestamp': self.timestamp.isoformat(),
            'read': self.read
        }


class NotificationService:
    """Service for managing and sending notifications"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.websocket_connections: Dict[str, Set[WebSocket]] = {}
        self.user_preferences: Dict[str, NotificationPreferences] = {}
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
    async def initialize(self):
        """Initialize the notification service"""
        try:
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            self.is_running = True
            
            # Start notification processor
            asyncio.create_task(self._process_notifications())
            
            logger.info("Notification service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the notification service"""
        self.is_running = False
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
    
    async def register_websocket(self, user_id: str, websocket: WebSocket):
        """Register a WebSocket connection for a user"""
        if user_id not in self.websocket_connections:
            self.websocket_connections[user_id] = set()
        self.websocket_connections[user_id].add(websocket)
        logger.info(f"WebSocket registered for user {user_id}")
    
    async def unregister_websocket(self, user_id: str, websocket: WebSocket):
        """Unregister a WebSocket connection"""
        if user_id in self.websocket_connections:
            self.websocket_connections[user_id].discard(websocket)
            if not self.websocket_connections[user_id]:
                del self.websocket_connections[user_id]
        logger.info(f"WebSocket unregistered for user {user_id}")
    
    async def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Set notification preferences for a user"""
        self.user_preferences[user_id] = NotificationPreferences(preferences)
        
        # Store in Redis for persistence
        await self.redis.set(
            f"notification_prefs:{user_id}",
            json.dumps(preferences),
            expire=86400 * 30  # 30 days
        )
        
        logger.info(f"Updated preferences for user {user_id}")
    
    async def get_user_preferences(self, user_id: str) -> NotificationPreferences:
        """Get notification preferences for a user"""
        if user_id not in self.user_preferences:
            # Try to load from Redis
            stored_prefs = await self.redis.get(f"notification_prefs:{user_id}")
            if stored_prefs:
                prefs_dict = json.loads(stored_prefs)
                self.user_preferences[user_id] = NotificationPreferences(prefs_dict)
            else:
                # Return default preferences
                self.user_preferences[user_id] = NotificationPreferences()
        
        return self.user_preferences[user_id]
    
    async def create_goal_notification(
        self,
        player_name: str,
        team: str,
        points: int,
        is_captain: bool,
        user_id: str,
        opponent_id: str,
        is_user_player: bool
    ) -> Notification:
        """Create a goal notification"""
        priority = NotificationPriority.HIGH if is_captain else NotificationPriority.MEDIUM
        
        title = f"{'⚽ CAPTAIN ' if is_captain else '⚽ '}GOAL!"
        message = f"{player_name} ({team}) scores! +{points} points"
        
        if is_user_player:
            message += " for you!"
        else:
            message += " for your opponent!"
        
        return Notification(
            type=NotificationType.GOAL,
            title=title,
            message=message,
            data={
                'player_name': player_name,
                'team': team,
                'points': points,
                'is_captain': is_captain,
                'user_id': user_id,
                'opponent_id': opponent_id,
                'is_user_player': is_user_player
            },
            priority=priority
        )
    
    async def create_assist_notification(
        self,
        player_name: str,
        team: str,
        points: int,
        is_captain: bool,
        user_id: str,
        opponent_id: str,
        is_user_player: bool
    ) -> Notification:
        """Create an assist notification"""
        priority = NotificationPriority.MEDIUM
        
        title = f"{'🅰️ CAPTAIN ' if is_captain else '🅰️ '}ASSIST!"
        message = f"{player_name} ({team}) with an assist! +{points} points"
        
        if is_user_player:
            message += " for you!"
        else:
            message += " for your opponent!"
        
        return Notification(
            type=NotificationType.ASSIST,
            title=title,
            message=message,
            data={
                'player_name': player_name,
                'team': team,
                'points': points,
                'is_captain': is_captain,
                'user_id': user_id,
                'opponent_id': opponent_id,
                'is_user_player': is_user_player
            },
            priority=priority
        )
    
    async def create_bonus_change_notification(
        self,
        player_name: str,
        team: str,
        old_bonus: int,
        new_bonus: int,
        is_captain: bool,
        user_id: str,
        opponent_id: str,
        is_user_player: bool
    ) -> Notification:
        """Create a bonus points change notification"""
        change = new_bonus - old_bonus
        
        title = "🎯 Bonus Points Update"
        message = f"{player_name} ({team}): {old_bonus} → {new_bonus} bonus"
        
        if is_captain:
            message = f"CAPTAIN {message}"
        
        if change > 0:
            message += f" (+{change} points)"
        else:
            message += f" ({change} points)"
        
        return Notification(
            type=NotificationType.BONUS_CHANGE,
            title=title,
            message=message,
            data={
                'player_name': player_name,
                'team': team,
                'old_bonus': old_bonus,
                'new_bonus': new_bonus,
                'change': change,
                'is_captain': is_captain,
                'user_id': user_id,
                'opponent_id': opponent_id,
                'is_user_player': is_user_player
            },
            priority=NotificationPriority.LOW
        )
    
    async def create_red_card_notification(
        self,
        player_name: str,
        team: str,
        is_captain: bool,
        user_id: str,
        opponent_id: str,
        is_user_player: bool
    ) -> Notification:
        """Create a red card notification"""
        title = "🟥 RED CARD!"
        message = f"{player_name} ({team}) sent off!"
        
        if is_captain:
            title = "🟥 CAPTAIN RED CARD!"
            message = f"DISASTER! Captain {message}"
        
        return Notification(
            type=NotificationType.RED_CARD,
            title=title,
            message=message,
            data={
                'player_name': player_name,
                'team': team,
                'is_captain': is_captain,
                'user_id': user_id,
                'opponent_id': opponent_id,
                'is_user_player': is_user_player
            },
            priority=NotificationPriority.CRITICAL if is_captain else NotificationPriority.HIGH
        )
    
    async def create_injury_notification(
        self,
        player_name: str,
        team: str,
        is_captain: bool,
        user_id: str,
        opponent_id: str,
        is_user_player: bool
    ) -> Notification:
        """Create an injury notification"""
        title = "🚑 Injury"
        message = f"{player_name} ({team}) injured and subbed off"
        
        if is_captain:
            title = "🚑 CAPTAIN INJURED!"
        
        return Notification(
            type=NotificationType.INJURY,
            title=title,
            message=message,
            data={
                'player_name': player_name,
                'team': team,
                'is_captain': is_captain,
                'user_id': user_id,
                'opponent_id': opponent_id,
                'is_user_player': is_user_player
            },
            priority=NotificationPriority.HIGH if is_captain else NotificationPriority.MEDIUM
        )
    
    async def create_captain_haul_notification(
        self,
        player_name: str,
        team: str,
        points: int,
        user_id: str,
        opponent_id: str,
        is_user_player: bool
    ) -> Notification:
        """Create a captain haul notification (10+ points)"""
        title = "©️✅ CAPTAIN HAUL!"
        message = f"{player_name} ({team}) delivers with {points} points!"
        
        if is_user_player:
            message = f"Your captain {message}"
        else:
            message = f"Opponent's captain {message}"
        
        return Notification(
            type=NotificationType.CAPTAIN_HAUL,
            title=title,
            message=message,
            data={
                'player_name': player_name,
                'team': team,
                'points': points,
                'user_id': user_id,
                'opponent_id': opponent_id,
                'is_user_player': is_user_player
            },
            priority=NotificationPriority.HIGH
        )
    
    async def create_captain_fail_notification(
        self,
        player_name: str,
        team: str,
        points: int,
        user_id: str,
        opponent_id: str,
        is_user_player: bool
    ) -> Notification:
        """Create a captain fail notification (2 or less points)"""
        title = "©️❌ Captain Blank"
        message = f"{player_name} ({team}) disappoints with only {points} points"
        
        if is_user_player:
            message = f"Your captain {message}"
        else:
            message = f"Opponent's captain {message}"
        
        return Notification(
            type=NotificationType.CAPTAIN_FAIL,
            title=title,
            message=message,
            data={
                'player_name': player_name,
                'team': team,
                'points': points,
                'user_id': user_id,
                'opponent_id': opponent_id,
                'is_user_player': is_user_player
            },
            priority=NotificationPriority.MEDIUM
        )
    
    async def create_battle_update_notification(
        self,
        user_score: int,
        opponent_score: int,
        score_diff: int,
        user_name: str,
        opponent_name: str,
        user_id: str,
        opponent_id: str
    ) -> Notification:
        """Create a battle score update notification"""
        if score_diff > 0:
            title = "⚔️ You're winning!"
            message = f"{user_name} {user_score} - {opponent_score} {opponent_name}"
        elif score_diff < 0:
            title = "⚔️ You're losing!"
            message = f"{user_name} {user_score} - {opponent_score} {opponent_name}"
        else:
            title = "⚔️ Tied battle!"
            message = f"{user_name} {user_score} - {opponent_score} {opponent_name}"
        
        return Notification(
            type=NotificationType.BATTLE_UPDATE,
            title=title,
            message=message,
            data={
                'user_score': user_score,
                'opponent_score': opponent_score,
                'score_diff': score_diff,
                'user_name': user_name,
                'opponent_name': opponent_name,
                'user_id': user_id,
                'opponent_id': opponent_id
            },
            priority=NotificationPriority.LOW
        )
    
    async def send_notification(self, user_id: str, notification: Notification):
        """Send a notification to a user"""
        # Check user preferences
        prefs = await self.get_user_preferences(user_id)
        
        if not prefs.enabled:
            return
        
        # Check if notification type is enabled
        if notification.type not in prefs.events or not prefs.events[notification.type]:
            return
        
        # Check priority threshold
        if notification.priority.value < prefs.min_priority.value:
            return
        
        # Check quiet hours
        if prefs.quiet_hours['enabled']:
            # TODO: Implement quiet hours check
            pass
        
        # Queue the notification
        await self.notification_queue.put((user_id, notification))
    
    async def _process_notifications(self):
        """Process queued notifications"""
        while self.is_running:
            try:
                # Get notification from queue
                user_id, notification = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )
                
                # Get user preferences
                prefs = await self.get_user_preferences(user_id)
                
                # Send in-app notification
                if prefs.in_app:
                    await self._send_in_app_notification(user_id, notification)
                
                # Send browser push notification
                if prefs.browser_push:
                    await self._send_browser_push_notification(user_id, notification)
                
                # Store notification history
                await self._store_notification(user_id, notification)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
    
    async def _send_in_app_notification(self, user_id: str, notification: Notification):
        """Send in-app notification via WebSocket"""
        if user_id in self.websocket_connections:
            message = {
                'type': 'notification',
                'data': notification.to_dict()
            }
            
            # Send to all user's connections
            for websocket in self.websocket_connections[user_id].copy():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket notification: {e}")
                    # Remove dead connection
                    await self.unregister_websocket(user_id, websocket)
    
    async def _send_browser_push_notification(self, user_id: str, notification: Notification):
        """Send browser push notification"""
        # This would integrate with a service like Firebase Cloud Messaging
        # or Web Push API. For now, we'll just log it.
        logger.info(f"Would send browser push to {user_id}: {notification.title}")
        
        # TODO: Implement actual browser push notification
        # This would require:
        # 1. User's push subscription info (endpoint, keys)
        # 2. VAPID keys for authentication
        # 3. Sending the notification via Web Push Protocol
    
    async def _store_notification(self, user_id: str, notification: Notification):
        """Store notification in Redis for history"""
        key = f"notifications:{user_id}"
        
        # Store notification
        await self.redis.zadd(
            key,
            notification.timestamp.timestamp(),
            json.dumps(notification.to_dict())
        )
        
        # Keep only last 100 notifications
        await self.redis.zremrangebyrank(key, 0, -101)
        
        # Set expiry to 7 days
        await self.redis.expire(key, 604800)
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get notification history for a user"""
        key = f"notifications:{user_id}"
        
        # Get notifications from Redis (newest first)
        notifications = await self.redis.zrevrange(
            key,
            offset,
            offset + limit - 1
        )
        
        return [json.loads(n) for n in notifications]
    
    async def mark_notification_read(self, user_id: str, notification_id: str):
        """Mark a notification as read"""
        # This would update the notification in storage
        # For now, we'll just log it
        logger.info(f"Marked notification {notification_id} as read for user {user_id}")
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        # This would query unread notifications from storage
        # For now, return 0
        return 0