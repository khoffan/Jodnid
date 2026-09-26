"""รวมยอดสำหรับหน้าสรุปและ Flex รายวัน/รายเดือน"""

from datetime import datetime

from sqlmodel import Session, and_, desc, extract, select

from model.models import Categories, Transactions, UserBudget


class DBManagerDashboard:
    @staticmethod
    def get_dashboard_data(
        session: Session,
        user_id: str,
        type: str = "monthly",
        day: int = None,
        month: int = None,
        year: int = None,
    ):
        try:
            now = datetime.now()

            target_month = int(month) if month else now.month
            target_year = int(year) if year else now.year
            target_day = int(day) if day else now.day
            # สร้างเงื่อนไขพื้นฐาน (Filter by User)
            filters = [Transactions.user_id == user_id]

            if type == "daily":
                # --- Logic สำหรับรายวัน ---
                # กรองเฉพาะ วัน/เดือน/ปี ปัจจุบัน
                filters.append(extract("day", Transactions.transaction_date) == target_day)
                filters.append(extract("month", Transactions.transaction_date) == target_month)
                filters.append(extract("year", Transactions.transaction_date) == target_year)
            else:
                filters.append(extract("month", Transactions.transaction_date) == target_month)
                filters.append(extract("year", Transactions.transaction_date) == target_year)

            # 1. ดึงข้อมูล Transactions พร้อมหมวดหมู่ (เรียงลำดับใหม่ล่าสุดขึ้นก่อน)
            statement = (
                select(Transactions, Categories)
                .join(Categories, isouter=True)
                .where(and_(*filters))
                .order_by(Transactions.transaction_date.desc())  # เอาล่าสุดขึ้นก่อน
            )
            results = session.exec(statement).all()

            budget_statement = select(UserBudget).where(
                UserBudget.user_id == user_id,
                UserBudget.month == target_month,
                UserBudget.year == target_year,
            )
            budget_results = session.exec(budget_statement).all()
            total_budget = sum(budget.amount for budget in budget_results)
            remaining_budget = total_budget - sum(budget.current_spent for budget in budget_results)

            # 2. คำนวณยอดรวมและ Summary
            summary_by_cat = {}
            total_amount = 0

            for tx, cat in results:
                # ยอดรวมและสรุปรายหมวดคือ "ยอดใช้จ่าย" จึงไม่นับรายรับ
                if tx.transaction_type != "expense":
                    continue
                cat_name = cat.name if cat else "ทั่วไป"
                summary_by_cat[cat_name] = summary_by_cat.get(cat_name, 0) + tx.amount
                total_amount += tx.amount

            return {
                "total_amount": total_amount,
                "summary": summary_by_cat,
                "total_budget": total_budget,
                "remaining_budget": remaining_budget,
                "transactions": [
                    {
                        "item": tx.item_name,
                        "amount": tx.amount,
                        "type": tx.transaction_type,
                        "date": tx.transaction_date.strftime(
                            "%H:%M" if type == "daily" else "%d/%m/%Y"
                        ),  # ถ้ารายวันโชว์เป็นเวลาแทน
                        "icon": cat.icon if cat else "✨",
                        "category": cat.name if cat else "ทั่วไป",
                    }
                    for tx, cat in results[:10]
                ],
            }
        except Exception as e:
            print(f"Error in get_dashboard_data: {str(e)}")
            return {"total_amount": 0, "summary": {}, "transactions": []}
