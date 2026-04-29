import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from sqlmodel import Field, Relationship, SQLModel, create_engine, Session, Column, JSON
from dotenv import load_dotenv

load_dotenv()

# --- 1. ตาราง Users ---
class Users(SQLModel, table=True):
    line_user_id: str = Field(primary_key=True, index=True)
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    transactions: List["Transactions"] = Relationship(back_populates="user")
    temp_transactions: List["TempTransactions"] = Relationship(back_populates="user")
    attachments: List["Attachments"] = Relationship(back_populates="user")

# --- 2. ตาราง Attachments (เก็บข้อมูลไฟล์แยกต่างหาก) ---
class Attachments(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    file_path: str  # เก็บ path เช่น uploads/user_id/date/msg_id.jpg
    file_type: str = Field(default="image/jpeg") # image/png, image/jpeg
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign Key
    user_id: str = Field(foreign_key="users.line_user_id")
    
    # Relationships
    user: Users = Relationship(back_populates="attachments")
    # เชื่อมกลับไปหา Transaction (ถ้ามี)
    transaction: Optional["Transactions"] = Relationship(back_populates="attachment")
    temp_transaction: Optional["TempTransactions"] = Relationship(back_populates="attachment")

# --- 3. ตาราง Categories ---
class Categories(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    icon: Optional[str] = None 
    color_code: Optional[str] = None 
    
    # --- เพิ่มส่วน Parent-Child ---
    # parent_id เป็น Nullable เพราะหมวดหมู่หลัก (Parent) จะไม่มีพ่อ
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    
    # ความสัมพันธ์ชี้กลับมาที่ตัวเอง
    parent: Optional["Categories"] = Relationship(
        back_populates="children", 
        sa_relationship_kwargs={"remote_side": "Categories.id"}
    )
    children: List["Categories"] = Relationship(back_populates="parent")

    # ความสัมพันธ์กับ Transaction (เหมือนเดิม)
    transactions: List["Transactions"] = Relationship(back_populates="category")
    
    # ความสัมพันธ์กับ UserBudget (สำหรับ Parent Category เท่านั้น)
    budgets: List["UserBudget"] = Relationship(back_populates="category")

# --- 4. ตาราง Transactions (กดยืนยันแล้ว) ---
class Transactions(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    amount: float
    item_name: str
    receiver_name: Optional[str] = None
    transaction_type: str = Field(default="expense")
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    
    # เพิ่ม Field ใหม่
    source_type: str = Field(default="text") # 'text' หรือ 'image'
    
    # Foreign Keys
    user_id: str = Field(foreign_key="users.line_user_id")
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    attachment_id: Optional[str] = Field(default=None, foreign_key="attachments.id") # เชื่อมไปตารางรูป

    # Relationships
    user: Users = Relationship(back_populates="transactions")
    category: Optional[Categories] = Relationship(back_populates="transactions")
    attachment: Optional[Attachments] = Relationship(back_populates="transaction")

# --- 5. ตาราง TempTransactions (รอ Confirm) ---
class TempTransactions(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.line_user_id")
    
    # เก็บข้อมูลจาก AI
    raw_data: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    # เพิ่ม Field ใหม่เหมือนตารางจริง
    source_type: str = Field(default="text")
    attachment_id: Optional[str] = Field(default=None, foreign_key="attachments.id")
    
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )

    # Relationships
    user: Users = Relationship(back_populates="temp_transactions")
    attachment: Optional[Attachments] = Relationship(back_populates="temp_transaction")

class UserBudget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    
    # เชื่อมโยงกับ Category (ใช้เฉพาะ Parent Category)
    category_id: int = Field(foreign_key="categories.id")
    
    amount: float            # งบประมาณที่ตั้งไว้ (Limit)
    current_spent: float = Field(default=0.0) # ยอดที่ใช้ไปแล้วในเดือนนั้น
    
    month: int
    year: int

    # Relationship เพื่อให้ดึงชื่อ Category มาโชว์ในแอปได้ง่ายๆ
    category: Optional["Categories"] = Relationship(back_populates="budgets")

class CategoryMapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alias_name: str = Field(index=True, unique=True) # คำที่ AI ส่งมา เช่น "อาหารและเครื่องดื่ม"
    category_id: int = Field(foreign_key="categories.id") # ชี้ไปยังหมวดหมู่จริงใน DB
    
    # ความสัมพันธ์
    category: Optional["Categories"] = Relationship()

class SystemConfiguration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    key: str = Field(index=True, unique=True)
    value: str
    value_type: str 
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SystemLog(SQLModel, table=True):
    # ข้อมูลพื้นฐาน
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    level: str = Field(index=True)  # INFO, WARNING, ERROR, CRITICAL
    
    # ระบุจุดที่เกิด
    module: str = Field(index=True) # เช่น 'OCR_PROCESSOR', 'LINE_BOT_WEBHOOK'
    message: str # ข้อความอธิบายสั้นๆ
    
    # ข้อมูลเชิงลึกสำหรับ Debug
    user_id: Optional[str] = Field(default=None, index=True)
    payload: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON)) # เก็บ JSON Data ต้นทาง
    stack_trace: Optional[str] = Field(default=None) # เก็บ Traceback ยาวๆ เมื่อพัง
    
    # บริบทอื่นๆ
    environment: str = Field(default="production") # dev / prod
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Administrator(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    uid: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    profile: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    role: str = Field(default="admin")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# --- Database Connection ---
raw_url_db = os.getenv("DATABASE_URL")
engine = create_engine(raw_url_db)

def create_db_and_tables():
    print("Tables detected:", SQLModel.metadata.tables.keys())
    SQLModel.metadata.create_all(engine)
    print("Database structure updated with Attachments table.")

# --- Session Generator (สำหรับ FastAPI Dependency) ---
def get_session():
    """สร้าง Database Session และปิดให้อัตโนมัติเมื่อทำงานเสร็จ"""
    with Session(engine) as session:
        yield session