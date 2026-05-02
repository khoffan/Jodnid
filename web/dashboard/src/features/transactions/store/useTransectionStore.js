import { create } from "zustand";
import api from "../../../common/lib/api";

const useTransactionStore = create((set) => ({
  dashboardData: null,
  transactions: [],
  summary: {},
  totalAmount: 0,
  loading: false,
  currentType: "monthly",

  fetchDashboard: async (userId, type = "monthly", day, month, year) => {
    set({ loading: true, currentType: type });

    try {
      const now = new Date();
      const queryParams = {
        type: type,
        day: day || now.getDate(),
        month: month || now.getMonth() + 1,
        year: year || now.getFullYear(),
      };

      const response = await api.get(
        `/api/dashboard/${userId}`,
        {
          params: queryParams,
        },
        {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("id_token")}`,
          },
        },
      );

      // ตรวจสอบว่า API คืนค่า success หรือไม่ (ถ้ามี)
      // หรือตรวจสอบโครงสร้างข้อมูลที่ได้รับ
      const data = response.data;

      set({
        dashboardData: data, // เก็บก้อนใหญ่ไว้เช็คใน UI
        transactions: data.transactions || [],
        summary: data.summary || {},
        totalAmount: data.total_amount || 0,
        loading: false,
      });
    } catch (error) {
      console.error(`Fetch ${type} dashboard error:`, error);
      set({
        loading: false,
        dashboardData: null, // เคลียร์ข้อมูลเมื่อเกิด error
        transactions: [],
        totalAmount: 0,
        summary: {},
      });
    }
  },

  saveBudget: async (userId, categoryId, amount) => {
    set({ loading: true });
    try {
      // ส่งทั้ง user_id, category_id และ amount ไปยัง Backend
      const res = await api.post("/api/budget/setup", {
        user_id: userId,
        category_id: parseInt(categoryId), // มั่นใจว่าเป็น Integer ตามที่ SQLModel ต้องการ
        amount: parseFloat(amount),
      });

      console.log(`API Response for Budget Setup (${categoryId}):`, res.data);

      if (!res.data.success) {
        set({ loading: false }); // อย่าลืมปิด loading กรณีไม่สำเร็จ
        return {
          success: false,
          message: res.data.message || "Failed to set up budget",
        };
      }

      set({ loading: false });
      return { success: true };
    } catch (error) {
      console.error(`Budget Setup Error for Category ${categoryId}:`, error);
      set({ loading: false });
      return {
        success: false,
        message: error.response?.data?.detail || "Internal Server Error",
      };
    }
  },

  // เพิ่มฟังก์ชันสำหรับล้างค่า (Clear Store) เวลา Logout
  clearStore: () =>
    set({ transactions: [], summary: {}, totalAmount: 0, loading: false }),
}));

export default useTransactionStore;
