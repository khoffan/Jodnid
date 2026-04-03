from sqlalchemy import and_
from sqlmodel import Session, extract, select
from model.models import UserBudget, engine, Users, Transactions, TempTransactions, Categories, Attachments
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# --- 1. จัดการ User (เหมือนเดิมแต่เพิ่ม Error Handling) ---
def get_or_create_user(line_user_id: str, display_name: str = None):
    with Session(engine) as session:
        user = session.get(Users, line_user_id)
        if not user:
            user = Users(line_user_id=line_user_id, display_name=display_name)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

# --- 2. บันทึกข้อมูลชั่วคราว (เพิ่ม attachment_id และ source_type) ---
def save_temp_transaction(user_id: str, raw_data: List[Dict[str, Any]], 
                          attachment_id: str = None, source_type: str = "text"):
    with Session(engine) as session:
        temp_entry = TempTransactions(
            user_id=user_id, 
            raw_data=raw_data,
            attachment_id=attachment_id,
            source_type=source_type
        )
        session.add(temp_entry)
        session.commit()
        session.refresh(temp_entry)
        return temp_entry.id

# --- 3. ย้ายข้อมูลจาก Temp ไปเป็น Transaction จริง (รองรับ Category และ Attachment) ---
def confirm_and_save_transaction(temp_id: str):
    with Session(engine) as session:
        # 1. ดึงข้อมูลชั่วคราว
        temp = session.get(TempTransactions, temp_id)
        if not temp:
            return False
        
        # Mapping ภาษาไทย/อังกฤษ และ Icon สำหรับหมวดหมู่
        cat_map = {
            "food": {"name": "อาหาร", "icon": "🍔", "color": "#FF5733"},
            "อาหาร": {"name": "อาหาร", "icon": "🍔", "color": "#FF5733"},
            "travel": {"name": "เดินทาง", "icon": "🚗", "color": "#3357FF"},
            "เดินทาง": {"name": "เดินทาง", "icon": "🚗", "color": "#3357FF"},
            "shopping": {"name": "ช้อปปิ้ง", "icon": "🛍️", "color": "#FF33A1"},
            "ช้อปปิ้ง": {"name": "ช้อปปิ้ง", "icon": "🛍️", "color": "#FF33A1"},
            "เครื่องดื่ม": {"name": "เครื่องดื่ม", "icon": "☕", "color": "#6F4E37"}
        }

        total_amount = 0.0
        item_count = 0

        # 2. วนลูปตามรายการที่ AI สกัดมาได้ (รองรับหลายรายการใน 1 temp_id)
        for item in temp.raw_data:
            # ดึงหมวดหมู่จาก item (AI ส่งมา) และทำความสะอาด String
            raw_cat = str(item.get('category', 'other')).strip()
            clean_cat = "".join(raw_cat.split()) # ลบช่องว่างกลางคำ
            
            # หาข้อมูลหมวดหมู่มาตรฐานจาก Map
            cat_info = cat_map.get(clean_cat, {"name": clean_cat, "icon": "✨", "color": "#808080"})
            final_cat_name = cat_info["name"]

            # ตรวจสอบใน DB ว่ามีหมวดหมู่นี้หรือยัง
            statement = select(Categories).where(Categories.name == final_cat_name)
            category = session.exec(statement).first()
            
            if not category:
                category = Categories(
                    name=final_cat_name,
                    icon=cat_info["icon"],
                    color_code=cat_info["color"]
                )
                session.add(category)
                session.flush() # เพื่อให้ได้ ID มาใช้ต่อ

            # 3. สร้าง Transaction จริง
            amount = float(item.get('amount', 0))
            new_tx = Transactions(
                user_id=temp.user_id,
                amount=amount,
                item_name=item.get('item') or item.get('receiver') or "ไม่ระบุรายการ",
                transaction_type="expense", 
                receiver_name=item.get('receiver'),
                source_type=temp.source_type,
                attachment_id=temp.attachment_id,
                category_id=category.id,
                transaction_date=datetime.now() # หรือจะใช้เวลาจาก temp ถ้ามีเก็บไว้
            )
            session.add(new_tx)
            total_amount += amount
            item_count += 1
        
        # 4. ลบ Temp และ Commit
        session.delete(temp)
        session.commit()
        
        # คืนค่ากลับไปบอกผลลัพธ์ (เพื่อเอาไปโชว์ใน Flex Message ตอบกลับ)
        return {"count": item_count, "total": total_amount}
