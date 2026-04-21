from helper.utils import get_config_value, create_summary_flex, clear_config_cache
from model.db_manament import (
    get_parent_categories,
    get_temp_transaction_data,
    get_temp_transaction_data,
    create_system_config,
    get_system_config_data,
    update_system_config
)
from helper.webhook_helper import (
    process_webhook_event,
    confirme_data_from_edit
)
from fastapi import FastAPI, BackgroundTasks
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
from helper.utils import (
    get_user_overview,
    send_push_notification,
    get_daily_usage,
    get_monthly_usage,
    get_all_users
)

# database service
from model.db_manament import (
    get_dashboard_data,
    setup_user_budget,
)
from model.models import create_db_and_tables, get_session


load_dotenv()

app = FastAPI()

origins = [
    os.getenv("FRONTEND_URL"),
    os.getenv("ADMIN_URL"),
    "https://jodnid.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Usage
api_key = os.getenv("TYPHOON_API_KEY")
is_test_mode = os.getenv("TEST_MODE")
line_access_token = ""
if is_test_mode:
    line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN_TEST")
else:
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
async def line_webhook(data: LineWebhook, background_tasks: BackgroundTasks):
    is_maintenance_mode = get_config_value(key="is_maintenance_mode",default=False)    
    for event in data.events:
        # 1. ดึง UID และประเภทของ Event
        user_id = event.get("source", {}).get("userId")
        reply_token = event.get("replyToken")
        if is_maintenance_mode:
            send_push_notification(user_id=user_id, content="ระบบกำลังปรับปรุง กรุณาลองใหม่อีกครั้งภายหลัง", alt_text="ระบบกำลังปรับปรุง")
            continue
        background_tasks.add_task(process_webhook_event, event, user_id, reply_token, line_access_token, api_key)
        
    return {"status": "ok"}

@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: str, type: str = "monthly",day: int = None, month: int = None, year: int = None):
    print(f"User ID: {user_id}, Type: {type}, Month: {month}, Year: {year}")
    # ส่ง type เข้าไปในฟังก์ชันจัดการข้อมูล
    return get_dashboard_data(user_id, type, day, month, year)


@app.get("/api/temp-transaction/{temp_id}")
async def get_temp_transaction(temp_id: str):
    data = get_temp_transaction_data(temp_id)
    print(data)
    return data

@app.post("/api/transactions/confirm-bulk")
async def confirme_transaction_bulk_edit(data: dict):
    user_id = data.get("user_id")
    items = data.get("items")
    temp_id = data.get("temp_id")
    confirme_data_from_edit(temp_id, user_id, items)
    return {"success": True, "message": "Confirm bulk transaction"}


@app.get("/api/categories/parent")
async def get_categories_parent():
    print("fetch categories parent")
    return get_parent_categories()



@app.post("/api/budget/setup")
async def setup_budget(data: dict):
    user_id = data.get("user_id")
    amount = data.get("amount")
    category_id = data.get("category_id")
    print(f"Setting up budget for user_id: {user_id} with amount: {amount} and category_id: {category_id}")
    if not user_id or not amount or not category_id:
        return {"success": False, "message": "Missing user_id or amount or category_id"}
    
    
    return setup_user_budget(user_id, category_id=category_id, amount=amount)


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
    processed_count = 0
    
    for user in all_users:
        user_id = user.line_user_id
        # ดึงข้อมูลจากฟังก์ชันสรุปที่คุยกันก่อนหน้า
        data = get_dashboard_data(db, user_id, type="daily") 
        
        if data["total_amount"] > 0:
            flex_content = create_summary_flex(
                title="📊 สรุปรายงานรายวัน",
                total=data["total_amount"],
                items=data["transactions"],
                remaining=data.get("budget_remaining", 0),
                percent=data.get("total_percent", 0)
            )
            
            # ส่งเป็น Flex Message
            send_push_notification(user_id, content=flex_content, alt_text="สรุปยอดรายวัน")
            processed_count += 1
            
    return {"status": "success", "users_notified": processed_count}

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


@app.post("/api/overview/stats")
async def overview_stat(data: dict, db: Session = Depends(get_session)):
    user_id = data.get("user_id")
    if not user_id:
        return {"success": False, "message": "Missing user_id"}
    
    data = get_user_overview(db, user_id)

    return {
        "success": True,
        "data": data
    }

@app.post("/api/administrator/config/create")
async def create_system_configuration(data: dict, db: Session = Depends(get_session)):
    name = data.get("name")
    key = data.get("key")
    value = data.get("value")
    value_type = data.get("value_type")
    description = data.get("description")
    if not name or not key or not value or not value_type:
        return {"success": False, "message": "Missing name or key or value or value_type"}
    
    return create_system_config(db, name, key, value, value_type, description)


@app.get("/api/administrator/all")
def get_all_system_configuration(db: Session = Depends(get_session)):
    return get_system_config_data(db)


@app.patch("/api/administrator/config/update")
def update_system_configuration(data: dict, db: Session = Depends(get_session)):
    key = data.get("key")
    value = data.get("value")
    value_type = data.get("value_type")
    description = data.get("description")
    if not key or not value:
        return {"success": False, "message": "Missing key or value"}
    clear_config_cache()
    return update_system_config(db, key, value, value_type, description)

@app.patch("/api/administrator/config/toggle")
def toggle_system_configuration(data: dict, db: Session = Depends(get_session)):
    key = data.get("key")
    value = data.get("value")
    if not key or not value:
        return {"success": False, "message": "Missing key or value"}
    clear_config_cache()
    return update_system_config(db, key, value)

if __name__ == "__main__":
    create_db_and_tables()
    port = int(os.getenv("PORT", 5005)) # ถ้าไม่มีใน .env ให้ใช้ 5005 เป็น default
    uvicorn.run("index:app", host="0.0.0.0", port=port, reload=True)