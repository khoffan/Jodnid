import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import api from "../../../../common/lib/api";
import { LogOut } from "lucide-react";
import { useWebAuthStore } from "../../auth/store/web_auth.store";

// Helper สำหรับจัดรูปแบบวันที่ให้สแกนอ่านง่ายขึ้น
const formatDate = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("th-TH", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// Helper สำหรับเลือก Emoji ตาม Category ID
const getCategoryIcon = (categoryId) => {
  const icons = {
    1: "🍜", // อาหารและเครื่องดื่ม
    2: "🚗", // การเดินทาง
    3: "🛍️", // shopping
    4: "🏠", // ที่อยู่อาศัย
    5: "📝", // อื่นๆ
  };
  return icons[categoryId] || "🏷️";
};

export default function TransactionListPage() {
  const navigate = useNavigate();
  const { logout } = useWebAuthStore();
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const token = sessionStorage.getItem("id_token");
        if (!token) {
          console.error("No ID token found in sessionStorage");
          return;
        }
        
        // ตัวอย่างการเรียก API หรือใช้ข้อมูล Mock ที่ส่งมา
        const response = await api.get("/api/web/transactions", {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
        });
        
        if (response.data.success) {
          // 🛠️ ทำการ Map ข้อมูลจาก Backend ให้ตรงกับ Field ที่ใช้ใน UI
          const mappedData = response.data.data.map((tx) => {
            return {
              id: tx.id,
              note: tx.item_name,                    // ใช้ item_name เป็น note ใน UI
              type: tx.transaction_type,            // ใช้ transaction_type
              amount: Number(tx.amount),             // แปลงเป็นตัวเลข
              date: formatDate(tx.transaction_date),  // จัดรูปแบบวันที่
              categoryName: tx.category_name,        // ใช้ชื่อหมวดหมู่จาก JSON ได้เลย
              categoryIcon: getCategoryIcon(tx.category_id), // ดึง Icon ตาม category_id
            };
          });
          
          setTransactions(mappedData);
        } else {
          console.error("Failed to fetch transactions:", response.data.message);
        }
      } catch (error) {
        console.error("Error fetching transactions:", error);
      }
    };
    fetchTransactions();
  }, []);

  // คำนวณสรุปยอดรวม
  const totalIncome = transactions
    .filter((t) => t.type === "income")
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpense = transactions
    .filter((t) => t.type === "expense")
    .reduce((sum, t) => sum + t.amount, 0);

  const netBalance = totalIncome - totalExpense;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      {/* Header / Navbar สำหรับ Web App */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span className="text-xl p-2 bg-green-50 text-green-600 rounded-xl">
              💼
            </span>
            <span className="font-bold text-gray-900 text-lg tracking-tight">
              JodNid
            </span>
          </div>
          <div className="flex items-center gap-4">
            <button
            onClick={() => navigate("/add")}
            className="px-4 py-2 bg-green-600 text-white font-semibold text-sm rounded-xl hover:bg-green-700 transition flex items-center gap-1.5 shadow-sm"
            >
              <span>+</span> เพิ่มรายการ
            </button>
            <button
              onClick={() => logout()}
              className="bg-amber-700 text-white px-4 py-2 font-semibold text-sm rounded-xl hover:bg-amber-800 transition flex items-center gap-1.5 shadow-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 animate-fade-in">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
              รายการของฉัน
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              สรุปรายรับ-รายจ่าย JodNid Smart Account Book
            </p>
          </div>
        </div>

        {/* การ์ดสรุปยอด */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-10">
          <div className="bg-gradient-to-br from-[#06C755] to-[#05b348] p-6 rounded-2xl text-white shadow-xl shadow-green-100/30">
            <p className="text-xs uppercase tracking-wider opacity-80 font-semibold mb-1">
              ยอดเงินคงเหลือสุทธิ
            </p>
            <h2 className="text-4xl font-bold tracking-tight">
              ฿{netBalance.toLocaleString("th-TH", { minimumFractionDigits: 2 })}
            </h2>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
                รายรับทั้งหมด
              </span>
              <p className="text-2xl font-bold text-green-600 mt-2 tracking-tight">
                +฿
                {totalIncome.toLocaleString("th-TH", {
                  minimumFractionDigits: 2,
                })}
              </p>
            </div>
            <div className="text-xs text-gray-400 mt-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              กระแสเงินสดเข้า
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
                รายจ่ายทั้งหมด
              </span>
              <p className="text-2xl font-bold text-red-600 mt-2 tracking-tight">
                -฿
                {totalExpense.toLocaleString("th-TH", {
                  minimumFractionDigits: 2,
                })}
              </p>
            </div>
            <div className="text-xs text-gray-400 mt-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
              กระแสเงินสดออก
            </div>
          </div>
        </div>

        {/* รายการธุรกรรม */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-800 tracking-tight">
              รายการล่าสุด
            </h3>
            <span className="text-xs text-gray-400 font-medium bg-gray-50 px-3 py-1 rounded-full border border-gray-100">
              ทั้งหมด {transactions.length} รายการ
            </span>
          </div>

          {transactions.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-sm">
              ยังไม่มีรายการในขณะนี้ เริ่มต้นเพิ่มข้อมูลกันเลย!
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {transactions.map((tx) => {
                console.log("Rendering transaction:", tx);
                return (
                <div
                  key={tx.id}
                  onClick={() => navigate(`/edit-temp/${tx.id}`)}
                  className="flex items-center justify-between py-4 first:pt-0 last:pb-0 hover:bg-gray-50/50 px-3 -mx-3 rounded-xl transition-all cursor-pointer group"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gray-50 border border-gray-100 rounded-2xl flex items-center justify-center shadow-sm text-xl group-hover:scale-105 transition-all duration-200">
                      {tx.categoryIcon}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800 tracking-tight">
                        {tx.note}
                      </p>
                      <span className="text-xs text-gray-400 font-medium">
                        {tx.date}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span
                      className={`text-sm font-extrabold tracking-tight ${
                        tx.type === "income" ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {tx.type === "income" ? "+" : "-"}฿
                      {tx.amount.toLocaleString("th-TH", {
                        minimumFractionDigits: 2,
                      })}
                    </span>
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      {tx.categoryName}
                    </p>
                  </div>
                </div>
              )
              })}
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-gray-100 bg-white py-6 mt-12 text-center text-xs text-gray-400">
        JodNid Smart Account Book &copy; 2026
      </footer>
    </div>
  );
}