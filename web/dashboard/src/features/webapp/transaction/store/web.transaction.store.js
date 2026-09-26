import { create } from "zustand";
import api from "../../../../common/lib/api";

export const WEB_PAGE_SIZE = 20;

const errorDetail = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
};

const initialState = {
  items: [],
  total: 0,
  totals: { income: 0, expense: 0 },
  loading: false,
  error: null,
};

export const useWebTransaction = create((set) => ({
  ...initialState,

  // ประวัติรายการของเดือนที่เลือก (backend คืนยอดรับ/จ่ายของทั้งเดือน ไม่ใช่แค่หน้าที่แสดง)
  fetchTransactions: async ({ month, year, categoryId, offset = 0 }) => {
    set({ loading: true, error: null });
    try {
      const res = await api.get("/api/web/transactions", {
        params: {
          month,
          year,
          category_id: categoryId || undefined,
          limit: WEB_PAGE_SIZE,
          offset,
        },
      });
      const { items, total, totals } = res.data.data;
      set({ items, total, totals, loading: false });
    } catch (error) {
      console.error("Error fetching transactions:", error);
      set({ ...initialState, error: errorDetail(error, "ไม่สามารถดึงข้อมูลได้") });
    }
  },

  createTransaction: async (transaction) => {
    try {
      const res = await api.post("/api/web/transaction/add", transaction);
      return { success: !!res.data.success };
    } catch (error) {
      console.error("Error creating transaction:", error);
      return { success: false, error: errorDetail(error, "บันทึกไม่สำเร็จ กรุณาลองใหม่อีกครั้ง") };
    }
  },

  updateTransaction: async (id, changes) => {
    try {
      await api.patch(`/api/web/transactions/${id}`, changes);
      return { success: true };
    } catch (error) {
      return { success: false, error: errorDetail(error, "แก้ไขไม่สำเร็จ กรุณาลองใหม่อีกครั้ง") };
    }
  },

  deleteTransaction: async (id) => {
    try {
      await api.delete(`/api/web/transactions/${id}`);
      return { success: true };
    } catch (error) {
      return { success: false, error: errorDetail(error, "ลบไม่สำเร็จ กรุณาลองใหม่อีกครั้ง") };
    }
  },

  // ดาวน์โหลด CSV ผ่าน axios instance เดิม (ต้องแนบ token) แล้วสร้างลิงก์ดาวน์โหลดในหน้า
  exportCsv: async ({ month, year }) => {
    try {
      const res = await api.get("/api/web/transactions/export", {
        params: { month, year },
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `jodnid-${year}-${String(month).padStart(2, "0")}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      return { success: true };
    } catch (error) {
      console.error("Error exporting transactions:", error);
      return { success: false, error: "ดาวน์โหลดไม่สำเร็จ กรุณาลองใหม่อีกครั้ง" };
    }
  },

  // ล้างข้อมูลเมื่อ logout ไม่ให้ค้างในหน่วยความจำให้คนถัดไปเห็น
  reset: () => set(initialState),
}));
