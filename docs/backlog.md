# Backlog — ปัญหาที่ตรวจพบแล้วแต่ยังไม่ได้แก้

ตรวจเมื่อ 2026-09-26 จากโค้ดบน `feature/update-ocr` (`file:line` อ้างอิง ณ commit `e8dba52`)
แบ่งเป็นก้อนตาม branch ที่จะใช้แก้ เรียงตามลำดับที่ตกลงกันไว้ **แก้ข้อไหนแล้วให้ลบออกจากไฟล์นี้ในคอมมิตเดียวกัน**

บริบทที่ใช้ตัดสินลำดับ: production มีผู้ใช้จริงแล้ว, admin console มีผู้ใช้คนเดียว,
web app เป็นตัวช่วยบนคอม (ไม่ใช่เวอร์ชันเต็มของ LIFF)

---

## 1. `hotfix/liff-auth` — แตกจาก `master` แล้ว deploy ก่อน

endpoint ของ LIFF เชื่อ `user_id` จาก path/body และไม่มี `get_current_user` → ใครรู้ LINE user id ของคนอื่น
ก็อ่าน/เขียนข้อมูลเงินของคนนั้นได้ แก้โดย **คง URL เดิม** แต่เทียบ `user_id` กับ `sub` (ไม่ตรง = 403)
เพื่อไม่ให้ LIFF เวอร์ชันเก่าที่ผู้ใช้เปิดค้างไว้พัง

- `GET /api/dashboard/{user_id}` — อ่านสรุปของคนอื่นได้ `routes/api_liff_v1.py:156-173`
- `POST /api/overview/stats` — เชื่อ body `user_id` `routes/api_liff_v1.py:175-192`
- `POST /api/budget/setup` — เขียนทับงบของคนอื่นได้ `routes/api_liff_v1.py:219-239`
- `GET /api/budgets/{user_id}` `routes/api_liff_v1.py:241-258`
- `POST /api/categories/add` — สร้างหมวดใส่บัญชีคนอื่น + ไม่ตรวจเจ้าของ `parent_id` `routes/api_liff_v1.py:266-285`
- `GET /api/temp-transaction/{temp_id}` — ไม่ตรวจเจ้าของ, ไม่ตรวจ `expires_at`, log `data` ทั้งก้อน
  และใช้ `user_id` ค้างจาก startup `routes/api_liff_v1.py:54-57,194-202`
- `POST /api/transactions/confirm-bulk` — ไม่มี auth, push ข้อความไปหา body `user_id` (ส่งหาใครก็ได้),
  ตอบ `success: true` เสมอแม้ temp หายหรือยืนยันไปแล้ว `routes/api_liff_v1.py:204-215`,
  `helper/webhook_helper.py:606,642`
- บังคับ auth แล้วจะเกิดอาการใหม่: LIFF ที่เปิดค้างเกิน ~1 ชม. ได้ 401 แล้วแสดง ฿0 เงียบๆ →
  ต้องขอ token ใหม่ผ่าน LIFF แล้ว reload หนึ่งครั้ง `web/dashboard/src/common/lib/api.js:21-32`

## 2. ก่อน merge `feature/update-ocr`

- ซ่อนสาย web ไว้หลัง `?webapp=true` จนกว่าก้อนที่ 5 จะเสร็จ
  `web/dashboard/src/features/webapp/auth/store/web_auth.store.js:88-96`
- ทดสอบเส้นทางหลักใน [manual_test.md](manual_test.md) (จดข้อความ/รูปผ่าน LINE, ยืนยัน/ยกเลิก/undo,
  แก้ผ่าน LIFF) — ปัญหา admin (A-1, A-4, A-6) ระบุใน PR ว่าไปแก้ในก้อนที่ 4

## 3. `feature/liff-fixes`

