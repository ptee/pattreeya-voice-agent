import { RoomServiceClient } from 'livekit-server-sdk';
import type { ConfigManager } from './config.js';
import { getConfig } from './config.js';

export class RoomManager {
  private client: RoomServiceClient;

  constructor(config?: ConfigManager) {
    const cfg = config ?? getConfig();
    this.client = new RoomServiceClient(
      cfg.getLivekitUrl(),
      cfg.getLivekitApiKey(),
      cfg.getLivekitApiSecret(),
    );
  }

  async createPattreeyaRoom(roomNameSuffix?: string, maxParticipants: number = 10): Promise<string> {
    const roomName = roomNameSuffix
      ? `pattreeya-${roomNameSuffix}`
      : `pattreeya-${new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 15)}`;

    await this.client.createRoom({
      name: roomName,
      maxParticipants,
      emptyTimeout: 300,
    });
    return roomName;
  }

  async deletePattreeyaRoom(roomName: string): Promise<boolean> {
    await this.client.deleteRoom(roomName);
    return true;
  }

  async listPattreeyaRooms(): Promise<string[]> {
    const rooms = await this.client.listRooms();
    return rooms
      .filter((r) => r.name.startsWith('pattreeya-'))
      .map((r) => r.name);
  }

  async roomExists(roomName: string): Promise<boolean> {
    const rooms = await this.client.listRooms();
    return rooms.some((r) => r.name === roomName);
  }
}

let _roomManagerInstance: RoomManager | null = null;

export function getRoomManager(config?: ConfigManager): RoomManager {
  if (!_roomManagerInstance) {
    _roomManagerInstance = new RoomManager(config);
  }
  return _roomManagerInstance;
}
