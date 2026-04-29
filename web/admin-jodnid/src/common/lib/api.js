import axios from "axios";
import { config } from "../config/config";
import { auth } from "../firebase/firebase_config";
import { getIdToken } from "firebase/auth";

const api = axios.create({
  // ดึงค่าจาก .env หรือใส่ URL ตรงๆ (แนะนำให้ใช้ .env)
  baseURL: config.api.baseUrl,
  timeout: 10000, // ถ้าเกิน 10 วินาทีให้ตัด (Timeout)
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

api.interceptors.request.use(async (config) => {
  const token = sessionStorage.getItem("token");
  if (!token) {
    const newToken = await getIdToken(auth.currentUser);
    sessionStorage.setItem("token", newToken);
    config.headers.Authorization = `Bearer ${newToken}`;
  } else {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
