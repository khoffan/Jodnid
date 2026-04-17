from model.db_manament import sync_user_budgets
import requests
import os
import io
from PIL import Image, ImageEnhance
from datetime import datetime
from sqlmodel import Session, select, func, extract
from model.models import Categories, Transactions, UserBudget, Users
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
is_test_mode = os.getenv("TEST_MODE")
line_access_token = ""
if is_test_mode:
    line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN_TEST")
else:
    line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
configuration = Configuration(access_token=line_access_token)

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
    line_liff_id = os.getenv("LINE_LIFF_ID")
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
                # 2. ปุ่มแก้ไข (เปิด LIFF)
                {
                    "type": "button",
                    "style": "secondary",
                    "color": "#E5E7EB", # สีเทาอ่อนเพื่อให้ปุ่ม ยืนยัน เด่นกว่า
                    "margin": "sm",
                    "action": {
                        "type": "uri",
                        "label": "✏️ แก้ไขรายการ",
                        "uri": f"https://liff.line.me/{line_liff_id}?path=/edit-temp/{temp_id}"
                    }
                },
                {
                    "type": "button",
                    "style": "link",
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

def get_instruction_flex():
    """สร้าง Flex Message แนะนำวิธีการใช้งานแอป จดนิด"""

    line_liff_id = os.getenv("LINE_LIFF_ID")
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "💡 วิธีใช้ จดนิด (JodNid)",
                    "weight": "bold",
                    "color": "#1DB446",
                    "size": "sm"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "คุณสามารถบันทึกรายจ่ายได้ง่ายๆ ด้วย 2 วิธีหลักครับ:",
                    "wrap": True,
                    "size": "xs",
                    "color": "#555555"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        # วิธีที่ 1: พิมพ์ข้อความ
                        {
                            "type": "text",
                            "text": "1️⃣ พิมพ์รายการและยอดเงิน",
                            "weight": "bold",
                            "size": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#F0F9F4",
                            "paddingAll": "10px",
                            "cornerRadius": "md",
                            "contents": [
                                {"type": "text", "text": "✅ ค่ากะเพรา 60", "size": "xs", "color": "#1DB446"},
                                {"type": "text", "text": "✅ เติมน้ำมัน 1000", "size": "xs", "color": "#1DB446", "margin": "xs"},
                                {"type": "text", "text": "✅ เงินเดือนออก 30000", "size": "xs", "color": "#1DB446", "margin": "xs"}
                            ]
                        },
                        # วิธีที่ 2: ส่งรูป
                        {
                            "type": "text",
                            "text": "2️⃣ ส่งรูปสลิปโอนเงิน",
                            "weight": "bold",
                            "size": "sm",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "ส่งรูปสลิปจากแอปธนาคารได้ทันที ระบบจะสกัดข้อมูลให้โดยอัตโนมัติครับ",
                            "wrap": True,
                            "size": "xs",
                            "color": "#888888"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "⚠️ ข้อควรระวัง",
                            "size": "xs",
                            "weight": "bold",
                            "color": "#FF3B30"
                        },
                        {
                            "type": "text",
                            "text": "• บอทยังไม่รองรับการคุยเล่นทั่วไป\n• ต้องมี 'ชื่อรายการ' และ 'ตัวเลข' เสมอ",
                            "wrap": True,
                            "size": "xxs",
                            "color": "#999999",
                            "margin": "xs"
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "secondary",
                    "color": "#F0F0F0",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "📊 ดูแดชบอร์ด",
                        "uri": f"https://liff.line.me/{line_liff_id}"
                    }
                }
            ]
        }
    }
    
def create_summary_flex(title, total, items, remaining, percent):
    # กำหนดสีของ Progress Bar ตามสถานะ
    bar_color = "#EF4444" if percent > 90 else "#22C55E"
    
    # สร้างส่วนรายการ (Transaction Rows)
    item_nodes = []
    for item in items[:3]: # แสดง 3 รายการล่าสุดใน Flex เพื่อความกระชับ
        item_nodes.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"{item['icon']} {item['item']}", "size": "sm", "color": "#555555", "flex": 4},
                {"type": "text", "text": f"฿{item['amount']:,.0f}", "size": "sm", "color": "#111111", "align": "end", "weight": "bold", "flex": 2}
            ]
        })

    return {
        "type": "bubble",
        "size": "giga",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "color": "#1DB446", "size": "sm"},
                {"type": "text", "text": f"฿{total:,.2f}", "weight": "bold", "size": "xxl", "margin": "md"},
                {"type": "text", "text": "ยอดใช้จ่ายรวมวันนี้", "size": "xs", "color": "#aaaaaa"},
                {"type": "separator", "margin": "lg"},
                
                # รายการล่าสุด
                {"type": "box", "layout": "vertical", "margin": "lg", "spacing": "sm", "contents": item_nodes},
                
                {"type": "separator", "margin": "lg"},
                
                # Progress Bar ของงบประมาณเดือน
                {"type": "box", "layout": "vertical", "margin": "lg", "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "งบประมาณเดือนนี้", "size": "xs", "color": "#aaaaaa"},
                        {"type": "text", "text": f"{percent:.1f}%", "size": "xs", "color": "#aaaaaa", "align": "end"}
                    ]},
                    {"type": "box", "layout": "vertical", "margin": "sm", "backgroundColor": "#F3F4F6", "height": "6px", "cornerRadius": "3px", "contents": [
                        {"type": "box", "layout": "vertical", "width": f"{min(percent, 100)}%", "backgroundColor": bar_color, "height": "6px", "cornerRadius": "3px", "contents": []}
                    ]}
                ]}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "ดูรายละเอียดในแอป",
                        "uri": "https://liff.line.me/YOUR_LIFF_ID/dashboard/daily"
                    },
                    "style": "primary",
                    "color": "#111827",
                    "height": "sm"
                }
            ]
        }
    }


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

