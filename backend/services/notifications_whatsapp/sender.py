"""
WhatsApp message sender
"""
import time
import random
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
    """Send a single WhatsApp message handling popups and JS click dispatch"""
    phone = normalize_phone(phone)
    
    # Encode message in URL
    message_encoded = urllib.parse.quote(message)
    url = f"https://web.whatsapp.com/send?phone={phone}&text={message_encoded}"
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Check if invalid number dialog appears
        try:
            dialogs = driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"]')
            for dialog in dialogs:
                txt = dialog.text.lower()
                if "no es válido" in txt or "invalid" in txt or "no se pudo encontrar" in txt:
                    # Dismiss dialog
                    try:
                        ok_btn = dialog.find_element(By.CSS_SELECTOR, 'button')
                        driver.execute_script("arguments[0].click();", ok_btn)
                    except Exception:
                        pass
                    save_screenshot(driver, "errors", f"invalid_phone_{phone}")
                    return {
                        "phone": phone,
                        "status": "error",
                        "message": "El número de teléfono no es válido o no está registrado en WhatsApp"
                    }
        except Exception:
            pass
        
        # Find message input box
        wait = WebDriverWait(driver, 18)
        input_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][role="textbox"], div[data-testid="conversation-compose-box-input"]'))
        )
        
        # Focus input box safely with JavaScript to avoid element click interception
        driver.execute_script("arguments[0].focus();", input_box)
        time.sleep(1)
        
        # Press ENTER to send
        input_box.send_keys(Keys.ENTER)
        time.sleep(2)
        
        # Fallback: Find and click send button with JavaScript if still present
        send_selectors = [
            'button[aria-label="Enviar"]',
            'button[data-tab="11"]',
            'span[data-icon="send"]',
            'button[data-testid="compose-btn-send"]'
        ]
        
        for selector in send_selectors:
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, selector)
                if btns and btns[0].is_displayed():
                    driver.execute_script("arguments[0].click();", btns[0])
                    time.sleep(2)
                    break
            except Exception:
                continue
        
        time.sleep(3)
        
        # Screenshot after sending
        save_screenshot(driver, "success", "message_sent")
        
        return {"phone": phone, "status": "success", "message": "Enviado correctamente"}
        
    except Exception as e:
        save_screenshot(driver, "errors", f"error_{phone}")
        return {"phone": phone, "status": "error", "message": str(e)}

def send_messages(driver, messages):
    """Send multiple messages with delay"""
    results = []
    
    for i, msg in enumerate(messages, 1):
        print(f"\n[{i}/{len(messages)}] Enviando a {msg['phone']}...")
        
        result = send_message(driver, msg['phone'], msg['message'])
        results.append(result)
        
        if result['status'] == 'success':
            print(f"✓ Enviado exitosamente")
        else:
            print(f"✗ Error: {result['message']}")
        
        # Random delay between messages
        if i < len(messages):
            delay = random.randint(MESSAGE_DELAY_MIN, MESSAGE_DELAY_MAX)
            print(f"⏱️  Esperando {delay}s...")
            time.sleep(delay)
    
    return results
