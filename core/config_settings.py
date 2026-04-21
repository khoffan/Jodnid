from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # กำหนดค่าตัวแปรและ Type (ถ้าใน .env ไม่มี จะใช้ค่า Default ที่ใส่ไว้)
    TYPHOON_API_KEY: str
    PORT: int
    DEBUG: bool
    LINE_CHANNEL_ACCESS_TOKEN: str
    LINE_CHANNEL_ACCESS_TOKEN_TEST: str
    LINE_DATA_API: str
    LINE_API: str
    LINE_LIFF_ID: str
    LINE_LIFF_ID_TEST: str
    FRONTEND_URL: str
    ADMIN_URL: str
    CRON_SECRET_TOKEN: str
    # Database
    DATABASE_URL: str
    TEST_MODE: bool
    # Cloudinary
    CLOUNDIARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # ตั้งค่าการโหลดไฟล์ .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings():
    """ใช้ lru_cache เพื่อให้โหลดไฟล์ครั้งเดียวแล้วจำค่าไว้ตลอด"""
    return Settings()

# สร้าง instance ไว้พร้อมใช้งาน
settings = get_settings()
