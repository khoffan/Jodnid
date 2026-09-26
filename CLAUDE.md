# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**JodNid (จดนิด)** — ผู้ช่วยบันทึกรายรับ-รายจ่ายบน LINE ผู้ใช้พิมพ์ข้อความ (`"ค่าข้าว 60"`) หรือส่งรูปสลิป/ใบเสร็จ
ระบบใช้ LLM สกัดยอดเงิน + ชื่อรายการ + หมวดหมู่ ส่ง Flex ให้ยืนยัน (หรือบันทึกทันทีถ้าเปิด bypass mode)
แล้วตัดยอดออกจากงบประมาณรายเดือนของหมวดนั้น

| Path | หน้าที่ | Stack |
|---|---|---|
| root | Backend API + LINE webhook | FastAPI, SQLModel, Alembic |
| [web/dashboard/](web/dashboard/) | LIFF mini-app **และ** web app (bundle เดียวกัน) | Vite + React 19, Zustand, `@line/liff` |
| [web/admin-jodnid/](web/admin-jodnid/) | Admin console (config, log, สถิติ, ผู้ใช้, หมวดหมู่) | Vite + React 19, Firebase Auth |
| [web/jodnid-landing/](web/jodnid-landing/) | Landing page | Next.js 16 App Router, TS |

---

## คำสั่งที่ใช้บ่อย

```bash
# Backend (root)
source venv/Scripts/activate         # Git Bash; PowerShell ใช้ venv\Scripts\activate
pip install -r requirements.txt
python index.py                      # dev: สร้างตาราง แล้วรัน uvicorn --reload บน $PORT (5005)
uvicorn index:app --reload --port 5005   # เหมือนกัน แต่ "ไม่" เรียก create_db_and_tables()

# Migration (alembic ไม่ได้อยู่ใน requirements.txt — ต้อง pip install alembic ก่อน)
alembic revision --autogenerate -m "describe change"
alembic upgrade head

# Frontend
cd web/dashboard      && npm install && npm run dev    # vite :5173
cd web/admin-jodnid   && npm install && npm run dev    # vite :5000 (pin ไว้ใน vite.config.js)
cd web/jodnid-landing && npm install && npm run dev    # next :3000
npm run build && npm run lint
```

- DB ใหม่เอี่ยม: ต้องรัน `python index.py` หรือ `alembic upgrade head` อย่างน้อยหนึ่งครั้ง ไม่งั้นทุก request จะพังเพราะไม่มีตาราง
- `migrations/` อยู่ใน `.gitignore` แต่ถูก track ไว้แล้ว → ไฟล์ revision ใหม่ต้อง `git add -f`
- Webhook ต้องมี public URL ตอน dev — โดเมน ngrok ที่ผูกกับ LINE channel อยู่ใน [domain.txt](domain.txt)
- **ไม่มี test suite** (ไม่มีไฟล์เทส ไม่มี pytest/vitest config ไม่มี CI) → ห้ามอ้างว่า "เทสผ่าน" ให้ตรวจด้วยการรันจริงผ่าน LINE chat / LIFF / admin console
- มีสคริปต์ตรวจสอบที่รันซ้ำได้ 2 ตัว (ไม่ใช่ test framework ไม่มี dependency เพิ่ม):
  `python scripts/verify_pipeline.py` (ออฟไลน์ ไม่ต้องต่อ API/DB) และ
  `python scripts/ocr_bench.py` (วัดคุณภาพ OCR จริง) → **แก้เส้นทางรับ-จ่ายเมื่อไหร่ ให้รัน
  `verify_pipeline.py` ก่อนเสมอ** แล้วบันทึกผลลง [docs/verification-log.md](docs/verification-log.md)
  พร้อมวันที่-เวลา (รายการใหม่ไว้บนสุด)

---

## กฎกลาง (ใช้กับทุกภาษาในรีโปนี้)

✅ **ทำ**
- ข้อความที่ผู้ใช้เห็นทั้งหมดเป็น **ภาษาไทย** และคง emoji นำหน้าไว้ (`✅ บันทึกสำเร็จ`, `⚡ เปิดโหมดบันทึกด่วน`, `⚠️ งบเกินแล้ว!`) — layout ของ Flex/QuickReply พึ่ง emoji พวกนี้ในการสื่อความหมาย
  - **ยกเว้น admin console** — มีผู้ใช้คนเดียว label/ปุ่มภาษาอังกฤษได้ แต่ error ต้องแสดง `detail` ภาษาไทย
    ที่ backend ส่งมา ไม่ใช่ข้อความของ axios (`"Request failed with status code 403"`)
