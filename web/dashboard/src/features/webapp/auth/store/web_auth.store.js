import { create } from "zustand";
import liff from "@line/liff";
import api from "../../../../common/lib/api";

const testMode = import.meta.env.VITE_TEST_MODE;

export const useWebAuthStore = create((set) => ({
  isAuth: false,
  isWebApp: false,
  isOnboarded: true,
  user: null,
  userId: null,
  error: null,
  loading: false,

  setLogin: (user) => {
    set({ isAuth: true, user, userId: user?.user_id || null, error: null });
  },
  // ฟังก์ชัน Initialize ระบบ
  initApp: async (navigate) => {
    set({ loading: true, error: null });

    const urlParams = new URLSearchParams(window.location.search);
    const isWebApp =false;
    // const isWebApp = urlParams.get("webapp") === "true" || !liff.isInClient();
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
        userId: user ? JSON.parse(user).user_id : null,
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

        const userResponse = await api.post("/api/user", {
          id_token: idToken,
        });
        const userInfo = userResponse?.data?.user_info;
        if (userInfo) {
          sessionStorage.setItem("user_info", JSON.stringify(userInfo));
        }

        const onboardingStatusResponse = await api.get("/api/user/onboarding-status");
        const isOnboarded = !!onboardingStatusResponse?.data?.is_onboarded;

        set({
          user: userInfo || null,
          userId: userInfo?.user_id || context.userId,
          isAuth: true,
          isOnboarded,
          loading: false,
        });

        const targetPath = urlParams.get("path");
        if (targetPath) {
          navigate(targetPath);
          return;
        }

        if (!isOnboarded) {
          navigate("/setup", { replace: true });
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
      let clientId;
      if (import.meta.env.VITE_ENV === "production") {
        clientId = import.meta.env.VITE_LINE_CHANNEL_ID;
      } else {
        clientId = testMode
          ? import.meta.env.VITE_LINE_CHANNEL_ID_TEST
          : import.meta.env.VITE_LINE_CHANNEL_ID;
      }

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
        isOnboarded: true,
        user: null,
        userId: null,
        loading: false,
        error: null,
      });
      return;
    } else {
      liff.logout();
    }
    set({ isAuth: false, isOnboarded: true, user: null, loading: false, error: null });
  },

  completeOnboarding: async () => {
    try {
      const response = await api.post("/api/user/onboarded");
      if (!response?.data?.success) {
        return false;
      }

      set({ isOnboarded: true });
      return true;
    } catch (error) {
      console.error("Failed to complete onboarding:", error);
      return false;
    }
  },
}));
