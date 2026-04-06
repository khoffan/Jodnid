from openai import OpenAI
import json

def extract_transactions(api_key: str, user_prompt: str):
    """
    ฟังก์ชันสำหรับสกัดข้อมูลรายรับ-รายจ่ายจากข้อความผู้ใช้
    คืนค่าเป็น List ของ Dictionary หรือ None หากเกิดข้อผิดพลาด
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.opentyphoon.ai/v1"
    )

    system_prompt = (
        "คุณคือ 'AI สมุดบัญชีอัจฉริยะ' หน้าที่ของคุณคือสกัดข้อมูลจากใบเสร็จ/สลิปอย่างละเอียด\n"
        "กฎการสกัดข้อมูล (Strict Rules):\n"
        "1. ตอบเป็น JSON รูปแบบ: {\"transactions\": [...]} เท่านั้น\n"
        "2. การแยกรายการ (Line Items):\n"
        "   - ให้ดึงรายการสินค้าแต่ละชิ้นแยกกัน (item, amount, category)\n"
        "   - **ห้าม** ดึงยอด 'Grand Total' หรือ 'ยอดรวมสุทธิ' มาเป็นรายการสินค้า เพื่อป้องกันยอดซ้ำซ้อน\n"
        "3. การจัดการภาษีและค่าธรรมเนียม (Tax & Service Charge):\n"
        "   - หากพบยอด VAT 7% ให้สร้าง item ชื่อ 'ภาษีมูลค่าเพิ่ม (VAT)'\n"
        "   - หากพบยอด Service Charge ให้สร้าง item ชื่อ 'ค่าบริการ (Service Charge)'\n"
        "   - รายการเหล่านี้ให้ใช้ type: 'tax' และ category: 'อื่นๆ'\n"
        "4. ฟิลด์ที่บังคับมี:\n"
        "   - item: ชื่อสินค้า หรือ 'ภาษีมูลค่าเพิ่ม (VAT)'\n"
        "   - amount: ตัวเลขจำนวนเงิน (float)\n"
        "   - category: หมวดหมู่สินค้า (เช่น อาหาร, ช้อปปิ้ง) หรือ 'อื่นๆ' สำหรับ tax\n"
        "   - type: 'expense' (สำหรับสินค้าทั่วไป) หรือ 'tax' (สำหรับภาษี/ค่าบริการ)\n"
        "5. หากเป็นสลิปโอนเงิน (Bank Slip) ที่มีรายการเดียว: ให้ดึงชื่อผู้รับ/รายการ และยอดเงินโอนสุทธิมาเป็นรายการเดียว (type: expense)"
    )

    try:
        # ใช้ chat.completions.create แบบปกติ (ไม่ stream เพื่อให้ได้ JSON ก้อนเดียวที่สมบูรณ์)
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, # ปรับให้ต่ำลงเพื่อให้ผลลัพธ์คงที่ (Deterministic)
            max_tokens=2000,
            top_p=0.9,
            response_format={"type": "json_object"} # บังคับให้ตอบเป็น JSON
        )

        # ดึงเนื้อหาออกมา
        content = response.choices[0].message.content
        
        # แปลง String JSON เป็น Python List/Dict
        transactions = json.loads(content)
        
        # ปรับ format เล็กน้อยเผื่อ LLM คืนค่ามาเป็น Dict ที่มี Key ครอบอีกที
        if isinstance(transactions, dict) and "transactions" in transactions:
            return transactions["transactions"]
        
        return transactions

    except Exception as e:
        print(f"Error extracting transactions: {e}")
        return None

def is_transaction_message(api_key: str, user_prompt: str) -> bool:
    """
    ใช้ AI ตรวจสอบว่าข้อความเป็นรายการรับ-จ่ายหรือไม่ 
    คืนค่า True หากเป็นรายการ, False หากไม่ใช่
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.opentyphoon.ai/v1"
    )

    system_prompt = (
        "Check if the message is about financial transactions (income/expense/buy/sell/pay).\n"
        "Return ONLY 'true' or 'false'. No explanation."
    )

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0, # ต้องการความแม่นยำสูงสุด
            max_tokens=50  # ใช้ token น้อยมากเพราะตอบแค่คำเดียว
        )

        result = response.choices[0].message.content.strip().lower()
        return "true" in result
    except Exception as e:
        print(f"Validation Error: {e}")
        return True # Fallback เป็น True เพื่อให้ไปเช็คต่อที่ตัวหลักหาก AI ตัวเล็กพัง

