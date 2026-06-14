import React from "react";

export const LogDetailModal = ({ isOpen, onClose, log }) => {
  if (!isOpen || !log) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white rounded-lg w-11/12 md:w-3/4 p-6 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Log detail</h3>
          <button onClick={onClose} className="text-gray-500">
            Close
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-xs text-gray-500">Timestamp</p>
            <p className="font-mono text-sm">{log.timestamp}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Level / Module</p>
            <p>
              {log.level} — {log.module}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Message</p>
            <p>{log.message}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Payload</p>
            <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
              {JSON.stringify(log.payload, null, 2)}
            </pre>
          </div>
          {log.stack_trace && (
            <div>
              <p className="text-xs text-gray-500">Stack trace</p>
              <pre className="bg-black text-white p-2 rounded text-xs overflow-auto max-h-64">
                {log.stack_trace}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogDetailModal;
