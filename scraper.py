from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.action_chains import ActionChains


def click_at_coordinates(driver, x, y):
    """Clicks at the specified x, y pixel coordinates using JavaScript."""
    try:
        # Click using JavaScript at the specific coordinates
        driver.execute_script(f"document.elementFromPoint({x}, {y}).click();")
        print(f"Clicked at ({x}, {y})")
        time.sleep(3)  # Wait for the page to load after click
    except Exception as e:
        print(f"Error clicking at ({x}, {y}): {e}")

def scrape_brightspace(username, password):
    options = Options()
    options.add_argument("--window-size=1920,1080")  # Set window size to capture full page

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:    
        driver.get("https://purdue.brightspace.com/")
        time.sleep(10)

        wait = WebDriverWait(driver, 10)

        # **Step 1: Wait for the first shadow host**
        shadow_host = wait.until(EC.presence_of_element_located((By.TAG_NAME, "d2l-html-block")))

        # **Step 2: Find Login Button in Shadow Root**
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        login_button = shadow_root.find_element(By.CSS_SELECTOR, 'a[title="Purdue West Lafayette Login"]')
        login_button.click()

        # **Step 3: Login Process**
        username_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))

        username_element.send_keys(username)
        password_element = driver.find_element(By.ID, "password")
        password_element.send_keys(password)

        submit_button = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
        submit_button.click()
        time.sleep(10)

        # **Step 5: Wait for Homepage to Load**
        WebDriverWait(driver, 15).until(EC.title_contains("Homepage - Purdue West Lafayette"))
        time.sleep(5)
        print("Logged in successfully!")

        # **Step 6: Scroll to the courses section**
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(10)

        # **Step 7: Manually define the pixel coordinates for the course links**
        # Replace these pixel coordinates with the exact ones where the courses are located
        course_coordinates = [
            (206, 625+500),  # Example course 1 location
            (519, 625+500),  # Example course 2 location
            (916, 625+500),  # Example course 3 location
            (206, 1034+500),  # Example course 1 location
            (519, 1034+500),  # Example course 2 location
            (916, 1034+500)  # Example course 3 location
            # Add more coordinates as needed
        ]
        time.sleep(10)

        # **Step 8: Click on the defined coordinates**
        for x, y in course_coordinates:
            # Create an ActionChains object
            actions = ActionChains(driver)

            # Move the mouse to the desired coordinates and click
            actions.move_by_offset(x, y).click().perform()
            time.sleep(10)


    finally:
        driver.quit()

# Run the scraper
scrape_brightspace("gupt1206", "Thunder@0205?!")
