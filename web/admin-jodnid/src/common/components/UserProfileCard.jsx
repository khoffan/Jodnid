import { LogOut, UserIcon } from "lucide-react";
import { Link } from "react-router";

export default function UserProfileCard({ user, handleLogout }) {
  return (
    <div className="relative group">
      {/* Profile Trigger */}
      <button className="flex items-center gap-3 p-1 pr-3 hover:bg-gray-50 rounded-full transition-all duration-200 border border-transparent hover:border-gray-100">
        <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold shadow-md shadow-indigo-100">
          {user?.email?.charAt(0).toUpperCase() || "U"}
        </div>
        <div className="flex flex-col items-start hidden sm:flex">
          <span className="text-sm font-bold text-gray-800 leading-tight">
            {user?.email?.split("@")[0]}
          </span>
          <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">
            Administrator
          </span>
        </div>
      </button>

      {/* Dropdown Menu */}
      <div className="absolute right-0 mt-2 w-56 bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 translate-y-2 group-hover:translate-y-0">
        {/* User Info Header (Mobile/Extra Info) */}
        <div className="px-5 py-3 border-b border-gray-50 mb-1">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-tighter">
            Signed in as
          </p>
          <p className="text-sm font-semibold text-gray-700 truncate">
            {user?.email}
          </p>
        </div>

        {/* Options */}
        <button className="flex items-center gap-3 px-5 py-3 text-sm text-gray-600 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left transition-colors">
          <UserIcon size={16} />
          <Link to="/profile" className="font-medium">
            จัดการโปรไฟล์
          </Link>
        </button>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-5 py-3 text-sm text-red-500 hover:bg-red-50 w-full text-left transition-colors"
        >
          <LogOut size={16} />
          <span className="font-medium">ออกจากระบบ</span>
        </button>
      </div>
    </div>
  );
}
