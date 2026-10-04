import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Users as UsersIcon } from "lucide-react";
import useUsersStore, { PAGE_SIZE } from "../store/users.store";

const formatDate = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("th-TH");
};

export const UsersPage = () => {
  const {
    users,
    total,
    offset,
    isLoading,
    error,
    fetchUsers,
    setSearch,
    toggleBypassMode,
    syncBudgets,
    nextPage,
    prevPage,
  } = useUsersStore();
  const [searchDraft, setSearchDraft] = useState("");
  // user ที่กำลังมี request ค้างอยู่ — กันกดซ้ำระหว่างรอผล
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    fetchUsers(0);
  }, [fetchUsers]);

  const handleToggle = async (user) => {
    const next = !user.use_bypass_mode;
    const label = next ? "เปิด" : "ปิด";
    if (!confirm(`ยืนยัน${label}โหมดบันทึกด่วนให้ "${user.display_name ?? user.line_user_id}"?`)) {
      return;
    }
    setBusyId(user.line_user_id);
    const result = await toggleBypassMode(user.line_user_id, next);
    setBusyId(null);
    if (!result.success) {
      alert("ไม่สามารถอัปเดตได้: " + result.error);
    }
  };

  const handleSyncBudgets = async (user) => {
    setBusyId(user.line_user_id);
    const result = await syncBudgets(user.line_user_id);
    setBusyId(null);
    alert(
      result.success
        ? `ซ่อมยอดงบเดือนนี้แล้ว (แก้ ${result.updated} หมวด)`
        : "ซ่อมยอดงบไม่สำเร็จ: " + result.error,
    );
  };

  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + PAGE_SIZE, total);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <UsersIcon className="text-blue-500" /> ผู้ใช้งาน
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          ค้นหาผู้ใช้ และปิดโหมดบันทึกด่วนให้คนที่แจ้งว่าระบบจดยอดผิด
        </p>
      </div>

      <form
        className="flex gap-2 bg-white border border-gray-100 rounded-xl p-4 shadow-sm"
        onSubmit={(e) => {
          e.preventDefault();
          setSearch(searchDraft);
        }}
      >
        <input
          value={searchDraft}
          onChange={(e) => setSearchDraft(e.target.value)}
          placeholder="ค้นหาจากชื่อ, LINE user id หรืออีเมล..."
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm flex-1"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600"
        >
          ค้นหา
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">ผู้ใช้</th>
                <th className="text-left px-4 py-3 font-medium">สถานะ</th>
                <th className="text-left px-4 py-3 font-medium">สมัครเมื่อ</th>
                <th className="text-left px-4 py-3 font-medium">โหมดบันทึกด่วน</th>
                <th className="text-left px-4 py-3 font-medium">ยอดงบ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                    กำลังโหลด...
                  </td>
                </tr>
              )}

              {!isLoading && users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                    ไม่พบผู้ใช้ตามเงื่อนไขที่ค้นหา
                  </td>
                </tr>
              )}

              {!isLoading &&
                users.map((user) => (
                  <tr key={user.line_user_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {user.picture_url ? (
                          <img
                            src={user.picture_url}
                            alt=""
                            className="w-8 h-8 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-gray-200" />
                        )}
                        <div className="min-w-0">
                          <p className="font-medium text-gray-800">
                            {user.display_name ?? "ไม่ระบุชื่อ"}
                          </p>
                          <p className="text-xs text-gray-400 truncate max-w-64">
                            {user.line_user_id}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-md text-xs font-semibold ${
                          user.is_onboarded
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        {user.is_onboarded ? "ตั้งค่าแล้ว" : "ยังไม่ตั้งค่า"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggle(user)}
                        disabled={busyId === user.line_user_id}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
                          user.use_bypass_mode ? "bg-blue-600" : "bg-gray-200"
                        }`}
                        aria-checked={user.use_bypass_mode}
                        role="switch"
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            user.use_bypass_mode ? "translate-x-6" : "translate-x-1"
                          }`}
                        />
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleSyncBudgets(user)}
                        disabled={busyId === user.line_user_id}
                        className="px-3 py-1.5 rounded-lg border border-gray-200 text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50 whitespace-nowrap"
                      >
                        ซ่อมยอดงบ
                      </button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between px-4 py-3 bg-gray-50 text-sm text-gray-500">
          <span>
            แสดง {from}-{to} จาก {total} คน
          </span>
          <div className="flex gap-2">
            <button
              onClick={prevPage}
              disabled={offset === 0}
              className="p-2 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-white"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={nextPage}
              disabled={offset + PAGE_SIZE >= total}
              className="p-2 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-white"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
