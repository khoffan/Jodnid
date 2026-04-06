from openai import OpenAI
import requests
import json
import re
from ai.text_nlp import extract_transactions

def is_financial_document(api_key: str, ocr_text: str) -> bool:
    """
    ตรวจสอบว่าข้อความจาก OCR เข้าข่ายเป็นสลิปธนาคารหรือใบเสร็จรับเงินหรือไม่
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.opentyphoon.ai/v1"
    )

    # Prompt เน้นประหยัด token และตอบแค่ true/false
    system_prompt = (
        "Analyze if this text is from a Bank Slip or Shopping Receipt.\n"
        "Return 'true' if it contains: Bank Name, Transaction Date, Amount, OR Shop Name.\n"
        "Return 'false' otherwise. Answer ONLY 'true' or 'false'."
    )

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ocr_text[:1000]} # ส่งแค่ 1000 ตัวอักษรแรกเพื่อประหยัด token
            ],
            temperature=0,
            max_tokens=1000, 
            top_p=1
        )
        result = response.choices[0].message.content.strip().lower()
        return "true" in result
    except Exception as e:
        print(f"Image Validation Error: {e}")
        return True # Fallback ให้ผ่านไปก่อนถ้า AI พัง

def extract_text_from_image(image_path,filename,api_key):
    url = "https://api.opentyphoon.ai/v1/ocr"
    model = "typhoon-ocr"
    task_type = "default"
    max_tokens = 16384
    temperature = 0.1
    top_p = 0.6
    repetition_penalty = 1.2
    pages = None

    files = {'file': (filename, image_path, 'image/jpeg')}
    data = {
            'model': model,
            'task_type': task_type,
            'max_tokens': str(max_tokens),
            'temperature': str(temperature),
            'top_p': str(top_p),
            'repetition_penalty': str(repetition_penalty)
    }

    if pages:
        data['pages'] = json.dumps(pages)

    headers = {
            'Authorization': f'Bearer {api_key}'
    }

    response = requests.post(url, files=files, data=data, headers=headers)

    if response.status_code == 200:
        result = response.json()

        # Extract text from successful results
        extracted_texts = []
        for page_result in result.get('results', []):
            if page_result.get('success') and page_result.get('message'):
                content = page_result['message']['choices'][0]['message']['content']
                try:
                    # Try to parse as JSON if it's structured output
                    parsed_content = json.loads(content)
                    text = parsed_content.get('natural_text', content)
                except json.JSONDecodeError:
                    text = content
                extracted_texts.append(text)
            elif not page_result.get('success'):
                print(f"Error processing {page_result.get('filename', 'unknown')}: {page_result.get('error', 'Unknown error')}")
        full_text = '\n'.join(extracted_texts)
        if not is_financial_document(api_key, full_text):
            print("The extracted text does not appear to be from a financial document. Skipping transaction extraction.")
            return {"success": False, "error": "Not a financial document"}

        response = extract_transactions(api_key, full_text)
        return {"success": True, "text": response}
    else:
        return {"success": False, "error": response.text}
       
