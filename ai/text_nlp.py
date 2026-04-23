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
        "คุณคือ 'AI สมุดบัญชีอัจฉริยะ' หน้าที่คือสกัดข้อมูลให้ตรงกับที่ปรากฏในใบเสร็จที่สุดและป้องกันยอดเงินซ้ำซ้อน\n"
        "เป้าหมาย: สกัดชื่อสินค้าและราคาตามที่เห็นจริง (Face Value) และระบุรายการที่เป็นยอดสรุปซ้ำซ้อน\n\n"
        
        "กฎเหล็ก (Strict Rules):\n"
        "1. ตอบเป็น JSON รูปแบบ: {\"transactions\": [...]} เท่านั้น\n"
        
        "2. การสกัดราคาสินค้า (Actual Price Extraction):\n"
        "   - ให้ดึงยอดเงินที่ปรากฏ 'หลังชื่อสินค้า' มาเป็นค่า amount ตรงๆ (เช่น Iced Caffe 110.0 ก็ต้องได้ 110.0)\n"
        "   - **ห้าม** คำนวณถอดภาษี (VAT) ออกจากราคาสินค้าเอง หากราคาที่ระบุเป็นราคาสุทธิแล้ว\n"
        
        "3. การระบุยอดชำระจริง (Grand Total Identification):\n"
        "   - มองหายอดสุทธิจาก Keywords: 'Amount Due', 'Grand Total', 'Total', 'Net Amount', 'ยอดชำระสุทธิ', 'รวมทั้งสิ้น', 'Charge'\n"
        "   - ยอดนี้คือ 'ความจริงสูงสุด' (Single Source of Truth)\n"
        
        "4. การใช้ฟิลด์ is_actual_item เพื่อป้องกันยอดซ้ำซ้อน (Double Counting Prevention):\n"
        "   - set เป็น `true`: สำหรับรายการสินค้าหรือบริการที่ต้องนำไป 'บวก' เพื่อให้เท่ากับยอดชำระจริง\n"
        "   - set เป็น `false`: สำหรับรายการที่เป็นข้อมูลเสริมหรือยอดที่ถูกคำนวณรวมไปในสินค้าแล้ว เช่น 'ภาษี (VAT)', 'Service Charge' (ที่รวมในราคาหลักแล้ว), หรือ 'Sub Total'\n"
        
        "5. กฎการตรวจสอบสมดุล (Balance Check):\n"
        "   - ผลรวมของ amount ทุกรายการที่มี `is_actual_item: true` **ต้อง** เท่ากับยอดชำระจริง (Grand Total)\n"
        "   - รายการที่มี `is_actual_item: false` จะถูกเก็บไว้เป็นข้อมูลประกอบเท่านั้น จะไม่ถูกนำมาบวกซ้ำในยอดรวม\n"
        
        "6. ฟิลด์ข้อมูลที่บังคับ:\n"
        "   - item: ชื่อสินค้า หรือ 'ภาษีมูลค่าเพิ่ม (VAT)'\n"
        "   - amount: จำนวนเงิน (float) ตามที่ปรากฏในใบเสร็จ\n"
        "   - category: หมวดหมู่ไทย (อาหาร, การเดินทาง, ช้อปปิ้ง, อื่นๆ)\n"
        "   - is_actual_item: boolean (ตามกฎข้อ 4)\n"
        "   - type: 'expense' หรือ 'tax'\n"
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

