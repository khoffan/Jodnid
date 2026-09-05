# Manual Test — เคสที่ต้องทดสอบด้วยมือ

รายการที่ **สคริปต์อัตโนมัติตรวจแทนไม่ได้** เพราะต้องใช้ LINE จริง, Firebase จริง หรือเบราว์เซอร์จริง
ส่วนที่ตรวจอัตโนมัติได้แล้วอยู่ที่ `python scripts/verify_pipeline.py` (ไม่ต้องทำซ้ำที่นี่)

เมื่อทดสอบเสร็จ ให้บันทึกผลลง [verification-log.md](verification-log.md) พร้อมวันที่-เวลา

การเตรียมสภาพแวดล้อม:

```bash
# Backend
source venv/Scripts/activate
python index.py                       # :5005 — ต้องมี ngrok ผูกกับ LINE channel (ดู domain.txt)

# Admin console
cd web/admin-jodnid && npm run dev    # :5000
```

---

## Phase A — Admin system: ความปลอดภัยและการใช้งานพื้นฐาน

เพิ่มเมื่อ 2026-09-06 00:37 (+07)

### A-1 ⚠️ ช่องโหว่ยกระดับสิทธิ์ต้องถูกปิดแล้ว

**ทำไมต้องเทส:** ก่อนแก้ ใครก็ตามที่สมัคร Firebase account เองแล้วยิง `POST /sync` จะกลายเป็น admin ทันที

| ขั้นตอน | ผลที่ต้องได้ |
|---|---|
| 1. ยิง `POST /api/administrator/sync` **โดยไม่แนบ header Authorization** | `403` (HTTPBearer ปฏิเสธ) — ต้องไม่ใช่ `200` |
| 2. สร้าง Firebase account ใหม่ที่ยังไม่มีแถวใน `Administrator` แล้ว login เข้า console | login ไม่ผ่าน / เด้งกลับหน้า login — ต้องไม่หลุดเข้าไปได้ |
| 3. เช็คตาราง `Administrator` หลังข้อ 2 | **ต้องไม่มีแถวใหม่เกิดขึ้น** |

```bash
# ข้อ 1 ตรวจเร็วๆ ด้วย curl
curl -i -X POST http://localhost:5005/api/administrator/sync \
     -H "Content-Type: application/json" \
     -d '{"uid":"attacker-uid","email":"attacker@example.com"}'
```

### A-2 สร้าง admin คนแรกด้วย seed script

```bash
python scripts/seed_admin.py --uid <firebase-uid> --email you@example.com --name "ชื่อคุณ"
python scripts/seed_admin.py --list
```

- [ ] สร้างแล้วขึ้นในรายการ `--list` และ login เข้า console ได้

### A-3 หน้า System Configuration โหลดได้ (เดิมพังสนิท)

**ทำไมต้องเทส:** `get_system_config_data` เคยมี `self` ค้างอยู่ ทำให้ `GET /all` โยน `TypeError` ตารางจึงว่างเปล่าตลอด

- [ ] เปิดหน้าแรกของ console แล้วเห็นตาราง config พร้อมข้อมูล (ไม่ใช่ตารางว่างหรือ spinner ค้าง)
- [ ] Network tab: `GET /api/administrator/all` ตอบ `200` พร้อม `data` เป็น array

### A-4 แก้ไข config ผ่าน modal แล้วบันทึกจริง

**ทำไมต้องเทส:** เดิม frontend ยิง `POST` แต่ backend เป็น `PATCH` (405) และปุ่ม Save แค่ `console.log`

- [ ] กดแก้ config หนึ่งตัว เปลี่ยน `value` และ `description` แล้วกด Save
- [ ] ตารางอัปเดตค่าใหม่ทันทีโดยไม่ต้อง refresh
- [ ] Network tab: `PATCH /api/administrator/config/update` ตอบ `200`
- [ ] เปลี่ยน `name` ให้ซ้ำกับ config ตัวอื่น → ต้องขึ้น alert ว่าชื่อถูกใช้แล้ว ไม่ใช่ 500

### A-5 Toggle แล้วค่ามีผลกับ backend ทันที

**ทำไมต้องเทส:** `get_config_value` ถูก `@lru_cache` และเดิม `clear_config_cache()` ถูกเรียก *ก่อน* เขียน DB

- [ ] เปิด `is_maintenance_mode` ใน console
- [ ] ส่งข้อความเข้า LINE ทันที → ต้องได้ `"ระบบกำลังปรับปรุง กรุณาลองใหม่อีกครั้งภายหลัง"` โดยไม่ต้องรีสตาร์ต backend
- [ ] ปิด `is_maintenance_mode` แล้วส่งอีกครั้ง → กลับมาทำงานปกติ

