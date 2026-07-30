"""
Selenium WebDriver setup for WhatsApp notifications
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from .config import SELENIUM_URL

def setup_driver():
    """Configure and return Selenium WebDriver"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Connect to remote Selenium
    driver = webdriver.Remote(
        command_executor=SELENIUM_URL,
        options=options
    )
    
    return driver
