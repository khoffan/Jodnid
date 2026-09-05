"""หมวดหมู่รายจ่าย (ส่วนกลางและของผู้ใช้แต่ละคน)"""

from typing import List

from sqlmodel import Session, and_, select

from model.models import Categories


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
