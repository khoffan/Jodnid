import React from "react";
import useAuthStore from "../../features/authentication/store/auth.store";
import { NavLink, useNavigate } from "react-router";
import UserProfileCard from "./UserProfileCard";

const SIDEBAR_MENUS = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: "📊",
    requiredPermission: "overview_view",
  },
  {
    name: "Logs",
    path: "/logs",
    icon: "📝",
    requiredPermission: "log_view",
  },
  {
    name: "Administrator",
    path: "/administrator",
    icon: "👥",
    requiredPermission: "admin_read",
  },
  {
    name: "Config",
    path: "/config",
    icon: "⚙️",
    requiredPermission: "config_read",
  },
  {
    name: "Users",
    path: "/users",
    icon: "👤",
    requiredPermission: "user_view",
  },
];

export default function Sidebar() {
  const store = useAuthStore();
  const user = store?.user;
  const signOut = store?.signOut;
  const navigate = useNavigate();

  // Show all menus for admin users (permissions check can be added later)
  const visibleMenus = SIDEBAR_MENUS;

  const handleLogout = () => {
    if (signOut) {
      signOut();
    }
    navigate("/login", {
      replace: true,
    });
  };

  return (
    <aside className="w-64 h-full bg-white text-slate-900 flex flex-col justify-between border-r border-gray-200 p-4 flex-shrink-0">
      <div className="flex flex-col gap-4">
        <div className="px-3 py-4 border-b border-gray-200">
          <h2 className="text-lg font-bold tracking-tight text-slate-900">JodNid</h2>
          <p className="text-xs text-slate-500 mt-1">Administrator</p>
        </div>

        <nav className="flex flex-col gap-1">
          {visibleMenus.length > 0 ? (
            visibleMenus.map((menu) => (
              <NavLink
                key={menu.path}
                to={menu.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all ${
                    isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                  }`
                }
              >
                <span className="text-base">{menu.icon}</span>
                <span>{menu.name}</span>
              </NavLink>
            ))
          ) : (
            <p className="text-xs text-slate-500 px-3 py-2">No menu items</p>
          )}
        </nav>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <UserProfileCard user={user} handleLogout={handleLogout} />
      </div>
    </aside>
  );
}
