import asyncio
import inspect
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
            assert len(page.controls) >= 2
            menu_bar = next(c for c in page.controls if isinstance(c, ft.MenuBar))
            assert menu_bar is not None
            assert len(menu_bar.controls) == 2
            assert menu_bar.controls[0].content.value == "File"
            assert menu_bar.controls[1].content.value == "Themes"
            
            # Verify shortcut label
            file_menu = menu_bar.controls[0]
            open_btn = file_menu.controls[0]
            assert open_btn.content.value == "Open"
            assert open_btn.trailing.value == "Ctrl+O"
            
            assert any(
                (isinstance(c, ft.Container) and isinstance(c.content, ft.Markdown)) or
                (isinstance(c, ft.Column) and any(isinstance(sc, ft.Container) and isinstance(sc.content, ft.Markdown) for sc in c.controls))
                for c in page.controls
            )
            
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
            
            # Find the Themes submenu
            menu_bar = next(c for c in page.controls if isinstance(c, ft.MenuBar))
            themes_menu = None
            for control in menu_bar.controls:
                if isinstance(control, ft.SubmenuButton) and control.content.value == "Themes":
                    themes_menu = control
                    break
            
            assert themes_menu is not None
            
            # Find Light and Dark menu items
            light_btn = None
            dark_btn = None
            for item in themes_menu.controls:
                if isinstance(item, ft.MenuItemButton) and item.content.value == "Light":
                    light_btn = item
                if isinstance(item, ft.MenuItemButton) and item.content.value == "Dark":
                    dark_btn = item
            
            assert light_btn is not None
            assert dark_btn is not None
            
            # Trigger Light mode
            toggle_coro = light_btn.on_click(None)
            if asyncio.iscoroutine(toggle_coro):
                await toggle_coro
            assert page.theme_mode == ft.ThemeMode.LIGHT
            
            # Trigger Dark mode
            toggle_coro = dark_btn.on_click(None)
            if asyncio.iscoroutine(toggle_coro):
                await toggle_coro
            assert page.theme_mode == ft.ThemeMode.DARK
        except Exception as ex:
            errors.append(ex)

    await ft.run_async(test_app, view=ft.AppView.FLET_APP_HIDDEN)
    if errors:
        raise errors[0]

@pytest.mark.asyncio
async def test_keyboard_shortcut():
    errors = []
    async def test_app(page: ft.Page):
        def on_error(e):
            errors.append(f"Flet page error: {e.data}")
            
        page.on_error = on_error
        try:
            await main(page)
            
            # Since we can't easily mock FilePicker.pick_files (it's inside open_file),
            # we just verify the keyboard event handler is set and call it.
            assert page.on_keyboard_event is not None
            
            # Simulate Ctrl+O
            # In some Flet versions KeyboardEvent is a simple class or a subclass of Event
            # Let's try to call it.
            # However, open_file will block on pick_files() which we can't easily bypass
            # without significant mocking.
            # For now, let's just ensure the event handler exists and is callable.
            # We don't await it because we didn't mock pick_files, but we verify it's there.
            assert inspect.iscoroutinefunction(page.on_keyboard_event)
            
        except Exception as ex:
            errors.append(ex)

    await ft.run_async(test_app, view=ft.AppView.FLET_APP_HIDDEN)
    if errors:
        raise errors[0]