- comment และ docstring ใหม่เขียนภาษาไทยตามของเดิมได้ ผสมศัพท์เทคนิคภาษาอังกฤษ
- แก้เฉพาะบรรทัดที่เกี่ยวข้องกับงาน

❌ **ห้าม**
- ห้าม commit `.env`, `*.db`, `uploads/`, `venv/`, `node_modules/`, `dist/`, `.next/`
- ห้าม log หรือ print ค่า `id_token`, `LINE_CHANNEL_ACCESS_TOKEN`, `FIREBASE_ACCOUNT_KEY`, `TYPHOON_API_KEY`
- ห้าม reformat ทั้งไฟล์ (โปรเจกต์ไม่มี prettier/ruff/black config — diff จะบวมจนรีวิวไม่ได้)
- ห้ามเพิ่ม dependency, test framework, CI, Docker, หรือ formatter config ใหม่โดยไม่ได้ถูกขอ

---

## Python / Backend

### สิ่งที่ต้องรู้ก่อนแก้

**Flow หลัก** `POST /webhook` ([index.py](index.py)) รับ event batch จาก LINE → ผ่านด่าน 3 ชั้นก่อนเสมอ
(maintenance mode → user onboarded หรือยัง → เดือนนี้ตั้งงบหรือยัง) → โยนเข้า `BackgroundTasks` เพื่อให้ตอบ
`200 ok` ทัน timeout → [helper/webhook_helper.py](helper/webhook_helper.py) แยกเป็น text / image / postback

**Text path** ไล่ต้นทุนจากถูกไปแพง: keyword ช่วยเหลือ/ทักทาย (0 ms) → regex `.+\s+\d+` จับรูปแบบ
`"<รายการ> <จำนวน>"` (0 ms ไม่เรียก LLM) → ถ้ามีตัวเลขเท่านั้นจึงเรียก `is_transaction_message()` →
`extract_transactions()`

**Image path** โหลดรูปจาก LINE → `pre_process_image_file` (แก้หมุนตาม EXIF, คงภาพสี, ย่อกว้าง 2000px, q92 —
โหมด `"legacy"` คือ grayscale + contrast ×2 แบบเดิม เก็บไว้เทียบผล) → `run_ocr()` ส่ง **เต็มใบครั้งเดียว**
เป็นค่าเริ่มต้น แบ่งด้วย `split_image_into_text_blocks` เฉพาะรูปที่สูงเกิน 3.5 เท่าของความกว้าง
(`should_split_image`) → OCR ขนานด้วย `ThreadPoolExecutor` 3 workers + retry 429/5xx/timeout 2 ครั้ง →
ต่อกลับ **ตามลำดับ index** พร้อมตัดบรรทัดซ้ำตรงรอยต่อ (`_join_chunk_texts`) → `is_financial_document()`
คัดรูปที่ไม่ใช่ใบเสร็จ → `extract_transactions()` → `summarize_extraction()` เก็บตัวเลขวัดผลลง
`SystemLog.payload` (module `"ocr_pipeline"`)

- **ห้ามใส่ preprocessing แบบ Tesseract (binarize / ดัน contrast) กลับเข้าไปในเส้นทางหลัก** — `typhoon-ocr`
  เป็น vision LLM การทำแบบนั้นทำให้สระ/วรรณยุกต์ไทยและตัวพิมพ์จางบนกระดาษความร้อนหาย
- **ห้ามให้ chunk เดียวที่พังทำให้ทั้งงานพัง** — โอกาสพังคูณตามจำนวนชิ้น (6 ชิ้นที่ 5% ต่อชิ้น = 26%)
- วัดผลก่อนแก้เสมอด้วย [scripts/ocr_bench.py](scripts/ocr_bench.py) (`--init-labels` สร้างไฟล์เฉลย,
  `--stage ocr` วัดชั้นอ่านข้อความอย่างเดียว, `--stage full` วัดถึงชั้นสกัดรายการ)

**Persist** ถ้า `Users.use_bypass_mode` → เขียน `Transactions` เลย; ถ้าไม่ → เขียน `TempTransactions`
แล้วส่ง Flex ที่มีปุ่ม postback `action=confirm&temp_id=…` และปุ่มแก้ไข deep-link ไป
`https://liff.line.me/{LIFF_ID}?path=/edit-temp/{temp_id}`

