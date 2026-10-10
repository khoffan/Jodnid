import { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import { useWebAuthStore } from "../store/web_auth.store";

export default function LineCallbackPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const completeLineLogin = useWebAuthStore((state) => state.completeLineLogin);
  const [error, setError] = useState(null);
  // code ของ LINE ใช้ได้ครั้งเดียว — StrictMode/รีเฟรชทำให้ effect รันซ้ำแล้วครั้งที่สองจะล้ม
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    const params = new URLSearchParams(location.search);
    completeLineLogin(params.get("code"), params.get("state")).then((result) => {
      if (!result.success) {
        setError(result.error);
        return;
      }
      navigate(result.isOnboarded ? "/" : "/setup", { replace: true });
    });
  }, [location.search, navigate, completeLineLogin]);

  return (
    <div className="max-w-md mx-auto min-h-screen bg-white p-6 flex flex-col justify-center items-center text-center">
      <div className="w-16 h-16 bg-primary-soft rounded-2xl flex items-center justify-center mb-6 shadow-sm border border-primary-soft-strong animate-pulse">
        <span className="text-3xl">🔑</span>
      </div>

      <h1 className="text-2xl font-extrabold text-gray-800 tracking-tight mb-2">
        กำลังเข้าสู่ระบบ
      </h1>

      {error ? (
        <div className="mt-4 p-4 bg-red-50 border border-red-100 rounded-2xl w-full">
          <p className="text-sm text-red-600 font-medium">⚠️ {error}</p>
          <button
            onClick={() => navigate("/login", { replace: true })}
            className="mt-4 px-4 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-semibold hover:bg-gray-200 transition"
          >
            กลับไปหน้าเข้าสู่ระบบ
          </button>
        </div>
      ) : (
        <p className="text-sm text-gray-400 mt-1 max-w-xs">กำลังตรวจสอบข้อมูล กรุณารอสักครู่...</p>
      )}
    </div>
  );
}
