import { useEffect } from 'react';
import useTransactionStore from '../store/useTransectionStore';
import LoadingSkeleton from '../components/LoadindSkeleton';

const Overview = ({ userId }) => {
  const { overviewStat, loading, fetchOverviewStat } = useTransactionStore();

  useEffect(() => {
    if (userId) {
      fetchOverviewStat(userId);
    }
  }, [userId, fetchOverviewStat]);

  if (loading) return <LoadingSkeleton />;

  // คำนวณความคืบหน้าของงบประมาณ (Progress)
  const budgetUsagePercent = overviewStat.budgetLimit > 0 
    ? (overviewStat.monthlyTotal / overviewStat.budgetLimit) * 100 
    : 0;

  return (
    <>
      <h1 className="text-2xl font-bold text-gray-800">สรุปภาพรวม</h1>

      {/* Card แสดงยอด Monthly & Budget Progress */}
      <div className="bg-white rounded-[2rem] p-6 shadow-sm border border-gray-100 space-y-4">
        <div>
          <p className="text-gray-400 text-xs">ยอดใช้จ่ายเดือนนี้</p>
          <div className="flex justify-between items-end">
            <h2 className="text-3xl font-black text-gray-900">
              ฿ {overviewStat.monthlyTotal.toLocaleString()}
            </h2>
            <p className="text-[10px] text-gray-400">จากงบ ฿{overviewStat.budgetLimit.toLocaleString()}</p>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-1000 ${budgetUsagePercent > 90 ? 'bg-red-500' : 'bg-green-500'}`}
            style={{ width: `${Math.min(budgetUsagePercent, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Grid สำหรับ Daily & Average */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-600 p-5 rounded-[2rem] text-white">
          <p className="text-blue-100 text-[10px] opacity-80">วันนี้</p>
          <p className="text-xl font-bold">฿ {overviewStat.dailyTotal.toLocaleString()}</p>
        </div>
        <div className="bg-white p-5 rounded-[2rem] border border-gray-100 shadow-sm">
          <p className="text-gray-400 text-[10px]">เฉลี่ยต่อวัน</p>
          <p className="text-xl font-bold text-gray-800">฿ {overviewStat.dailyAverage.toLocaleString()}</p>
        </div>
      </div>

      {/* Stat แยกตามหมวดหมู่ */}
      <div className="bg-white rounded-[2rem] p-6 shadow-sm border border-gray-100">
        <h3 className="font-bold text-gray-800 text-sm mb-4">สัดส่วนหมวดหมู่</h3>
        <div className="space-y-4">
          {Object.entries(overviewStat.categories).map(([name, amount]) => (
            <div key={name} className="flex justify-between items-center">
              <span className="text-sm text-gray-600">{name}</span>
              <span className="text-sm font-bold text-gray-900">฿ {amount.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default Overview;