**ยอดเงินผิด**
- `sync_user_budgets` group ตาม `category_id` ลูก ไม่รวมขึ้นแม่ และหมวดที่ยอดลดเหลือ 0 ไม่ถูก reset
  `model/db/budget.py:93-123` — และถูกเรียกทุกครั้งที่เปิด overview (`helper/utils.py:767`) ทำให้ GET
  เขียน DB → overview ต้องอ่านอย่างเดียว, `sync_user_budgets` เป็นเครื่องมือซ่อม (ปุ่มใน admin + cron ทุกคืน)
- แก้ผ่าน EditTemp ไม่ส่ง `grand_total` → `select_billable_items(items, None)` บวก VAT ทุกบรรทัด
  ใบแบบรวม VAT ถูกตัดงบเกิน `model/db/transactions.py:158-174`
  → EditTemp แสดงเฉพาะบรรทัดที่จะบันทึก (ผลจาก `select_billable_items`) + ยอดสุทธิ, ยอดไม่ตรงให้เตือน
  แต่บันทึกได้ และยึดตามที่ผู้ใช้แก้
- `/api/categories/parent` คืนเฉพาะหมวด global → หมวดที่ผู้ใช้สร้างไม่ขึ้นใน onboarding / add / edit
  `model/db/categories.py:149-153`

**หน้าที่พัง**
- ปุ่มสรุปรายวันใน Flex ลิงก์ `?path=/dashboard/daily` แต่ route คือ `/summary/:type`
  `helper/utils.py:603` vs `web/dashboard/src/pages/LiffPage.jsx:18,26`
- (ต้องยืนยัน) เปิดครั้งแรกผ่าน `liff.line.me` URL มี `liff.state=?path=…` แทน `path` → deep link หาย
  `web_auth.store.js:89,172`
- `initApp` ล้ม → `userId` เป็น null แล้ว LiffPage หมุนค้าง, ไม่แสดง `error` `pages/LiffPage.jsx:32`
- EditTemp: temp หาย/หมดอายุ/ยืนยันแล้ว → ค้างที่ "กำลังโหลดข้อมูลดิบ..." `EditTempPage.jsx:20-26,58`
- EditTemp: label ใช้ `cat.emoji` ที่ไม่มี (field คือ `icon`) `EditTempPage.jsx:120`
- EditTemp: ปุ่มลบเป็น `opacity-0 group-hover` มองไม่เห็นบนมือถือ `EditTempPage.jsx:78`
- EditTemp: แถวใหม่ default หมวด `"อาหาร"` ที่ไม่มีจริง `EditTempPage.jsx:133`
- EditTemp: select ผูกกับค่าจาก LLM เช่น `"🍔 อาหาร…"` ที่ไม่ตรง option → UI โชว์ตัวแรกแต่บันทึกค่าเดิม
  `EditTempPage.jsx:113-123`
- EditTemp: ไม่มีสถานะกำลังบันทึก (กดซ้ำได้), ไม่มีปุ่มยกเลิก temp, บันทึกแถว 0 บาท `EditTempPage.jsx:43-56,142-148`
- Summary: ทุกแถวแสดง `-฿` รวมรายรับ, จำนวน "รายการ" คือแค่ 10 แถวแรก
  `features/transactions/pages/Dashboard.jsx:168,194`, `model/db/dashboard.py:85`
- Summary: ตัวเลือกวันมี 1–31 ทุกเดือน, ปีมีแค่ 2 ปี `Dashboard.jsx:69-76`

**ยังไม่ครบ**
- Overview ไปหน้า `/summary/*` หรือ `/setup` ไม่ได้, ไม่แสดง `error`, แสดง 0 ก่อนเริ่มโหลด
  `features/dashboard/pages/OverviewPage.jsx:8,22,29-85`
