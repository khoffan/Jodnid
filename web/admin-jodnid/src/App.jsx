import { useEffect } from "react";
import { Routes, Route } from "react-router";
import { SystemConfiguration } from "./features/systemConfiguration/pages/SystemConfiguration";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "./common/firebase/firebase_config";

import AdminNavbar from "./common/components/AdminNavbar";
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
  const { user, isLoading } = useAuthStore();
  useEffect(() => {
    const subscription = onAuthStateChanged(auth, (user) => {
      useAuthStore.setState({ user, isLoading: false });
    });
    return () => subscription();
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
