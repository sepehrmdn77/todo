"""Twinkling-dots background for the auth screens (ported from flet/learn/animated_login.py)."""

import asyncio
import random

import flet as ft

from shared import theme

DOT_COUNT = 50
DOT_SIZE = 2.5
MIN_POSITION = -100
MAX_POSITION = 2000
FADE_MS = 600
TICK_SECONDS = FADE_MS / 1000
TOGGLE_PROBABILITY = 0.5


def _dot() -> ft.Container:
    color = random.choice(theme.AUTH_DOT_COLORS)
    return ft.Container(
        left=random.randint(MIN_POSITION, MAX_POSITION),
        top=random.randint(MIN_POSITION, MAX_POSITION),
        width=DOT_SIZE,
        height=DOT_SIZE,
        shape=ft.BoxShape.CIRCLE,
        bgcolor=color,
        opacity=0,
        animate_opacity=ft.Animation(FADE_MS, ft.AnimationCurve.EASE),
        shadow=ft.BoxShadow(spread_radius=20, blur_radius=100, color=color),
    )


@ft.control
class AnimatedBackground(ft.Stack):
    """Dots fade in and out at random while the view is on screen.

    All dots change in one batched update per tick (instead of one update per dot),
    which keeps server-to-browser traffic low. The loop starts on mount and stops
    on unmount, so leaving the screen leaves nothing running.
    """

    def init(self) -> None:
        super().init()
        self.expand = True
        self.controls = [_dot() for _ in range(DOT_COUNT)]
        self._running = False

    def did_mount(self) -> None:
        super().did_mount()
        self._running = True
        self.page.run_task(self._twinkle)

    def will_unmount(self) -> None:
        self._running = False
        super().will_unmount()

    async def _twinkle(self) -> None:
        while self._running:
            for dot in self.controls:
                if random.random() < TOGGLE_PROBABILITY:
                    dot.opacity = 0 if dot.opacity else 1
            try:
                self.update()
            except RuntimeError:  # the view was removed between two ticks
                return
            await asyncio.sleep(TICK_SECONDS)
