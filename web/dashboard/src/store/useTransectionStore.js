import { create } from "zustand";
import api from "../lib/api";

const useTransactionStore = create((set) => ({
  transactions: [],
  summary: {},
  totalAmount: 0,
  loading: false,
  currentType: "monthly", // เก็บสถานะปัจจุบันไว้เช็คได้

  // เพิ่ม State สำหรับ Overview Stat โดยเฉพาะ
  overviewStat: {
    monthlyTotal: 0,
    dailyTotal: 0,
    dailyAverage: 0,
    percentChange: 0,
    budgetLimit: 0,
    categories: {},
  },

  fetchDashboard: async (userId, type = "monthly", month, year) => {
    // ป้องกันการโหลดซ้ำถ้ากำลังโหลดอยู่ (Optional)
    set({ loading: true, currentType: type });

    try {
      const now = new Date();
      const queryParams = {
        type: type,
        month: month || now.getMonth() + 1, // ถ้าไม่ส่ง month มาให้ใช้เดือนปัจจุบัน
        year: year || now.getFullYear(), // ถ้าไม่ส่ง year มาให้ใช้ปีปัจจุบัน
      };
      // ส่ง type ไปเป็น Query Parameter หรือ Path Parameter ตามที่คุณออกแบบใน FastAPI
      // แบบที่ 1: ใช้ Query String (แนะนำ) -> /api/dashboard/USER_ID?type=daily
      const response = await api.get(`/api/dashboard/${userId}`, {
        params: queryParams,
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

  fetchOverviewStat: async (userId) => {
    set({ loading: true });
    try {
      const res = await api.post(`/api/overview/stats`, {
        user_id: userId,
      });
      if (res.data.success) {
        set({ overviewStat: res.data.data, loading: false });
      }
    } catch (e) {
      console.error("Fetch overview stats error:", e);
      set({ loading: false });
    }
  },

  saveBudget: async (userId, amount) => {
    set({ loading: true });
    try {
      const res = await api.post("/api/budget/setup", {
        user_id: userId,
        amount: parseFloat(amount),
      });
      console.log("API Response for Budget Setup:", res.data);
      if (!res.data.success) {
        return {
          success: false,
          message: res.data.message || "Failed to set up budget",
        };
      }
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
