import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import requests
from openai import OpenAI
from sqlmodel import Session

from ai.text_nlp import extract_transactions
from helper.logger import JodNidLogger
from helper.utils import Utilities
from model.db import select_billable_items

OCR_TIMEOUT_SECONDS = 45
OCR_MAX_PARALLEL_WORKERS = 3
OCR_MAX_ATTEMPTS = 3  # ยิงครั้งแรก + retry อีก 2 ครั้ง
OCR_RETRY_BACKOFF_SECONDS = 1.5  # หน่วงแบบเพิ่มขึ้น: 1.5s แล้ว 3.0s
OCR_RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
OCR_SPLIT_ASPECT_RATIO = 3.5  # สูงเกิน 3.5 เท่าของความกว้างค่อยแบ่งเป็นชิ้นย่อย
OCR_RAW_TEXT_LOG_LIMIT = 1500  # ตัดข้อความดิบก่อนเก็บลง log


def _extract_texts_from_ocr_result(result: dict[str, Any]) -> list[str]:
    extracted_texts = []
    for page_result in result.get("results", []):
        if page_result.get("success") and page_result.get("message"):
            content = page_result["message"]["choices"][0]["message"]["content"]
            try:
                parsed_content = json.loads(content)
                text = parsed_content.get("natural_text", content)
            except json.JSONDecodeError:
                text = content
            extracted_texts.append(text)
    return extracted_texts


