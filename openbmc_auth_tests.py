import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

@pytest.fixture(scope="session")
def driver():
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')

    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 10)

def login(driver, wait, username: str, password: str):
    driver.get("https://localhost:2443/?next=/login#/login")
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
def test_successful_login(driver, wait):
    login(driver, wait, "root", "0penBmc")

    header = wait.until(
        EC.visibility_of_element_located((By.ID, "app-header-refresh"))
    )
    
    assert header.is_displayed(), "Авторизация не удалась"

def test_invalid_credentials(driver, wait):
    initial_url = "https://localhost:2443/?next=/login#/login"
    login(driver, wait, "wrong", "wrong")
    
    try:
        wait.until(EC.url_to_be(initial_url))
    except Exception:
        pytest.fail(f"Редирект на другую страницу. Текущий URL: {driver.current_url}")
    
    assert driver.current_url == initial_url, "Не произошел редирект на другую страницу при неверных данных"

def test_bun(driver, wait):
    username_field = wait.until(EC.visibility_of_element_located((By.ID, "username")))
    username_field.clear()
    password_field = driver.find_element(By.ID, "password")
    password_field.clear()

    expected_url = "https://127.0.0.1:2443/#/"

    login(driver, wait, "tester", "ClosedBmc")
    try:
        wait.until(EC.url_to_be(expected_url))
    except Exception:
        pytest.fail
    time.sleep(5)

    for _ in range (3):
        login(driver, wait, "tester", "Close453Bmc")
        time.sleep(5)
    
    login(driver, wait, "tester", "ClosedBmc")
    time.sleep(5)

    errorWindow = driver.find_element(By.CLASS_NAME, 'neterror')
    assert errorWindow.is_displayed()