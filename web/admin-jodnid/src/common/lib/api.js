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

api.interceptors.request.use(
  async (config) => {
    const currentUser = auth.currentUser;
    if (currentUser) {
      // ดึง Token ล่าสุด หากหมดอายุ Firebase SDK จะจัดการทำ Refresh token ให้ทันที
      // การใส่พารามิเตอร์ true ลงไปใน getIdToken(true) จะเป็นการบังคับ Force Refresh (หากต้องการชัวร์ๆ)
      // แต่ปกติเรียกธรรมดา getIdToken() ก็เพียงพอแล้วครับ มันฉลาดพอจะสลับใบเมื่อใบเก่าใกล้หมดอายุ
      const token = await currentUser.getIdToken();
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      // กรณีเพิ่งเปิดแอปและ Firebase ยังโหลดไม่เสร็จ ให้ดึงจาก Storage ประทังไปก่อน
      const token = sessionStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

export default api;