**AI layer** ทั้งสองโมดูลใน [ai/](ai/) ยิงไป Typhoon ผ่าน OpenAI SDK ที่ base_url
`https://api.opentyphoon.ai/v1` โมเดล `typhoon-v2.5-30b-a3b-instruct`; OCR ใช้ endpoint แยก
`https://api.opentyphoon.ai/v1/ocr` โมเดล `typhoon-ocr` — ใช้ `TYPHOON_API_KEY` ตัวเดียวกันทั้งคู่

### ✅ ทำ

- **Route ใหม่** → เขียนไว้ใน `setup_router()` ของ class ใน [routes/](routes/) (`LiffApi`, `CronAPis`,
  `AdministratorAPIs`) ไม่ใช่สร้าง module-level router ใหม่ — dependency ที่ใช้ร่วม (`logger`,
  `line_access_token`) รับผ่าน `__init__`
- **Route ของ admin** → ต้องมี dependency ตรวจสิทธิ์ **ทุกตัวไม่มีข้อยกเว้น**
  - อ่านอย่างเดียว → `Depends(get_current_user)`
  - เขียนข้อมูล (POST/PATCH/DELETE) → `Depends(require_role(ROLE_ADMIN))` และเรียก
    `audit_log(logger, user, "<action>", {...})` แทน `logger.info` ธรรมดา
  - `scripts/verify_pipeline.py` มีหัวข้อตรวจสองข้อนี้อยู่ ถ้าลืมจะ FAIL ทันที
- **ห้ามให้ endpoint ไหนสร้างแถว `Administrator`** — การเพิ่ม admin ทำผ่าน
  `python scripts/seed_admin.py` เท่านั้น (เคยมีช่องโหว่ให้ใครก็ได้ยกระดับตัวเองเป็น admin)
- **Logic ที่แตะ DB** → เป็น `@staticmethod` ใน `DBManager*` ที่เหมาะสม ([model/db/](model/db/) —
  ไฟล์ละหนึ่งความรับผิดชอบ: `users`, `transactions`, `categories`, `dashboard`, `budget`, `admin`)
  และรับ `session: Session` เป็น argument แรกเสมอ
- **import DBManager** → `from model.db import DBManagerXxx` เท่านั้น ไม่ต้องอ้างชื่อไฟล์ย่อย
  ถ้าเพิ่ม manager ใหม่ ต้อง re-export ใน [model/db/__init__.py](model/db/__init__.py) ด้วย
- **Session ใน route** → `db: Session = Depends(get_session)`
- **ค่า config** → `from core.config_settings import settings` แล้วใช้ `settings.XXX`
- **Feature flag ตอน runtime** → `Utilities.get_config_value(key=...)` และ **ทุกครั้งที่เขียนค่า config
  ต้องเรียก `Utilities.clear_config_cache()`** (ค่านี้ถูก `@lru_cache`)
- **Log** → `logger.info(module="...", message="...", user_id=user_id)` /
  `logger.error(...)` — `module` ควรบอกจุดเกิดจริง เช่น `"webhook_text_ai"`, `"webhook_postback"`
- **แก้ SQLModel ใน [model/models.py](model/models.py)** → สร้าง Alembic revision ในคอมมิตเดียวกันเสมอ
- **งานที่ใช้เวลา** (LLM, OCR, ส่ง push หลายคน) → ผ่าน `BackgroundTasks` หรือ endpoint cron
- **user_id** → เอาจาก `user["sub"]` ของ `Depends(get_current_user)` — route ของ LIFF ที่ยังรับ `user_id`
  ใน path/body (เพื่อให้ frontend เก่าใช้ได้) ต้องผ่าน `ensure_same_user(user, claimed)`
  ([middleware/line_auth.py](middleware/line_auth.py)) แล้วใช้ค่าที่คืนมาเท่านั้น
  `verify_pipeline.py` ตรวจว่าทุก route ของ LIFF มี `get_current_user` ยกเว้นที่อยู่ใน `_LIFF_PUBLIC_ROUTES`
- **ทุกครั้งที่สร้างหรือลบแถว `Transactions`** → ต้องปรับ `UserBudget.current_spent` ให้ตรงกัน
  (`current_spent` เป็นยอดสะสมแบบ denormalized; `undo_transaction` ทำย้อนกลับพร้อม clamp ที่ 0;
  `sync_user_budgets()` คือเครื่องมือซ่อมเมื่อค่าเพี้ยน)
