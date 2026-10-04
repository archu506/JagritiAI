import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("jagriti_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the token is invalid/expired, clear it and let the app fall back to
// anonymous/citizen flows rather than getting stuck in a broken auth state.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("jagriti_token");
      localStorage.removeItem("jagriti_user");
    }
    return Promise.reject(err);
  }
);
