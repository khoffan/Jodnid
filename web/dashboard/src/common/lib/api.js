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

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response.status === 401) {
      sessionStorage.removeItem("id_token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  },
);

export default api;
