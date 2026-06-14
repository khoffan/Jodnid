import { mockConfigs } from "./mockData";

export const ConfigTab = () => {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">System Configuration</h2>
        <p className="text-sm text-slate-500">ค่าตั้งต้นจาก mock data สำหรับหน้า config</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-slate-600">Name</th>
              <th className="px-4 py-3 text-slate-600">Key</th>
              <th className="px-4 py-3 text-slate-600">Value</th>
              <th className="px-4 py-3 text-slate-600">Description</th>
            </tr>
          </thead>
          <tbody>
            {mockConfigs.map((config) => (
              <tr
                key={config.key}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 text-slate-700 font-medium">{config.name}</td>
                <td className="px-4 py-3 text-slate-500 font-mono text-xs">{config.key}</td>
                <td className="px-4 py-3 text-slate-700">{config.value}</td>
                <td className="px-4 py-3 text-slate-500">{config.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
