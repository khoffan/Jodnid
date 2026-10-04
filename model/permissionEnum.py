from enum import Enum

class PermissionEnum(str, Enum):
    # 📊 Overview Module
    OVERVIEW_VIEW = "overview_view"

    # ⚙️ Config Module
    CONFIG_READ = "config_read"
    CONFIG_WRITE = "config_write"  # 🚨 จะถูกบล็อกบน Production ใน Middleware
    CONFIG_EDIT = "config_edit"
    CONFIG_DELETE = "config_delete"

    # 👤 Users Module
    USER_VIEW = "user_view"
    USER_MANAGE = "user_manage"

    # 🔑 Admin Management Module
    ADMIN_READ = "admin_read"
    ADMIN_MANAGE = "admin_manage"