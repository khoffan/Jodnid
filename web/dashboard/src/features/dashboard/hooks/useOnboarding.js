import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import useTransactionStore from "../../transactions/store/useTransectionStore";
import api from "../../../common/lib/api";
import { useWebAuthStore } from "../../webapp/auth/store/web_auth.store";

export const ICON_OPTIONS = [
  "📦",
  "🍔",
  "🚗",
  "🏠",
  "💊",
  "🎮",
  "✈️",
  "👗",
  "📚",
  "💻",
  "🎵",
  "🏋️",
  "☕",
  "🎁",
  "🐾",
  "🔧",
];

const errorDetail = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
};

// งบที่กรอกไว้ (ค่าที่ > 0) เป็นคู่ [categoryId, amount]
export const budgetEntries = (budgets) =>
  Object.entries(budgets).filter(([, value]) => parseFloat(value) > 0);

/**
 * logic ทั้งหมดของหน้าตั้งค่าเริ่มต้น (โหลดหมวด/งบ, เพิ่มหมวด, บันทึกงบ, บันทึกสถานะ onboard)
 *
 * หน้าจอ LIFF กับ web หน้าตาต่างกันได้เต็มที่ แต่การเรียก API ที่แตะงบต้องอยู่ที่นี่ที่เดียว
 * (verify_pipeline ตรวจว่าไฟล์หน้าจอไม่เรียก API เอง)
 */
export const useOnboarding = (userId) => {
  const { saveBudget } = useTransactionStore();
  const { isOnboarded, setOnboardStatus } = useWebAuthStore();
  const navigate = useNavigate();

  // จำโหมดไว้ตั้งแต่เปิดหน้า — isOnboarded จะกลายเป็น true หลังกดยืนยัน ไม่ให้หน้าเปลี่ยนกลางคัน
  const [setupBudgetOnly] = useState(isOnboarded);

  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState({});
  const [loading, setLoading] = useState(true);

  const [newCategory, setNewCategory] = useState({ name: "", icon: "📦", parentId: null });
  const [addingCategory, setAddingCategory] = useState(false);
  const [addCategoryError, setAddCategoryError] = useState("");
  const [addCategorySuccess, setAddCategorySuccess] = useState("");

  const [saveResults, setSaveResults] = useState({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [confirmError, setConfirmError] = useState("");

  // หมวดที่ใช้ได้ (ส่วนกลาง + ของผู้ใช้) และงบเดือนนี้ที่ตั้งไว้แล้ว
  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    const load = async () => {
      try {
        const [catRes, budRes] = await Promise.all([
          api.get("/api/categories/parent"),
          api.get(`/api/budgets/${userId}`),
        ]);
        if (cancelled) return;
        const cats = catRes.data || [];
        const initial = Object.fromEntries(cats.map((cat) => [cat.id, ""]));
        if (budRes.data?.success && Array.isArray(budRes.data.data)) {
          budRes.data.data.forEach((b) => {
            initial[b.category_id] = b.amount?.toString() ?? "";
          });
        }
        setCategories(cats);
        setBudgets(initial);
      } catch (err) {
        console.error("Failed to load onboarding data:", err);
        if (!cancelled) {
          setConfirmError("⚠️ ไม่สามารถดึงข้อมูลหมวดหมู่/งบได้ กรุณารีเฟรชหน้านี้");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const setBudget = (categoryId, value) => {
    setBudgets((prev) => ({ ...prev, [categoryId]: value }));
  };

  const hasBudget = budgetEntries(budgets).length > 0;

  const addCategory = async () => {
    setAddCategoryError("");
    setAddCategorySuccess("");
    const name = newCategory.name.trim();
    if (!name) {
      setAddCategoryError("กรุณาใส่ชื่อหมวดหมู่");
      return;
    }
    setAddingCategory(true);
    try {
      const res = await api.post("/api/categories/add", {
        user_id: userId,
        name,
        icon: newCategory.icon,
        parent_id: newCategory.parentId,
      });
      if (res.data?.success === false) {
        setAddCategoryError(res.data.message || "เพิ่มหมวดหมู่ไม่สำเร็จ");
        return;
      }
      setAddCategorySuccess(`เพิ่ม "${name}" สำเร็จ!`);
      setNewCategory({ name: "", icon: "📦", parentId: null });
      const catRes = await api.get("/api/categories/parent");
      const cats = catRes.data || [];
      setCategories(cats);
      setBudgets((prev) => {
        const updated = { ...prev };
        cats.forEach((cat) => {
          if (!(cat.id in updated)) updated[cat.id] = "";
        });
        return updated;
      });
    } catch (err) {
      setAddCategoryError(errorDetail(err, "เกิดข้อผิดพลาด กรุณาลองใหม่"));
    } finally {
      setAddingCategory(false);
    }
  };

  const confirm = async () => {
    const entries = budgetEntries(budgets);
    if (entries.length === 0) {
      setConfirmError("⚠️ กรุณาระบุงบประมาณอย่างน้อย 1 หมวดหมู่");
      return;
    }

    setSaving(true);
    setConfirmError("");
    const results = {};
    for (const [categoryId, amount] of entries) {
      results[categoryId] = await saveBudget(userId, categoryId, parseFloat(amount));
    }
    setSaveResults(results);

    // บันทึกงบไม่ครบ → ยังไม่นับว่า onboard แล้ว และให้กดลองใหม่ได้
    if (!Object.values(results).every((r) => r.success)) {
      setSaving(false);
      setConfirmError("⚠️ บันทึกงบบางหมวดไม่สำเร็จ กรุณาตรวจสอบแล้วกดยืนยันอีกครั้ง");
      return;
    }

    const onboarded = await setOnboardStatus();
    setSaving(false);
    if (!onboarded) {
      setConfirmError("⚠️ บันทึกสถานะไม่สำเร็จ กรุณากดยืนยันอีกครั้ง");
      return;
    }
    setSaved(true);
    setTimeout(() => navigate("/"), 1200);
  };

  return {
    setupBudgetOnly,
    categories,
    budgets,
    loading,
    setBudget,
    hasBudget,
    newCategory,
    setNewCategory,
    addingCategory,
    addCategoryError,
    addCategorySuccess,
    addCategory,
    saveResults,
    saving,
    saved,
    confirmError,
    setConfirmError,
    confirm,
  };
};
