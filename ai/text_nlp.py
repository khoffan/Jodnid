import json
from typing import Any, Dict, List

from openai import OpenAI
from sqlmodel import Session

from helper.utils import Utilities


def extract_transactions(
    api_key: str, user_prompt: str, user_id: str, session: Session
) -> List[Dict[str, Any]] | None:
    """
    ฟังก์ชันสำหรับสกัดข้อมูลรายรับ-รายจ่ายจากข้อความผู้ใช้
    คืนค่าเป็น List ของ Dictionary หรือ None หากเกิดข้อผิดพลาด
    """
    client = OpenAI(api_key=api_key, base_url="https://api.opentyphoon.ai/v1")
    available_categories_str = Utilities.generate_system_prompt_categories(
        session=session, user_id=user_id
    )

    system_prompt = (
        "คุณคือ 'AI สมุดบัญชีอัจฉริยะ' ของระบบ JodNid หน้าที่ของคุณคือสกัดข้อมูลจากข้อความหรือสลิป และจัดหมวดหมู่ให้ตรงกับข้อมูลในระบบ\n\n"
        "📋 กฎเหล็กเรื่องหมวดหมู่ (Category Allowed List):\n"
        "คุณต้องเลือกใช้ชื่อหมวดหมู่ที่ระบุในรายการด้านล่างนี้ 'เป๊ะๆ ทุกตัวอักษร' ห้ามคิดชื่อหมวดหมู่ใหม่เองเด็ดขาด:\n"
        f"{available_categories_str}\n"
        "- 'อื่นๆ' (ใช้เมื่อรายการนั้นไม่ตรงกับหมวดหมู่ใดๆ ด้านบนเลยจริงๆ)\n\n"
        "🔍 คำแนะนำในการพิจารณาเลือกหมวดหมู่:\n"
        "1. ให้ความสำคัญกับหมวดหมู่เฉพาะ (Specific) ที่ระบุชื่อชัดเจนก่อนหมวดหมู่กว้างๆ เสมอ\n"
        "   - ตัวอย่าง: หากผู้ใช้พิมพ์ว่า 'ซื้ออาหารเปียกแมว 200' และในรายการมีหมวด 'ของเล่นแมว' หรือ 'สัตว์เลี้ยง' ให้เลือกหมวดนั้นทันที ห้ามนำไปใส่ในหมวด 'อาหารและเครื่องดื่ม' เด็ดขาด\n"
        "2. หากเป็นของกินทั่วไปของมนุษย์ เช่น ข้าว กาแฟ ชาบู ให้เข้าหมวด 'อาหารและเครื่องดื่ม'\n\n"
        "⚠️ กฎเหล็กในการตอบกลับ (Strict JSON Output):\n"
        '1. ตอบกลับเป็น JSON รูปแบบ: {"grand_total": float, "transactions": [...]} เท่านั้น ห้ามมีข้อความเกริ่นนำ\n'
        "2. ยอดสุทธิ (grand_total): ยอดรวมที่จ่ายจริงตามสลิป หากไม่พบให้ใส่ null\n"
        "3. ราคา (amount): ดึงยอดเงินของแต่ละรายการตามจริง ห้ามคำนวณ VAT เอง\n"
        "4. การระบุรายการจริง (is_actual_item):\n"
        "   - set เป็น true: สำหรับสินค้าหรือบริการหลักที่ต้องนำไปรวมให้เท่ากับยอดชำระจริง\n"
        "   - set เป็น false: สำหรับยอดที่ถูกรวมไปแล้วในรายการอื่น หรือยอด Subtotal เพื่อป้องกันการนับซ้ำ\n"
        "5. ลำดับความสำคัญและการคำนวณ (priority):\n"
        "   - true: สำหรับรายการเสริมที่ต้องบวกเพิ่ม (เช่น VAT หรือ Service Charge ที่แยกบรรทัดมา)\n"
        "   - false: สำหรับรายการสินค้าทั่วไป หรือรายการที่รวมทุกอย่างไว้แล้ว\n"
        "6. ความถูกต้อง: ผลรวมของรายการ (is_actual_item=true) + รายการ (priority=true) ต้องเท่ากับ grand_total เสมอ\n\n"
        "🎯 ฟิลด์ข้อมูลที่บังคับในก้อน JSON:\n"
        "- grand_total: ยอดรวมสุทธิ (float หรือ null)\n"
        "- item: ชื่อสินค้า หรือ 'ภาษีมูลค่าเพิ่ม (VAT)'\n"
        "- amount: จำนวนเงิน (float)\n"
        "- category: ชื่อหมวดหมู่ (ต้องสะกดตรงตามรายการด้านบนเป๊ะๆ)\n"
        "- is_actual_item: boolean\n"
        "- priority: boolean\n"
        "- type: 'expense' หรือ 'tax'\n"
    )

    try:
        # ใช้ chat.completions.create แบบปกติ (ไม่ stream เพื่อให้ได้ JSON ก้อนเดียวที่สมบูรณ์)
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # ปรับให้ต่ำลงเพื่อให้ผลลัพธ์คงที่ (Deterministic)
            max_tokens=3000,
            top_p=0.9,
            response_format={"type": "json_object"},  # บังคับให้ตอบเป็น JSON
        )

        # ดึงเนื้อหาออกมา
        content = response.choices[0].message.content
        # แปลง String JSON เป็น Python List/Dict
        data = json.loads(content)

        # ปรับ format เล็กน้อยเผื่อ LLM คืนค่ามาเป็น Dict ที่มี Key ครอบอีกที
        if isinstance(data["transactions"], dict) and "transactions" in data:
            return data

        return data

    except Exception as e:
        print(f"Error extracting transactions: {e}")
        return None


def is_transaction_message(api_key: str, user_prompt: str) -> bool:
    """
    ใช้ AI ตรวจสอบว่าข้อความเป็นรายการรับ-จ่ายหรือไม่
    คืนค่า True หากเป็นรายการ, False หากไม่ใช่
    """
    client = OpenAI(api_key=api_key, base_url="https://api.opentyphoon.ai/v1")

    system_prompt = (
        "Check if the message is about financial transactions (income/expense/buy/sell/pay).\n"
        "Return ONLY 'true' or 'false'. No explanation."
    )

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,  # ต้องการความแม่นยำสูงสุด
            max_tokens=200,  # ใช้ token น้อยมากเพราะตอบแค่คำเดียว
        )

        result = response.choices[0].message.content.strip().lower()
        return "true" in result
    except Exception as e:
        print(f"Validation Error: {e}")
        return True  # Fallback เป็น True เพื่อให้ไปเช็คต่อที่ตัวหลักหาก AI ตัวเล็กพัง
