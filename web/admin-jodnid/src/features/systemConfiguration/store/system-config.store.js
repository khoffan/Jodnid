import { create } from "zustand";
import api from "../../../common/lib/api";

const useConfigStore = create((set, get) => ({
  configs: [],
  isLoading: false,
  error: null,

  // Action: ดึงข้อมูลจาก API
  fetchConfigs: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get("/api/administrator/all");
      set({ configs: response.data.data, isLoading: false, error: null });
    } catch (err) {
      set({ error: err, isLoading: false });
    }
  },

  createConfig: async (newConfig) => {
    set({ isLoading: true });
    try {
      await api.post("/api/administrator/config/create", newConfig);
      // หลังสร้างเสร็จ ให้ดึงข้อมูลใหม่เพื่ออัปเดตตาราง
      await get().fetchConfigs();
      set({ isLoading: false });
      return { success: true };
    } catch (err) {
      set({ isLoading: false });
      return {
        success: false,
        error: err.response?.data?.detail || "สร้างไม่สำเร็จ",
      };
    }
  },

  toggleConfig: async (key, value) => {
    try {
      await api.patch("/api/administrator/config/toggle", { key, value });
      await get().fetchConfigs();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },

  // Action: อัปเดตข้อมูล (และรอให้ Backend Clear Cache)
  updateConfig: async (key, payload) => {
    try {
      await api.post("/api/administrator/config/update", { key, ...payload });
      // หลังอัปเดต ให้ดึงข้อมูลใหม่มาทับทันทีเพื่อให้ UI ตรงกับ DB
      await get().fetchConfigs();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },
}));

export default useConfigStore;
