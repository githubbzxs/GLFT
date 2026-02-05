export type AuthExpiredReason = "missing" | "expired" | "unauthorized";

export const TOKEN_STORAGE_KEY = "token";
export const AUTH_EXPIRED_EVENT = "glft:auth-expired";

type JwtPayload = {
  exp?: number;
};

const decodeJwtPayload = (token: string): JwtPayload | null => {
  const payload = token.split(".")[1];
  if (!payload) {
    return null;
  }

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padding = normalized.length % 4;
    const padded = padding === 0 ? normalized : normalized + "=".repeat(4 - padding);
    return JSON.parse(atob(padded)) as JwtPayload;
  } catch {
    return null;
  }
};

export const getToken = (): string | null => localStorage.getItem(TOKEN_STORAGE_KEY);

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

export const clearToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
};

export const isTokenExpired = (token: string, skewInSeconds = 30): boolean => {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== "number") {
    return true;
  }
  const nowSeconds = Math.floor(Date.now() / 1000);
  return payload.exp <= nowSeconds + skewInSeconds;
};

export const hasValidToken = (): boolean => {
  const token = getToken();
  if (!token) {
    return false;
  }
  return !isTokenExpired(token);
};

export const notifyAuthExpired = (reason: AuthExpiredReason): void => {
  window.dispatchEvent(
    new CustomEvent<AuthExpiredReason>(AUTH_EXPIRED_EVENT, {
      detail: reason
    })
  );
};
