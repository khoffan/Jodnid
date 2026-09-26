# บันทึกการตรวจสอบ (Verification Log)

โปรเจกต์นี้ไม่มี test suite และไม่มี CI ([CLAUDE.md](../CLAUDE.md)) การยืนยันว่าโค้ดใช้ได้จริง
จึงต้องรันเองแล้วบันทึกผลไว้ที่นี่ **เพิ่มรายการใหม่ไว้บนสุดเสมอ**

เครื่องมือที่ใช้ประจำ:

| คำสั่ง | ตรวจอะไร | ต้องต่อเน็ต / DB |
|---|---|---|
| `python scripts/verify_pipeline.py` | กติกาและ flow ของเส้นทางรับ-จ่ายทั้งหมด | ไม่ต้อง |
| `python scripts/ocr_bench.py --images uploads --labels bench_labels.json --variants vlm --stage full --user-id <LINE_USER_ID>` | คุณภาพการอ่านใบเสร็จจริง | ต้อง (Typhoon API + DB) |

---

## 2026-09-26 19:18 (+07) — `feature/liff-fixes` (backlog ก้อนที่ 3)

- `sync_user_budgets` รวมยอดหมวดลูกขึ้นแม่ + reset หมวดที่ไม่มีรายจ่ายเป็น 0 และเลิกถูกเรียกจากหน้า
  overview (GET ไม่เขียน DB แล้ว) → ซ่อมผ่าน `POST /api/administrator/users/sync-budgets` หรือ
  cron `POST /api/cron/sync-budgets` (เพิ่ม `sync_all_budgets`)
- หน้าแก้ใบเสร็จ: backend คืน `items` (ผลจาก `select_billable_items`) + `grand_total` → ไม่นับ VAT ซ้ำ,
  เตือนเมื่อยอดไม่ตรง, หมวดจาก LLM ถูกจับคู่กับชื่อจริง, ปุ่มลบเห็นบนมือถือ, มีปุ่มยกเลิก
  (`DELETE /api/temp-transaction/{id}`), สถานะกำลังบันทึก, ไม่บันทึกแถว 0 บาท, แสดง error แทนค้าง
- `confirm-bulk` ตอบ 409 เมื่อบันทึกไม่สำเร็จ (เดิม `success: true` เสมอ)
- `/api/categories/parent` ต้องมี token และคืนหมวดส่วนกลาง + หมวดของผู้ใช้
- Flex สรุปรายวันลิงก์ `/summary/daily` + route `/dashboard/:type` พาข้อความเก่าไปหน้าที่ถูก
- Summary: รายรับแสดง `+฿`, จำนวนรายการจริง, วันตามเดือน, ปีย้อนหลัง 5 ปี; Overview มีลิงก์ไป
  สรุป/ตั้งงบ + แสดง error; LIFF บังคับ onboarding ก่อน; ลบ dead code

### ชุดตรวจอัตโนมัติ

- `python scripts/verify_pipeline.py` → **36/36** (เพิ่ม 6 หัวข้อที่ใช้ SQLite ใน memory: sync รวมยอดขึ้นแม่,
  overview อ่านอย่างเดียว, sync_all_budgets, หมวดที่ใช้ได้, มุมมองหน้าแก้ไข, path ใน Flex มี route จริง)
  — รันก่อนแก้ได้ FAIL 6 ข้อตามคาด
- TestClient + SQLite ชั่วคราว: ช่องโหว่/สิทธิ์ LIFF **33/33** (เพิ่ม temp view, ยกเลิก temp,
  categories/parent), web endpoint **14/14**
- `npm run lint` / `npm run build` ของ dashboard ผ่าน

### ยังไม่ได้ตรวจ

- หน้าแก้ใบเสร็จ / summary / overview บนมือถือจริงใน LINE
- **ต้องตั้ง cron** เรียก `POST /api/cron/sync-budgets` (header `X-Cron-Token`) ทุกคืน — หลัง deploy
  ควรเรียกหนึ่งครั้งเพื่อซ่อมยอดที่เพี้ยนจากสูตรเดิม

