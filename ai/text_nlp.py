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
        "คุณคือ 'AI สมุดบัญชีอัจฉริยะ' หน้าที่ของคุณคือสกัดข้อมูลรายรับ-รายจ่ายจากข้อความภาษาไทย\n"
        "กฎเหล็ก:\n"
        "1. ตอบกลับเป็น JSON format เท่านั้น (Array of Objects)\n"
        "2. แยกรายการ (Transactions) ออกมาให้ชัดเจนหากมีการซื้อหลายอย่าง\n"
        "3. ระบุฟิลด์: item (ชื่อรายการ), amount (จำนวนเงิน), category (หมวดหมู่), และ type (income หรือ expense)\n"
        "4. ไม่ต้องทักทาย ไม่ต้องมีคำเกริ่น หรือแสดงความคิดเห็นส่วนตัว\n"
        "5. หากข้อมูลไม่ชัดเจน ให้ใช้ความฉลาดของ LLM ในการวิเคราะห์หมวดหมู่ที่เหมาะสมที่สุด"
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
            max_tokens=512,
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

# --- วิธีการใช้งาน ---
# my_api_key = "YOUR_TYPHOON_API_KEY"
# user_text = "ผมซื้อข้าวที่ร้านมาเรียม 60 บาทพร้อมกับน้ำอัดลม 17 บาทจาก 7/11"
# results = extract_transactions(my_api_key, user_text)

# if results:
#     for txn in results:
#         print(f"รายการ: {txn['item']} | ยอด: {txn['amount']} | หมวดหมู่: {txn['category']}")