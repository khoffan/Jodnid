import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, RefreshCw, ScrollText } from "lucide-react";
import useMonitoringStore, { PAGE_SIZE } from "../store/monitoring.store";

const LEVEL_STYLE = {
  ERROR: "bg-red-100 text-red-700",
  CRITICAL: "bg-red-200 text-red-900",
  WARNING: "bg-amber-100 text-amber-700",
  INFO: "bg-blue-100 text-blue-700",
};

const formatTime = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("th-TH");
};

export const SystemLogPage = () => {
  const {
    logs,
    logTotal,
    logOffset,
    logModules,
    filters,
    isLoading,
    error,
    fetchLogs,
    setFilter,
    nextPage,
    prevPage,
  } = useMonitoringStore();
  const [expandedId, setExpandedId] = useState(null);
  const [searchDraft, setSearchDraft] = useState("");

  useEffect(() => {
    fetchLogs(0);
  }, [fetchLogs]);

  const from = logTotal === 0 ? 0 : logOffset + 1;
  const to = Math.min(logOffset + PAGE_SIZE, logTotal);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ScrollText className="text-blue-500" /> System Log
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            ดู telemetry ของ OCR และข้อผิดพลาดที่เกิดขึ้นจริงโดยไม่ต้องเปิดฐานข้อมูล
          </p>
        </div>
        <button
          onClick={() => fetchLogs(logOffset)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors font-medium rounded-lg text-sm"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="flex flex-wrap gap-3 items-center bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
        <select
          value={filters.level}
          onChange={(e) => setFilter({ level: e.target.value })}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
        >
          <option value="">ทุกระดับ</option>
          <option value="INFO">INFO</option>
          <option value="ERROR">ERROR</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>

        <select
          value={filters.module}
          onChange={(e) => setFilter({ module: e.target.value })}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm max-w-56"
        >
          <option value="">ทุก module</option>
          {logModules.map((moduleName) => (
            <option key={moduleName} value={moduleName}>
              {moduleName}
            </option>
          ))}
        </select>

        <form
          className="flex gap-2 flex-1 min-w-56"
          onSubmit={(e) => {
            e.preventDefault();
            setFilter({ search: searchDraft });
          }}
        >
          <input
            value={searchDraft}
            onChange={(e) => setSearchDraft(e.target.value)}
            placeholder="ค้นหาในข้อความ..."
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm flex-1"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600"
          >
            ค้นหา
          </button>
        </form>
      </div>

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
                <th className="text-left px-4 py-3 font-medium">เวลา</th>
                <th className="text-left px-4 py-3 font-medium">ระดับ</th>
                <th className="text-left px-4 py-3 font-medium">Module</th>
                <th className="text-left px-4 py-3 font-medium">ข้อความ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                    กำลังโหลด...
                  </td>
                </tr>
              )}

              {!isLoading && logs.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                    ไม่พบข้อมูลตามเงื่อนไขที่เลือก
                  </td>
                </tr>
              )}

              {!isLoading &&
                logs.map((log) => (
                  <tr
                    key={log.id}
                    onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                    className="hover:bg-gray-50 cursor-pointer align-top"
                  >
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {formatTime(log.timestamp)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-md text-xs font-semibold ${
                          LEVEL_STYLE[log.level] ?? "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {log.level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{log.module}</td>
                    <td className="px-4 py-3 text-gray-800">
                      <p className="break-words">{log.message}</p>
                      {expandedId === log.id && (
                        <div className="mt-2 space-y-2">
                          {log.user_id && (
                            <p className="text-xs text-gray-400">user: {log.user_id}</p>
                          )}
                          {log.payload && (
                            <pre className="bg-gray-900 text-gray-100 rounded-lg p-3 text-xs overflow-x-auto">
                              {JSON.stringify(log.payload, null, 2)}
                            </pre>
                          )}
                          {log.stack_trace && (
                            <pre className="bg-red-50 text-red-700 rounded-lg p-3 text-xs overflow-x-auto">
                              {log.stack_trace}
                            </pre>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between px-4 py-3 bg-gray-50 text-sm text-gray-500">
          <span>
            แสดง {from}-{to} จาก {logTotal} รายการ
          </span>
          <div className="flex gap-2">
            <button
              onClick={prevPage}
              disabled={logOffset === 0}
              className="p-2 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-white"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={nextPage}
              disabled={logOffset + PAGE_SIZE >= logTotal}
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
