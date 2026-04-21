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
        "กฎเหล็กป้องกันยอดซ้ำ (Strict Rules):\n"
        "1. ตอบเป็น JSON รูปแบบ: {\"transactions\": [...]} เท่านั้น\n"
        "2. การแยกประเภทเอกสาร:\n"
        "   - หากเป็น 'สลิปธนาคาร' (Bank Slip): ให้สกัดเพียง 1 รายการ คือยอดโอนสุทธิ (item: ชื่อผู้รับ, type: expense)\n"
        "   - หากเป็น 'ใบเสร็จร้านค้า' (Receipt): ให้สกัดเฉพาะรายการสินค้าแยกชิ้น (Line Items) + ภาษี + Service Charge\n"
        "3. การสกัดรายการย่อย (Line Items):\n"
        "   - ห้ามดึงยอด 'Grand Total', 'Total', 'Subtotal', 'Amount Due', หรือ 'ยอดรวมสุทธิ' มาเป็นรายการสินค้าเด็ดขาด\n"
        "   - ห้ามสกัดรายการที่เป็นการทวนจำนวนเงิน (เช่น 'รวม 5 รายการ')\n"
        "4. การจัดการภาษีและค่าธรรมเนียม:\n"
        "   - พบ VAT 7% ให้สร้าง item: 'ภาษีมูลค่าเพิ่ม (VAT)', type: 'tax', category: 'อื่นๆ'\n"
        "   - พบ Service Charge ให้สร้าง item: 'ค่าบริการ (Service Charge)', type: 'tax', category: 'อื่นๆ'\n"
        "5. ฟิลด์ที่ต้องมีในทุก Transaction:\n"
        "   - item: ชื่อสินค้า/ผู้รับ (ตามภาษาในใบเสร็จ)\n"
        "   - amount: จำนวนเงินตัวเลข (float)\n"
        "   - category: หมวดหมู่ (ไทยเท่านั้น เช่น อาหาร, การเดินทาง, ช้อปปิ้ง, บันเทิง, อื่นๆ)\n"
        "   - type: 'expense' (สินค้า/บริการ) หรือ 'tax' (ภาษี/ค่าบริการ)\n"
        "6. การตรวจสอบความถูกต้อง (Self-Correction):\n"
        "   - ยอดรวมของทุกรายการใน JSON (รวม tax) ต้องเท่ากับยอด Grand Total ที่ปรากฏจริงในเอกสาร\n"
        "7. กฎการรักษาสมดุลตัวเลข (Balance Rule):\n"
        "   - ยอด Grand Total คือ 'ความจริงสูงสุด' (Single Source of Truth)\n"
        "   - ผลรวมของ (ทุก items ใน JSON) 'ต้อง' เท่ากับ Grand Total เป๊ะๆ\n"
        "   - **สำคัญ:** หากราคาสินค้าในใบเสร็จเป็นราคาที่รวมภาษีแล้ว (Inclusive VAT) ให้ AI คำนวณถอดภาษีออกจากตัวสินค้า เพื่อให้เมื่อบวกกลับกับรายการ 'ภาษีมูลค่าเพิ่ม (VAT)' แล้วยอดรวมต้องไม่เกิน Grand Total\n"
        "8. วิธีจัดการราคาสินค้าและภาษี (Net Price Logic):\n"
        "   - ห้ามสกัดรายการชื่อ 'Vatable', 'ยอดก่อนภาษี' หรือ 'Net Amount'\n"
        "   - หากใบเสร็จระบุราคาสินค้า (เช่น 55.0) และ VAT (เช่น 3.6) โดยมี Grand Total คือ 55.0\n"
        "   - AI ต้องปรับค่าสินค้าเป็น (Grand Total - VAT) = 51.4 และ VAT = 3.6 เพื่อให้รวมกันได้ 55.0 พอดี\n"
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

