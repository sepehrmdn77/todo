from features.tasks.models import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, CategorySummary, Task, TaskDraft


def test_task_from_api_should_map_fields():
    task = Task.from_api({"id": 3, "title": "T", "description": None, "category": "finnish",
                          "is_completed": True, "created_date": "x", "updated_date": "y"})
    assert task == Task(id=3, title="T", description=None, category="finnish", is_completed=True)


def test_draft_validate_should_require_title():
    assert "title" in TaskDraft(title="   ", description="", category=None).validate()


def test_draft_validate_should_limit_lengths():
    errors = TaskDraft(title="x" * (TITLE_MAX_LENGTH + 1), description="d" * (DESCRIPTION_MAX_LENGTH + 1),
                       category=None).validate()
    assert set(errors) == {"title", "description"}


def test_draft_validate_should_reject_unknown_category():
    assert "category" in TaskDraft(title="T", description="", category="cooking").validate()


def test_draft_to_payload_should_trim_and_null_blank_description():
    payload = TaskDraft(title="  Essay ", description="   ", category="university").to_payload()
    assert payload == {"title": "Essay", "description": None, "category": "university"}


def test_summary_progress_should_handle_empty_category():
    assert CategorySummary(category="finnish", total=0, completed=0).progress == 0.0
    assert CategorySummary(category="finnish", total=4, completed=1).progress == 0.25
    assert CategorySummary(category="finnish", total=4, completed=1).label == "Finnish"
