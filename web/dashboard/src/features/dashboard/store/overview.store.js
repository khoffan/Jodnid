import { create } from "zustand";
import api from "../../../common/lib/api";

export const useOverviewStore = create((set) => ({
    // 1. ปรับโครงสร้างเริ่มต้นให้สอดคล้องกับ API Response
    overviewStat: {
        monthlyTotal: 0,
        dailyTotal: 0,
        dailyAverage: 0,
        budgetLimit: 0,
        categories: [], // เปลี่ยนจาก {} เป็น [] เพื่อรองรับข้อมูลชุดใหม่
    },
    loading: false,
    error: null,

    // 2. ปรับฟังก์ชัน Fetch ข้อมูล
    fetchOverviewStat: async (userId, day, month, year) => {
        set({ loading: true, error: null });
        try {
            // ส่ง parameter วัน/เดือน/ปี ไปด้วยเพื่อให้ Backend filter ข้อมูลได้แม่นยำ
            const res = await api.post(`/api/overview/stats`, {
                user_id: userId,
                day: day,
                month: month,
                year: year
            });

            if (res.data.success) {
                set({ 
                    overviewStat: res.data.data, 
                    loading: false 
                });
            } else {
                set({ error: "ไม่สามารถดึงข้อมูลได้", loading: false });
            }
        } catch (e) {
            console.error("Fetch overview stats error:", e);
            set({ 
                error: e.response?.data?.message || "เกิดข้อผิดพลาดในการเชื่อมต่อ", 
                loading: false 
            });
        }
    },

    // (Optional) ฟังก์ชันสำหรับ Reset ข้อมูล
    clearOverview: () => set({
        overviewStat: {
            monthlyTotal: 0,
            dailyTotal: 0,
            dailyAverage: 0,
            budgetLimit: 0,
            categories: [],
        }
    })
}));