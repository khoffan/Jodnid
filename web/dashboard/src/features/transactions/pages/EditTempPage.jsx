import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import { Trash2, Plus, Save, X } from "lucide-react";
import api from "../../../common/lib/api";

// ยอมให้ยอดรวมต่างจากใบเสร็จได้ไม่เกินนี้ (ตรงกับ BILLABLE_TOTAL_TOLERANCE ฝั่ง backend) — ใช้แสดงคำเตือนเท่านั้น
const TOTAL_TOLERANCE = 1;
const FALLBACK_CATEGORY = "อื่นๆ";

// LLM อาจส่งหมวดมาเป็น "🍔 อาหารและเครื่องดื่ม" → จับคู่กับชื่อหมวดจริงแบบเดียวกับตอนบันทึก (คำสุดท้าย)
const normalizeCategory = (value, names) => {
  const raw = String(value || "").trim();
  if (names.includes(raw)) return raw;
  const last = raw.split(" ").pop();
  if (names.includes(last)) return last;
  return names.includes(FALLBACK_CATEGORY) ? FALLBACK_CATEGORY : names[0] || "";
};

const toAmount = (value) => {
  const n = parseFloat(value);
  return Number.isFinite(n) ? n : 0;
};

const errorDetail = (error, fallback) => error?.response?.data?.detail || fallback;

