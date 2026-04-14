import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import useTransactionStore from "../../transactions/store/useTransectionStore";
import api from "../../../common/lib/api";

const Onboarding = ({ userId }) => {
  // 1. สร้าง State เก็บรายการ Categories และยอดงบ (แยกตาม ID)
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState({}); // { "1": "5000", "2": "2000" }
  const { saveBudget, loading } = useTransactionStore();
  const navigate = useNavigate();

  // 2. Fetch Parent Categories จาก API
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await api.get("/api/categories/parent");
        const data = response.data;
        setCategories(data);

        // Initial state สำหรับ budgets
        const initialBudgets = {};
        data.forEach((cat) => {
          initialBudgets[cat.id] = "";
        });
        setBudgets(initialBudgets);
      } catch (error) {
        console.error("Failed to fetch categories:", error);
      }
    };
    fetchCategories();
  }, []);

  const handleInputChange = (id, value) => {
    setBudgets((prev) => ({
      ...prev,
      [id]: value,
    }));
  };

  const handleSave = async () => {
    // กรองเอาเฉพาะหมวดที่มีการกรอกตัวเลข
    const budgetEntries = Object.entries(budgets).filter(([val]) => val > 0);

    if (budgetEntries.length === 0) {
      return alert("กรุณาระบุงบประมาณอย่างน้อย 1 หมวดหมู่");
    }

    try {
      // วนลูปส่ง API บันทึกงบ (หรือปรับ API ให้รับเป็น Array ก็ได้)
      const promises = budgetEntries.map(([catId, amount]) =>
        saveBudget(userId, catId, parseFloat(amount)),
      );

      const results = await Promise.all(promises);
      const allSuccess = results.every((res) => res.success);

      if (allSuccess) {
        navigate("/");
      } else {
        alert("เกิดข้อผิดพลาดบางรายการ กรุณาลองใหม่");
      }
    } catch (error) {
      alert("ระบบขัดข้อง กรุณาลองใหม่");
      console.error(error);
    }
  };

  return (
    <>
      <div className="flex-1 flex flex-col pt-8 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">
            ตั้งเป้างบประมาณ 🎯
          </h1>
          <p className="text-gray-500 mt-2">
            แยกงบตามหมวดหมู่เพื่อการคุมเงินที่แม่นยำขึ้น
          </p>
        </div>

        <div className="space-y-6 pb-10">
          {categories.map((cat) => (
            <div key={cat.id} className="border-b border-gray-100 pb-4">
              <label className="flex items-center gap-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                <span>{cat.icon}</span> {cat.name} (บาท)
              </label>
              <input
                type="number"
                value={budgets[cat.id] || ""}
                onChange={(e) => handleInputChange(cat.id, e.target.value)}
                placeholder="0"
                className="w-full text-2xl font-bold py-2 focus:outline-none focus:border-green-500 placeholder:text-gray-200 transition-colors"
              />
            </div>
          ))}

          <div className="bg-blue-50 p-4 rounded-2xl flex items-start gap-3">
            <span className="text-xl">💡</span>
            <p className="text-sm text-blue-700">
              จดนิดจะช่วยแจ้งเตือนเมื่อคุณใช้เงินในแต่ละหมวดใกล้ครบกำหนดที่ตั้งไว้
            </p>
          </div>
        </div>
      </div>

      <div className="pt-4 bg-white border-t border-gray-50">
        <button
          onClick={handleSave}
          disabled={loading || categories.length === 0}
          className={`w-full py-4 rounded-2xl font-bold text-lg shadow-lg transition-all ${
            loading
              ? "bg-gray-300"
              : "bg-green-500 hover:bg-green-600 text-white active:scale-95"
          }`}
        >
          {loading ? "กำลังบันทึก..." : "เริ่มคุมงบเลย!"}
        </button>
      </div>
    </>
  );
};

export default Onboarding;
