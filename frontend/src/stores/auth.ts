import { defineStore } from "pinia";

import { getMe, login, register } from "../api/auth";
import { extractErrorMessage } from "../lib/error";
import { clearStoredToken, getStoredToken, setStoredToken } from "../lib/token";
import type { TokenResponse, UserProfile } from "../types/api";

interface AuthState {
  token: string;
  user: UserProfile | null;
  loading: boolean;
  initialized: boolean;
}

function pickToken(resp: TokenResponse): string {
  return resp.access_token || "";
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: "",
    user: null,
    loading: false,
    initialized: false,
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
  },
  actions: {
    async initSession() {
      if (this.initialized) return;
      this.initialized = true;

      const cached = getStoredToken();
      if (!cached) return;

      this.token = cached;
      try {
        this.user = await getMe();
      } catch {
        this.logout();
      }
    },

    async doRegister(payload: { email: string; nickname: string; password: string }) {
      this.loading = true;
      try {
        const resp = await register(payload);
        this.afterAuth(resp);
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async doLogin(payload: { email: string; password: string }) {
      this.loading = true;
      try {
        const resp = await login(payload);
        this.afterAuth(resp);
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      } finally {
        this.loading = false;
      }
    },

    async refreshMe() {
      if (!this.token) return;
      this.user = await getMe();
    },

    logout() {
      this.token = "";
      this.user = null;
      clearStoredToken();
    },

    afterAuth(resp: TokenResponse) {
      const token = pickToken(resp);
      if (!token) {
        throw new Error("后端未返回 access_token");
      }

      this.token = token;
      setStoredToken(token);

      if (resp.user) {
        this.user = resp.user;
      } else {
        void this.refreshMe();
      }
    },
  },
});