# ฟังชั้นนี้ใช้ในการทำงานทางด้าน stats ต่างๆ เช่น ดึงข้อมูลยอดรวมรายวัน รายเดือน หรือคำนวณค่าเฉลี่ย เป็นต้น
def get_user_overview(session: Session, user_id: str):
    today = datetime.now()
    
    sync_user_budgets(session, user_id, today.month, today.year)
    
    # 1. ยอดรวมทั้งเดือน และ วันนี้ (เหมือนเดิม)
    monthly_total = get_monthly_usage(session, user_id)
    if monthly_total is None:
        monthly_total = 0.0

    daily_total = get_daily_usage(session, user_id)
    if daily_total is None:
        daily_total = 0.0

    # 2. ดึงข้อมูล Budget รายหมวดหมู่ (หัวใจสำคัญของระบบใหม่)
    # เราจะ Join UserBudget กับ Categories เพื่อเอาชื่อและ Icon ของ Parent Category มาแสดง
    budget_statement = select(
        Categories.name,
        Categories.icon,
        UserBudget.amount,       # งบที่ตั้งไว้ (Limit)
        UserBudget.current_spent  # ยอดที่ใช้ไป (Actual Spent)
    ).join(
        Categories, UserBudget.category_id == Categories.id
    ).where(
        UserBudget.user_id == user_id,
        UserBudget.month == today.month,
        UserBudget.year == today.year
    )
    
    budget_results = session.exec(budget_statement).all()
    print(budget_results)
    # จัดรูปแบบข้อมูล Categories สำหรับ Frontend
    # จะมีข้อมูลทั้ง limit, spent และ percentage เพื่อให้ Frontend วาด Progress Bar ได้ทันที
    categories_overview = []
    total_budget_limit = 0.0
    
    for name, icon, limit, spent in budget_results:
        total_budget_limit += float(limit)
        remaining = float(limit) - float(spent)
        percent = (float(spent) / float(limit) * 100) if limit > 0 else 0
        
        categories_overview.append({
            "name": name,
            "icon": icon,
            "limit": float(limit),
            "spent": float(spent),
            "remaining": round(remaining, 2),
            "percent": round(percent, 1)
        })

    # 3. คำนวณค่าเฉลี่ยรายวัน (Daily Average)
    days_passed = today.day
    daily_average = monthly_total / days_passed if days_passed > 0 else 0.0

    return {
        "monthlyTotal": float(monthly_total),
        "dailyTotal": float(daily_total),
        "dailyAverage": round(float(daily_average), 2),
        "budgetLimit": total_budget_limit, # ยอดรวมงบทุกหมวดหมู่
        "categories": categories_overview   # ข้อมูลรายหมวดหมู่แบบละเอียด
    }

def get_all_users(session: Session):
    """ดึงข้อมูลผู้ใช้ทั้งหมด (สำหรับการส่ง Notification)"""
    statement = select(Users)
    return session.exec(statement).all()

def get_line_profile(user_id: str, line_token: str):
    # GET https://api.line.me/v2/bot/profile/{userId}
    api = os.getenv("LINE_API")
    url = f"{api}/bot/profile/{user_id}"

    headers = {
        "Authorization": f"Bearer {line_token}"
    }

    result = requests.get(url, headers=headers)
    if result.status_code == 200:
        data = result.json()  # คืนค่าเป็น dict ที่มี displayName, pictureUrl, statusMessage
        print(data)
        return data
    else:
        print(f"Error fetching profile: {result.status_code} - {result.text}")
        return None
    
def pre_process_image_file(image_data):
    try:
        print('DEBUG: start pre processing image')
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
        else:
            # กรณีส่งเป็น File Object มา
            img = Image.open(image_data)

        # --- 1. Resize ---
        max_width = 1500
        if img.width > max_width:
            w_percent = (max_width / float(img.width))
            h_size = int((float(img.height) * float(w_percent)))
            img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)

        # --- 2. Convert to Grayscale (ลดสีเหลือขาวดำ/เทา) ---
        img = img.convert('L')

        # --- 3. Enhance Contrast (ช่วยให้ตัวหนังสือในใบกำกับภาษีชัดขึ้น) ---
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0) 

        # แปลงกลับเป็น Bytes เพื่อส่งไป API ต่อ
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        print("DEBUG: processed image")
        return img_byte_arr.getvalue() # คืนค่ากลับเป็น bytes
    except Exception as e:
        print(f"Image Preprocessing Error: {e}")
        return image_data


