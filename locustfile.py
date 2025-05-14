from locust import HttpUser, task

USERNAME = "root"
PASSWORD = "0penBmc"

class OpenBmcTestUser(HttpUser):
    host = "https://localhost:2443"

    def on_start(self):
        self.client.auth = (USERNAME, PASSWORD)
        self.client.verify = False

    @task(1)
    def system_info_test(self):
        self.client.get("/redfish/v1/Systems/system")

    @task(2)
    def pover_state_test(self):
        self.client.get("/redfish/v1/Systems/system/").json().get("PowerState")