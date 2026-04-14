import { useEffect } from "react";
import { useOverviewStore } from "../store/overview.store";
import LoadingSkeleton from "../../../common/components/loading/LoadindSkeleton";
import { StatCard } from "../components/dashboard/StatCard";
import { CategoryItem } from "../components/dashboard/CategoryItem";

export const OverviewPage = ({ userId }) => {
  const { overviewStat, loading, fetchOverviewStat } = useOverviewStore();

  useEffect(() => {
    if (userId) {
      const now = new Date();
      fetchOverviewStat(
        userId,
        now.getDate(),
        now.getMonth() + 1,
        now.getFullYear(),
      );
    }
  }, [userId, fetchOverviewStat]);

  if (loading) return <LoadingSkeleton />;

  const budgetUsagePercent =
    overviewStat.budgetLimit > 0
      ? (overviewStat.monthlyTotal / overviewStat.budgetLimit) * 100
      : 0;

  return (
    <div className="space-y-6 pb-24 px-2">
      <h1 className="text-2xl font-bold text-gray-800">สรุปภาพรวม</h1>

      {/* Main Budget Card */}
      <div className="bg-white rounded-[2.5rem] p-7 shadow-sm border border-gray-100 space-y-5">
        <div>
          <p className="text-gray-400 text-xs font-medium uppercase tracking-wider">
            ยอดใช้จ่ายเดือนนี้
          </p>
          <div className="flex justify-between items-end mt-1">
            <h2 className="text-4xl font-black text-gray-900">
              ฿{overviewStat.monthlyTotal.toLocaleString()}
            </h2>
            <p className="text-xs font-bold text-gray-700">
              งบ ฿{overviewStat.budgetLimit.toLocaleString()}
            </p>
          </div>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-1000 ${budgetUsagePercent > 90 ? "bg-red-500" : "bg-green-500"}`}
            style={{ width: `${Math.min(budgetUsagePercent, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        <StatCard
          label="วันนี้"
          value={overviewStat.dailyTotal}
          variant="blue"
        />
        <StatCard label="เฉลี่ยต่อวัน" value={overviewStat.dailyAverage} />
      </div>

      {/* Categories List */}
      <div className="bg-white rounded-[2.5rem] p-7 shadow-sm border border-gray-100">
        <h3 className="font-bold text-gray-800 text-sm mb-6 flex items-center gap-2">
          <span className="w-1 h-4 bg-indigo-500 rounded-full"></span>
          งบประมาณแยกตามหมวดหมู่
        </h3>
        <div className="space-y-7">
          {overviewStat.categories.length > 0 ? (
            overviewStat.categories.map((cat) => (
              <CategoryItem key={cat.name} cat={cat} />
            ))
          ) : (
            <p className="text-center py-4 text-gray-400 text-xs">
              ยังไม่มีข้อมูล
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
