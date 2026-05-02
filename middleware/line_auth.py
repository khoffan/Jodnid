import httpx
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config_settings import settings

isTestMode = settings.TEST_MODE
if isTestMode:
    LINE_CHANNEL_ID = settings.LINE_CHANNEL_ID_TEST
else:
    LINE_CHANNEL_ID = settings.LINE_CHANNEL_ID



security = HTTPBearer()



async def verify_id_token_with_line(id_token: str, channel_id: str):
    """
    ตรวจสอบ id_token ผ่าน LINE API โดยตรง ไม่ต้องกังวลเรื่อง Algorithm
    """
    LINE_VERIFY_URL = settings.LINE_VERIFY_URL
    payload = {
        "id_token": id_token,
        "client_id": channel_id
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            LINE_VERIFY_URL, 
            data=payload, 
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired ID token"
            )
            
        # จะได้ Payload ที่ถอดรหัสแล้วจาก LINE
        return response.json()

async def get_current_user_line(credentials: HTTPAuthorizationCredentials = Security(security)):
    header_token = credentials.credentials
    payload = await verify_id_token_with_line(header_token, LINE_CHANNEL_ID)
    return payload