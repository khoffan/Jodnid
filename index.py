import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
import os

# function
from ai.ocr import extract_text_from_image
from ai.text_nlp import extract_transactions
from helper.helper import get_content_line, create_dynamic_flex_receipt, send_line_reply, send_loading_indicator, save_line_image

# database service
from model.db_manament import get_or_create_user, save_temp_transaction, confirm_and_save_transaction, create_attachment_record, get_dashboard_data


load_dotenv()

app = fastapi.FastAPI()

origin = [
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

            # กรณีที่ 1: เป็นข้อความ (Text)
            
            final_transactions = None
            if msg_type == "text":
                user_text = message.get("text")
                print(f"[{user_id}] Text: {user_text}")
                send_loading_indicator(user_id=user_id, line_token=line_access_token)
                # ส่งไปให้ Typhoon วิเคราะห์รายการ
                final_transactions = extract_transactions(api_key, user_text)

                temp_id = save_temp_transaction(user_id, final_transactions)
                
                # TODO: บันทึกลง Database โดยผูกกับ user_id
                # TODO: Reply กลับหา User ผ่าน LINE Messaging API
                # return {"status": "success", "type": "text", "result": final_transection}

            # กรณีที่ 2: เป็นรูปภาพ (Image)
            elif msg_type == "image":
                message_id = message.get("id")
                print(f"[{user_id}] Image ID: {message_id}")
                send_loading_indicator(user_id=user_id, line_token=line_access_token)
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
                    ocr_text = ocr_json["text"]
                    final_transactions = [ocr_text]

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
                    response = send_line_reply(reply_token, flex_content={
                        "type": "flex",
                        "altText": "บันทึกรายการสำเร็จ",
                        "contents": flex_msg # รับค่ามาจากฟังก์ชันแรก
                    }, line_token=line_access_token)
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
            category = params.get("cat")
            if action == "confirm":
                success = confirm_and_save_transaction(temp_id=post_temp_id, category_name=category)
                print(success)
                if success:
                    # แปลง category code เป็นคำอ่านภาษาไทยให้ User เข้าใจง่าย
                    cat_map = {
                        "food": "🍔 อาหาร",
                        "travel": "🚗 เดินทาง",
                        "shopping": "🛍️ ช้อปปิ้ง",
                        "other": "✨ อื่นๆ"
                    }
                    display_cat = cat_map.get(category, "ทั่วไป")
                    text_reply = f"✅ บันทึกรายการลงหมวด {display_cat} เรียบร้อยแล้วครับ"
                else:
                    text_reply = "❌ ไม่พบข้อมูลรายการนี้ หรือรายการอาจหมดอายุแล้วครับ"

                # 3. ตอบกลับเพื่อยืนยันผลการทำงาน
                send_line_reply(reply_token, flex_content={"type": "text", "text": text_reply}, line_token=line_access_token)

                

    return {"status": "ok"}

@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: str, month: int = None, year: int = None):
    return get_dashboard_data(user_id, month, year)


if __name__ == "__main__":
    from model.models import create_db_and_tables
    create_db_and_tables()
    
    port = int(os.getenv("PORT", 5005)) # ถ้าไม่มีใน .env ให้ใช้ 5005 เป็น default

    
    uvicorn.run("index:app", host="0.0.0.0", port=port, reload=True)