import { http, unwrap } from "./client";
import type { GameActions, GameState } from "../types/api";

export async function getGameState(gameId: number): Promise<GameState> {
  return unwrap<GameState>(http.get(`/games/${gameId}/state`));
}

export async function getGameActions(gameId: number): Promise<GameActions> {
  return unwrap<GameActions>(http.get(`/games/${gameId}/actions/available`));
}

export async function discardTile(gameId: number, tile: string): Promise<Record<string, unknown>> {
  return unwrap<Record<string, unknown>>(http.post(`/games/${gameId}/actions/discard`, { tile }));
}

export async function tsumo(gameId: number): Promise<Record<string, unknown>> {
  return unwrap<Record<string, unknown>>(http.post(`/games/${gameId}/actions/tsumo`));
}

export async function ron(gameId: number): Promise<Record<string, unknown>> {
  return unwrap<Record<string, unknown>>(http.post(`/games/${gameId}/actions/ron`));
}

export async function peng(gameId: number): Promise<Record<string, unknown>> {
  return unwrap<Record<string, unknown>>(http.post(`/games/${gameId}/actions/peng`));
}
