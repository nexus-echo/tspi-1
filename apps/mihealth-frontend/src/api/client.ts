import axios from "axios";

// Same-origin via Vite proxy (/api -> backend). Override with VITE_API_BASE if needed.
const baseURL = (import.meta as any).env?.VITE_API_BASE || "/api";

export const api = axios.create({ baseURL });

const ACCESS = "mh_access";
const REFRESH = "mh_refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS);
  },
  get refresh() {
    return localStorage.getItem(REFRESH);
  },
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS, access);
    localStorage.setItem(REFRESH, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

// Attach bearer token on every request.
api.interceptors.request.use((config) => {
  const t = tokenStore.access;
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

// On 401, try one refresh, then retry; otherwise bubble up.
let refreshing: Promise<string | null> | null = null;
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && tokenStore.refresh) {
      original._retry = true;
      if (!refreshing) {
        refreshing = api
          .post("/auth/refresh", { refresh_token: tokenStore.refresh })
          .then((res) => {
            tokenStore.set(res.data.access_token, res.data.refresh_token);
            return res.data.access_token as string;
          })
          .catch(() => {
            tokenStore.clear();
            return null;
          })
          .finally(() => {
            refreshing = null;
          });
      }
      const newToken = await refreshing;
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  }
);
