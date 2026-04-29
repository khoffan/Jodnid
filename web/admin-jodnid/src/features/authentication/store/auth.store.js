import { create } from "zustand";
import { auth } from "../../../common/firebase/firebase_config";
import {
  signInWithEmailAndPassword,
  signOut,
  createUserWithEmailAndPassword,
} from "firebase/auth";
import api from "../../../common/lib/api";
const useAuthStore = create((set) => ({
  user: null,
  isLoading: true,
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

// Listen for auth state changes

export default useAuthStore;
