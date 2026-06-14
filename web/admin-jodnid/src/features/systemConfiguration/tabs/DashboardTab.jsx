import { dashboardCards } from "./mockData";

export const DashboardTab = () => {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Dashboard</h2>
        <p className="text-sm text-slate-500">ภาพรวมระบบแบบเรียลไทม์</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {dashboardCards.map((card) => (
          <div
            key={card.label}
            className="rounded-xl border border-gray-200 bg-slate-50 p-4 shadow-sm"
          >
            <p className="text-xs uppercase tracking-widest text-slate-500">{card.label}</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{card.value}</p>
            <p className="mt-2 text-sm text-slate-500">{card.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
