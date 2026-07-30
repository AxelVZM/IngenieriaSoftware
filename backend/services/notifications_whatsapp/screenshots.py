"""
Screenshot utilities
"""
import os
import glob
from datetime import datetime
from .config import QR_DIR, SUCCESS_DIR, ERROR_DIR

def cleanup_old_screenshots(directory):
    """Remove old screenshots, keep only the latest"""
    files = glob.glob(os.path.join(directory, "*.png"))
    # Delete all existing files
    for old_file in files:
        try:
            os.remove(old_file)
        except:
            pass

def save_screenshot(driver, screenshot_type, name):
    """Save screenshot to appropriate directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    
    if screenshot_type == "qr":
        path = os.path.join(QR_DIR, filename)
        cleanup_old_screenshots(QR_DIR)  # Delete old QR before saving
    elif screenshot_type == "success":
        path = os.path.join(SUCCESS_DIR, filename)
        cleanup_old_screenshots(SUCCESS_DIR)  # Delete old success before saving
    elif screenshot_type == "errors":
        path = os.path.join(ERROR_DIR, filename)
        # Don't cleanup errors - keep all
    else:
        return None
    
    driver.save_screenshot(path)
    return path
