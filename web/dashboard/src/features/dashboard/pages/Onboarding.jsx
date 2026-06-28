import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import useTransactionStore from "../../transactions/store/useTransectionStore";
import api from "../../../common/lib/api";
import { useWebAuthStore } from "../../webapp/auth/store/web_auth.store";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const STEP = { BUDGET: 0, CATEGORIES: 1, REVIEW: 2 };
const STEP_LABELS = ["ตั้งงบประมาณ", "หมวดหมู่", "ตรวจสอบ"];
const STEP_ICONS = ["💰", "🏷️", "✅"];
const ICON_OPTIONS = [
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

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const Onboarding = ({ userId }) => {
  // ── mode ──────────────────────────────────────────────────────────────────
  // "strict" = ต้องครบทุกขั้นตอนก่อนยืนยัน
  // "quick"  = แค่ตั้งงบก็ยืนยันได้เลย
  const [mode, setMode] = useState("strict");

  // ── stepper ───────────────────────────────────────────────────────────────
  const [step, setStep] = useState(STEP.BUDGET);
  const [visited, setVisited] = useState(new Set([STEP.BUDGET]));

  // ── data ──────────────────────────────────────────────────────────────────
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState({});
  const [dataLoading, setDataLoading] = useState(false);

  // ── add-category form ─────────────────────────────────────────────────────
  const [newCatName, setNewCatName] = useState("");
  const [newCatIcon, setNewCatIcon] = useState("📦");
  const [newCatParentId, setNewCatParentId] = useState(null);
  const [addingCat, setAddingCat] = useState(false);
  const [addCatError, setAddCatError] = useState("");
  const [addCatSuccess, setAddCatSuccess] = useState("");

  // ── save state ────────────────────────────────────────────────────────────
  const [saveResults, setSaveResults] = useState({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const { saveBudget } = useTransactionStore();
  const {
    isWebApp,
    onboardingCategories,
    onboardingBudgets,
    fetchOnboardingData,
    onboardingLoading,
    isOnboarded,
  } = useWebAuthStore();
  const navigate = useNavigate();
  const setupBudgetOnly = isOnboarded;
  const activeStepLabels = setupBudgetOnly ? [STEP_LABELS[STEP.BUDGET]] : STEP_LABELS;
  const activeStepIcons = setupBudgetOnly ? [STEP_ICONS[STEP.BUDGET]] : STEP_ICONS;

  useEffect(() => {
    if (setupBudgetOnly) {
      setStep(STEP.BUDGET);
      setVisited(new Set([STEP.BUDGET]));
    }
  }, [setupBudgetOnly]);

  // ── fetch onboarding data ─────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setDataLoading(true);
      try {
        if (isWebApp) {
          if (onboardingCategories.length === 0) {
            const { categories: cats, budgets: buds } = await fetchOnboardingData(userId);
            setCategories(cats);
            setBudgets(buds);
          } else {
            setCategories(onboardingCategories);
            setBudgets(onboardingBudgets);
          }
        } else {
          const [catRes, budRes] = await Promise.all([
            api.get("/api/categories/parent"),
            api.get(`/api/budgets/${userId}`),
          ]);

          const cats = catRes.data || [];
          setCategories(cats);

          const initial = {};
          cats.forEach((c) => {
            initial[c.id] = "";
          });

          if (budRes.data?.success && Array.isArray(budRes.data.data)) {
            budRes.data.data.forEach((b) => {
              initial[b.category_id] = b.amount?.toString() ?? "";
            });
          }
          setBudgets(initial);
        }
      } catch (err) {
        console.error("Failed to load onboarding data:", err);
      } finally {
        setDataLoading(false);
      }
    };

    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // ── helpers ───────────────────────────────────────────────────────────────
  const hasBudget = Object.values(budgets).some((v) => parseFloat(v) > 0);

  const canConfirm = setupBudgetOnly
    ? hasBudget
    : mode === "quick"
      ? hasBudget
      : hasBudget && visited.has(STEP.CATEGORIES) && visited.has(STEP.REVIEW);

  const isFinalStep = setupBudgetOnly || step === STEP.REVIEW;

  const goTo = (s) => {
    setStep(s);
    setVisited((prev) => new Set([...prev, s]));
  };

  const handleBudgetChange = (id, value) => {
    setBudgets((prev) => ({ ...prev, [id]: value }));
  };

  // ── add custom category ───────────────────────────────────────────────────
  const handleAddCategory = async () => {
    setAddCatError("");
    setAddCatSuccess("");
    if (!newCatName.trim()) {
      setAddCatError("กรุณาใส่ชื่อหมวดหมู่");
      return;
    }
    setAddingCat(true);
    try {
      const res = await api.post("/api/categories/add", {
        user_id: userId,
        name: newCatName.trim(),
        icon: newCatIcon,
        parent_id: newCatParentId,
      });
      if (res.data?.success === false) {
        setAddCatError(res.data.message || "เพิ่มหมวดหมู่ไม่สำเร็จ");
      } else {
        setAddCatSuccess(`เพิ่ม "${newCatName.trim()}" สำเร็จ!`);
        setNewCatName("");
        setNewCatIcon("📦");
        setNewCatParentId(null);
        // refresh category list
        const catRes = await api.get("/api/categories/parent");
        const cats = catRes.data || [];
        setCategories(cats);
        setBudgets((prev) => {
          const updated = { ...prev };
          cats.forEach((c) => {
            if (!(c.id in updated)) updated[c.id] = "";
          });
          return updated;
        });
      }
    } catch {
      setAddCatError("เกิดข้อผิดพลาด กรุณาลองใหม่");
    } finally {
      setAddingCat(false);
    }
  };

  // ── confirm & save ────────────────────────────────────────────────────────
  const handleConfirm = async () => {
    const entries = Object.entries(budgets).filter(([, v]) => parseFloat(v) > 0);
    if (entries.length === 0) return alert("กรุณาระบุงบประมาณอย่างน้อย 1 หมวดหมู่");

    setSaving(true);
    const results = {};
    for (const [catId, amount] of entries) {
      results[catId] = await saveBudget(userId, catId, parseFloat(amount));
    }
    setSaveResults(results);
    setSaving(false);
    setSaved(true);

    if (Object.values(results).every((r) => r.success)) {
      setTimeout(() => navigate("/"), 1200);
    }
  };

  // ── layout ────────────────────────────────────────────────────────────────
  const wrapper = isWebApp
    ? "w-full max-w-7xl mx-auto mt-4 px-4 sm:px-6 lg:px-8"
    : "w-full max-w-lg mx-auto px-4";

  const isLoading = dataLoading || onboardingLoading;

  return (
    <div className={wrapper}>
      {/* ── Header & mode toggle ── */}
      <div className="flex items-center justify-between mb-6 mt-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">ตั้งค่าเริ่มต้น 🚀</h1>
          <p className="text-gray-500 text-sm mt-1">
            {setupBudgetOnly ? "ตั้งงบประมาณของคุณ" : "ตั้งงบประมาณและหมวดหมู่ของคุณ"}
          </p>
        </div>
        {!setupBudgetOnly && (
          <div className="flex items-center bg-gray-100 rounded-full p-1 gap-1">
            <button
              onClick={() => setMode("quick")}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                mode === "quick" ? "bg-white text-green-600 shadow-sm" : "text-gray-500"
              }`}
            >
              ⚡ ด่วน
            </button>
            <button
              onClick={() => setMode("strict")}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                mode === "strict" ? "bg-white text-blue-600 shadow-sm" : "text-gray-500"
              }`}
            >
              📋 ครบถ้วน
            </button>
          </div>
        )}
      </div>

      {/* ── Mode hint ── */}
      {!setupBudgetOnly && (
        <div
          className={`mb-5 px-4 py-2.5 rounded-2xl text-xs font-medium flex items-center gap-2 ${
            mode === "strict" ? "bg-blue-50 text-blue-700" : "bg-green-50 text-green-700"
          }`}
        >
          {mode === "strict" ? (
            <>📋 โหมดครบถ้วน — ต้องทำครบทุกขั้นตอนก่อนกดยืนยัน</>
          ) : (
            <>⚡ โหมดด่วน — ตั้งงบเสร็จแล้วกดยืนยันได้เลย</>
          )}
        </div>
      )}

      {/* ── Stepper ── */}
      <div className="flex items-center mb-8">
        {activeStepLabels.map((label, i) => (
          <div key={i} className="flex items-center flex-1 last:flex-none">
            <button
              onClick={() => visited.has(i) && goTo(i)}
              className="flex flex-col items-center gap-1"
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold transition-all ${
                  step === i
                    ? "bg-green-500 text-white shadow-lg scale-110"
                    : visited.has(i)
                      ? "bg-green-100 text-green-600"
                      : "bg-gray-100 text-gray-400"
                }`}
              >
                {visited.has(i) && step !== i ? "✓" : activeStepIcons[i]}
              </div>
              <span
                className={`text-xs font-medium ${step === i ? "text-green-600" : "text-gray-400"}`}
              >
                {label}
              </span>
            </button>
            {i < activeStepLabels.length - 1 && (
              <div
                className={`flex-1 h-0.5 mx-2 mb-5 transition-colors ${
                  visited.has(i + 1) ? "bg-green-300" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* ── Step content ── */}
      <div className="pb-32">
        {step === STEP.BUDGET && (
          <SetBudgetStep
            categories={categories}
            budgets={budgets}
            loading={isLoading}
            onInputChange={handleBudgetChange}
          />
        )}
        {!setupBudgetOnly && step === STEP.CATEGORIES && (
          <CategoriesStep
            categories={categories}
            newCatName={newCatName}
            newCatIcon={newCatIcon}
            newCatParentId={newCatParentId}
            addingCat={addingCat}
            addCatError={addCatError}
            addCatSuccess={addCatSuccess}
            onNameChange={setNewCatName}
            onIconChange={setNewCatIcon}
            onParentChange={setNewCatParentId}
            onAdd={handleAddCategory}
          />
        )}
        {!setupBudgetOnly && step === STEP.REVIEW && (
          <ReviewStep
            categories={categories}
            budgets={budgets}
            saveResults={saveResults}
            saved={saved}
          />
        )}
      </div>

      {/* ── Fixed footer nav ── */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-4 pb-6 pt-3 z-10">
        <div className="max-w-lg mx-auto space-y-2">
          {/* Quick-mode skip link */}
          {!setupBudgetOnly && mode === "quick" && step === STEP.BUDGET && hasBudget && (
            <div className="text-center">
              <button
                onClick={() => goTo(STEP.REVIEW)}
                className="text-sm text-green-600 underline underline-offset-2"
              >
                ข้ามไปตรวจสอบ & ยืนยันเลย →
              </button>
            </div>
          )}

          <div className="flex gap-3">
            {!setupBudgetOnly && step > 0 && (
              <button
                onClick={() => goTo(step - 1)}
                className="flex-1 py-3.5 rounded-2xl font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 transition-all"
              >
                ← ย้อนกลับ
              </button>
            )}

            {!isFinalStep ? (
              <button
                onClick={() => {
                  if (step === STEP.BUDGET && !hasBudget) {
                    return alert("กรุณาระบุงบประมาณอย่างน้อย 1 หมวดหมู่ก่อน");
                  }
                  goTo(step + 1);
                }}
                className="flex-1 py-3.5 rounded-2xl font-bold bg-green-500 hover:bg-green-600 text-white shadow-lg transition-all active:scale-95"
              >
                ถัดไป →
              </button>
            ) : (
              <button
                onClick={handleConfirm}
                disabled={!canConfirm || saving || saved}
                className={`flex-1 py-3.5 rounded-2xl font-bold shadow-lg transition-all text-lg ${
                  !canConfirm || saving || saved
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-green-500 hover:bg-green-600 text-white active:scale-95"
                }`}
              >
                {saving ? "กำลังบันทึก..." : saved ? "✅ บันทึกแล้ว!" : "ยืนยัน & เริ่มเลย!"}
              </button>
            )}
          </div>

          {/* strict-mode checklist hint on review step */}
          {!setupBudgetOnly && mode === "strict" && step === STEP.REVIEW && !canConfirm && (
            <p className="text-xs text-center text-amber-600">
              {!hasBudget && "⚠️ ยังไม่ได้ตั้งงบ "}
              {!visited.has(STEP.CATEGORIES) && "⚠️ ยังไม่ได้เข้าขั้นตอนหมวดหมู่ "}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Step 1 — Set Budget
// ---------------------------------------------------------------------------
const SetBudgetStep = ({ categories, budgets, loading, onInputChange }) => (
  <div>
    <div className="mb-5">
      <h2 className="text-xl font-bold text-gray-800">💰 ตั้งงบประมาณ</h2>
      <p className="text-sm text-gray-500 mt-1">
        ระบุงบในแต่ละหมวดหมู่ที่ต้องการ (ปล่อยว่างได้ถ้าไม่ต้องการ)
      </p>
    </div>

    {loading ? (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="animate-pulse h-16 bg-gray-100 rounded-2xl" />
        ))}
      </div>
    ) : (
      <div className="space-y-4">
        {categories.map((cat) => (
          <div key={cat.id} className="border-b border-gray-100 pb-4">
            <label className="flex items-center gap-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
              <span>{cat.icon}</span>
              {cat.name} (บาท)
            </label>
            <input
              type="number"
              value={budgets[cat.id] ?? ""}
              onChange={(e) => onInputChange(cat.id, e.target.value)}
              placeholder="0"
              min="0"
              className="w-full text-2xl font-bold py-2 bg-transparent focus:outline-none placeholder:text-gray-200 transition-colors"
            />
          </div>
        ))}

        <div className="bg-blue-50 p-4 rounded-2xl flex items-start gap-3">
          <span className="text-xl">💡</span>
          <p className="text-sm text-blue-700">
            จดนิดจะแจ้งเตือนเมื่อใช้เงินในแต่ละหมวดใกล้ครบงบที่ตั้งไว้
          </p>
        </div>
      </div>
    )}
  </div>
);

// ---------------------------------------------------------------------------
// Step 2 — Categories
// ---------------------------------------------------------------------------
const CategoriesStep = ({
  categories,
  newCatName,
  newCatIcon,
  newCatParentId,
  addingCat,
  addCatError,
  addCatSuccess,
  onNameChange,
  onIconChange,
  onParentChange,
  onAdd,
}) => (
  <div>
    <div className="mb-5">
      <h2 className="text-xl font-bold text-gray-800">🏷️ จัดการหมวดหมู่</h2>
      <p className="text-sm text-gray-500 mt-1">
        ดูหมวดหมู่ที่มีอยู่ หรือเพิ่มหมวดหมู่ใหม่ของคุณเอง
      </p>
    </div>

    {/* Existing categories grid */}
    <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 mb-6">
      {categories.map((cat) => (
        <div key={cat.id} className="bg-gray-50 rounded-2xl p-3 flex flex-col items-center gap-1.5">
          <span className="text-2xl">{cat.icon}</span>
          <span className="text-xs font-medium text-gray-600 text-center leading-tight">
            {cat.name}
          </span>
        </div>
      ))}
    </div>

    {/* Add custom category */}
    <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">➕ เพิ่มหมวดหมู่ใหม่</h3>

      {/* Icon picker */}
      <p className="text-xs text-gray-400 mb-2">เลือกไอคอน</p>
      <div className="flex flex-wrap gap-2 mb-4">
        {ICON_OPTIONS.map((icon) => (
          <button
            key={icon}
            onClick={() => onIconChange(icon)}
            className={`w-9 h-9 rounded-xl text-xl flex items-center justify-center transition-all ${
              newCatIcon === icon
                ? "bg-green-100 ring-2 ring-green-400"
                : "bg-gray-50 hover:bg-gray-100"
            }`}
          >
            {icon}
          </button>
        ))}
      </div>

      <input
        type="text"
        value={newCatName}
        onChange={(e) => onNameChange(e.target.value)}
        placeholder="ชื่อหมวดหมู่ เช่น ค่าเช่า"
        className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-green-300"
      />

      <select
        value={newCatParentId ?? ""}
        onChange={(e) => onParentChange(e.target.value ? parseInt(e.target.value) : null)}
        className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-green-300 bg-white"
      >
        <option value="">— หมวดหมู่หลัก (ไม่มีหมวดแม่) —</option>
        {categories.map((cat) => (
          <option key={cat.id} value={cat.id}>
            {cat.icon} {cat.name}
          </option>
        ))}
      </select>

      {addCatError && <p className="text-xs text-red-500 mb-3">{addCatError}</p>}
      {addCatSuccess && <p className="text-xs text-green-600 mb-3">{addCatSuccess}</p>}

      <button
        onClick={onAdd}
        disabled={addingCat}
        className="w-full py-2.5 rounded-xl bg-green-500 hover:bg-green-600 text-white font-medium text-sm transition-all active:scale-95 disabled:bg-gray-300"
      >
        {addingCat ? "กำลังเพิ่ม..." : `${newCatIcon} เพิ่มหมวดหมู่`}
      </button>
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Step 3 — Review & Confirm
// ---------------------------------------------------------------------------
const ReviewStep = ({ categories, budgets, saveResults, saved }) => {
  const entries = Object.entries(budgets).filter(([, v]) => parseFloat(v) > 0);
  const catMap = Object.fromEntries(categories.map((c) => [String(c.id), c]));
  const total = entries.reduce((sum, [, v]) => sum + parseFloat(v), 0);

  return (
    <div>
      <div className="mb-5">
        <h2 className="text-xl font-bold text-gray-800">✅ ตรวจสอบก่อนยืนยัน</h2>
        <p className="text-sm text-gray-500 mt-1">สรุปงบประมาณที่คุณตั้งไว้</p>
      </div>

      {entries.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <span className="text-5xl block mb-3">😅</span>
          <p className="text-sm">ยังไม่ได้ตั้งงบประมาณ</p>
          <p className="text-xs mt-1">กลับไปขั้นตอนแรกแล้วใส่ตัวเลขก่อนนะ</p>
        </div>
      ) : (
        <>
          <div className="space-y-3 mb-5">
            {entries.map(([catId, amount]) => {
              const cat = catMap[catId];
              const result = saveResults[catId];
              return (
                <div
                  key={catId}
                  className="flex items-center justify-between bg-gray-50 rounded-2xl px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{cat?.icon ?? "📦"}</span>
                    <div>
                      <p className="font-semibold text-gray-800 text-sm">{cat?.name ?? catId}</p>
                      <p className="text-xs text-gray-400">
                        {parseFloat(amount).toLocaleString("th-TH")} บาท / เดือน
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    {result ? (
                      result.success ? (
                        <span className="text-green-500 font-bold">✅</span>
                      ) : (
                        <span className="text-red-400 text-xs">❌ {result.message}</span>
                      )
                    ) : (
                      <span className="text-gray-300 text-sm">—</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Total */}
          <div className="bg-green-50 rounded-2xl px-4 py-3.5 flex justify-between items-center mb-4">
            <span className="font-semibold text-gray-700">รวมงบทั้งหมด</span>
            <span className="text-xl font-bold text-green-600">
              {total.toLocaleString("th-TH")} บาท
            </span>
          </div>

          {!saved && (
            <div className="bg-amber-50 rounded-2xl p-4 flex items-start gap-3">
              <span className="text-xl">⚠️</span>
              <p className="text-sm text-amber-700">
                กด &ldquo;ยืนยัน & เริ่มเลย!&rdquo; ด้านล่างเพื่อบันทึกงบประมาณ
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Onboarding;
