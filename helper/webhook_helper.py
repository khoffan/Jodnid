# from helper.utils import get_config_value
import re
from typing import Any, Dict, List

from ai.ocr import extract_text_from_image
from ai.text_nlp import extract_transactions, is_transaction_message
from helper.logger import JodNidLogger
from helper.utils import (
    create_dynamic_flex_receipt,
    get_content_line,
    get_instruction_flex,
    get_line_profile,
    pre_process_image_file,
    save_line_image,
    send_line_reply_v3,
    send_loading_indicator_v3,
    send_push_notification,
)
from model.db_manament import DBManagerTransactions, DBManagerUsers

manager_transactions = DBManagerTransactions()
manager_users = DBManagerUsers()


async def process_webhook_event(
    event: dict,
    user_id: str,
    reply_token: str,
    line_access_token: str,
    api_key: str,
    logger: JodNidLogger,
):
    event_type = event.get("type")
    profile = get_line_profile(user_id=user_id, line_token=line_access_token)

    # ดึงค่า User (หรือสร้างถ้ายังไม่มี)
    manager_users.get_or_create_user(
        line_user_id=user_id,
        profile={
            "display_name": profile.get("displayName"),
        },
    )

    if event_type == "message":
        message = event.get("message", {})
        msg_type = message.get("type")
        logger.info(module="webhook", message=f"handle message type: {msg_type}", user_id=user_id)
        # --- กรณีเป็น Text ---
        if msg_type == "text":
            user_text = message.get("text")
            logger.info(
                module="webhook", message=f"handle text message: {user_text}", user_id=user_id
            )
            # is_text_active = get_config_value(key="is_text_active")
            # if is_text_active:
            #     send_push_notification(user_id, content="ระบบกำลังปรับปรุง กรุณาลองใหม่อีกครั้งในภายหลัง")
            #     return
            # Logic: เช็ค Keywords และเรียก AI (ย้ายจาก Webhook มาที่นี่)
            await handle_text_message(
                user_id, user_text, reply_token, line_access_token, api_key, logger
            )

        # --- กรณีเป็น Image (งานที่หนักที่สุด) ---
        elif msg_type == "image":
            message_id = message.get("id")
            logger.info(
                module="webhook", message=f"handle image message id: {message_id}", user_id=user_id
            )
            # is_ocr_active = get_config_value(key="is_ocr_active")
            # if is_ocr_active:
            #     send_push_notification(user_id, content="ระบบกำลังปรับปรุง กรุณาลองใหม่อีกครั้งในภายหลัง")
            #     return
            # ย้าย Logic การทำ OCR และ Extract ไปไว้ในฟังก์ชันย่อย
            await handle_image_message(
                user_id, message_id, reply_token, line_access_token, api_key, logger
            )

    elif event_type == "postback":
        postback_data = event.get("postback", {}).get("data")
        logger.info(
            module="webhook", message=f"handle postback data: {postback_data}", user_id=user_id
        )
        # Logic การจัดการ Confirm/Cancel
        await handle_postback(postback_data, user_id, logger)


