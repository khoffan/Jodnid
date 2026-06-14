import { useLocation } from "react-router";
import { Settings } from "lucide-react";
import { DashboardTab } from "../tabs/DashboardTab";
import { LogsTab } from "../tabs/LogsTab";
import { AdministratorTab } from "../tabs/AdministratorTab";
import { ConfigTab } from "../tabs/ConfigTab";
import { UsersTab } from "../tabs/UsersTab";

export const SystemConfiguration = () => {
  const location = useLocation();

  const renderView = () => {
    switch (location.pathname) {
      case "/logs":
        return <LogsTab />;
      case "/administrator":
        return <AdministratorTab />;
      case "/config":
        return <ConfigTab />;
      case "/users":
        return <UsersTab />;
      default:
        return <DashboardTab />;
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-end">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-slate-900">
            <Settings className="text-slate-900" /> JodNid Administrator
          </h1>
          <p className="text-slate-500 text-sm mt-1">จัดการระบบหลังบ้าน</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="p-6 bg-white">{renderView()}</div>
      </div>
    </div>
  );
};
