from sqlmodel import Session, extract, select
from model.models import engine, Users, Transactions, TempTransactions, Categories, Attachments
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
def confirm_and_save_transaction(temp_id: str, category_name: str):
    with Session(engine) as session:
        temp = session.get(TempTransactions, temp_id)
        if not temp:
            return False
        
        statement = select(Categories).where(Categories.name == category_name)
        category = session.exec(statement).first()
        
        # ถ้ายังไม่มี ให้สร้างใหม่
        if not category:
            category = Categories(
                name=category_name,
                icon="✨", # ใส่ icon default ไว้ก่อน หรือจะ map ตามชื่อก็ได้
                color_code="#808080" # สีเทา default
            )
            session.add(category)
            session.flush() # เพื่อให้ได้ category.id มาใช้ต่อโดยยังไม่ commit ทั้งหมด
        
        # วนลูปบันทึกรายการ (รองรับกรณี 1 รูปมีหลายรายการ)
        for item in temp.raw_data:
            new_tx = Transactions(
                user_id=temp.user_id,
                amount=float(item.get('amount', 0)),
                item_name=item.get('item') or item.get('receiver') or "ไม่ระบุรายการ",
                transaction_type="expense", 
                receiver_name=item.get('receiver'),
                # ดึงข้อมูลจาก Temp มาใส่ใน Transaction จริง
                source_type=temp.source_type,
                attachment_id=temp.attachment_id,
                category_id=category.id
            )
            session.add(new_tx)
        
        # ลบ Temp หลังจากย้ายเสร็จ (Clean up)
        session.delete(temp)
        session.commit()
        return True
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
    
def get_dashboard_data(user_id: str, month: int = None, year: int = None):
    with Session(engine) as session:
        # กำหนดช่วงเวลา (Default เดือนปัจจุบัน)
        now = datetime.now()
        target_month = month or now.month
        target_year = year or now.year
        
        # 1. ดึงข้อมูล Transactions พร้อมหมวดหมู่
        statement = select(Transactions, Categories).join(Categories, isouter=True).where(
            Transactions.user_id == user_id,
            extract('month', Transactions.transaction_date) == target_month,
            extract('year', Transactions.transaction_date) == target_year
        )
        results = session.exec(statement).all()
        
        # 2. คำนวณยอดรวมแยกตามหมวดหมู่ (สำหรับกราฟ)
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
                    "date": tx.transaction_date.strftime("%d/%m/%Y"),
                    "icon": cat.icon if cat else "✨"
                } for tx, cat in results[:10] # ส่งไปแค่ 10 รายการล่าสุด
            ]
        }