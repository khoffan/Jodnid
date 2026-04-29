from helper.utils import get_all_users, get_line_profile, get_user_overview
from fastapi import APIRouter, Depends
from sqlmodel import Session
from model.db_manament import (
    get_parent_categories,
    get_temp_transaction_data,
    get_temp_transaction_data,
    get_dashboard_data,
    setup_user_budget,
)

from helper.webhook_helper import (
    confirme_data_from_edit
)
from helper.logger import JodNidLogger
from model.models import get_session

class LiffApi:
    def __init__(self, logger: JodNidLogger, line_access_token: str):
        self.logger = logger
        self.line_access_token = line_access_token
        self.router = APIRouter(
            prefix="/api",
            tags=["LIFF-v1"]
        )
    def setup_router(self):
        router = self.router
        logger = self.logger
        users = get_all_users(next(get_session()))
        user_id = None
        for user in users:
            profile = get_line_profile(user_id=user.line_user_id, line_token=self.line_access_token)
            user_id=profile.get("userId")
    
        @router.get("/dashboard/{user_id}")
        async def get_dashboard(user_id: str, type: str = "monthly",day: int = None, month: int = None, year: int = None):
            logger.info(module="dashboard", message=f"User ID: {user_id}, Type: {type}, Month: {month}, Year: {year}", user_id=user_id)
            # ส่ง type เข้าไปในฟังก์ชันจัดการข้อมูล
            return get_dashboard_data(user_id, type, day, month, year)
        
        @router.post("/overview/stats")
        async def overview_stat(data: dict, db: Session = Depends(get_session)):
            user_id = data.get("user_id")
            if not user_id:
                return {"success": False, "message": "Missing user_id"}
            
            logger.info(module="app", message=f"Overview stats requested for user_id: {user_id}", user_id=user_id)
            data = get_user_overview(db, user_id)
            logger.info(module="app", message=f"Overview stats for user_id: {user_id} retrieved successfully", user_id=user_id)
            return {
                "success": True,
                "data": data
            }


        @router.get("/temp-transaction/{temp_id}")
        async def get_temp_transaction(temp_id: str):
            data = get_temp_transaction_data(temp_id)
            logger.info(module="transaction_edit", message=f"temp_id: {temp_id}, data: {data}", user_id=user_id)
            return data

        @router.post("/transactions/confirm-bulk")
        async def confirme_transaction_bulk_edit(data: dict):
            user_id = data.get("user_id")
            items = data.get("items")
            temp_id = data.get("temp_id")
            logger.info(module="transaction_confirm_edit", message=f"Confirming bulk transaction for user_id: {user_id} with temp_id: {temp_id}", user_id=user_id)
            confirme_data_from_edit(temp_id, user_id, items, logger)
            return {"success": True, "message": "Confirm bulk transaction"}


        @router.get("/categories/parent")
        async def get_categories_parent():
            logger.info(module="categories", message="Fetching categories parent")
            return get_parent_categories()



        @router.post("/budget/setup")
        async def setup_budget(data: dict):
            user_id = data.get("user_id")
            amount = data.get("amount")
            category_id = data.get("category_id")
            logger.info(module="budget", message=f"Setting up budget for user_id: {user_id} with amount: {amount} and category_id: {category_id}", user_id=user_id)
            if not user_id or not amount or not category_id:
                logger.error(module="budget", message=f"Missing user_id or amount or category_id", user_id=user_id)
                return {"success": False, "message": "Missing user_id or amount or category_id"}
            
            return setup_user_budget(user_id, category_id=category_id, amount=amount)
        