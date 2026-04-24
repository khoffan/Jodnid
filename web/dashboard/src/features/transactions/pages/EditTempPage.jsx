import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import { Trash2, Plus, Save } from "lucide-react";
import api from "../../../common/lib/api";

export const EditTempPage = ({ userId }) => {
  const { tempId } = useParams();
  const navigate = useNavigate();
  const [items, setItems] = useState([]); // เก็บ array จาก raw_data
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/api/temp-transaction/${tempId}`).then((res) => {
      setItems(res.data.raw_data || []);
      setLoading(false);
    });
    api.get(`/api/categories/parent`).then((res) => {
      setCategories(res.data);
    });
  }, [tempId]);

  // ฟังก์ชันแก้ไขค่าในแต่ละ Row
  const updateItem = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  };

  // ลบบางรายการที่ไม่ต้องการ
  const removeItem = (index) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleConfirmAll = async () => {
    try {
      // ส่ง items ทั้งหมดที่แก้ไขแล้วกลับไปบันทึกลง DB จริง
      await api.post(`/api/transactions/confirm-bulk`, {
        user_id: userId,
        temp_id: tempId,
        items: items,
      });
      navigate("/summary/daily");
    } catch (e) {
      alert("บันทึกไม่สำเร็จ");
      console.error(e);
    }
  };

  if (loading)
    return <div className="p-10 text-center">กำลังโหลดข้อมูลดิบ...</div>;

  return (
    <div className="p-4 max-w-md mx-auto pb-24">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-black text-slate-800">
          ตรวจสอบความถูกต้อง
        </h2>
        <span className="text-[10px] bg-amber-100 text-amber-600 px-2 py-1 rounded-full font-bold">
          {items.length} รายการ
        </span>
      </div>

      <div className="space-y-4">
        {items.map((item, index) => (
          <div
            key={index}
            className="bg-white p-5 rounded-[2rem] shadow-sm border border-slate-100 relative group"
          >
            {/* ปุ่มลบรายการย่อย */}
            <button
              onClick={() => removeItem(index)}
              className="absolute -top-2 -right-2 bg-red-50 text-red-400 p-2 rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Trash2 size={14} />
            </button>

            <div className="grid grid-cols-1 gap-3">
              <input
                placeholder="ชื่อรายการ"
                className="w-full text-sm font-bold bg-slate-50 border-none rounded-xl p-2.5 focus:ring-2 ring-indigo-500"
                value={item.item}
                onChange={(e) => updateItem(index, "item", e.target.value)}
              />

              <div className="flex gap-2">
                <div className="relative flex-1">
                  <span className="absolute left-3 top-2.5 text-slate-400 text-sm">
                    ฿
                  </span>
                  <input
                    type="number"
                    className="w-full pl-7 p-2.5 bg-slate-50 border-none rounded-xl text-sm font-black focus:ring-2 ring-indigo-500"
                    value={item.amount}
                    onChange={(e) =>
                      updateItem(index, "amount", Number(e.target.value))
                    }
                  />
                </div>

                <select
                  className="flex-1 p-2.5 bg-slate-50 border-none rounded-xl text-[10px] font-bold focus:ring-2 ring-indigo-500"
                  value={item.category}
                  onChange={(e) =>
                    updateItem(index, "category", e.target.value)
                  }
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.name}>
                      {cat.emoji} {cat.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ปุ่มเพิ่มแถวใหม่ (เผื่อ AI สกัดมาไม่ครบ) */}
      <button
        onClick={() =>
          setItems([
            ...items,
            { item: "", amount: 0, category: "อาหาร", type: "expense" },
          ])
        }
        className="w-full mt-4 py-3 border-2 border-dashed border-slate-200 rounded-3xl text-slate-400 text-xs font-bold flex items-center justify-center gap-2 active:bg-slate-50"
      >
        <Plus size={16} /> เพิ่มรายการอื่น
      </button>

      {/* Bottom Action Bar */}
      <div className="fixed bottom-6 left-0 right-0 px-4">
        <button
          onClick={handleConfirmAll}
          className="w-full py-4 bg-slate-900 text-white rounded-[2rem] font-black shadow-xl flex items-center justify-center gap-3 active:scale-95 transition-transform"
        >
          <Save size={20} />
          บันทึกทั้งหมดลงบัญชี
        </button>
      </div>
    </div>
  );
};
