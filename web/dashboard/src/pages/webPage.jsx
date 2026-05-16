import { Route, Routes } from "react-router";
import LoginPage from "../features/webapp/auth/pages/LoginPage";
import AuthGuard from "../common/guard/AuthGuard";
import TransactionListPage from "../features/webapp/transaction/pages/TransactionListPage";
import AddTransactionPage from "../features/webapp/transaction/pages/AddTransactionPage";
import LoginCallbackPage from "../features/webapp/auth/pages/LineCallbackPage";

export default function webPage() {
  const element = (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/login/callback" element={<LoginCallbackPage />} />
      <Route path="/" element={<AuthGuard />}>
        <Route index element={<TransactionListPage />} />
        <Route path="/add" element={<AddTransactionPage />} />
      </Route>
    </Routes>
  );

  return <div className="w-full min-h-screen bg-gray-50">{element}</div>;
}
