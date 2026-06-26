import { useWebAuthStore } from "../../features/webapp/auth/store/web_auth.store";
import { useEffect } from "react";
import { useNavigate, Outlet, Navigate, useLocation } from "react-router";

export default function AuthGuard() {
  const { loading, user, isOnboarded } = useWebAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // ถ้าโหลดสถานะเสร็จแล้ว และไม่มี user ให้เด้งไปหน้า login
    if (!loading && !user) {
      navigate("/login", { replace: true });
      return;
    }

    // ถ้ายังไม่ onboarding ให้บังคับไปหน้า setup ก่อน
    if (!loading && user && !isOnboarded && location.pathname !== "/setup") {
      navigate("/setup", { replace: true });
    }
  }, [user, loading, isOnboarded, location.pathname, navigate]);

  // 1. ระหว่างที่ Firebase กำลังเช็คสถานะ (isLoading) ให้โชว์หน้าโหลดนวลๆ
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-500 font-medium">กำลังยืนยันตัวตน...</p>
        </div>
      </div>
    );
  }

  // 2. ถ้ามี User แล้ว ให้แสดงเนื้อหาข้างใน (children)
  // 3. ถ้าไม่มี User ตัว useEffect ข้างบนจะทำงานเพื่อเปลี่ยนหน้า
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}
