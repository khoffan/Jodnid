import { adminItems } from "./mockData";

export const AdministratorTab = () => {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Administrator Tasks</h2>
        <p className="text-sm text-slate-500">งานสำคัญสำหรับผู้ดูแลระบบ</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {adminItems.map((item) => (
          <div key={item.title} className="rounded-xl border border-gray-200 bg-slate-50 p-4">
            <h3 className="text-base font-semibold text-slate-900">{item.title}</h3>
            <p className="mt-2 text-sm text-slate-500">{item.description}</p>
            <span className="mt-4 inline-flex rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700 border border-gray-200">
              {item.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
