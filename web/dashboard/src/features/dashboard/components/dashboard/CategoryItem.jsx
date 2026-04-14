import { useState } from "react";

export const CategoryItem = ({ cat }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isWarning = cat.percent > 90;

  return (
    <div
      className={`p-3 -mx-3 rounded-3xl transition-all duration-300 ${isExpanded ? "bg-slate-50" : "bg-transparent"}`}
    >
      {/* ส่วนบน: คลิกเพื่อกางออก */}
      <div
        className="flex justify-between items-start cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl bg-white w-12 h-12 flex items-center justify-center rounded-2xl shadow-sm border border-gray-50 group-active:scale-95 transition-transform">
            {cat.icon}
          </span>
          <div>
            <p className="text-sm font-bold text-gray-800">{cat.name}</p>
            <p className="text-[10px] text-gray-400">
              {cat.percent.toFixed(0)}% ของงบหมวดนี้
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm font-black text-gray-900">
            ฿{cat.spent.toLocaleString()}
          </p>
          <div className="flex items-center justify-end gap-1">
            <p className="text-[9px] text-gray-400 font-medium uppercase tracking-tighter">
              Details
            </p>
            {/* Icon ลูกศร หมุนตามสถานะ */}
            <svg
              className={`w-2.5 h-2.5 text-gray-400 transition-transform duration-300 ${isExpanded ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="3"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Progress Bar (แสดงตลอดเวลา) */}
      <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden mt-3">
        <div
          className={`h-full transition-all duration-700 ${isWarning ? "bg-orange-500" : "bg-indigo-500"}`}
          style={{ width: `${Math.min(cat.percent, 100)}%` }}
        ></div>
      </div>

      {/* ส่วนที่ Expand ออกมา: แสดงข้อมูลเจาะลึก */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${isExpanded ? "max-h-20 opacity-100 mt-4" : "max-h-0 opacity-0"}`}
      >
        <div className="grid grid-cols-2 gap-2 pb-1">
          <div className="bg-white/60 p-2 rounded-xl border border-gray-100">
            <p className="text-[9px] text-gray-400 uppercase font-bold">
              งบที่ตั้งไว้
            </p>
            <p className="text-xs font-bold text-gray-700">
              ฿{cat.limit.toLocaleString()}
            </p>
          </div>
          <div className="bg-white/60 p-2 rounded-xl border border-gray-100">
            <p className="text-[9px] text-gray-400 uppercase font-bold">
              คงเหลือจริง
            </p>
            <p
              className={`text-xs font-bold ${cat.remaining < 0 ? "text-red-500" : "text-green-600"}`}
            >
              ฿{cat.remaining.toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
