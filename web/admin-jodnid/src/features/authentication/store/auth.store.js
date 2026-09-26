import { create } from "zustand";
import { auth } from "../../../common/firebase/firebase_config";
import { signInWithEmailAndPassword, signOut } from "firebase/auth";
import api, { errorMessage } from "../../../common/lib/api";

const useAuthStore = create((set) => ({
  // แถว Administrator จาก backend เท่านั้น — มีค่าเมื่อผ่าน /sync แล้ว (ไม่ใช่แค่ login Firebase ได้)
  user: null,
  isLoading: true, // กำลังตรวจสถานะตอนเปิดแอป
  isVerifying: false, // กำลังตรวจสิทธิ์หลังกดเข้าสู่ระบบ
  authError: "",

  // เรียกทุกครั้งที่สถานะ Firebase เปลี่ยน: ต้องมีแถว Administrator ที่ยังเปิดใช้งานอยู่ถึงเข้าได้
  // Firebase account ที่สมัครเองได้ (API key อยู่ใน bundle) จึงต้องตรวจกับ backend ทุกครั้ง
  verifyAdmin: async (firebaseUser) => {
    if (!firebaseUser) {
      set({ user: null, isLoading: false, isVerifying: false });
      return;
    }
    let response;
    try {
      response = await api.post("/api/administrator/sync", {
        name: firebaseUser.displayName,
        phone: firebaseUser.phoneNumber,
        profile: firebaseUser.photoURL,
      });
    } catch (error) {
      const status = error?.response?.status;
      set({ user: null, isLoading: false, isVerifying: false });
      if (status === 401 || status === 403) {
        // ไม่มีสิทธิ์ (ไม่มีแถว Administrator / ถูกปิดใช้งาน) → ออกจาก Firebase ด้วย
        set({ authError: errorMessage(error, "บัญชีนี้ไม่มีสิทธิ์เข้าใช้งาน console") });
        await signOut(auth);
      } else {
        // backend ล่ม/timeout ไม่ได้แปลว่าไม่มีสิทธิ์ — ไม่ sign out ให้ลองใหม่ได้
        set({ authError: errorMessage(error, "เชื่อมต่อระบบไม่ได้ กรุณาลองใหม่อีกครั้ง") });
      }
      return;
    }

    // ระหว่างรอ /sync ผู้ใช้อาจกดออกจากระบบหรือเปลี่ยนบัญชีไปแล้ว — ห้ามตั้ง user จากผลที่มาช้า
    if (auth.currentUser?.uid !== firebaseUser.uid) return;

    if (!response.data?.success) {
      set({
        user: null,
        isLoading: false,
        isVerifying: false,
        authError: response.data?.message || "บัญชีนี้ไม่มีสิทธิ์เข้าใช้งาน console",
      });
      await signOut(auth);
      return;
    }
    set({ user: response.data.data, isLoading: false, isVerifying: false, authError: "" });
  },

  // สำเร็จแล้ว onAuthStateChanged → verifyAdmin จะตัดสินต่อว่าเข้าได้หรือไม่
  signIn: async (email, password) => {
    set({ isVerifying: true, authError: "" });
    try {
      await signInWithEmailAndPassword(auth, email, password);
      return true;
    } catch {
      set({ isVerifying: false, authError: "อีเมลหรือรหัสผ่านไม่ถูกต้อง" });
      return false;
    }
  },

  setUser: (user) => set({ user }),

  signOut: async () => {
    await signOut(auth);
    set({ user: null, isLoading: false, authError: "" });
  },
}));

export default useAuthStore;
