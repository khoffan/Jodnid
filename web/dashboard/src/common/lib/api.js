import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

//setup core axios export api
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("id_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// token หมดอายุ → ให้ web_auth.store เป็นคนจัดการ (LIFF SDK เรียกได้ที่ store นั้นที่เดียว)
let onUnauthorized = null;
export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler;
};

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && onUnauthorized) {
      onUnauthorized();
    }
    return Promise.reject(error);
  },
);

export default api;
