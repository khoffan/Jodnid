import { Camera, Database, MessageSquare, Wrench } from "lucide-react";

const STATE_STYLE = {
  ok: { dot: "bg-green-500", chip: "bg-green-500" },
  warn: { dot: "bg-amber-500", chip: "bg-amber-500" },
  down: { dot: "bg-red-500", chip: "bg-red-500" },
  unknown: { dot: "bg-gray-400", chip: "bg-gray-400" },
};

const buildItems = (status) => {
  if (!status) {
    return [
      { label: "Database", value: "ไม่ทราบสถานะ", icon: <Database />, state: "unknown" },
      { label: "LINE API", value: "ไม่ทราบสถานะ", icon: <MessageSquare />, state: "unknown" },
      { label: "OCR", value: "ไม่ทราบสถานะ", icon: <Camera />, state: "unknown" },
      { label: "Maintenance", value: "ไม่ทราบสถานะ", icon: <Wrench />, state: "unknown" },
    ];
  }

  const features = status.features ?? {};
  return [
    {
      label: "Database",
      value: status.database?.detail ?? "-",
      icon: <Database />,
      state: status.database?.ok ? "ok" : "down",
    },
    {
      label: "LINE API",
      value: status.line_api?.detail ?? "-",
      icon: <MessageSquare />,
      state: status.line_api?.ok ? "ok" : "down",
    },
    {
      label: "OCR / ข้อความ",
      value: `${features.is_ocr_active ? "เปิด" : "ปิด"} / ${
        features.is_text_active ? "เปิด" : "ปิด"
      }`,
      icon: <Camera />,
      state: features.is_ocr_active && features.is_text_active ? "ok" : "warn",
    },
    {
      label: "Maintenance",
      value: features.is_maintenance_mode ? "กำลังปรับปรุง" : "ให้บริการปกติ",
      icon: <Wrench />,
      state: features.is_maintenance_mode ? "warn" : "ok",
    },
  ];
};

export const StatusCards = ({ status }) => {
  const statusItems = buildItems(status);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {statusItems.map((item) => {
        const style = STATE_STYLE[item.state] ?? STATE_STYLE.unknown;
        return (
          <div
            key={item.label}
            className="bg-gray-50 border border-gray-100 rounded-xl shadow-sm p-4"
          >
            <div className="flex flex-row items-center gap-4">
              <div className={`p-3 ${style.chip} rounded-xl text-white shadow-md`}>
                {item.icon}
              </div>
              <div className="min-w-0">
                <p className="text-xs text-gray-500 font-medium">{item.label}</p>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${style.dot}`}></span>
                  <p className="text-lg font-bold text-gray-800 truncate" title={item.value}>
                    {item.value}
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
