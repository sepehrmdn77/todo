import logging

import flet as ft

from api.client import ApiClient
from config import load_settings
from features.auth.service import AuthService
from features.tasks.service import TaskService
from router import Router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main(page: ft.Page) -> None:
    """One call per browser session: each session gets its own ApiClient (and tokens)."""
    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.request_timeout_seconds)
    router = Router(page, AuthService(client), TaskService(client))

    async def close_client(_=None) -> None:
        await client.close()

    page.title = "Todo"
    page.window.width = 420
    page.window.height = 870
    page.on_close = close_client
    page.on_route_change = router.handle_route_change
    await router.handle_route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
