import { create } from "zustand";
import api, { errorMessage } from "../../../common/lib/api";

// endpoint config ตอบ 200 พร้อม {success: false, message} เมื่อทำไม่สำเร็จ (ชื่อซ้ำ, ค่าผิดชนิด ฯลฯ)
// ต้องเช็ค response ด้วย ไม่ใช่แค่ดัก exception
const failed = (response, fallback) =>
  response.data?.success === false
    ? { success: false, error: response.data.message || fallback }
    : null;

const useConfigStore = create((set, get) => ({
  configs: [],
  status: null,
  isLoading: false,
  error: null,

  // Action: ดึงข้อมูลจาก API
  fetchConfigs: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get("/api/administrator/all");
      set({ configs: response.data.data, isLoading: false, error: null });
    } catch (err) {
      set({ error: errorMessage(err, "ไม่สามารถดึงข้อมูลได้"), isLoading: false });
    }
  },

  // Action: ดึงสถานะจริงของระบบมาแสดงบนการ์ดด้านบน
  fetchStatus: async () => {
    try {
      const response = await api.get("/api/administrator/status");
      set({ status: response.data.data });
    } catch {
      set({ status: null });
    }
  },

  refreshCache: async () => {
    try {
      await api.post("/api/administrator/config/refresh-cache");
      await get().fetchConfigs();
      await get().fetchStatus();
      return { success: true };
    } catch (err) {
      return { success: false, error: errorMessage(err, "ล้างแคชไม่สำเร็จ") };
    }
  },

  createConfig: async (newConfig) => {
    set({ isLoading: true });
    try {
      const response = await api.post("/api/administrator/config/create", newConfig);
      const failure = failed(response, "สร้างไม่สำเร็จ");
      if (failure) {
        set({ isLoading: false });
        return failure;
      }
      // หลังสร้างเสร็จ ให้ดึงข้อมูลใหม่เพื่ออัปเดตตาราง
      await get().fetchConfigs();
      set({ isLoading: false });
      return { success: true };
    } catch (err) {
      set({ isLoading: false });
      return { success: false, error: errorMessage(err, "สร้างไม่สำเร็จ") };
    }
  },

  toggleConfig: async (key, value) => {
    try {
      const response = await api.patch("/api/administrator/config/toggle", { key, value });
      const failure = failed(response, "อัปเดตไม่สำเร็จ");
      if (failure) return failure;
      await get().fetchConfigs();
      return { success: true };
    } catch (err) {
      return { success: false, error: errorMessage(err, "อัปเดตไม่สำเร็จ") };
    }
  },

  // Action: อัปเดตข้อมูล (และรอให้ Backend Clear Cache)
  updateConfig: async (key, payload) => {
    try {
      const response = await api.patch("/api/administrator/config/update", { key, ...payload });
      const failure = failed(response, "บันทึกไม่สำเร็จ");
      if (failure) return failure;
      // หลังอัปเดต ให้ดึงข้อมูลใหม่มาทับทันทีเพื่อให้ UI ตรงกับ DB
      await get().fetchConfigs();
      return { success: true };
    } catch (err) {
      return { success: false, error: errorMessage(err, "บันทึกไม่สำเร็จ") };
    }
  },
}));

export default useConfigStore;
