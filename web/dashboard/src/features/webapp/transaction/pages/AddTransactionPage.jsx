import React, { useState } from "react";
import { useNavigate } from "react-router";
// import liff from "@line/liff";
// import api from "../../../common/lib/api"; // นำเข้า api ของคุณที่นี่

export default function AddTransactionPage() {
  const navigate = useNavigate();
  const [amount, setAmount] = useState("");
  const [type, setType] = useState("expense"); // 'expense' หรือ 'income'
  const [category, setCategory] = useState("food");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [note, setNote] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const transactionData = {
      amount: parseFloat(amount),
      type,
      category,
      date,
      note,
    };

    console.log("Saving transaction data:", transactionData);

    // TODO: เชื่อมต่อ API บันทึกข้อมูล
    // try {
    //   await api.post("/api/transactions", transactionData);
    //   alert("บันทึกสำเร็จ!");
    //
    //   if (liff.isInClient()) {
    //     liff.closeWindow();
    //   } else {
    //     navigate("/");
    //   }
    // } catch (err) {
    //   alert("เกิดข้อผิดพลาดในการบันทึกข้อมูล");
    // } finally {
    //   setIsLoading(false);
    // }

    // จำลองการทำงาน (Mock API)
    setTimeout(() => {
      setIsLoading(false);
      alert("บันทึกรายการเรียบร้อยแล้ว! 📝");

      // 🔹 ตรวจสอบว่าเปิดผ่าน LINE LIFF หรือไม่

      navigate("/"); // กลับสู่หน้าหลักสำหรับ Web App ทั่วไป
    }, 1000);
  };

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded-3xl min-h-[80vh] flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-gray-800 tracking-tight">
              จดบันทึก JodNid
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              จัดการรายรับ-รายจ่ายของคุณอย่างรวดเร็ว
            </p>
          </div>
          <button
            onClick={() => navigate("/")}
            className="text-sm font-medium text-gray-400 hover:text-gray-700 transition"
          >
            ย้อนกลับ
          </button>
        </div>

        {/* ฟอร์ม */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* ประเภท: รายรับ / รายจ่าย */}
          <div className="flex gap-2 p-1 bg-gray-50 border border-gray-100 rounded-2xl">
            <button
              type="button"
              onClick={() => setType("expense")}
              className={`flex-1 py-3 text-center rounded-xl font-semibold transition-all ${
                type === "expense"
                  ? "bg-red-500 text-white shadow-lg shadow-red-200"
                  : "text-gray-500 hover:bg-gray-100/50 active:scale-[0.98]"
              }`}
            >
              รายจ่าย
            </button>
            <button
              type="button"
              onClick={() => setType("income")}
              className={`flex-1 py-3 text-center rounded-xl font-semibold transition-all ${
                type === "income"
                  ? "bg-green-500 text-white shadow-lg shadow-green-200"
                  : "text-gray-500 hover:bg-gray-100/50 active:scale-[0.98]"
              }`}
            >
              รายรับ
            </button>
          </div>

          {/* จำนวนเงิน */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
              จำนวนเงิน (บาท)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="w-full px-4 py-3.5 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none transition-all text-lg font-medium"
              required
              min="0"
              step="0.01"
            />
          </div>

          {/* หมวดหมู่ */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
              หมวดหมู่
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-3.5 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none transition-all bg-white"
            >
              <option value="food">🍔 อาหารและเครื่องดื่ม</option>
              <option value="transport">🚌 การเดินทาง</option>
              <option value="shopping">🛍️ ช้อปปิ้ง</option>
              <option value="bills">💡 ค่าน้ำ/ค่าไฟ</option>
              <option value="others">✨ อื่นๆ</option>
            </select>
          </div>

          {/* วันที่ */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
              วันที่
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-4 py-3.5 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none transition-all"
              required
            />
          </div>

          {/* หมายเหตุ */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
              หมายเหตุ (เพิ่มเติม)
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="เช่น ค่าข้าวมื้อเที่ยง, ซื้ออุปกรณ์"
              rows={2}
              className="w-full px-4 py-3 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-green-100 focus:border-green-400 outline-none resize-none transition-all"
            />
          </div>

          {/* ปุ่มบันทึก */}
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-4 bg-[#06C755] hover:bg-[#05b348] text-white rounded-2xl font-bold shadow-md shadow-green-100 active:scale-[0.98] transition-all flex items-center justify-center ${
              isLoading ? "opacity-75 cursor-not-allowed" : ""
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
              "บันทึกรายการ"
            )}
          </button>
        </form>
      </div>

      <p className="text-[10px] text-gray-400 text-center mt-6">
        JodNid Smart Account Book
      </p>
    </div>
  );
}