export const EditTempPage = ({ userId }) => {
  const { tempId } = useParams();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [grandTotal, setGrandTotal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const categoryNames = categories.map((cat) => cat.name);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tempRes, categoryRes] = await Promise.all([
          api.get(`/api/temp-transaction/${tempId}`),
          api.get(`/api/categories/parent`),
        ]);
        const names = (categoryRes.data || []).map((cat) => cat.name);
        // backend คัดให้แล้วเหลือเฉพาะบรรทัดที่จะบันทึกจริง (ไม่มีบรรทัดยอดรวมย่อย)
        const editable = (tempRes.data.items || []).map((item) => ({
          ...item,
          category: normalizeCategory(item.category, names),
        }));
        setCategories(categoryRes.data || []);
        setItems(editable);
        setGrandTotal(tempRes.data.grand_total ?? null);
      } catch (e) {
        console.error(e);
        setLoadError(errorDetail(e, "ไม่สามารถดึงข้อมูลได้"));
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [tempId]);

  const updateItem = (index, field, value) => {
    setItems(items.map((item, i) => (i === index ? { ...item, [field]: value } : item)));
  };

  const removeItem = (index) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const addItem = () => {
    setItems([
      ...items,
      {
        item: "",
        amount: 0,
        category: normalizeCategory(FALLBACK_CATEGORY, categoryNames),
        is_actual_item: true,
        priority: false,
      },
    ]);
  };

  const total = items.reduce((sum, item) => sum + toAmount(item.amount), 0);
  const totalMismatch = grandTotal !== null && Math.abs(total - grandTotal) > TOTAL_TOLERANCE;

  const handleConfirmAll = async () => {
    const toSave = items
      .filter((item) => toAmount(item.amount) > 0)
      .map((item) => ({ ...item, amount: toAmount(item.amount) }));
    if (toSave.length === 0) {
      setSaveError("กรุณาใส่จำนวนเงินอย่างน้อย 1 รายการ");
      return;
    }

    setSaving(true);
    setSaveError(null);
    try {
      await api.post(`/api/transactions/confirm-bulk`, {
        user_id: userId,
        temp_id: tempId,
        items: toSave,
      });
      navigate("/summary/daily");
    } catch (e) {
      console.error(e);
      setSaveError(errorDetail(e, "บันทึกไม่สำเร็จ กรุณาลองใหม่อีกครั้ง"));
      setSaving(false);
    }
  };

  const handleCancel = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      await api.delete(`/api/temp-transaction/${tempId}`);
      navigate("/", { replace: true });
    } catch (e) {
      console.error(e);
      setSaveError(errorDetail(e, "ยกเลิกไม่สำเร็จ กรุณาลองใหม่อีกครั้ง"));
      setSaving(false);
    }
  };

  if (loading) return <div className="p-10 text-center">กำลังโหลดข้อมูล...</div>;

  if (loadError) {
    return (
      <div className="p-6 text-center space-y-4">
        <p className="text-sm text-red-600">⚠️ {loadError}</p>
        <button
          onClick={() => navigate("/", { replace: true })}
          className="px-5 py-2.5 bg-slate-900 text-white rounded-2xl text-sm font-bold"
        >
          กลับหน้าหลัก
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-md mx-auto pb-40">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-black text-slate-800">ตรวจสอบความถูกต้อง</h2>
        <span className="text-[10px] bg-amber-100 text-amber-600 px-2 py-1 rounded-full font-bold">
          {items.length} รายการ
        </span>
      </div>

      <div className="space-y-4">
        {items.map((item, index) => (
          <div
            key={index}
            className="bg-white p-5 rounded-[2rem] shadow-sm border border-slate-100 relative"
          >
            {/* ปุ่มลบรายการย่อย — แสดงตลอด เพราะบนมือถือไม่มี hover */}
            <button
              onClick={() => removeItem(index)}
              aria-label="ลบรายการ"
              className="absolute -top-2 -right-2 bg-red-50 text-red-400 p-2 rounded-full shadow-sm"
            >
              <Trash2 size={14} />
            </button>

            <div className="grid grid-cols-1 gap-3">
              <input
                placeholder="ชื่อรายการ"
                className="w-full text-sm font-bold bg-slate-50 border-none rounded-xl p-2.5 focus:ring-2 ring-indigo-500"
                value={item.item || ""}
                onChange={(e) => updateItem(index, "item", e.target.value)}
              />

              <div className="flex gap-2">
                <div className="relative flex-1">
                  <span className="absolute left-3 top-2.5 text-slate-400 text-sm">฿</span>
                  <input
                    type="text"
                    inputMode="decimal"
                    className="w-full pl-7 p-2.5 bg-slate-50 border-none rounded-xl text-sm font-black focus:ring-2 ring-indigo-500"
                    placeholder="0.00"
                    value={item.amount === 0 ? "" : item.amount}
                    onChange={(e) => {
                      const val = e.target.value;
                      // เก็บเป็น string ระหว่างพิมพ์ เพื่อให้พิมพ์จุดทศนิยมได้ แปลงเป็นตัวเลขตอนบันทึก
                      if (val === "" || /^[0-9]*\.?[0-9]*$/.test(val)) {
                        updateItem(index, "amount", val === "" ? 0 : val);
                      }
                    }}
                  />
                </div>

                <select
                  className="flex-1 p-2.5 bg-slate-50 border-none rounded-xl text-[10px] font-bold focus:ring-2 ring-indigo-500"
                  value={item.category}
                  onChange={(e) => updateItem(index, "category", e.target.value)}
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.name}>
                      {cat.icon} {cat.name}
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
        onClick={addItem}
        className="w-full mt-4 py-3 border-2 border-dashed border-slate-200 rounded-3xl text-slate-400 text-xs font-bold flex items-center justify-center gap-2 active:bg-slate-50"
      >
        <Plus size={16} /> เพิ่มรายการอื่น
      </button>

      {/* Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 px-4 pb-6 pt-3 bg-white/95 space-y-2">
        <div className="flex justify-between text-sm font-bold text-slate-700">
          <span>ยอดรวม</span>
          <span>฿{total.toLocaleString("th-TH", { minimumFractionDigits: 2 })}</span>
        </div>
        {grandTotal !== null && (
          <p className={`text-xs ${totalMismatch ? "text-amber-600" : "text-slate-400"}`}>
            {totalMismatch
              ? `⚠️ ไม่ตรงกับยอดสุทธิบนใบเสร็จ ฿${grandTotal.toLocaleString("th-TH", { minimumFractionDigits: 2 })} — ตรวจสอบก่อนบันทึก`
              : `✅ ตรงกับยอดสุทธิบนใบเสร็จ`}
          </p>
        )}
        {saveError && <p className="text-xs text-red-600">⚠️ {saveError}</p>}
        <div className="flex gap-2">
          <button
            onClick={handleCancel}
            disabled={saving}
            className="px-4 py-4 bg-slate-100 text-slate-600 rounded-[2rem] font-bold flex items-center justify-center gap-1 disabled:opacity-50"
          >
            <X size={18} />
            ยกเลิก
          </button>
          <button
            onClick={handleConfirmAll}
            disabled={saving}
            className="flex-1 py-4 bg-slate-900 text-white rounded-[2rem] font-black shadow-xl flex items-center justify-center gap-3 active:scale-95 transition-transform disabled:opacity-50"
          >
            <Save size={20} />
            {saving ? "กำลังบันทึก..." : "บันทึกทั้งหมดลงบัญชี"}
          </button>
        </div>
      </div>
    </div>
  );
};
