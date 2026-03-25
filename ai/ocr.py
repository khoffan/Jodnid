import requests
import json
import re

def parse_slip_data(text):
    data = {
        "amount": 0.0,
        "fee": 0.0,
        "timestamp": None,
        "receiver": None
    }

    # 1. หาจำนวนเงิน (Amount) - มองหาตัวเลขหน้าคำว่า "บาท"
    amount_match = re.search(r"จำนวนเงิน\s*\*?\*?([\d,]+\.\d{2})\*?\*?\s*บาท", text)
    if amount_match:
        data["amount"] = float(amount_match.group(1).replace(",", ""))

    # 2. หาค่าธรรมเนียม (Fee)
    fee_match = re.search(r"ค่าธรรมเนียม\s*\*?\*?([\d,]+\.\d{2})\*?\*?\s*บาท", text)
    if fee_match:
        data["fee"] = float(fee_match.group(1).replace(",", ""))

    # 3. หาวันที่และเวลา (Timestamp)
    # แพทเทิร์น: 19 ก.พ. 2569 - 00:30
    time_match = re.search(r"(\d{1,2}\s+[ก-ฮ\.]+\s+\d{4}\s*-\s*\d{2}:\d{2})", text)
    if time_match:
        data["timestamp"] = time_match.group(1)

    # 4. หาผู้รับเงิน (Receiver) 
    # Logic: หาบรรทัดที่ต่อจาก "ไปยัง"
    receiver_match = re.search(r"ไปยัง\n(.+)", text)
    if receiver_match:
        data["receiver"] = receiver_match.group(1).strip()

    return data

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
        text = '\n'.join(extracted_texts)
        response = parse_slip_data(text=text)
        return {"success": True, "text": response}
    else:
        return {"success": False, "error": response.text}
       