---

## 2026-09-26 19:05 (+07) — merge `hotfix/liff-auth` เข้า `feature/update-ocr`

- ปิดช่องโหว่ endpoint ของ LIFF ที่เชื่อ `user_id` จาก path/body: ทุก route ต้องมี token และผ่าน
  `ensure_same_user` (ไม่ตรง = 403), temp ต้องเป็นของตัวเองและยังไม่หมดอายุ (404),
  ตั้งงบ/สร้างหมวดได้เฉพาะหมวดส่วนกลางหรือของตัวเอง, LIFF ขอ token ใหม่เองเมื่อได้ 401
- conflict: `model/db_manament.py` ถูกลบบน branch นี้ → ย้าย `get_user_temp_transaction` ไป
  `model/db/transactions.py` และ `can_use_category` ไป `model/db/categories.py`

### ชุดตรวจอัตโนมัติ

- `python scripts/verify_pipeline.py` → **30/30** (เพิ่ม 2 หัวข้อ: ทุก route ของ LIFF ต้องผ่าน
  `get_current_user` ยกเว้น `_LIFF_PUBLIC_ROUTES`, และ `ensure_same_user` ปฏิเสธ user_id ของคนอื่น)
  - ลองลบ `get_current_user` ออกจาก `/api/dashboard/{user_id}` ชั่วคราว → หัวข้อนี้ FAIL ชี้ route ถูกตัว
- สคริปต์ TestClient + SQLite ชั่วคราว (override `get_current_user`, mock push ของ LINE):
  - ช่องโหว่ LIFF **27/27** — ก่อนแก้ (บน master) รันแล้วเห็นช่องโหว่จริง เช่น เขียนทับงบของคนอื่นได้
    และข้อความ LINE ถูกส่งไปหาคนที่ระบุใน body
  - web endpoint เดิม **14/14**
- `npm run lint` / `npm run build` ของ dashboard ผ่าน

### ยังไม่ได้ตรวจ

- **การขอ token ใหม่เมื่อได้ 401 บนมือถือจริง** — เปิด LIFF ใน LINE ค้าง > 1 ชม. แล้วกดใช้งาน ต้องได้หน้าที่
  โหลดใหม่พร้อมข้อมูล ถ้าเห็น "⚠️ เซสชันหมดอายุ" แปลว่า LIFF คืน token เก่าหลัง `liff.logout()`
- ทุก request ของ LIFF เรียก LINE verify API หนึ่งครั้ง — ดู latency หลัง deploy

---

## 2026-09-26 16:39 (+07) — แก้รายรับ/วันที่จากหน้า web ถูกบันทึกเป็นรายจ่ายวันนี้

- `save_transaction()` อ่าน `type` (เฉพาะ `"income"` เท่านั้นที่เป็นรายรับ — LLM ส่ง `expense`/`tax`
  ซึ่งยังเป็นรายจ่าย) และ `date` (ว่าง / อ่านไม่ออก / อนาคต เช่นปี พ.ศ. → ใช้เวลาปัจจุบัน)
- รายรับไม่ตัดงบ และรายจ่ายตัดงบของ **เดือนที่รายการเกิดจริง** แทนเดือนปัจจุบัน
- ตัดรายรับออกจากยอดใช้จ่ายทุกจุด: `undo_transaction`, `sync_user_budgets`,
  `get_daily_usage` / `get_monthly_usage`, สรุปใน dashboard (เพิ่ม field `type` ในรายการ),
  และยอดเงินรายเดือนในหน้า Stats ของ admin

### ชุดตรวจอัตโนมัติ

