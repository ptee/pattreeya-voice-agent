# Room Management Guide

## Overview

The Voice Agent now includes comprehensive room management functionality to create and manage LiveKit rooms with the "pattreeya" prefix. This enables automated room creation for voice conversations.

## RoomManager Module

The `src/room_manager.py` module provides the core room management functionality via the `RoomManager` class.

### Features

- **Create Rooms**: Create new LiveKit rooms with "pattreeya-" prefix
- **List Rooms**: List all active pattreeya rooms
- **Delete Rooms**: Remove pattreeya rooms when no longer needed
- **Room Exists Check**: Verify if a room exists before operations

### RoomManager API

#### Initialization

```python
from room_manager import RoomManager, get_room_manager

# Create instance (singleton pattern)
room_manager = get_room_manager()

# Or with custom config
from config import ConfigManager
room_manager = RoomManager(config=ConfigManager())
```

#### Create a Room

```python
import asyncio

async def create_room():
    room_manager = get_room_manager()

    # With auto-generated timestamp suffix
    room_name = await room_manager.create_pattreeya_room()
    # Returns: "pattreeya-20250120-143025"

    # With custom suffix
    room_name = await room_manager.create_pattreeya_room(
        room_name_suffix="interview-alice"
    )
    # Returns: "pattreeya-interview-alice"

asyncio.run(create_room())
```

#### List Active Rooms

```python
async def list_rooms():
    room_manager = get_room_manager()
    rooms = await room_manager.list_pattreeya_rooms()
    # Returns: ["pattreeya-20250120-143025", "pattreeya-interview-alice"]

asyncio.run(list_rooms())
```

#### Delete a Room

```python
async def delete_room():
    room_manager = get_room_manager()
    success = await room_manager.delete_pattreeya_room("pattreeya-20250120-143025")
    # Returns: True if successful

asyncio.run(delete_room())
```

#### Check Room Existence

```python
async def check_room():
    room_manager = get_room_manager()
    exists = await room_manager.room_exists("pattreeya-interview-alice")
    # Returns: True or False

asyncio.run(check_room())
```

## Agent Function Tools

The Assistant agent includes 3 new function tools for room management:

### 1. create_pattreeya_room

Creates a new LiveKit room with "pattreeya-" prefix.

**Usage in conversations:**
```
User: "Create a new room for a meeting"
Agent: "I'll create a new room for you. [calls create_pattreeya_room tool]"
Agent: "Successfully created room: pattreeya-20250120-143025. You can now connect to this room for a voice conversation with Pattreeya."
```

**Parameters:**
- `room_name_suffix` (optional): Custom suffix for the room name
  - If not provided, timestamp is used (e.g., "20250120-143025")
  - If provided, becomes: "pattreeya-{suffix}"

### 2. list_pattreeya_rooms

Lists all active pattreeya rooms.

**Usage in conversations:**
```
User: "What rooms are available?"
Agent: "I'll check what rooms are currently active. [calls list_pattreeya_rooms tool]"
Agent: "Currently active pattreeya rooms: pattreeya-20250120-143025, pattreeya-interview-alice"
```

**Returns:** List of active room names, or message if no rooms exist.

### 3. delete_pattreeya_room

Deletes a specific pattreeya room.

**Usage in conversations:**
```
User: "Delete the interview-alice room"
Agent: "I'll delete that room for you. [calls delete_pattreeya_room tool]"
Agent: "Successfully deleted room: pattreeya-interview-alice"
```

**Parameters:**
- `room_name` (required): Name of the room to delete

## Room Naming Convention

All rooms created have the "pattreeya-" prefix:

- **Timestamp format**: `pattreeya-{YYYYMMDD-HHMMSS}`
  - Example: `pattreeya-20250120-143025`
  - Used when no suffix is provided

- **Custom suffix format**: `pattreeya-{custom-suffix}`
  - Example: `pattreeya-interview-alice`
  - Used when custom suffix is provided

## Auto-Cleanup

Rooms are configured to auto-delete after 5 minutes of inactivity (empty_timeout=300 seconds). This helps manage resources automatically.

