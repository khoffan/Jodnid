"""หมวดหมู่รายจ่าย (ส่วนกลางและของผู้ใช้แต่ละคน)"""

from typing import List

from sqlmodel import Session, and_, or_, select

from model.models import Categories, Transactions, UserBudget


class DBManagerCategories:
    # --- 5. จัดการ Category (เพื่อความง่ายในการเรียกใช้) ---
    @staticmethod
    def get_all_categories(session: Session) -> List[Categories]:
        try:
            statement = select(Categories)
            return session.exec(statement).all()
        except Exception as e:
            print(f"Error in get_all_categories: {str(e)}")
            return []

    @staticmethod
    def get_category_by_name(session: Session, name: str):
        try:
            statement = select(Categories).where(Categories.name == name)
            return session.exec(statement).first()
        except Exception as e:
            print(f"Error in get_category_by_name: {str(e)}")
            return None

    @staticmethod
    def insert_category(
        session: Session, name: str, icon: str = "📁", parent_id: int = None, user_id: str = None
    ):
        try:
            new_category = Categories(name=name, icon=icon, parent_id=parent_id, user_id=user_id)
            session.add(new_category)
            session.commit()
            session.refresh(new_category)
            return new_category
        except Exception as e:
            print(f"Error in insert_category: {str(e)}")
            return None

    @staticmethod
    def get_global_categories(session: Session) -> List[dict]:
        """
        หมวดหมู่ส่วนกลาง (`user_id IS NULL`) ที่ผู้ใช้ทุกคนเห็น

        เพิ่มที่นี่แล้ว prompt ของ AI จะดึงไปเองผ่าน `generate_system_prompt_categories()`
        จึงเป็นวิธีเดียวที่ควรใช้เพิ่มหมวดหมู่ ห้าม hardcode ลง prompt
        """
        statement = (
            select(Categories).where(Categories.user_id.is_(None)).order_by(Categories.name)
        )
        categories = session.exec(statement).all()
        by_id = {category.id: category for category in categories}

        return [
            {
                "id": category.id,
                "name": category.name,
                "icon": category.icon,
                "color_code": category.color_code,
                "parent_id": category.parent_id,
                "parent_name": (
                    by_id[category.parent_id].name if category.parent_id in by_id else None
                ),
            }
            for category in categories
        ]

    @staticmethod
    def create_global_category(
        session: Session, name: str, icon: str = "📁", parent_id: int = None
    ):
        name = (name or "").strip()
        if not name:
            return {"success": False, "message": "ต้องระบุชื่อหมวดหมู่"}

        exists = session.exec(
            select(Categories).where(
                and_(Categories.name == name, Categories.user_id.is_(None))
            )
        ).first()
        if exists:
            return {"success": False, "message": f"มีหมวดหมู่ '{name}' อยู่แล้ว"}

        if parent_id is not None:
            parent = session.get(Categories, parent_id)
            if not parent or parent.user_id is not None:
                return {"success": False, "message": "ไม่พบหมวดหมู่แม่ที่ระบุ"}

        category = Categories(name=name, icon=icon or "📁", parent_id=parent_id, user_id=None)
        session.add(category)
        session.commit()
        session.refresh(category)
        return {"success": True, "data": category.dict()}

    @staticmethod
    def update_global_category(
        session: Session, category_id: int, name: str = None, icon: str = None
    ):
        category = session.get(Categories, category_id)
        if not category or category.user_id is not None:
            return {"success": False, "message": "ไม่พบหมวดหมู่ส่วนกลางนี้"}

        if name and name.strip():
            category.name = name.strip()
        if icon:
            category.icon = icon

        session.add(category)
        session.commit()
        session.refresh(category)
        return {"success": True, "data": category.dict()}

    @staticmethod
    def delete_global_category(session: Session, category_id: int):
        """
        ลบหมวดหมู่ส่วนกลาง — ปฏิเสธถ้ายังมีอะไรอ้างถึงอยู่

        ลบทั้งที่ยังมี Transactions ผูกอยู่จะทำให้ประวัติของผู้ใช้เสียหาย
        และ UserBudget ที่ผูกกับหมวดนั้นจะกลายเป็นงบลอย
        """
        category = session.get(Categories, category_id)
        if not category or category.user_id is not None:
            return {"success": False, "message": "ไม่พบหมวดหมู่ส่วนกลางนี้"}

        if session.exec(
            select(Transactions).where(Transactions.category_id == category_id).limit(1)
        ).first():
            return {"success": False, "message": "ลบไม่ได้ เพราะยังมีรายการที่ใช้หมวดหมู่นี้อยู่"}

        if session.exec(
            select(UserBudget).where(UserBudget.category_id == category_id).limit(1)
        ).first():
            return {"success": False, "message": "ลบไม่ได้ เพราะยังมีงบประมาณที่ผูกกับหมวดหมู่นี้"}

        if session.exec(
            select(Categories).where(Categories.parent_id == category_id).limit(1)
        ).first():
            return {"success": False, "message": "ลบไม่ได้ เพราะยังมีหมวดหมู่ย่อยอยู่ข้างใน"}

        session.delete(category)
        session.commit()
        return {"success": True, "message": f"ลบหมวดหมู่ '{category.name}' แล้ว"}

    @staticmethod
    def can_use_category(session: Session, category_id: int, user_id: str) -> bool:
        """หมวดใช้ได้เมื่อเป็นหมวดส่วนกลาง (`user_id IS NULL`) หรือเป็นของผู้ใช้คนนี้"""
        category = session.get(Categories, category_id)
        return category is not None and category.user_id in (None, user_id)

    @staticmethod
    def get_user_parent_categories(session: Session, user_id: str) -> List[Categories]:
        """หมวดหลักที่ผู้ใช้คนนี้เลือกได้: หมวดส่วนกลาง + หมวดที่ผู้ใช้สร้างเอง (ส่วนกลางขึ้นก่อน)"""
        statement = (
            select(Categories)
            .where(
                Categories.parent_id.is_(None),
                or_(Categories.user_id.is_(None), Categories.user_id == user_id),
            )
            .order_by(Categories.user_id.is_not(None), Categories.id)
        )
        return session.exec(statement).all()

    @staticmethod
    def get_parent_categories(session: Session) -> List[Categories]:
        try:
            # เลือกเฉพาะรายการที่ไม่มี parent_id (เป็นรากของหมวดหมู่)
            statement = select(Categories).where(
                and_(Categories.parent_id.is_(None), Categories.user_id.is_(None))
            )
            results = session.exec(statement).all()

            return results
        except Exception as e:
            print(f"Error in get_parent_categories: {str(e)}")
            return []
