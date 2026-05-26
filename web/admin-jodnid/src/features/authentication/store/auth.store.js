import { create } from "zustand";
import { auth } from "../../../common/firebase/firebase_config";
import { signInWithEmailAndPassword, signOut, createUserWithEmailAndPassword, onAuthStateChanged } from "firebase/auth";
import api from "../../../common/lib/api";

const useAuthStore = create((set) => ({
  user: null,
  isLoading: true,
  initializeAuth: () => {
    set({ isLoading: true });

    // onAuthStateChanged จะทำงานเมื่อเปิดแอป หรือเมื่อ Firebase แอบ Refresh Token สำเร็จ
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          // ดึง idToken ล่าสุด (ถ้าใกล้หมดอายุ หรือหมดแล้วมันจะ Refresh ให้เองเบื้องหลัง)
          const idToken = await firebaseUser.getIdToken();
          sessionStorage.setItem("token", idToken);

          // ดึงข้อมูลผู้ใช้จาก Backend มา Sync
          const res = await api.post("/api/administrator/sync", {
            uid: firebaseUser.uid,
            email: firebaseUser.email,
            name: firebaseUser.displayName,
            phone: firebaseUser.phoneNumber,
            profile: firebaseUser.photoURL,
          });

          set({ user: res.data.data, isLoading: false });
        } catch (error) {
          console.error("Error syncing user data:", error);
          set({ user: null, isLoading: false });
        }
      } else {
        // ไม่มีผู้ใช้ล็อกอินอยู่ หรือกด SignOut ไปแล้ว
        sessionStorage.removeItem("token");
        set({ user: null, isLoading: false });
      }
    });

    return unsubscribe;
  },

  signIn: async (email, password) => {
    try {
      set({ isLoading: true });
      const result = await signInWithEmailAndPassword(auth, email, password);
      console.log(result);
      const idToken = await result.user.getIdToken();
      sessionStorage.setItem("token", idToken);
      const res = await api.post("/api/administrator/sync", {
        uid: result.user.uid,
        email: result.user.email,
        name: result.user.displayName,
        phone: result.user.phoneNumber,
        profile: result.user.photoURL,
      });
      const user = res.data.data;
      console.log(user);
      set({ user: user, isLoading: false });
      return { success: true };
    } catch (error) {
      set({ isLoading: false });
      return { success: false, error: error };
    }
  },
  signUp: async (name, email, password) => {
    try {
      set({ isLoading: true });
      await createUserWithEmailAndPassword(auth, email, password);
      set({ isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  signOut: async () => {
    await signOut(auth);
    set({ user: null, isLoading: false });
  },
}));

export default useAuthStore;
