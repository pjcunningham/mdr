import asyncio
import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import flet as ft
from mdr.main import main

@pytest.mark.asyncio
async def test_page_initialization():
    errors = []
    async def test_app(page: ft.Page):
        def on_error(e):
            errors.append(f"Flet page error: {e.data}")
            
        page.on_error = on_error
        try:
            # Call main with a real but isolated page object
            await main(page)
            
            # Verify page properties set in main
            assert page.title == "Markdown Reader"
            assert page.theme_mode == ft.ThemeMode.DARK
            
            # Verify UI components presence
            assert len(page.controls) > 0
            assert isinstance(page.controls[0], ft.Markdown)
            assert page.appbar is not None
            assert page.appbar.title.value == "Markdown Reader"
            
            # FilePicker is NOT in overlay anymore by default in initialization
            # It's created on-demand in open_file
            assert not any(isinstance(c, ft.FilePicker) for c in page.overlay)
            
            # Verify that page.update() works
            page.update()
            
        except Exception as ex:
            errors.append(ex)

    await ft.run_async(test_app, view=ft.AppView.FLET_APP_HIDDEN)
    if errors:
        raise errors[0]

@pytest.mark.asyncio
async def test_theme_toggle():
    errors = []
    async def test_app(page: ft.Page):
        def on_error(e):
            errors.append(f"Flet page error: {e.data}")
            
        page.on_error = on_error
        try:
            await main(page)
            
            # Initial state should be DARK
            assert page.theme_mode == ft.ThemeMode.DARK
            
            # Find the toggle button
            toggle_btn = None
            for action in page.appbar.actions:
                if isinstance(action, ft.IconButton) and action.tooltip == "Toggle Light/Dark Mode":
                    toggle_btn = action
                    break
            
            assert toggle_btn is not None
            
            # Trigger toggle
            toggle_theme_coro = toggle_btn.on_click(None)
            if asyncio.iscoroutine(toggle_theme_coro):
                await toggle_theme_coro
            assert page.theme_mode == ft.ThemeMode.LIGHT
            
            # Trigger toggle again
            toggle_theme_coro = toggle_btn.on_click(None)
            if asyncio.iscoroutine(toggle_theme_coro):
                await toggle_theme_coro
            assert page.theme_mode == ft.ThemeMode.DARK
        except Exception as ex:
            errors.append(ex)

    await ft.run_async(test_app, view=ft.AppView.FLET_APP_HIDDEN)
    if errors:
        raise errors[0]