- ไม่มี onboarding guard ในสาย LIFF — deep link ข้าม onboarding ได้ `web_auth.store.js:172-180`
- `setOnboardStatus` ไม่ set `isOnboarded: true` ใน store `web_auth.store.js:40-46`
- LIFF logout ไม่ล้าง `userId` / sessionStorage `web_auth.store.js:236-239`
- `useTransectionStore.js` ส่ง `Authorization` เป็น argument ที่ 3 ของ `api.get` (ผิดกฎ) `:24-34`
- dead code: `completeOnboarding`, `setOnboardingData`, `clearStore`, `clearOverview`,
  `TransectionDetail.jsx` (มี placeholder `https://your-api.com/`)
- ข้อความอังกฤษ "Details" `CategoryItem.jsx:33`, `index.html` เป็น `lang="en"` + title `dashboard`

## 4. `feature/admin-fixes` — แก้เฉพาะที่พัง (ไม่ทำ UI แยกบทบาท ไม่แปลไทย)

**พัง**
- import `./common/guard/authGuard` ไม่ตรงตัวพิมพ์กับไฟล์ `AuthGuard.jsx` → build บน Linux/Vercel พัง
  `web/admin-jodnid/src/App.jsx:9`
- interceptor ใช้ token ที่ cache ไว้ ไม่ให้ Firebase refresh → 401 ทุก call หลัง ~1 ชม.
  และ `getIdToken(null)` throw ตอนยังไม่ login `web/admin-jodnid/src/common/lib/api.js:16-25`
- Firebase account ที่ไม่ใช่ admin (หรือ admin ที่ถูกปิด) ยังเข้า console ได้ — `/sync` ตอบ 401 แต่ Firebase
  ยัง signed in และ AuthGuard ปล่อยผ่าน `App.jsx:34-36,49`, `common/guard/AuthGuard.jsx:30`,
  `features/authentication/store/auth.store.js:30-32`
- ข้อความ error ตอน login ไม่เคยขึ้น (LoginPage ถูก unmount ระหว่าง `isLoading`)
  `auth.store.js:14`, `App.jsx:40-45`, `LoginPage.jsx:17-19`
- create/toggle/update config ที่ backend ตอบ `200 {success:false}` ถูกกลืนเงียบ
  `features/systemConfiguration/store/system-config.store.js:45,61,72`
- ช่องแก้ชื่อ config ผูกกับ `selectedConfig.name` แทน `localName` พิมพ์ไม่ได้ `ConfigModel.jsx:86,90`
- ฟอร์มสร้าง config ชนิด boolean/json มี input ซ้อนสองอัน และ boolean ส่งค่า `""`
  `CreateConfigModal.jsx:157,183-193,204-222`
- ล้างค่า config ไม่ได้ (`if not key or not value`) `routes/api_administrator_v1.py:255,278`

**ความปลอดภัย**
- `console.log(result)` พิมพ์ `UserCredential` ที่มี token `auth.store.js:16,27`
- logout ไม่ลบ `sessionStorage["token"]` `auth.store.js:45-48`
- Firebase persistence เป็น IndexedDB (ไม่ใช่ session) `common/firebase/firebase_config.js:17`
- audit actor ปลอมได้ — `/sync` เขียน `email` จาก body แล้ว `audit_log` ใช้เป็น actor
  `routes/api_administrator_v1.py:200`, `model/db/admin.py:34-35`
- audit log ถูกเขียนก่อนรู้ผล แม้การกระทำล้มเหลว `routes/api_administrator_v1.py:117,138,153,169,226,257,280`
- 401 detail ส่งข้อความ exception ภายในออกไป `middleware/auth.py:75`

**ยังไม่ครบ**
- แสดง `detail` ภาษาไทยจาก backend แทนข้อความ axios ภาษาอังกฤษ ทุก store
  (`system-config.store.js:38,65,78`, `categories.store.js:28,41,54`, `users.store.js:44`, `ProfilePage.jsx:49`)
- config ไม่ตรวจค่าตาม `value_type` ฝั่ง backend → ค่า int/json ผิดทำให้ `get_config_value` พังใน webhook
  `model/db/admin.py:50-65,121-158`, `helper/utils.py:1031`
