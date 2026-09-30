import flet as ft

from api.client import ApiError
from features.auth.animated_background import AnimatedBackground
from features.auth.service import AuthService
from features.auth.validation import validate_login, validate_registration
from shared import theme
from shared.ui import navigate, show_message


def _auth_view(route: str, heading: str, subheading: str, controls: list[ft.Control]) -> ft.View:
    """Dark screen with twinkling dots and a translucent card (design from flet/learn/animated_login.py)."""
    card = ft.Container(
        width=400,
        padding=15,
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.045, theme.AUTH_TEXT),
        shadow=ft.BoxShadow(spread_radius=20, blur_radius=45, color=ft.Colors.with_opacity(0.45, "black")),
        content=ft.Column(
            tight=True,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Text(heading, size=20, weight=ft.FontWeight.W_600, color=theme.AUTH_TEXT),
                ft.Text(subheading, size=12, color=theme.AUTH_MUTED),
                ft.Divider(height=5, color="transparent"),
                *controls,
            ],
        ),
    )
    return ft.View(
        route=route,
        bgcolor=theme.AUTH_BG,
        padding=0,
        controls=[
            ft.Stack(
                expand=True,
                controls=[
                    AnimatedBackground(),
                    ft.Column(
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[card])],
                    ),
                ],
            )
        ],
    )


def _input(password: bool = False, autofocus: bool = False) -> ft.TextField:
    return ft.TextField(
        password=password,
        can_reveal_password=password,
        autofocus=autofocus,
        focused_border_color=theme.AUTH_ACCENT,
        border_radius=5,
        border_width=1.5,
        cursor_height=16,
        cursor_color=theme.AUTH_TEXT,
        content_padding=10,
        text_size=12,
        color=theme.AUTH_TEXT,
    )


def _labeled(label: str, field: ft.TextField) -> ft.Control:
    return ft.Column(
        spacing=4,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[ft.Text(label, size=10, color=theme.AUTH_TEXT), field],
    )


def _submit_button(text: str) -> ft.Button:
    return ft.Button(
        content=text,
        expand=True,
        height=38,
        bgcolor=theme.AUTH_ACCENT,
        color=theme.AUTH_TEXT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
    )


def _switch_link(text: str, on_click) -> ft.TextButton:
    return ft.TextButton(content=ft.Text(text, size=12, color=theme.AUTH_MUTED), on_click=on_click)


def build_login_view(page: ft.Page, auth: AuthService) -> ft.View:
    username = _input(autofocus=True)
    password = _input(password=True)
    submit = _submit_button("Sign In")

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
        "Sign in to see your tasks.",
        [
            _labeled("Username", username),
            _labeled("Password", password),
            ft.Divider(height=5, color="transparent"),
            ft.Row(controls=[submit]),
            _switch_link("New here? Create an account", lambda _: navigate(page, "/register")),
        ],
    )


def build_register_view(page: ft.Page, auth: AuthService) -> ft.View:
    username = _input(autofocus=True)
    password = _input(password=True)
    confirm = _input(password=True)
    submit = _submit_button("Create account")

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
            _labeled("Username", username),
            _labeled("Password", password),
            _labeled("Confirm password", confirm),
            ft.Divider(height=5, color="transparent"),
            ft.Row(controls=[submit]),
            _switch_link("Already have an account? Sign in", lambda _: navigate(page, "/login")),
        ],
    )
