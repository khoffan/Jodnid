from fastapi import Depends, APIRouter, Security, HTTPException
from fastapi.security import APIKeyHeader
from model.models import get_session
from sqlmodel import Session
from helper.logger import JodNidLogger
from model.db_manament import (
    get_dashboard_data,
)

# function
from helper.utils import (
    send_push_notification,
    get_daily_usage,
    get_monthly_usage,
    get_all_users,
    create_summary_flex, 
    get_all_users, 
    get_line_profile
)
from core.config_settings import settings
header_scheme = APIKeyHeader(name="X-Cron-Token", auto_error=False)

async def verify_cron_token(token: str = Security(header_scheme)):
    expected_token = settings.CRON_SECRET_TOKEN
    if not token or token != expected_token:
        raise HTTPException(
            status_code=403, 
            detail="Could not validate credentials"
        )
    return token

class CronAPis:
    def __init__(self, logger: JodNidLogger, line_access_token: str,):
        self.router = APIRouter(
            prefix="/api/cron",
            tags=["Cron"],
            dependencies=[Depends(verify_cron_token)]
        )
        self.line_access_token = line_access_token
        self.logger = logger
        
    def setup_router(self):
        router = self.router
        logger = self.logger
        # cron job service
        @router.post("/remind-to-record")
        async def remind_logic(db: Session = Depends(get_session)):
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
                    logger.info(module="cron", message=f"Reminder logic executed: {count_reminded}/{len(all_users)} users reminded", user_id=user_id)    
                else:
                    logger.info(module="cron", message=f"User {user_id} has already recorded their expenses today.")    
            return {
                "status": "success", 
                "total_users": len(all_users), 
                "reminded_count": count_reminded
            }

        # --- เส้นที่ 2: สรุปรายวัน (Run ตอน 21:00) ---
        @router.post("/summary-daily")
        async def daily_summary(db: Session = Depends(get_session)):
            all_users = get_all_users(db)
            processed_count = 0
            
            logger.info(module="cron", message=f"Daily summary cron job started for {len(all_users)} users")    
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
                    logger.info(module="cron", message=f"Daily summary cron job completed: {processed_count}/{len(all_users)} users notified", user_id=user_id)    
                else:
                    logger.info(module="cron", message=f"User {user_id} has no expenses recorded today.", user_id=user_id)    
            return {"status": "success", "users_notified": processed_count}

        # --- เส้นที่ 3: สรุปรายเดือน (Run ทุกสิ้นเดือน หรือตามสั่ง) ---
        @router.post("/summary-monthly")
        async def monthly_summary(db: Session = Depends(get_session)):
            all_users = get_all_users(db)
            logger.info(module="cron", message=f"Monthly summary cron job started for {len(all_users)} users", user_id=user_id)    
            for user in all_users:
                user_id = user.line_user_id
                amount = get_monthly_usage(db, user_id)
                msg = f"📅 สรุปยอดใช้จ่ายเดือนนี้ทั้งหมด ฿{amount:,.2f} ครับ"
                send_push_notification(user_id, msg, alt_text="สรุปยอดรายเดือน")
                logger.info(module="cron", message=f"Monthly summary cron job completed: {msg} users notified", user_id=user.line_user_id)    
            return {"status": "monthly_summary_sent"}