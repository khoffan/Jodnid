import { Navigate, Route, Routes, useNavigate } from "react-router";
import LoginPage from "../features/webapp/auth/pages/LoginPage";
import AuthGuard from "../common/guard/AuthGuard";
import TransactionListPage from "../features/webapp/transaction/pages/TransactionListPage";
import AddTransactionPage from "../features/webapp/transaction/pages/AddTransactionPage";
import LoginCallbackPage from "../features/webapp/auth/pages/LineCallbackPage";
import { WebOnboarding } from "../features/dashboard/pages/WebOnboarding";
import WebNavbar from "../common/components/webComponent/WebNavbar";
import { useWebAuthStore } from "../features/webapp/auth/store/web_auth.store";
import { useWebTransaction } from "../features/webapp/transaction/store/web.transaction.store";

export default function WebPage() {
  const { userId, logout, isAuth } = useWebAuthStore();
  const navigate = useNavigate();

  // ล้างข้อมูลรายการในหน่วยความจำด้วย ไม่ให้ค้างให้คนที่ใช้เครื่องต่อเห็น
  const handleLogout = async () => {
    useWebTransaction.getState().reset();
    await logout();
    navigate("/login", { replace: true });
  };

  const element = (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/login/callback" element={<LoginCallbackPage />} />
      <Route path="/" element={<AuthGuard />}>
        <Route index element={<TransactionListPage />} />
        <Route path="/add" element={<AddTransactionPage />} />
        <Route path="/setup" element={<WebOnboarding userId={userId} />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );

  return (
    <div className="w-full min-h-screen bg-gray-50">
      {isAuth && <WebNavbar navigate={navigate} logout={handleLogout} />}
      {element}
    </div>
  );
}
