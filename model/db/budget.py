"""งบประมาณรายเดือนต่อหมวดหมู่ และการซิงก์ยอดสะสม"""

from datetime import datetime

from sqlmodel import Session, extract, func, select

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
    def sync_user_budgets(session: Session, user_id: str, month: int, year: int):
        """
        ฟังก์ชันสำหรับคำนวณยอดใช้จ่ายจริงจาก Transactions
        แล้วนำไปอัปเดตในตาราง UserBudget ให้เป็นปัจจุบันที่สุด
        """
        # 1. ดึงยอดรวมการใช้จ่ายแยกตามหมวดหมู่จาก Transactions จริงของเดือนนั้นๆ
        # สมมติว่า Transaction มีฟิลด์ category_id และ amount
        spent_statement = (
            select(Transactions.category_id, func.sum(Transactions.amount).label("total_spent"))
            .where(
                Transactions.user_id == user_id,
                Transactions.transaction_type == "expense",
                func.extract("month", Transactions.transaction_date) == month,
                func.extract("year", Transactions.transaction_date) == year,
            )
            .group_by(Transactions.category_id)
        )

        actual_spent_results = session.exec(spent_statement).all()

        # 2. นำยอดที่ได้ไป Update ใน UserBudget
        for cat_id, total_spent in actual_spent_results:
            # หาตารางงบประมาณที่ตรงกับหมวดหมู่และเดือนนั้น
            budget_record = session.exec(
                select(UserBudget).where(
                    UserBudget.user_id == user_id,
                    UserBudget.category_id == cat_id,
                    UserBudget.month == month,
                    UserBudget.year == year,
                )
            ).first()

            if budget_record:
                budget_record.current_spent = float(total_spent)
                session.add(budget_record)

        session.commit()  # บันทึกการอัปเดตทั้งหมด
