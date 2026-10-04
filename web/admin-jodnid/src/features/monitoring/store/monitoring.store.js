import { create } from "zustand";
import api from "../../../common/lib/api";

const PAGE_SIZE = 50;

const useMonitoringStore = create((set, get) => ({
  metrics: null,
  metricsError: null,

  logs: [],
  logTotal: 0,
  logOffset: 0,
  logModules: [],
  filters: { level: "", module: "", search: "" },
  isLoading: false,
  error: null,

  fetchMetrics: async (days = 7) => {
    try {
      const response = await api.get("/api/administrator/metrics", { params: { days } });
      set({ metrics: response.data.data, metricsError: null });
    } catch {
      set({ metricsError: "ไม่สามารถดึงข้อมูลสรุปได้", metrics: null });
    }
  },

  setFilter: (patch) => {
    set({ filters: { ...get().filters, ...patch } });
    get().fetchLogs(0);
  },

  fetchLogs: async (offset = 0) => {
    set({ isLoading: true });
    const { level, module, search } = get().filters;
    try {
      const response = await api.get("/api/administrator/logs", {
        params: {
          level: level || undefined,
          module: module || undefined,
          search: search || undefined,
          limit: PAGE_SIZE,
          offset,
        },
      });
      const { items, total } = response.data.data;
      set({
        logs: items,
        logTotal: total,
        logOffset: offset,
        logModules: response.data.modules ?? [],
        isLoading: false,
        error: null,
      });
    } catch {
      set({ error: "ไม่สามารถดึงข้อมูลได้", isLoading: false });
    }
  },

  nextPage: () => {
    const { logOffset, logTotal } = get();
    if (logOffset + PAGE_SIZE < logTotal) get().fetchLogs(logOffset + PAGE_SIZE);
  },

  prevPage: () => {
    const { logOffset } = get();
    if (logOffset > 0) get().fetchLogs(Math.max(0, logOffset - PAGE_SIZE));
  },
}));

export { PAGE_SIZE };
export default useMonitoringStore;
