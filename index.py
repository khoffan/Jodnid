import os
from typing import Any, Dict, List

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config_settings import settings
from helper.logger import JodNidLogger

# function
from helper.utils import LineUtils, Utilities
from helper.webhook_helper import process_webhook_event
from model.db_manament import DBManagerBudget, DBManagerUsers
from model.models import create_db_and_tables, get_session
from routes.api_administrator_v1 import AdministratorAPIs
from routes.api_cron_v1 import CronAPis
from routes.api_liff_v1 import LiffApi

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
    is_maintenance_mode = Utilities.get_config_value(key="is_maintenance_mode", default=False)
    for event in data.events:
        # 1. ดึง UID และประเภทของ Event
        user_id = event.get("source", {}).get("userId")
        reply_token = event.get("replyToken")
        logger.info(
            module="webhook", message=f"Received event from user_id: {user_id}", user_id=user_id
        )
        if is_maintenance_mode:
            logger.info(module="webhook", message="Maintenance mode is enabled", user_id=user_id)
            LineUtils.send_push_notification(
                user_id=user_id,
                content="ระบบกำลังปรับปรุง กรุณาลองใหม่อีกครั้งภายหลัง",
                alt_text="ระบบกำลังปรับปรุง",
            )
            continue

        onboarding_status = DBManagerUsers.get_user_onboarding_status(db_session, user_id)
        if not onboarding_status.get("success") or not onboarding_status.get("is_onboarded"):
            logger.info(
                module="webhook",
                message="User is not onboarded yet, send onboarding prompt",
                user_id=user_id,
            )
            LineUtils.send_line_reply_v3(
                reply_token=reply_token,
                text="ยังไม่ได้ตั้งค่าเริ่มต้นการใช้งานครับ กรุณาเปิด LIFF เพื่อทำ onboarding ก่อนใช้งาน",
            )
            continue

        # ถ้าเดือนนี้ยังไม่ได้ตั้งงบ ให้แจ้งกลับทันทีและยังไม่ประมวลผลธุรกรรมต่อ
        can_setup_budget = DBManagerBudget.can_setup_budget_this_month(db_session, user_id)
        if can_setup_budget:
            logger.info(
                module="webhook",
                message="User has no monthly budget yet, send budget setup prompt",
                user_id=user_id,
            )

            prompt_text = "เดือนนี้คุณยังไม่ได้ตั้งงบประมาณครับ กรุณาเข้า LIFF เพื่อตั้งงบก่อนเริ่มใช้งาน"
            if reply_token:
                LineUtils.send_line_reply_v3(reply_token=reply_token, text=prompt_text)
            else:
                LineUtils.send_push_notification(
                    user_id=user_id,
                    content=prompt_text,
                    alt_text="แจ้งเตือนตั้งงบประมาณ",
                )
            continue

        background_tasks.add_task(
            process_webhook_event,
            db_session,
            event,
            user_id,
            reply_token,
            line_access_token,
            api_key,
            logger,
        )

    return {"status": "ok"}


if __name__ == "__main__":
    create_db_and_tables()
    port = int(os.getenv("PORT", 5005))  # ถ้าไม่มีใน .env ให้ใช้ 5005 เป็น default
    logger.info(module="app", message=f"Starting server on port {port}")
    uvicorn.run("index:app", host="0.0.0.0", port=port, reload=True)
