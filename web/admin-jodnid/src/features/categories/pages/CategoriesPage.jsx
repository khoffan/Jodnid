import { useEffect, useState } from "react";
import { FolderTree, Pencil, Plus, Trash2, X } from "lucide-react";
import useCategoriesStore from "../store/categories.store";

const EMPTY_FORM = { name: "", icon: "📁", parent_id: "" };

export const CategoriesPage = () => {
  const { categories, isLoading, error, fetchCategories, createCategory, updateCategory, deleteCategory } =
    useCategoriesStore();
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const parents = categories.filter((category) => !category.parent_id);

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = editingId
      ? await updateCategory(editingId, { name: form.name, icon: form.icon })
      : await createCategory({
          name: form.name,
          icon: form.icon,
          parent_id: form.parent_id ? Number(form.parent_id) : null,
        });

    if (!result.success) {
      alert(result.error);
      return;
    }
    resetForm();
  };

  const handleEdit = (category) => {
    setEditingId(category.id);
    setForm({ name: category.name, icon: category.icon ?? "📁", parent_id: "" });
  };

  const handleDelete = async (category) => {
    if (!confirm(`ยืนยันลบหมวดหมู่ "${category.name}"?`)) return;
    const result = await deleteCategory(category.id);
    if (!result.success) {
      alert(result.error);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FolderTree className="text-blue-500" /> หมวดหมู่ส่วนกลาง
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          หมวดหมู่ที่ผู้ใช้ทุกคนเห็น เพิ่มที่นี่แล้ว AI จะนำไปใช้จัดหมวดหมู่ให้เองอัตโนมัติ
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex flex-wrap gap-3 items-end bg-white border border-gray-100 rounded-xl p-4 shadow-sm"
      >
        <div>
          <label className="block text-xs text-gray-500 mb-1">ไอคอน</label>
          <input
            value={form.icon}
            onChange={(e) => setForm({ ...form, icon: e.target.value })}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-20 text-center"
            maxLength={4}
          />
        </div>
        <div className="flex-1 min-w-48">
          <label className="block text-xs text-gray-500 mb-1">ชื่อหมวดหมู่</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="เช่น สุขภาพและความงาม"
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
            required
          />
        </div>
        {!editingId && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">อยู่ใต้หมวดหมู่</label>
            <select
              value={form.parent_id}
              onChange={(e) => setForm({ ...form, parent_id: e.target.value })}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
            >
              <option value="">— เป็นหมวดหมู่หลัก —</option>
              {parents.map((parent) => (
                <option key={parent.id} value={parent.id}>
                  {parent.icon} {parent.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <button
          type="submit"
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600"
        >
          <Plus size={16} />
          {editingId ? "บันทึกการแก้ไข" : "เพิ่มหมวดหมู่"}
        </button>
        {editingId && (
          <button
            type="button"
            onClick={resetForm}
            className="flex items-center gap-2 px-3 py-2 text-gray-500 rounded-lg text-sm hover:bg-gray-100"
          >
            <X size={16} /> ยกเลิก
          </button>
        )}
      </form>

      {error && (
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading && <p className="px-4 py-8 text-center text-gray-400 text-sm">กำลังโหลด...</p>}

        {!isLoading && categories.length === 0 && (
          <p className="px-4 py-8 text-center text-gray-400 text-sm">ยังไม่มีหมวดหมู่ส่วนกลาง</p>
        )}

        <ul className="divide-y divide-gray-100">
          {!isLoading &&
            categories.map((category) => (
              <li key={category.id} className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
                <span className="text-xl w-8 text-center">{category.icon ?? "📁"}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800">{category.name}</p>
                  {category.parent_name && (
                    <p className="text-xs text-gray-400">อยู่ใต้ {category.parent_name}</p>
                  )}
                </div>
                <button
                  onClick={() => handleEdit(category)}
                  className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50"
                  title="แก้ไข"
                >
                  <Pencil size={16} />
                </button>
                <button
                  onClick={() => handleDelete(category)}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                  title="ลบ"
                >
                  <Trash2 size={16} />
                </button>
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
};
