"""Small UI helpers shared by all features."""

import flet as ft

from api.client import ApiError, AuthenticationError

LOGIN_ROUTE = "/login"


def navigate(page: ft.Page, route: str) -> None:
    """Navigate from any handler (sync or async) without blocking it."""
    page.run_task(page.push_route, route)


def show_message(page: ft.Page, message: str) -> None:
    page.show_dialog(ft.SnackBar(content=ft.Text(message), show_close_icon=True))


def report_error(page: ft.Page, error: ApiError) -> None:
    """Show a user-safe message; send the user to login if their session ended."""
    show_message(page, error.message)
    if isinstance(error, AuthenticationError):
        navigate(page, LOGIN_ROUTE)
