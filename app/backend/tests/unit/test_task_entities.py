import pytest

from tasks.entities import (
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    InvalidTaskError,
    Task,
    TaskCategory,
)


def test_task_should_strip_title_and_description():
    task = Task(user_id=1, title="  Buy milk  ", description="  2 litres ")
    assert task.title == "Buy milk"
    assert task.description == "2 litres"


def test_task_should_reject_whitespace_only_title():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="   ")


def test_task_should_reject_title_longer_than_limit():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="x" * (TITLE_MAX_LENGTH + 1))


def test_task_should_store_blank_description_as_none():
    assert Task(user_id=1, title="Read", description="   ").description is None


def test_task_should_reject_description_longer_than_limit():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="Read", description="x" * (DESCRIPTION_MAX_LENGTH + 1))


def test_task_should_accept_category_given_as_string():
    assert Task(user_id=1, title="Verbs", category="finnish").category is TaskCategory.FINNISH


def test_task_should_reject_unknown_category():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="Verbs", category="cooking")


def test_apply_changes_should_only_touch_given_fields():
    task = Task(user_id=1, title="Old", description="keep", category=TaskCategory.GENERAL)
    task.apply_changes({"title": "New"})
    assert (task.title, task.description, task.category) == ("New", "keep", TaskCategory.GENERAL)


def test_apply_changes_should_allow_marking_incomplete():
    task = Task(user_id=1, title="Done already", is_completed=True)
    task.apply_changes({"is_completed": False})
    assert task.is_completed is False


def test_apply_changes_should_clear_description_and_category_with_none():
    task = Task(user_id=1, title="T", description="d", category=TaskCategory.FINNISH)
    task.apply_changes({"description": None, "category": None})
    assert task.description is None and task.category is None


def test_apply_changes_should_reject_null_title():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="T").apply_changes({"title": None})


def test_apply_changes_should_reject_null_completion():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="T").apply_changes({"is_completed": None})


def test_apply_changes_should_reject_unknown_fields():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="T").apply_changes({"user_id": 2})


def test_task_should_reject_control_character_in_title():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="a\x00b")


def test_task_should_reject_newline_in_title():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="a\nb")


def test_task_should_reject_nul_in_description():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="Read", description="a\x00b")


def test_task_should_allow_newline_and_tab_in_description():
    assert Task(user_id=1, title="Read", description="a\n\tb\r\nc").description == "a\n\tb\r\nc"
