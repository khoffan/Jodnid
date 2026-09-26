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
    try {
      const response = await api.post("/api/administrator/sync", {
        name: firebaseUser.displayName,
        phone: firebaseUser.phoneNumber,
        profile: firebaseUser.photoURL,
      });
      if (!response.data?.success) throw new Error(response.data?.message);
      set({ user: response.data.data, isLoading: false, isVerifying: false, authError: "" });
    } catch (error) {
      set({
        user: null,
        isLoading: false,
        isVerifying: false,
        authError: errorMessage(error, "บัญชีนี้ไม่มีสิทธิ์เข้าใช้งาน console"),
      });
      await signOut(auth);
    }
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
