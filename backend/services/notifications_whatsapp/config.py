"""
WhatsApp notification service configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Selenium configuration
SELENIUM_URL = os.getenv("SELENIUM_URL", "http://localhost:4444")

# WhatsApp settings
WHATSAPP_URL = "https://web.whatsapp.com/"
LOGIN_TIMEOUT = 180  # seconds
MESSAGE_DELAY_MIN = 20  # seconds
MESSAGE_DELAY_MAX = 30  # seconds

# Screenshot paths (inside services/notifications_whatsapp/)
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
QR_DIR = os.path.join(SCREENSHOT_DIR, "qr")
SUCCESS_DIR = os.path.join(SCREENSHOT_DIR, "success")
ERROR_DIR = os.path.join(SCREENSHOT_DIR, "errors")

# Create directories
for directory in [QR_DIR, SUCCESS_DIR, ERROR_DIR]:
    os.makedirs(directory, exist_ok=True)

# Phone normalization
COUNTRY_CODE = "51"  # Peru