- **ตัดงบที่ parent category** → `category.parent_id or category.id` เสมอ เพื่อให้ sub-category รวมยอดขึ้นแม่
- **เลือกรายการที่จะบันทึก** → ใช้ `select_billable_items(transactions, grand_total)`
  ([model/db/billable.py](model/db/billable.py)) **ที่เดียวเท่านั้น** ห้ามเขียนเงื่อนไข
  `is_actual_item` / `priority` เองซ้ำที่อื่น ตอนนี้ `save_transaction()`,
  `create_dynamic_flex_receipt()` (ทั้งยอดรวมและรายการ) และ `summarize_extraction()` เรียกตัวนี้ร่วมกัน
  ถ้าแยกกันเขียนเมื่อไหร่ บิลที่ผู้ใช้เห็นกับยอดที่ตัดจากงบจะเพี้ยนทันที
  - เชื่อ flag `priority` จาก LLM ตรงๆ ไม่ได้ ใบเสร็จไทยมีทั้งแบบ **แยก VAT** (ต้องบวกเพิ่ม) และ
    **รวม VAT แล้ว** (บรรทัด VAT เป็นข้อมูลเฉยๆ) แต่ LLM ติด `priority=true` ให้เหมือนกันทั้งคู่
    จึงต้องเทียบผลรวมกับ `grand_total` เพื่อตัดสินว่าจะบวกหรือไม่ (วัดแล้ว `grand_total` แม่น 100%)
  - ค่าที่คืนกลับมาตัวที่สองคือผลตรวจยอดแบบ 3 ค่า: `True` ลงตัว / `False` ไม่ลงตัวสักทาง /
    `None` ไม่มี `grand_total` ให้เทียบ **ต้องเช็คด้วย `is False` เสมอ ห้ามใช้ `not matched`**
    ไม่งั้นการจดด้วยข้อความสั้นๆ (ที่ไม่มียอดสุทธิ) จะถูกบังคับให้ยืนยันไปหมด
    `save_transaction()` ส่งค่านี้ออกมาใน key `total_matched` ของ result
- **โหมดบันทึกด่วน (bypass) ไม่ใช่คำสั่งเด็ดขาด** → ทั้ง `handle_text_message` และ
  `handle_image_message` ต้องเรียก `resolve_confirmation()` แทนการอ่าน `user_record.use_bypass_mode`
  ตรงๆ ถ้ายอดไม่ลงตัวให้พาไปเส้นทาง `TempTransactions` + เตือนผู้ใช้ด้วย `send_review_warning()`
  ดีกว่าตัดงบผิดแบบเงียบๆ
- **ด่านคัดว่าเป็นเอกสารการเงินไหม** → `looks_like_money_document()` (regex ตัวเลขเงิน + คำสำคัญ)
  ต้องรันก่อนเสมอ แล้วค่อยตกไปที่ `is_financial_document()` ที่เรียก LLM
  classifier ตัวเล็กตอบไม่คงที่ เคยตีสลิปโอนเงินที่ OCR อ่านครบถ้วนตกมาแล้ว — heuristic ตัดทั้ง
  false negative และ request ทิ้งได้ในตัวเดียว
- **หมวดหมู่ใหม่** → เพิ่มแถวในตาราง `Categories` (`user_id IS NULL` = global, มี `user_id` = ของผู้ใช้คนนั้น)
  prompt จะดึงไปเองผ่าน `generate_system_prompt_categories()`

### ❌ ห้าม

- ❌ ห้าม `os.getenv()` ใน business logic ใหม่ — ใช้ `settings` (ที่มีอยู่ใน `models.py` / `migrations/env.py`
  เป็นข้อยกเว้นเดิม เพราะต้องอ่านก่อน settings พร้อม)