## Integration with Voice Agent

The room management tools are integrated into the Agent class and can be called by the LLM during conversations:

```python
from agent import Assistant

assistant = Assistant()
# Assistant has access to room management tools via:
# - create_pattreeya_room()
# - list_pattreeya_rooms()
# - delete_pattreeya_room()
```

## Configuration

Room management requires the following environment variables (set in `.env.local`):

```bash
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

These are used by RoomManager to connect to your LiveKit instance via the LiveKitAPI.

## Error Handling

All room management operations include comprehensive error handling:

```python
from room_manager import RoomManager

async def safe_create_room():
    try:
        room_manager = RoomManager()
        room_name = await room_manager.create_pattreeya_room()
        return room_name
    except Exception as e:
        print(f"Failed to create room: {e}")
        # Handle error appropriately
```

Errors are logged with `logger.error()` for debugging.

## Testing

The room management functionality is tested with unit tests:

```bash
# Run all tests
uv run pytest tests/test_agent.py -v

# Run specific test
uv run pytest tests/test_agent.py::test_offers_assistance -v
```

## Examples

### Example 1: Create a Meeting Room

```python
import asyncio
from room_manager import get_room_manager

async def main():
    rm = get_room_manager()

    # Create a meeting room
    room_name = await rm.create_pattreeya_room(
        room_name_suffix="standup-meeting"
    )
    print(f"Meeting room created: {room_name}")

asyncio.run(main())
```

### Example 2: List and Manage Rooms

```python
import asyncio
from room_manager import get_room_manager

async def main():
    rm = get_room_manager()

    # List all rooms
    rooms = await rm.list_pattreeya_rooms()
    print(f"Active rooms: {rooms}")

    # Delete old rooms
    for room in rooms:
        if "old-" in room:
            await rm.delete_pattreeya_room(room)
            print(f"Deleted: {room}")

asyncio.run(main())
```

### Example 3: Room Monitoring

```python
import asyncio
from room_manager import get_room_manager

async def main():
    rm = get_room_manager()

    # Create a room
    room_name = await rm.create_pattreeya_room(
        room_name_suffix="test-room"
    )
    print(f"Created: {room_name}")

    # Check if it exists
    exists = await rm.room_exists(room_name)
    print(f"Room exists: {exists}")

    # Delete it
    success = await rm.delete_pattreeya_room(room_name)
    print(f"Deleted: {success}")

asyncio.run(main())
```

## Async/Await Pattern

All RoomManager methods are async and must be called with `await`:

```python
# ✓ Correct
room_name = await room_manager.create_pattreeya_room()

# ✗ Incorrect
room_name = room_manager.create_pattreeya_room()  # Will return coroutine, not room name
```

## Performance Considerations

- Room creation/deletion is fast (typically <100ms)
- Listing rooms is O(n) where n is total rooms in LiveKit server
- Room existence checks are O(n) for all rooms
- No caching is performed; each call queries LiveKit directly

For high-volume operations, consider caching the room list.

## Troubleshooting

### "Failed to initialize RoomManager"
- Check that `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` are set
- Verify LiveKit server is accessible at the provided URL

### "Failed to create room"
- Ensure API credentials are correct
- Check LiveKit server logs for permission issues
- Verify room name doesn't already exist

### "Room not found"
- Room may have been auto-deleted after 5 minutes of inactivity
- List rooms to see currently active rooms

## Related Files

- **src/room_manager.py**: Core RoomManager implementation
- **src/agent.py**: Agent integration with room tools
- **tests/test_agent.py**: Tests for room functionality
- **.env.example**: Environment configuration template

## Future Enhancements

Potential improvements for room management:

1. **Room Metadata**: Add custom metadata to rooms (user info, purpose, etc.)
2. **Room Limits**: Set per-room participant limits and timeouts
3. **Room Monitoring**: Track room activity and participant info
4. **Bulk Operations**: Create/delete multiple rooms in batch
5. **Room History**: Log room creation/deletion for auditing
6. **Room Scheduling**: Schedule rooms to be created/deleted at specific times

