import { Routes, Route, Navigate } from "react-router";
import { OverviewPage } from "../features/dashboard/pages/OverviewPage";
import Dashboard from "../features/transactions/pages/Dashboard";
import LoadingCheckUser from "../common/components/loading/LoadingCheckUser";
import Onboarding from "../features/dashboard/pages/Onboarding";
import { EditTempPage } from "../features/transactions/pages/EditTempPage";

export default function LiffPage({ userId }) {
  const element = (
    <Routes>
      {/* ถ้ามี userId ให้ไป Dashboard ถ้าไม่มี (หรือยังไม่ Login) ให้กลับไปหน้าหลัก */}
      <Route path="/" element={<OverviewPage userId={userId} />} />

      {/* หน้า Onboarding สำหรับตั้งค่า Budget ครั้งแรก */}
      <Route path="/setup" element={<Onboarding userId={userId} />} />

      {/* สรุปรายวัน/รายเดือน (ใช้ Dashboard เดียวกันแต่ส่ง Type ไปเช็คข้างใน) */}
      <Route path="/summary/:type" element={<Dashboard userId={userId} />} />

      <Route
        path="/edit-temp/:tempId"
        element={<EditTempPage userId={userId} />}
      />

      {/* Fallback กรณีเข้า Path มั่ว */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );

  return (
    <div className="max-w-md mx-auto min-h-screen shadow-2xl bg-white p-5 pt-10 pb-20 rounded-3xl">
      {!userId ? <LoadingCheckUser /> : element}
    </div>
  );
}
