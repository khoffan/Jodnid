import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlmodel import Session, and_, desc, extract, func, select

from model.models import (
    Administrator,
    Attachments,
    Categories,
    CategoryMapping,
    SystemConfiguration,
    TempTransactions,
    Transactions,
    UserBudget,
    Users,
)


class DBManagerUsers:
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


class DBManagerTransactions:
    @staticmethod
    def save_temp_transaction(
        session: Session,
        user_id: str,
        raw_data: List[Dict[str, Any]],
        attachment_id: str = None,
        source_type: str = "text",
    ):
        try:
            temp_entry = TempTransactions(
                user_id=user_id,
                raw_data=raw_data,
                attachment_id=attachment_id,
                source_type=source_type,
            )
            session.add(temp_entry)
            session.commit()
            session.refresh(temp_entry)
            return temp_entry.id
        except Exception as e:
            print(f"Error in save_temp_transaction: {str(e)}")
            return None

    @staticmethod
    def delete_temp_transaction(session: Session, temp_id: str):
        try:
            temp = session.get(TempTransactions, temp_id)
            if temp:
                session.delete(temp)
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error in delete_temp_transaction: {str(e)}")
            return False

    @staticmethod
    def undo_transaction(session: Session, user_id: str, undo_token: str):
        try:
            statement = select(Transactions).where(
                Transactions.user_id == user_id,
                Transactions.undo_token == undo_token,
            )
            transactions = session.exec(statement).all()
            if not transactions:
                return False

            budget_updates = {}
            for transaction in transactions:
                parent_id = None
                if transaction.category_id and transaction.category:
                    parent_id = (
                        transaction.category.parent_id
                        if transaction.category.parent_id
                        else transaction.category.id
                    )
                elif transaction.category_id:
                    parent_id = transaction.category_id

                if parent_id:
                    key = (
                        parent_id,
                        transaction.transaction_date.month,
                        transaction.transaction_date.year,
                    )
                    budget_updates[key] = budget_updates.get(key, 0.0) + transaction.amount

                session.delete(transaction)

            for (parent_id, month, year), amount_to_reduce in budget_updates.items():
                budget_statement = select(UserBudget).where(
                    UserBudget.user_id == user_id,
                    UserBudget.category_id == parent_id,
                    UserBudget.month == month,
                    UserBudget.year == year,
                )
                budget = session.exec(budget_statement).first()
                if budget:
                    budget.current_spent = max(0.0, budget.current_spent - amount_to_reduce)
                    session.add(budget)

            session.commit()
            return True
        except Exception as e:
            print(f"Error in undo_transaction: {str(e)}")
            return False

    # บันทึกจากชั่วคร่าวเข้าตารางจริง (รองรับทั้งกรณีมี Temp และไม่มี Temp)
    @staticmethod
    def save_transaction(
        session: Session,
        temp: TempTransactions = None,
        user_id: str = None,
        edit: bool = False,
        items: List[Dict[str, Any]] = None,
        skip_confirm: bool = False,
        attachment_id: str = None,
        undo_token: str = None,
    ):
        # ดึงหมวด "อื่นๆ" ไว้รอเลย เผื่อต้องใช้ (Fallback)
        statement_other = select(Categories).where(
            Categories.name == "อื่นๆ", Categories.parent_id.is_(None)
        )
        default_parent = session.exec(statement_other).first()
        if not default_parent:
            default_parent = Categories(name="อื่นๆ", icon="✨")
            session.add(default_parent)
            session.flush()

        total_amount = 0.0
        item_count = 0
        updated_budgets_info = []  # เก็บข้อมูล Budget ที่ถูกอัปเดต
        processed_parent_ids = set()  # ป้องกันการดึง Budget ซ้ำถ้ามีหลายรายการใน Parent เดียวกัน
        now = datetime.now()
        batch_undo_token = undo_token or str(uuid.uuid4())

        if edit:
            raw_data = items
        elif temp is None:
            raw_data = items
        else:
            raw_data = temp.raw_data.get("transactions", [])
        for item in raw_data:
            if not item.get("is_actual_item", True) or item.get("priority", True):
                continue
            raw_cat_name = str(item.get("category", "อื่นๆ")).strip()

            # 2. ค้นหาใน Mapping Table ก่อน
            # 1. ค้นหาใน Mapping Table (เช่น AI ส่ง "อาหาร" มา -> เจอ "อาหารและเครื่องดื่ม")
            mapping = session.exec(
                select(CategoryMapping).where(CategoryMapping.alias_name == raw_cat_name)
            ).first()
            if mapping:
                target_cat = mapping.category
            else:
                target_cat = session.exec(
                    select(Categories).where(Categories.name == raw_cat_name)
                ).first()

                if not target_cat:
                    target_cat = default_parent

                    new_mapping = CategoryMapping(
                        alias_name=raw_cat_name,
                        category_id=default_parent.id,  # ผูกเข้ากับ ID ของ "อื่นๆ" หลัก
                    )
                    session.add(new_mapping)

            parent_id = target_cat.parent_id if target_cat.parent_id else target_cat.id

            # 2. บันทึก Transaction
            amount = float(item.get("amount", 0))
            new_tx = Transactions(
                user_id=(temp.user_id if temp else user_id),
                amount=amount,
                item_name=item.get("item")
                or item.get("receiver")
                or item.get("note")
                or "ไม่ระบุรายการ",
                transaction_type="expense",
                category_id=target_cat.id,
                transaction_date=now,
                source_type=item.get("source_type", "text"),
                is_confirmed=not skip_confirm,
                attachment_id=attachment_id
                if attachment_id
                else (temp.attachment_id if temp else None),
                undo_token=batch_undo_token,
            )
            session.add(new_tx)

            # 3. อัปเดต UserBudget (ตัดงบที่ Parent)
            statement_b = select(UserBudget).where(
                UserBudget.user_id == (temp.user_id if temp else user_id),
                UserBudget.category_id == parent_id,
                UserBudget.month == now.month,
                UserBudget.year == now.year,
            )
            budget = session.exec(statement_b).first()

            if budget:
                budget.current_spent += amount
                session.add(budget)
                # เก็บ ID ไว้เพื่อไปดึงข้อมูลสรุปหลัง commit
                processed_parent_ids.add(budget.id)

            total_amount += amount
            item_count += 1

        # 4. ลบ Temp และ Commit เพื่อให้ข้อมูลลง DB จริง
        if temp is not None:
            session.delete(temp)
        session.commit()

        # 5. ดึงข้อมูล Budget ที่อัปเดตแล้วมาเตรียมส่งกลับ (ต้องดึงใหม่หลัง commit เพื่อความชัวร์)
        for b_id in processed_parent_ids:
            b = session.get(UserBudget, b_id)
            if b:
                updated_budgets_info.append(
                    {
                        "category_name": b.category.name,
                        "amount": b.amount,
                        "current_spent": b.current_spent,
                        "icon": b.category.icon,
                    }
                )

        return {
            "current_transaction_id": new_tx.id,
            "undo_token": batch_undo_token,
            "count": item_count,
            "total": total_amount,
            "budgets": updated_budgets_info,  # ส่งข้อมูลสรุปงบกลับไป
        }

    # --- 3. ย้ายข้อมูลจาก Temp ไปเป็น Transaction จริง (รองรับ Category และ Attachment) ---
    @staticmethod
    def confirm_and_save_transaction(
        session: Session,
        temp_id: str = None,
        user_id: str = None,
        edit: bool = False,
        items: List[Dict[str, Any]] = None,
        attachment_id: str = None,
        skip_confirm: bool = False,
        undo_token: str = None,
    ):
        try:
            # 1. ดึงข้อมูลชั่วคราว
            if temp_id is None and items is not None:
                return DBManagerTransactions.save_transaction(
                    session=session,
                    temp=None,
                    user_id=user_id,
                    edit=edit,
                    items=items,
                    skip_confirm=skip_confirm,
                    attachment_id=attachment_id,
                    undo_token=undo_token,
                )
            else:
                temp = session.get(TempTransactions, temp_id)
                if not temp:
                    return False
                return DBManagerTransactions.save_transaction(
                    session=session,
                    temp=temp,
                    user_id=None,
                    edit=edit,
                    items=items,
                    skip_confirm=skip_confirm,
                    undo_token=undo_token,
                )
        except Exception as e:
            print(f"Error in confirm_and_save_transaction: {str(e)}")
            return False

    # --- 4. บันทึก Metadata ของรูปภาพ ---
    @staticmethod
    def create_attachment_record(
        session: Session, user_id: str, file_path: str, file_type: str = "image/jpeg"
    ):
        try:
            new_attachment = Attachments(
                id=str(uuid.uuid4()),
                user_id=user_id,
                file_path=file_path,  # ควรเป็น Relative Path
                file_type=file_type,
            )
            session.add(new_attachment)
            session.commit()
            session.refresh(new_attachment)
            return new_attachment.id
        except Exception as e:
            print(f"Error in create_attachment_record: {str(e)}")
            return None

    # ดึงข้อมูล temp transaction เพื่อแสดงผลก่อนยืนยัน (กรณีมี temp_id)
    @staticmethod
    def get_temp_transaction_data(session: Session, temp_id):
        try:
            statement = select(TempTransactions).where(TempTransactions.id == temp_id)
            return session.exec(statement).first()
        except Exception as e:
            print(f"Error in get_temp_transaction_data: {str(e)}")
            return None

    @staticmethod
    def get_Transactions(session: Session):
        try:
            # ทำการ Join ระหว่าง Transactions และ Category โดยใช้ category_id
            statement = select(Transactions, Categories).join(Categories)
            results = session.exec(statement).all()

            # แปลงผลลัพธ์ให้อยู่ในรูปแบบที่นำไปใช้งานต่อได้ง่าย (เช่น รวมข้อมูลเข้าด้วยกัน)
            combined_data = []
            for tx, cat in results:
                tx_data = tx.model_dump()  # หรือ tx.__dict__ ในกรณีใช้ SQLAlchemy ธรรมดา
                # เพิ่มข้อมูล category เข้าไปใน Transaction Object
                tx_data["category_name"] = cat.name if cat else "ไม่มีหมวดหมู่"
                combined_data.append(tx_data)

            return combined_data
        except Exception as e:
            print(f"Error in get_Transactions: {str(e)}")
            return []

    @staticmethod
    def get_transaction_by_id(session: Session, transaction_id: str):
        try:
            statement = select(Transactions).where(Transactions.id == transaction_id)
            return session.exec(statement).first()
        except Exception as e:
            print(f"Error in get_transaction_by_id: {str(e)}")
            return None


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
    def get_parent_categories(session: Session) -> List[Categories]:
        try:
            # เลือกเฉพาะรายการที่ไม่มี parent_id (เป็นรากของหมวดหมู่)
            statement = select(Categories).where(Categories.parent_id.is_(None))
            results = session.exec(statement).all()

            return results
        except Exception as e:
            print(f"Error in get_parent_categories: {str(e)}")
            return []


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
