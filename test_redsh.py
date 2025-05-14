import pytest
import requests
import warnings
import logging
import time
from logging.handlers import RotatingFileHandler

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

file_handler = RotatingFileHandler(
    'redfish_tests.log', 
    maxBytes=0,
    backupCount=0,
    encoding='utf-8'
)

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG) 

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Добавляем обработчики к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Фикстура конфигурации для аутенфикации в Bmc
@pytest.fixture(scope="session")
def bmc_config():
    return {
        "username": "root",
        "password": "0penBmc",
        "verify_ssl": False,
        "base_url": "https://127.0.0.1:2443"
    }

# Фикстура Sessions
@pytest.fixture
def session_url(bmc_config):
    return f"{bmc_config['base_url']}/redfish/v1/SessionService/Sessions"

# Фикстура System
@pytest.fixture
def systems_url(bmc_config):
    return f"{bmc_config['base_url']}/redfish/v1/Systems/system"

# Фикстура автоматического создания и закрытия сессии
@pytest.fixture(scope="function")
def auth_session(bmc_config, session_url):
    session = requests.Session()
    session.verify = bmc_config["verify_ssl"]
    logger.info("Инициализация новой сессии")

    # Явно указываем url для правильного закрытия сессии
    base_url = session_url.split("/redfish")[0]

    # Передаём конфиг Bmc
    response = session.post(
        session_url,
        json={
            "UserName": bmc_config["username"],
            "Password": bmc_config["password"]
        },
        headers={"Content-Type": "application/json"}
    )
    
    # Внутренняя проверка статуса
    if response.status_code != 201:
        logger.error(f"Ошибка аутентификации: {response.text}")
        pytest.fail(f"Authentication failed: {response.text}")
    
    # Внутренняя проверка токена
    session.headers.update({
        "X-Auth-Token": response.headers["X-Auth-Token"]
    })
    logger.info("Сессия успешно создана")
    
    yield session
    
    # Удаление сессии
    location = response.headers["Location"]
    try:
        delete_url = f"{base_url}{location}"
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", requests.packages.urllib3.exceptions.InsecureRequestWarning)
            session.delete(delete_url)
        logger.info("Сессия успешно удалена")
    except Exception as e:
            logger.error(f"Ошибка при удалении сессии: {str(e)}")

# Тест на аутенфикацию
def test_correct_sessions(auth_session, session_url, bmc_config):
    logger.info("Запуск теста аутентификации")
    
    # Доп. создание сессии, т.к. нужно вытащить статус и токен в тесте
    response = auth_session.post(
        session_url,
        json={
            "UserName": bmc_config["username"],
            "Password": bmc_config["password"]
        },
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 201, f"Ожидался статус 201, получен {response.status_code}"
    assert "X-Auth-Token" in response.headers
    logger.info("Аутентификация прошла успешно")

# Тест получения информации о системе
def test_systems_with_session(auth_session, systems_url):
    logger.info("Запуск теста получения информации о системе")
    response = auth_session.get(systems_url)
    response.raise_for_status()
    system_data = response.json()
    logger.debug(f"Ответ сервера: {system_data}")
    assert response.status_code == 200   
    assert "Status" in system_data, "Отсутствует поле Status в ответе"
    assert "PowerState" in system_data, "Отсутствует поле PowerState в ответе"
    logger.info("Основные поля присутствуют в ответе")

# Тест управления питанием
def test_power_management(auth_session, systems_url):
    
    logger.info("Запуск теста управления питанием")

    # Дополняем url
    reset_url = f"{systems_url}/Actions/ComputerSystem.Reset"

    # Включение системы
    response = auth_session.post(
        reset_url,
        json={"ResetType": "On"},
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 202, (
        f"Ожидался статус 202 Accepted, получен {response.status_code}. " # !!!Bmc возвращвет статус 204!!!
        f"Ответ сервера: {response.text}"
    )
    logger.info("Команда включения принята")

    timeout = 60  
    start_time = time.time()

    # Ожидаем включени системы     
    while time.time() - start_time < timeout:
        response = auth_session.get(systems_url)
        system_data = response.json()
            
        if system_data.get("PowerState") == "On":
            logger.info("Система включена")
            break
            
        logger.debug("Ожидание изменения статуса...")
        time.sleep(5)
    else:
        logger.error("Таймаут ожидания включения системы")
        pytest.fail("Система не включилась в течение заданного времени")

# Обработка ошибок
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):

    # Обработки результатов тестов
    outcome = yield
    result = outcome.get_result()

    if result.when == "call" and result.failed:
        logger.error(f"Тест {item.name} провален с ошибкой: {result.longrepr}")

if __name__ == "__main__":
    logger.info("Запуск тестовой сессии")
    pytest.main(["-v", __file__])
    logger.info("Завершение тестовой сессии")