def _ocr_single_chunk(chunk_bytes: bytes, filename: str, api_key: str, chunk_index: int) -> dict:
    """
    ยิง OCR หนึ่งชิ้น พร้อม retry เมื่อเจอปัญหาชั่วคราว (429 / 5xx / timeout)
    การแบ่งรูปทำให้โอกาสพังทบกันหลายเท่า ถ้าไม่ retry รูปเดียวพังทั้งใบ
    """
    url = "https://api.opentyphoon.ai/v1/ocr"
    model = "typhoon-ocr"
    task_type = "default"
    max_tokens = 16384
    temperature = 0.1
    top_p = 0.6
    repetition_penalty = 1.2

    files = {"file": (f"{filename}-part-{chunk_index + 1}.jpg", chunk_bytes, "image/jpeg")}
    data = {
        "model": model,
        "task_type": task_type,
        "max_tokens": str(max_tokens),
        "temperature": str(temperature),
        "top_p": str(top_p),
        "repetition_penalty": str(repetition_penalty),
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    last_error = "unknown OCR error"
    attempt = 0
    for attempt in range(1, OCR_MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=OCR_TIMEOUT_SECONDS,
            )
        except requests.RequestException as e:
            last_error = f"OCR request error: {e}"
        else:
            if response.status_code == 200:
                chunk_text = "\n".join(_extract_texts_from_ocr_result(response.json())).strip()
                if chunk_text:
                    return {
                        "success": True,
                        "index": chunk_index,
                        "text": chunk_text,
                        "attempts": attempt,
                    }
                # ชิ้นที่ไม่มีตัวหนังสือเลย (เช่นโลโก้ล้วน) ยิงซ้ำก็ได้ผลเดิม
                last_error = "Empty OCR text from chunk"
                break

            last_error = f"OCR request failed ({response.status_code}): {response.text[:200]}"
            if response.status_code not in OCR_RETRY_STATUS:
                break

        if attempt < OCR_MAX_ATTEMPTS:
            time.sleep(OCR_RETRY_BACKOFF_SECONDS * attempt)

    return {"success": False, "index": chunk_index, "error": last_error, "attempts": attempt}


def _join_chunk_texts(texts: list[str], max_overlap_lines: int = 10) -> str:
    """
    ต่อข้อความจากแต่ละชิ้นเข้าด้วยกัน พร้อมตัดบรรทัดที่ซ้ำตรงรอยต่อ

    ชิ้นที่แบ่งมาซ้อนทับกันเล็กน้อยเพื่อกันข้อความตกหล่น ผลข้างเคียงคือบรรทัดตรงรอยต่อ
    ถูกอ่านซ้ำสองรอบ ถ้าปล่อยไว้ LLM จะนับยอดของบรรทัดนั้นซ้ำ ทำให้ยอดรวมเกินจริง
    """
    joined: list[str] = []
    for text in texts:
        lines = text.splitlines()
        if joined:
            tail = [line.strip() for line in joined[-max_overlap_lines:] if line.strip()]
            drop_count = 0
            for size in range(min(max_overlap_lines, len(lines)), 0, -1):
                head = [line.strip() for line in lines[:size] if line.strip()]
                if head and len(head) <= len(tail) and tail[-len(head) :] == head:
                    drop_count = size
                    break
            lines = lines[drop_count:]
        joined.extend(lines)

    return "\n".join(joined).strip()


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def summarize_extraction(data: Any) -> dict[str, Any]:
    """
    สรุปตัวเลขของผลลัพธ์ที่ LLM สกัดมา ไว้ใช้วัดคุณภาพ pipeline

    `amount_saved` คำนวณด้วย `select_billable_items()` ตัวเดียวกับที่ `save_transaction()` ใช้
    จึงเป็นยอดที่จะถูกตัดจากงบผู้ใช้จริง ถ้าไม่ตรงกับ `grand_total` แปลว่ายอดที่ผู้ใช้เห็น
    กับยอดที่ระบบตัดไม่ตรงกัน
    """
    items = data.get("transactions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []

    grand_total = _to_float(data.get("grand_total")) if isinstance(data, dict) else None
    amount_all = sum(_to_float(item.get("amount")) or 0.0 for item in items if isinstance(item, dict))

    billable_items, total_matched = select_billable_items(items, grand_total)
    amount_saved = sum(_to_float(item.get("amount")) or 0.0 for item in billable_items)

    return {
        "item_count": len(items),
        "billable_count": len(billable_items),
        "grand_total": grand_total,
        "amount_all": round(amount_all, 2),
        "amount_saved": round(amount_saved, 2),
        "total_diff": None if grand_total is None else round(amount_saved - grand_total, 2),
        "total_matched": total_matched,
    }


# ตัวเลขเงินที่มีทศนิยม 2 ตำแหน่ง เช่น 2,800.00 หรือ 269.00
_MONEY_PATTERN = re.compile(r"\d{1,3}(?:,\d{3})*\.\d{2}")
_MONEY_KEYWORDS = (
    "บาท",
    "฿",
    "thb",
    "จำนวนเงิน",
    "ยอด",
    "รวม",
    "สุทธิ",
    "total",
    "amount",
    "ใบเสร็จ",
    "ใบกำกับ",
    "โอนเงิน",
    "ชำระ",
    "เงินสด",
    "ภาษี",
    "vat",
    "cash",
    "ราคา",
)


def looks_like_money_document(ocr_text: str) -> bool:
    """
    ด่านตรวจแบบ deterministic: ถ้าข้อความมีทั้งตัวเลขเงินและคำที่บ่งบอกว่าเป็นเรื่องเงิน
    ให้ถือว่าเป็นเอกสารการเงินได้เลย ไม่ต้องถาม LLM ซ้ำ

    จำเป็นเพราะ classifier ตัวเล็กตอบไม่คงที่ เคยตีสลิปโอนเงินที่ OCR อ่านได้ครบถ้วนตกมาแล้ว
    ผู้ใช้จะเจอข้อความ "อ่านรูปไม่ได้" ทั้งที่ระบบอ่านได้ — ตัดทิ้งได้ทั้งความผิดพลาดและ 1 request
    """
    if not ocr_text or not _MONEY_PATTERN.search(ocr_text):
        return False
    lowered = ocr_text.lower()
    return any(keyword in lowered for keyword in _MONEY_KEYWORDS)


def is_financial_document(api_key: str, ocr_text: str) -> bool:
    client = OpenAI(api_key=api_key, base_url="https://api.opentyphoon.ai/v1")

    # ปรับ Prompt ให้ยอมรับ Shopping Receipt มากขึ้น
    system_prompt = (
        "You are a financial document classifier.\n"
        "Analyze if the text is a Bank Slip, POS Receipt, Tax Invoice, or Restaurant Bill.\n"
        "Criteria for 'true':\n"
        "- Contains a Total Amount (e.g., Baht, THB, Total, Amount Due).\n"
        "- Contains a Transaction Date.\n"
        "- Contains either a Shop Name, Merchant Name, or Bank Name.\n"
        "Return 'true' if it looks like a record of spending money. Return 'false' otherwise.\n"
        "Answer ONLY 'true' or 'false'."
    )

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ocr_text[:1500]},  # เพิ่มเป็น 1500 เผื่อหัวใบเสร็จยาว
            ],
            temperature=0,
            max_tokens=600,
        )
        result = response.choices[0].message.content.strip().lower()
        return "true" in result
    except Exception as e:
        print(f"Image Validation Error: {e}")
        return True


