import { Camera, Database, MessageSquare } from "lucide-react";

export const StatusCards = () => {
  const statusItems = [
    {
      label: "OCR Status",
      value: "Active",
      icon: <Camera />,
      color: "bg-blue-500",
    },
    {
      label: "Database",
      value: "Connected",
      icon: <Database />,
      color: "bg-green-500",
    },
    {
      label: "LINE API",
      value: "Online",
      icon: <MessageSquare />,
      color: "bg-purple-500",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {statusItems.map((item, idx) => (
        <div key={idx} className="bg-gray-50 border border-gray-100 rounded-xl shadow-sm p-4">
          <div className="flex flex-row items-center gap-4">
            <div className={`p-3 ${item.color} rounded-xl text-white shadow-md`}>
              {item.icon}
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">{item.label}</p>
              <p className="text-xl font-bold text-gray-800">{item.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
