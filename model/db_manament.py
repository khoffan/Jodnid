from model.models import CategoryMapping
from sqlalchemy import and_
from sqlmodel import Session, extract, select
from helper.utils import get_line_profile
from model.models import UserBudget, engine, Users, Transactions, TempTransactions, Categories, Attachments
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# --- 1. จัดการ User (เหมือนเดิมแต่เพิ่ม Error Handling) ---
def get_or_create_user(line_user_id: str, line_access_token: str = None):
    profile = get_line_profile(user_id=line_user_id, line_token=line_access_token)
    display_name = profile["displayName"] if profile else "Unknown User"
    
    with Session(engine) as session:
        user = session.get(Users, line_user_id)
        
        if not user:
            # กรณี User ใหม่: สร้าง Record ใหม่
            user = Users(line_user_id=line_user_id, display_name=display_name)
            session.add(user)
        else:
            # กรณี User เก่า: เช็คว่าต้องอัปเดตชื่อไหม (ป้องกันค่า null หรือชื่อเก่า)
            if user.display_name != display_name:
                user.display_name = display_name
                # หากมีฟิลด์รูปโปรไฟล์ (pictureUrl) ก็อัปเดตตรงนี้ได้เลย
        
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

def delete_temp_transaction(temp_id: str):
    with Session(engine) as session:
        temp = session.get(TempTransactions, temp_id)
        if temp:
            session.delete(temp)
            session.commit()
            return True
        return False