def run_ocr(
    image_bytes: bytes,
    filename: str,
    api_key: str,
    force_split: Optional[bool] = None,
) -> dict[str, Any]:
    """
    อ่านข้อความจากรูปด้วย typhoon-ocr แล้วคืนข้อความดิบ + ข้อมูลสำหรับวัดผล

    - ค่าเริ่มต้นคือส่ง "ทั้งใบ" ครั้งเดียว เพราะ vision LLM ต้องเห็นโครงสร้างทั้งใบ
      ถึงจะจับคู่ชื่อรายการกับคอลัมน์ราคาได้ถูก และการแบ่งทำให้โอกาสพังคูณตามจำนวนชิ้น
    - แบ่งเฉพาะใบเสร็จที่ยาวผิดปกติเท่านั้น (ดู `should_split_image`)
    - ชิ้นที่พังบางส่วนไม่ทำให้ทั้งงานพัง ตราบใดที่อ่านสำเร็จเกินครึ่ง
    """
    started_at = time.monotonic()

    should_split = (
        Utilities.should_split_image(image_bytes, OCR_SPLIT_ASPECT_RATIO)
        if force_split is None
        else force_split
    )
    if should_split:
        split_chunks = Utilities.split_image_into_text_blocks(image_bytes) or [image_bytes]
    else:
        split_chunks = [image_bytes]

    meta: dict[str, Any] = {
        "chunk_count": len(split_chunks),
        "chunk_failed": 0,
        "split": len(split_chunks) > 1,
        "attempts_max": 0,
        "ocr_char_count": 0,
    }

    chunk_results: list[dict] = []
    chunk_errors: list[str] = []
    max_workers = min(OCR_MAX_PARALLEL_WORKERS, len(split_chunks))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_ocr_single_chunk, chunk_bytes, filename, api_key, idx): idx
            for idx, chunk_bytes in enumerate(split_chunks)
        }

        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                result = future.result()
            except Exception as e:
                chunk_errors.append(f"chunk {idx}: {e}")
                continue

            meta["attempts_max"] = max(meta["attempts_max"], result.get("attempts", 1))
            if result.get("success"):
                chunk_results.append(result)
            else:
                chunk_errors.append(f"chunk {result['index']}: {result.get('error')}")

    meta["chunk_failed"] = len(chunk_errors)
    meta["latency_ocr_ms"] = int((time.monotonic() - started_at) * 1000)

    # ยอมให้บางชิ้นพังได้ ขอแค่ยังอ่านได้เกินครึ่ง — ได้ข้อมูลบางส่วนดีกว่าไม่ได้อะไรเลย
    if not chunk_results or len(chunk_results) * 2 < len(split_chunks):
        meta["fail_reason"] = "; ".join(chunk_errors)[:500] or "no OCR result"
        return {"success": False, "error": meta["fail_reason"], "meta": meta}

    chunk_results.sort(key=lambda item: item["index"])
    full_text = _join_chunk_texts([item["text"] for item in chunk_results])
    meta["ocr_char_count"] = len(full_text)
    if chunk_errors:
        meta["chunk_error_sample"] = chunk_errors[0][:200]

    return {"success": True, "text": full_text, "meta": meta}


def extract_text_from_image(
    image_path: bytes,
    filename: str,
    api_key: str,
    user_id: str,
    session: Session,
    logger: Optional[JodNidLogger] = None,
):
    started_at = time.monotonic()
    ocr_result = run_ocr(image_bytes=image_path, filename=filename, api_key=api_key)
    meta = ocr_result["meta"]
    meta["filename"] = filename

    def _finish(payload: dict[str, Any]) -> dict[str, Any]:
        meta["latency_total_ms"] = int((time.monotonic() - started_at) * 1000)
        if logger:
            level = "ok" if payload.get("success") else "failed"
            logger.info(
                module="ocr_pipeline",
                message=f"ocr {level}: {meta.get('fail_reason', 'extracted')}",
                user_id=user_id,
                payload=meta,
            )
        payload["meta"] = meta
        return payload

    if not ocr_result["success"]:
        return _finish({"success": False, "error": ocr_result["error"]})

    full_text = ocr_result["text"]
    meta["raw_text"] = full_text[:OCR_RAW_TEXT_LOG_LIMIT]

    if looks_like_money_document(full_text):
        meta["financial_check"] = "heuristic"
    else:
        meta["financial_check"] = "llm"
        if not is_financial_document(api_key, full_text):
            meta["fail_reason"] = "not a financial document"
            return _finish({"success": False, "error": "Not a financial document"})

    response = extract_transactions(api_key, full_text, user_id, session)
    if response is None:
        meta["fail_reason"] = "extraction returned none"
        return _finish({"success": False, "error": "Failed to extract transactions"})

    meta.update(summarize_extraction(response))
    return _finish({"success": True, "text": response})
