const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const USER_KEY = "user";
const IS_AUTH_KEY = "isAuthenticated";
const USER_NAME_KEY = "userName";
const REMEMBER_ME_KEY = "rememberMe";

type StorageKind = "local" | "session";

function getStorage(kind: StorageKind): Storage {
  return kind === "local" ? localStorage : sessionStorage;
}

export function setRememberPreference(remember: boolean): void {
  localStorage.setItem(REMEMBER_ME_KEY, remember ? "true" : "false");
}

export function getRememberPreference(): boolean {
  return localStorage.getItem(REMEMBER_ME_KEY) === "true";
}

export function setAuthSession(params: {
  accessToken: string;
  refreshToken?: string;
  user: unknown;
  userName?: string;
  rememberMe: boolean;
}): void {
  const targetKind: StorageKind = params.rememberMe ? "local" : "session";
  const target = getStorage(targetKind);
  const other = getStorage(targetKind === "local" ? "session" : "local");

  other.removeItem(ACCESS_TOKEN_KEY);
  other.removeItem(REFRESH_TOKEN_KEY);
  other.removeItem(USER_KEY);
  other.removeItem(IS_AUTH_KEY);
  other.removeItem(USER_NAME_KEY);

  target.setItem(ACCESS_TOKEN_KEY, params.accessToken);
  if (params.refreshToken) {
    target.setItem(REFRESH_TOKEN_KEY, params.refreshToken);
  }
  target.setItem(USER_KEY, JSON.stringify(params.user));
  target.setItem(IS_AUTH_KEY, "true");
  if (params.userName) {
    target.setItem(USER_NAME_KEY, params.userName);
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshTokenWithStorage(): { token: string | null; storage: Storage } {
  const local = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (local) {
    return { token: local, storage: localStorage };
  }
  return { token: sessionStorage.getItem(REFRESH_TOKEN_KEY), storage: sessionStorage };
}

export function readUserFromStorage(): { token: string | null; user: unknown | null } {
  const token = getAccessToken();
  const userRaw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
  if (!userRaw) {
    return { token, user: null };
  }
  try {
    return { token, user: JSON.parse(userRaw) };
  } catch {
    return { token, user: null };
  }
}

export function clearAuthSession(): void {
  for (const storage of [localStorage, sessionStorage]) {
    storage.removeItem(ACCESS_TOKEN_KEY);
    storage.removeItem(REFRESH_TOKEN_KEY);
    storage.removeItem(USER_KEY);
    storage.removeItem(IS_AUTH_KEY);
    storage.removeItem(USER_NAME_KEY);
  }
}