async def handle_text_message(
    user_id: str,
    user_text: str,
    reply_token: str,
    line_access_token: str,
    api_key: str,
    logger: JodNidLogger,
):
    try:
        HELPER_KEYWORDS = [
            "ช่วยด้วย",
            "วิธีใช้",
            "ทำอะไรได้บ้าง",
            "สอนหน่อย",
            "help",
            "how to use",
            "how to use จดนิด",
        ]
        GREETING_KEYWORDS = ["สวัสดี", "hello", "hi", "เริ่ม", "start", "start จดนิด"]
        SUMMARY_KEYWORDS = [
            "ขอดูยอด",
            "สรุปยอด",
            "ใช้ไปเท่าไหร่",
            "summary",
            "how much",
            "how much have i spent",
            "how much have i spent today",
        ]
        user_text_lower = user_text.lower().strip()
        logger.info(
            module="webhook_text_ai",
            message=f"processing text message: {user_text_lower}",
            user_id=user_id,
        )

        # --- 1. คำสั่งช่วยเหลือ (Help/Guidance) ---
        if any(k in user_text_lower for k in HELPER_KEYWORDS):
            logger.info(
                module="webhook_text_ai", message="processing helper keywords", user_id=user_id
            )
            send_push_notification(
                user_id, alt_text="คําแนะนำ", content=get_instruction_flex()
            )  # ส่ง Flex คำแนะนำที่เราคุยกัน

        # --- 2. คำทักทาย (Greetings) ---
        elif any(k in user_text_lower for k in GREETING_KEYWORDS):
            logger.info(
                module="webhook_text_ai", message="processing greeting keywords", user_id=user_id
            )
            profile = get_line_profile(user_id=user_id, line_token=line_access_token)
            user_name = profile.get("displayName", "คุณ")
            greeting_text = (
                f"สวัสดีครับคุณ {user_name}! 🙏\n"
                "ผม 'จดนิด' พร้อมช่วยบันทึกรายจ่ายให้คุณแล้ว\n"
                "ลองพิมพ์ 'ค่าข้าว 60' หรือส่งรูปสลิปมาได้เลยครับ"
            )
            send_push_notification(user_id, content=greeting_text, alt_text="สวัสดีครับ")

        # --- STEP B: ดักจับรูปแบบยอดฮิตด้วย Regex (เร็วมาก - 0ms) ---
        # Pattern: [ข้อความ] ตามด้วย [ตัวเลข] เช่น "กะเพรา 50" หรือ "โอน 100"
        is_simple_format = re.search(r".+\s+\d+", user_text)

        # --- STEP C: ถ้าไม่เข้าเงื่อนไขง่ายๆ ค่อยใช้ AI เช็ค (ช้า - 1-2s) ---
        # เราจะเรียก AI ก็ต่อเมื่อมีตัวเลขในข้อความเท่านั้น เพื่อประหยัดเวลา
        has_number = any(char.isdigit() for char in user_text)

        is_transaction = False
        if is_simple_format:
            is_transaction = True
        elif has_number:
            logger.info(
                module="webhook_text_ai",
                message="processing has number text message",
                user_id=user_id,
            )
            # ส่ง loading indicator เฉพาะตอนที่ต้องรอ AI นานๆ
            send_loading_indicator_v3(user_id=user_id, seconds=5)
            is_transaction = is_transaction_message(api_key, user_text)

        if is_transaction:
            logger.info(
                module="webhook_text_ai", message="processing transaction message", user_id=user_id
            )
            send_line_reply_v3(reply_token, text="จดนิดกำลังวิเคราะห์รายการให้นะครับ... ⏳")
            # ส่งไปให้ Typhoon วิเคราะห์รายการ
            final_transactions = extract_transactions(api_key, user_text)
            logger.info(
                module="webhook_text_ai",
                message=f"Extracted Transactions: {final_transactions}",
                user_id=user_id,
            )
            temp_id = manager_transactions.save_temp_transaction(user_id, final_transactions)

            flex_msg = create_dynamic_flex_receipt(final_transactions, temp_id=temp_id)
            send_push_notification(user_id, content=flex_msg, alt_text="บันทึกรายการสำเร็จ")
        else:
            logger.info(
                module="webhook_text_ai", message="Not a transaction message.", user_id=user_id
            )
            guidance_text = (
                "🤖 จดนิด ยังไม่เข้าใจรายการนี้ครับ\n\n"
                "💡 วิธีจดที่ถูกต้อง:\n"
                "• พิมพ์ [รายการ] [จำนวนเงิน]\n"
                "  เช่น 'ค่าข้าว 60' หรือ 'ได้เงินเดือน 30000'\n"
                "• ส่งรูป 'สลิปโอนเงิน' ได้เลย\n\n"
                "⚠️ สิ่งที่จดไม่ได้:\n"
                "• ข้อความทักทายหรือคุยเล่น\n"
                "• ข้อความที่ไม่มีตัวเลขจำนวนเงิน"
            )
            # (Option) คุณอาจจะส่งข้อความกลับไปบอก User ว่าไม่พบรายการในข้อความนี้ก็ได้
            send_push_notification(
                user_id, content=guidance_text, alt_text="จดนิดยังไม่เข้าใจรายการนี้ครับ"
            )
    except Exception as e:
        logger.error(
            module="webhook_text_ai",
            message=f"Error handling text message: {str(e)}",
            user_id=user_id,
        )
        send_push_notification(user_id, content="เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง")


