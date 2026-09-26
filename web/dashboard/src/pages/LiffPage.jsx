import { Routes, Route, Navigate, useLocation, useParams } from "react-router";
import { OverviewPage } from "../features/dashboard/pages/OverviewPage";
import Dashboard from "../features/transactions/pages/Dashboard";
import LoadingCheckUser from "../common/components/loading/LoadingCheckUser";
import Onboarding from "../features/dashboard/pages/Onboarding";
import { EditTempPage } from "../features/transactions/pages/EditTempPage";
import { useWebAuthStore } from "../features/webapp/auth/store/web_auth.store";

// Flex สรุปรายวันรุ่นเก่าที่ส่งไปแล้วลิงก์ ?path=/dashboard/daily — พาไป route ที่ถูกต้อง
const LegacySummaryRedirect = () => {
  const { type } = useParams();
  return <Navigate to={`/summary/${type}`} replace />;
};

export default function LiffPage({ userId }) {
  const error = useWebAuthStore((state) => state.error);
  const isOnboarded = useWebAuthStore((state) => state.isOnboarded);
  const location = useLocation();

  // ยังไม่ onboard → ทุกหน้าพาไป /setup ก่อน (กันการเข้าผ่าน deep link หรือกดลิงก์ในแอป)
  if (userId && !isOnboarded && location.pathname !== "/setup") {
    return <Navigate to="/setup" replace />;
  }
  const element = (
    <Routes>
      {/* ถ้ามี userId ให้ไป Dashboard ถ้าไม่มี (หรือยังไม่ Login) ให้กลับไปหน้าหลัก */}
      <Route path="/" element={<OverviewPage userId={userId} />} />

      {/* หน้า Onboarding สำหรับตั้งค่า Budget ครั้งแรก */}
      <Route path="/setup" element={<Onboarding userId={userId} />} />

      {/* สรุปรายวัน/รายเดือน (ใช้ Dashboard เดียวกันแต่ส่ง Type ไปเช็คข้างใน) */}
      <Route path="/summary/:type" element={<Dashboard userId={userId} />} />
      <Route path="/dashboard/:type" element={<LegacySummaryRedirect />} />

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
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm text-red-600 text-center">⚠️ {error}</p>
        </div>
      )}
      {!userId ? !error && <LoadingCheckUser /> : element}
    </div>
  );
}
