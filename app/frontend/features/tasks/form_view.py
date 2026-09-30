from typing import Optional

import flet as ft

from api.client import ApiError
from features.tasks.models import CATEGORIES, CATEGORY_LABELS, DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, Task, TaskDraft
from features.tasks.service import TaskService
from shared import theme
from shared.ui import navigate, report_error, show_message

NO_CATEGORY = "none"


def build_task_form_view(page: ft.Page, tasks: TaskService, task: Optional[Task]) -> ft.View:
    """Create (task=None) or edit an existing task."""
    is_edit = task is not None
    title = ft.TextField(
        label="Title", value=task.title if task else "", max_length=TITLE_MAX_LENGTH, autofocus=True
    )
    description = ft.TextField(
        label="Description (optional)",
        value=(task.description or "") if task else "",
        multiline=True,
        min_lines=3,
        max_lines=6,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    category = ft.Dropdown(
        label="Category",
        value=(task.category if task and task.category else NO_CATEGORY),
        options=[ft.dropdown.Option(key=NO_CATEGORY, text="No category")]
        + [ft.dropdown.Option(key=key, text=CATEGORY_LABELS[key]) for key in CATEGORIES],
    )
    save = ft.Button(content="Save changes" if is_edit else "Add task", icon=ft.Icons.CHECK)

    def read_draft() -> TaskDraft:
        chosen = None if category.value in (None, NO_CATEGORY) else category.value
        return TaskDraft(title=title.value or "", description=description.value or "", category=chosen)

    async def submit(_=None) -> None:
        draft = read_draft()
        errors = draft.validate()
        title.error = errors.get("title")
        description.error = errors.get("description")
        category.error_text = errors.get("category")
        if errors:
            page.update()
            return
        save.disabled = True
        page.update()
        try:
            if task is None:
                await tasks.create_task(draft)
            else:
                await tasks.update_task(task.id, draft)
        except ApiError as exc:
            save.disabled = False
            page.update()
            report_error(page, exc)
            if exc.status_code == 404:  # task was deleted elsewhere: nothing left to edit
                await page.push_route("/")
            return
        show_message(page, "Task saved." if is_edit else "Task added.")
        await page.push_route("/")

    async def delete_confirmed(_=None) -> None:
        page.pop_dialog()
        try:
            await tasks.delete_task(task.id)
        except ApiError as exc:
            report_error(page, exc)
            if exc.status_code == 404:  # already gone
                await page.push_route("/")
            return
        show_message(page, "Task deleted.")
        await page.push_route("/")

    def confirm_delete(_=None) -> None:
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Delete this task?"),
                content=ft.Text("This can't be undone."),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda _: page.pop_dialog()),
                    ft.TextButton(content="Delete", on_click=delete_confirmed),
                ],
            )
        )

    save.on_click = submit
    title.on_submit = submit
    actions: list[ft.Control] = [save]
    if is_edit:
        actions.append(ft.OutlinedButton(content="Delete", icon=ft.Icons.DELETE_OUTLINE, on_click=confirm_delete))

    header = ft.Row(
        controls=[
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, tooltip="Back to tasks",
                          on_click=lambda _: navigate(page, "/")),
            ft.Text("Edit task" if is_edit else "New task", size=24, weight=ft.FontWeight.W_700, color=theme.TEXT),
        ]
    )
    return ft.View(
        route=f"/tasks/{task.id}" if is_edit else "/tasks/new",
        bgcolor=theme.FG,
        padding=20,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                width=theme.PANEL_WIDTH,
                content=ft.Column(spacing=16, controls=[header, title, description, category, ft.Row(actions)]),
            )
        ],
    )
