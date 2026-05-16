import { create } from "zustand";
import liff from "@line/liff";
import api from "../../../../common/lib/api";

const testMode = import.meta.env.VITE_TEST_MODE;

export const useWebAuthStore = create((set) => ({
  isAuth: false,
  isWebApp: false,
  user: null,
  userId: null,
  error: null,
  loading: false,

  setLogin: (user) => {
    set({ isAuth: true, user, error: null });
  },
  // ฟังก์ชัน Initialize ระบบ
  initApp: async (navigate) => {
    set({ loading: true, error: null });

    const urlParams = new URLSearchParams(window.location.search);
    const isWebApp = urlParams.get("webapp") === "true" || !liff.isInClient();
    console.log("Initializing app - isWebApp:", isWebApp, "LIFF Context:", !liff.isInClient());
    // 🔹 กรณีเปิดผ่าน Web Browser / Desktop
    if (isWebApp) {
      const user = sessionStorage.getItem("user_info");
      if (!user) {
        set({
          isWebApp: true,
          error: "กรุณาเข้าสู่ระบบผ่าน LINE ก่อนใช้งาน",
          loading: false,
        });
        return;
      }
      set({
        isWebApp: true,
        user: user ? JSON.parse(user) : null,
        isAuth: true,
        loading: false,
      });
      return;
    }

    // 🔹 กรณีเปิดผ่าน LINE LIFF Client

    let liffId = testMode
      ? import.meta.env.VITE_LINE_LIFF_ID_TEST
      : import.meta.env.VITE_LINE_LIFF_ID;

    if (import.meta.env.VITE_ENV === "production") {
      liffId = import.meta.env.VITE_LINE_LIFF_ID;
    } else if (!liffId) {
      console.error("LIFF ID is not defined in environment variables");
      set({
        error: "เกิดข้อผิดพลาด: ไม่พบ LIFF ID กรุณาตรวจสอบไฟล์ .env",
        loading: false,
      });
      return;
    }

    try {
      await liff.init({ liffId });

      if (liff.isLoggedIn()) {
        const context = liff.getContext();
        const idToken = liff.getIDToken();
        sessionStorage.setItem("id_token", idToken);

        await api.post("/api/user", {
          id_token: idToken,
        });

        set({
          userId: context.userId,
          isAuth: true,
          loading: false,
        });

        const targetPath = urlParams.get("path");
        if (targetPath) {
          navigate(targetPath);
        }
      } else {
        liff.login();
        // ยังไม่ล็อกอิน ให้แสดงปุ่มให้ผู้ใช้กด
        set({ loading: false, isAuth: false });
      }
    } catch (error) {
      console.error("LIFF Initialization failed:", error);
      set({ error: error.message, loading: false });
    }
  },

  login: async () => {
    set({ loading: true, error: null });

    // 🔹 ตรวจสอบว่าใช้งานผ่าน LIFF หรือไม่
    if (!liff.isInClient()) {
      // 🌐 กรณีใช้ผ่าน Web Browser ทั่วไป ให้ Redirect ไปยังหน้า LINE Login (Web)
      const clientId = testMode
        ? import.meta.env.VITE_LINE_CHANNEL_ID_TEST
        : import.meta.env.VITE_LINE_CHANNEL_ID;

      const redirectUri = window.location.origin + "/login/callback";
      const state = Math.random().toString(36).substring(7);

      const lineLoginUrl = `https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(
        redirectUri,
      )}&state=${state}&scope=profile%20openid`;
      window.location.href = lineLoginUrl;
      return;
    }

    // 📱 กรณีใช้งานในแอป LINE (LIFF)
    if (!liff.isLoggedIn()) {
      liff.login();
    }
  },

  logout: async () => {
    if (!liff.isInClient()) {
      sessionStorage.removeItem("id_token");
      sessionStorage.removeItem("user_info");
      set({
        isAuth: false,
        user: null,
        userId: null,
        loading: false,
        error: null,
      });
      return;
    } else {
      liff.logout();
    }
    set({ isAuth: false, user: null, loading: false, error: null });
  },
}));
