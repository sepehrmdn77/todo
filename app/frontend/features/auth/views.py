import flet as ft

from api.client import ApiError
from features.auth.service import AuthService
from features.auth.validation import USERNAME_MAX_LENGTH, validate_login, validate_registration
from shared import theme
from shared.ui import navigate, show_message


def _auth_view(route: str, heading: str, subheading: str, controls: list[ft.Control]) -> ft.View:
    card = ft.Container(
        width=360,
        padding=24,
        border_radius=24,
        bgcolor=theme.BG,
        content=ft.Column(
            tight=True,
            spacing=16,
            controls=[
                ft.Text(heading, size=28, weight=ft.FontWeight.W_700, color=theme.TEXT),
                ft.Text(subheading, color=theme.MUTED),
                *controls,
            ],
        ),
    )
    return ft.View(
        route=route,
        bgcolor=theme.FG,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[card],
    )


def _username_field() -> ft.TextField:
    return ft.TextField(label="Username", autofocus=True, max_length=USERNAME_MAX_LENGTH)


def _password_field(label: str = "Password") -> ft.TextField:
    return ft.TextField(label=label, password=True, can_reveal_password=True)


def build_login_view(page: ft.Page, auth: AuthService) -> ft.View:
    username = _username_field()
    password = _password_field()
    submit = ft.Button(content="Log in", icon=ft.Icons.LOGIN)

    async def log_in(_=None) -> None:
        errors = validate_login(username.value or "", password.value or "")
        username.error = errors.get("username")
        password.error = errors.get("password")
        if errors:
            page.update()
            return
        submit.disabled = True
        page.update()
        try:
            await auth.login(username.value, password.value)
        except ApiError as exc:
            submit.disabled = False
            page.update()
            show_message(page, exc.message)
            return
        await page.push_route("/")

    submit.on_click = log_in
    password.on_submit = log_in
    return _auth_view(
        "/login",
        "Welcome back",
        "Log in to see your tasks.",
        [
            username,
            password,
            submit,
            ft.TextButton(content="New here? Create an account", on_click=lambda _: navigate(page, "/register")),
        ],
    )


def build_register_view(page: ft.Page, auth: AuthService) -> ft.View:
    username = _username_field()
    password = _password_field()
    confirm = _password_field("Confirm password")
    submit = ft.Button(content="Create account", icon=ft.Icons.PERSON_ADD)

    async def register(_=None) -> None:
        errors = validate_registration(username.value or "", password.value or "", confirm.value or "")
        username.error = errors.get("username")
        password.error = errors.get("password")
        confirm.error = errors.get("confirm_password")
        if errors:
            page.update()
            return
        submit.disabled = True
        page.update()
        try:
            await auth.register(username.value, password.value, confirm.value)
        except ApiError as exc:
            submit.disabled = False
            page.update()
            show_message(page, exc.message)
            return
        await page.push_route("/")

    submit.on_click = register
    confirm.on_submit = register
    return _auth_view(
        "/register",
        "Create your account",
        "It takes ten seconds.",
        [
            username,
            password,
            confirm,
            submit,
            ft.TextButton(content="Already have an account? Log in", on_click=lambda _: navigate(page, "/login")),
        ],
    )