- ❌ ห้ามเปิด `Session(engine)` เองใน route — ใช้ `Depends(get_session)`
- ❌ ห้ามใช้ `print()` แทน logger ในโค้ดใหม่ (ของเดิมมีเยอะ อย่าเพิ่มอีก)
- ❌ ห้ามเรียก logger ใน loop ที่วนถี่ — `JodNidLogger` commit ทุกบรรทัด
- ❌ ห้ามทำงานหนักแบบ synchronous ใน `/webhook` — LINE จะ timeout แล้วยิง event ซ้ำ
- ❌ ห้าม hardcode รายชื่อหมวดหมู่ลงใน system prompt — prompt ต้อง generate จาก DB
- ❌ ห้ามเปลี่ยนชื่อโมเดล Typhoon, base_url, หรือ `response_format={"type": "json_object"}` โดยไม่ได้ถูกขอ
- ❌ ห้ามแก้ field ของ SQLModel แล้วปล่อยให้ `create_all()` จัดการ — production ใช้ Alembic
- ❌ ห้าม `return HTTPException(...)` — ต้อง `raise` (FastAPI จะ serialize เป็น body แล้วตอบ 200)
- ❌ ห้ามเชื่อ `user_id` ที่ส่งมาใน body/path สำหรับ endpoint ที่แตะเงินของผู้ใช้ — ให้ยึด `sub` จาก token
- ❌ ห้ามลบ fallback ที่ classifier คืน `True` ตอน exception — ตั้งใจให้โมเดลเล็กที่ล่มไม่ทำให้ข้อความผู้ใช้หาย

### Style

- ความยาวบรรทัด ~100, double quotes, type hint ครบใน signature
- import จัดกลุ่ม stdlib → third-party → local (`core`, `helper`, `model`, `routes`, `ai`, `middleware`)
- ชื่อฟังก์ชัน DB manager เป็น snake_case กริยานำหน้า (`get_`, `save_`, `update_`, `can_`, `sync_`)

---

## JavaScript / TypeScript (เว็บทั้ง 3 ตัว)

### สิ่งที่ต้องรู้ก่อนแก้

- `web/dashboard` ship bundle เดียวใช้สองที่: [App.jsx](web/dashboard/src/App.jsx) แยกด้วย `isWebApp` เป็น
  `WebPage` (LINE OAuth login, transaction list, add) หรือ `LiffPage` (overview, onboarding, summary,
  edit temp) — **ตอนนี้สาย web เปิดเฉพาะเมื่อขอด้วย `?webapp=true`** (จำไว้ใน `sessionStorage["web_mode"]`
  เพราะ redirect กลับจาก LINE Login ไม่มีพารามิเตอร์นี้) และต้องเปิดนอกแอป LINE และไม่ใช่ลิงก์ LIFF
  (`path` / `liff.state` / `liffClientId`) — เมื่อสาย web พร้อมจะเลิกบังคับ `?webapp=true`
- LIFF deep link ใช้ `?path=/route` ซึ่ง `initApp` อ่านแล้วส่งต่อให้ `navigate()` หลัง login
- Auth คนละชุดกัน: dashboard ใช้ LINE ID token (`sessionStorage["id_token"]`),
  admin ใช้ Firebase ID token (`sessionStorage["token"]`)

### ✅ ทำ

- **เรียก API** → ผ่าน axios instance ใน `common/lib/api.js` ของแอปนั้นเสมอ (มี interceptor แนบ bearer
  token ให้แล้ว)
- **state ที่ข้าม component** → Zustand store ใน `features/<feature>/store/*.store.js`
- **โครงไฟล์ใหม่** → `features/<feature>/{pages,components,store}/` และของใช้ร่วมไว้ `common/`
  (`components`, `guard`, `lib`, `config`)
- **สไตล์** → Tailwind utility class ใน `className` เท่านั้น
- **ข้อความ error / empty state** → ภาษาไทย เช่น `"ไม่สามารถดึงข้อมูลได้"`, `"เกิดข้อผิดพลาดในการเชื่อมต่อ"`
- **route ใหม่ใน dashboard** → เพิ่มใน [LiffPage.jsx](web/dashboard/src/pages/LiffPage.jsx) หรือ
  [webPage.jsx](web/dashboard/src/pages/webPage.jsx) ให้ตรงกับ host ที่จะใช้ และให้ตรงกับ `?path=` ที่ backend
  สร้างไว้ใน Flex
- **แตะ `web/jodnid-landing`** → อ่าน `node_modules/next/dist/docs/` ก่อนเขียนโค้ด (Next.js 16 มี breaking
  change จาก convention เดิม — ดู [AGENTS.md](web/jodnid-landing/AGENTS.md) ของโฟลเดอร์นั้น)
- **env ฝั่ง client** → ต้องขึ้นต้น `VITE_` (Vite) หรือ `NEXT_PUBLIC_` (Next) ถึงจะถูกอ่าน

### ❌ ห้าม

