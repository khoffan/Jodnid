import axios from "axios";

const api = axios.create({
  // ดึงค่าจาก .env หรือใส่ URL ตรงๆ (แนะนำให้ใช้ .env)
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 10000, // ถ้าเกิน 10 วินาทีให้ตัด (Timeout)
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

export default api;
