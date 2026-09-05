"""ข้อมูลสำหรับ Admin console และ System configuration"""

from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, desc, select

from model.models import Administrator, SystemConfiguration


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
