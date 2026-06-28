from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from core.config_settings import settings
from helper.logger import JodNidLogger
from helper.utils import Utilities
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

class CategoryCreateRequest(BaseModel):
    user_id: str | None = None
    icon: str | None = None
    name: str
    parent_id: int | None = None


# Use DBManager classes directly and pass `db: Session` from route dependencies


class LiffApi:
    def __init__(self, logger: JodNidLogger, line_access_token: str):
        self.logger = logger
        self.line_access_token = line_access_token
        self.router = APIRouter(prefix="/api", tags=["LIFF-v1"])

    def setup_router(self):
        router = self.router
        logger = self.logger
        users = Utilities.get_all_users(next(get_session()))
        user_id = None
        for user in users:
            user_id = user.line_user_id

        @router.post("/user")
        async def update_user_profile(req: LineLoginRequest, db: Session = Depends(get_session)):
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
            DBManagerUsers.get_or_create_user(
                db,
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

        @router.post("/user/onboarded")
        async def set_user_onboarded(
            user: dict = Depends(get_current_user),
            db: Session = Depends(get_session),
        ):
            user_id = user.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user token",
                )

            updated = DBManagerUsers.set_user_onboarded(db, line_user_id=user_id)
            if not updated:
                return {"success": False, "message": "ไม่สามารถอัปเดตสถานะ onboarding ได้"}

            return {"success": True, "message": "อัปเดตสถานะ onboarding เรียบร้อยแล้ว"}

        @router.get("/user/onboarding-status")
        async def get_user_onboarding_status(
            user: dict = Depends(get_current_user),
            db: Session = Depends(get_session),
        ):
            user_id = user.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user token",
                )

            return DBManagerUsers.get_user_onboarding_status(db, line_user_id=user_id)

        @router.post("/web/transaction/add")
        async def add_transaction(
            req: LineWebTransactionRequest,
            user: dict = Depends(get_current_user),
            db: Session = Depends(get_session),
        ):
            user_id = user.get("sub")
            logger.info(
                module="transaction_add",
                message=f"Adding transaction for user_id: {user_id}",
                user_id=user_id,
            )
            DBManagerTransactions.confirm_and_save_transaction(
                db, temp_id=None, user_id=user_id, edit=False, items=req.items
            )
            return HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail={"success": True, "message": "Transaction added"},
            )

        @router.get("/web/transactions")
        async def get_transaction_web(
            user: dict = Depends(get_current_user), db: Session = Depends(get_session)
        ):
            data = DBManagerTransactions.get_Transactions(db)
            return {"success": True, "data": data}

        @router.get("/dashboard/{user_id}")
        async def get_dashboard(
            user_id: str,
            type: str = "monthly",
            day: int = None,
            month: int = None,
            year: int = None,
            db: Session = Depends(get_session),
        ):
            logger.info(
                module="dashboard",
                message=f"User ID: {user_id}, Type: {type}, Month: {month}, Year: {year}",
                user_id=user_id,
            )
            # ส่ง type เข้าไปในฟังก์ชันจัดการข้อมูล
            return DBManagerDashboard.get_dashboard_data(
                db, user_id, type=type, day=day, month=month, year=year
            )

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
            data = Utilities.get_user_overview(db, user_id)
            logger.info(
                module="app",
                message=f"Overview stats for user_id: {user_id} retrieved successfully",
                user_id=user_id,
            )
            return {"success": True, "data": data}

        @router.get("/temp-transaction/{temp_id}")
        async def get_temp_transaction(temp_id: str, db: Session = Depends(get_session)):
            data = DBManagerTransactions.get_temp_transaction_data(db, temp_id)
            logger.info(
                module="transaction_edit",
                message=f"temp_id: {temp_id}, data: {data}",
                user_id=user_id,
            )
            return data

        @router.post("/transactions/confirm-bulk")
        async def confirme_transaction_bulk_edit(data: dict, db: Session = Depends(get_session)):
            user_id = data.get("user_id")
            items = data.get("items")
            temp_id = data.get("temp_id")
            logger.info(
                module="transaction_confirm_edit",
                message=f"Confirming bulk transaction for user_id: {user_id} with temp_id: {temp_id}",
                user_id=user_id,
            )
            confirme_data_from_edit(db, temp_id, user_id, items, logger)
            return {"success": True, "message": "Confirm bulk transaction"}

        

        @router.post("/budget/setup")
        async def setup_budget(data: dict, db: Session = Depends(get_session)):
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

            return DBManagerBudget.setup_user_budget(
                db, user_id, category_id=category_id, amount=amount
            )

        @router.get("/budgets/{user_id}")
        async def get_user_budgets(user_id: str, db: Session = Depends(get_session)):
            logger.info(
                module="budget",
                message=f"Fetching budget remaining for user_id: {user_id}",
                user_id=user_id,
            )
            try:
                now = datetime.now()
                result = DBManagerBudget.get_user_budget(db, user_id, now.month, now.year)
                return {"success": True, "data": result}
            except Exception as e:
                logger.error(
                    module="budget",
                    message=f"Error fetching budget remaining for user_id: {user_id} - {str(e)}",
                    user_id=user_id,
                )
                return {"success": False, "message": "Error fetching budget remaining"}

            
        @router.get("/categories/parent")
        async def get_categories_parent(db: Session = Depends(get_session)):
            logger.info(module="categories", message="Fetching categories parent")
            return DBManagerCategories.get_parent_categories(db)

        @router.post("/categories/add")
        async def add_category(data: CategoryCreateRequest, db: Session = Depends(get_session)):
            user_id = data.user_id
            name = data.name
            parent_id = data.parent_id
            icon = data.icon
            logger.info(
                module="categories",
                message=f"Adding category for user_id: {user_id} with name: {name} and parent_id: {parent_id}",
                user_id=user_id,
            )
            if not user_id or not name:
                logger.error(
                    module="categories",
                    message="Missing user_id or name",
                    user_id=user_id,
                )
                return {"success": False, "message": "Missing user_id or name"}

            return Utilities.handle_custom_category_creation(db, name, icon, user_id, parent_id)