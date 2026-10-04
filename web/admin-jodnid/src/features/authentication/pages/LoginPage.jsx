import { useState } from "react";
import { Navigate } from "react-router";
import useAuthStore from "../store/auth.store";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // error เก็บใน store: การตรวจสิทธิ์จบใน verifyAdmin ซึ่งอาจทำงานตอนหน้านี้ถูก render ใหม่
  const { user, signIn, isVerifying, authError: errorMsg } = useAuthStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    await signIn(email, password);
  };

  if (user) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-[2.5rem] shadow-xl p-8 border border-gray-100">
        {/* Header Section */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            ยินดีต้อนรับกลับมา
          </h1>
          <p className="text-gray-500 mt-2">
            เข้าสู่ระบบ JodNid Administrator เพื่อจัดการระบบหลังบ้าน
          </p>
        </div>

        {/* Error Callout */}
        {errorMsg && (
          <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 text-sm rounded-2xl text-center">
            {errorMsg}
          </div>
        )}

        {/* Form Section */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase ml-4 mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-6 py-4 bg-gray-50 border-transparent focus:border-indigo-500 focus:bg-white focus:ring-0 rounded-2xl transition-all duration-200 outline-none"
              placeholder="name@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase ml-4 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-6 py-4 bg-gray-50 border-transparent focus:border-indigo-500 focus:bg-white focus:ring-0 rounded-2xl transition-all duration-200 outline-none"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isVerifying}
            className={`w-full py-4 mt-4 rounded-2xl font-bold text-white transition-all duration-200 shadow-lg ${
              isVerifying
                ? "bg-gray-300 cursor-not-allowed shadow-none"
                : "bg-indigo-600 hover:bg-indigo-700 shadow-indigo-100"
            }`}
          >
            {isVerifying ? "กำลังตรวจสอบ..." : "เข้าสู่ระบบ"}
          </button>
        </form>
      </div>
    </div>
  );
}