# --- 3. ย้ายข้อมูลจาก Temp ไปเป็น Transaction จริง (รองรับ Category และ Attachment) ---
def confirm_and_save_transaction(temp_id: str, edit: bool = False, items: List[Dict[str, Any]] = None):
    with Session(engine) as session:
        # 1. ดึงข้อมูลชั่วคราว
        temp = session.get(TempTransactions, temp_id)
        if not temp:
            return False

        # ดึงหมวด "อื่นๆ" ไว้รอเลย เผื่อต้องใช้ (Fallback)
        statement_other = select(Categories).where(Categories.name == "อื่นๆ", Categories.parent_id == None)
        default_parent = session.exec(statement_other).first()
        if not default_parent:
            default_parent = Categories(name="อื่นๆ", icon="✨")
            session.add(default_parent)
            session.flush()

        total_amount = 0.0
        item_count = 0
        updated_budgets_info = [] # เก็บข้อมูล Budget ที่ถูกอัปเดต
        processed_parent_ids = set() # ป้องกันการดึง Budget ซ้ำถ้ามีหลายรายการใน Parent เดียวกัน
        now = datetime.now()
        
        if edit:
            raw_data = items
        else:
            raw_data = temp.raw_data

        for item in raw_data:
            raw_cat_name = str(item.get('category', 'อื่นๆ')).strip()
            
            # 2. ค้นหาใน Mapping Table ก่อน
            # 1. ค้นหาใน Mapping Table (เช่น AI ส่ง "อาหาร" มา -> เจอ "อาหารและเครื่องดื่ม")
            mapping = session.exec(
                select(CategoryMapping).where(CategoryMapping.alias_name == raw_cat_name)
            ).first()

            if mapping:
                target_cat = mapping.category
            else:
                # 2. ถ้าไม่มีใน Mapping ลองหาใน Categories ตรงๆ
                target_cat = session.exec(
                    select(Categories).where(Categories.name == raw_cat_name)
                ).first()
                
                # 3. ถ้ายังไม่เจออีก ลงหมวด "อื่นๆ"
                if not target_cat:
                    # สร้างหมวดหมู่ย่อยใหม่เพื่อเก็บ Stat ในอนาคต
                    target_cat = Categories(
                        name=raw_cat_name, 
                        icon="📝", 
                        parent_id=default_parent.id # ผูกไว้กับ "อื่นๆ" ก่อนในเบื้องต้น
                    )
                    session.add(target_cat)
                    session.flush() 
                    
                    # เพิ่มเข้า Mapping Table อัตโนมัติ เพื่อให้ครั้งหน้าไม่ต้องสร้างซ้ำ
                    new_mapping = CategoryMapping(alias_name=raw_cat_name, category_id=target_cat.id)
                    session.add(new_mapping)
            print(f"target cat {target_cat}")
            # 5. หา Parent ID เพื่อไปตัด Budget
            # (ถ้า target_cat มี parent_id ให้ใช้ parent_id, ถ้าไม่มีแสดงว่าเป็น Parent เองอยู่แล้ว)
            parent_id = target_cat.parent_id if target_cat.parent_id else target_cat.id

            # 2. บันทึก Transaction
            amount = float(item.get('amount', 0))
            new_tx = Transactions(
                user_id=temp.user_id,
                amount=amount,
                item_name=item.get('item') or item.get('receiver') or "ไม่ระบุรายการ",
                transaction_type="expense", 
                category_id=target_cat.id,
                transaction_date=now
            )
            session.add(new_tx)

            # 3. อัปเดต UserBudget (ตัดงบที่ Parent)
            statement_b = select(UserBudget).where(
                UserBudget.user_id == temp.user_id,
                UserBudget.category_id == parent_id,
                UserBudget.month == now.month,
                UserBudget.year == now.year
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
        session.delete(temp)
        session.commit()

        # 5. ดึงข้อมูล Budget ที่อัปเดตแล้วมาเตรียมส่งกลับ (ต้องดึงใหม่หลัง commit เพื่อความชัวร์)
        for b_id in processed_parent_ids:
            b = session.get(UserBudget, b_id)
            if b:
                updated_budgets_info.append({
                    "category_name": b.category.name,
                    "amount": b.amount,
                    "current_spent": b.current_spent,
                    "icon": b.category.icon
                })
        
        return {
            "count": item_count, 
            "total": total_amount,
            "budgets": updated_budgets_info # ส่งข้อมูลสรุปงบกลับไป
        }
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
    
def get_temp_transaction_data(temp_id):
    with Session(engine) as session:
        statement = select(TempTransactions).where(TempTransactions.id == temp_id)
        return session.exec(statement).first()

# --- 5. จัดการ Category (เพื่อความง่ายในการเรียกใช้) ---
def get_all_categories():
    with Session(engine) as session:
        statement = select(Categories)
        return session.exec(statement).all()

def get_category_by_name(name: str):
    with Session(engine) as session:
        statement = select(Categories).where(Categories.name == name)
        return session.exec(statement).first()
    
def get_dashboard_data(user_id: str, type: str = "monthly",day: int = None, month: int = None, year: int = None):
    with Session(engine) as session:
        now = datetime.now()
        

        target_month = int(month) if month else now.month
        target_year = int(year) if year else now.year
        target_day = int(day) if day else now.day
        # สร้างเงื่อนไขพื้นฐาน (Filter by User)
        filters = [Transactions.user_id == user_id]
        
        if type == "daily":
            # --- Logic สำหรับรายวัน ---
            # กรองเฉพาะ วัน/เดือน/ปี ปัจจุบัน
            filters.append(extract('day', Transactions.transaction_date) == target_day)
            filters.append(extract('month', Transactions.transaction_date) == target_month)
            filters.append(extract('year', Transactions.transaction_date) == target_year)
        else:
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

def setup_user_budget(user_id: str, category_id: int, amount: float):
    with Session(engine) as session:
        now = datetime.now()
        
        # 1. ตรวจสอบก่อนว่า category_id ที่ส่งมาคือ Parent Category จริงหรือไม่ (กันพลาด)
        category = session.get(Categories, category_id)
        print(f"category {category}")
        if not category or category.parent_id is not None:
            return {
                "success": False, 
                "message": "กรุณาเลือกหมวดหมู่หลัก (Parent Category) ในการตั้งงบประมาณ"
            }

        # 2. ค้นหาว่าในเดือน/ปี และหมวดหมู่นี้ User เคยตั้งงบไว้หรือยัง
        statement = select(UserBudget).where(
            UserBudget.user_id == user_id,
            UserBudget.category_id == category_id,
            UserBudget.month == now.month,
            UserBudget.year == now.year
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
                year=now.year
            )
            session.add(budget)
            
        session.commit()
        return {
            "success": True, 
            "message": f"ตั้งงบประมาณหมวด {category.name} เรียบร้อยแล้วครับ"
        }
        
def get_parent_categories() -> List[Categories]:
    """
    ดึงข้อมูลหมวดหมู่หลัก (Parent Categories) ทั้งหมดในระบบ
    เพื่อนำไปแสดงผลในหน้าตั้งค่า Budget หรือใช้จัดกลุ่มรายงาน
    """
    with Session(engine) as session:
        # เลือกเฉพาะรายการที่ไม่มี parent_id (เป็นรากของหมวดหมู่)
        statement = select(Categories).where(Categories.parent_id == None)
        results = session.exec(statement).all()
        
        return results