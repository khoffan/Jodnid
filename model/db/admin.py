"""ข้อมูลสำหรับ Admin console และ System configuration"""

import json
from datetime import datetime

import requests
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, desc, select

from model.models import Administrator, SystemConfiguration


CONFIG_VALUE_TYPES = ("string", "boolean", "int", "json")


def validate_config_value(value: str | None, value_type: str) -> str | None:
    """ตรวจว่าค่า config แปลงตาม `value_type` ได้จริง (กติกาเดียวกับ `Utilities.get_config_value`)

    คืนข้อความ error ภาษาไทย หรือ None ถ้าถูกต้อง — ค่าที่ผิดชนิดเคยทำให้ webhook พังตอนอ่าน config
    """
    if value_type not in CONFIG_VALUE_TYPES:
        return f"ไม่รู้จักชนิด '{value_type}' (ใช้ได้: {', '.join(CONFIG_VALUE_TYPES)})"
    text = "" if value is None else str(value)
    if value_type == "boolean" and text.lower() not in ("true", "false"):
        return "ค่าชนิด boolean ต้องเป็น true หรือ false"
    if value_type == "int":
        try:
            int(text)
        except ValueError:
            return "ค่าชนิด int ต้องเป็นจำนวนเต็ม"
    if value_type == "json":
        try:
            json.loads(text)
        except json.JSONDecodeError:
            return "ค่าชนิด json ไม่ถูกต้อง"
    return None


class DBManagerAdmin:
    # administrator db menament
    @staticmethod
    def sync_administrator_profile(
        session: Session,
        uid: str,
        email: str = None,
        name: str = None,
        phone: str = None,
        profile: str = None,
    ):
        """
        อัปเดตโปรไฟล์ของ admin ที่มีสิทธิ์อยู่แล้วให้ตรงกับข้อมูลจาก Firebase

        ⚠️ ห้ามสร้างแถวใหม่ที่นี่เด็ดขาด ถ้าสร้างได้ ใครก็ตามที่สมัคร Firebase account เอง
        (API key อยู่ใน bundle ฝั่ง client) จะยกระดับตัวเองเป็น admin ได้ทันที
        การเพิ่ม admin ต้องทำผ่าน `python scripts/seed_admin.py` เท่านั้น
        """
        admin = session.exec(select(Administrator).where(Administrator.uid == uid)).first()
        if not admin:
            return {"success": False, "message": "Administrator not found"}

        if email:
            admin.email = email
        if name:
            admin.name = name
        if phone:
            admin.phone = phone
        if profile:
            admin.profile = profile
        admin.updated_at = datetime.utcnow()

        session.add(admin)
        session.commit()
        session.refresh(admin)
        return {"success": True, "data": admin.dict()}

    @staticmethod
    def create_system_config(
        session: Session, name: str, key: str, value: str, value_type: str, description: str
    ):
        error = validate_config_value(value, value_type)
        if error:
            return {"success": False, "message": error}

        system_configuration = SystemConfiguration(
            name=name, key=key, value=value, value_type=value_type, description=description
        )
        session.add(system_configuration)
        try:
            session.commit()
        except IntegrityError:
            # ทั้ง name และ key เป็น unique — ถ้าซ้ำต้องบอกให้ชัด ไม่ใช่ปล่อยเป็น 500
            session.rollback()
            return {"success": False, "message": f"ชื่อ '{name}' หรือ key '{key}' ถูกใช้ไปแล้ว"}

        session.refresh(system_configuration)
        return {"success": True, "data": system_configuration}

    @staticmethod
    def get_system_status(session: Session, line_access_token: str = None):
        """
        เช็คสถานะจริงของระบบ ไม่ใช่ค่าคงที่

        ทุกด่านห้ามโยน exception ออกไป เพราะหน้า console ต้องแสดงผลได้เสมอ
        แม้ระบบใดระบบหนึ่งจะล่ม (นั่นคือข้อมูลที่ admin ต้องการเห็นพอดี)
        """
        from helper.utils import Utilities

        # --- ฐานข้อมูล ---
        try:
            session.exec(select(SystemConfiguration).limit(1)).first()
            database = {"ok": True, "detail": "Connected"}
        except Exception as e:
            database = {"ok": False, "detail": f"Error: {type(e).__name__}"}

        # --- LINE Messaging API ---
        line_status = {"ok": False, "detail": "No token"}
        if line_access_token:
            try:
                response = requests.get(
                    "https://api.line.me/v2/bot/info",
                    headers={"Authorization": f"Bearer {line_access_token}"},
                    timeout=5,
                )
                if response.status_code == 200:
                    line_status = {"ok": True, "detail": response.json().get("displayName", "Online")}
                else:
                    line_status = {"ok": False, "detail": f"HTTP {response.status_code}"}
            except Exception as e:
                line_status = {"ok": False, "detail": f"Error: {type(e).__name__}"}

        # --- สวิตช์ฟีเจอร์ (ค่าเริ่มต้นตรงกับที่ webhook ใช้จริง) ---
        # get_config_value เปิด connection เอง — DB ล่มต้องรายงานว่า "ไม่ทราบ" ไม่ใช่ทำให้ทั้งหน้าพัง
        features = {}
        for key, default in (
            ("is_ocr_active", True),
            ("is_text_active", True),
            ("is_maintenance_mode", False),
        ):
            try:
                features[key] = bool(Utilities.get_config_value(key=key, default=default))
            except Exception:
                features[key] = None

        return {"database": database, "line_api": line_status, "features": features}

    @staticmethod
    def get_system_config_data(session: Session):
        statement = select(SystemConfiguration).order_by(desc(SystemConfiguration.created_at))

        system_configuration = session.exec(statement).all()
        system_configuration_list = [config.dict() for config in system_configuration]
        return {"success": True, "data": system_configuration_list}

    @staticmethod
    def update_system_config(
        session: Session,
        key: str,
        value: str,
        value_type: str = None,
        description: str = None,
        name: str = None,
    ):
        # 1. ค้นหา Config ด้วย Key
        statement = select(SystemConfiguration).where(SystemConfiguration.key == key)
        system_configuration = session.exec(statement).first()

        if not system_configuration:
            return {"success": False, "message": "System configuration not found"}

        # ตรวจเมื่อค่าหรือชนิดเปลี่ยนเท่านั้น — แถวเก่าที่ค่าผิดชนิดอยู่แล้วยังแก้ชื่อ/คำอธิบายได้
        if value != system_configuration.value or value_type:
            error = validate_config_value(value, value_type or system_configuration.value_type)
            if error:
                return {"success": False, "message": error}

        # 2. อัปเดตค่า (ตรวจสอบก่อนว่ามีการส่งค่าใหม่มาไหม)
        system_configuration.value = value
        if value_type:
            system_configuration.value_type = value_type
        if description:
            system_configuration.description = description
        if name:
            # หน้าแก้ไขใน console ให้แก้ name ได้ ถ้าไม่รับตรงนี้ค่าที่ผู้ใช้แก้จะเงียบหาย
            system_configuration.name = name

        # 3. อัปเดตเวลาแก้ไขล่าสุด
        system_configuration.updated_at = datetime.utcnow()

        session.add(system_configuration)
        try:
            session.commit()
        except IntegrityError:
            # `name` เป็น unique ถ้าซ้ำกับตัวอื่นต้องบอกให้ชัด ไม่ใช่ปล่อยเป็น 500
            session.rollback()
            return {"success": False, "message": f"ชื่อ '{name}' ถูกใช้ไปแล้ว"}

        session.refresh(system_configuration)
        return {"success": True, "data": system_configuration}
