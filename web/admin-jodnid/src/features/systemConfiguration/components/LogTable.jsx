import React, { useEffect, useState } from "react";
import useLogsStore from "../store/system-logs.store";
import LogDetailModal from "./LogDetailModal";

export const LogTable = () => {
  const { logs, page, per_page, total, isLoading, fetchLogs, fetchLogById } = useLogsStore();
  const [open, setOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    fetchLogs({ page: 1 });
  }, [fetchLogs]);

  const openDetail = async (id) => {
    const data = await fetchLogById(id);
    setSelectedLog(data);
    setOpen(true);
  };

  return (
    <div>
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-lg font-semibold">Application Logs</h2>
      </div>

      <div className="overflow-x-auto bg-white border border-gray-200 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="p-2 text-left text-slate-700">Timestamp</th>
              <th className="p-2 text-left text-slate-700">Level</th>
              <th className="p-2 text-left text-slate-700">Module</th>
              <th className="p-2 text-left text-slate-700">Message</th>
              <th className="p-2 text-slate-700">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={5} className="p-4 text-center text-slate-600">
                  Loading...
                </td>
              </tr>
            )}
            {!isLoading && logs.length === 0 && (
              <tr>
                <td colSpan={5} className="p-4 text-center text-slate-600">
                  No logs
                </td>
              </tr>
            )}
            {!isLoading &&
              logs.map((l) => (
                <tr key={l.id} className="border-t border-gray-200">
                  <td className="p-2 font-mono text-xs text-slate-700">{l.timestamp}</td>
                  <td className="p-2 text-slate-700">{l.level}</td>
                  <td className="p-2 text-slate-700">{l.module}</td>
                  <td className="p-2 truncate max-w-md text-slate-700">{l.message}</td>
                  <td className="p-2">
                    <button
                      onClick={() => openDetail(l.id)}
                      className="text-black hover:text-slate-700"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <LogDetailModal isOpen={open} onClose={() => setOpen(false)} log={selectedLog} />
    </div>
  );
};

export default LogTable;
