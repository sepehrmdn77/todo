from typing import Optional

import flet as ft

from api.client import ApiError, AuthenticationError
from features.auth.service import AuthService
from features.tasks.models import CategorySummary, Task
from features.tasks.service import TaskService
from shared import theme
from shared.ui import navigate, report_error

EMPTY_ALL = "No tasks yet. Tap + to add your first one."
EMPTY_FILTERED = "No tasks in this category yet."


class HomeView:
    """Main screen: slide-out profile drawer, category cards with progress, and the task list."""

    def __init__(self, page: ft.Page, auth: AuthService, tasks: TaskService) -> None:
        self._page = page
        self._auth = auth
        self._tasks = tasks
        self._all_tasks: list[Task] = []
        self._summaries: list[CategorySummary] = []
        self._selected_category: Optional[str] = None
        self._load_error: Optional[str] = None
        self._categories_row = ft.Row(scroll=ft.ScrollMode.AUTO)
        self._task_list = ft.Column(height=400, spacing=10, scroll=ft.ScrollMode.AUTO)
        self._main_panel = self._build_main_panel()

    async def build(self) -> ft.View:
        """Load data, then return the view. AuthenticationError propagates to the router."""
        await self._load()
        self._render()
        return ft.View(route="/", padding=0, bgcolor=theme.BG, controls=[self._build_layout()])

    # ---- data -------------------------------------------------------------------------

    async def _load(self) -> None:
        try:
            self._all_tasks = await self._tasks.list_tasks()
            self._summaries = await self._tasks.category_summary()
            self._load_error = None
        except AuthenticationError:
            raise
        except ApiError as exc:
            self._load_error = exc.message

    async def _reload(self, _=None) -> None:
        try:
            await self._load()
        except AuthenticationError as exc:
            report_error(self._page, exc)
            return
        self._render()
        self._page.update()

    # ---- rendering --------------------------------------------------------------------

    def _render(self) -> None:
        self._categories_row.controls = [self._category_card(summary) for summary in self._summaries]
        if self._load_error:
            self._task_list.controls = [
                ft.Text(self._load_error, color=theme.TEXT),
                ft.Button(content="Try again", icon=ft.Icons.REFRESH, on_click=self._reload),
            ]
            return
        visible = [t for t in self._all_tasks if self._selected_category in (None, t.category)]
        if visible:
            self._task_list.controls = [self._task_row(task) for task in visible]
        else:
            empty = EMPTY_FILTERED if self._selected_category else EMPTY_ALL
            self._task_list.controls = [ft.Text(empty, color=theme.MUTED)]

    def _category_card(self, summary: CategorySummary) -> ft.Control:
        selected = summary.category == self._selected_category

        def toggle_filter(_=None) -> None:
            self._selected_category = None if selected else summary.category
            self._render()
            self._page.update()

        return ft.Container(
            border_radius=20,
            bgcolor=theme.BG,
            border=ft.Border.all(2, theme.TEXT) if selected else None,
            width=170,
            height=110,
            padding=15,
            ink=True,
            tooltip=f"Show only {summary.label} tasks" if not selected else "Show all tasks",
            on_click=toggle_filter,
            content=ft.Column(
                controls=[
                    ft.Text(f"{summary.total} tasks", color=theme.MUTED),
                    ft.Text(summary.label, size=18, weight=ft.FontWeight.W_600, color=theme.TEXT),
                    ft.ProgressBar(value=summary.progress, color=theme.PINK, bgcolor=theme.TRACK,
                                   bar_height=5, border_radius=20),
                ]
            ),
        )

    def _task_row(self, task: Task) -> ft.Control:
        accent = theme.CATEGORY_COLORS.get(task.category or "", theme.PURPLE)
        checkbox = ft.Checkbox(
            value=task.is_completed,
            shape=ft.CircleBorder(),
            active_color=theme.PINK,
            check_color=theme.TEXT,
            border_side=ft.BorderSide(2, accent),
            tooltip="Mark as not done" if task.is_completed else "Mark as done",
            semantics_label=f"{task.title}, {'done' if task.is_completed else 'not done'}",
        )

        async def toggle_done(_=None) -> None:
            try:
                await self._tasks.set_completed(task.id, bool(checkbox.value))
            except ApiError as exc:
                checkbox.value = task.is_completed
                self._page.update()
                report_error(self._page, exc)
                return
            await self._reload()

        def open_editor(_=None) -> None:
            navigate(self._page, f"/tasks/{task.id}")

        checkbox.on_change = toggle_done
        return ft.Container(
            height=70,
            width=theme.PANEL_WIDTH,
            bgcolor=theme.BG,
            border_radius=25,
            padding=ft.Padding.only(left=12, right=4),
            content=ft.Row(
                controls=[
                    checkbox,
                    ft.Container(
                        expand=True,
                        on_click=open_editor,
                        content=ft.Text(
                            task.title,
                            size=17,
                            weight=ft.FontWeight.W_300,
                            color=theme.MUTED if task.is_completed else theme.TEXT,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                    ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_color=theme.TEXT, tooltip="Edit task",
                                  on_click=open_editor),
                ]
            ),
        )

    # ---- layout -----------------------------------------------------------------------

    def _build_layout(self) -> ft.Control:
        return ft.Container(
            width=theme.PANEL_WIDTH,
            height=theme.PANEL_HEIGHT,
            bgcolor=theme.BG,
            border_radius=35,
            content=ft.Stack(
                controls=[
                    self._build_profile_panel(),
                    ft.Row(alignment=ft.MainAxisAlignment.END, controls=[self._main_panel]),
                ]
            ),
        )

    def _build_main_panel(self) -> ft.Container:
        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(icon=ft.Icons.MENU, icon_color=theme.TEXT, tooltip="Open menu",
                              on_click=self._open_drawer),
                ft.IconButton(icon=ft.Icons.REFRESH, icon_color=theme.TEXT, tooltip="Refresh",
                              on_click=self._reload),
            ],
        )
        return ft.Container(
            width=theme.PANEL_WIDTH,
            height=theme.PANEL_HEIGHT,
            bgcolor=theme.FG,
            border_radius=35,
            animate=ft.Animation(600, ft.AnimationCurve.DECELERATE),
            animate_scale=ft.Animation(400, ft.AnimationCurve.DECELERATE),
            padding=ft.Padding.only(top=50, left=20, right=20, bottom=5),
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(height=20),
                    ft.Text(f"What's up, {self._auth.username}!", size=30, weight=ft.FontWeight.W_700,
                            color=theme.TEXT),
                    ft.Text("CATEGORIES", color=theme.MUTED),
                    ft.Container(padding=ft.Padding.only(top=10, bottom=20), content=self._categories_row),
                    ft.Text("TASKS", color=theme.MUTED),
                    ft.Stack(
                        controls=[
                            self._task_list,
                            ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=theme.PINK, tooltip="Add task",
                                                    bottom=2, right=20,
                                                    on_click=lambda _: navigate(self._page, "/tasks/new")),
                        ]
                    ),
                ]
            ),
        )

    def _build_profile_panel(self) -> ft.Control:
        def log_out(_=None) -> None:
            self._auth.logout()
            navigate(self._page, "/login")

        return ft.Container(
            width=theme.PANEL_WIDTH,
            height=theme.PANEL_HEIGHT,
            bgcolor=theme.BG,
            border_radius=35,
            padding=ft.Padding.only(left=40, top=60, right=200),
            content=ft.Column(
                spacing=16,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, tooltip="Close menu",
                                  on_click=self._close_drawer),
                    ft.CircleAvatar(foreground_image_src=theme.AVATAR_IMAGE, radius=45),
                    ft.Text(self._auth.username or "", size=24, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.TextButton(content="Log out", icon=ft.Icons.LOGOUT, on_click=log_out),
                ],
            ),
        )

    def _open_drawer(self, _=None) -> None:
        self._main_panel.width = theme.DRAWER_PANEL_WIDTH
        self._main_panel.scale = ft.Scale(0.8, alignment=ft.Alignment.CENTER_RIGHT)
        self._main_panel.border_radius = ft.BorderRadius.only(top_left=35, bottom_left=35)
        self._main_panel.update()

    def _close_drawer(self, _=None) -> None:
        self._main_panel.width = theme.PANEL_WIDTH
        self._main_panel.scale = ft.Scale(1, alignment=ft.Alignment.CENTER_RIGHT)
        self._main_panel.border_radius = 35
        self._main_panel.update()
