import { create } from "zustand";
import api from "../lib/api";

const useTransactionStore = create((set) => ({
  transactions: [],
  summary: {},
  totalAmount: 0,
  loading: false,
  currentType: "monthly", // เก็บสถานะปัจจุบันไว้เช็คได้

  fetchDashboard: async (userId, type = "monthly") => {
    // ป้องกันการโหลดซ้ำถ้ากำลังโหลดอยู่ (Optional)
    set({ loading: true, currentType: type });

    try {
      // ส่ง type ไปเป็น Query Parameter หรือ Path Parameter ตามที่คุณออกแบบใน FastAPI
      // แบบที่ 1: ใช้ Query String (แนะนำ) -> /api/dashboard/USER_ID?type=daily
      const response = await api.get(`/api/dashboard/${userId}`, {
        params: { type: type },
      });

      // สมมติว่า Backend คืนค่าโครงสร้างเดิมที่ใช้งานอยู่
      set({
        transactions: response.data.transactions || [],
        summary: response.data.summary || {},
        totalAmount: response.data.total_amount || 0,
        loading: false,
      });
    } catch (error) {
      console.error(`Fetch ${type} dashboard error:`, error);
      // ถ้า Error ให้ล้างข้อมูลเก่าหรือจัดการตามความเหมาะสม
      set({
        loading: false,
        transactions: [],
        totalAmount: 0,
        summary: {},
      });
    }
  },

  saveBudget: async (userId, amount) => {
    set({ loading: true });
    try {
      await api.post("/api/budget/setup", {
        user_id: userId,
        amount: parseFloat(amount),
      });
      set({ loading: false });
      return { success: true };
    } catch (error) {
      console.error("Budget Setup Error:", error);
      set({ loading: false });
      return { success: false };
    }
  },

  // เพิ่มฟังก์ชันสำหรับล้างค่า (Clear Store) เวลา Logout
  clearStore: () =>
    set({ transactions: [], summary: {}, totalAmount: 0, loading: false }),
}));

export default useTransactionStore;
