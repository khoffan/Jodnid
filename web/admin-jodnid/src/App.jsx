import { useEffect } from "react";
import { Routes, Route } from "react-router";
import { SystemConfiguration } from "./features/systemConfiguration/pages/SystemConfiguration";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "./common/firebase/firebase_config";

import AdminNavbar from "./common/components/AdminNavbar";
import LoginPage from "./features/authentication/pages/LoginPage";
import AuthGuard from "./common/guard/AuthGuard";
import useAuthStore from "./features/authentication/store/auth.store";
import ProfilePage from "./features/profile/pages/ProfilePage";
import { DashboardPage } from "./features/monitoring/pages/DashboardPage";
import { SystemLogPage } from "./features/monitoring/pages/SystemLogPage";
import { UsersPage } from "./features/users/pages/UsersPage";
import { CategoriesPage } from "./features/categories/pages/CategoriesPage";

const element = (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/" element={<AuthGuard />}>
      <Route index element={<SystemConfiguration />} />
      <Route path="dashboard" element={<DashboardPage />} />
      <Route path="logs" element={<SystemLogPage />} />
      <Route path="users" element={<UsersPage />} />
      <Route path="categories" element={<CategoriesPage />} />
      <Route path="profile" element={<ProfilePage />} />
    </Route>
  </Routes>
);

export default function App() {
  const { user, isLoading } = useAuthStore();
  useEffect(() => {
    // ทุกครั้งที่ Firebase เปลี่ยนสถานะ ต้องตรวจกับ backend ว่าเป็น admin จริง ไม่ใช่เชื่อ Firebase อย่างเดียว
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      useAuthStore.getState().verifyAdmin(firebaseUser);
    });
    return () => unsubscribe();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen w-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  return (
    <div>
      {user && <AdminNavbar />}
      {element}
    </div>
  );
}
