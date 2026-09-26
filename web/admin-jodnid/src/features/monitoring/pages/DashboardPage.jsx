import { useEffect, useState } from "react";
import { AlertTriangle, LayoutDashboard, Receipt, ScanLine, Users } from "lucide-react";
import useMonitoringStore from "../store/monitoring.store";

const MetricCard = ({ icon, label, value, hint, tone = "blue" }) => {
  const tones = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    amber: "bg-amber-500",
    red: "bg-red-500",
  };
  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 ${tones[tone]} rounded-lg text-white`}>{icon}</div>
        <p className="text-xs text-gray-500 font-medium">{label}</p>
      </div>
      <p className="text-3xl font-bold text-gray-800 mt-3">{value}</p>
      {hint && <p className="text-xs text-gray-400 mt-1">{hint}</p>}
    </div>
  );
};

export const DashboardPage = () => {
  const { metrics, metricsError, fetchMetrics } = useMonitoringStore();
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetchMetrics(days);
  }, [fetchMetrics, days]);

  if (metricsError) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
          {metricsError}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="p-8 max-w-6xl mx-auto text-gray-400 text-sm">กำลังโหลดข้อมูลสรุป...</div>
    );
  }

  const { users, transactions, ocr, errors_in_range: errors } = metrics;
  const mismatchTone =
    ocr.total_mismatch_rate === null || ocr.total_mismatch_rate < 10 ? "green" : "amber";

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <LayoutDashboard className="text-blue-500" /> ภาพรวมระบบ
          </h1>
          <p className="text-gray-500 text-sm mt-1">ตัวเลขย้อนหลัง {metrics.range_days} วัน</p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value={1}>24 ชั่วโมง</option>
          <option value={7}>7 วัน</option>
          <option value={30}>30 วัน</option>
        </select>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-500">ผู้ใช้</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard icon={<Users size={18} />} label="ผู้ใช้ทั้งหมด" value={users.total} />
          <MetricCard
            icon={<Users size={18} />}
            label="ตั้งค่าเริ่มต้นแล้ว"
            value={users.onboarded}
            hint={`${users.total - users.onboarded} คนยังไม่ได้ตั้งค่า`}
            tone="green"
          />
          <MetricCard
            icon={<Users size={18} />}
            label="เปิดโหมดบันทึกด่วน"
            value={users.bypass_mode}
            tone="amber"
          />
          <MetricCard
            icon={<Users size={18} />}
            label={`ผู้ใช้ใหม่ใน ${metrics.range_days} วัน`}
            value={users.new_in_range}
          />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-500">การจดรายการ</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            icon={<Receipt size={18} />}
            label="รายการวันนี้"
            value={transactions.today}
          />
          <MetricCard
            icon={<Receipt size={18} />}
            label="รายการเดือนนี้"
            value={transactions.this_month}
          />
          <MetricCard
            icon={<Receipt size={18} />}
            label="ยอดรวมเดือนนี้"
            value={`฿${transactions.amount_this_month.toLocaleString()}`}
            tone="green"
          />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-500">คุณภาพการอ่านใบเสร็จ</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={<ScanLine size={18} />}
            label="อ่านสำเร็จ"
            value={ocr.success_rate === null ? "-" : `${ocr.success_rate}%`}
            hint={`จากตัวอย่าง ${ocr.sample_size} รูป`}
            tone={ocr.success_rate === null || ocr.success_rate >= 90 ? "green" : "amber"}
          />
          <MetricCard
            icon={<AlertTriangle size={18} />}
            label="ยอดไม่ลงตัว"
            value={ocr.total_mismatch_rate === null ? "-" : `${ocr.total_mismatch_rate}%`}
            hint={`${ocr.total_mismatched} รายการที่ต้องให้ผู้ใช้ยืนยันเอง`}
            tone={mismatchTone}
          />
          <MetricCard
            icon={<ScanLine size={18} />}
            label="เวลาเฉลี่ย (median)"
            value={ocr.median_latency_ms === null ? "-" : `${ocr.median_latency_ms} ms`}
          />
          <MetricCard
            icon={<AlertTriangle size={18} />}
            label="ข้อผิดพลาดในระบบ"
            value={errors}
            hint={`ระดับ ERROR ใน ${metrics.range_days} วัน`}
            tone={errors > 0 ? "red" : "green"}
          />
        </div>
      </section>
    </div>
  );
};
