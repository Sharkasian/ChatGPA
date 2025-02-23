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


def find_element_in_shadow_roots(driver, selectors):
    """
    Traverse multiple shadow roots to find the target element.
    :param driver: Selenium WebDriver
    :param selectors: List of tuples (shadow host selector, target element selector)
    :return: Final shadow DOM element or None
    """
    current_element = driver

    for i in range(len(selectors) - 1):
        shadow_host_selector = selectors[i]
        target_selector = selectors[i + 1]

        shadow_host = current_element.find_element(By.CSS_SELECTOR, shadow_host_selector)
        if not shadow_host:
            return None
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        if not shadow_root:
            return None
        current_element = shadow_root.find_element(By.CSS_SELECTOR, target_selector)
        if not current_element:
            return None

    return current_element

def scrape_brightspace(username, password):
    options = Options()
    options.add_argument("--window-size=1920,1080")  # Set window size to capture full page

    script = """
    window.clicks = [];
    document.addEventListener('click', function(event) {
    window.clicks.push({x: event.clientX, y: event.clientY});
    });
    """
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:    
        driver.get("https://purdue.brightspace.com/")
        wait = WebDriverWait(driver, 5)

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
        time.sleep(5)

        # **Step 5: Wait for Homepage to Load**
        WebDriverWait(driver, 5).until(EC.title_contains("Homepage - Purdue West Lafayette"))
        time.sleep(5)
        print("Logged in successfully!")

        # **Step 6: Scroll to the courses section**
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(3)

        # selectors = [
        #     "d2l-expand-collapse-content",       # Shadow Root 1
        #     "d2l-my-courses",     # Shadow Root 2
        #     "d2l-my-courses-container",   # Shadow Root 3
        #     "d2l-tabs",       # Shadow Root 4
        #     "d2l-tab-panel",     # Shadow Root 5
        #     "d2l-my-courses-content",        # Shadow Root 6 (Target element)
        #     "d2l-my-courses-card-grid",     # Shadow Root 7
        #     "d2l-enrollment-card",       # Shadow Root 8
        #     "d2l-card",     # Shadow Root 9
        # ]

        # # Get the final element inside all shadow roots
        # shadow_element = find_element_in_shadow_roots(driver, selectors)
        # if shadow_element:
        #     print("\n\n\nFound the target element!\n\n\n")
        # else:
        #     print("\n\n\nTarget element not found.\n\n\n")       


             
        # **Step 8: Manually define the pixel coordinates for the course links**
        # Replace these pixel coordinates with the exact ones where the courses are located
        course_coordinates = [
            (200, 300),
            (500, 300),
            (800, 300),
            (200, 600),
            (500, 600),
            (800, 600)
        ]  # Python list to store clicks

        # # **Step 8: Click on the def# ined coordinates**
        for x, y in course_coordinates:
            # Create an ActionChains obj#     ect
            actions = ActionChains(driver)
    
            # Move the mouse to the desired coordinates and click
            actions.move_by_offset(x, y).click().perform()
            time.sleep(3)

        time.sleep(5)
        print("All course links clicked successfully!")
        
    finally:
        driver.quit()

# Run the scraper
scrape_brightspace("deng312", "Edzt6921!")
