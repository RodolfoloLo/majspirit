import { http, unwrap } from "./client";
import type { RoomSummary } from "../types/api";

export async function listRooms(page = 1, size = 20, status = ""): Promise<RoomSummary[]> {
  const params: Record<string, string | number> = { page, size };
  if (status) params.status = status;

  const result = await unwrap<{ items?: RoomSummary[] } | RoomSummary[]>(
    http.get("/rooms", { params }),
  );

  if (Array.isArray(result)) return result;
  return result.items ?? [];
}

export async function getRoom(roomId: number): Promise<RoomSummary> {
  return unwrap<RoomSummary>(http.get(`/rooms/${roomId}`));
}

export async function createRoom(name: string, maxPlayers = 4): Promise<RoomSummary> {
  return unwrap<RoomSummary>(http.post("/rooms", { name, max_players: maxPlayers }));
}

export async function joinRoom(roomId: number, seat: number): Promise<RoomSummary> {
  return unwrap<RoomSummary>(http.post(`/rooms/${roomId}/join`, { seat }));
}

export async function leaveRoom(roomId: number): Promise<{ ok?: boolean }> {
  return unwrap<{ ok?: boolean }>(http.post(`/rooms/${roomId}/leave`));
}

export async function setReady(roomId: number, ready: boolean): Promise<{ ready: boolean }> {
  return unwrap<{ ready: boolean }>(http.post(`/rooms/${roomId}/ready`, { ready }));
}

export async function startRoom(roomId: number): Promise<{ started?: boolean; game_id?: number }> {
  return unwrap<{ started?: boolean; game_id?: number }>(http.post(`/rooms/${roomId}/start`));
}
