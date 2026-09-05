"""ข้อมูลสำหรับ Admin console และ System configuration"""

from datetime import datetime

from sqlmodel import Session, desc, select

from model.models import Administrator, SystemConfiguration


class DBManagerAdmin:
    def __init__(self):
        pass

    # administrator db menament
    @staticmethod
    def update_administrator_data_system(session: Session, uid: str, email: str):
        admin = session.exec(select(Administrator).where(Administrator.uid == uid)).first()
        if admin:
            admin.email = email
            session.add(admin)
            session.commit()
        else:
            admin = Administrator(
                uid=uid,
                email=email,
            )
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
        session.commit()
        session.refresh(system_configuration)
        return {"success": True, "data": system_configuration}

    @staticmethod
    def get_system_config_data(self, session: Session):
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
    ):
        # 1. ค้นหา Config ด้วย Key
        statement = select(SystemConfiguration).where(SystemConfiguration.key == key)
        system_configuration = session.exec(statement).first()

        if system_configuration:
            # 2. อัปเดตค่า (ตรวจสอบก่อนว่ามีการส่งค่าใหม่มาไหม)
            system_configuration.value = value
            if value_type:
                system_configuration.value_type = value_type
            if description:
                system_configuration.description = description

            # 3. อัปเดตเวลาแก้ไขล่าสุด
            system_configuration.updated_at = datetime.utcnow()

            session.add(system_configuration)
            session.commit()
            session.refresh(system_configuration)

            return {"success": True, "data": system_configuration}

        return {"success": False, "message": "System configuration not found"}
