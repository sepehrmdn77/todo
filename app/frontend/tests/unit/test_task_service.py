import asyncio
import json

import httpx

from api.client import ApiClient
from features.tasks.models import TaskDraft
from features.tasks.service import TaskService

TASK_JSON = {"id": 1, "title": "Essay", "description": None, "category": "university",
             "is_completed": False, "created_date": "2026-09-30T10:00:00", "updated_date": "2026-09-30T10:00:00"}


def service_with(handler) -> TaskService:
    client = ApiClient("http://api.test", 5, transport=httpx.MockTransport(handler))
    client.set_tokens("a", "r")
    return TaskService(client)


def test_list_tasks_should_request_one_short_page_and_map_tasks():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[TASK_JSON])

    tasks = asyncio.run(service_with(handler).list_tasks())
    assert [t.title for t in tasks] == ["Essay"]
    assert len(requests) == 1
    assert requests[0].url.path == "/todo/tasks"
    assert (requests[0].url.params["limit"], requests[0].url.params["offset"]) == ("100", "0")


def test_list_tasks_should_fetch_every_page_until_a_short_one():
    offsets = []

    def handler(request):
        offsets.append(int(request.url.params["offset"]))
        rows = [{**TASK_JSON, "id": i} for i in range(100)] if offsets[-1] == 0 else [{**TASK_JSON, "id": 100}]
        return httpx.Response(200, json=rows)

    tasks = asyncio.run(service_with(handler).list_tasks())
    assert len(tasks) == 101
    assert offsets == [0, 100]


def test_create_task_should_post_draft_payload():
    def handler(request):
        assert request.method == "POST"
        assert json.loads(request.content) == {"title": "Essay", "description": None, "category": "university"}
        return httpx.Response(201, json=TASK_JSON)

    task = asyncio.run(service_with(handler).create_task(TaskDraft("Essay", "", "university")))
    assert task.id == 1


def test_update_task_should_patch_draft_payload():
    def handler(request):
        assert (request.method, request.url.path) == ("PATCH", "/todo/tasks/1")
        return httpx.Response(200, json=TASK_JSON)

    asyncio.run(service_with(handler).update_task(1, TaskDraft("Essay", "", None)))


def test_set_completed_should_patch_only_completion():
    def handler(request):
        assert json.loads(request.content) == {"is_completed": False}
        return httpx.Response(200, json=TASK_JSON)

    asyncio.run(service_with(handler).set_completed(1, False))


def test_delete_task_should_send_delete():
    def handler(request):
        assert (request.method, request.url.path) == ("DELETE", "/todo/tasks/1")
        return httpx.Response(204)

    assert asyncio.run(service_with(handler).delete_task(1)) is None


def test_category_summary_should_map_rows():
    def handler(request):
        assert request.url.path == "/todo/tasks/summary"
        return httpx.Response(200, json=[{"category": "finnish", "total": 2, "completed": 1}])

    [summary] = asyncio.run(service_with(handler).category_summary())
    assert (summary.category, summary.progress) == ("finnish", 0.5)
