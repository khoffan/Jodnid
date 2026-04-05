import { useState, useEffect } from 'react';
import liff from '@line/liff';
import { Routes, Route, Navigate, useNavigate } from 'react-router'
import Dashboard from './pages/Dashboard';
import Onboarding from './pages/Onboarding';
import UserCheckingLoading from './components/loading/LoadingCheckUser';
import Overview from './pages/OverviewPage';

function App() {
  const [userId, setUserId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    liff.init({ liffId: import.meta.env.VITE_LINE_LIFF_ID }).then(() => {
      if (liff.isLoggedIn()) {
        const context = liff.getContext();
        setUserId(context.userId);

        const urlParams = new URLSearchParams(window.location.search);
        const targetPath = urlParams.get("path");

        if(targetPath) {
          navigate(targetPath);
        }
      } else {
        liff.login();
      }
    });
  }, [navigate]);

  const element = (
    <Routes>
      {/* ถ้ามี userId ให้ไป Dashboard ถ้าไม่มี (หรือยังไม่ Login) ให้กลับไปหน้าหลัก */}
      <Route path="/" element={<Overview userId={userId} />} />
      
      {/* หน้า Onboarding สำหรับตั้งค่า Budget ครั้งแรก */}
      <Route path="/setup" element={<Onboarding userId={userId} />} />

      {/* สรุปรายวัน/รายเดือน (ใช้ Dashboard เดียวกันแต่ส่ง Type ไปเช็คข้างใน) */}
      <Route path="/summary/:type" element={<Dashboard userId={userId} />} />

      {/* Fallback กรณีเข้า Path มั่ว */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )


  return (
    <div className="max-w-md mx-auto min-h-screen shadow-2xl bg-white p-5 pt-10 pb-20 rounded-3xl">
      {!userId ? <UserCheckingLoading /> : element}
    </div>
  );
}

export default App;