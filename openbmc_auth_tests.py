import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Фикстура для инициализации и завершения работы драйвера
@pytest.fixture(scope="module")
def driver():
    # Настройка опций Chrome
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless") # Для CI

    service = Service(executable_path="/usr/bin/chromedriver")

    # Инициализация драйвера
    driver = webdriver.Chrome(service=service, options=options)
    yield driver  # Возвращаем драйвер тесту

    # Завершение работы драйвера после выполнения теста
    driver.quit()

# Тест для проверки авторизации
def test_success_login(driver):
    # Переход на страницу авторизации
    driver.get('https://localhost:2443/?next=/login#/login')
    time.sleep(3)  # Ожидание загрузки страницы

    # Поиск элементов на странице
    username = driver.find_element(By.ID, 'username')
    password = driver.find_element(By.ID, 'password')
    login_button = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.mt-3')

    # Ввод данных для авторизации
    username.send_keys('root')
    password.send_keys('0penBmc')

    # Нажатие кнопки входа
    login_button.click()
    time.sleep(3)  # Ожидание завершения авторизации

    successWindow = driver.find_element(By.CLASS_NAME, 'app-container')

    # Проверка успешной авторизации (пример проверки)
    assert successWindow.is_displayed()

def test_fail_login(driver):
    # Переход на страницу авторизации
    driver.get('https://localhost:2443/?next=/login#/login')
    time.sleep(3)

    username = driver.find_element(By.ID, 'username')
    password = driver.find_element(By.ID, 'password')
    login_button = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.mt-3')

    # Ввод данных для авторизации
    username.send_keys('root')
    password.send_keys('OpenBmc') # Не верный пароль

    login_button.click()
    time.sleep(3)

    errorWindow = driver.find_element(By.CLASS_NAME, 'neterror')

    assert errorWindow.is_displayed()

def test_block_user(driver):
    # Функция для попытки входа
    def attempt_login(username_value, password_value):
        driver.get('https://localhost:2443/?next=/login#/login')
        time.sleep(3)
        # Ожидание появления элементов формы
        username = driver.find_element(By.ID, 'username')
        password = driver.find_element(By.ID, 'password')
        login_button = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.mt-3')
        
        # Ввод данных для авторизации
        username.send_keys(username_value)
        password.send_keys(password_value)
        login_button.click()

    # Попытка входа с правильным паролем
    attempt_login('user', 'somepass1')  # Правильный пароль
    time.sleep(3)

    # Три попытки входа с неверным паролем
    for _ in range(3):
        attempt_login('user', 'OpenBmc')  # Неверный пароль
        time.sleep(3)

    # Попытка входа с правильным паролем
    attempt_login('user', 'somepass1')  # Правильный пароль
    time.sleep(3)

    errorWindow = driver.find_element(By.CLASS_NAME, 'neterror')

    assert errorWindow.is_displayed()