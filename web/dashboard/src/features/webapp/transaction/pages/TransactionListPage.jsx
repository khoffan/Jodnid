import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { ChevronLeft, ChevronRight, Download, Pencil, Trash2, X } from "lucide-react";
import api from "../../../../common/lib/api";
import { useWebTransaction, WEB_PAGE_SIZE } from "../store/web.transaction.store";

const MONTHS = [
  "มกราคม",
  "กุมภาพันธ์",
  "มีนาคม",
  "เมษายน",
  "พฤษภาคม",
  "มิถุนายน",
  "กรกฎาคม",
  "สิงหาคม",
  "กันยายน",
  "ตุลาคม",
  "พฤศจิกายน",
  "ธันวาคม",
];

const money = (value) =>
  Number(value || 0).toLocaleString("th-TH", { minimumFractionDigits: 2 });

// วันที่แบบ YYYY-MM-DD ตามเวลาเครื่อง (toISOString เป็น UTC → ก่อน 07:00 จะได้เมื่อวาน)
const toLocalDate = (value) => {
  const d = new Date(value);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

const formatDate = (value) =>
  new Date(value).toLocaleDateString("th-TH", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

const EditTransactionModal = ({ tx, categories, onClose, onSaved }) => {
  const { updateTransaction } = useWebTransaction();
  const [form, setForm] = useState({
    item_name: tx.item_name,
    amount: String(tx.amount),
    category_id: tx.category_id ?? "",
    type: tx.transaction_type,
    date: toLocalDate(tx.transaction_date),
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    const result = await updateTransaction(tx.id, {
      ...form,
      amount: parseFloat(form.amount),
      category_id: form.category_id === "" ? undefined : Number(form.category_id),
    });
    setSaving(false);
    if (result.success) {
      onSaved();
    } else {
      setError(result.error);
    }
  };

  const input =
    "w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        onSubmit={handleSave}
        className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-800">แก้ไขรายการ</h2>
          <button type="button" onClick={onClose} aria-label="ปิด" className="p-1 text-gray-400">
            <X size={20} />
          </button>
        </div>

        <input
          className={input}
          value={form.item_name}
          onChange={(e) => setForm({ ...form, item_name: e.target.value })}
          placeholder="ชื่อรายการ"
          required
        />
        <div className="flex gap-2">
          <input
            className={input}
            inputMode="decimal"
            value={form.amount}
            onChange={(e) => {
              if (/^[0-9]*\.?[0-9]*$/.test(e.target.value)) {
                setForm({ ...form, amount: e.target.value });
              }
            }}
            placeholder="จำนวนเงิน"
            required
          />
          <select
            className={input}
            value={form.type}
            onChange={(e) => setForm({ ...form, type: e.target.value })}
          >
            <option value="expense">รายจ่าย</option>
            <option value="income">รายรับ</option>
          </select>
        </div>
        <div className="flex gap-2">
          <select
            className={input}
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          >
            {form.category_id === "" && <option value="">ไม่มีหมวดหมู่</option>}
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.icon} {cat.name}
              </option>
            ))}
          </select>
          <input
            type="date"
            className={input}
            value={form.date}
            max={toLocalDate(new Date())}
            onChange={(e) => setForm({ ...form, date: e.target.value })}
          />
        </div>

        {error && <p className="text-sm text-red-600">⚠️ {error}</p>}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 rounded-xl hover:bg-gray-100"
          >
            ยกเลิก
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 text-sm font-semibold text-white bg-green-600 rounded-xl hover:bg-green-700 disabled:opacity-50"
          >
            {saving ? "กำลังบันทึก..." : "บันทึก"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default function TransactionListPage() {
  const navigate = useNavigate();
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [categoryId, setCategoryId] = useState("");
  const [offset, setOffset] = useState(0);
  const [categories, setCategories] = useState([]);
  const [editing, setEditing] = useState(null);
  const [actionError, setActionError] = useState("");

  const { items, total, totals, loading, error, fetchTransactions, deleteTransaction, exportCsv } =
    useWebTransaction();

  useEffect(() => {
    api
      .get("/api/categories/parent")
      .then((res) => setCategories(res.data || []))
      .catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    fetchTransactions({ month, year, categoryId, offset });
  }, [month, year, categoryId, offset, fetchTransactions]);

  const reload = () => fetchTransactions({ month, year, categoryId, offset });

  // เปลี่ยนตัวกรองแล้วกลับไปหน้าแรกเสมอ
  const changeFilter = (setter) => (value) => {
    setter(value);
    setOffset(0);
  };

  const handleDelete = async (tx) => {
    if (!window.confirm(`ลบ "${tx.item_name}" ฿${money(tx.amount)} ใช่ไหม? ยอดงบจะถูกคืนด้วย`)) {
      return;
    }
    setActionError("");
    const result = await deleteTransaction(tx.id);
    if (result.success) {
      reload();
    } else {
      setActionError(result.error);
    }
  };

  const handleExport = async () => {
    setActionError("");
    const result = await exportCsv({ month, year });
    if (!result.success) setActionError(result.error);
  };

  const netBalance = totals.income - totals.expense;
  const years = [0, 1, 2, 3, 4].map((offsetYear) => now.getFullYear() - offsetYear);
  const select =
    "px-3 py-2 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500";

  return (
    <>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">รายการของฉัน</h1>
            <p className="text-sm text-gray-500 mt-1">
              สรุปรายรับ-รายจ่ายประจำเดือน {MONTHS[month - 1]} {year + 543}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              className={select}
              value={month}
              onChange={(e) => changeFilter(setMonth)(Number(e.target.value))}
            >
              {MONTHS.map((name, i) => (
                <option key={name} value={i + 1}>
                  {name}
                </option>
              ))}
            </select>
            <select
              className={select}
              value={year}
              onChange={(e) => changeFilter(setYear)(Number(e.target.value))}
            >
              {years.map((y) => (
                <option key={y} value={y}>
                  พ.ศ. {y + 543}
                </option>
              ))}
            </select>
            <select
              className={select}
              value={categoryId}
              onChange={(e) => changeFilter(setCategoryId)(e.target.value)}
            >
              <option value="">ทุกหมวดหมู่</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.icon} {cat.name}
                </option>
              ))}
            </select>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 flex items-center gap-1.5"
            >
              <Download size={16} /> ดาวน์โหลด CSV
            </button>
          </div>
        </div>

        {/* การ์ดสรุปยอดของเดือน (ทั้งเดือน ไม่ใช่แค่หน้าที่แสดง) */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-10">
          <div className="bg-linear-to-br from-[#06C755] to-[#05b348] p-6 rounded-2xl text-white shadow-xl shadow-green-100/30">
            <p className="text-xs uppercase tracking-wider opacity-80 font-semibold mb-1">
              คงเหลือสุทธิเดือนนี้
            </p>
            <h2 className="text-4xl font-bold tracking-tight">฿{money(netBalance)}</h2>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
            <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
              รายรับ
            </span>
            <p className="text-2xl font-bold text-green-600 mt-2 tracking-tight">
              +฿{money(totals.income)}
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
            <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
              รายจ่าย
            </span>
            <p className="text-2xl font-bold text-red-600 mt-2 tracking-tight">
              -฿{money(totals.expense)}
            </p>
          </div>
        </div>

        {actionError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
            ⚠️ {actionError}
          </div>
        )}

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-800 tracking-tight">รายการ</h3>
            <span className="text-xs text-gray-400 font-medium bg-gray-50 px-3 py-1 rounded-full border border-gray-100">
              ทั้งหมด {total} รายการ
            </span>
          </div>

          {loading ? (
            <div className="text-center py-16 text-gray-400 text-sm">กำลังโหลด...</div>
          ) : error ? (
            <div className="text-center py-16 text-red-600 text-sm">⚠️ {error}</div>
          ) : items.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-sm space-y-3">
              <p>ยังไม่มีรายการในเดือนนี้</p>
              <button
                onClick={() => navigate("/add")}
                className="px-4 py-2 bg-green-600 text-white rounded-xl text-sm font-semibold"
              >
                + เพิ่มรายการ
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {items.map((tx) => (
                <div key={tx.id} className="flex items-center justify-between gap-4 py-4">
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-12 h-12 bg-gray-50 border border-gray-100 rounded-2xl flex items-center justify-center shadow-sm text-xl shrink-0">
                      {tx.category_icon}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-800 tracking-tight truncate">
                        {tx.item_name}
                      </p>
                      <span className="text-xs text-gray-400 font-medium">
                        {formatDate(tx.transaction_date)} • {tx.category_name}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span
                      className={`text-sm font-extrabold tracking-tight ${
                        tx.transaction_type === "income" ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {tx.transaction_type === "income" ? "+" : "-"}฿{money(tx.amount)}
                    </span>
                    <button
                      onClick={() => setEditing(tx)}
                      aria-label="แก้ไข"
                      className="p-2 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-50"
                    >
                      <Pencil size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(tx)}
                      aria-label="ลบ"
                      className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {total > WEB_PAGE_SIZE && (
            <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-50 text-sm text-gray-500">
              <span>
                แสดง {offset + 1}-{Math.min(offset + WEB_PAGE_SIZE, total)} จาก {total}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setOffset(Math.max(0, offset - WEB_PAGE_SIZE))}
                  disabled={offset === 0}
                  aria-label="หน้าก่อน"
                  className="p-2 rounded-lg border border-gray-200 disabled:opacity-40"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  onClick={() => setOffset(offset + WEB_PAGE_SIZE)}
                  disabled={offset + WEB_PAGE_SIZE >= total}
                  aria-label="หน้าถัดไป"
                  className="p-2 rounded-lg border border-gray-200 disabled:opacity-40"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {editing && (
        <EditTransactionModal
          tx={editing}
          categories={categories}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            reload();
          }}
        />
      )}

      <footer className="border-t border-gray-100 bg-white py-6 mt-12 text-center text-xs text-gray-400">
        จดนิด JodNid &copy; 2026
      </footer>
    </>
  );
}
