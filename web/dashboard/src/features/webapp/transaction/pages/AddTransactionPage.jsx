import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import api from "../../../../common/lib/api";
import { useWebTransaction } from "../store/web.transaction.store";

export default function AddTransactionPage() {
  const navigate = useNavigate();
  const { createTransaction } = useWebTransaction();
  // State สำหรับเก็บรายการที่เพิ่มเข้ามา
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);

  // State สำหรับฟอร์มกรอกรายการย่อย
  const [amount, setAmount] = useState("");
  const [type, setType] = useState("expense");
  const [category, setCategory] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [note, setNote] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [validate, setValidate] = useState({
    amount: true,
    category: true,
    date: true,
    note: true,
    is_actual_item: false,
    priority: false,
  });

  // คำนวณสรุปยอดรวมของรายการที่กำลังจะบันทึก
  const totalIncome = items
    .filter((i) => i.type === "income")
    .reduce((sum, i) => sum + i.amount, 0);

  const totalExpense = items
    .filter((i) => i.type === "expense")
    .reduce((sum, i) => sum + i.amount, 0);

  const netBalance = totalIncome - totalExpense;

  useEffect(() => {
    const fetchCatogories = async () => {
      try {
        const res = await api.get(`/api/categories/parent`);
        setCategories(res.data);
        setCategory(res.data[0]?.name || "");
      } catch (e) {
        console.error("Error fetching categories:", e);
      }
    };
    fetchCatogories();
  }, []);

  // เพิ่มรายการลงในลิสต์ชั่วคราว
  const handleAddItem = (e) => {
    e.preventDefault();

    if (!amount || parseFloat(amount) <= 0) {
      setValidate({ ...validate, amount: false });
      // alert("กรุณาระบุจำนวนเงินที่มากกว่า 0");
      return;
    }

    if (!category) {
      setValidate({ ...validate, category: false });
      // alert("กรุณาเลือกหมวดหมู่");
      return;
    }
    if (!date) {
      setValidate({ ...validate, date: false });
      // alert("กรุณาเลือกวันที่");
      return;
    }
    if (!note) {
      setValidate({ ...validate, note: false });
      // alert("กรุณาระบุหมายเหตุ");
      return;
    }
    const newItem = {
      id: Date.now(), // ใช้ timestamp เป็น ID ชั่วคราว
      amount: parseFloat(amount),
      type,
      category,
      date,
      note: note,
      is_actual_item: true, // กำหนดเป็นรายการจริงที่จะบันทึก
      priority: false,
    };

    setItems([...items, newItem]);

    // รีเซ็ตเฉพาะช่องจำนวนเงินและหมายเหตุ เพื่อให้กรอกรายการถัดไปได้ง่าย
    setAmount("");
    setNote("");
    setValidate({
      amount: true,
      category: true,
      date: true,
      note: true,
      is_actual_item: false,
      priority: false,
    });
  };

  // ลบรายการออกจากลิสต์
  const handleRemoveItem = (id) => {
    setItems(items.filter((i) => i.id !== id));
  };

  // บันทึกรายการทั้งหมด
  const handleSubmitAll = async (e) => {
    e.preventDefault();
    if (items.length === 0) {
      alert("กรุณาเพิ่มรายการอย่างน้อย 1 รายการก่อนบันทึก");
      return;
    }
    setIsLoading(true);
    const newItems = items.map((i) => ({
      amount: i.amount.toFixed(2),
      category: i.category,
      type: i.type,
      note: i.note,
      date: i.date,
      is_actual_item: i.is_actual_item,
      priority: false,
    }));
    const result = await createTransaction({
      total: Math.abs(netBalance).toFixed(2),
      items: newItems,
    });

    setIsLoading(false);
    if (result) {
      alert(`บันทึกรายการทั้งหมด ${newItems.length} รายการเรียบร้อยแล้ว! 📝`);
      navigate("/");
    } else {
      alert("เกิดข้อผิดพลาดในการบันทึกรายการ กรุณาลองใหม่อีกครั้ง");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800 flex flex-col justify-between">
      {/* Header / Navbar สำหรับ Web App */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span
              className="text-xl p-2 bg-green-50 text-green-600 rounded-xl cursor-pointer"
              onClick={() => navigate("/")}
            >
              💼
            </span>
            <span className="font-bold text-gray-900 text-lg tracking-tight">JodNid</span>
          </div>
          <button
            onClick={() => navigate("/")}
            className="text-sm font-semibold text-gray-400 hover:text-gray-700 transition"
          >
            ย้อนกลับ
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            จดบันทึกรายการใหม่
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            สามารถเพิ่มรายการย่อยหลายรายการพร้อมกัน และบันทึกในคราวเดียว
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* ฝั่งซ้าย: ฟอร์มกรอกรายการ */}
          <div className="lg:col-span-2 bg-white p-8 rounded-2xl border border-gray-100 shadow-sm h-fit">
            <form onSubmit={handleAddItem} className="space-y-6">
              {/* ประเภท: รายรับ / รายจ่าย */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  ประเภทรายการ
                </label>
                <div className="flex gap-3 p-1 bg-gray-50 border border-gray-100 rounded-2xl">
                  <button
                    type="button"
                    onClick={() => setType("expense")}
                    className={`flex-1 py-3 text-center rounded-xl font-semibold transition-all text-sm ${
                      type === "expense"
                        ? "bg-red-500 text-white shadow-lg shadow-red-100"
                        : "text-gray-500 hover:bg-gray-100/50 active:scale-[0.98]"
                    }`}
                  >
                    📉 รายจ่าย
                  </button>
                  <button
                    type="button"
                    onClick={() => setType("income")}
                    className={`flex-1 py-3 text-center rounded-xl font-semibold transition-all text-sm ${
                      type === "income"
                        ? "bg-green-600 text-white shadow-lg shadow-green-100"
                        : "text-gray-500 hover:bg-gray-100/50 active:scale-[0.98]"
                    }`}
                  >
                    📈 รายรับ
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">
                    จำนวนเงิน (บาท)
                  </label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-4 py-3.5 border border-gray-200 rounded-xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none transition-all text-base font-medium bg-gray-50/20"
                    required
                    min="0"
                    step="0.01"
                  />
                  {validate.amount === false && (
                    <p className="text-red-500 text-xs mt-1">กรุณาระบุจำนวนเงินที่มากกว่า 0</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">หมวดหมู่</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-4 py-3.5 border border-gray-200 rounded-xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none transition-all bg-gray-50/20"
                  >
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.name}>
                        {cat.icon} {cat.name}
                      </option>
                    ))}
                  </select>
                  {validate.category === false && (
                    <p className="text-red-500 text-xs mt-1">กรุณาเลือกหมวดหมู่</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">วันที่</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-4 py-3.5 border border-gray-200 rounded-xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none transition-all bg-gray-50/20 text-gray-700 font-medium"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">
                  หมายเหตุ (เพิ่มเติม)
                </label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="เช่น ค่าข้าวมื้อเที่ยง, ซื้ออุปกรณ์"
                  rows={2}
                  className="w-full px-4 py-3.5 border border-gray-200  rounded-xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none resize-none transition-all bg-gray-50/20"
                />
                {validate.note === false && (
                  <p className="text-red-500 text-xs mt-1">กรุณาระบุหมายเหตุ</p>
                )}
              </div>

              <button
                type="submit"
                className="w-full py-3.5 border-2 border-green-600 text-green-600 hover:bg-green-50 font-bold rounded-xl transition-all active:scale-[0.98]"
              >
                ➕ เพิ่มรายการนี้ลงในลิสต์
              </button>
            </form>
          </div>

          {/* ฝั่งขวา: สรุปรายการในลิสต์และยอดรวม */}
          <div className="flex flex-col gap-6 h-full justify-between">
            {/* สรุปภาพรวม */}
            <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm h-fit">
              <h2 className="text-lg font-bold text-gray-800 mb-4 tracking-tight">
                สรุปยอดรวมในลิสต์
              </h2>

              <div className="space-y-4 border-b border-gray-100 pb-4 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">รายการทั้งหมด</span>
                  <span className="font-bold text-gray-700">{items.length} รายการ</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">รวมรายรับ</span>
                  <span className="font-bold text-green-600">
                    +฿
                    {totalIncome.toLocaleString("th-TH", {
                      minimumFractionDigits: 2,
                    })}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">รวมรายจ่าย</span>
                  <span className="font-bold text-red-600">
                    -฿
                    {totalExpense.toLocaleString("th-TH", {
                      minimumFractionDigits: 2,
                    })}
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center mb-6">
                <span className="text-sm font-semibold text-gray-700">คงเหลือสุทธิ</span>
                <span
                  className={`text-xl font-extrabold tracking-tight ${
                    netBalance >= 0 ? "text-green-600" : "text-red-600"
                  }`}
                >
                  ฿
                  {netBalance.toLocaleString("th-TH", {
                    minimumFractionDigits: 2,
                  })}
                </span>
              </div>

              <button
                onClick={handleSubmitAll}
                disabled={isLoading || items.length === 0}
                className={`w-full py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold shadow-sm active:scale-[0.98] transition-all flex items-center justify-center text-sm tracking-wide ${
                  isLoading || items.length === 0 ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                {isLoading ? (
                  <svg
                    className="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : (
                  `บันทึกทั้งหมด (${items.length} รายการ)`
                )}
              </button>
            </div>

            {/* ลิสต์รายการย่อยที่เพิ่มแล้ว */}
            <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex-1 max-h-[350px] overflow-y-auto">
              <h3 className="text-sm font-bold text-gray-800 mb-4">รายการที่กำลังเพิ่ม</h3>

              {items.length === 0 ? (
                <div className="text-center py-12 text-gray-400 text-xs">
                  ยังไม่มีรายการย่อย ลองเพิ่มรายการที่ฟอร์มฝั่งซ้ายมือ
                </div>
              ) : (
                <div className="space-y-3">
                  {items.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-3 border border-gray-50 bg-gray-50/50 rounded-xl"
                    >
                      <div className="flex items-center gap-3">
                        <div></div>
                        <div>
                          <p className="text-xs font-bold text-gray-800">{item.note}</p>
                          <p className="text-[10px] text-gray-400">
                            {item.category} • {item.date}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span
                          className={`text-xs font-extrabold ${
                            item.type === "income" ? "text-green-600" : "text-red-600"
                          }`}
                        >
                          {item.type === "income" ? "+" : "-"}฿
                          {item.amount.toLocaleString("th-TH", {
                            minimumFractionDigits: 2,
                          })}
                        </span>
                        <button
                          onClick={() => handleRemoveItem(item.id)}
                          className="text-red-500 hover:text-red-600 p-1.5 rounded-lg border border-red-100 hover:bg-red-50 transition"
                          aria-label="ลบรายการ"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white py-6 mt-12 text-center text-xs text-gray-400">
        JodNid Smart Account Book &copy; 2026
      </footer>
    </div>
  );
}
