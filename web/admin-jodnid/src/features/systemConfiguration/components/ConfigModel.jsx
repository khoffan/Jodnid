import { Save, Info, X } from "lucide-react";
import { useState, useEffect } from "react";

export const ConfigModal = ({
  isOpen,
  onOpenChange,
  selectedConfig,
  onSave,
}) => {
  const [localName, setLocalName] = useState("");
  const [localValue, setLocalValue] = useState("");
  const [localDesc, setLocalDesc] = useState("");

  useEffect(() => {
    if (selectedConfig) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLocalName(selectedConfig.name || "");
      setLocalValue(selectedConfig.value || "");
      setLocalDesc(selectedConfig.description || "");
    }
  }, [selectedConfig]);

  if (!isOpen) return null;

  const close = () => onOpenChange(false);

  const handleSave = () => {
    onSave({
      ...selectedConfig,
      name: localName,
      value: localValue,
      description: localDesc,
    });
    close();
  };

  const isBoolean = selectedConfig?.value_type === "boolean";
  const isEnabled = localValue === "true";

  const toggleBoolean = () => {
    setLocalValue(isEnabled ? "false" : "true");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <div className="flex items-center gap-2 text-blue-500">
              <Info size={18} />
              <h2 className="font-bold text-lg text-gray-800">
                แก้ไขการตั้งค่า
              </h2>
            </div>
            <p className="text-xs text-gray-400 mt-1">{selectedConfig?.name}</p>
          </div>
          <button
            onClick={close}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors self-start"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* เปิดการแก้ไข name */}
          <div>
            <label className="text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              placeholder="กรอกชื่อการตั้งค่า..."
              value={selectedConfig.name}
              onChange={(e) => setLocalName(e.target.value)}
            />
            <p className="text-xs text-gray-500">
              Name เป็นค่าคงที่ของระบบ ไม่สามารถแก้ไขได้
            </p>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">
              System Key
            </label>
            <input
              type="text"
              readOnly
              className="w-full px-3 py-2 bg-gray-100 border border-gray-200 rounded-lg text-red-500 font-mono text-sm cursor-not-allowed"
              value={selectedConfig?.key || ""}
            />
          </div>

          {isBoolean ? (
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-xl border border-gray-100">
              <div className="flex flex-col">
                <span className="text-sm font-medium text-gray-800">
                  สถานะการใช้งาน
                </span>
                <span className="text-xs text-gray-500">
                  เปิดหรือปิดฟีเจอร์นี้ในระบบ
                </span>
              </div>
              <button
                type="button"
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${isEnabled ? "bg-green-500" : "bg-gray-300"}`}
                onClick={toggleBoolean}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isEnabled ? "translate-x-6" : "translate-x-1"}`}
                />
              </button>
            </div>
          ) : (
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">Value</label>
              <input
                type="text"
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                placeholder="กรอกค่าการตั้งค่า..."
                value={localValue}
                onChange={(e) => setLocalValue(e.target.value)}
              />
            </div>
          )}

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm min-h-[80px]"
              placeholder="อธิบายว่า Config นี้ใช้ทำอะไร..."
              value={localDesc}
              onChange={(e) => setLocalDesc(e.target.value)}
            />
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-2 bg-gray-50/50">
          <button
            onClick={close}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-blue-500 hover:bg-blue-600 rounded-lg shadow-md shadow-blue-500/30 transition-colors"
          >
            <Save size={16} />
            บันทึกการเปลี่ยนแปลง
          </button>
        </div>
      </div>
    </div>
  );
};
