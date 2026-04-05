import { useEffect } from 'react';
import { useParams } from 'react-router'; // เพิ่ม useParams
import useTransactionStore from '../store/useTransectionStore';
import LoadingSkeleton from '../components/LoadindSkeleton';

const Dashboard = ({ userId }) => {
  const { type } = useParams(); // รับค่า 'daily' หรือ 'monthly' จาก URL
  const { transactions, totalAmount, summary, fetchDashboard, loading } = useTransactionStore();
  useEffect(() => {
    if (userId) {
      // คุณสามารถส่ง type ไปที่ store เพื่อให้ backend filter ข้อมูลตามช่วงเวลาได้
      fetchDashboard(userId, type || 'monthly'); 
    }
  }, [userId, type]);

  if (loading) return <LoadingSkeleton />;

  // --- จัดการ UI ตาม Type ---
  const isDaily = type === 'daily';
  const headerTitle = isDaily ? "ยอดใช้จ่ายวันนี้" : "ยอดใช้จ่ายเดือนนี้";
  const headerGradient = isDaily 
    ? "from-blue-500 to-blue-600" // สีฟ้าสำหรับรายวัน
    : "from-green-500 to-green-600"; // สีเขียวสำหรับรายเดือน

  return (
    <>
      {/* Header Card (Dynamic Color & Title) */}
      <div className={`bg-gradient-to-br ${headerGradient} rounded-3xl p-6 text-white shadow-lg mb-6 transition-all duration-500`}>
        <div className="flex justify-between items-center mb-1">
          <p className="opacity-80 text-sm font-light">{headerTitle}</p>
          <span className="bg-white/20 px-3 py-1 rounded-full text-[10px] backdrop-blur-sm">
            {isDaily ? "Today" : "This Month"}
          </span>
        </div>
        <h1 className="text-4xl font-bold mt-1">
          ฿ {totalAmount.toLocaleString()}
        </h1>
      </div>

      {/* สรุปตามหมวดหมู่ */}
      <div className="mb-2 flex items-center justify-between px-1">
        <h3 className="font-bold text-gray-800 text-sm">แยกตามหมวดหมู่</h3>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-6">
        {Object.entries(summary).length > 0 ? (
          Object.entries(summary).map(([name, amount]) => (
            <div key={name} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 hover:border-green-200 transition-colors">
              <p className="text-gray-400 text-[10px] uppercase tracking-wider">{name}</p>
              <p className="font-bold text-gray-800 text-lg">฿ {amount.toLocaleString()}</p>
            </div>
          ))
        ) : (
          <div className="col-span-2 text-center py-4 text-gray-400 text-sm bg-white rounded-2xl border border-dashed">
            ยังไม่มีข้อมูลในส่วนนี้
          </div>
        )}
      </div>

      {/* รายการล่าสุด */}
      <div className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-gray-800">รายการ{isDaily ? 'วันนี้' : 'ล่าสุด'}</h3>
          <button className="text-green-600 text-xs font-medium">ดูทั้งหมด</button>
        </div>
        
        <div className="space-y-4">
          {transactions.length > 0 ? (
            transactions.map((tx, idx) => (
              <div key={idx} className="flex items-center justify-between border-b border-gray-50 pb-3 last:border-0 hover:bg-gray-50 transition-colors rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="bg-gray-50 w-11 h-11 rounded-2xl flex items-center justify-center text-xl shadow-inner">
                    {tx.icon || '💸'}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800 text-sm">{tx.item}</p>
                    <p className="text-gray-400 text-[10px] mt-0.5">{tx.date}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-red-500 text-sm">-฿ {tx.amount.toLocaleString()}</p>
                  <p className="text-[9px] text-gray-300 uppercase">{tx.category}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-10">
              <p className="text-gray-300 text-sm">ไม่มีรายการใช้จ่าย</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Dashboard;