- `python scripts/verify_pipeline.py` → **28/28** สองรอบติด
- ทดสอบ endpoint ด้วย `TestClient` + SQLite ชั่วคราว ผ่าน **14/14** (5 เคสเดิม + 9 เคสใหม่):
  รายรับเป็น `income` และไม่ตัดงบ, วันที่เดือนก่อนถูกเก็บและตัดงบเดือนก่อน, `type=tax` ยังเป็นรายจ่าย,
  วันที่ `2569-01-01` ถูกแทนด้วยวันนี้, `get_monthly_usage` ไม่รวมรายรับ,
  undo ทั้งชุดคืนงบเฉพาะรายจ่ายและคืนถูกเดือน

### ยังไม่ได้ตรวจ

- หน้า `/add` และหน้ารายการในเบราว์เซอร์จริง, และหน้า overview ของ LIFF หลังมีรายรับในเดือน
- `sync_user_budgets` กับข้อมูลที่มีรายรับ (ทดสอบแค่ผ่านโค้ด ไม่ได้รันเคสนี้)

---

## 2026-09-26 16:32 (+07) — เปิดใช้งานสาย web app ของ dashboard

- `initApp` เลือกสาย web เมื่อ `?webapp=true` หรือเปิดนอกแอป LINE ยกเว้น URL ที่เป็นลิงก์ LIFF
  (`path` / `liff.state` / `liffClientId`) เพื่อไม่ให้ deep link จาก Flex บน LINE PC หลุดไปหน้า web
- 🔒 **แก้ข้อมูลรั่ว:** `GET /api/web/transactions` เดิมคืนรายการของ **ผู้ใช้ทุกคน** —
  ตอนนี้กรองด้วย `sub` จาก token และเรียงวันที่ล่าสุดก่อน

### ชุดตรวจอัตโนมัติ

- `python scripts/verify_pipeline.py` → รอบแรก **27/28** แล้วรันซ้ำอีก 9 รอบได้ **28/28 ทุกรอบ**
  ไม่สามารถจับได้ว่าหัวข้อไหนตกในรอบแรก (ดูแค่บรรทัดสรุป) → มีหัวข้อที่ผลไม่คงที่อยู่ ควรหาต่อ
- `npm run lint` และ `npm run build` ของ dashboard ผ่าน (มีแค่ warning chunk > 500 kB เดิม)
- ทดสอบ endpoint ด้วย FastAPI `TestClient` + SQLite ชั่วคราว (override `get_current_user` /
  `get_session` ไม่แตะ DB จริง) ผ่าน **5/5**:

| เคส | ผล |
|---|---|
| `POST /web/transaction/add` สำเร็จ | `201 {"success": true}` |
| หลังบันทึก `UserBudget.current_spent` | 0 → 60 |
| บันทึกไม่สำเร็จ | `500 {"detail": "ไม่สามารถบันทึกรายการได้"}` |
| `GET /web/transactions` มีรายการของผู้ใช้อื่นใน DB | เห็นเฉพาะของตัวเอง 1 แถว |
| ไม่มี token | `401` |

### ยังไม่ได้ตรวจ

- LINE Login ผ่านเบราว์เซอร์จริง (`/login` → `/login/callback`) — ต้องมีคนกด login ด้วยบัญชี LINE
  และ callback URL `http://localhost:5173/login/callback` ต้องลงทะเบียนไว้ใน LINE Login channel
- เปิด LIFF ในแอป LINE และลิงก์ `แก้ไข` จาก Flex บน LINE PC ว่ายังไปหน้า LIFF ถูก
- พบบั๊กใหม่ (ยังไม่แก้): รายรับ/วันที่ที่กรอกหน้า `/add` ถูกบันทึกเป็นรายจ่ายวันนี้ (ดู CLAUDE.md)

---

## 2026-09-26 15:38 (+07) — แก้บั๊กที่รู้แล้ว 2 ตัว

- `POST /api/web/transaction/add` เปลี่ยนจาก `return HTTPException` เป็นตอบ `201` พร้อม
  `{"success": true}` และ `raise` 500 เมื่อบันทึกไม่สำเร็จ (ปรับ `web.transaction.store.js`
  ให้อ่าน `res.data.success` ตาม)
