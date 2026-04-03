import requests
import os
from datetime import datetime
from sqlmodel import Session, select, func, extract
from model.models import Transactions, Users
from dotenv import load_dotenv
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    FlexMessage,
    FlexContainer,
    ShowLoadingAnimationRequest,
    PushMessageRequest,
    TextMessage
)

load_dotenv()


configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

# file system
def save_line_image(user_id: str, message_id: str, image_bytes: bytes):
    """
    จัดการสร้าง Folder และบันทึกไฟล์รูปภาพ
    โครงสร้าง: uploads/{user_id}/{YYYY-MM-DD}/{message_id}.jpg
    """
    try:
        # 1. เตรียมข้อมูล Path
        base_dir = "uploads"
        current_date = datetime.now().strftime("%Y-%m-%d")
        target_dir = os.path.join(base_dir, user_id, current_date)
        
        # 2. สร้าง Folder ถ้ายังไม่มี (makedirs จะสร้าง folder ย่อยให้ครบทุกระดับ)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        # 3. กำหนดชื่อไฟล์และ Path เต็ม
        # แนะนำให้ใช้ .jpg เป็นค่าเริ่มต้นสำหรับรูปจาก LINE
        file_name = f"{message_id}.jpg"
        file_path = os.path.join(target_dir, file_name)
        
        # 4. บันทึกไฟล์
        with open(file_path, "wb") as f:
            f.write(image_bytes)
            
        print(f"Successfully saved image: {file_path}")
        return file_path  # คืนค่า path เพื่อเอาไปเก็บใน DB
        
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None


