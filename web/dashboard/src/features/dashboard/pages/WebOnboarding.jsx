import { ICON_OPTIONS, budgetEntries, useOnboarding } from "../hooks/useOnboarding";

// ---------------------------------------------------------------------------
// หน้าตั้งค่าเริ่มต้นสาย web (จอคอม): เห็นทุกอย่างในหน้าเดียว ไม่มี stepper
// ซ้าย = หมวดหมู่ + เพิ่มหมวด, กลาง = กรอกงบ, ขวา = สรุปยอด + ปุ่มยืนยัน (ติดขอบบนเวลาเลื่อน)
// logic ทั้งหมดอยู่ใน useOnboarding — ไฟล์นี้มีแต่หน้าจอ
// ---------------------------------------------------------------------------
const money = (value) => Number(value || 0).toLocaleString("th-TH", { minimumFractionDigits: 2 });

const card = "bg-white rounded-2xl border border-gray-100 shadow-sm p-6";
const input =
  "w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#06C755]/40 focus:border-[#06C755]";

const CategoryPanel = ({ onboarding }) => {
  const {
    categories,
    newCategory,
    setNewCategory,
    addingCategory,
    addCategoryError,
    addCategorySuccess,
    addCategory,
  } = onboarding;

  return (
    <section className={card}>
      <h2 className="text-lg font-bold text-gray-800">🏷️ หมวดหมู่ของคุณ</h2>
      <p className="text-sm text-gray-500 mt-1 mb-5">หมวดส่วนกลาง + หมวดที่คุณสร้างเอง</p>

      <div className="flex flex-wrap gap-2 mb-6">
        {categories.map((cat) => (
          <span
            key={cat.id}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-50 border border-gray-100 text-sm text-gray-700"
          >
            {cat.icon} {cat.name}
          </span>
        ))}
      </div>

      <div className="border-t border-gray-100 pt-5 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">➕ เพิ่มหมวดหมู่ใหม่</h3>
        <div className="grid grid-cols-8 gap-1.5">
          {ICON_OPTIONS.map((icon) => (
            <button
              key={icon}
              type="button"
              aria-label={`เลือกไอคอน ${icon}`}
              aria-pressed={newCategory.icon === icon}
              onClick={() => setNewCategory((c) => ({ ...c, icon }))}
              className={`aspect-square rounded-lg text-lg flex items-center justify-center transition ${
                newCategory.icon === icon
                  ? "bg-green-50 ring-2 ring-[#06C755]"
                  : "bg-gray-50 hover:bg-gray-100"
              }`}
            >
              {icon}
            </button>
          ))}
        </div>
        <input
          className={input}
          aria-label="ชื่อหมวดหมู่ใหม่"
          value={newCategory.name}
          onChange={(e) => setNewCategory((c) => ({ ...c, name: e.target.value }))}
          placeholder="ชื่อหมวดหมู่ เช่น ค่าเช่า"
        />
        <select
          className={input}
          aria-label="หมวดแม่ของหมวดใหม่"
          value={newCategory.parentId ?? ""}
          onChange={(e) =>
            setNewCategory((c) => ({
              ...c,
              parentId: e.target.value ? parseInt(e.target.value) : null,
            }))
          }
        >
          <option value="">หมวดหมู่หลัก (ไม่มีหมวดแม่)</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              อยู่ใต้ {cat.icon} {cat.name}
            </option>
          ))}
        </select>
        {addCategoryError && <p className="text-sm text-red-600">⚠️ {addCategoryError}</p>}
        {addCategorySuccess && <p className="text-sm text-green-600">✅ {addCategorySuccess}</p>}
        <button
          type="button"
          onClick={addCategory}
          disabled={addingCategory}
          className="w-full py-2.5 rounded-xl border-2 border-[#06C755] text-[#06C755] font-semibold text-sm hover:bg-green-50 transition disabled:opacity-50"
        >
          {addingCategory ? "กำลังเพิ่ม..." : `${newCategory.icon} เพิ่มหมวดหมู่`}
        </button>
      </div>
    </section>
  );
};

