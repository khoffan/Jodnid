import { useState } from "react";
import { mockLogs } from "./mockData";

export const LogsTab = () => {
  const [selectedLog, setSelectedLog] = useState(null);

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white border border-gray-200 p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Application Logs</h2>
        <p className="text-sm text-slate-500">รายการบันทึกเหตุการณ์ล่าสุดในระบบ</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-slate-600">Timestamp</th>
              <th className="px-4 py-3 text-slate-600">Level</th>
              <th className="px-4 py-3 text-slate-600">Module</th>
              <th className="px-4 py-3 text-slate-600">Message</th>
              <th className="px-4 py-3 text-slate-600">Action</th>
            </tr>
          </thead>
          <tbody>
            {mockLogs.map((log) => (
              <tr
                key={log.id}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 font-mono text-xs text-slate-700">{log.timestamp}</td>
                <td className="px-4 py-3 text-slate-700">{log.level}</td>
                <td className="px-4 py-3 text-slate-700">{log.module}</td>
                <td className="px-4 py-3 truncate text-slate-700 max-w-xl">{log.message}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => setSelectedLog(log)}
                    className="text-sm font-medium text-black hover:text-slate-700"
                  >
                    Detail
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedLog && (
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900">Log detail</h3>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-gray-100 bg-slate-50 p-3">
              <p className="text-xs uppercase text-slate-500">Timestamp</p>
              <p className="text-sm text-slate-700">{selectedLog.timestamp}</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-slate-50 p-3">
              <p className="text-xs uppercase text-slate-500">Level</p>
              <p className="text-sm text-slate-700">{selectedLog.level}</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-slate-50 p-3">
              <p className="text-xs uppercase text-slate-500">Module</p>
              <p className="text-sm text-slate-700">{selectedLog.module}</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-slate-50 p-3">
              <p className="text-xs uppercase text-slate-500">Message</p>
              <p className="text-sm text-slate-700">{selectedLog.message}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