def send_push_notification(user_id: str, content: any, alt_text: str = "แจ้งเตือนจากจดนิด"):
    """
    ฟังก์ชันกลางสำหรับส่ง Push Message
    :param user_id: ID ของผู้ใช้ LINE
    :param content: ถ้าเป็น str จะส่งเป็น Text, ถ้าเป็น dict จะส่งเป็น Flex
    :param alt_text: ข้อความที่จะโชว์บน Notification ของมือถือ
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        try:
            # ตรวจสอบว่าเป็นข้อความธรรมดาหรือ Flex
            if isinstance(content, str):
                message = TextMessage(text=content)
            elif isinstance(content, dict):
                message = FlexMessage(
                    altText=alt_text,
                    contents=FlexContainer.from_dict(content)
                )
            else:
                print("Error: Unsupported content type")
                return False

            # ส่ง Push Message
            line_bot_api.push_message(
                PushMessageRequest(to=user_id, messages=[message])
            )
            return True
            
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
            return False

def get_content_line(msg_id: str, line_token:str):
    line_api = os.getenv("LINE_DATA_API")
    url = f"{line_api}/bot/message/{msg_id}/content"

    headers = {
       "Authorization": f"Bearer {line_token}"     
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content  # คืนค่าเป็น binary data (bytes)
    else:
        print(f"Error fetching image: {response.connection}")
        return None


def create_dynamic_flex_receipt(transactions: list, temp_id: str):
    # ป้องกัน total พังถ้าข้อมูลไม่ใช่ตัวเลข
    try:
        total = sum(float(t.get('amount', 0)) for t in transactions)
    except:
        total = 0.0
    
    cat_map = {
        "food": "🍔 อาหาร",
        "อาหาร": "🍔 อาหาร",
        "travel": "🚗 เดินทาง",
        "เดินทาง": "🚗 เดินทาง",
        "shopping": "🛍️ ช้อปปิ้ง",
        "ช้อปปิ้ง": "🛍️ ช้อปปิ้ง",
        "เครื่องดื่ม": "☕ เครื่องดื่ม", # เพิ่มกรณีที่ Typhoon ส่ง 'เครื่องดื่ม' มา
        "other": "✨ อื่นๆ",
        "อื่นๆ": "✨ อื่นๆ"
    }

    item_rows = []
    for t in transactions:
        name = str(t.get('item') or t.get('receiver') or 'ไม่ระบุ')
        amount = float(t.get('amount', 0))
        # ดึงหมวดหมู่ที่ AI วิเคราะห์มาให้ (ถ้าไม่มีให้เป็น other)
        cat_code = t.get('category', 'other')
        cat_display = cat_map.get(cat_code, f"✨ {cat_code}")

        # แถวรายการสินค้า
        item_rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": name, "size": "sm", "color": "#555555", "flex": 4},
                {"type": "text", "text": f"฿{amount:,.2f}", "size": "sm", "color": "#111111", "align": "end", "flex": 2}
            ]
        })
        # แถวแสดงหมวดหมู่ (ตัวเล็กๆ ใต้รายการ)
        item_rows.append({
            "type": "text",
            "text": f"หมวดหมู่: {cat_display}",
            "size": "xs",
            "color": "#999999",
            "margin": "none"
        })

    flex_json = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "ตรวจสอบรายการ", "color": "#1DB446", "weight": "bold", "size": "sm"},
                {"type": "text", "text": f"฿ {total:,.2f}", "weight": "bold", "size": "xxl", "margin": "md"}
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "separator", "margin": "md"},
                {
                    "type": "box", 
                    "layout": "vertical", 
                    "margin": "lg", 
                    "spacing": "sm", 
                    "contents": item_rows
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#1DB446", # สีเขียวเพื่อการยืนยัน
                    "action": {
                        "type": "postback",
                        "label": "✅ ยืนยันบันทึกรายการ",
                        "data": f"action=confirm&temp_id={temp_id}" # ไม่ต้องส่ง cat แล้วเพราะฝังใน temp_id/db ไปแล้ว
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "color": "#FF3B30",
                    "height": "sm",
                    "margin": "sm",
                    "action": {
                        "type": "postback",
                        "label": "❌ ยกเลิก",
                        "data": f"action=cancel&temp_id={temp_id}"
                    }
                }
            ]
        }
    }
    return flex_json

# 2. ฟังก์ชันส่ง (เน้นเรื่องการสื่อสาร)
def send_line_reply_v3(reply_token: str, alt_text: str = None ,flex_json: dict = None, text: str = None, ):
    """ส่ง Reply โดยใช้ SDK v3"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # SDK จะช่วย Validate JSON ให้ผ่าน FlexContainer
        message = None
        if flex_json:
            # ใช้ FlexContainer.from_dict เพื่อ Validate JSON ของคุณ
            message = FlexMessage(
                altText=alt_text,
                contents=FlexContainer.from_dict(flex_json)
            )
        elif text:
            message = TextMessage(text=text)
            
        if message:
            return line_bot_api.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[message]
                )
            )

def send_loading_indicator_v3(user_id: str, seconds: int = 5):
    """โชว์ Loading Animation (SDK v3)"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.show_loading_animation(
            ShowLoadingAnimationRequest(chatId=user_id, loadingSeconds=seconds)
        )

def get_daily_usage(session: Session, user_id: str):
    """เช็คว่าวันนี้มีการจดหรือยัง และดึงยอดรวม"""
    today = datetime.now()
    statement = select(func.sum(Transactions.amount)).where(
        Transactions.user_id == user_id,
        extract('day', Transactions.transaction_date) == today.day,
        extract('month', Transactions.transaction_date) == today.month,
        extract('year', Transactions.transaction_date) == today.year
    )
    result = session.exec(statement).first()
    return result # ถ้าเป็น None แปลว่ายังไม่ได้จด, ถ้ามีค่าคือยอดรวมวันนี้

def get_monthly_usage(session: Session, user_id: str):
    """ดึงยอดรวมรายเดือน"""
    today = datetime.now()
    statement = select(func.sum(Transactions.amount)).where(
        Transactions.user_id == user_id,
        extract('month', Transactions.transaction_date) == today.month,
        extract('year', Transactions.transaction_date) == today.year
    )
    return session.exec(statement).first() or 0.0

def get_all_users(session: Session):
    """ดึงข้อมูลผู้ใช้ทั้งหมด (สำหรับการส่ง Notification)"""
    statement = select(Users)
    return session.exec(statement).all()