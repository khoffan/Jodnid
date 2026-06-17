from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlmodel import Session

from core.config_settings import settings
from helper.logger import JodNidLogger

# function
from helper.utils import LineUtils, Utilities
from model.db_manament import DBManagerDashboard
from model.models import get_session

header_scheme = APIKeyHeader(name="X-Cron-Token", auto_error=False)


async def verify_cron_token(token: str = Security(header_scheme)):
    expected_token = settings.CRON_SECRET_TOKEN
    if not token or token != expected_token:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing cron token")
    return token


class CronAPis:
    def __init__(
        self,
        logger: JodNidLogger,
        line_access_token: str,
    ):
        self.router = APIRouter(
            prefix="/api/cron", tags=["Cron"], dependencies=[Depends(verify_cron_token)]
        )
        self.line_access_token = line_access_token
        self.logger = logger

    def setup_router(self):
        router = self.router
        logger = self.logger

        # cron job service
        @router.post("/remind-to-record")
        async def remind_logic(db: Session = Depends(get_session)):
            all_users = Utilities.get_all_users(db)
            count_reminded = 0
            for user in all_users:
                user_id = user.line_user_id
                daily_amount = Utilities.get_daily_usage(db, user_id)

                if daily_amount is None:
                    # 4. ถ้ายังไม่จด (None) -> ส่ง Push Notification ทันที
                    LineUtils.send_push_notification(
                        user_id=user.line_user_id,
                        content="📝 วันนี้ยังไม่ได้บันทึกรายการเลยนะ อย่าลืมจด 'จดนิด' เพื่อวินัยทางการเงินที่แม่นยำนะครับ",
                        alt_text="เตือนบันทึกรายจ่ายวันนี้",
                    )
                    count_reminded += 1
                    logger.info(
                        module="cron",
                        message=f"Reminder logic executed: {count_reminded}/{len(all_users)} users reminded",
                        user_id=user_id,
                    )
                else:
                    logger.info(
                        module="cron",
                        message=f"User {user_id} has already recorded their expenses today.",
                    )
            return {
                "status": "success",
                "total_users": len(all_users),
                "reminded_count": count_reminded,
            }

        # --- เส้นที่ 3: สรุปรายเดือน (Run ทุกสิ้นเดือน หรือตามสั่ง) ---
        @router.post("/summary-monthly")
        async def monthly_summary(db: Session = Depends(get_session)):
            all_users = Utilities.get_all_users(db)
            processed_count = 0

            for user in all_users:
                user_id = user.line_user_id
                logger.info(
                    module="cron",
                    message=f"Monthly summary cron job started for {len(all_users)} users",
                    user_id=user_id,
                )
                # ดึงข้อมูลจากฟังก์ชันสรุปที่คุยกันก่อนหน้า
                data = DBManagerDashboard.get_dashboard_data(db, user_id, type="monthly")
                print(f"Monthly summary for user {user_id}: {data}")

                if data["total_amount"] > 0:
                    flex_content = LineUtils.create_summary_flex(
                        title="📊 สรุปรายงานรายเดือน",
                        data=data,
                        current_month_spent=data.get("remaining_budget", 0.0),
                        total_budget=data.get("total_budget", 0.0),
                    )

                    # ส่งเป็น Flex Message
                    LineUtils.send_push_notification(
                        user_id, content=flex_content, alt_text="สรุปยอดรายเดือน"
                    )
                    processed_count += 1
                    logger.info(
                        module="cron",
                        message=f"Monthly summary cron job completed: {processed_count}/{len(all_users)} users notified",
                        user_id=user_id,
                    )
                else:
                    logger.info(
                        module="cron",
                        message=f"User {user_id} has no expenses recorded this month.",
                        user_id=user_id,
                    )
            return {"status": "success", "users_notified": processed_count}
