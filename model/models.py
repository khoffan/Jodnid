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

    transactions: List["Transactions"] = Relationship(back_populates="category")

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
    amount: float
    month: int
    year: int

# --- Database Connection ---
raw_url_db = os.getenv("DATABASE_URL")
engine = create_engine(raw_url_db)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    print("Database structure updated with Attachments table.")

# --- Session Generator (สำหรับ FastAPI Dependency) ---
def get_session():
    """สร้าง Database Session และปิดให้อัตโนมัติเมื่อทำงานเสร็จ"""
    with Session(engine) as session:
        yield session