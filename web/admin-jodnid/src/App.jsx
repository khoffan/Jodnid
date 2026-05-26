import { useEffect } from "react";
import { Routes, Route } from "react-router";
import { SystemConfiguration } from "./features/systemConfiguration/pages/SystemConfiguration";

import Sidebar from "./common/components/Sidebar";
import LoginPage from "./features/authentication/pages/LoginPage";
import AuthGuard from "./common/guard/authGuard";
import useAuthStore from "./features/authentication/store/auth.store";
import ProfilePage from "./features/profile/pages/ProfilePage";

const element = (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/" element={<AuthGuard />}>
      <Route index element={<SystemConfiguration />} />
      <Route path="profile" element={<ProfilePage />} />
    </Route>
  </Routes>
);

export default function App() {
  const { initializeAuth, isLoading, user } = useAuthStore();
  useEffect(() => {
    return initializeAuth();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen w-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  return (
    // 💡 ใช้ flex เพื่อจัดเซ็ตแนวแกน X (ซ้าย-ขวา) และจำกัดความสูงเต็มหน้าจอ
    <div className="flex h-screen w-full bg-slate-50 dark:bg-slate-950 overflow-hidden">
      {/* ฝั่งซ้าย: เรนเดอร์ Sidebar ถ้ามี user */}
      {user && <Sidebar />}

      {/* ฝั่งขวา: พื้นที่แสดงเนื้อหาหลักของแต่ละหน้าจอ */}
      <main className="flex-1 h-full overflow-y-auto p-6 text-slate-800 dark:text-slate-100">
        {element}
      </main>
    </div>
  );
}
