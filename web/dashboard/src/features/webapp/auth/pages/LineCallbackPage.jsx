import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import { useWebAuthStore } from "../store/web_auth.store";
import api from "../../../../common/lib/api";

export default function LineCallbackPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { initApp, setLogin } = useWebAuthStore();

  const [status, setStatus] = useState("กำลังตรวจสอบข้อมูล กรุณารอสักครู่...");
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(location.search);
      const code = params.get("code");
      // const state = params.get("state");

      // ตรวจสอบเบื้องต้นว่ามี code หรือไม่
      if (!code) {
        setError("ไม่พบรหัสยืนยันตัวตน (Code) จาก LINE");
        return;
      }

      try {
        const res = await api.post("/api/user", {
          code,
        })
        console.log("LINE Login Response:", res.data);
        const user = res.data.user_info;
        sessionStorage.setItem("id_token", res.data.id_token);
        sessionStorage.setItem("user_info", JSON.stringify(user));
        setStatus("เข้าสู่ระบบสำเร็จ กำลังโหลดข้อมูล...");
        setLogin(user);
        // TODO: ส่ง code ไปให้ Backend แลก token
        // ตัวอย่างเช่น:
        // const res = await api.post("/api/auth/line-login", { code });
        //
        // เมื่อ Backend ตอบกลับมาและบันทึก session แล้ว:
        // sessionStorage.setItem("id_token", res.data.id_token);
        // await initApp(navigate); // โหลดข้อมูล User ใหม่
        // navigate("/");

        // --- Mock การทำงาน ---

        navigate("/");

      } catch (err) {
        console.error("LINE Login Error:", err);
        setError("เกิดข้อผิดพลาดในการเข้าสู่ระบบด้วย LINE");
      }
    };

    handleCallback();
  }, [location, navigate, initApp]);

  return (
    <div className="max-w-md mx-auto min-h-screen bg-white p-6 flex flex-col justify-center items-center text-center">
      <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mb-6 shadow-sm border border-green-100 animate-pulse">
        <span className="text-3xl">🔑</span>
      </div>

      <h1 className="text-2xl font-extrabold text-gray-800 tracking-tight mb-2">
        กำลังเข้าสู่ระบบ
      </h1>

      {error ? (
        <div className="mt-4 p-4 bg-red-50 border border-red-100 rounded-2xl w-full">
          <p className="text-sm text-red-600 font-medium">{error}</p>
          <button
            onClick={() => navigate("/login")}
            className="mt-4 px-4 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-semibold hover:bg-gray-200 transition"
          >
            กลับไปหน้า Login
          </button>
        </div>
      ) : (
        <p className="text-sm text-gray-400 mt-1 max-w-xs">{status}</p>
      )}
    </div>
  );
}
