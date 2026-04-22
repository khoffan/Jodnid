import { useState } from "react";
import { Plus, Save, X } from "lucide-react";
import useConfigStore from "../store/system-config.store";

export const CreateConfigModal = ({ isOpen, onOpenChange }) => {
  const createConfig = useConfigStore((state) => state.createConfig);
  const [formData, setFormData] = useState({
    name: "",
    key: "",
    value: "",
    value_type: "string",
    description: "",
  });

  if (!isOpen) return null;

  const close = () => onOpenChange(false);

  const handleSubmit = async () => {
    const keyRegex = /^[a-z0-9_]+$/;
    if (!keyRegex.test(formData.key)) {
      alert("Key ต้องเป็นตัวเล็กและใช้ _ เท่านั้น (snake_case)");
      return;
    }

    const result = await createConfig(formData);
    if (result.success) {
      close();
      setFormData({
        name: "",
        key: "",
        value: "",
        value_type: "string",
        description: "",
      });
    } else {
      alert(result.error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div 
        className="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-config-modal-title"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2 text-blue-500">
            <Plus size={20} />
            <h2 id="create-config-modal-title" className="font-bold text-xl text-gray-800">
              สร้าง Configuration ใหม่
            </h2>
          </div>
          <button 
            onClick={close} 
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Display Name</label>
            <input
              type="text"
              placeholder="เช่น เปิดปิดระบบ OCR"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">System Key (snake_case)</label>
            <input
              type="text"
              placeholder="เช่น is_ocr_active"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              value={formData.key}
              onChange={(e) => setFormData({ ...formData, key: e.target.value })}
            />
          </div>

          <div className="flex gap-3">
            <div className="space-y-1 w-1/3">
              <label className="text-sm font-medium text-gray-700">Type</label>
              <select
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                value={formData.value_type}
                onChange={(e) => setFormData({ ...formData, value_type: e.target.value })}
              >
                <option value="string">String</option>
                <option value="boolean">Boolean</option>
                <option value="int">Integer</option>
                <option value="json">JSON</option>
              </select>
            </div>
            
            <div className="space-y-1 flex-1">
              <label className="text-sm font-medium text-gray-700">Value</label>
              <input
                type="text"
                placeholder="ค่าเริ่มต้น"
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                value={formData.value}
                onChange={(e) => setFormData({ ...formData, value: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Description</label>
            <textarea
              placeholder="คำอธิบายการใช้งาน..."
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm min-h-[80px]"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
            onClick={handleSubmit}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-blue-500 hover:bg-blue-600 rounded-lg shadow-md shadow-blue-500/30 transition-colors"
          >
            <Save size={16} />
            ยืนยันการสร้าง
          </button>
        </div>
      </div>
    </div>
  );
};
