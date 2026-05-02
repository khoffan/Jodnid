export default function LoadingCheckUser() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-10 space-y-4">
      {/* Spinner หรือ Icon สวยๆ */}
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 border-4 border-green-100 rounded-full"></div>
        <div className="absolute inset-0 border-4 border-green-600 rounded-full border-t-transparent animate-spin"></div>
      </div>
      
      {/* ข้อความประกอบ */}
      <div className="flex flex-col items-center space-y-1">
        <h3 className="text-lg font-semibold text-gray-700">กำลังตรวจสอบข้อมูล</h3>
        <p className="text-sm text-gray-400 animate-pulse">กรุณารอสักครู่ ระบบกำลังเชื่อมต่อกับ JodNid...</p>
      </div>
    </div>
  )
}