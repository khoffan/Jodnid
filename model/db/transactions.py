"""บันทึก / ยืนยัน / ยกเลิก รายการรับ-จ่าย และไฟล์แนบ"""

import csv
import io
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Session, func, or_, select

from model.db.billable import select_billable_items
from model.db.categories import DBManagerCategories
from model.models import Attachments, Categories, TempTransactions, Transactions, UserBudget


def _resolve_transaction_date(raw_date: Any, now: datetime) -> datetime:
    """แปลง `date` ที่ผู้ใช้กรอก (เช่น "2026-09-20" จากหน้า web) เป็น datetime

    ค่าว่าง / อ่านไม่ออก / อยู่ในอนาคต (เช่นปี พ.ศ. 2569) → ใช้เวลาปัจจุบัน
    ถ้ามาแค่วันที่ จะเติมเวลาปัจจุบันให้ เพื่อให้เรียงลำดับในวันเดียวกันได้
    """
    if not raw_date:
        return now
    try:
        text = str(raw_date).strip()
        parsed = datetime.fromisoformat(text)
        if len(text) == 10:
            parsed = datetime.combine(parsed.date(), now.time())
        parsed = parsed.replace(tzinfo=None)
    except (TypeError, ValueError):
        return now
    return now if parsed > now else parsed


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

                # รายรับไม่เคยถูกตัดงบ จึงไม่ต้องคืนงบ
                if parent_id and transaction.transaction_type == "expense":
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
        grand_total: float = None,
    ):
        # 🎯 หา user_id หลักที่จะใช้ในลูปนี้
        current_user_id = temp.user_id if temp else user_id

        # 1. ดึงหมวด "อื่นๆ" ของระบบ (Global Fallback)
        statement_other = select(Categories).where(
            Categories.name == "อื่นๆ",
            Categories.parent_id.is_(None),
            Categories.user_id.is_(None),  # 🔒 ดึงเฉพาะของส่วนกลางเท่านั้น
        )
        default_parent = session.exec(statement_other).first()
        if not default_parent:
            default_parent = Categories(name="อื่นๆ", icon="✨", user_id=None)
            session.add(default_parent)
            session.flush()

        total_amount = 0.0
        item_count = 0
        updated_budgets_info = []
        processed_parent_ids = set()
        now = datetime.now()
        batch_undo_token = undo_token or str(uuid.uuid4())

        if edit:
            raw_data = items
        elif temp is None:
            raw_data = items
        else:
            raw_data = temp.raw_data.get("transactions", [])
            if grand_total is None:
                grand_total = temp.raw_data.get("grand_total")

        # เผื่อผู้เรียกส่งก้อน dict เต็มๆ มาแทนที่จะแกะ transactions ออกมาก่อน
        if isinstance(raw_data, dict):
            if grand_total is None:
                grand_total = raw_data.get("grand_total")
            raw_data = raw_data.get("transactions", [])

        # ยึด grand_total เป็นตัวตัดสินว่าจะบวกยอด VAT ที่แยกบรรทัดหรือไม่ (ดู select_billable_items)
        billable_items, total_matched = select_billable_items(raw_data, grand_total)

        new_tx = None

        for item in billable_items:

            # ล้างช่องว่างหัวท้ายที่ AI อาจจะแถมมา
            raw_cat_name = str(item.get("category", "อื่นๆ")).strip()
            # 🧹 STEP SPACES SPLIT NORMALIZATION
            # ถ้า AI ส่งมาเป็น "🍔 อาหารและเครื่องดื่ม" การ split(" ") จะได้เป็น ["🍔", "อาหารและเครื่องดื่ม"]
            parts = raw_cat_name.split(" ")
            
            if len(parts) > 1:
                # ถ้ารูปแบบมีช่องว่างคั่น ให้ดึงคำสุดท้ายที่เป็นชื่อหมวดหมู่ดิบๆ มาใช้
                clean_cat_name = parts[-1].strip()
            else:
                # ถ้าไม่มีช่องว่าง (ส่งมาแค่ชื่อปกติ) ก็ใช้ค่าเดิมได้เลย
                clean_cat_name = raw_cat_name

            # 🚨 Fallback กันเหนียวเผื่อตัดแล้วได้ค่าว่าง
            if not clean_cat_name:
                clean_cat_name = "อื่นๆ"

            # 2. 🎯 ค้นหาตรงๆ ในตาราง Categories (สโคปเฉพาะ Global + Only User)
            target_cat = session.exec(
                select(Categories).where(
                    Categories.name == clean_cat_name,
                    or_(
                        Categories.user_id.is_(None),  # หมวดหมู่ส่วนกลาง
                        Categories.user_id == current_user_id,  # หรือหมวดหมู่ Custom ของผู้ใช้คนนี้
                    ),
                )
            ).first()
            print(f"Matching category for '{raw_cat_name}': {target_cat.name if target_cat else 'Not Found'}")
            # 3. ถ้า AI ดื้อหรือหลุดพิมพ์หมวดหมู่นอกเหนือจากที่สั่ง ให้หลุดเข้า "อื่นๆ" ของระบบ
            if not target_cat:
                target_cat = default_parent

            # หา Parent ID เพื่อใช้ตัดงบ (กรณีในอนาคตมี Sub-category)
            parent_id = target_cat.parent_id if target_cat.parent_id else target_cat.id

            # 4. บันทึก Transaction
            amount = float(item.get("amount", 0))
            # LLM ส่ง type เป็น "expense" / "tax" มา — มีแค่หน้า web ที่ส่ง "income" ได้
            tx_type = "income" if item.get("type") == "income" else "expense"
            tx_date = _resolve_transaction_date(item.get("date"), now)
            new_tx = Transactions(
                user_id=current_user_id,
                amount=amount,
                item_name=item.get("item") or item.get("receiver") or item.get("note") or "ไม่ระบุรายการ",
                transaction_type=tx_type,
                category_id=target_cat.id,
                transaction_date=tx_date,
                source_type=item.get("source_type", "text"),
                is_confirmed=not skip_confirm,
                attachment_id=attachment_id
                if attachment_id
                else (temp.attachment_id if temp else None),
                undo_token=batch_undo_token,
            )
            session.add(new_tx)

            # 5. อัปเดต UserBudget (ตัดงบที่ Parent ของเดือนที่รายการเกิดจริง) — รายรับไม่ตัดงบ
            budget = None
            if tx_type == "expense":
                statement_b = select(UserBudget).where(
                    UserBudget.user_id == current_user_id,
                    UserBudget.category_id == parent_id,
                    UserBudget.month == tx_date.month,
                    UserBudget.year == tx_date.year,
                )
                budget = session.exec(statement_b).first()
                print(f"Budget before update: {budget}")
            if budget:
                budget.current_spent += amount
                session.add(budget)
                processed_parent_ids.add(budget.id)

            total_amount += amount
            item_count += 1

        # ลบ Temp และ Commit
        if temp is not None:
            session.delete(temp)
        session.commit()

        # 6. ดึงข้อมูล Budget ที่อัปเดตแล้วส่งกลับไปแสดงผลบน LINE Flex Message
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
            "current_transaction_id": new_tx.id if new_tx else None,
            "undo_token": batch_undo_token,
            "count": item_count,
            "total": total_amount,
            "budgets": updated_budgets_info,
            # False = ผลรวมไม่ตรงกับ grand_total ที่อ่านได้จากสลิป ควรให้ผู้ใช้ตรวจสอบ
            "total_matched": total_matched,
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
        grand_total: float = None,
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
                    grand_total=grand_total,
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
    def get_user_temp_transaction(
        session: Session, temp_id: str, user_id: str
    ) -> TempTransactions | None:
        """คืน temp ที่ยังไม่หมดอายุและเป็นของ `user_id` เท่านั้น ไม่งั้นคืน None

        ไม่แยกกรณี "ไม่มี" กับ "เป็นของคนอื่น" เพื่อไม่ให้เดา temp_id ของคนอื่นได้
        """
        temp = session.get(TempTransactions, temp_id)
        if not temp or temp.user_id != user_id:
            return None
        if temp.expires_at and temp.expires_at < datetime.utcnow():
            return None
        return temp

    # ---------------------------------------------------------------- web app: ประวัติ/แก้/ลบ/export
    @staticmethod
    def _adjust_budget(session: Session, tx: Transactions, sign: int) -> None:
        """ปรับ `current_spent` ตามรายการนี้: sign=+1 ตัดงบ, -1 คืนงบ (ไม่ต่ำกว่า 0)

        ตัดที่หมวดแม่ของเดือนที่รายการเกิดจริง เหมือนตอนบันทึก — รายรับ/ไม่มีหมวด ไม่แตะงบ
        """
        if tx.transaction_type != "expense" or not tx.category_id:
            return
        category = session.get(Categories, tx.category_id)
        if not category:
            return
        budget = session.exec(
            select(UserBudget).where(
                UserBudget.user_id == tx.user_id,
                UserBudget.category_id == (category.parent_id or category.id),
                UserBudget.month == tx.transaction_date.month,
                UserBudget.year == tx.transaction_date.year,
            )
        ).first()
        if budget:
            budget.current_spent = max(0.0, budget.current_spent + sign * tx.amount)
            session.add(budget)

    @staticmethod
    def _transaction_view(tx: Transactions, category: Optional[Categories]) -> Dict[str, Any]:
        return {
            "id": tx.id,
            "item_name": tx.item_name,
            "amount": tx.amount,
            "transaction_type": tx.transaction_type,
            "transaction_date": tx.transaction_date.isoformat(),
            "source_type": tx.source_type,
            "category_id": tx.category_id,
            "category_name": category.name if category else "ไม่มีหมวดหมู่",
            "category_icon": category.icon if category and category.icon else "🏷️",
        }

    @staticmethod
    def get_user_transactions(
        session: Session,
        user_id: str,
        month: int,
        year: int,
        category_id: Optional[int] = None,
        limit: Optional[int] = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """ประวัติรายการของผู้ใช้ในเดือนหนึ่ง (ใหม่สุดก่อน) + จำนวนทั้งหมด + ยอดรับ/จ่ายของทั้งเดือน

        ใช้ outer join เพื่อไม่ให้รายการที่ไม่มีหมวดหายไป และกรองหมวดแม่แล้วรวมหมวดลูกด้วย
        """
        month_start = datetime(year, month, 1)
        next_month = datetime(year + month // 12, month % 12 + 1, 1)
        filters = [
            Transactions.user_id == user_id,
            Transactions.transaction_date >= month_start,
            Transactions.transaction_date < next_month,
        ]
        if category_id is not None:
            filters.append(
                or_(Transactions.category_id == category_id, Categories.parent_id == category_id)
            )

        def base(*columns):
            return (
                select(*columns)
                .select_from(Transactions)
                .join(Categories, Transactions.category_id == Categories.id, isouter=True)
                .where(*filters)
            )

        total = session.exec(base(func.count(Transactions.id))).one()
        totals = {"income": 0.0, "expense": 0.0}
        for tx_type, amount in session.exec(
            base(Transactions.transaction_type, func.sum(Transactions.amount)).group_by(
                Transactions.transaction_type
            )
        ).all():
            totals["income" if tx_type == "income" else "expense"] += float(amount or 0)

        statement = base(Transactions, Categories).order_by(
            Transactions.transaction_date.desc(), Transactions.id
        )
        if limit is not None:
            statement = statement.limit(limit).offset(offset)
        items = [
            DBManagerTransactions._transaction_view(tx, cat)
            for tx, cat in session.exec(statement).all()
        ]
        return {"items": items, "total": total, "totals": totals}

    @staticmethod
    def update_user_transaction(
        session: Session, user_id: str, transaction_id: str, changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """แก้รายการของผู้ใช้ (`amount`, `item_name`, `category_id`, `type`, `date`) แล้วย้ายยอดงบตาม"""
        tx = session.get(Transactions, transaction_id)
        if not tx or tx.user_id != user_id:
            return {"success": False, "message": "ไม่พบรายการนี้"}

        amount = tx.amount
        if "amount" in changes:
            try:
                amount = float(changes["amount"])
            except (TypeError, ValueError):
                amount = 0.0
            if amount <= 0:
                return {"success": False, "message": "จำนวนเงินต้องมากกว่า 0"}

        category_id = changes.get("category_id", tx.category_id)
        if category_id is not None and not DBManagerCategories.can_use_category(
            session, category_id, user_id
        ):
            return {"success": False, "message": "ไม่สามารถใช้หมวดหมู่นี้ได้"}

        tx_type = changes.get("type", tx.transaction_type)
        if tx_type not in ("income", "expense"):
            return {"success": False, "message": "ประเภทรายการไม่ถูกต้อง"}

        item_name = str(changes.get("item_name", tx.item_name) or "").strip()
        if not item_name:
            return {"success": False, "message": "กรุณาระบุชื่อรายการ"}

        # คืนงบตามค่าเดิมก่อน แล้วค่อยตัดตามค่าใหม่ — ครอบคลุมทั้งเปลี่ยนจำนวน/หมวด/ชนิด/เดือน
        DBManagerTransactions._adjust_budget(session, tx, -1)
        tx.amount = amount
        tx.category_id = category_id
        tx.transaction_type = tx_type
        tx.item_name = item_name
        if changes.get("date"):
            new_date = _resolve_transaction_date(changes["date"], datetime.now())
            # หน้าเว็บส่งวันที่มาทุกครั้ง — ถ้าวันเดิม คงเวลาเดิมไว้ ไม่ให้แก้ชื่อแล้วลำดับรายการเปลี่ยน
            if new_date.date() != tx.transaction_date.date():
                tx.transaction_date = new_date
        DBManagerTransactions._adjust_budget(session, tx, +1)
        session.add(tx)
        session.commit()
        session.refresh(tx)
        category = session.get(Categories, tx.category_id) if tx.category_id else None
        return {"success": True, "data": DBManagerTransactions._transaction_view(tx, category)}

    @staticmethod
    def delete_user_transaction(
        session: Session, user_id: str, transaction_id: str
    ) -> Dict[str, Any]:
        """ลบรายการของผู้ใช้หนึ่งรายการ และคืนยอดงบที่เคยตัดไป"""
        tx = session.get(Transactions, transaction_id)
        if not tx or tx.user_id != user_id:
            return {"success": False, "message": "ไม่พบรายการนี้"}
        DBManagerTransactions._adjust_budget(session, tx, -1)
        session.delete(tx)
        session.commit()
        return {"success": True, "message": "ลบรายการแล้ว"}

    @staticmethod
    def export_user_transactions_csv(
        session: Session, user_id: str, month: int, year: int, category_id: Optional[int] = None
    ) -> str:
        """CSV ของเดือน (ตามหมวดที่กรอง) — ขึ้นต้นด้วย BOM ให้ Excel เปิดภาษาไทยได้ถูกต้อง"""

        def cell(value: str) -> str:
            # ข้อความที่ขึ้นต้นด้วย = + - @ จะถูก Excel ตีความเป็นสูตร (ชื่อรายการมาจากผู้ใช้/OCR)
            return f"'{value}" if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value

        page = DBManagerTransactions.get_user_transactions(
            session, user_id, month, year, category_id=category_id, limit=None
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["วันที่", "รายการ", "หมวดหมู่", "ประเภท", "จำนวนเงิน"])
        for item in reversed(page["items"]):  # เก่าไปใหม่ อ่านเป็นสมุดบัญชีได้
            writer.writerow(
                [
                    item["transaction_date"][:16].replace("T", " "),
                    cell(item["item_name"]),
                    cell(item["category_name"]),
                    "รายรับ" if item["transaction_type"] == "income" else "รายจ่าย",
                    f"{item['amount']:.2f}",
                ]
            )
        return "\ufeff" + buffer.getvalue()

    @staticmethod
    def get_transaction_by_id(session: Session, transaction_id: str):
        try:
            statement = select(Transactions).where(Transactions.id == transaction_id)
            return session.exec(statement).first()
        except Exception as e:
            print(f"Error in get_transaction_by_id: {str(e)}")
            return None
