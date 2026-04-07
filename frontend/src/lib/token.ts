const TOKEN_KEY = "majspirit_access_token";

export function getStoredToken(): string {
  return sessionStorage.getItem(TOKEN_KEY) ?? "";
}

export function setStoredToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}
