import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlmodel import Session
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
import os

# function
from ai.ocr import extract_text_from_image
from ai.text_nlp import (
    extract_transactions,
    is_transaction_message
)
from helper.helper import (
    get_content_line,
    create_dynamic_flex_receipt,
    get_instruction_flex,
    get_line_profile,
    send_line_reply_v3,
    send_loading_indicator_v3,
    save_line_image,
    send_push_notification,
    get_daily_usage,
    get_monthly_usage,
    get_all_users
)

# database service
from model.db_manament import (
    get_or_create_user,
    save_temp_transaction,
    confirm_and_save_transaction,
    create_attachment_record,
    get_dashboard_data,
    setup_user_budget,
    delete_temp_transaction
)
from model.models import get_session


load_dotenv()

app = fastapi.FastAPI()

origin = [
    "https://jodnid.vercel.app",
    os.getenv("FRONTEND_URL"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Usage
api_key = os.getenv("TYPHOON_API_KEY")
line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

header_scheme = APIKeyHeader(name="X-Cron-Token", auto_error=False)

def verify_cron_token(token: str = Security(header_scheme)):
    expected_token = os.getenv("CRON_SECRET_TOKEN")
    if not token or token != expected_token:
        raise HTTPException(
            status_code=403, 
            detail="Could not validate credentials"
        )
    return token


class UserMessage(BaseModel):
    message: str

class LineWebhook(BaseModel):
    destination: str
    events: List[Dict[str, Any]]

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/webhook")
async def line_webhook(data: LineWebhook):
    for event in data.events:
        # 1. ดึง UID และประเภทของ Event
        user_id = event.get("source", {}).get("userId")
        reply_token = event.get("replyToken")
        event_type = event.get("type")

        get_or_create_user(line_user_id=user_id)

        temp_id = None

        if event_type == "message":
            message = event.get("message", {})
            msg_type = message.get("type")
            
            # bot conversation condition
            # รายการคำสำคัญ (Keywords)
            HELPER_KEYWORDS = ["ช่วยด้วย", "วิธีใช้", "ทำอะไรได้บ้าง", "สอนหน่อย"]
            GREETING_KEYWORDS = ["สวัสดี", "hello", "hi", "เริ่ม"]
            SUMMARY_KEYWORDS = ["ขอดูยอด", "สรุปยอด", "ใช้ไปเท่าไหร่"]
            
            # transaction condition
            final_transactions = None
            if msg_type == "text":
                user_text = message.get("text")
                user_text_lower = user_text.lower()
                print(f"[{user_id}] Text: {user_text}")
                send_loading_indicator_v3(user_id=user_id, seconds=10)
                is_transaction = is_transaction_message(api_key, user_text)
                print(f"Is Transaction: {is_transaction}")

                                # --- 1. คำสั่งช่วยเหลือ (Help/Guidance) ---
                if any(k in user_text_lower for k in HELPER_KEYWORDS):
                    send_line_reply_v3(reply_token, alt_text="คําแนะนำ",  flex_json=get_instruction_flex()) # ส่ง Flex คำแนะนำที่เราคุยกัน
                
                # --- 2. คำทักทาย (Greetings) ---
                elif any(k in user_text_lower for k in GREETING_KEYWORDS):
                    profile = get_line_profile(user_id=user_id, line_token=line_access_token)
                    user_name = profile.get("displayName", "คุณ")
                    greeting_text = (
                        f"สวัสดีครับคุณ {user_name}! 🙏\n"
                        "ผม 'จดนิด' พร้อมช่วยบันทึกรายจ่ายให้คุณแล้ว\n"
                        "ลองพิมพ์ 'ค่าข้าว 60' หรือส่งรูปสลิปมาได้เลยครับ"
                    )
                    send_line_reply_v3(reply_token, text=greeting_text)

                elif is_transaction:
                    # ส่งไปให้ Typhoon วิเคราะห์รายการ
                    final_transactions = extract_transactions(api_key, user_text)
                    print(f"Extracted Transactions: {final_transactions}")
                    temp_id = save_temp_transaction(user_id, final_transactions)
                    
                    # TODO: บันทึกลง Database โดยผูกกับ user_id
                    # TODO: Reply กลับหา User ผ่าน LINE Messaging API
                    # return {"status": "success", "type": "text", "result": final_transection}
                else:
                    print("Not a transaction message.")
                    guidance_text = (
                        "🤖 จดนิด ยังไม่เข้าใจรายการนี้ครับ\n\n"
                        "💡 วิธีจดที่ถูกต้อง:\n"
                        "• พิมพ์ [รายการ] [จำนวนเงิน]\n"
                        "  เช่น 'ค่าข้าว 60' หรือ 'ได้เงินเดือน 30000'\n"
                        "• ส่งรูป 'สลิปโอนเงิน' ได้เลย\n\n"
                        "⚠️ สิ่งที่จดไม่ได้:\n"
                        "• ข้อความทักทายหรือคุยเล่น\n"
                        "• ข้อความที่ไม่มีตัวเลขจำนวนเงิน"
                    )
                    # (Option) คุณอาจจะส่งข้อความกลับไปบอก User ว่าไม่พบรายการในข้อความนี้ก็ได้
                    send_line_reply_v3(reply_token, text=guidance_text)

            # กรณีที่ 2: เป็นรูปภาพ (Image)
            elif msg_type == "image":
                message_id = message.get("id")
                print(f"[{user_id}] Image ID: {message_id}")
                send_loading_indicator_v3(user_id=user_id, seconds=20)
                image_bytes = get_content_line(message_id, line_token=line_access_token)
                if image_bytes is None:
                    print("Failed to download image")
                    return {"status": "error", "message": "Failed to download image"}
                # NOTE: LINE ไม่ได้ส่งไฟล์รูปมาตรงๆ แต่ส่ง message_id มา
                # คุณต้องเขียนฟังก์ชันไป get รูปจาก LINE API มาก่อน (ใช้ Channel Access Token)
                # จากนั้นค่อยส่งไฟล์นั้นไปที่ extract_text_from_image
                save_file = save_line_image(user_id=user_id, message_id=message_id, image_bytes=image_bytes)
                if save_file:
                    attachment_id = create_attachment_record(user_id=user_id, file_path=save_file, file_type="image/jpeg")
                    # ตัวอย่าง Flow:
                    # image_bytes = download_line_image(message_id)
                    ocr_json = extract_text_from_image(image_bytes, f"{message_id}.jpg", api_key)
                    status = ocr_json.get("success")
                    if not status:
                        print(f"OCR failed: {ocr_json.get('error')}")
                        send_line_reply_v3(reply_token, text="ขออภัยครับ ระบบไม่สามารถอ่านข้อมูลจากรูปนี้ได้ กรุณาลองใหม่อีกครั้งด้วยรูปที่ชัดเจนขึ้นครับ")
                        return
                    ocr_result = ocr_json["text"]
                    final_transactions = ocr_result

                    temp_id = save_temp_transaction(user_id, final_transactions, attachment_id=attachment_id, source_type="image")
                else:
                    print("Failed to save image")


            # --- ถ้ามีข้อมูลรายการ (ไม่ว่าจะมาจาก Text หรือ Image) ให้ส่ง Flex Reply ---
            if final_transactions:
                try:
                    print(f"DEBUG: final_transactions type: {final_transactions}")
                    
                    # 1. จัดทำ Flex JSON
                    flex_msg = create_dynamic_flex_receipt(final_transactions, temp_id=temp_id)
                    
                    # 2. ส่ง Reply
                    print("DEBUG: Sending reply...")
                    response = send_line_reply_v3(reply_token, alt_text="บันทึกรายการสำเร็จ", flex_json=flex_msg)
                    print(f"DEBUG: Line API Response: {response}")
                    
                except Exception as e:
                    print(f"ERROR in processing Flex Reply: {str(e)}")
            
        elif event_type == 'postback':
            postback_data = event.get("postback", {}).get("data")
            print(f"[{user_id}] Postback: {postback_data}")
            from urllib.parse import parse_qsl
            params = dict(parse_qsl(postback_data))
            print(params)

            action = params.get("action")
            post_temp_id = params.get("temp_id")
            if action == "confirm":
                result = confirm_and_save_transaction(temp_id=post_temp_id)
                print(result)
                if result:
                    
                    count = result.get("count", 0)
                    total = result.get("total", 0.0)
                    text_reply = f"✅ บันทึกสำเร็จ {count} รายการ\n💰 ยอดรวม ฿{total:,.2f}\nเรียบร้อยแล้วครับ"
                else:
                    text_reply = "❌ ไม่พบข้อมูลรายการนี้ หรือรายการอาจหมดอายุแล้วครับ"

                # 3. ตอบกลับเพื่อยืนยันผลการทำงาน
                send_line_reply_v3(reply_token, text=text_reply)
            elif action == "cancel":
                delete_temp_transaction(temp_id=post_temp_id)
                # (Option) ถ้า User กดกยกเลิก อาจจะแค่บอกว่ายกเลิกแล้ว
                send_line_reply_v3(reply_token=reply_token, text="🗑️ ยกเลิกการบันทึกรายการเรียบร้อยครับ")

    return {"status": "ok"}

@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: str, type: str = "monthly", month: int = None, year: int = None):
    # ส่ง type เข้าไปในฟังก์ชันจัดการข้อมูล
    return get_dashboard_data(user_id, type, month, year)

@app.post("/api/budget/setup")
async def setup_budget(data: dict):
    user_id = data.get("user_id")
    amount = data.get("amount")
    
    return setup_user_budget(user_id, amount)


# cron job service
@app.post("/api/cron/remind-to-record")
async def remind_logic(db: Session = Depends(get_session), _ : str = Depends(verify_cron_token)):
    all_users = get_all_users(db)
    count_reminded = 0
    for user in all_users:
        user_id = user.line_user_id
        daily_amount = get_daily_usage(db, user_id)
        
        if daily_amount is None:
            # 4. ถ้ายังไม่จด (None) -> ส่ง Push Notification ทันที
            send_push_notification(
                user_id=user.line_user_id,
                content="📝 วันนี้ยังไม่ได้บันทึกรายการเลยนะ อย่าลืมจด 'จดนิด' เพื่อวินัยทางการเงินที่แม่นยำนะครับ",
                alt_text="เตือนบันทึกรายจ่ายวันนี้"
            )
            count_reminded += 1
    return {
        "status": "success", 
        "total_users": len(all_users), 
        "reminded_count": count_reminded
    }

# --- เส้นที่ 2: สรุปรายวัน (Run ตอน 21:00) ---
@app.post("/api/cron/summary-daily")
async def daily_summary(_ : str = Depends(verify_cron_token), db: Session = Depends(get_session)):


    all_users = get_all_users(db)
    for user in all_users:
        user_id = user.line_user_id
        amount = get_daily_usage(db, user_id) or 0.0
        # คุณสามารถสร้าง Flex JSON สวยๆ ตรงนี้แล้วส่งไป
        msg = f"📊 สรุปยอดใช้จ่ายวันนี้ของคุณคือ ฿{amount:,.2f} ครับ"
        send_push_notification(user_id, msg, alt_text="สรุปยอดรายวัน")
        return {"status": "summary_sent"}

# --- เส้นที่ 3: สรุปรายเดือน (Run ทุกสิ้นเดือน หรือตามสั่ง) ---
@app.post("/api/cron/summary-monthly")
async def monthly_summary(_ : str = Depends(verify_cron_token),db: Session = Depends(get_session)):
    all_users = get_all_users(db)
    for user in all_users:
        user_id = user.line_user_id
        amount = get_monthly_usage(db, user_id)
        msg = f"📅 สรุปยอดใช้จ่ายเดือนนี้ทั้งหมด ฿{amount:,.2f} ครับ"
        send_push_notification(user_id, msg, alt_text="สรุปยอดรายเดือน")
        return {"status": "monthly_summary_sent"}


if __name__ == "__main__":
    from model.models import create_db_and_tables
    create_db_and_tables()
    
    port = int(os.getenv("PORT", 5005)) # ถ้าไม่มีใน .env ให้ใช้ 5005 เป็น default

    
    uvicorn.run("index:app", host="0.0.0.0", port=port, reload=True)