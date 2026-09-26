# Backlog — ปัญหาที่ตรวจพบแล้วแต่ยังไม่ได้แก้

ตรวจเมื่อ 2026-09-26 จากโค้ดบน `feature/update-ocr` (`file:line` อ้างอิง ณ commit `e8dba52`)
แบ่งเป็นก้อนตาม branch ที่จะใช้แก้ เรียงตามลำดับที่ตกลงกันไว้ **แก้ข้อไหนแล้วให้ลบออกจากไฟล์นี้ในคอมมิตเดียวกัน**

บริบทที่ใช้ตัดสินลำดับ: production มีผู้ใช้จริงแล้ว, admin console มีผู้ใช้คนเดียว,
web app เป็นตัวช่วยบนคอม (ไม่ใช่เวอร์ชันเต็มของ LIFF)

---

## 2. ทดสอบด้วยมือก่อน deploy (เจ้าของโปรเจกต์ทำเอง)

- ทดสอบเส้นทางหลักใน [manual_test.md](manual_test.md) (จดข้อความ/รูปผ่าน LINE, ยืนยัน/ยกเลิก/undo,
  แก้ผ่าน LIFF) — ปัญหา admin (A-1, A-4, A-6) ระบุใน PR ว่าไปแก้ในก้อนที่ 4

## 3. `feature/liff-fixes` — แก้แล้ว (เหลือข้อเสี่ยงต่ำ)

- postback `confirm` / `cancel` จาก Flex ใช้ `temp_id` โดยไม่ตรวจว่าเป็นของผู้ใช้ที่กด — ข้อมูล postback
  มาจากปุ่มที่ระบบสร้าง ผู้ใช้แก้เองไม่ได้ จึงเสี่ยงต่ำ `helper/webhook_helper.py` (action `confirm`/`cancel`)

## 4. `feature/admin-fixes` — แก้แล้ว (เหลือที่ตั้งใจไม่ทำ/ยังไม่ตัดสินใจ)

- ไม่ทำ UI แยกตามบทบาท และไม่แปล label เป็นไทย (admin console มีผู้ใช้คนเดียว — ตัดสินใจ 2026-09-26)
- `get_current_user` ของ admin เปิด `Session(engine)` เอง แทน `Depends(get_session)` `middleware/auth.py`
- dependency `@heroui/*` / `framer-motion` ใน `package.json` ไม่มีที่ใช้ — ลบหรือเริ่มใช้ ต้องตัดสินใจก่อน
  (CLAUDE.md ระบุว่าเป็น UI library ของ admin)

## 5. `feature/web-app` — ตัวช่วยบนคอม

**ขอบเขตที่ตกลง:** ประวัติรายการกรองเดือน/หมวด + แบ่งหน้า + ยอดรวมรายเดือน, จดหลายรายการ,
แก้ไข/ลบรายการพร้อมปรับงบ, export CSV — ไม่ทำ overview/งบ (ให้ดูใน LIFF) เสร็จแล้วเลิกซ่อนหลัง `?webapp=true`
(ตอนนี้ต้องเปิดด้วย `?webapp=true` ซึ่งจำไว้ใน `sessionStorage["web_mode"]` — ดูคอมเมนต์ใน `initApp`)

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
