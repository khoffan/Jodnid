import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router";
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
      <Route index element={<Navigate to="/dashboard" replace />} />
      <Route path="dashboard" element={<SystemConfiguration />} />
      <Route path="logs" element={<SystemConfiguration />} />
      <Route path="administrator" element={<SystemConfiguration />} />
      <Route path="config" element={<SystemConfiguration />} />
      <Route path="users" element={<SystemConfiguration />} />
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
      <div className="flex items-center justify-center h-screen w-full bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900"></div>
      </div>
    );
  }
  return (
    <div className="flex h-screen w-full bg-slate-50 overflow-hidden">
      {user && <Sidebar />}

      <main className="flex-1 h-full overflow-y-auto p-6 text-slate-800">{element}</main>
    </div>
  );
}
