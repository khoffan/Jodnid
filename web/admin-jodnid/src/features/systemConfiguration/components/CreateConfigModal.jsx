import { useState } from "react";
import { Plus, Save, X } from "lucide-react";
import useConfigStore from "../store/system-config.store";
import Switch from "../../../common/components/Switch";

const EMPTY_FORM = { name: "", key: "", value: "", value_type: "string", description: "" };
const NO_ERRORS = { name: "", key: "", value: "", value_type: "", description: "" };

export const CreateConfigModal = ({ isOpen, onOpenChange }) => {
  const createConfig = useConfigStore((state) => state.createConfig);
  const [useTextArea, setUseTextArea] = useState(false);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState(NO_ERRORS);

  if (!isOpen) return null;

  // ปิดแล้วล้างฟอร์ม — เปิดครั้งหน้าจะได้ไม่เห็นค่า/ข้อความ error ค้าง
  const close = () => {
    setFormData(EMPTY_FORM);
    setFormError(NO_ERRORS);
    setUseTextArea(false);
    onOpenChange(false);
  };

  // แสดง error ทีละช่อง และล้าง error ของช่องที่แก้แล้ว
  const fail = (field, message) => setFormError({ ...NO_ERRORS, [field]: message });

  const handleSubmit = async () => {
    const keyRegex = /^[a-z0-9_]+$/;
    if (!formData.name) return fail("name", "Display Name is required");
    if (!keyRegex.test(formData.key)) {
      return fail("key", "Key ต้องเป็นตัวเล็กและใช้ _ เท่านั้น (snake_case)");
    }
    // string ว่างได้ ชนิดอื่นต้องมีค่า (backend ตรวจรูปแบบตามชนิดอีกชั้น)
    if (!formData.value && formData.value_type !== "string") {
      return fail("value", "Value is required");
    }
    if (!formData.value_type) return fail("value_type", "Value type is required");
    if (!formData.description) return fail("description", "Description is required");

    setFormError(NO_ERRORS);
    const result = await createConfig(formData);
    if (result.success) {
      close();
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
            <h2
              id="create-config-modal-title"
              className="font-bold text-xl text-gray-800"
            >
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
            <label className="text-sm font-medium text-gray-700">
              Display Name
            </label>
            <input
              type="text"
              placeholder="เช่น เปิดปิดระบบ OCR"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
            />
            {formError.name && (
              <p className="text-red-500 text-sm">{formError.name}</p>
            )}
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">
              System Key (snake_case)
            </label>
            <input
              type="text"
              placeholder="เช่น is_ocr_active"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              value={formData.key}
              onChange={(e) =>
                setFormData({ ...formData, key: e.target.value })
              }
            />
            {formError.key && (
              <p className="text-red-500 text-sm">{formError.key}</p>
            )}
          </div>

          <div className="flex gap-3">
            <div className="space-y-1 w-1/3">
              <label className="text-sm font-medium text-gray-700">Type</label>
              <select
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                value={formData.value_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    value_type: e.target.value,
                    // boolean ใช้ select ที่แสดง True เป็นค่าแรก ต้องตั้งค่าให้ตรงกับที่เห็น
                    value: e.target.value === "boolean" ? "true" : "",
                  })
                }
              >
                <option value="string">String</option>
                <option value="boolean">Boolean</option>
                <option value="int">Integer</option>
                <option value="json">JSON</option>
              </select>
              {formError.value_type && (
                <p className="text-red-500 text-sm">{formError.value_type}</p>
              )}
            </div>

            <div className="space-y-1 flex-1">
              <div className="flex items-center gap-3">
                {/* Label บอกสถานะปัจจุบัน */}
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                  {useTextArea ? "Textarea" : "Input"}
                </span>

                {/* Switch Container */}
                {formData.value_type === "string" && (
                  <Switch onChange={setUseTextArea} value={useTextArea} />
                )}
              </div>
              {formData.value_type === "boolean" && (
                <select
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                  value={formData.value}
                  onChange={(e) =>
                    setFormData({ ...formData, value: e.target.value })
                  }
                >
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              )}
              {formData.value_type === "json" && (
                <textarea
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                  value={formData.value}
                  onChange={(e) =>
                    setFormData({ ...formData, value: e.target.value })
                  }
                />
              )}
              {useTextArea && formData.value_type === "string" && (
                <textarea
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                  value={formData.value}
                  onChange={(e) =>
                    setFormData({ ...formData, value: e.target.value })
                  }
                />
              )}
              {/* ช่องพิมพ์ธรรมดาสำหรับ int และ string แบบบรรทัดเดียว (boolean/json มีช่องของตัวเองด้านบน) */}
              {(formData.value_type === "int" ||
                (formData.value_type === "string" && !useTextArea)) && (
                <input
                  type="text"
                  placeholder="ค่าเริ่มต้น"
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                  value={formData.value}
                  onChange={(e) =>
                    setFormData({ ...formData, value: e.target.value })
                  }
                />
              )}
              {formError.value && (
                <p className="text-red-500 text-sm">{formError.value}</p>
              )}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              placeholder="คำอธิบายการใช้งาน..."
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm min-h-[80px]"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
            />
            {formError.description && (
              <p className="text-red-500 text-sm">{formError.description}</p>
            )}
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
