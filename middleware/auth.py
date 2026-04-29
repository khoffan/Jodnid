from sqlmodel import select, Session
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, credentials
import firebase_admin
from model.models import Administrator, engine
from core.config_settings import settings
import json
# 1. Initialize Firebase (ควรใช้ environment variable เพื่อความปลอดภัย)
if not firebase_admin._apps:
    try:
        firebase_key_json = json.loads(settings.FIREBASE_ACCOUNT_KEY)
        # ใน Production แนะนำให้ใช้ ENV หรือโหลดไฟล์ผ่าน Path ที่ปลอดภัย
        cred = credentials.Certificate(firebase_key_json)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initializing Firebase",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ใช้ HTTPBearer เพื่อดักจับ Header "Authorization: Bearer <token>"
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    ฟังก์ชัน Dependency สำหรับตรวจสอบ Firebase ID Token
    """
    token = credentials.credentials
    
    try:
        # 2. ตรวจสอบ Token กับ Firebase
        decoded_token = auth.verify_id_token(token)
        
        # คืนค่าข้อมูล User (เช่น uid, email, name) ออกไปให้ Route เรียกใช้
        statement = select(Administrator).where(Administrator.uid == decoded_token['uid'])
        with Session(engine) as session:
            userAdmin = session.exec(statement).first()
        
            if not userAdmin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return userAdmin
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )