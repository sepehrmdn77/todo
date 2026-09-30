from api.client import ApiClient
from features.tasks.models import CategorySummary, Task, TaskDraft

TASKS_PATH = "/todo/tasks"
PAGE_SIZE = 100  # backend maximum; one page is plenty for a personal todo list


class TaskService:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def list_tasks(self) -> list[Task]:
        rows = await self._client.request("GET", TASKS_PATH, params={"limit": PAGE_SIZE})
        return [Task.from_api(row) for row in rows]

    async def get_task(self, task_id: int) -> Task:
        return Task.from_api(await self._client.request("GET", f"{TASKS_PATH}/{task_id}"))

    async def create_task(self, draft: TaskDraft) -> Task:
        return Task.from_api(await self._client.request("POST", TASKS_PATH, json=draft.to_payload()))

    async def update_task(self, task_id: int, draft: TaskDraft) -> Task:
        return Task.from_api(await self._client.request("PATCH", f"{TASKS_PATH}/{task_id}", json=draft.to_payload()))

    async def set_completed(self, task_id: int, completed: bool) -> Task:
        data = await self._client.request("PATCH", f"{TASKS_PATH}/{task_id}", json={"is_completed": completed})
        return Task.from_api(data)

    async def delete_task(self, task_id: int) -> None:
        await self._client.request("DELETE", f"{TASKS_PATH}/{task_id}")

    async def category_summary(self) -> list[CategorySummary]:
        rows = await self._client.request("GET", f"{TASKS_PATH}/summary")
        return [CategorySummary.from_api(row) for row in rows]
