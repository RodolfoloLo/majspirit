import axios from "axios";

import { generateRequestId } from "../lib/requestId";
import { getStoredToken } from "../lib/token";
import type { ApiEnvelope } from "../types/api";

const defaultBase = "/api/v1";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultBase,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

http.interceptors.request.use((config) => {
  const token = getStoredToken();
  const headers = config.headers;

  headers.set("X-Request-Id", generateRequestId());
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return config;
});

export async function unwrap<T>(promise: Promise<{ data: unknown }>): Promise<T> {
  const response = await promise;
  const payload = response.data as Partial<ApiEnvelope<T>> | T;

  if (
    payload &&
    typeof payload === "object" &&
    "code" in payload &&
    "data" in payload
  ) {
    const envelope = payload as ApiEnvelope<T>;
    if (envelope.code !== 0) {
      throw new Error(envelope.message || "业务请求失败");
    }
    return envelope.data;
  }

  return payload as T;
}