- ปุ่ม "ซ่อมยอดงบ" (`sync_user_budgets`) ในหน้าผู้ใช้ — มาจากก้อนที่ 3
- Profile: phone ไม่ถูกบันทึก, ชื่อไม่อัปเดต `Administrator.name`, `user` มีสองรูปแบบ
  `ProfilePage.jsx:13-14,29,111-125`, `auth.store.js:26-28` vs `App.jsx:35`
- ลบ `signUp` ที่ไม่ได้ใช้ `auth.store.js:35-44`, dependency `@heroui/*` / `framer-motion` ไม่ได้ใช้

## 5. `feature/web-app` — ตัวช่วยบนคอม

**ขอบเขตที่ตกลง:** ประวัติรายการกรองเดือน/หมวด + แบ่งหน้า + ยอดรวมรายเดือน, จดหลายรายการ,
แก้ไข/ลบรายการพร้อมปรับงบ, export CSV — ไม่ทำ overview/งบ (ให้ดูใน LIFF) เสร็จแล้วเลิกซ่อนหลัง `?webapp=true`

**พัง**
- refresh แล้ว `/api/user/onboarding-status` ได้ 401 ไม่มี try/catch → หมุนค้าง `web_auth.store.js:98-125`
- onboarding วนกลับ `/setup` หลัง refresh `Onboarding.jsx:208-212`, `web_auth.store.js:40-46`
- login ครั้งแรก `isOnboarded` ค้างเป็น `true` → ผู้ใช้ใหม่เห็นแค่ขั้นตั้งงบ `LineCallbackPage.jsx:35,48-50`
- คลิกรายการไป `/edit-temp/{tx.id}` ที่ไม่มีใน WebPage (และเป็น id ผิดชนิด) → หน้าขาว
  `TransactionListPage.jsx:169`, `pages/webPage.jsx:15-24`
- วันที่ default ใช้ `toISOString()` (UTC) ก่อน 07:00 ได้เมื่อวาน `AddTransactionPage.jsx:17`
- `get_Transactions` ใช้ inner join → รายการที่ไม่มีหมวดหาย `model/db/transactions.py:363-364`
- (ต้องยืนยัน) `LINE_REDIRECT_URI` ต้องตรงกับ `origin + "/login/callback"` ทุก environment

**ความปลอดภัย**
- OAuth `state` ไม่ถูกเก็บและตรวจ `web_auth.store.js:208`, `LineCallbackPage.jsx:18`
- `console.log("LINE Login Response:", res.data)` พิมพ์ `id_token` `LineCallbackPage.jsx:30`

**ยังไม่ครบ / กฎ**
- token หมดอายุ → พาไปหน้า login, logout ไม่ล้าง store อื่น, `/login` ไม่ redirect คนที่ login แล้ว,
  callback ส่ง code ซ้ำตอน refresh/StrictMode
- navbar ไม่มีลิงก์กลับหน้ารายการ `WebNavbar.jsx:14-20`, route `/setup` ซ้ำ `webPage.jsx:21-22`
- รายการไม่มี loading/error state, ไอคอนหมวด hardcode ตาม id `TransactionListPage.jsx:20-29,35-75,158`
- Add: note บังคับแต่ label บอก "(เพิ่มเติม)", โหลดหมวดพลาดแค่ console.log `AddTransactionPage.jsx:46-48,73-77`
- Onboarding: บันทึกพลาดบางส่วนแล้วกดซ้ำไม่ได้แต่ถูกนับว่า onboard แล้ว, error 400 ไม่แสดง `detail`
  `Onboarding.jsx:121-122,187-188,206-209,380`
- ใส่ `Authorization` เอง `TransactionListPage.jsx:43-50`, `web.transaction.store.js:13-17`
- `console.log` ค้าง, คอมเมนต์ TODO/Mock, ข้อความอังกฤษ ("Logout", "Login", footer), `alert()` แทนข้อความในหน้า