- `AuthGuard.jsx` ใช้ `loading` / `isAuth` ที่มีอยู่จริงใน store แทน `isLoading` / `user`

### ชุดตรวจอัตโนมัติ

- `python scripts/verify_pipeline.py` → **ผ่าน 28/28 หัวข้อ** (exit 0)
  — บน Windows ต้องตั้ง `PYTHONIOENCODING=utf-8` ไม่งั้นตอน print ภาษาไทยจะพังด้วย `UnicodeEncodeError`
- `npx eslint` ไฟล์ dashboard ที่แก้ทั้ง 2 ไฟล์ผ่าน ไม่มี warning

### ยังไม่ได้ตรวจ

- ยังไม่ได้ยิง endpoint จริง และยังไม่ได้เปิด dashboard ในเบราว์เซอร์ — สาย web app เป็น dead code
  (`isWebApp` ถูก hardcode เป็น `false`) จึงทดสอบผ่าน UI ไม่ได้จนกว่าจะเปิดคืน

---

## 2026-09-06 01:34 (+07) — Admin system (Phase A–D)

**ครอบคลุมคอมมิต** `d5060cb`, `a16b202`, `98194bc` และคอมมิต Phase D

### ชุดตรวจอัตโนมัติ

```
python scripts/verify_pipeline.py
```

ผล: **ผ่าน 28/28 หัวข้อ** (เพิ่มจาก 14 หัวข้อเดิม เป็นของ admin 14 หัวข้อ)

หัวข้อที่เพิ่มในรอบนี้:

| หัวข้อ | ผลที่ได้ |
|---|---|
| สร้าง router ของ admin ได้โดยไม่แตะ DB ตอน startup | ลงทะเบียน 15 route โดยไม่ query DB |
| ทุก route ของ admin ต้องผ่าน `get_current_user` | ป้องกันครบ 15 route |
| route ที่เขียนข้อมูลต้องบังคับบทบาท admin | ตรวจ 9 route ที่เขียนข้อมูล |
| `require_role` ปฏิเสธบทบาทที่ไม่ได้รับอนุญาต | admin ผ่าน / viewer ได้ 403 |
| การกระทำใน admin ถูกบันทึกเป็น audit log | `module=admin_audit` พร้อม actor/action/รายละเอียด |
| `get_system_config_data` เรียกด้วย session อย่างเดียวได้ | signature ถูก และเรียกได้จริง |
| `sync_administrator_profile` ไม่สร้าง admin ใหม่ | ปฏิเสธและไม่เขียน DB |
| `get_current_user` ปฏิเสธ admin ที่ถูกปิดใช้งาน | ตอบ 403 Forbidden |
| `clear_config_cache` ถูกเรียกหลังเขียน DB | `write -> clear_cache` |
| update/create config คืน error แทนที่จะพังเมื่อชื่อซ้ำ | คืน `success=False` พร้อมข้อความไทย |
| `get_system_status` ไม่ล้มแม้ DB และ LINE API ใช้ไม่ได้ | รายงานสถานะครบโดยไม่ล้ม |
| `feature_enabled` ค่าเริ่มต้นเป็นเปิดเสมอ | ไม่มี config = เปิด / false = ปิด |
| ปิดสวิตช์ OCR แล้ว webhook ต้องไม่ประมวลผลรูป | ปิด = ไม่เรียก handler + แจ้งผู้ใช้ |
| ปิดสวิตช์ข้อความแล้ว webhook ต้องไม่ประมวลผลข้อความ | ปิด = ไม่เรียก handler + แจ้งผู้ใช้ |

> หัวข้อ **"ทุก route ของ admin ต้องผ่าน get_current_user"** คือตัวที่กันไม่ให้ช่องโหว่แบบ
> `POST /sync` ที่ไม่มี auth กลับมาอีกโดยไม่มีใครสังเกต — ไล่ dependency ทั้งต้นไม้จึงรองรับ
> ทั้ง `get_current_user` ตรงๆ และที่ถูกห่อด้วย `require_role()`

