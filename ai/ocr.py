from openai import OpenAI
import requests
import json
import re
from ai.text_nlp import extract_transactions

def is_financial_document(api_key: str, ocr_text: str) -> bool:
    client = OpenAI(api_key=api_key, base_url="https://api.opentyphoon.ai/v1")

    # ปรับ Prompt ให้ยอมรับ Shopping Receipt มากขึ้น
    system_prompt = (
        "You are a financial document classifier.\n"
        "Analyze if the text is a Bank Slip, POS Receipt, Tax Invoice, or Restaurant Bill.\n"
        "Criteria for 'true':\n"
        "- Contains a Total Amount (e.g., Baht, THB, Total, Amount Due).\n"
        "- Contains a Transaction Date.\n"
        "- Contains either a Shop Name, Merchant Name, or Bank Name.\n"
        "Return 'true' if it looks like a record of spending money. Return 'false' otherwise.\n"
        "Answer ONLY 'true' or 'false'."
    )

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ocr_text[:1500]} # เพิ่มเป็น 1500 เผื่อหัวใบเสร็จยาว
            ],
            temperature=0,
            max_tokens=600,
        )
        result = response.choices[0].message.content.strip().lower()
        return "true" in result
    except Exception as e:
        print(f"Image Validation Error: {e}")
        return True

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
    
    print("response ocr", response.json().get("results", []))
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
        print("response after extract", response)
        return {"success": True, "text": response}
    else:
        return {"success": False, "error": response.text}
       
