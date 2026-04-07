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
