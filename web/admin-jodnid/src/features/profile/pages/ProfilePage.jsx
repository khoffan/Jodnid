import { useState } from "react";
import { updatePassword, updateProfile } from "firebase/auth";
import { auth } from "../../../common/firebase/firebase_config"; // ปรับ path ตามไฟล์ firebase config ของคุณ
import useAuthStore from "../../authentication/store/auth.store";
import { User, Lock, Phone, Edit3, Save, X } from "lucide-react";

export default function ProfilePage() {
  const { user } = useAuthStore();

  // State สำหรับโหมดและข้อมูล
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    fullName: user?.displayName || "",
    phone: user?.phoneNumber || "",
    newPassword: "",
    confirmPassword: "",
  });

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ type: "", msg: "" });

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: "", msg: "" });

    try {
      // 1. อัปเดตข้อมูลพื้นฐาน (Firebase Auth เก็บ displayName ได้)
      await updateProfile(auth.currentUser, {
        displayName: formData.fullName,
      });

      // 2. อัปเดตรหัสผ่าน (ถ้ามีการกรอก)
      if (formData.newPassword) {
        if (formData.newPassword !== formData.confirmPassword) {
          throw new Error("รหัสผ่านไม่ตรงกัน");
        }
        await updatePassword(auth.currentUser, formData.newPassword);
      }

      setStatus({ type: "success", msg: "อัปเดตข้อมูลสำเร็จแล้ว" });
      setIsEditing(false); // ปิดโหมดแก้ไข
      setFormData((prev) => ({
        ...prev,
        newPassword: "",
        confirmPassword: "",
      }));
    } catch (error) {
      setStatus({ type: "error", msg: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-10 px-4">
      <div className="bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden">
        {/* Header Section */}
        <div className="p-8 border-b border-gray-50 flex justify-between items-center bg-gray-50/50">
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 bg-indigo-600 rounded-3xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
              {user?.email?.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                โปรไฟล์ผู้ใช้งาน
              </h1>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl font-semibold transition-all ${
              isEditing
                ? "bg-gray-200 text-gray-600"
                : "bg-indigo-50 text-indigo-600 hover:bg-indigo-100"
            }`}
          >
            {isEditing ? (
              <>
                <X size={18} /> ยกเลิก
              </>
            ) : (
              <>
                <Edit3 size={18} /> แก้ไขโปรไฟล์
              </>
            )}
          </button>
        </div>

        <form onSubmit={handleUpdateProfile} className="p-8 space-y-8">
          {/* ข้อมูลทั่วไป */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-400 uppercase ml-1 flex items-center gap-2">
                <User size={14} /> Full Name
              </label>
              <input
                disabled={!isEditing}
                type="text"
                value={formData.fullName}
                onChange={(e) =>
                  setFormData({ ...formData, fullName: e.target.value })
                }
                className="w-full px-5 py-3.5 bg-gray-50 border-transparent rounded-2xl focus:bg-white focus:ring-2 focus:ring-indigo-500/20 transition-all outline-none disabled:opacity-60"
                placeholder="กรุณากรอกชื่อ-นามสกุล"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-400 uppercase ml-1 flex items-center gap-2">
                <Phone size={14} /> Phone Number
              </label>
              <input
                disabled={!isEditing}
                type="tel"
                value={formData.phone}
                onChange={(e) =>
                  setFormData({ ...formData, phone: e.target.value })
                }
                className="w-full px-5 py-3.5 bg-gray-50 border-transparent rounded-2xl focus:bg-white focus:ring-2 focus:ring-indigo-500/20 transition-all outline-none disabled:opacity-60"
                placeholder="08X-XXX-XXXX"
              />
            </div>
          </div>

          {/* ส่วนเปลี่ยนรหัสผ่าน (จะแสดงเมื่ออยู่ในโหมดแก้ไขเท่านั้น) */}
          {isEditing && (
            <div className="pt-6 border-t border-gray-100 space-y-6">
              <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                <Lock size={16} /> เปลี่ยนรหัสผ่าน (ระบุหากต้องการเปลี่ยน)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <input
                  type="password"
                  placeholder="รหัสผ่านใหม่"
                  value={formData.newPassword}
                  onChange={(e) =>
                    setFormData({ ...formData, newPassword: e.target.value })
                  }
                  className="w-full px-5 py-3.5 bg-gray-50 border-transparent rounded-2xl focus:bg-white focus:ring-2 focus:ring-indigo-500/20 transition-all outline-none"
                />
                <input
                  type="password"
                  placeholder="ยืนยันรหัสผ่านใหม่"
                  value={formData.confirmPassword}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      confirmPassword: e.target.value,
                    })
                  }
                  className="w-full px-5 py-3.5 bg-gray-50 border-transparent rounded-2xl focus:bg-white focus:ring-2 focus:ring-indigo-500/20 transition-all outline-none"
                />
              </div>
            </div>
          )}

          {/* Status Message */}
          {status.msg && (
            <div
              className={`p-4 rounded-2xl text-sm font-medium ${status.type === "success" ? "bg-green-50 text-green-600" : "bg-red-50 text-red-600"}`}
            >
              {status.msg}
            </div>
          )}

          {/* Action Buttons */}
          {isEditing && (
            <div className="flex justify-end pt-4">
              <button
                disabled={loading}
                type="submit"
                className="flex items-center gap-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl font-bold shadow-lg shadow-indigo-100 transition-all disabled:bg-gray-300"
              >
                <Save size={18} /> {loading ? "กำลังบันทึก..." : "บันทึกข้อมูล"}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
