export interface ApiEnvelope<T> {
  code: number;
  message: string;
  request_id?: string;
  data: T;
}

export interface UserProfile {
  id: number;
  email: string;
  nickname: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  last_login_at?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user?: UserProfile;
}

export interface RoomSummary {
  room_id?: number;
  id?: number;
  name?: string;
  owner_id?: number;
  status?: string;
  max_players?: number;
  created_at?: string;
  players?: Array<{
    user_id: number;
    nickname?: string;
    seat: number;
    ready: boolean;
    online?: boolean;
  }>;
}

export interface HistoryItem {
  match_id: number;
  finished_at?: string;
  rank: number;
  final_score: number;
  score_delta: number;
}

export interface MatchTurn {
  action: string;
  seat: number;
  tile?: string;
  from_seat?: number;
  at: string;
}

export interface MatchRound {
  round_index: number;
  dealer_seat: number;
  initial_hands: Record<string, string[]>;
  initial_wall: string[];
  turns: MatchTurn[];
  result?: Record<string, unknown>;
}

export interface MatchRankingItem {
  seat: number;
  user_id: number;
  is_bot?: boolean;
  nickname?: string;
  final_score: number;
  score_delta: number;
  rank: number;
}

export interface MatchDetailData {
  game_id: number;
  match_id: number;
  room_id: number;
  finished_at: string;
  players: Array<{ seat: number; user_id: number }>;
  initial_scores: number[];
  final_scores: number[];
  ranking: MatchRankingItem[];
  rounds: MatchRound[];
}

export interface MatchDetailResponse {
  match_id: number;
  room_id: number;
  created_at: string;
  detail: MatchDetailData;
}

export interface GameStatePlayer {
  seat: number;
  user_id: number;
  is_bot: boolean;
  nickname: string;
  hand_count: number;
  discards: string[];
}

export interface GameState {
  game_id: number;
  match_id: number;
  round_index: number;
  dealer_seat: number;
  turn_seat: number;
  wall_remaining: number;
  status: string;
  scores: number[];
  players: GameStatePlayer[];
  my_seat: number | null;
  my_hand: string[] | null;
  pending_ron: number[];
  last_discard: { seat: number; tile: string; next_turn_seat?: number } | null;
}

export interface GameActions {
  seat: number | null;
  actions: string[];
  deadline_ms: number;
}

export interface PaginationResult<T> {
  items: T[];
  page: number;
  size: number;
  total?: number;
}

export interface WsEvent<T = unknown> {
  type: string;
  ts: string;
  request_id?: string;
  data: T;
}
