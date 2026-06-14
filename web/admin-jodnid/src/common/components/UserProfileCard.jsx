import { LogOut, UserIcon } from "lucide-react";
import { Link } from "react-router";

export default function UserProfileCard({ user, handleLogout }) {
  return (
    <div className="relative group">
      {/* Profile Trigger */}
      <button className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200">
        <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center text-slate-700 font-bold text-sm">
          {user?.email?.charAt(0).toUpperCase() || "U"}
        </div>
        <div className="flex flex-col items-start flex-1 min-w-0">
          <span className="text-xs font-semibold text-slate-900 truncate">
            {user?.email?.split("@")[0]}
          </span>
          <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">
            Admin
          </span>
        </div>
      </button>

      {/* Dropdown Menu */}
      <div className="absolute left-0 right-0 bottom-full mb-2 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
        <div className="px-4 py-3 border-b border-gray-100">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Account</p>
          <p className="text-sm font-semibold text-slate-900 truncate mt-1">{user?.email}</p>
        </div>

        <Link
          to="/profile"
          className="flex items-center gap-3 px-4 py-3 text-sm text-slate-700 hover:bg-slate-50 transition-colors w-full text-left border-b border-gray-100"
        >
          <UserIcon size={16} />
          <span className="font-medium">Profile</span>
        </Link>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors w-full text-left"
        >
          <LogOut size={16} />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </div>
  );
}
