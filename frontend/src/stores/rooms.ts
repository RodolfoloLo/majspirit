import { defineStore } from "pinia";

import {
  createRoom,
  getRoom,
  joinRoom,
  leaveRoom,
  listRooms,
  setReady,
  startRoom,
} from "../api/rooms";
import { extractErrorMessage } from "../lib/error";
import type { RoomSummary } from "../types/api";

interface RoomState {
  rooms: RoomSummary[];
  currentRoom: RoomSummary | null;
  loading: boolean;
}

export const useRoomStore = defineStore("room", {
  state: (): RoomState => ({
    rooms: [],
    currentRoom: null,
    loading: false,
  }),
  actions: {
    async loadRooms() {
      this.loading = true;
      try {
        this.rooms = await listRooms();
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async loadRoom(roomId: number) {
      this.loading = true;
      try {
        this.currentRoom = await getRoom(roomId);
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async createAndEnter(name: string, maxPlayers = 4) {
      this.loading = true;
      try {
        this.currentRoom = await createRoom(name, maxPlayers);
        return this.currentRoom;
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async join(roomId: number, seat: number) {
      this.loading = true;
      try {
        await joinRoom(roomId, seat);
        await this.loadRoom(roomId);
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async leave(roomId: number) {
      this.loading = true;
      try {
        await leaveRoom(roomId);
        this.currentRoom = null;
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async ready(roomId: number, readyFlag: boolean) {
      this.loading = true;
      try {
        await setReady(roomId, readyFlag);
        await this.loadRoom(roomId);
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async start(roomId: number) {
      this.loading = true;
      try {
        return await startRoom(roomId);
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },
  },
});
