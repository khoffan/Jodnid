"""
ชั้นจัดการฐานข้อมูลของ JodNid แยกเป็นไฟล์ละหนึ่งความรับผิดชอบ

ใช้ `from model.db import DBManagerXxx` ได้เลย ไม่ต้องอ้างชื่อไฟล์ย่อย
เวลาเพิ่ม manager ใหม่ ให้สร้างไฟล์ใหม่ในโฟลเดอร์นี้แล้วมา re-export ตรงนี้ด้วย
"""

from model.db.admin import DBManagerAdmin
from model.db.billable import BILLABLE_TOTAL_TOLERANCE, select_billable_items
from model.db.budget import DBManagerBudget
from model.db.categories import DBManagerCategories
from model.db.dashboard import DBManagerDashboard
from model.db.transactions import DBManagerTransactions
from model.db.users import DBManagerUsers

__all__ = [
    "BILLABLE_TOTAL_TOLERANCE",
    "DBManagerAdmin",
    "DBManagerBudget",
    "DBManagerCategories",
    "DBManagerDashboard",
    "DBManagerTransactions",
    "DBManagerUsers",
    "select_billable_items",
]