const BudgetPanel = ({ onboarding }) => {
  const { categories, budgets, loading, setBudget } = onboarding;

  return (
    <section className={card}>
      <h2 className="text-lg font-bold text-gray-800">💰 งบประมาณรายเดือน</h2>
      <p className="text-sm text-gray-500 mt-1 mb-5">
        ใส่เฉพาะหมวดที่ต้องการคุมงบ ปล่อยว่างได้ — จดนิดจะแจ้งเตือนเมื่อใกล้ครบงบ
      </p>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse h-12 bg-gray-100 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="divide-y divide-gray-50">
          {categories.map((cat) => (
            <label key={cat.id} className="flex items-center justify-between gap-4 py-3">
              <span className="flex items-center gap-3 text-sm font-medium text-gray-700">
                <span className="w-9 h-9 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center text-lg">
                  {cat.icon}
                </span>
                {cat.name}
              </span>
              <span className="relative w-40 shrink-0">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
                  ฿
                </span>
                <input
                  type="number"
                  min="0"
                  aria-label={`งบของ ${cat.name} (บาท)`}
                  inputMode="decimal"
                  value={budgets[cat.id] ?? ""}
                  onChange={(e) => setBudget(cat.id, e.target.value)}
                  placeholder="0"
                  className={`${input} pl-7 text-right font-semibold`}
                />
              </span>
            </label>
          ))}
        </div>
      )}
    </section>
  );
};

const SummaryPanel = ({ onboarding }) => {
  const { categories, budgets, hasBudget, saveResults, saving, saved, confirmError, confirm } =
    onboarding;
  const entries = budgetEntries(budgets);
  const catMap = Object.fromEntries(categories.map((c) => [String(c.id), c]));
  const total = entries.reduce((sum, [, value]) => sum + parseFloat(value), 0);

  return (
    <aside className="space-y-4">
      <div className="bg-linear-to-br from-[#06C755] to-[#05b348] p-6 rounded-2xl text-white shadow-xl shadow-green-100/30">
        <p className="text-xs uppercase tracking-wider opacity-80 font-semibold mb-1">
          งบรวมต่อเดือน
        </p>
        <p className="text-3xl font-bold tracking-tight">฿{money(total)}</p>
        <p className="text-xs opacity-80 mt-1">{entries.length} หมวดที่ตั้งงบ</p>
      </div>

      <div className={card}>
        {entries.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">ยังไม่ได้ใส่งบหมวดไหน</p>
        ) : (
          <ul className="space-y-2 mb-4">
            {entries.map(([categoryId, amount]) => {
              const cat = catMap[categoryId];
              const result = saveResults[categoryId];
              return (
                <li key={categoryId} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">
                    {cat?.icon} {cat?.name ?? categoryId}
                  </span>
                  <span className="font-semibold text-gray-800">
                    ฿{money(amount)}
                    {result && (result.success ? " ✅" : " ❌")}
                  </span>
                </li>
              );
            })}
          </ul>
        )}

        {confirmError && <p className="text-sm text-red-600 mb-3">{confirmError}</p>}

        <button
          type="button"
          onClick={confirm}
          disabled={!hasBudget || saving || saved}
          className="w-full py-3 rounded-xl font-bold text-white bg-[#06C755] hover:bg-[#05b348] transition shadow-sm disabled:bg-gray-200 disabled:text-gray-400 disabled:shadow-none"
        >
          {saving ? "กำลังบันทึก..." : saved ? "✅ บันทึกแล้ว" : "บันทึกงบประมาณ"}
        </button>
      </div>
    </aside>
  );
};

export const WebOnboarding = ({ userId }) => {
  const onboarding = useOnboarding(userId);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
          {onboarding.setupBudgetOnly ? "แก้ไขงบประมาณ" : "ตั้งค่าเริ่มต้น 🚀"}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {onboarding.setupBudgetOnly
            ? "ปรับงบรายเดือน หรือเพิ่มหมวดหมู่ใหม่แล้วตั้งงบได้ในหน้าเดียว"
            : "เลือกหมวดหมู่และตั้งงบประมาณรายเดือนก่อนเริ่มจดรายการ"}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* จอแคบเรียง งบ → สรุป+ปุ่มบันทึก → หมวด เพื่อให้ปุ่มบันทึกไม่ไปอยู่ท้ายฟอร์มเพิ่มหมวด */}
        <div className="order-3 lg:order-none lg:col-span-4">
          <CategoryPanel onboarding={onboarding} />
        </div>
        <div className="order-1 lg:order-none lg:col-span-5">
          <BudgetPanel onboarding={onboarding} />
        </div>
        {/* sticky ต้องอยู่ที่ grid item เอง (items-start ทำให้ความสูงเท่าเนื้อหา) — top-24 พ้น navbar h-16 */}
        <div className="order-2 lg:order-none lg:col-span-3 lg:sticky lg:top-24">
          <SummaryPanel onboarding={onboarding} />
        </div>
      </div>
    </main>
  );
};
