"""จัดการข้อมูลผู้ใช้และสถานะ onboarding"""

from typing import Any, Dict

from sqlmodel import Session, col, desc, func, or_, select

from model.models import Users


class DBManagerUsers:
    @staticmethod
    def search_users(session: Session, search: str = None, limit: int = 50, offset: int = 0):
        """ค้นหาผู้ใช้แบบแบ่งหน้า สำหรับหน้าจัดการผู้ใช้ใน admin console"""
        limit = max(1, min(limit, 200))
        conditions = []
        if search:
            conditions.append(
                or_(
                    col(Users.display_name).contains(search),
                    col(Users.line_user_id).contains(search),
                    col(Users.email).contains(search),
                )
            )

        count_statement = select(func.count()).select_from(Users)
        statement = select(Users).order_by(desc(Users.created_at))
        for condition in conditions:
            count_statement = count_statement.where(condition)
            statement = statement.where(condition)

        total = session.exec(count_statement).one()
        users = session.exec(statement.offset(offset).limit(limit)).all()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [user.dict() for user in users],
        }

    @staticmethod
    def set_user_bypass_mode(session: Session, line_user_id: str, enabled: bool):
        """
        เปิด-ปิดโหมดบันทึกด่วนให้ผู้ใช้จากฝั่ง admin

        ใช้ตอนผู้ใช้แจ้งว่าระบบบันทึกยอดผิด จะได้บังคับให้กลับไปกดยืนยันทุกครั้งก่อน
        """
        user = session.get(Users, line_user_id)
        if not user:
            return {"success": False, "message": "ไม่พบผู้ใช้รายนี้"}

        user.use_bypass_mode = bool(enabled)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"success": True, "data": user.dict()}

    @staticmethod
    def get_or_create_user(session: Session, line_user_id: str, profile: Dict = None) -> Users:
        display_name = profile["display_name"] if profile else "Unknown User"

        user = session.get(Users, line_user_id)

        if not user:
            # กรณี User ใหม่: สร้าง Record ใหม่
            user = Users(line_user_id=line_user_id, display_name=display_name)
            session.add(user)
        else:
            # กรณี User เก่า: เช็คว่าต้องอัปเดตชื่อไหม (ป้องกันค่า null หรือชื่อเก่า)
            if user.display_name != display_name:
                user.display_name = display_name
            if profile.get("email") and user.email != profile.get("email"):
                user.email = profile.get("email")
            if profile.get("picture_url") and user.picture_url != profile.get("picture_url"):
                user.picture_url = profile.get("picture_url")

        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def update_user_config(
        session: Session, line_user_id: str, update_data: Dict[str, Any]
    ) -> bool:
        try:
            # 1. ดึงข้อมูลปัจจุบันของผู้ใช้จาก Database
            user = session.get(Users, line_user_id)

            if not user:
                print(f"User not found: {line_user_id}")
                return False

            # 🛡️ Whitelist: เฉพาะฟิลด์ในโมเดล Users ที่เราอนุญาตให้สลับค่าแบบ PATCH ได้
            allowed_fields = {"display_name", "email", "picture_url", "use_bypass_mode"}

            # 2. ตรวจสอบและวนลูปอัปเดตค่าที่ส่งมาจากชิ้นงานฝั่ง Webhook
            has_changes = False
            for key, value in update_data.items():
                if key in allowed_fields:
                    # เช็คว่าค่าใหม่ต่างจากค่าเดิมใน DB ไหม ป้องกันการสั่ง Update ซ้ำโดยไม่จำเป็น
                    if getattr(user, key) != value:
                        setattr(user, key, value)
                        has_changes = True

            # 3. สั่ง Commit เฉพาะเมื่อตรวจสอบพบข้อมูลเปลี่ยนแปลงจริง
            if has_changes:
                session.add(user)
                session.commit()
                print(f"Successfully PATCH updated profile for user: {line_user_id}")
            else:
                print("No changes detected, skip DB write.")

            return True

        except Exception as e:
            print(f"Failed to update user config: {str(e)}")
            return False

    @staticmethod
    def set_user_onboarded(session: Session, line_user_id: str) -> bool:
        try:
            user = session.get(Users, line_user_id)

            if not user:
                print(f"User not found: {line_user_id}")
                return False

            # ถ้า onboarded แล้ว ไม่ต้องเขียน DB ซ้ำ
            if user.is_onboarded:
                return True

            user.is_onboarded = True
            session.add(user)
            session.commit()
            return True

        except Exception as e:
            print(f"Failed to update onboarding status: {str(e)}")
            return False

    @staticmethod
    def get_user_onboarding_status(session: Session, line_user_id: str) -> Dict[str, Any]:
        try:
            user = session.get(Users, line_user_id)
            if not user:
                return {"success": False, "message": "User not found", "is_onboarded": False}

            return {"success": True, "is_onboarded": bool(user.is_onboarded)}
        except Exception as e:
            print(f"Failed to get onboarding status: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get onboarding status",
                "is_onboarded": False,
            }
