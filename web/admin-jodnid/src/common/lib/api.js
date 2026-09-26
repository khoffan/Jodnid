import axios from "axios";
import { config } from "../config/config";
import { auth } from "../firebase/firebase_config";

const api = axios.create({
  // ดึงค่าจาก .env หรือใส่ URL ตรงๆ (แนะนำให้ใช้ .env)
  baseURL: config.api.baseUrl,
  timeout: 10000, // ถ้าเกิน 10 วินาทีให้ตัด (Timeout)
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ขอ token จาก Firebase ทุกครั้ง: getIdToken() คืนตัวที่ cache ไว้ และ refresh ให้เองเมื่อใกล้หมดอายุ (1 ชม.)
// เดิมเก็บ token ไว้ใน sessionStorage แล้วใช้ซ้ำตลอด → ใช้ไปราว 1 ชม. ทุก call ได้ 401
api.interceptors.request.use(async (config) => {
  const currentUser = auth.currentUser;
  if (currentUser) {
    config.headers.Authorization = `Bearer ${await currentUser.getIdToken()}`;
  }
  return config;
});

// ข้อความ error ที่แสดงให้ admin เห็น: ใช้ detail/message ภาษาไทยจาก backend ก่อน
// ไม่ใช่ "Request failed with status code 403" ของ axios
export const errorMessage = (error, fallback = "เกิดข้อผิดพลาดในการเชื่อมต่อ") => {
  const data = error?.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.message === "string") return data.message;
  return fallback;
};

export default api;
