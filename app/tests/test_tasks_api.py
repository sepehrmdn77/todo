
def test_tasks_list_404(anonymous_client):

    response = anonymous_client.get("/tasks")
    assert response.status_code == 404

# def test_tasks_list_200(auth_client):
#     response = auth_client.get("/tasks")
#     assert response.status_code == 200
#     assert len(response.json()) > 0

# def test_tasks_list_200(auth_client, random_task):
#     task_obj = random_task
#     response = auth_client.get(f"/tasks/{task_obj.id}")
#     assert response.status_code == 200
#     assert len(response.json()) > 0
