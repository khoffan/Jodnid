import { Edit3 } from "lucide-react";

export const ConfigTable = ({ configs, onEdit, onToggle }) => {
  const handleToggle = (config) => {
    if (onToggle) {
      const newValue = config.value === "true" ? "false" : "true";
      onToggle(config.key, newValue);
    }
  };

  if (!configs || configs.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500">
        ไม่พบข้อมูลการตั้งค่า
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-xl">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-100">
            <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
              CONFIGURATION
            </th>
            <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
              VALUE
            </th>
            <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
              DESCRIPTION
            </th>
            <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider text-center">
              ACTIONS
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-50">
          {configs.map((config) => (
            <tr
              key={config.key}
              className="hover:bg-gray-50/50 transition-colors"
            >
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex flex-col">
                  <p className="text-sm font-bold text-gray-800">
                    {config.name}
                  </p>
                  <p className="text-xs text-gray-400 font-mono tracking-tighter">
                    {config.key}
                  </p>
                </div>
              </td>
              <td className="px-6 py-4">
                {config.value_type === "boolean" ? (
                  <div className="flex items-center">
                    <button
                      type="button"
                      onClick={() => handleToggle(config)}
                      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        config.value === "true" ? "bg-blue-600" : "bg-gray-200"
                      }`}
                      role="switch"
                      aria-checked={config.value === "true"}
                    >
                      <span
                        aria-hidden="true"
                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          config.value === "true"
                            ? "translate-x-5"
                            : "translate-x-0"
                        }`}
                      />
                    </button>
                    <span
                      className={`ml-3 text-xs font-medium ${config.value === "true" ? "text-blue-600" : "text-gray-400"}`}
                    >
                      {config.value === "true" ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                ) : (
                  <div className="inline-block px-2.5 py-1 rounded-md bg-gray-50 border border-gray-200 shadow-sm">
                    <code className="text-xs font-mono text-gray-600">
                      {config.value}
                    </code>
                  </div>
                )}
              </td>
              <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                {config.description}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-center">
                <button
                  type="button"
                  title="แก้ไขการตั้งค่า"
                  onClick={() => onEdit(config)}
                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors focus:outline-none"
                >
                  <Edit3 size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
