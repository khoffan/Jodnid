import requests
import os
from datetime import datetime

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

# def send_flex_receipt(reply_token: str, transactions: list, line_token: str):    
#     # 1. คำนวณยอดรวมและชื่อร้าน (ตัวอย่าง)
#     total_amount = sum(t['amount'] for t in transactions)
#     store_name = " & ".join(list(set([t.get('store', 'ร้านค้า') for t in transactions])))

#     # 2. วนลูปสร้างรายการสินค้า (Dynamic Rows)
#     item_rows = []
#     for t in transactions:
#         item_rows.append({
#             "type": "box",
#             "layout": "horizontal",
#             "contents": [
#                 {"type": "text", "text": t['item'], "size": "sm", "color": "#555555", "flex": 0},
#                 {"type": "text", "text": f"฿ {t['amount']:.2f}", "size": "sm", "color": "#111111", "align": "end"}
#             ]
#         })

#     # 3. ประกอบเข้ากับโครงสร้าง Flex JSON
#     flex_content = {
#         "type": "bubble",
#         "header": {
#             "type": "box",
#             "layout": "vertical",
#             "contents": [
#                 {"type": "text", "text": "บันทึกรายการสำเร็จ", "color": "#1DB446", "weight": "bold", "size": "sm"},
#                 {"type": "text", "text": f"฿ {total_amount:.2f}", "weight": "bold", "size": "xxl", "margin": "md"},
#                 {"type": "text", "text": store_name, "size": "xs", "color": "#aaaaaa", "wrap": True}
#             ]
#         },
#         "body": {
#             "type": "box",
#             "layout": "vertical",
#             "contents": [
#                 {"type": "separator", "margin": "md"},
#                 {
#                     "type": "box",
#                     "layout": "vertical",
#                     "margin": "lg",
#                     "spacing": "sm",
#                     "contents": item_rows # <--- เอาแถวที่วนลูปไว้มาใส่ตรงนี้
#                 }
#                 # ... ส่วนอื่นๆ ของ JSON (Footer, Separator) ตามที่ให้ไปด้านบน ...
#             ]
#         }
#     }

#     # 4. ยิง API ส่งกลับหา LINE
#     payload = {
#         "replyToken": reply_token,
#         "messages": [
#             {
#                 "type": "flex",
#                 "altText": f"บันทึกยอดเงิน ฿{total_amount:.2f} เรียบร้อย",
#                 "contents": flex_content
#             }
#         ]
#     }
    
#     return requests.post(
#         "https://api.line.me/v2/bot/message/reply",
#         headers={"Authorization": f"Bearer {line_token}"},
#         json=payload
#     )


def create_dynamic_flex_receipt(transactions: list, temp_id: str):
    # ป้องกัน total พังถ้าข้อมูลไม่ใช่ตัวเลข
    try:
        total = sum(float(t.get('amount', 0)) for t in transactions)
    except:
        total = 0.0
    
    item_rows = []
    for t in transactions:
        # ดึงค่าและจัดการให้เป็น String เสมอ
        name = str(t.get('item') or t.get('receiver') or 'ไม่ระบุ')
        amount = float(t.get('amount', 0))

        item_rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text", 
                    "text": name, 
                    "size": "sm", 
                    "color": "#555555", 
                    "flex": 4  # ใช้ flex 4 แทน 0 เพื่อให้มีพื้นที่ตัวหนังสือ
                },
                {
                    "type": "text", 
                    "text": f"฿{amount:,.2f}", 
                    "size": "sm", 
                    "color": "#111111", 
                    "align": "end",
                    "flex": 2  # ให้ราคากินพื้นที่ 2 ส่วน
                }
            ]
        })

    flex_json = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "สกัดข้อมูลสำเร็จ", "color": "#1DB446", "weight": "bold", "size": "sm"},
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
            "spacing": "sm", # เพิ่มระยะห่างระหว่างแถวปุ่ม
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button", "style": "primary", "color": "#FF5733", "height": "sm",
                            "action": {"type": "postback", "label": "🍔 อาหาร", "data": f"action=confirm&temp_id={temp_id}&cat=food"}
                        },
                        {
                            "type": "button", "style": "primary", "color": "#3357FF", "height": "sm",
                            "action": {"type": "postback", "label": "🚗 เดินทาง", "data": f"action=confirm&temp_id={temp_id}&cat=travel"}
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button", "style": "primary", "color": "#FF33A1", "height": "sm",
                            "action": {"type": "postback", "label": "🛍️ ช้อปปิ้ง", "data": f"action=confirm&temp_id={temp_id}&cat=shopping"}
                        },
                        {
                            "type": "button", "style": "primary", "color": "#1DB446", "height": "sm",
                            "action": {"type": "postback", "label": "✨ อื่นๆ", "data": f"action=confirm&temp_id={temp_id}&cat=other"}
                        }
                    ]
                }
            ]
        }
    }
    return flex_json

# 2. ฟังก์ชันส่ง (เน้นเรื่องการสื่อสาร)
def send_line_reply(reply_token: str, flex_content: dict, line_token: str):
    url = "https://api.line.me/v2/bot/message/reply"
    payload = {
        "replyToken": reply_token,
        "messages": [
            flex_content
        ]
    }
    headers = {"Authorization": f"Bearer {line_token}", "Content-Type": "application/json"}
    return requests.post(url, headers=headers, json=payload)

def send_loading_indicator(user_id: str, line_token: str):
    url = "https://api.line.me/v2/bot/chat/loading/start"
    payload = {
        "chatId": user_id,
        "loadingSeconds": 5 # โชว์ไว้ 5 วินาที (สูงสุด 60)
    }
    headers = {"Authorization": f"Bearer {line_token}", "Content-Type": "application/json"}
    requests.post(url, headers=headers, json=payload)