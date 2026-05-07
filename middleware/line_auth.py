import httpx
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config_settings import settings


security = HTTPBearer()

# ฟังก์ชันสำหรับแลก Code เป็น Token
async def exchange_code_for_tokens(code: str, is_test_mode: bool) -> dict:
    token_url = "https://api.line.me/oauth2/v2.1/token"
    
    channel_id = settings.LINE_CHANNEL_ID_TEST if is_test_mode else settings.LINE_CHANNEL_ID
    channel_secret = settings.LINE_CHANNEL_SECRET_TEST if is_test_mode else settings.LINE_CHANNEL_SECRET
    
    # ⚠️ ตรวจสอบว่าใน settings มี redirect_uri หรือไม่ (ต้องตรงกับ LINE Developer)
    redirect_uri = settings.LINE_REDIRECT_URI

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": channel_id,
        "client_secret": channel_secret
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code with LINE: {response.text}"
            )
        
        return response.json()

# ฟังก์ชันสำหรับตรวจสอบ ID Token กับ LINE
async def verify_id_token_with_line(id_token: str, channel_id: str) -> dict:
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
            
        return response.json()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    # สามารถเพิ่ม Query parameter เพื่อรับ is_test_mode หรือตรวจสอบผ่าน Environment ได้
) -> dict:
    """
    Dependency สำหรับตรวจสอบ Token ผ่าน Bearer
    """
    token = credentials.credentials
    
    # ⚠️ หมายเหตุ: สามารถเพิ่มเงื่อนไขแยก Test Mode หรือ Production ได้ตรงนี้
    channel_id = settings.LINE_CHANNEL_ID_TEST if settings.TEST_MODE else settings.LINE_CHANNEL_ID
    
    try:
        user_info = await verify_id_token_with_line(token, channel_id)
        # user_info จะมีข้อมูลเช่น sub (User ID), name, picture ฯลฯ
        return user_info
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )