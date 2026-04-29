import { useEffect } from "react";
import { useNavigate, Outlet, Navigate } from "react-router";
import useAuthStore from "../../features/authentication/store/auth.store";

export default function AuthGuard() {
  const { user, isLoading } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    // ถ้าโหลดสถานะเสร็จแล้ว และไม่มี user ให้เด้งไปหน้า login
    if (!isLoading && !user) {
      navigate("/login", { replace: true });
    }
  }, [user, isLoading, navigate]);

  // 1. ระหว่างที่ Firebase กำลังเช็คสถานะ (isLoading) ให้โชว์หน้าโหลดนวลๆ
  if (isLoading) {
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
