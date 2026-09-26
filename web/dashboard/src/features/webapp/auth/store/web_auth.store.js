import { create } from "zustand";
import liff from "@line/liff";
import api, { setUnauthorizedHandler } from "../../../../common/lib/api";

const testMode = import.meta.env.VITE_TEST_MODE;

const AUTH_RECOVER_KEY = "auth_recover_at";
const OAUTH_STATE_KEY = "line_oauth_state";
const LIFF_SESSION_KEY = "liff_session";
const AUTH_RECOVER_COOLDOWN_MS = 60_000;
let isRecovering = false;

const extractUserId = (user) => {
  if (!user) return null;
  return user.user_id ?? user.id ?? user.userId ?? null;
};

export const useWebAuthStore = create((set, get) => ({
  isAuth: false,
  isWebApp: false,
  isOnboarded: true,
  user: null,
  userId: null,
  error: null,
  loading: false,
  onboardingCategories: [],
  onboardingBudgets: {},
  onboardingLoading: false,

  // บันทึกว่า onboard แล้ว และอัปเดต store ด้วย — ไม่งั้น guard จะพากลับ /setup และหน้า /setup
  // ครั้งถัดไปจะแสดงขั้นเลือกหมวดซ้ำ
  setOnboardStatus: async () => {
    try {
      const response = await api.post("/api/user/onboarded");
      if (!response?.data?.success) return false;
      set({ isOnboarded: true });
      return true;
    } catch (error) {
      console.error("Failed to complete onboarding:", error);
      return false;
    }
  },

  fetchOnboardingData: async (userId) => {
    if (!userId) {
      set({ onboardingCategories: [], onboardingBudgets: {}, onboardingLoading: false });
      return { categories: [], budgets: {} };
    }

    set({ onboardingLoading: true });

    try {
      const [categoryRes, budgetRes] = await Promise.all([
        api.get("/api/categories/parent"),
        api.get(`/api/budgets/${userId}`),
      ]);

      const categories = categoryRes.data || [];
      const budgets = {};

      if (budgetRes.data?.success && Array.isArray(budgetRes.data.data)) {
        budgetRes.data.data.forEach((b) => {
          budgets[b.category_id] = b.amount?.toString() ?? "";
        });
      }

      set({
        onboardingCategories: categories,
        onboardingBudgets: budgets,
        onboardingLoading: false,
      });

      return { categories, budgets };
    } catch (error) {
      console.error("Failed to fetch onboarding data:", error);
      set({ onboardingCategories: [], onboardingBudgets: {}, onboardingLoading: false });
      return { categories: [], budgets: {} };
    }
  },

  // ฟังก์ชัน Initialize ระบบ
  initApp: async (navigate) => {
    set({ loading: true, error: null });

    const urlParams = new URLSearchParams(window.location.search);
    // ลิงก์ LIFF (deep link จาก Flex / redirect หลัง liff.login) ที่ถูกเปิดนอกแอป LINE เช่น LINE PC
    // ยังต้องไปสาย LIFF — ดูจาก ?path= ที่ backend สร้าง และพารามิเตอร์ที่ LIFF SDK แนบมาเอง
    const isLiffLink =
      urlParams.has("path") || urlParams.has("liff.state") || urlParams.has("liffClientId");
    // แท็บที่เปิดมาจากลิงก์ LIFF ให้อยู่สาย LIFF ต่อ — หลัง liff.init/navigate URL ไม่มีพารามิเตอร์แล้ว
    // ถ้ากดรีเฟรชในเบราว์เซอร์นอกแอป (เช่น LINE PC) จะหลุดไปสาย web
    if (isLiffLink) sessionStorage.setItem(LIFF_SESSION_KEY, "1");
    const inLiffSession = sessionStorage.getItem(LIFF_SESSION_KEY) === "1";
    // liff.isInClient() เรียกก่อน liff.init() ได้
    const isWebApp =
      urlParams.get("webapp") === "true" || (!liff.isInClient() && !isLiffLink && !inLiffSession);
    // 🔹 กรณีเปิดผ่าน Web Browser / Desktop
    if (isWebApp) {
      const storedUser = sessionStorage.getItem("user_info");
      if (!storedUser || !sessionStorage.getItem("id_token")) {
        set({ isWebApp: true, isAuth: false, loading: false });
        return;
      }

      try {
        const parsedUser = JSON.parse(storedUser);
        const parsedUserId = extractUserId(parsedUser);
        const onboardingStatusResponse = await api.get("/api/user/onboarding-status");
        const isOnboarded = !!onboardingStatusResponse?.data?.is_onboarded;
        await get().fetchOnboardingData(parsedUserId);

        set({
          isWebApp: true,
          user: parsedUser,
          userId: parsedUserId,
          isAuth: true,
          isOnboarded,
          loading: false,
        });
      } catch (error) {
        // 401 = token หมดอายุ → recoverSession พาไปหน้า login แล้ว; อย่างอื่นให้ login ใหม่พร้อมข้อความ
        set({
          isWebApp: true,
          isAuth: false,
          loading: false,
          error:
            error.response?.status === 401 ? null : "เชื่อมต่อระบบไม่ได้ กรุณาเข้าสู่ระบบอีกครั้ง",
        });
      }
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

        // ยังไม่ onboard → ต้องตั้งค่าก่อนเสมอ แม้เปิดมาจาก deep link
        if (!isOnboarded) {
          navigate("/setup", { replace: true });
          return;
        }

        // อ่าน URL ใหม่หลัง liff.init() — เปิดครั้งแรกผ่าน liff.line.me URL จะมาเป็น liff.state
        // แล้ว SDK แปลงกลับเป็น ?path=... ให้ระหว่าง init
        const targetPath =
          new URLSearchParams(window.location.search).get("path") || urlParams.get("path");
        if (targetPath) {
          navigate(targetPath);
        }
      } else {
        liff.login();
        // ยังไม่ล็อกอิน ให้แสดงปุ่มให้ผู้ใช้กด
        set({ loading: false, isAuth: false });
      }
    } catch (error) {
      // 401 = token หมดอายุ → interceptor เรียก recoverSession ไปแล้ว อย่าเขียนทับข้อความของมัน
      if (error.response?.status === 401) return;
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
      // state แบบสุ่มที่เดาไม่ได้ เก็บไว้เทียบตอน LINE redirect กลับ (กัน CSRF ของ OAuth)
      const state = crypto.randomUUID();
      sessionStorage.setItem(OAUTH_STATE_KEY, state);

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

  // LINE ID token อายุ ~1 ชม. และ liff.getIDToken() คืนตัวที่ cache ไว้แม้หมดอายุแล้ว
  // → logout เพื่อล้าง cache แล้ว reload ให้ initApp เรียก liff.login() ขอ token ใหม่
  // ลองได้ครั้งเดียวต่อ 1 นาที กัน reload วนไม่รู้จบถ้า token ใหม่ก็ยังใช้ไม่ได้
  recoverSession: () => {
    if (isRecovering) return;

    const lastTry = Number(sessionStorage.getItem(AUTH_RECOVER_KEY) || 0);
    if (Date.now() - lastTry < AUTH_RECOVER_COOLDOWN_MS) {
      set({ error: "เซสชันหมดอายุ กรุณาปิดแล้วเปิดหน้านี้ใหม่อีกครั้ง", loading: false });
      return;
    }

    isRecovering = true;
    sessionStorage.setItem(AUTH_RECOVER_KEY, String(Date.now()));
    sessionStorage.removeItem("id_token");

    if (get().isWebApp) {
      sessionStorage.removeItem("user_info");
      window.location.href = "/login";
      return;
    }

    try {
      if (liff.isLoggedIn()) liff.logout();
    } catch {
      // liff.init ยังไม่สำเร็จ — reload ก็พอ
    }
    window.location.reload();
  },

  // หน้า /login/callback: ตรวจ state แล้วแลก code เป็น token (ทำครั้งเดียวต่อ code)
  completeLineLogin: async (code, state) => {
    const expectedState = sessionStorage.getItem(OAUTH_STATE_KEY);
    sessionStorage.removeItem(OAUTH_STATE_KEY);
    if (!code || !state || state !== expectedState) {
      return { success: false, error: "ลิงก์เข้าสู่ระบบไม่ถูกต้องหรือหมดอายุ กรุณาเข้าสู่ระบบใหม่" };
    }

    try {
      const res = await api.post("/api/user", { code });
      const user = res.data.user_info;
      sessionStorage.setItem("id_token", res.data.id_token);
      sessionStorage.setItem("user_info", JSON.stringify(user));

      const statusRes = await api.get("/api/user/onboarding-status");
      const isOnboarded = !!statusRes?.data?.is_onboarded;
      await get().fetchOnboardingData(extractUserId(user));
      set({
        isWebApp: true,
        isAuth: true,
        user,
        userId: extractUserId(user),
        isOnboarded,
        error: null,
      });
      return { success: true, isOnboarded };
    } catch (error) {
      console.error("LINE Login Error:", error);
      return { success: false, error: "เกิดข้อผิดพลาดในการเข้าสู่ระบบด้วย LINE" };
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
  },
}));

setUnauthorizedHandler(() => useWebAuthStore.getState().recoverSession());
