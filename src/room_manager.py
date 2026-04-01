"""
Room Manager - Manages all state and managers for a single room/user.

Each room has its own isolated set of managers to prevent state conflicts
between different users (e.g., user001, user002).
"""

import asyncio
import logging
from typing import Dict, Optional

from src.agent.agent_manager import AgentManager
from src.agent.prompt_manager import PromptManager
from src.agent.session_manager import ChatSessionManager
from src.api.websocket_manager import WebSocketManager
from src.message_templates.websocket_message_template import WebsocketMessageTemplate

logger = logging.getLogger(__name__)


class RoomManager:
    """Manages all state and managers for a single room/user."""

    def __init__(self, room_id: str):
        """
        Initialize a new room with isolated managers.

        Args:
            room_id: Unique identifier for this room (e.g., 'user001', 'user002')
        """
        self.room_id = room_id
        logger.info(f"Initializing RoomManager for room: {room_id}")

        # Initialize room-specific managers
        self.session_manager = ChatSessionManager()
        self.ws_manager = WebSocketManager(room_id=room_id)
        self.message_manager = WebsocketMessageTemplate()
        self.user_profile = self.message_manager.contact_param()
        self.location_data = self.message_manager.location_param()

        # Initialize prompt manager and agent executor
        self.prompt_manager = PromptManager()
        self.agent_executor = AgentManager(
            self.ws_manager,
            self.message_manager,
            self.session_manager,
            self.user_profile,
            self.prompt_manager,
        )

        logger.info(f"RoomManager initialized successfully for room: {room_id}")

    async def cleanup(self):
        """Clean up resources when room closes."""
        logger.info(f"Cleaning up RoomManager for room: {self.room_id}")
        try:
            # End session if active
            if hasattr(self.session_manager, "active_session") and self.session_manager.active_session:
                self.session_manager.end_session()

            # Disconnect websocket
            await self.ws_manager.disconnect(self.room_id)

            logger.info(f"RoomManager cleanup completed for room: {self.room_id}")
        except Exception as e:
            logger.error(f"Error during cleanup for room {self.room_id}: {e}")


# Global registry of active rooms
_rooms: Dict[str, RoomManager] = {}
_rooms_lock = asyncio.Lock()


async def get_or_create_room(room_id: str) -> RoomManager:
    """
    Get existing room or create a new one.

    Args:
        room_id: Unique identifier for the room

    Returns:
        RoomManager instance for the specified room
    """
    async with _rooms_lock:
        if room_id not in _rooms:
            logger.info(f"Creating new room: {room_id}")
            _rooms[room_id] = RoomManager(room_id)
        return _rooms[room_id]


async def remove_room(room_id: str):
    """
    Remove a room from the registry and clean it up.

    Args:
        room_id: Unique identifier for the room to remove
    """
    async with _rooms_lock:
        if room_id in _rooms:
            logger.info(f"Removing room: {room_id}")
            room = _rooms[room_id]
            await room.cleanup()
            del _rooms[room_id]
            logger.info(f"Room removed: {room_id}")
        else:
            logger.warning(f"Attempted to remove non-existent room: {room_id}")


def get_active_rooms() -> list[str]:
    """
    Get list of currently active room IDs.

    Returns:
        List of active room IDs
    """
    return list(_rooms.keys())


def get_room_count() -> int:
    """
    Get the number of currently active rooms.

    Returns:
        Count of active rooms
    """
    return len(_rooms)
