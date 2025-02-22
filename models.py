from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import time
from google.cloud import vision

def scrape_brightspace(username, password):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--window-size=1920,1080")  # Set window size to capture full page
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    try:    
        driver.get("https://purdue.brightspace.com/")
        time.sleep(10)
        
        # Accessing shadow DOM to find the login button
        wait = WebDriverWait(driver, 7)
        
        # **Step 1: Wait for the shadow host**
        shadow_host = wait.until(EC.presence_of_element_located((By.TAG_NAME, "d2l-html-block")))
        
        # **Step 2: Get shadow root using JavaScript**
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        
        # **Step 3: Wait for the element inside shadow DOM**
        login_button = WebDriverWait(driver, 10).until(
            lambda d: shadow_root.find_element(By.CSS_SELECTOR, 'a[title="Purdue West Lafayette Login"]')
        )
        
        # **Step 4: Click the login button**
        login_button.click()

        # Wait for username field and enter username
        username_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_element.send_keys(username)
        
        # Enter password
        password_element = driver.find_element(By.ID, "password")
        password_element.send_keys(password)
        
        # Try different possible submit button selectors
        try:
            submit_button = driver.find_element(By.ID, "submit")
        except:
            try:
                submit_button = driver.find_element(By.NAME, "submit")
            except:
                try:
                    submit_button = driver.find_element(By.CLASS_NAME, "submit-button")
                except:
                    submit_button = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
        
        submit_button.click()

        time.sleep(10)
        print("opened")
        
        # Scroll down the page
        driver.execute_script("window.scrollBy(0, 500);")  # Scroll down by 500 pixels
        time.sleep(2)  # Wait for the page to load

        # Capture the full page screenshot
        screenshot_path = "brightspace_courses.png"
        driver.get_screenshot_as_file(screenshot_path)

        # # Use Google Vision to extract text
        # extracted_text = extract_text_from_image(screenshot_path)

        # # Find course titles that start with "Spring 2025"
        # courses = [line for line in extracted_text.split("\n") if line.startswith("Spring 2025")]

        # print("Detected Courses:", courses)

        syllabus = []
        
    finally:
        driver.quit()

scrape_brightspace("gupt1206","Thunder@0205?!")