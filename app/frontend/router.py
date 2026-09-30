import re
from typing import Optional

import flet as ft

from api.client import ApiError, AuthenticationError
from features.auth.service import AuthService
from features.auth.views import build_login_view, build_register_view
from features.tasks.form_view import build_task_form_view
from features.tasks.home_view import HomeView
from features.tasks.service import TaskService
from shared.ui import show_message

HOME_ROUTE = "/"
LOGIN_ROUTE = "/login"
REGISTER_ROUTE = "/register"
NEW_TASK_ROUTE = "/tasks/new"
PUBLIC_ROUTES = frozenset({LOGIN_ROUTE, REGISTER_ROUTE})
EDIT_TASK_ROUTE = re.compile(r"^/tasks/(?P<task_id>[1-9][0-9]{0,9})$")


class Router:
    """Maps page.route to a view and enforces the signed-in guard."""

    def __init__(self, page: ft.Page, auth: AuthService, tasks: TaskService) -> None:
        self._page = page
        self._auth = auth
        self._tasks = tasks

    async def handle_route_change(self, _event: Optional[ft.RouteChangeEvent] = None) -> None:
        route = self._page.route or HOME_ROUTE
        redirect = self._guard(route)
        if redirect:
            await self._page.push_route(redirect)
            return
        try:
            view = await self._build_view(route)
        except AuthenticationError as exc:
            self._auth.logout()
            show_message(self._page, exc.message)
            await self._page.push_route(LOGIN_ROUTE)
            return
        if view is None:
            await self._page.push_route(HOME_ROUTE)
            return
        self._page.views.clear()
        self._page.views.append(view)
        self._page.update()

    def _guard(self, route: str) -> Optional[str]:
        if route not in PUBLIC_ROUTES and not self._auth.is_authenticated:
            return LOGIN_ROUTE
        if route in PUBLIC_ROUTES and self._auth.is_authenticated:
            return HOME_ROUTE
        return None

    async def _build_view(self, route: str) -> Optional[ft.View]:
        """Return the view for `route`, or None to send the user home."""
        if route == LOGIN_ROUTE:
            return build_login_view(self._page, self._auth)
        if route == REGISTER_ROUTE:
            return build_register_view(self._page, self._auth)
        if route == NEW_TASK_ROUTE:
            return build_task_form_view(self._page, self._tasks, task=None)
        match = EDIT_TASK_ROUTE.match(route)
        if match:
            return await self._build_edit_view(int(match["task_id"]))
        if route == HOME_ROUTE:
            return await HomeView(self._page, self._auth, self._tasks).build()
        return None

    async def _build_edit_view(self, task_id: int) -> Optional[ft.View]:
        try:
            task = await self._tasks.get_task(task_id)
        except AuthenticationError:
            raise
        except ApiError as exc:
            show_message(self._page, exc.message)
            return None
        return build_task_form_view(self._page, self._tasks, task=task)
