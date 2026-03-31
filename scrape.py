from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests
import time

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

load_dotenv()

SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")
USE_BRIGHT_DATA = SBR_WEBDRIVER and SBR_WEBDRIVER.strip()


def scrape_website(website):
    """Scrape website using Bright Data or local Chrome"""
    # Validate URL
    if not website:
        raise ValueError("URL cannot be empty")
    if not website.startswith(("http://", "https://")):
        website = f"https://{website}"
    
    if USE_BRIGHT_DATA:
        return scrape_with_bright_data(website)
    else:
        return scrape_with_chrome(website)


def scrape_with_bright_data(website):
    """Scrape using Bright Data Scraping Browser"""
    print("Connecting to Bright Data Scraping Browser...")
    try:
        from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
        from selenium.webdriver import Remote, ChromeOptions
        
        sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
        with Remote(sbr_connection, options=ChromeOptions()) as driver:
            driver.get(website)
            print("Waiting for captcha to solve...")
            solve_res = driver.execute(
                "executeCdpCommand",
                {
                    "cmd": "Captcha.waitForSolve",
                    "params": {"detectTimeout": 10000},
                },
            )
            print("Captcha solve status:", solve_res["value"]["status"])
            print("Navigated! Scraping page content...")
            html = driver.page_source
            return html
    except Exception as e:
        print(f"Bright Data scraping failed: {e}")
        print("Falling back to local Chrome scraping...")
        return scrape_with_chrome(website)


def scrape_with_chrome(website):
    """Scrape using local Chrome/Chromium browser"""
    print(f"Starting Chrome browser for: {website}")
    driver = None
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Initialize webdriver
        print("Initializing WebDriver...")
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"WebDriver Manager failed: {e}. Trying without service...")
                driver = webdriver.Chrome(options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        driver.set_page_load_timeout(30)
        print(f"Navigating to {website}...")
        driver.get(website)
        
        # Wait for page to load
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("Page fully loaded!")
        except Exception as wait_error:
            print(f"Page load timeout: {wait_error}. Using current state.")
        
        time.sleep(2)  # Additional wait for JavaScript rendering
        html = driver.page_source
        return html
        
    except Exception as e:
        print(f"Error during scraping: {type(e).__name__}: {e}")
        raise
    finally:
        if driver:
            try:
                print("Closing browser...")
                driver.quit()
            except Exception as e:
                print(f"Error closing browser: {e}")


def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""


def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Get text or further process the content
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def split_dom_content(dom_content, max_length=2500):
    """
    Split content into smaller chunks for faster processing.
    Reduced from 6000 to 2500 for faster Ollama parsing.
    """
    chunks = []
    for i in range(0, len(dom_content), max_length):
        chunk = dom_content[i : i + max_length].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
    
    # Remove duplicate chunks
    unique_chunks = []
    seen = set()
    for chunk in chunks:
        chunk_hash = hash(chunk[:100])  # Use first 100 chars as hash
        if chunk_hash not in seen:
            seen.add(chunk_hash)
            unique_chunks.append(chunk)
    
    print(f"Split into {len(unique_chunks)} unique chunks (from {len(chunks)} total)")
    return unique_chunks
