import { useWebAuthStore } from "../store/web_auth.store";

export default function LoginPage() {
  const { login, error, loading, isAuth, logout } = useWebAuthStore();

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
      {/* โลโก้และชื่อแอป */}
      <div className="text-center mb-10">
        <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-sm border border-green-100">
          <span className="text-3xl">💰</span>
        </div>
        <h1 className="text-4xl font-extrabold text-gray-800 tracking-tight mb-2">
          JodNid
        </h1>
        <p className="text-gray-500 max-w-xs mx-auto">
          สมุดบัญชีอัจฉริยะ บันทึกรายรับ-รายจ่ายของคุณได้ทุกที่ทุกเวลา
        </p>
      </div>

      {/* การ์ด Login */}
      <div className="w-full max-w-sm bg-white border border-gray-100 rounded-3xl p-8 shadow-xl flex flex-col items-center">
        <h2 className="text-lg font-semibold text-gray-700 mb-6">
          เข้าสู่ระบบเพื่อใช้งาน
        </h2>

        {/* ปุ่ม Login */}
        <button
          onClick={login}
          disabled={loading}
          className={`w-full py-3.5 px-6 bg-[#06C755] hover:bg-[#05b348] text-white rounded-2xl font-semibold shadow-md active:scale-[0.98] transition-all flex items-center justify-center gap-3 ${
            loading ? "opacity-75 cursor-not-allowed" : ""
          }`}
        >
          {loading ? (
            <svg
              className="animate-spin h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          ) : (
            <>
              <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                <path d="M10 19.385l-5.769-5.77a.77.77 0 0 1 0-1.09l5.77-5.769a.77.77 0 1 1 1.09 1.09l-4.469 4.469h10.923a.77.77 0 0 1 0 1.538H6.621l4.469 4.469a.77.77 0 0 1-1.09 1.09z" />
              </svg>
              <span>เข้าสู่ระบบด้วย LINE</span>
            </>
          )}
        </button>

        {/* แสดง Error */}
        {error && (
          <div className="mt-5 p-3 bg-red-50 border border-red-200 rounded-xl w-full">
            <p className="text-sm text-red-600 text-center">{error}</p>
          </div>
        )}

        {/* ข้อความเตือนสำหรับผู้ใช้ Web */}
        <p className="text-xs text-gray-400 mt-8 text-center">
          ระบบจะเชื่อมต่อข้อมูลอัตโนมัติเมื่อเข้าใช้งานผ่าน LIFF หรือ LINE
          Browser
        </p>
        {isAuth && <button onClick={logout}>Logout</button>}
      </div>
    </div>
  );
}
