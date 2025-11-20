"""
Room management for LiveKit Agent
Handles creation and management of rooms with 'pattreeya' prefix
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from livekit.api import LiveKitAPI
from config import get_config

logger = logging.getLogger("room_manager")


class RoomManager:
    """Manages LiveKit rooms for the voice agent"""

    def __init__(self, config=None):
        """Initialize room manager with LiveKit credentials"""
        self.config = config or get_config()
        try:
            self.api = LiveKitAPI(
                url=self.config.get_livekit_url(),
                api_key=self.config.get_livekit_api_key(),
                api_secret=self.config.get_livekit_api_secret(),
            )
            logger.info("RoomManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RoomManager: {e}")
            raise

    async def create_pattreeya_room(
        self,
        room_name_suffix: Optional[str] = None,
        max_participants: int = 10,
    ) -> str:
        """
        Create a new LiveKit room with 'pattreeya-' prefix

        Args:
            room_name_suffix: Optional suffix for the room name.
                            If None, uses timestamp (e.g., 'pattreeya-20250120-143025')
            max_participants: Maximum participants allowed in the room (default: 10)

        Returns:
            str: The created room name

        Raises:
            Exception: If room creation fails
        """
        try:
            # Generate room name
            if room_name_suffix:
                room_name = f"pattreeya-{room_name_suffix}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                room_name = f"pattreeya-{timestamp}"

            # Create the room via API
            from livekit.api.room_service import CreateRoomRequest

            await self.api.room.create_room(
                req=CreateRoomRequest(
                    room=room_name,
                    max_participants=max_participants,
                    empty_timeout=300,  # Auto-delete after 5 minutes of inactivity
                )
            )

            logger.info(
                f"Created room '{room_name}' with max {max_participants} participants"
            )
            return room_name

        except Exception as e:
            logger.error(f"Failed to create room: {e}")
            raise

    async def delete_pattreeya_room(self, room_name: str) -> bool:
        """
        Delete a pattreeya room

        Args:
            room_name: Name of the room to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            Exception: If deletion fails
        """
        try:
            if not room_name.startswith("pattreeya-"):
                logger.warning(f"Room '{room_name}' does not start with 'pattreeya-'")

            from livekit.api.room_service import DeleteRoomRequest

            await self.api.room.delete_room(req=DeleteRoomRequest(room=room_name))
            logger.info(f"Deleted room '{room_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete room '{room_name}': {e}")
            raise

    async def list_pattreeya_rooms(self) -> list[str]:
        """
        List all active pattreeya rooms

        Returns:
            list: Names of all active pattreeya rooms
        """
        try:
            from livekit.api.room_service import ListRoomsRequest

            response = await self.api.room.list_rooms(req=ListRoomsRequest())
            pattreeya_rooms = [
                room.name
                for room in response.rooms
                if room.name.startswith("pattreeya-")
            ]
            logger.info(f"Found {len(pattreeya_rooms)} pattreeya rooms")
            return pattreeya_rooms

        except Exception as e:
            logger.error(f"Failed to list rooms: {e}")
            return []

    async def room_exists(self, room_name: str) -> bool:
        """
        Check if a room exists

        Args:
            room_name: Name of the room to check

        Returns:
            bool: True if room exists, False otherwise
        """
        try:
            from livekit.api.room_service import ListRoomsRequest

            response = await self.api.room.list_rooms(req=ListRoomsRequest())
            return any(room.name == room_name for room in response.rooms)

        except Exception as e:
            logger.error(f"Failed to check if room exists: {e}")
            return False


# Global singleton instance
_room_manager_instance: Optional[RoomManager] = None


def get_room_manager(config=None) -> RoomManager:
    """Get or create the global RoomManager instance"""
    global _room_manager_instance
    if _room_manager_instance is None:
        _room_manager_instance = RoomManager(config)
    return _room_manager_instance


if __name__ == "__main__":
    # Simple test
    async def test_room_manager():
        try:
            logging.basicConfig(level=logging.INFO)
            rm = get_room_manager()
            print("✓ RoomManager initialized successfully")

            # Create a test room
            room_name = await rm.create_pattreeya_room(room_name_suffix="test")
            print(f"✓ Created room: {room_name}")

            # List rooms
            rooms = await rm.list_pattreeya_rooms()
            print(f"✓ Active pattreeya rooms: {rooms}")

            # Check if room exists
            exists = await rm.room_exists(room_name)
            print(f"✓ Room exists: {exists}")

        except Exception as e:
            print(f"✗ Error: {e}")

    asyncio.run(test_room_manager())
