import { Camera, Database, MessageSquare } from "lucide-react";

export const StatusCards = () => {
  const statusItems = [
    {
      label: "OCR Status",
      value: "Active",
      icon: <Camera />,
    },
    {
      label: "Database",
      value: "Connected",
      icon: <Database />,
    },
    {
      label: "LINE API",
      value: "Online",
      icon: <MessageSquare />,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {statusItems.map((item, idx) => (
        <div key={idx} className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
          <div className="flex flex-row items-center gap-4">
            <div className="p-3 bg-slate-200 rounded-xl text-black shadow-sm">{item.icon}</div>
            <div>
              <p className="text-xs text-slate-500 font-medium">{item.label}</p>
              <p className="text-xl font-bold text-black">{item.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
