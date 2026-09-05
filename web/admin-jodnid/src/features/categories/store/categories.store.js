import { create } from "zustand";
import api from "../../../common/lib/api";

const useCategoriesStore = create((set, get) => ({
  categories: [],
  isLoading: false,
  error: null,

  fetchCategories: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get("/api/administrator/categories");
      set({ categories: response.data.data, isLoading: false, error: null });
    } catch {
      set({ error: "ไม่สามารถดึงข้อมูลได้", isLoading: false });
    }
  },

  createCategory: async (payload) => {
    try {
      const response = await api.post("/api/administrator/categories", payload);
      if (!response.data.success) {
        return { success: false, error: response.data.message ?? "สร้างไม่สำเร็จ" };
      }
      await get().fetchCategories();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },

  updateCategory: async (id, payload) => {
    try {
      const response = await api.patch(`/api/administrator/categories/${id}`, payload);
      if (!response.data.success) {
        return { success: false, error: response.data.message ?? "แก้ไขไม่สำเร็จ" };
      }
      await get().fetchCategories();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },

  deleteCategory: async (id) => {
    try {
      const response = await api.delete(`/api/administrator/categories/${id}`);
      if (!response.data.success) {
        return { success: false, error: response.data.message ?? "ลบไม่สำเร็จ" };
      }
      await get().fetchCategories();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },
}));

export default useCategoriesStore;
