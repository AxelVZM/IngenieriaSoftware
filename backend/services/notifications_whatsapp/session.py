"""
WhatsApp session management (login with QR)
"""
import time
import base64
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .config import WHATSAPP_URL
from .screenshots import save_screenshot

def check_login_status(driver):
    """Check if already logged in"""
    selectors = [
        '#pane-side',  # Main chat panel
        'div[data-testid="chat-list"]',
        'div[aria-label="Chat list"]',
        'div[data-testid="conversation-panel-wrapper"]',
    ]
    
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element.is_displayed():
                return True
        except NoSuchElementException:
            continue
    
    return False

def get_qr_base64(driver):
    """Capture QR code canvas and return as base64"""
    try:
        canvas = driver.find_element(By.CSS_SELECTOR, 'canvas[aria-label*="QR"]')
        canvas_base64 = driver.execute_script("""
            var canvas = arguments[0];
            return canvas.toDataURL('image/png').substring(22);
        """, canvas)
        return canvas_base64
    except Exception:
        # Fallback to any canvas or full screenshot
        try:
            canvases = driver.find_elements(By.TAG_NAME, "canvas")
            if canvases and canvases[0].is_displayed():
                return driver.execute_script("""
                    return arguments[0].toDataURL('image/png').substring(22);
                """, canvases[0])
        except Exception:
            pass
        screenshot = driver.get_screenshot_as_png()
        return base64.b64encode(screenshot).decode('utf-8')

def wait_for_login(driver):
    """Navigate to WhatsApp and wait dynamically for login or QR ready"""
    driver.get(WHATSAPP_URL)
    
    # Poll for login or QR ready up to 18 seconds
    start_time = time.time()
    while time.time() - start_time < 18:
        if check_login_status(driver):
            save_screenshot(driver, "success", "already_logged_in")
            return True
        
        # Check if QR canvas appeared
        try:
            canvases = driver.find_elements(By.TAG_NAME, "canvas")
            if canvases and canvases[0].is_displayed():
                time.sleep(0.5)  # brief settle time for QR rendering
                qr_base64 = get_qr_base64(driver)
                save_screenshot(driver, "qr", "qr_code")
                return qr_base64
        except Exception:
            pass
        
        time.sleep(0.8)
    
    # Final attempt fallback
    if check_login_status(driver):
        save_screenshot(driver, "success", "already_logged_in")
        return True
    
    qr_base64 = get_qr_base64(driver)
    save_screenshot(driver, "qr", "qr_code")
    return qr_base64

def verify_login(driver):
    """Verify login status without blocking unnecessarily"""
    if check_login_status(driver):
        save_screenshot(driver, "success", "login_verified")
        return True
    
    # Brief retry
    time.sleep(1)
    if check_login_status(driver):
        save_screenshot(driver, "success", "login_verified")
        return True
    
    return False
