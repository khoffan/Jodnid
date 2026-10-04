import { create } from "zustand";
import api, { errorMessage } from "../../../common/lib/api";

const PAGE_SIZE = 50;

const useUsersStore = create((set, get) => ({
  users: [],
  total: 0,
  offset: 0,
  search: "",
  isLoading: false,
  error: null,

  fetchUsers: async (offset = 0) => {
    set({ isLoading: true });
    try {
      const response = await api.get("/api/administrator/users", {
        params: { search: get().search || undefined, limit: PAGE_SIZE, offset },
      });
      const { items, total } = response.data.data;
      set({ users: items, total, offset, isLoading: false, error: null });
    } catch {
      set({ error: "ไม่สามารถดึงข้อมูลได้", isLoading: false });
    }
  },

  setSearch: (search) => {
    set({ search });
    get().fetchUsers(0);
  },

  toggleBypassMode: async (lineUserId, enabled) => {
    try {
      const response = await api.patch("/api/administrator/users/bypass-mode", {
        line_user_id: lineUserId,
        enabled,
      });
      if (!response.data.success) {
        return { success: false, error: response.data.message ?? "ไม่สำเร็จ" };
      }
      await get().fetchUsers(get().offset);
      return { success: true };
    } catch (err) {
      return { success: false, error: errorMessage(err, "ไม่สำเร็จ") };
    }
  },

  // ซ่อม UserBudget.current_spent เดือนนี้ของผู้ใช้ให้ตรงกับรายการจริง
  syncBudgets: async (lineUserId) => {
    try {
      const response = await api.post("/api/administrator/users/sync-budgets", {
        line_user_id: lineUserId,
      });
      if (!response.data.success) {
        return { success: false, error: response.data.message ?? "ไม่สำเร็จ" };
      }
      return { success: true, updated: response.data.data.updated };
    } catch (err) {
      return { success: false, error: errorMessage(err, "ไม่สำเร็จ") };
    }
  },

  nextPage: () => {
    const { offset, total } = get();
    if (offset + PAGE_SIZE < total) get().fetchUsers(offset + PAGE_SIZE);
  },

  prevPage: () => {
    const { offset } = get();
    if (offset > 0) get().fetchUsers(Math.max(0, offset - PAGE_SIZE));
  },
}));

export { PAGE_SIZE };
export default useUsersStore;
