import { LayoutDashboard, Megaphone, Settings } from "lucide-react";
import { Link as RouterLink, useLocation } from "react-router";

export const AdminNavbar = () => {
  const { pathname } = useLocation();

  const menuItems = [
    { label: "Configs", path: "/", icon: <Settings size={18} /> },
    {
      label: "Broadcast",
      path: "/broadcast",
      icon: <Megaphone size={18} />,
    },
    {
      label: "Stats",
      path: "/dashboard",
      icon: <LayoutDashboard size={18} />,
    },
  ];

  return (
    <nav className="flex items-center px-6 py-3 border-b border-gray-200 bg-white/70 backdrop-blur-md sticky top-0 z-50 justify-between">
      <div className="flex items-center gap-2">
        <p className="font-bold text-gray-800">JodNid ADMIN</p>
      </div>
      <div className="hidden sm:flex items-center gap-6">
        {menuItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <RouterLink
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2 font-medium transition-colors ${isActive ? "text-blue-600" : "text-gray-600 hover:text-gray-900"}`}
            >
              {item.icon} {item.label}
            </RouterLink>
          );
        })}
      </div>
      <div>
        <button className="px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors">
          Logout
        </button>
      </div>
    </nav>
  );
};
