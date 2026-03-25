from sqlmodel import Session, select
from model.models import engine, Users, Transactions, TempTransactions, Categories
from typing import List, Dict, Any

# --- 1. จัดการ User ---
def get_or_create_user(line_user_id: str, display_name: str = None):
    with Session(engine) as session:
        user = session.get(Users, line_user_id)
        if not user:
            user = Users(line_user_id=line_user_id, display_name=display_name)
            session.add(user)
            session.commit()
            session.refresh(user)
            print("New user created successfully.")
        return user

# --- 2. บันทึกข้อมูลชั่วคราว (รอ Confirm) ---
def save_temp_transaction(user_id: str, raw_data: List[Dict[str, Any]]):
    with Session(engine) as session:
        # สร้างรายการ Temp ใหม่
        temp_entry = TempTransactions(user_id=user_id, raw_data=raw_data)
        session.add(temp_entry)
        session.commit()
        session.refresh(temp_entry)
        return temp_entry.id # คืนค่า ID เพื่อเอาไปใส่ใน Postback Data ของ Flex Message

# --- 3. ย้ายข้อมูลจาก Temp ไปเป็น Transaction จริง (เมื่อ User กด Confirm) ---
def confirm_and_save_transaction(temp_id: str):
    with Session(engine) as session:
        # ดึงข้อมูลจากตาราง Temp
        temp = session.get(TempTransactions, temp_id)
        if not temp:
            return False
        
        saved_items = []
        # วนลูปบันทึกรายการที่อยู่ใน raw_data (เพราะ 1 ครั้งอาจมีหลายรายการ)
        for item in temp.raw_data:
            new_tx = Transactions(
                user_id=temp.user_id,
                amount=float(item.get('amount', 0)),
                item_name=item.get('item') or item.get('receiver') or "ไม่ระบุรายการ",
                transaction_type="expense", # หรือดึงจาก AI ถ้าสกัดมาได้
                receiver_name=item.get('receiver')
            )
            session.add(new_tx)
            saved_items.append(new_tx)
        
        # ลบข้อมูลใน Temp ทิ้งหลังจากย้ายเสร็จ
        session.delete(temp)
        session.commit()
        return True