### A-6 ปิดใช้งาน admin แล้วต้องเข้าไม่ได้

```bash
python scripts/seed_admin.py --uid <firebase-uid> --deactivate
```

- [ ] ผู้ใช้คนนั้นเรียก API ใดๆ ของ admin → ได้ `403 Administrator account is disabled` (ไม่ใช่ `401 Invalid authentication credentials`)
- [ ] `--activate` แล้วกลับมาใช้ได้

### A-7 Backend สตาร์ตได้แม้ยังไม่มีข้อมูล

**ทำไมต้องเทส:** `setup_router()` เคย query ผู้ใช้ทั้งหมดตอน import

- [ ] `python index.py` บน DB เปล่า (ยังไม่มีผู้ใช้เลย) → สตาร์ตผ่าน ไม่มี error

---

## Phase B — สวิตช์ใน console ต้องมีผลกับระบบจริง

เพิ่มเมื่อ 2026-09-06 00:52 (+07)

เตรียมข้อมูลก่อน:

```bash
python scripts/seed_config.py          # สร้าง config พื้นฐาน 3 ตัว (รันซ้ำได้ ไม่ทับค่าเดิม)
python scripts/seed_config.py --list
```

### B-1 ปิด OCR แล้วส่งรูปเข้า LINE

- [ ] ปิดสวิตช์ `is_ocr_active` ใน console
- [ ] ส่งรูปสลิปเข้า LINE → ได้ `"ขออภัยครับ ฟีเจอร์นี้ปิดปรับปรุงชั่วคราว..."` และ **ต้องไม่มีการเรียก Typhoon OCR** (ดู log ว่าไม่มี `module="ocr_pipeline"`)
- [ ] เปิดกลับ → ส่งรูปอีกครั้งแล้วทำงานปกติ **โดยไม่ต้องรีสตาร์ต backend**

### B-2 ปิดการจดด้วยข้อความ

- [ ] ปิดสวิตช์ `is_text_active` → พิมพ์ `"ค่าข้าว 60"` แล้วได้ข้อความแจ้งปิดปรับปรุง
- [ ] เปิดกลับแล้วจดได้ตามปกติ

### B-3 การ์ดสถานะแสดงของจริง

**ทำไมต้องเทส:** เดิมเป็นค่า hardcode `"Active"/"Connected"/"Online"` ตลอด ไม่ว่าระบบจะล่มหรือไม่

- [ ] เปิดหน้าแรก → การ์ด 4 ใบแสดง Database, LINE API, OCR/ข้อความ, Maintenance
- [ ] การ์ด LINE API ขึ้นชื่อ bot จริง (ดึงจาก `GET /v2/bot/info`) ไม่ใช่คำว่า "Online" ลอยๆ
- [ ] ปิดสวิตช์ `is_maintenance_mode` แล้วเปิด → การ์ด Maintenance เปลี่ยนเป็น "กำลังปรับปรุง" สีเหลืองทันที
- [ ] ลองใส่ `LINE_CHANNEL_ACCESS_TOKEN` ผิดแล้วรีสตาร์ต → การ์ด LINE API เป็นสีแดงพร้อม `HTTP 401` (หน้าเว็บต้องไม่พัง)

### B-4 ปุ่ม Refresh Cache

- [ ] แก้ค่า config ในฐานข้อมูลตรงๆ (ไม่ผ่าน console) แล้วกดปุ่ม Refresh Cache
- [ ] ค่าที่ระบบใช้จริงเปลี่ยนตามทันที (ทดสอบด้วย `is_maintenance_mode` แล้วส่งข้อความเข้า LINE)

---

## เส้นทางรับ-จ่าย (จากงานรอบก่อน — ยังค้างอยู่)

- [ ] ส่งรูปใบเสร็จที่มีบรรทัด VAT แยก ตอนเปิดโหมดบันทึกด่วน → บันทึกทันที และยอดที่ตัดจากงบ **รวม VAT**
- [ ] ส่งรูปที่ AI อ่านยอดเพี้ยน → ได้ข้อความเตือน `"⚠️ ยอดรวมที่จดนิดอ่านได้ไม่ตรงกับยอดสุทธิ"` + บิลให้กดยืนยัน (ต้องไม่บันทึกทันที)
- [ ] พิมพ์ข้อความทั่วไปที่ไม่ใช่รายการ เช่น `"วันนี้อากาศดีจัง"` → ได้คำแนะนำวิธีจด ไม่ใช่ `"เกิดข้อผิดพลาด"`
- [ ] เส้นทาง postback: กดยืนยัน / ยกเลิก / undo
- [ ] แก้รายการผ่าน LIFF `?path=/edit-temp/{temp_id}`
