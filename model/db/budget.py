"""งบประมาณรายเดือนต่อหมวดหมู่ และการซิงก์ยอดสะสม"""

from datetime import datetime

from sqlmodel import Session, select

from model.models import Categories, Transactions, UserBudget


class DBManagerBudget:
    @staticmethod
    def get_user_budget(session: Session, user_id: str, month: int, year: int):
        try:
            statement = select(UserBudget).where(
                UserBudget.user_id == user_id,
                UserBudget.month == month,
                UserBudget.year == year,
            )
            budgets = session.exec(statement).all()
            return budgets
        except Exception as e:
            print(f"Error in get_user_budget: {str(e)}")
            return []

    @staticmethod
    def can_setup_budget_this_month(session: Session, user_id: str) -> bool:
        try:
            now = datetime.now()
            statement = select(UserBudget).where(
                UserBudget.user_id == user_id,
                UserBudget.month == now.month,
                UserBudget.year == now.year,
            )
            budget = session.exec(statement).first()

            # ถ้าเดือนปัจจุบันยังไม่มีงบประมาณใน DB ให้คืนค่า True
            return budget is None
        except Exception as e:
            print(f"Error in can_setup_budget_this_month: {str(e)}")
            return False

    @staticmethod
    def setup_user_budget(session: Session, user_id: str, category_id: int, amount: float):
        try:
            now = datetime.now()

            # 1. ตรวจสอบก่อนว่า category_id ที่ส่งมาคือ Parent Category จริงหรือไม่ (กันพลาด)
            category = session.get(Categories, category_id)
            print(f"category {category}")
            if not category or category.parent_id is not None:
                return {
                    "success": False,
                    "message": "กรุณาเลือกหมวดหมู่หลัก (Parent Category) ในการตั้งงบประมาณ",
                }

            # 2. ค้นหาว่าในเดือน/ปี และหมวดหมู่นี้ User เคยตั้งงบไว้หรือยัง
            statement = select(UserBudget).where(
                UserBudget.user_id == user_id,
                UserBudget.category_id == category_id,
                UserBudget.month == now.month,
                UserBudget.year == now.year,
            )
            budget = session.exec(statement).first()

            if budget:
                # กรณีมีอยู่แล้ว -> อัปเดตยอดงบใหม่
                budget.amount = amount
            else:
                # กรณีไม่มี -> สร้างใหม่ พร้อมตั้งค่าเริ่มต้น current_spent เป็น 0
                budget = UserBudget(
                    user_id=user_id,
                    category_id=category_id,
                    amount=amount,
                    current_spent=0.0,
                    month=now.month,
                    year=now.year,
                )
                session.add(budget)

            session.commit()
            return {"success": True, "message": f"ตั้งงบประมาณหมวด {category.name} เรียบร้อยแล้วครับ"}
        except Exception as e:
            print(f"Error in setup_user_budget: {str(e)}")
            return {"success": False, "message": "เกิดข้อผิดพลาดในการตั้งงบประมาณ กรุณาลองใหม่อีกครั้ง"}

    @staticmethod
    def sync_user_budgets(session: Session, user_id: str, month: int, year: int) -> dict:
        """
        เครื่องมือซ่อม `UserBudget.current_spent` (ยอดสะสมแบบ denormalized) ให้ตรงกับ Transactions จริง

        - รวมยอดหมวดลูกขึ้นหมวดแม่ (`parent_id or id`) เหมือนตอนตัดงบใน `save_transaction`
        - นับเฉพาะรายจ่ายของเดือนนั้น และหมวดที่ไม่มีรายจ่ายแล้วจะถูก reset เป็น 0
        ห้ามเรียกจากเส้นทางอ่านข้อมูล (เช่นหน้า overview) — ใช้ผ่านปุ่มใน admin หรือ cron เท่านั้น
        """
        month_start = datetime(year, month, 1)
        next_month = datetime(year + month // 12, month % 12 + 1, 1)
        rows = session.exec(
            select(Transactions.amount, Categories.id, Categories.parent_id)
            .join(Categories, Transactions.category_id == Categories.id)
            .where(
                Transactions.user_id == user_id,
                Transactions.transaction_type == "expense",
                Transactions.transaction_date >= month_start,
                Transactions.transaction_date < next_month,
            )
        ).all()

        spent_by_parent: dict[int, float] = {}
        for amount, category_id, parent_id in rows:
            key = parent_id or category_id
            spent_by_parent[key] = spent_by_parent.get(key, 0.0) + float(amount)

        budgets = session.exec(
            select(UserBudget).where(
                UserBudget.user_id == user_id,
                UserBudget.month == month,
                UserBudget.year == year,
            )
        ).all()

        changes = []
        for budget in budgets:
            actual = round(spent_by_parent.get(budget.category_id, 0.0), 2)
            if abs(budget.current_spent - actual) > 0.001:
                changes.append(
                    {"category_id": budget.category_id, "from": budget.current_spent, "to": actual}
                )
                budget.current_spent = actual
                session.add(budget)

        session.commit()
        return {"updated": len(changes), "changes": changes}

    @staticmethod
    def sync_all_budgets(session: Session, month: int, year: int) -> dict:
        """ซ่อมยอดของทุกคนที่มีงบในเดือนนั้น (ใช้กับ cron ทุกคืน)"""
        user_ids = session.exec(
            select(UserBudget.user_id)
            .where(UserBudget.month == month, UserBudget.year == year)
            .distinct()
        ).all()
        updated = 0
        for user_id in user_ids:
            updated += DBManagerBudget.sync_user_budgets(session, user_id, month, year)["updated"]
        return {"users": len(user_ids), "updated": updated}
