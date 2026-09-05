"""อ่าน SystemLog และสรุปเมตริกภาพรวมสำหรับ admin console"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlmodel import Session, col, desc, func, select

from model.models import SystemLog, Transactions, Users

# ดึงมาอ่านในหน่วยความจำเท่านี้ตอนสรุปเมตริก — payload เป็น JSON column
# ซึ่ง query เข้าไปข้างในได้ไม่เหมือนกันระหว่าง SQLite กับ Postgres จึงสรุปฝั่ง Python แทน
OCR_METRIC_SAMPLE_SIZE = 500


class DBManagerMonitoring:
    @staticmethod
    def get_system_logs(
        session: Session,
        level: str = None,
        module: str = None,
        user_id: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """ดึง SystemLog แบบแบ่งหน้า พร้อมตัวกรองที่หน้า console ใช้"""
        limit = max(1, min(limit, 200))
        conditions = []
        if level:
            conditions.append(SystemLog.level == level.upper())
        if module:
            conditions.append(SystemLog.module == module)
        if user_id:
            conditions.append(SystemLog.user_id == user_id)
        if search:
            conditions.append(col(SystemLog.message).contains(search))

        count_statement = select(func.count()).select_from(SystemLog)
        statement = select(SystemLog).order_by(desc(SystemLog.timestamp))
        for condition in conditions:
            count_statement = count_statement.where(condition)
            statement = statement.where(condition)

        total = session.exec(count_statement).one()
        logs = session.exec(statement.offset(offset).limit(limit)).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [log.dict() for log in logs],
        }

    @staticmethod
    def get_log_modules(session: Session) -> List[str]:
        """รายชื่อ module ที่มีอยู่จริง เอาไปทำ dropdown ตัวกรอง"""
        statement = select(SystemLog.module).distinct().order_by(SystemLog.module)
        return [row for row in session.exec(statement).all() if row]

    @staticmethod
    def _ocr_metrics(session: Session, since: datetime) -> Dict[str, Any]:
        """
        สรุปคุณภาพการอ่านใบเสร็จจาก telemetry ที่ `extract_text_from_image` เขียนไว้

        `total_matched=False` คือรายการที่ยอดไม่ลงตัวจนระบบไม่ยอมบันทึกทันที
        เป็นตัวชี้วัดตรงที่สุดว่า AI อ่านตัวเลขเพี้ยนบ่อยแค่ไหน
        """
        statement = (
            select(SystemLog)
            .where(SystemLog.module == "ocr_pipeline", SystemLog.timestamp >= since)
            .order_by(desc(SystemLog.timestamp))
            .limit(OCR_METRIC_SAMPLE_SIZE)
        )
        logs = session.exec(statement).all()

        total = len(logs)
        failed = 0
        mismatched = 0
        checked_totals = 0
        latencies: List[int] = []

        for log in logs:
            payload = log.payload if isinstance(log.payload, dict) else {}
            if payload.get("fail_reason"):
                failed += 1
            latency = payload.get("latency_total_ms")
            if isinstance(latency, int):
                latencies.append(latency)
            matched = payload.get("total_matched")
            if matched is not None:
                checked_totals += 1
                if matched is False:
                    mismatched += 1

        latencies.sort()
        return {
            "sample_size": total,
            "success_rate": round((total - failed) / total * 100, 1) if total else None,
            "failed": failed,
            "total_mismatch_rate": (
                round(mismatched / checked_totals * 100, 1) if checked_totals else None
            ),
            "total_mismatched": mismatched,
            "median_latency_ms": latencies[len(latencies) // 2] if latencies else None,
        }

    @staticmethod
    def get_admin_metrics(session: Session, days: int = 7) -> Dict[str, Any]:
        """ตัวเลขภาพรวมสำหรับหน้า Stats ของ admin console"""
        now = datetime.now()
        since = now - timedelta(days=days)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)

        def scalar(statement, default=0):
            try:
                value = session.exec(statement).one()
            except Exception:
                return default
            return value if value is not None else default

        users_total = scalar(select(func.count()).select_from(Users))
        users_onboarded = scalar(
            select(func.count()).select_from(Users).where(Users.is_onboarded == True)  # noqa: E712
        )
        users_bypass = scalar(
            select(func.count())
            .select_from(Users)
            .where(Users.use_bypass_mode == True)  # noqa: E712
        )
        users_new = scalar(
            select(func.count()).select_from(Users).where(Users.created_at >= since)
        )

        tx_today = scalar(
            select(func.count()).select_from(Transactions).where(Transactions.transaction_date >= today_start)
        )
        tx_month = scalar(
            select(func.count()).select_from(Transactions).where(Transactions.transaction_date >= month_start)
        )
        amount_month = scalar(
            select(func.sum(Transactions.amount)).where(Transactions.transaction_date >= month_start), 0.0
        )

        errors = scalar(
            select(func.count())
            .select_from(SystemLog)
            .where(SystemLog.level == "ERROR", SystemLog.timestamp >= since)
        )

        return {
            "range_days": days,
            "users": {
                "total": users_total,
                "onboarded": users_onboarded,
                "bypass_mode": users_bypass,
                "new_in_range": users_new,
            },
            "transactions": {
                "today": tx_today,
                "this_month": tx_month,
                "amount_this_month": round(float(amount_month or 0), 2),
            },
            "ocr": DBManagerMonitoring._ocr_metrics(session, since),
            "errors_in_range": errors,
        }
