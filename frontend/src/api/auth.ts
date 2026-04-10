import { http, unwrap } from "./client";
import type { TokenResponse, UserProfile } from "../types/api";

//type是
type LoginOrRegisterPayload = {
  email: string;
  password: string;
  nickname?: string;
};

//这两个async function是用来兼容重试的函数，因为后端可能同时提供了/auth/login和/login两种接口，我们希望在其中一个接口返回404时自动尝试另一个接口，以提高兼容性和用户体验。
//<T>是泛型，表示函数的返回类型可以根据调用时指定的类型参数来确定，这样函数就可以适用于不同的返回类型，而不需要重复编写相似的代码。
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

//这四个export async function是具体的用户接口函数
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
