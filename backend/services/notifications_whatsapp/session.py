"""
WhatsApp session management (login with QR)
"""
import time
import base64
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .config import WHATSAPP_URL, LOGIN_TIMEOUT
from .screenshots import save_screenshot

def check_login_status(driver):
    """Check if already logged in"""
    # Try multiple selectors (order matters)
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
    time.sleep(3)  # Wait for QR to load
    
    try:
        # Try to get QR canvas directly
        canvas = driver.find_element(By.CSS_SELECTOR, 'canvas[aria-label*="QR"]')
        
        # Get canvas as base64 using JavaScript
        canvas_base64 = driver.execute_script("""
            var canvas = arguments[0];
            return canvas.toDataURL('image/png').substring(22);
        """, canvas)
        
        return canvas_base64
    except:
        # Fallback: full screenshot
        screenshot = driver.get_screenshot_as_png()
        return base64.b64encode(screenshot).decode('utf-8')

def wait_for_login(driver):
    """Navigate to WhatsApp and wait for login"""
    driver.get(WHATSAPP_URL)
    time.sleep(8)  # Wait for page load
    
    # Check if already logged in (quick check, no extra wait)
    if check_login_status(driver):
        save_screenshot(driver, "success", "already_logged_in")
        return True
    
    # Return QR as base64
    qr_base64 = get_qr_base64(driver)
    save_screenshot(driver, "qr", "qr_code")
    
    return qr_base64

def verify_login(driver):
    """Verify login and save success screenshot"""
    time.sleep(3)  # Wait for login to complete
    
    if check_login_status(driver):
        save_screenshot(driver, "success", "login_verified")
        return True
    return False
