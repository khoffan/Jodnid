import { create } from "zustand";
import api from "../../../common/lib/api";

const useLogsStore = create((set, get) => ({
  logs: [],
  total: 0,
  page: 1,
  per_page: 20,
  isLoading: false,
  currentLog: null,

  fetchLogs: async (opts = {}) => {
    const page = opts.page || get().page || 1;
    const per_page = opts.per_page || get().per_page || 20;
    set({ isLoading: true });
    try {
      const params = { page, per_page, ...(opts.filters || {}) };
      const res = await api.get("/api/administrator/logs", { params });
      set({
        logs: res.data.data || [],
        total: res.data.total || 0,
        page,
        per_page,
        isLoading: false,
      });
    } catch (err) {
      set({ isLoading: false });
    }
  },

  fetchLogById: async (id) => {
    set({ isLoading: true });
    try {
      const res = await api.get(`/api/administrator/logs/${id}`);
      set({ currentLog: res.data.data || null, isLoading: false });
      return res.data.data;
    } catch (err) {
      set({ isLoading: false });
      return null;
    }
  },
}));

export default useLogsStore;
