import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { RotateCcw } from "lucide-react";
import useTransactionStore from "../store/useTransectionStore";
import LoadingSkeleton from "../../../common/components/loading/LoadindSkeleton";
import SelectField from "../../../common/components/dropdown/SelectFields";

const Dashboard = ({ userId }) => {
  const { type } = useParams();
  const { fetchDashboard, loading, dashboardData, transactions } =
    useTransactionStore();
  const now = new Date();

  const [selectedYear, setSelectedYear] = useState(now.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(now.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState(now.getDate());

  useEffect(() => {
    if (userId) {
      fetchDashboard(
        userId,
        type || "monthly",
        selectedDay,
        selectedMonth,
        selectedYear,
      );
    }
  }, [userId, type, selectedDay, selectedMonth, selectedYear, fetchDashboard]);

  // เปลี่ยนเงื่อนไข Loading ให้ยืดหยุ่นขึ้น
  if (loading) return <LoadingSkeleton />;
  if (!dashboardData)
    return <div className="p-10 text-center text-gray-400">ไม่พบข้อมูล</div>;

  // ดึงข้อมูลจากโครงสร้างใหม่ที่คุณส่งมา
  // {"total_amount": 100, "summary": {...}, "transactions": [...]}
  const { total_amount, summary } = dashboardData;
  const isDaily = type === "daily";
  const headerTitle = isDaily ? "ยอดใช้จ่ายวันนี้" : "ยอดใช้จ่ายเดือนนี้";

  // ✨ ฟังก์ชันสำหรับ Reset กลับเป็นค่าปัจจุบัน
  const handleReset = () => {
    setSelectedYear(now.getFullYear());
    setSelectedMonth(now.getMonth() + 1);
    setSelectedDay(now.getDate());
  };

  // ตรวจสอบว่าค่าที่เลือก "ต่างจากปัจจุบัน" หรือไม่ เพื่อแสดงปุ่ม Reset แบบ Dynamic
  const isFiltered =
    selectedYear !== now.getFullYear() ||
    selectedMonth !== now.getMonth() + 1 ||
    (type === "daily" && selectedDay !== now.getDate());

  // --- Prepare Options (เหมือนเดิม) ---
  const monthOptions = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
  ].map((name, i) => ({ label: name, value: i + 1 }));
  const yearOptions = [0, 1].map((offset) => ({
    label: `พ.ศ. ${now.getFullYear() - offset + 543}`,
    value: now.getFullYear() - offset,
  }));
  const daysOptions = Array.from({ length: 31 }, (_, i) => ({
    label: `${i + 1}`,
    value: i + 1,
  }));

  return (
    <div className="max-w-md mx-auto pb-20 px-2">
      {/* 📊 Filter Bar */}
      <div className="flex flex-col gap-2 mb-4">
        <div className="flex gap-2 items-end">
          <SelectField
            label="ปี"
            options={yearOptions}
            value={selectedYear}
            onChange={setSelectedYear}
            className="flex-1"
          />
          <SelectField
            label="เดือน"
            options={monthOptions}
            value={selectedMonth}
            onChange={setSelectedMonth}
            className="flex-[1.5]"
          />

          {isDaily && (
            <SelectField
              label="วัน"
              options={daysOptions}
              value={selectedDay}
              onChange={setSelectedDay}
              className="flex-1"
            />
          )}

          {/* 🔄 ปุ่ม Reset ด้วย Icon */}
          <button
            onClick={handleReset}
            className={`mb-1 p-2.5 rounded-2xl transition-all duration-300 flex items-center justify-center border
              ${
                isFiltered
                  ? "text-indigo-600 border-indigo-100 shadow-sm active:scale-90"
                  : "bg-gray-50 text-gray-300 border-transparent opacity-40 cursor-not-allowed"
              }`}
            disabled={!isFiltered}
          >
            {/* ใช้ Lucide Icon หรือ Emoji */}
            <RotateCcw size={20} strokeWidth={2.5} />
            {/* ถ้าไม่ใช้ library ใช้เป็น: <span>🔄</span> */}
          </button>
        </div>
      </div>

      {/* 💳 Header Card: แสดงยอดรวม (Total Amount) */}
      <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white shadow-2xl mb-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-full -mr-10 -mt-10 blur-2xl"></div>
        <p className="text-slate-400 text-xs font-medium uppercase tracking-widest opacity-80">
          {headerTitle}
        </p>
        <h1 className="text-5xl font-black mt-2 text-green-400">
          ฿{(total_amount || 0).toLocaleString()}
        </h1>
      </div>

      {/* 📑 Summary by Category (จาก Object summary) */}
      <div className="mb-4 flex items-center justify-between px-1">
        <h3 className="font-bold text-slate-800 text-sm">แยกตามหมวดหมู่</h3>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-8">
        {summary && Object.entries(summary).length > 0 ? (
          Object.entries(summary).map(([name, amount]) => (
            <div
              key={name}
              className="bg-white p-4 rounded-3xl shadow-sm border border-slate-100"
            >
              <p className="text-slate-400 text-[10px] font-bold uppercase tracking-tight mb-1 truncate">
                {name}
              </p>
              <p className="font-black text-slate-800 text-lg">
                ฿{amount.toLocaleString()}
              </p>
            </div>
          ))
        ) : (
          <div className="col-span-2 text-center py-4 text-gray-300 text-xs bg-gray-50 rounded-2xl border border-dashed">
            ไม่มีข้อมูลหมวดหมู่
          </div>
        )}
      </div>

      {/* 🕒 Transactions List (จาก transactions ใน dashboardData) */}
      <div className="bg-white rounded-[2.5rem] p-6 shadow-sm border border-slate-100">
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-bold text-slate-800">รายการล่าสุด</h3>
          <span className="text-[10px] bg-slate-100 px-2 py-1 rounded-full text-slate-500 font-bold uppercase">
            {transactions?.length || 0} รายการ
          </span>
        </div>

        <div className="space-y-5">
          {transactions && transactions.length > 0 ? (
            transactions.map((tx, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between group"
              >
                <div className="flex items-center gap-4">
                  <div className="bg-slate-50 w-12 h-12 rounded-2xl flex items-center justify-center text-xl group-hover:bg-green-50 transition-colors shadow-inner">
                    {tx.icon || "💸"}
                  </div>
                  <div>
                    <p className="font-bold text-slate-800 text-sm leading-tight">
                      {tx.item}
                    </p>
                    <p className="text-slate-400 text-[10px] mt-1">
                      {tx.date} • {tx.category}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-black text-slate-800 text-sm">
                    -฿{tx.amount.toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-10 text-slate-300 text-sm">
              ไม่มีรายการใช้จ่าย
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
