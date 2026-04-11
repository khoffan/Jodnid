from model.db_manament import delete_temp_transaction
from model.db_manament import confirm_and_save_transaction
from ai.text_nlp import extract_transactions
from helper.utils import (
    get_line_profile,
    get_instruction_flex,
    create_dynamic_flex_receipt,
    send_line_reply_v3,
    save_line_image,
    pre_process_image_file,
    get_content_line,
    send_loading_indicator_v3
)
from ai.text_nlp import is_transaction_message
from model.db_manament import get_or_create_user
from model.db_manament import save_temp_transaction
from ai.ocr import extract_text_from_image
from model.db_manament import create_attachment_record


async def process_webhook_event(event: dict, user_id: str, reply_token: str, line_access_token: str, api_key: str):
    event_type = event.get("type")
    # ดึงค่า User (หรือสร้างถ้ายังไม่มี)
    get_or_create_user(line_user_id=user_id, line_access_token=line_access_token)

    if event_type == "message":
        message = event.get("message", {})
        msg_type = message.get("type")

        # --- กรณีเป็น Text ---
        if msg_type == "text":
            user_text = message.get("text")
            # Logic: เช็ค Keywords และเรียก AI (ย้ายจาก Webhook มาที่นี่)
            await handle_text_message(user_id, user_text, reply_token, line_access_token, api_key)

        # --- กรณีเป็น Image (งานที่หนักที่สุด) ---
        elif msg_type == "image":
            message_id = message.get("id")
            # ย้าย Logic การทำ OCR และ Extract ไปไว้ในฟังก์ชันย่อย
            await handle_image_message(user_id, message_id, reply_token, line_access_token, api_key)

    elif event_type == 'postback':
        postback_data = event.get("postback", {}).get("data")
        # Logic การจัดการ Confirm/Cancel
        await handle_postback(user_id, postback_data, reply_token)


async def handle_text_message(user_id: str, user_text: str, reply_token: str, line_access_token: str, api_key: str):
    HELPER_KEYWORDS = ["ช่วยด้วย", "วิธีใช้", "ทำอะไรได้บ้าง", "สอนหน่อย"]
    GREETING_KEYWORDS = ["สวัสดี", "hello", "hi", "เริ่ม"]
    SUMMARY_KEYWORDS = ["ขอดูยอด", "สรุปยอด", "ใช้ไปเท่าไหร่"]
    user_text_lower = user_text.lower()
    send_loading_indicator_v3(user_id=user_id, seconds=10)
    is_transaction = is_transaction_message(api_key, user_text)
    print(f"Is Transaction: {is_transaction}")

    # --- 1. คำสั่งช่วยเหลือ (Help/Guidance) ---
    if any(k in user_text_lower for k in HELPER_KEYWORDS):
        send_line_reply_v3(reply_token, alt_text="คําแนะนำ",  flex_json=get_instruction_flex()) # ส่ง Flex คำแนะนำที่เราคุยกัน
    
    # --- 2. คำทักทาย (Greetings) ---
    elif any(k in user_text_lower for k in GREETING_KEYWORDS):
        profile = get_line_profile(user_id=user_id, line_token=line_access_token)
        user_name = profile.get("displayName", "คุณ")
        greeting_text = (
            f"สวัสดีครับคุณ {user_name}! 🙏\n"
            "ผม 'จดนิด' พร้อมช่วยบันทึกรายจ่ายให้คุณแล้ว\n"
            "ลองพิมพ์ 'ค่าข้าว 60' หรือส่งรูปสลิปมาได้เลยครับ"
        )
        send_line_reply_v3(reply_token, text=greeting_text)

    elif is_transaction:
        # ส่งไปให้ Typhoon วิเคราะห์รายการ
        final_transactions = extract_transactions(api_key, user_text)
        print(f"Extracted Transactions: {final_transactions}")
        temp_id = save_temp_transaction(user_id, final_transactions)
        
        flex_msg = create_dynamic_flex_receipt(final_transactions, temp_id=temp_id)
        send_line_reply_v3(reply_token, alt_text="บันทึกรายการสำเร็จ", flex_json=flex_msg)
    else:
        print("Not a transaction message.")
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
        send_line_reply_v3(reply_token, text=guidance_text)


async def handle_image_message(user_id: str, message_id: str, reply_token: str, line_access_token: str, api_key: str):
    send_loading_indicator_v3(user_id=user_id, seconds=20)
    image_bytes = get_content_line(message_id, line_token=line_access_token)
    processing_image = pre_process_image_file(image_bytes)
    if processing_image is None:
        print("Failed to download image")
        return {"status": "error", "message": "Failed to download image"}
    # NOTE: LINE ไม่ได้ส่งไฟล์รูปมาตรงๆ แต่ส่ง message_id มา
    # คุณต้องเขียนฟังก์ชันไป get รูปจาก LINE API มาก่อน (ใช้ Channel Access Token)
    # จากนั้นค่อยส่งไฟล์นั้นไปที่ extract_text_from_image
    save_file = save_line_image(user_id=user_id, message_id=message_id, image_bytes=image_bytes)
    if save_file:
        attachment_id = create_attachment_record(user_id=user_id, file_path=save_file, file_type="image/jpeg")
        # ตัวอย่าง Flow:
        # image_bytes = download_line_image(message_id)
        ocr_json = extract_text_from_image(processing_image, f"{message_id}.jpg", api_key)
        status = ocr_json.get("success")
        if not status:
            print(f"OCR failed: {ocr_json.get('error')}")
            send_line_reply_v3(reply_token, text="ขออภัยครับ ระบบไม่สามารถอ่านข้อมูลจากรูปนี้ได้ กรุณาลองใหม่อีกครั้งด้วยรูปที่ชัดเจนขึ้นครับ")
            return
        ocr_result = ocr_json["text"]
        final_transactions = ocr_result

        temp_id = save_temp_transaction(user_id, final_transactions, attachment_id=attachment_id, source_type="image")
        flex_msg = create_dynamic_flex_receipt(final_transactions, temp_id=temp_id)
        send_line_reply_v3(reply_token, alt_text="บันทึกรายการสำเร็จ", flex_json=flex_msg)
    else:
        print("Failed to save image")

async def handle_postback(user_id: str, postback_data, reply_token: str):
    from urllib.parse import parse_qsl
    params = dict(parse_qsl(postback_data))
    print(params)

    action = params.get("action")
    post_temp_id = params.get("temp_id")
    if action == "confirm":
        result = confirm_and_save_transaction(temp_id=post_temp_id)
        print(result)
        if result:
            
            count = result.get("count", 0)
            total = result.get("total", 0.0)
            text_reply = f"✅ บันทึกสำเร็จ {count} รายการ\n💰 ยอดรวม ฿{total:,.2f}\nเรียบร้อยแล้วครับ"
        else:
            text_reply = "❌ ไม่พบข้อมูลรายการนี้ หรือรายการอาจหมดอายุแล้วครับ"

        # 3. ตอบกลับเพื่อยืนยันผลการทำงาน
        send_line_reply_v3(reply_token, text=text_reply)
    elif action == "cancel":
        delete_temp_transaction(temp_id=post_temp_id)
        # (Option) ถ้า User กดกยกเลิก อาจจะแค่บอกว่ายกเลิกแล้ว
        send_line_reply_v3(reply_token=reply_token, text="🗑️ ยกเลิกการบันทึกรายการเรียบร้อยครับ")