async def handle_image_message(
    user_id: str,
    message_id: str,
    reply_token: str,
    line_access_token: str,
    api_key: str,
    logger: JodNidLogger,
):
    send_loading_indicator_v3(user_id=user_id, seconds=20)
    send_line_reply_v3(reply_token, text="จดนิดกำลังวิเคราะห์รายการให้นะครับ... ⏳")
    image_bytes = get_content_line(message_id, line_token=line_access_token)
    processing_image = pre_process_image_file(image_bytes)
    if processing_image is None:
        logger.error(module="webhook_image_ai", message="Failed to download image", user_id=user_id)
        return {"status": "error", "message": "Failed to download image"}
    # NOTE: LINE ไม่ได้ส่งไฟล์รูปมาตรงๆ แต่ส่ง message_id มา
    # คุณต้องเขียนฟังก์ชันไป get รูปจาก LINE API มาก่อน (ใช้ Channel Access Token)
    # จากนั้นค่อยส่งไฟล์นั้นไปที่ extract_text_from_image
    save_file = save_line_image(user_id=user_id, message_id=message_id, image_bytes=image_bytes)
    if save_file:
        attachment_id = manager_transactions.create_attachment_record(
            user_id=user_id, file_path=save_file, file_type="image/jpeg"
        )
        # ตัวอย่าง Flow:
        # image_bytes = download_line_image(message_id)
        ocr_json = extract_text_from_image(processing_image, f"{message_id}.jpg", api_key)
        status = ocr_json.get("success")
        if not status:
            logger.error(
                module="webhook_image_ai",
                message=f"OCR failed: {ocr_json.get('error')}",
                user_id=user_id,
            )
            send_push_notification(
                user_id,
                content="ขออภัยครับ ระบบไม่สามารถอ่านข้อมูลจากรูปนี้ได้ กรุณาลองใหม่อีกครั้งด้วยรูปที่ชัดเจนขึ้นครับ",
            )
            return
        ocr_result = ocr_json["text"]
        final_transactions = ocr_result

        temp_id = manager_transactions.save_temp_transaction(
            user_id, final_transactions, attachment_id=attachment_id, source_type="image"
        )
        flex_msg = create_dynamic_flex_receipt(final_transactions, temp_id=temp_id)
        send_push_notification(user_id, content=flex_msg, alt_text="บันทึกรายการสำเร็จ")
    else:
        logger.error(module="webhook_image_ai", message="Failed to save image", user_id=user_id)
        send_push_notification(
            user_id, content="ขออภัยครับ ระบบไม่สามารถอ่านข้อมูลจากรูปนี้ได้ กรุณาลองใหม่อีกครั้งด้วยรูปที่ชัดเจนขึ้นครับ"
        )


async def handle_postback(postback_data: str, user_id: str, logger: JodNidLogger):
    try:
        from urllib.parse import parse_qsl

        params = dict(parse_qsl(postback_data))

        action = params.get("action")
        post_temp_id = params.get("temp_id")
        logger.info(
            module="webhook_postback",
            message=f"processing postback action: {action}, temp_id: {post_temp_id}",
            user_id=user_id,
        )

        if action == "confirm":
            # 1. บันทึกลง DB และดึงข้อมูลสรุปงบที่อัปเดต
            result = manager_transactions.confirm_and_save_transaction(temp_id=post_temp_id)
            logger.info(module="webhook_postback", message=f"result: {result}", user_id=user_id)

            if result:
                count = result.get("count", 0)
                total = result.get("total", 0.0)
                budgets = result.get("budgets", [])

                # 2. ส่ง Reply ยืนยันการบันทึกสำเร็จก่อน (เพื่อปิด Loading ของ LINE)
                text_confirm = f"✅ บันทึกสำเร็จ {count} รายการ\n💰 ยอดรวม ฿{total:,.2f}"
                send_push_notification(user_id=user_id, content=text_confirm, alt_text="บันทึกสำเร็จ")
                logger.info(
                    module="webhook_postback",
                    message=f"text_confirm: {text_confirm}",
                    user_id=user_id,
                )
                # 3. ส่ง Push Message สรุปงบประมาณ (ถ้ามีการตั้งงบไว้)
                if budgets:
                    for b in budgets:
                        # คำนวณสถานะ
                        amount = b["amount"]
                        spent = b["current_spent"]
                        percent = (spent / amount) * 100 if amount > 0 else 0
                        remaining = amount - spent

                        # สร้างข้อความเตือนตามระดับการใช้จ่าย
                        status_emoji = "📊"
                        if percent >= 100:
                            status_emoji = "⚠️ งบเกินแล้ว!"
                        elif percent >= 80:
                            status_emoji = "🔔 ใกล้เต็มแล้ว!"

                        budget_msg = (
                            f"{status_emoji}\n"
                            f"หมวด: {b['icon']} {b['category_name']}\n"
                            f"ใช้ไป: {percent:.1f}% (฿{spent:,.2f})\n"
                            f"คงเหลือ: ฿{remaining:,.2f}"
                        )
                        logger.info(
                            module="webhook_postback",
                            message=f"budget_msg: {budget_msg}",
                            user_id=user_id,
                        )
                        # ส่งเป็น Push Message (เพราะอาจจะใช้เวลาประมวลผลแยกกัน)
                        send_push_notification(user_id, content=budget_msg, alt_text="สรุปยอดใช้จ่าย")

                        # TIP: ในอนาคตคุณสามารถเปลี่ยนจากส่ง Text เป็นส่ง
                        # send_line_push_v3(user_id, flex_json=create_budget_flex(b))
                        # เพื่อความสวยงามได้ครับ
            else:
                logger.info(
                    module="webhook_postback",
                    message=f"❌ ไม่พบข้อมูลรายการนี้ หรือถูกบันทึกไปแล้วครับ temp_id: {post_temp_id}",
                    user_id=user_id,
                )
                send_push_notification(
                    user_id=user_id,
                    content="❌ ไม่พบข้อมูลรายการนี้ หรือถูกบันทึกไปแล้วครับ",
                    alt_text="ไม่พบข้อมูล",
                )

        elif action == "cancel":
            logger.info(
                module="webhook_postback",
                message=f"canceling temp_id: {post_temp_id}",
                user_id=user_id,
            )
            manager_transactions.delete_temp_transaction(temp_id=post_temp_id)
            send_push_notification(
                user_id=user_id, content="🗑️ ยกเลิกการบันทึกรายการเรียบร้อยครับ", alt_text="ยกเลิกการบันทึก"
            )
    except Exception as e:
        logger.error(
            module="webhook_postback", message=f"Error handling postback: {str(e)}", user_id=user_id
        )
        send_push_notification(user_id, content="ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผล")