### ฝั่ง frontend

- `npm run lint` ของ admin console ผ่าน (ไม่มี warning)
- `npm run build` ผ่าน — 1,815 modules, bundle 446 kB (gzip 136 kB)

### ยังไม่ได้ตรวจ

เคสที่ต้องใช้ Firebase จริง / LINE จริง / เบราว์เซอร์จริง ทั้งหมดอยู่ใน
[manual_test.md](manual_test.md) หมวด Phase A–D **ยังไม่ได้ลงมือทดสอบ** โดยเฉพาะ:

- ช่องโหว่ยกระดับสิทธิ์ (A-1) — ควรยิง curl ยืนยันว่าได้ 403 จริง
- โหลดหน้าแรกของ console (A-3) — จุดที่เคยพังสนิท
- viewer ถูกปฏิเสธเมื่อกดแก้ข้อมูล (D-1)

---

## 2026-09-06 00:09 (+07) — OCR pipeline + กติกาการบันทึกยอด

**ครอบคลุมคอมมิต** `cd7aaf7`, `6c7ac1c`, `aea7d2b` (ทำงานช่วง 2026-09-05 22:49 – 23:02)

### 1. ชุดตรวจอัตโนมัติแบบออฟไลน์

```
python scripts/verify_pipeline.py
```

ผล: **ผ่าน 14/14 หัวข้อ** (exit code 0)

| หัวข้อ | ผลที่ได้ |
|---|---|
| `pre_process_image_file` หมุนรูปตาม EXIF | `(900, 400)` → `(400, 900)` |
| `pre_process_image_file` โหมด vlm/legacy | `vlm=RGB`, `legacy=L` |
| `should_split_image` แบ่งเฉพาะรูปยาวผิดปกติ | ยาว (aspect 4.0) = แบ่ง, ปกติ (1.5) = ไม่แบ่ง |
| `split_image_into_text_blocks` ไม่ทำข้อความหาย | 5 ชิ้น, เก็บข้อความ 100%, 26 ms |
| `_join_chunk_texts` ตัดบรรทัดซ้ำตรงรอยต่อ | ซ้ำถูกตัด / ไม่ซ้ำต่อครบ |
| `looks_like_money_document` | สลิป-ใบเสร็จผ่าน, ข้อความทั่วไปไม่ผ่าน |
| `select_billable_items` | ผ่าน 6 รูปแบบใบเสร็จ |
| บิลที่ผู้ใช้เห็น = ยอดที่บันทึก | ใบแยก VAT ฿269.00 / ใบรวม VAT ฿110.00 |
| `resolve_confirmation` | ผ่าน 6 สถานการณ์ |
| ข้อความทั่วไปตอบคำแนะนำ ไม่ใช่ error | ตอบคำแนะนำวิธีจด |
| bypass ON + ยอดไม่ลงตัว (ข้อความ) | ไม่บันทึก + เตือน + รอยืนยัน |
| bypass ON + ยอดลงตัว (ข้อความ) | บันทึกทันที พร้อม `grand_total` |
| bypass ON + ยอดไม่ลงตัว (รูป) | ไม่บันทึก + เตือน + รอยืนยัน |
| bypass ON + ยอดลงตัว (รูป) | บันทึกทันที + ผูก `attachment_id` |

### 2. วัดคุณภาพการอ่านใบเสร็จจริง (ยิง Typhoon API)

```
python scripts/ocr_bench.py --images uploads --labels bench_labels.json \
    --variants vlm --stage full --user-id Uca724fb6c9bffd7d8606e754e160eac3
```

ชุดข้อมูล: ใบเสร็จ/สลิปจริงจาก `uploads/` **6 ใบ** ที่ label ยอดจริงไว้ใน `bench_labels.json`
(เป็นรูปถ่ายจริง มีทั้งสลิปโอนเงินและใบเสร็จ POS ที่ถือถ่ายเอียงบนโต๊ะ)