- ❌ ห้ามสร้าง axios instance ใหม่ หรือใส่ `Authorization` header เองในแต่ละ call — interceptor ทำให้แล้ว
  (โค้ดเดิมใน `useTransectionStore.js` ส่ง header ซ้ำเป็น argument ที่ 3 ของ `api.get` ซึ่ง axios ทิ้งไปเฉยๆ —
  อย่าลอกแบบนั้น)
- ❌ ห้ามใช้ `fetch()` ตรงๆ
- ❌ ห้ามเอา secret จริงใส่ตัวแปร `VITE_*` / `NEXT_PUBLIC_*` — มันถูก inline ลง bundle ที่ผู้ใช้เปิดดูได้
- ❌ ห้ามเก็บ token ใน `localStorage` — โปรเจกต์นี้ใช้ `sessionStorage` ทั้งหมด
- ❌ ห้าม `import ... from "react-router-dom"` — ทุกแอปใช้ `react-router` v7 ตรงๆ
- ❌ ห้ามเพิ่ม UI library ใหม่ — dashboard ใช้ `@headlessui/react` + `lucide-react`,
  admin ใช้ `@heroui/react` + `framer-motion`, landing เขียน component เอง
- ❌ ห้ามแปลง `.jsx` เป็น `.tsx` ใน dashboard/admin (TypeScript ใช้เฉพาะ landing)
- ❌ ห้ามเพิ่ม state management ตัวอื่น (Redux, Context สำหรับ global state) — ใช้ Zustand
- ❌ ห้ามเรียก LIFF SDK นอก `web_auth.store.js` — การ init และ login รวมศูนย์อยู่ที่นั่น
- ❌ ห้ามแก้ `web/dashboard/vercel.json` (SPA rewrite ทุก path ไป `index.html`) โดยไม่จำเป็น

### Style

- 2 spaces, double quotes, semicolon, arrow function component แบบ named export
- ESLint กฎเดียวที่ปรับเพิ่ม: `no-unused-vars` ยกเว้นตัวแปรที่ขึ้นต้นด้วยตัวใหญ่หรือ `_`
- ไม่มี prettier config → เขียนให้เข้ากับไฟล์รอบข้าง อย่าจัด format ใหม่ทั้งไฟล์

---

## Environment & Config

- Backend อ่าน config จาก `.env` ผ่าน `pydantic-settings` ตัวเดียว
  ([core/config_settings.py](core/config_settings.py)) โหลดตอน import — key ที่ required หายไป = แอปตายตั้งแต่
  startup
- **`.env.example` ล้าสมัย: ขาด `LINE_REDIRECT_URI`** ซึ่ง `Settings` บังคับ — ถ้าเพิ่ม env ใหม่ ให้เติมทั้ง
  `Settings` และ `.env.example`
- `TEST_MODE` คือสวิตช์ dev/prod ที่เปลี่ยนพฤติกรรมจริง 3 จุด: ใช้ LINE channel token ตัวไหน, ใช้ LIFF id ตัวไหน,
  และรูปใบเสร็จเก็บลง `uploads/` ในเครื่อง หรืออัปขึ้น Cloudinary
- Auth มี 3 ชุดแยกกัน: LIFF/ผู้ใช้ทั่วไป ([middleware/line_auth.py](middleware/line_auth.py) — LINE ID token,
  user id อยู่ที่ `sub`), Admin ([middleware/auth.py](middleware/auth.py) — Firebase token + uid ต้องมีในตาราง
  `Administrator`), Cron ([routes/api_cron_v1.py](routes/api_cron_v1.py) — header `X-Cron-Token` เทียบกับ
  `CRON_SECRET_TOKEN` ผูกเป็น router-level dependency)

---

## บั๊กที่รู้แล้ว — อย่าลอก อย่าคงไว้

รายการเต็มพร้อม `file:line` อยู่ใน [docs/backlog.md](docs/backlog.md) แบ่งตาม branch ที่จะใช้แก้
**ห้ามถือว่าโค้ดเดิมเป็นตัวอย่างที่ถูก** จุดที่ยังผิดกฎข้างบนอยู่:

- `sync_user_budgets` ไม่รวมยอดหมวดย่อยขึ้นแม่ และถูกเรียกจากหน้า overview (GET ที่เขียน DB)
- โค้ด frontend หลายไฟล์ใส่ `Authorization` เอง, `console.log` ข้อมูล token, และใช้ `alert()`
- แก้ข้อไหนแล้ว ให้ลบออกจาก backlog ในคอมมิตเดียวกัน
