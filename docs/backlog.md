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
- admin ที่ถูกปิดใช้งานระหว่างเปิด console อยู่ยังค้างที่หน้าเดิม (ทุก call ได้ 403 + ข้อความ) จนกว่าจะ reload —
  ยังไม่มี response interceptor ที่พาออกจากระบบ `web/admin-jodnid/src/common/lib/api.js`
- โปรไฟล์ล้างชื่อ/เบอร์ให้ว่างไม่ได้ (`sync_administrator_profile` ข้ามค่าว่าง) `model/db/admin.py` — ตัดสินใจไม่แก้ (2026-09-26)

## 5. `feature/web-app` — แก้แล้ว (เหลือเล็กน้อย)

- วันที่ทั้งระบบเก็บแบบไม่มี timezone และใช้ `datetime.now()` ของเครื่อง server — server ต้องตั้งเป็น
  Asia/Bangkok ไม่งั้นรายการช่วง 00:00–07:00 จะตกไปวัน/เดือนก่อน (ทั้ง LINE, LIFF และเว็บ)
- login บนเว็บอยู่ได้เฉพาะแท็บเดิม (`sessionStorage`) และไม่เกินอายุ ID token (~1 ชม.) — ตั้งใจตามกฎ
  "ห้ามเก็บ token ใน localStorage" ถ้าต้องการให้อยู่นานกว่านี้ต้องทำ session ฝั่ง backend
