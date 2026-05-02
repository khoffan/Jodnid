import { create } from "zustand";
import liff from "@line/liff";
import api from "../../../../common/lib/api";

export const useWebAuthStore = create((set) => ({
  isAuth: false,
  isWebApp: false,
  user: null,
  error: null,
  loading: false,

  setLogin: () => {
    set({ isAuth: true });
  },
  // ฟังก์ชัน Initialize ระบบ
  initApp: async (navigate) => {
    set({ loading: true, error: null });

    const urlParams = new URLSearchParams(window.location.search);
    const isWebApp = urlParams.get("webapp") === "true" || !liff.isInClient();

    // 🔹 กรณีเปิดผ่าน Web Browser / Desktop
    if (isWebApp) {
      console.log("Web App Mode");
      set({
        isWebApp: true,
        userId: "mock-webapp-user-id", // เปลี่ยนเป็น Firebase UID หรือ Token ได้ในอนาคต
        isAuth: true,
        loading: false,
      });
      return;
    }

    // 🔹 กรณีเปิดผ่าน LINE LIFF Client
    const testMode = import.meta.env.VITE_TEST_MODE;
    let liffId = testMode
      ? import.meta.env.VITE_LINE_LIFF_ID_TEST
      : import.meta.env.VITE_LINE_LIFF_ID;

    if (!liffId) {
      console.error("LIFF ID is required, but none was found.");
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

        await api.post("/api/user", {});

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
      const clientId = import.meta.env.VITE_LINE_CHANNEL_ID;

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
    sessionStorage.removeItem("id_token");
    if (liff.isLoggedIn()) {
      liff.logout();
    }
    set({ isAuth: false, user: null, loading: false, error: null });
  },
}));