| metric | ก่อนแก้ | หลังแก้ |
|---|---|---|
| `ocr_ok` | 100% (6/6) | 100% (6/6) |
| `total_hit` — OCR อ่านยอดจริงเจอ | 100% (6/6) | 100% (6/6) |
| `total_exact` — LLM สกัด `grand_total` ถูก | 100% (6/6) | 100% (6/6) |
| **`saved_match` — ยอดที่ตัดจากงบถูก** | **67% (4/6)** | **100% (6/6)** |
| p50 latency | 6,380 ms | 5,424 ms |

รายใบหลังแก้ (ทุกใบ `total_matched=True`, ผ่านด่าน `looks_like_money_document` หมด):

```
เฉลย 1,500.00 → ตัดจากงบ 1,500.00   เลือก 1/2 รายการ
เฉลย 2,800.00 → ตัดจากงบ 2,800.00   เลือก 1/2 รายการ
เฉลย   269.00 → ตัดจากงบ   269.00   เลือก 4/4 รายการ   (ใบแยก VAT: บวกเพิ่ม)
เฉลย   110.00 → ตัดจากงบ   110.00   เลือก 1/2 รายการ   (ใบรวม VAT: ไม่บวกซ้ำ)
เฉลย   199.00 → ตัดจากงบ   199.45   เลือก 4/4 รายการ   (ต่าง 0.45 อยู่ในเกณฑ์ ±1 บาท)
เฉลย    45.00 → ตัดจากงบ    45.00   เลือก 1/2 รายการ
```

### 3. ตรวจโครงสร้างหลังแยกไฟล์ `model/db/`

- เทียบ `inspect.getsource()` ของ manager ทั้ง 6 คลาส + `select_billable_items` + `_amount_of`
  ระหว่างโมดูลเดิมกับโมดูลใหม่ → **ตรงกันทุกตัวอักษร** ไม่มีโค้ดตกหล่นหรือถูกแก้ระหว่างย้าย
- `python -m py_compile` ผ่านทุกไฟล์ที่แก้
- `import index` ผ่าน (ยืนยันว่าไม่มี circular import จากการย้าย `select_billable_items`)
- ไล่ import ทุก route: `api_liff_v1`, `api_cron_v1`, `api_administrator_v1` ผ่านหมด
- `grep` ยืนยันไม่เหลือ reference ถึง `model.db_manament` ทั้งในโค้ดและเอกสาร

### 4. สแกนหาตัวแปรที่ใช้ก่อนถูก assign

สแกน AST ทุกฟังก์ชันใน `helper/webhook_helper.py` → ไม่เหลือจุดที่ใช้ตัวแปรก่อน assign
(ก่อนหน้านี้มี 3 จุด: `quick_reply` 2 จุด และ `result` 1 จุด)

### ยังไม่ได้ตรวจ

- **ยังไม่ได้ยิงผ่าน LINE chat จริง** — เคสที่ควรลองก่อน merge:
  1. ส่งรูปใบเสร็จที่มีบรรทัด VAT แยก ตอนเปิดโหมดบันทึกด่วน → ต้องบันทึกทันที และยอดต้องรวม VAT
  2. ส่งรูปที่ AI อ่านยอดเพี้ยน → ต้องได้ข้อความเตือน + บิลให้กดยืนยัน ไม่ใช่บันทึกทันที
  3. พิมพ์ข้อความทั่วไปที่ไม่ใช่รายการ → ต้องได้คำแนะนำวิธีจด ไม่ใช่ "เกิดข้อผิดพลาด"
- ชุดข้อมูลวัดผลมีแค่ 6 ใบ ใน `uploads/` ยังมีอีก ~30 ใบที่ยัง label ไม่ครบ
- ยังไม่ได้ทดสอบเส้นทาง postback (ยืนยัน/ยกเลิก/undo) และเส้นทางแก้ผ่าน LIFF