# --- 4. บันทึก Metadata ของรูปภาพ ---
def create_attachment_record(user_id: str, file_path: str, file_type: str = "image/jpeg"):
    """
    สร้าง Record ในตาราง Attachments เพื่อเก็บ Path รูปที่บันทึกลง Disk แล้ว
    """
    with Session(engine) as session:
        new_attachment = Attachments(
            id=str(uuid.uuid4()),
            user_id=user_id,
            file_path=file_path, # ควรเป็น Relative Path
            file_type=file_type
        )
        session.add(new_attachment)
        session.commit()
        session.refresh(new_attachment)
        return new_attachment.id

# --- 5. จัดการ Category (เพื่อความง่ายในการเรียกใช้) ---
def get_all_categories():
    with Session(engine) as session:
        statement = select(Categories)
        return session.exec(statement).all()

def get_category_by_name(name: str):
    with Session(engine) as session:
        statement = select(Categories).where(Categories.name == name)
        return session.exec(statement).first()
    
def get_dashboard_data(user_id: str, type: str = "monthly", month: int = None, year: int = None):
    with Session(engine) as session:
        now = datetime.now()
        
        # สร้างเงื่อนไขพื้นฐาน (Filter by User)
        filters = [Transactions.user_id == user_id]
        
        if type == "daily":
            # --- Logic สำหรับรายวัน ---
            # กรองเฉพาะ วัน/เดือน/ปี ปัจจุบัน
            filters.append(extract('day', Transactions.transaction_date) == now.day)
            filters.append(extract('month', Transactions.transaction_date) == now.month)
            filters.append(extract('year', Transactions.transaction_date) == now.year)
        else:
            # --- Logic สำหรับรายเดือน (Default) ---
            target_month = month or now.month
            target_year = year or now.year
            filters.append(extract('month', Transactions.transaction_date) == target_month)
            filters.append(extract('year', Transactions.transaction_date) == target_year)

        # 1. ดึงข้อมูล Transactions พร้อมหมวดหมู่ (เรียงลำดับใหม่ล่าสุดขึ้นก่อน)
        statement = (
            select(Transactions, Categories)
            .join(Categories, isouter=True)
            .where(and_(*filters))
            .order_by(Transactions.transaction_date.desc()) # เอาล่าสุดขึ้นก่อน
        )
        results = session.exec(statement).all()
        
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
            "transactions": [
                {
                    "item": tx.item_name,
                    "amount": tx.amount,
                    "date": tx.transaction_date.strftime("%H:%M" if type == "daily" else "%d/%m/%Y"), # ถ้ารายวันโชว์เป็นเวลาแทน
                    "icon": cat.icon if cat else "✨",
                    "category": cat.name if cat else "ทั่วไป"
                } for tx, cat in results[:10]
            ]
        }

def setup_user_budget(user_id: str, amount: float):
    with Session(engine) as session:
        now = datetime.now()
        # เช็คว่าเดือนนี้เคยตั้งงบไปหรือยัง ถ้ามีแล้วให้ Update ถ้าไม่มีให้ Create
        statement = select(UserBudget).where(
            UserBudget.user_id == user_id,
            UserBudget.month == now.month,
            UserBudget.year == now.year
        )
        budget = session.exec(statement).first()
        
        if budget:
            budget.amount = amount
        else:
            budget = UserBudget(
                user_id=user_id, 
                amount=amount, 
                month=now.month, 
                year=now.year
            )
            session.add(budget)
            
        session.commit()
        return {"status": "success", "message": "ตั้งค่าบัดเจทเรียบร้อย"}