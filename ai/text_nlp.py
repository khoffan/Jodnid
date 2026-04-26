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
        "คุณคือ 'AI สมุดบัญชีอัจฉริยะ' หน้าที่คือสกัดข้อมูลและจัดหมวดหมู่ให้ตรงกับฐานข้อมูลของระบบ JodNid\n"
        "เป้าหมาย: สกัดชื่อสินค้า ราคา และจัดเข้า 5 หมวดหมู่หลักตามที่กำหนดเท่านั้น\n\n"
        
        "📋 กฎการจัดหมวดหมู่ (Category Mapping):\n"
        "ให้เลือกใช้ชื่อหมวดหมู่ที่ระบุไว้ด้านล่างนี้ 'เป๊ะๆ' เพื่อให้ระบบ Map เข้า Database ได้ถูกต้อง:\n"
        "1. 'อาหารและเครื่องดื่ม': อาหารสด/แห้ง, ขนม, กาแฟ, มื้ออาหาร, วัตถุดิบปรุงอาหาร\n"
        "2. 'การเดินทาง': ค่าน้ำมัน, ค่ารถสาธารณะ (BTS/MRT), Grab, ค่าที่จอดรถ, แท็กซี่\n"
        "3. 'ที่อยู่อาศัยและของใช้': ค่าเช่าห้อง, ค่าผ่อนบ้าน/คอนโด, ค่าส่วนกลาง, ค่าน้ำ/ไฟ/เน็ต, ของใช้ในบ้าน (ทิชชู่/ผงซักฟอก)\n"
        "4. 'ช้อปปิ้งและบันเทิง': เสื้อผ้า, ของฟุ่มเฟือย, เกม, เติมเกม, ดูหนัง, อุปกรณ์อิเล็กทรอนิกส์\n"
        "5. 'อื่นๆ': รายการที่ไม่เข้าพวกข้างต้น หรือยอดปรับสมดุล\n\n"

        "⚠️ กฎเหล็ก (Strict Rules):\n"
        "1. ตอบเป็น JSON รูปแบบ: {\"transactions\": [...]} เท่านั้น\n"
        "2. ราคา (Amount): ดึงยอดเงินตามที่ปรากฏจริงหลังชื่อสินค้า (Face Value) ห้ามคำนวณ VAT เอง\n"
        "3. การระบุรายการจริง (is_actual_item):\n"
        "   - set เป็น true: สำหรับสินค้าหรือบริการที่ต้องนำไปบวกให้เท่ากับยอดชำระจริง\n"
        "   - set เป็น false: สำหรับยอดที่ถูกรวมไปแล้ว เช่น 'ภาษี (VAT)', 'Service Charge'\n"
        "4. ความถูกต้อง: ผลรวมของรายการที่เป็น true ต้องเท่ากับยอดชำระสุทธิ (Grand Total) เสมอ\n\n"

        "🔍 ฟิลด์ข้อมูลที่บังคับ:\n"
        "- item: ชื่อสินค้า หรือ 'ภาษีมูลค่าเพิ่ม (VAT)'\n"
        "- amount: จำนวนเงิน (float)\n"
        "- category: ชื่อหมวดหมู่ (ต้องตรงกับ 5 ชื่อข้างต้นเท่านั้น)\n"
        "- is_actual_item: boolean\n"
        "- type: 'expense' หรือ 'tax'\n"
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
            max_tokens=200  # ใช้ token น้อยมากเพราะตอบแค่คำเดียว
        )

        result = response.choices[0].message.content.strip().lower()
        return "true" in result
    except Exception as e:
        print(f"Validation Error: {e}")
        return True # Fallback เป็น True เพื่อให้ไปเช็คต่อที่ตัวหลักหาก AI ตัวเล็กพัง

