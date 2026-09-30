import pytest

from tasks.entities import CategorySummary, InvalidTaskError, TaskCategory, TaskNotFoundError
from tasks.services import TaskService
from tests.unit.fakes import InMemoryTaskRepository

OWNER_ID = 1
STRANGER_ID = 2


@pytest.fixture
def service():
    return TaskService(InMemoryTaskRepository())


def test_create_task_should_return_stored_task_with_id(service):
    task = service.create_task(OWNER_ID, title=" Essay ", category=TaskCategory.UNIVERSITY)
    assert task.id is not None
    assert task.title == "Essay"
    assert service.get_task(OWNER_ID, task.id).category is TaskCategory.UNIVERSITY


def test_create_task_should_reject_blank_title(service):
    with pytest.raises(InvalidTaskError):
        service.create_task(OWNER_ID, title="  ")


def test_get_task_should_hide_other_users_tasks(service):
    task = service.create_task(OWNER_ID, title="Private")
    with pytest.raises(TaskNotFoundError):
        service.get_task(STRANGER_ID, task.id)


def test_list_tasks_should_filter_by_completion_and_category(service):
    service.create_task(OWNER_ID, title="A", category=TaskCategory.FINNISH, is_completed=True)
    service.create_task(OWNER_ID, title="B", category=TaskCategory.FINNISH)
    service.create_task(OWNER_ID, title="C", category=TaskCategory.PAINTING, is_completed=True)
    titles = [t.title for t in service.list_tasks(OWNER_ID, completed=True, category=TaskCategory.FINNISH)]
    assert titles == ["A"]


def test_update_task_should_apply_partial_changes(service):
    task = service.create_task(OWNER_ID, title="Old", description="keep")
    updated = service.update_task(OWNER_ID, task.id, {"title": "New"})
    assert (updated.title, updated.description) == ("New", "keep")


def test_update_task_should_persist_marking_incomplete(service):
    task = service.create_task(OWNER_ID, title="Done", is_completed=True)
    service.update_task(OWNER_ID, task.id, {"is_completed": False})
    assert service.get_task(OWNER_ID, task.id).is_completed is False


def test_update_task_should_reject_other_users_task(service):
    task = service.create_task(OWNER_ID, title="Mine")
    with pytest.raises(TaskNotFoundError):
        service.update_task(STRANGER_ID, task.id, {"title": "Hacked"})


def test_delete_task_should_remove_task(service):
    task = service.create_task(OWNER_ID, title="Temp")
    service.delete_task(OWNER_ID, task.id)
    with pytest.raises(TaskNotFoundError):
        service.get_task(OWNER_ID, task.id)


def test_summarize_categories_should_zero_fill_every_category_in_order(service):
    service.create_task(OWNER_ID, title="A", category=TaskCategory.PAINTING, is_completed=True)
    service.create_task(OWNER_ID, title="B", category=TaskCategory.PAINTING)
    assert service.summarize_categories(OWNER_ID) == [
        CategorySummary(TaskCategory.UNIVERSITY, total=0, completed=0),
        CategorySummary(TaskCategory.FINNISH, total=0, completed=0),
        CategorySummary(TaskCategory.PAINTING, total=2, completed=1),
    ]
