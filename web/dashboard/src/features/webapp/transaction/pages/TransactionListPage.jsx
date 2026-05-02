import React, { useState } from "react";
import { useNavigate } from "react-router";

// ข้อมูลจำลอง (Mock Data) สำหรับแสดงผล
const mockTransactions = [
  {
    id: 1,
    note: "ค่าข้าวมื้อเที่ยง",
    amount: 150.0,
    type: "expense", // 'expense' หรือ 'income'
    category: "food",
    date: "2026-05-02",
  },
  {
    id: 2,
    note: "เงินเดือน",
    amount: 25000.0,
    type: "income",
    category: "salary",
    date: "2026-05-01",
  },
  {
    id: 3,
    note: "ค่าน้ำมัน",
    amount: 500.0,
    type: "expense",
    category: "transport",
    date: "2026-04-30",
  },
];

const categoryIcons = {
  food: "🍔",
  transport: "🚌",
  shopping: "🛍️",
  bills: "💡",
  salary: "💰",
  others: "✨",
};

export default function TransactionListPage() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState(mockTransactions);

  // คำนวณสรุปยอดรวม
  const totalIncome = transactions
    .filter((t) => t.type === "income")
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpense = transactions
    .filter((t) => t.type === "expense")
    .reduce((sum, t) => sum + t.amount, 0);

  const netBalance = totalIncome - totalExpense;

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded-3xl min-h-[80vh] flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-gray-800 tracking-tight">
              รายการของฉัน
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              สรุปรายรับ-รายจ่าย JodNid
            </p>
          </div>
          <button
            onClick={() => navigate("/webapp/add")}
            className="px-4 py-2 bg-green-50 text-green-600 font-semibold text-sm rounded-xl hover:bg-green-100 transition-all flex items-center gap-1.5"
          >
            <span>+</span> เพิ่มรายการ
          </button>
        </div>

        {/* การ์ดสรุปยอด */}
        <div className="bg-gradient-to-br from-[#06C755] to-[#05b348] p-5 rounded-2xl text-white shadow-lg shadow-green-100 mb-6">
          <p className="text-xs opacity-80 font-medium">ยอดเงินคงเหลือสุทธิ</p>
          <h2 className="text-3xl font-bold mt-1 mb-4 tracking-tight">
            ฿{netBalance.toLocaleString("th-TH", { minimumFractionDigits: 2 })}
          </h2>
          <div className="flex justify-between border-t border-white/20 pt-4 text-xs">
            <div>
              <p className="opacity-75 mb-0.5">รายรับทั้งหมด</p>
              <span className="font-semibold text-green-100">
                +฿
                {totalIncome.toLocaleString("th-TH", {
                  minimumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="text-right">
              <p className="opacity-75 mb-0.5">รายจ่ายทั้งหมด</p>
              <span className="font-semibold text-red-200">
                -฿
                {totalExpense.toLocaleString("th-TH", {
                  minimumFractionDigits: 2,
                })}
              </span>
            </div>
          </div>
        </div>

        {/* รายการธุรกรรม (Transaction List) */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-700 px-1 mb-1">
            รายการล่าสุด
          </h3>

          {transactions.length === 0 ? (
            <div className="text-center py-12 text-gray-400 text-sm">
              ยังไม่มีรายการในขณะนี้ เริ่มต้นเพิ่มข้อมูลกันเลย!
            </div>
          ) : (
            transactions.map((tx) => (
              <div
                key={tx.id}
                onClick={() => navigate(`/edit-temp/${tx.id}`)}
                className="flex items-center justify-between p-4 border border-gray-100 bg-gray-50/50 rounded-2xl hover:border-gray-200 transition-all cursor-pointer active:scale-[0.99]"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 bg-white border border-gray-100 rounded-2xl flex items-center justify-center shadow-sm text-lg">
                    {categoryIcons[tx.category] || "✨"}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-800 tracking-tight">
                      {tx.note || "ไม่มีหมายเหตุ"}
                    </p>
                    <span className="text-[10px] text-gray-400 font-medium">
                      {tx.date}
                    </span>
                  </div>
                </div>

                <div>
                  <span
                    className={`text-sm font-bold tracking-tight ${
                      tx.type === "income" ? "text-green-500" : "text-red-500"
                    }`}
                  >
                    {tx.type === "income" ? "+" : "-"}฿
                    {tx.amount.toLocaleString("th-TH", {
                      minimumFractionDigits: 2,
                    })}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <p className="text-[10px] text-gray-400 text-center mt-8">
        JodNid Smart Account Book
      </p>
    </div>
  );
}
