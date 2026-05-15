from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from core.config_settings import settings
from helper.logger import JodNidLogger
from helper.utils import get_all_users, get_line_profile, get_user_overview
from helper.webhook_helper import confirme_data_from_edit
from middleware.line_auth import (
    exchange_code_for_tokens,
    get_current_user,
    verify_id_token_with_line,
)
from model.db_manament import (
    DBManagerBudget,
    DBManagerCategories,
    DBManagerDashboard,
    DBManagerTransactions,
    DBManagerUsers,
)
from model.models import get_session


class LineLoginRequest(BaseModel):
    code: str | None = None
    id_token: str | None = None


class LineWebTransactionRequest(BaseModel):
    total: float
    items: list[dict]


manager_categories = DBManagerCategories()
manager_transactions = DBManagerTransactions()
manager_user_budget = DBManagerBudget()
manager_dashboard = DBManagerDashboard()
manager_users = DBManagerUsers()


class LiffApi:
    def __init__(self, logger: JodNidLogger, line_access_token: str):
        self.logger = logger
        self.line_access_token = line_access_token
        self.router = APIRouter(prefix="/api", tags=["LIFF-v1"])

    def setup_router(self):
        router = self.router
        logger = self.logger
        users = get_all_users(next(get_session()))
        user_id = None
        for user in users:
            profile = get_line_profile(user_id=user.line_user_id, line_token=self.line_access_token)
            user_id = profile.get("userId")

        @router.post("/user")
        async def update_user_profile(req: LineLoginRequest):
            is_test_mode = settings.TEST_MODE
            if req.code is not None:
                token = await exchange_code_for_tokens(req.code, is_test_mode)
                id_token = token.get("id_token")
            else:
                id_token = req.id_token

            if not id_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID token not found in the response from LINE",
                )
            channel_id = settings.LINE_CHANNEL_ID_TEST if is_test_mode else settings.LINE_CHANNEL_ID
            user_payload = await verify_id_token_with_line(id_token, channel_id)
            print("user_payload: ", user_payload)
            manager_users.get_or_create_user(
                line_user_id=user_payload.get("sub"),
                profile={
                    "display_name": user_payload.get("name"),
                    "email": user_payload.get("email"),
                    "picture_url": user_payload.get("picture"),
                },
            )

            return {
                "success": True,
                "id_token": id_token,  # ส่ง id_token กลับไปให้ React เก็บไว้
                "user_info": {
                    "user_id": user_payload.get("sub"),
                    "name": user_payload.get("name"),
                    "picture": user_payload.get("picture"),
                },
            }

        @router.post("/web/transaction/add")
        async def add_transaction(
            req: LineWebTransactionRequest, user: dict = Depends(get_current_user)
        ):
            print("user: ", user.get("sub"))
            print("req: ", req)
            user_id = user.get("sub")
            logger.info(
                module="transaction_add",
                message=f"Adding transaction for user_id: {user_id}",
                user_id=user_id,
            )
            manager_transactions.confirm_and_save_transaction(
                temp_id=None, user_id=user_id, edit=False, items=req.items
            )
            return HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail={"success": True, "message": "Transaction added"},
            )

        @router.get("/web/transactions")
        async def get_transaction_web(user: dict = Depends(get_current_user)):
            data = manager_transactions.get_Transactions()
            return {"success": True, "data": data}

        @router.get("/dashboard/{user_id}")
        async def get_dashboard(
            user_id: str,
            type: str = "monthly",
            day: int = None,
            month: int = None,
            year: int = None,
        ):
            logger.info(
                module="dashboard",
                message=f"User ID: {user_id}, Type: {type}, Month: {month}, Year: {year}",
                user_id=user_id,
            )
            # ส่ง type เข้าไปในฟังก์ชันจัดการข้อมูล
            return manager_dashboard.get_dashboard_data(user_id, type, day, month, year)

        @router.post("/overview/stats")
        async def overview_stat(data: dict, db: Session = Depends(get_session)):
            user_id = data.get("user_id")
            if not user_id:
                return {"success": False, "message": "Missing user_id"}

            logger.info(
                module="app",
                message=f"Overview stats requested for user_id: {user_id}",
                user_id=user_id,
            )
            data = get_user_overview(db, user_id)
            logger.info(
                module="app",
                message=f"Overview stats for user_id: {user_id} retrieved successfully",
                user_id=user_id,
            )
            return {"success": True, "data": data}

        @router.get("/temp-transaction/{temp_id}")
        async def get_temp_transaction(temp_id: str):
            data = manager_transactions.get_temp_transaction_data(temp_id)
            logger.info(
                module="transaction_edit",
                message=f"temp_id: {temp_id}, data: {data}",
                user_id=user_id,
            )
            return data

        @router.post("/transactions/confirm-bulk")
        async def confirme_transaction_bulk_edit(data: dict):
            user_id = data.get("user_id")
            items = data.get("items")
            temp_id = data.get("temp_id")
            logger.info(
                module="transaction_confirm_edit",
                message=f"Confirming bulk transaction for user_id: {user_id} with temp_id: {temp_id}",
                user_id=user_id,
            )
            confirme_data_from_edit(temp_id, user_id, items, logger)
            return {"success": True, "message": "Confirm bulk transaction"}

        @router.get("/categories/parent")
        async def get_categories_parent():
            logger.info(module="categories", message="Fetching categories parent")
            return manager_categories.get_parent_categories()

        @router.post("/budget/setup")
        async def setup_budget(data: dict):
            user_id = data.get("user_id")
            amount = data.get("amount")
            category_id = data.get("category_id")
            logger.info(
                module="budget",
                message=f"Setting up budget for user_id: {user_id} with amount: {amount} and category_id: {category_id}",
                user_id=user_id,
            )
            if not user_id or not amount or not category_id:
                logger.error(
                    module="budget",
                    message="Missing user_id or amount or category_id",
                    user_id=user_id,
                )
                return {"success": False, "message": "Missing user_id or amount or category_id"}

            return manager_user_budget.setup_user_budget(
                user_id, category_id=category_id, amount=amount
            )
