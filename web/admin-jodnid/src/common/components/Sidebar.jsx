import React from "react";
import useAuthStore from "../../features/authentication/store/auth.store";
import { useNavigate } from "react-router";
import UserProfileCard from "./UserProfileCard";
// นิยามเมนูและสิทธิ์ที่จำเป็นต้องมีในการมองเห็นเมนูนั้นๆ
const SIDEBAR_MENUS = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: "📊", // สามารถเปลี่ยนเป็น Lucide React หรือ Heroicons ที่ใช้ในโปรเจกต์ได้เลยครับ
    requiredPermission: "overview_view",
  },
  {
    name: "Config Management",
    path: "/configs",
    icon: "⚙️",
    requiredPermission: "config_read",
  },
  {
    name: "Role Settings",
    path: "/roles",
    icon: "🔑",
    requiredPermission: "admin_manage", // เฉพาะระดับสูงที่จัดการสิทธิ์ได้
  },
  {
    name: "Administrators",
    path: "/admins",
    icon: "👥",
    requiredPermission: "admin_read", // เฉพาะระดับสูงที่ดูรายชื่อทีมหลังบ้านได้
  },
  {
    name: "Users Control",
    path: "/users",
    icon: "👤",
    requiredPermission: "user_view", // คนที่ดูประวัติผู้ใช้งานทั่วไปได้
  },
];

export default function Sidebar() {
  // 1. ดึงข้อมูลสิทธิ์และข้อมูลผู้ใช้จาก Store หลังบ้าน (ปรับตาม Store จริงของคุณได้เลยครับ)
  // สมมติโครงสร้าง: user: { name: "Khoffan", permissions: ["overview_view", "config_read"] }
  const { user, signOut } = useAuthStore?.() || {
    user: { permissions: ["overview_view", "config_read"] }, // Fallback ไว้ทดสอบ
  };
  const navigate = useNavigate();

  const userPermissions = user?.permissions || [];
  console.log("User Permissions:", userPermissions); // ล็อกสิทธิ์ที่ดึงมาได้เพื่อเช็คก่อนครับ

  // 2. กรองเมนูที่ User คนนี้มีสิทธิ์ดูเท่านั้น
  const visibleMenus = SIDEBAR_MENUS.filter((menu) =>
    userPermissions.includes(menu.requiredPermission),
  );

  const handleLogout = () => {
    signOut();
    navigate("/", {
      replace: true,
    });
  };

  return (
    <aside className="w-64 h-screen bg-slate-900 text-white flex flex-col justify-between p-4 border-r border-slate-800">
      {/* ส่วนบน: Logo และ รายการเมนู */}
      <div className="flex flex-col gap-6">
        <div className="px-2 py-3 text-xl font-bold tracking-wider text-teal-400 border-b border-slate-800">
          Molldini Admin
        </div>

        <nav className="flex flex-col gap-1">
          {visibleMenus.map((menu) => {
            // ตัวอย่างการเช็ค Active state เผื่อปรับแต่ง CSS สไตล์
            const isActive = true;

            return (
              <a
                key={menu.path}
                href={menu.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                  ${
                    isActive
                      ? "bg-teal-600 text-white"
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                  }`}
              >
                <span className="text-base">{menu.icon}</span>
                <span>{menu.name}</span>
              </a>
            );
          })}
        </nav>
      </div>

      {/* ส่วนล่าง: ProfileCard ที่มีอยู่แล้ว */}
      <div className="pt-4 border-t border-slate-800">
        {/* ปลดคอมเมนต์แล้วเรียกใช้ Component ของคุณตรงนี้ได้เลยครับ */}
        <UserProfileCard user={user} handleLogout={handleLogout} />
      </div>
    </aside>
  );
}