def confirme_data_from_edit(
    post_temp_id: str, user_id: str, items: List[Dict[str, Any]] = None, logger: JodNidLogger = None
):
    if logger is None:
        logger = JodNidLogger()

    try:
        # 1. บันทึกลง DB และดึงข้อมูลสรุปงบที่อัปเดต
        result = manager_transactions.confirm_and_save_transaction(
            temp_id=post_temp_id, edit=True, items=items
        )
        logger.info(module="webhook_postback_edit", message=f"result: {result}", user_id=user_id)
        if result:
            count = result.get("count", 0)
            total = result.get("total", 0.0)
            budgets = result.get("budgets", [])

            # 2. ส่ง Reply ยืนยันการบันทึกสำเร็จก่อน (เพื่อปิด Loading ของ LINE)
            text_confirm = f"✅ บันทึกสำเร็จ {count} รายการ\n💰 ยอดรวม ฿{total:,.2f}"
            send_push_notification(user_id=user_id, content=text_confirm, alt_text="บันทึกสำเร็จ")
            logger.info(
                module="webhook_postback_edit",
                message=f"text_confirm: {text_confirm}",
                user_id=user_id,
            )
            # 3. ส่ง Push Message สรุปงบประมาณ (ถ้ามีการตั้งงบไว้)
            if budgets:
                for b in budgets:
                    # คำนวณสถานะ
                    amount = b["amount"]
                    spent = b["current_spent"]
                    percent = (spent / amount) * 100 if amount > 0 else 0
                    remaining = amount - spent

                    # สร้างข้อความเตือนตามระดับการใช้จ่าย
                    status_emoji = "📊"
                    if percent >= 100:
                        status_emoji = "⚠️ งบเกินแล้ว!"
                    elif percent >= 80:
                        status_emoji = "🔔 ใกล้เต็มแล้ว!"

                    budget_msg = (
                        f"{status_emoji}\n"
                        f"หมวด: {b['icon']} {b['category_name']}\n"
                        f"ใช้ไป: {percent:.1f}% (฿{spent:,.2f})\n"
                        f"คงเหลือ: ฿{remaining:,.2f}"
                    )
                    logger.info(
                        module="webhook_postback_edit",
                        message=f"budget_msg: {budget_msg}",
                        user_id=user_id,
                    )
                    # ส่งเป็น Push Message (เพราะอาจจะใช้เวลาประมวลผลแยกกัน)
                    send_push_notification(user_id, content=budget_msg, alt_text="สรุปยอดใช้จ่าย")

                    # TIP: ในอนาคตคุณสามารถเปลี่ยนจากส่ง Text เป็นส่ง
                    # send_line_push_v3(user_id, flex_json=create_budget_flex(b))
                    # เพื่อความสวยงามได้ครับ
        else:
            logger.info(
                module="webhook_postback_edit",
                message=f"❌ ไม่พบข้อมูลรายการนี้ หรือถูกบันทึกไปแล้วครับ temp_id: {post_temp_id}",
                user_id=user_id,
            )
            send_push_notification(
                user_id=user_id, content="❌ ไม่พบข้อมูลรายการนี้ หรือถูกบันทึกไปแล้วครับ", alt_text="ไม่พบข้อมูล"
            )
    except Exception as e:
        logger.error(
            module="webhook_postback_edit",
            message=f"Error handling postback: {str(e)}",
            user_id=user_id,
        )
        send_push_notification(user_id, content="ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผล")
