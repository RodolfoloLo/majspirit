import { http, unwrap } from "./client";
import type { TokenResponse, UserProfile } from "../types/api";

type LoginOrRegisterPayload = {
  email: string;
  password: string;
  nickname?: string;
};

async function postWithFallback<T>(paths: string[], payload: unknown): Promise<T> {
  let lastError: unknown;
  for (const path of paths) {
    try {
      return await unwrap<T>(http.post(path, payload));
    } catch (error) {
      lastError = error;
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status !== 404) {
        throw error;
      }
    }
  }
  throw lastError ?? new Error("请求失败");
}

async function getWithFallback<T>(paths: string[]): Promise<T> {
  let lastError: unknown;
  for (const path of paths) {
    try {
      return await unwrap<T>(http.get(path));
    } catch (error) {
      lastError = error;
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status !== 404) {
        throw error;
      }
    }
  }
  throw lastError ?? new Error("请求失败");
}

export async function register(payload: LoginOrRegisterPayload): Promise<TokenResponse> {
  return postWithFallback<TokenResponse>(["/auth/register", "/register"], payload);
}

export async function login(payload: LoginOrRegisterPayload): Promise<TokenResponse> {
  return postWithFallback<TokenResponse>(["/auth/login", "/login"], payload);
}

export async function getMe(): Promise<UserProfile> {
  return getWithFallback<UserProfile>(["/auth/me", "/me"]);
}

export async function logout(): Promise<{ logged_out?: boolean }> {
  return postWithFallback<{ logged_out?: boolean }>(["/auth/logout", "/logout"], {});
}
