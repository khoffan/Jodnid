from helper.utils import get_all_users, get_line_profile
from fastapi import APIRouter, Depends
from sqlmodel import Session
from helper.logger import JodNidLogger
from model.models import get_session
from middleware.auth import get_current_user
from model.models import Administrator
from helper.utils import clear_config_cache
from model.db_manament import (
    create_system_config,
    get_system_config_data,
    update_system_config,
    update_administrator_data_system,
)

class AdministratorAPIs:
    def __init__(self, logger: JodNidLogger, line_access_token: str):
        self.logger = logger
        self.line_access_token = line_access_token
        self.router = APIRouter(
            prefix="/api/administrator",
            tags=["administrator"]
        )
    def setup_router(self):
        router = self.router
        logger = self.logger
        users = get_all_users(next(get_session()))
        user_id = None
        for user in users:
            profile = get_line_profile(user_id=user.line_user_id, line_token=self.line_access_token)
            user_id=profile.get("userId")
    
        # administrator service
        @router.post("/sync")
        async def sync_data(data: dict, db: Session = Depends(get_session),):
            logger.info(module="app", message=f"Syncing data for user_id: {user_id}", user_id=user_id)
            email = data.get("email")
            uid = data.get("uid")
            if not email or not uid:
                return {"success": False, "message": "Missing email or uid or name"}
            result = update_administrator_data_system(db,uid, email)
            logger.info(module="administrator", message=f"Data sync for uid: {uid} result: {result}", user_id=uid)
            if result.get("success") == False:
                logger.info(module="administrator", message=f"Data sync failed for uid: {uid}", user_id=uid)
                return {"success": False, "message": "Data sync failed"}
            return result
            
            
            

        @router.post("/config/create")
        async def create_system_configuration(data: dict, db: Session = Depends(get_session), user:Administrator = Depends(get_current_user)):
            name = data.get("name")
            key = data.get("key")
            value = data.get("value")
            value_type = data.get("value_type")
            description = data.get("description")
            if not name or not key or not value or not value_type:
                return {"success": False, "message": "Missing name or key or value or value_type"}
            
            logger.info(module="app", message=f"Creating system configuration for name: {name}, key: {key}, value: {value}, value_type: {value_type}, description: {description}", user_id=user.uid)
            return create_system_config(db, name, key, value, value_type, description)


        @router.get("/all")
        def get_all_system_configuration(db: Session = Depends(get_session), user:Administrator = Depends(get_current_user)):
            logger.info(module="app", message="Fetching all system configurations", user_id=user.uid)
            return get_system_config_data(db)


        @router.patch("/config/update")
        def update_system_configuration(data: dict, db: Session = Depends(get_session), user:Administrator = Depends(get_current_user)):
            key = data.get("key")
            value = data.get("value")
            value_type = data.get("value_type")
            description = data.get("description")
            if not key or not value:
                return {"success": False, "message": "Missing key or value"}
            clear_config_cache()
            logger.info(module="app", message=f"Updating system configuration for key: {key}, value: {value}, value_type: {value_type}, description: {description}", user_id=user.uid)
            return update_system_config(db, key, value, value_type, description)

        @router.patch("/config/toggle")
        def toggle_system_configuration(data: dict, db: Session = Depends(get_session), user:Administrator = Depends(get_current_user)):
            key = data.get("key")
            value = data.get("value")
            if not key or not value:
                return {"success": False, "message": "Missing key or value"}
            clear_config_cache()
            logger.info(module="app", message=f"Toggling system configuration for key: {key}, value: {value}", user_id=user.uid)
            return update_system_config(db, key, value)
        