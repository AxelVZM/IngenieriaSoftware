"""
WhatsApp message sender
"""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .config import MESSAGE_DELAY_MIN, MESSAGE_DELAY_MAX, COUNTRY_CODE
from .screenshots import save_screenshot

def normalize_phone(phone):
    """Normalize phone number to include country code"""
    clean = str(phone).replace(" ", "").replace("-", "").replace("+", "")
    if len(clean) == 9:
        return f"{COUNTRY_CODE}{clean}"
    return clean

def send_message(driver, phone, message):
    """Send a single WhatsApp message"""
    import urllib.parse
    phone = normalize_phone(phone)
    
    # Encode message in URL
    message_encoded = urllib.parse.quote(message)
    url = f"https://web.whatsapp.com/send?phone={phone}&text={message_encoded}"
    
    try:
        driver.get(url)
        time.sleep(8)
        
        # Find message input
        wait = WebDriverWait(driver, 20)
        input_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][role="textbox"]'))
        )
        
        # Click input (message already loaded from URL)
        input_box.click()
        time.sleep(2)
        
        # Try multiple selectors for send button
        send_selectors = [
            'button[aria-label="Enviar"]',
            'button[data-tab="11"]',
            'span[data-icon="send"]'
        ]
        
        send_button = None
        for selector in send_selectors:
            try:
                send_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break
            except:
                continue
        
        if not send_button:
            raise Exception("Send button not found")
        
        # Send
        send_button.click()
        time.sleep(5)
        
        # Screenshot after sending
        save_screenshot(driver, "success", "message_sent")
        
        return {"phone": phone, "status": "success", "message": "Sent"}
        
    except Exception as e:
        save_screenshot(driver, "errors", f"error_{phone}")
        return {"phone": phone, "status": "error", "message": str(e)}

def send_messages(driver, messages):
    """Send multiple messages with delay"""
    results = []
    
    for i, msg in enumerate(messages, 1):
        print(f"\n[{i}/{len(messages)}] Sending to {msg['phone']}...")
        
        result = send_message(driver, msg['phone'], msg['message'])
        results.append(result)
        
        if result['status'] == 'success':
            print(f"✓ Sent successfully")
        else:
            print(f"✗ Error: {result['message']}")
        
        # Random delay between messages
        if i < len(messages):
            delay = random.randint(MESSAGE_DELAY_MIN, MESSAGE_DELAY_MAX)
            print(f"⏱️  Waiting {delay}s...")
            time.sleep(delay)
    
    return results
