import { useState, useEffect } from 'react';
import liff from '@line/liff';
import Dashboard from './pages/Dashboard';
import Onboarding from './pages/OnBoarding';
import { Routes, Route, Navigate } from 'react-router'

function App() {
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    liff.init({ liffId: import.meta.env.VITE_LINE_LIFF_ID }).then(() => {
      if (liff.isLoggedIn()) {
        console.log("LIFF Login Success");
        const profile = liff.getContext();
        setUserId(profile.userId);
      } else {
        console.log("LIFF Login Required");
        liff.login();
      }
    });
  }, []);

  const element = (
    <Routes>
      {/* ถ้ามี userId ให้ไป Dashboard ถ้าไม่มี (หรือยังไม่ Login) ให้กลับไปหน้าหลัก */}
      <Route path="/" element={userId ? <Dashboard userId={userId} /> : <div className="p-10">กรุณาเข้าสู่ระบบผ่าน LINE</div>} />
      
      {/* หน้า Onboarding สำหรับตั้งค่า Budget ครั้งแรก */}
      <Route path="/setup" element={<Onboarding userId={userId} />} />

      {/* สรุปรายวัน/รายเดือน (ใช้ Dashboard เดียวกันแต่ส่ง Type ไปเช็คข้างใน) */}
      <Route path="/summary/:type" element={<Dashboard userId={userId} />} />

      {/* Fallback กรณีเข้า Path มั่ว */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )


  return (
    <div className="max-w-md mx-auto min-h-screen shadow-2xl bg-white">
      {element}
    </div>
  );
}

export default App;