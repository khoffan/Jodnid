import { mockUsers } from "./mockData";

export const UsersTab = () => {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Users</h2>
        <p className="text-sm text-slate-500">รายชื่อผู้ใช้ตัวอย่างสำหรับหน้าจอนี้</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-slate-600">ID</th>
              <th className="px-4 py-3 text-slate-600">Name</th>
              <th className="px-4 py-3 text-slate-600">Email</th>
              <th className="px-4 py-3 text-slate-600">Role</th>
              <th className="px-4 py-3 text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {mockUsers.map((user) => (
              <tr
                key={user.id}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 text-slate-700 font-mono">{user.id}</td>
                <td className="px-4 py-3 text-slate-700">{user.name}</td>
                <td className="px-4 py-3 text-slate-500">{user.email}</td>
                <td className="px-4 py-3 text-slate-700">{user.role}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 border border-gray-200">
                    {user.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
