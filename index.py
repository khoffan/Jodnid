from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
from core.config_settings import settings
from helper.utils import get_line_profile
from helper.logger import JodNidLogger
from helper.utils import get_config_value
from helper.webhook_helper import process_webhook_event



# function
from helper.utils import (
    send_push_notification,
    get_all_users
)
from model.models import create_db_and_tables, get_session
from routes.api_liff_v1 import LiffApi
from routes.api_cron_v1 import CronAPis
from routes.api_administrator_v1 import AdministratorAPIs


load_dotenv()

app = FastAPI()

origins = [
    settings.FRONTEND_URL,
    settings.ADMIN_URL,
    "https://jodnid.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserMessage(BaseModel):
    message: str

class LineWebhook(BaseModel):
    destination: str
    events: List[Dict[str, Any]]


db_session = next(get_session())
logger = JodNidLogger(db=db_session)
# Usage
api_key = settings.TYPHOON_API_KEY
is_test_mode = settings.TEST_MODE
line_access_token = ""
if is_test_mode:
    line_access_token = settings.LINE_CHANNEL_ACCESS_TOKEN_TEST
else:
    line_access_token = settings.LINE_CHANNEL_ACCESS_TOKEN


liff_api = LiffApi(logger=logger, line_access_token=line_access_token)
cron_apis = CronAPis(logger=logger, line_access_token=line_access_token)
administrator_api = AdministratorAPIs(logger=logger, line_access_token=line_access_token)

# start service
liff_api.setup_router()
cron_apis.setup_router()
administrator_api.setup_router()

app.include_router(liff_api.router)
app.include_router(cron_apis.router)
app.include_router(administrator_api.router)

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
        logger.info(module="webhook", message=f"Received event from user_id: {user_id}", user_id=user_id)
        if is_maintenance_mode:
            logger.info(module="webhook", message=f"Maintenance mode is enabled", user_id=user_id)
            send_push_notification(user_id=user_id, content="ระบบกำลังปรับปรุง กรุณาลองใหม่อีกครั้งภายหลัง", alt_text="ระบบกำลังปรับปรุง")
            continue
        background_tasks.add_task(process_webhook_event, event, user_id, reply_token, line_access_token, api_key, logger)
        
    return {"status": "ok"}

if __name__ == "__main__":
    create_db_and_tables()
    users = get_all_users(db_session)
    user_id = None
    for user in users:
        profile = get_line_profile(user_id=user.line_user_id, line_token=line_access_token)
        user_id=profile.get("userId")
    port = int(os.getenv("PORT", 5005)) # ถ้าไม่มีใน .env ให้ใช้ 5005 เป็น default
    logger.info(module="app", message=f"Starting server on port {port}", user_id=user_id)
    uvicorn.run("index:app", host="0.0.0.0", port=port, reload=True)