TASKS_URL = "/todo/tasks"


def create(client, **fields):
    payload = {"title": "Write essay", **fields}
    response = client.post(TASKS_URL, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_tasks_should_require_authentication(anonymous_client):
    assert anonymous_client.get(TASKS_URL).status_code in (401, 403)


def test_create_task_should_return_201_with_defaults(auth_client):
    task = create(auth_client, category="university")
    assert task["title"] == "Write essay"
    assert task["category"] == "university"
    assert task["is_completed"] is False
    assert task["description"] is None


def test_create_task_should_reject_whitespace_title(auth_client):
    response = auth_client.post(TASKS_URL, json={"title": "   "})
    assert response.status_code == 422
    assert auth_client.get(TASKS_URL).json() == []


def test_create_task_should_reject_unknown_category(auth_client):
    assert auth_client.post(TASKS_URL, json={"title": "Cook", "category": "cooking"}).status_code == 422


def test_create_task_should_reject_unknown_fields(auth_client):
    assert auth_client.post(TASKS_URL, json={"title": "T", "user_id": 99}).status_code == 422


def test_list_tasks_should_include_first_task_by_default(auth_client):
    first = create(auth_client, title="First")
    assert [t["id"] for t in auth_client.get(TASKS_URL).json()] == [first["id"]]


def test_list_tasks_should_filter_by_category_and_completion(auth_client):
    create(auth_client, title="Verbs", category="finnish", is_completed=True)
    create(auth_client, title="Nouns", category="finnish")
    create(auth_client, title="Sketch", category="general", is_completed=True)
    response = auth_client.get(TASKS_URL, params={"category": "finnish", "completed": "true"})
    assert [t["title"] for t in response.json()] == ["Verbs"]


def test_list_tasks_should_reject_limit_over_100(auth_client):
    assert auth_client.get(TASKS_URL, params={"limit": 101}).status_code == 422


def test_get_task_should_return_404_for_other_users_task(auth_client, other_client):
    task = create(auth_client)
    response = other_client.get(f"{TASKS_URL}/{task['id']}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_patch_task_should_update_only_given_fields(auth_client):
    task = create(auth_client, description="keep me", category="general")
    response = auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"title": "Renamed"})
    assert response.status_code == 200
    body = response.json()
    assert (body["title"], body["description"], body["category"]) == ("Renamed", "keep me", "general")


def test_patch_task_should_persist_marking_incomplete(auth_client):
    task = create(auth_client, is_completed=True)
    auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"is_completed": False})
    assert auth_client.get(f"{TASKS_URL}/{task['id']}").json()["is_completed"] is False


def test_patch_task_should_clear_description_and_category_with_null(auth_client):
    task = create(auth_client, description="d", category="finnish")
    body = auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"description": None, "category": None}).json()
    assert body["description"] is None and body["category"] is None


def test_patch_task_should_reject_null_title(auth_client):
    task = create(auth_client)
    assert auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"title": None}).status_code == 422


def test_patch_task_should_return_404_for_other_users_task(auth_client, other_client):
    task = create(auth_client)
    assert other_client.patch(f"{TASKS_URL}/{task['id']}", json={"title": "Mine now"}).status_code == 404


def test_delete_task_should_return_204_then_404(auth_client):
    task = create(auth_client)
    assert auth_client.delete(f"{TASKS_URL}/{task['id']}").status_code == 204
    assert auth_client.get(f"{TASKS_URL}/{task['id']}").status_code == 404


def test_summary_should_count_per_category_zero_filled(auth_client):
    create(auth_client, title="Verbs", category="finnish", is_completed=True)
    create(auth_client, title="Nouns", category="finnish")
    create(auth_client, title="No category")
    assert auth_client.get(f"{TASKS_URL}/summary").json() == [
        {"category": "university", "total": 0, "completed": 0},
        {"category": "finnish", "total": 2, "completed": 1},
        {"category": "general", "total": 0, "completed": 0},
    ]


def test_create_task_should_reject_nul_in_title(auth_client):
    assert auth_client.post(TASKS_URL, json={"title": "a\u0000b"}).status_code == 422


def test_list_tasks_should_reject_offset_beyond_int32(auth_client):
    response = auth_client.get(TASKS_URL, params={"offset": 99999999999999999999})
    assert response.status_code == 422
