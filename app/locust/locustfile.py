from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        response = self.client.post("/users/login", json={
            "username":"kazem",
            "password":"kazem"
        }
    )
        access_token = response.json()["access_token"]
        self.client.headers = {
            'Authorization': f'Bearer {access_token}',
            }

    @task
    def initial_task(self):
        self.client.get("/pages/public")

    @task
    def task_list(self):
        self.client.get("/todo/tasks?limit=10&offset=1")

    @task
    def not_found(self):
        self.client.get("/not-found")