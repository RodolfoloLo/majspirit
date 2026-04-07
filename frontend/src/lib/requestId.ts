export function generateRequestId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  const rand = Math.random().toString(16).slice(2);
  const now = Date.now().toString(16);
  return `${now}-${rand}`;
}
