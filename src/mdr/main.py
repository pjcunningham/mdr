import json
import os
from pathlib import Path

import flet as ft

MAX_RECENT_FILES = 10
DEFAULT_MARKDOWN = "# Welcome to Markdown Reader\nSelect a markdown file to view its content."


async def main(page: ft.Page):
    page.title = "Markdown Reader"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.padding = 0
    page.spacing = 0

    current_file_path = None
    recent_files_path = None

    md_view = ft.Markdown(
        value=DEFAULT_MARKDOWN,
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )

    recent_submenu = ft.SubmenuButton(
        content=ft.Text("Open Recent"),
        controls=[],
        leading=ft.Icon(ft.Icons.HISTORY),
    )

    def show_message(message: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()

    async def init_storage():
        nonlocal recent_files_path
        try:
            support_dir = await ft.StoragePaths().get_application_support_directory()
            app_dir = Path(support_dir) / "mdr"
            app_dir.mkdir(parents=True, exist_ok=True)
            recent_files_path = app_dir / "recent_files.json"
        except Exception as ex:
            show_message(f"Could not initialise app storage: {ex}")

    def read_recent_files_from_disk():
        if recent_files_path is None or not recent_files_path.exists():
            return []

        try:
            data = json.loads(recent_files_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return []
            return [str(p) for p in data if isinstance(p, str) and p.strip()]
        except Exception:
            return []

    def write_recent_files_to_disk(recent_files):
        if recent_files_path is None:
            return
        recent_files_path.write_text(
            json.dumps(recent_files, indent=2),
            encoding="utf-8",
        )

    async def get_recent_files():
        return read_recent_files_from_disk()

    async def set_recent_files(recent_files):
        try:
            write_recent_files_to_disk(recent_files)
        except Exception as ex:
            show_message(f"Could not save recent files: {ex}")

    async def clear_recent_files(e=None):
        await set_recent_files([])
        await update_recent_menu()

    async def update_recent_menu():
        recent_files = await get_recent_files()
        recent_submenu.controls.clear()

        if not recent_files:
            recent_submenu.controls.append(
                ft.MenuItemButton(
                    content=ft.Text("No recent files"),
                    disabled=True,
                )
            )
        else:
            for file_path in recent_files:
                recent_submenu.controls.append(
                    ft.MenuItemButton(
                        content=ft.Text(os.path.basename(file_path) or file_path),
                        data=file_path,
                        on_click=lambda e, path=file_path: page.run_task(open_recent_file, path),
                    )
                )

            recent_submenu.controls.append(ft.Divider())
            recent_submenu.controls.append(
                ft.MenuItemButton(
                    content=ft.Text("Clear Recent Files"),
                    leading=ft.Icon(ft.Icons.DELETE_SWEEP),
                    on_click=clear_recent_files,
                )
            )

        page.update()

    async def remember_recent_file(file_path):
        if not file_path:
            return

        recent_files = await get_recent_files()

        if file_path in recent_files:
            recent_files.remove(file_path)

        recent_files.insert(0, file_path)
        recent_files = recent_files[:MAX_RECENT_FILES]

        await set_recent_files(recent_files)
        await update_recent_menu()

    async def load_markdown_from_path(file_path, remember=True):
        nonlocal current_file_path

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            md_view.value = content or "# Empty file"
            current_file_path = file_path

            if remember:
                await remember_recent_file(file_path)

            page.update()

        except Exception as ex:
            show_message(f"Error opening file: {ex}")

    async def open_file(e):
        nonlocal current_file_path

        try:
            files = await ft.FilePicker().pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["md"],
            )
        except Exception as ex:
            show_message(f"File picker error: {ex}")
            return

        if not files:
            return

        selected = files[0]

        if getattr(selected, "path", None):
            await load_markdown_from_path(selected.path)
            return

        try:
            content = selected.bytes.decode("utf-8", errors="replace") if selected.bytes else ""
            md_view.value = content or "# Empty file"
            current_file_path = None
            page.update()
        except Exception as ex:
            show_message(f"Error reading file: {ex}")

    async def open_recent_file(file_path):
        await load_markdown_from_path(file_path)

    async def reload_file(e=None):
        if not current_file_path:
            show_message("No file is currently open to reload.")
            return
        await load_markdown_from_path(current_file_path, remember=False)

    async def set_light_mode(e):
        page.theme_mode = ft.ThemeMode.LIGHT
        page.update()

    async def set_dark_mode(e):
        page.theme_mode = ft.ThemeMode.DARK
        page.update()

    async def on_tap_link(e: ft.MarkdownTapLinkEvent):
        page.launch_url(e.url)

    async def on_keyboard(e: ft.KeyboardEvent):
        if e.ctrl and e.key:
            key = e.key.lower()
            if key == "o":
                await open_file(None)
            elif key == "r":
                await reload_file(None)

    md_view.on_tap_link = on_tap_link

    menu_bar = ft.MenuBar(
        controls=[
            ft.SubmenuButton(
                content=ft.Text("File"),
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text("Open"),
                        leading=ft.Icon(ft.Icons.FILE_OPEN),
                        trailing=ft.Text("Ctrl+O"),
                        on_click=open_file,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Reload"),
                        leading=ft.Icon(ft.Icons.REFRESH),
                        trailing=ft.Text("Ctrl+R"),
                        on_click=reload_file,
                    ),
                    recent_submenu,
                ],
            ),
            ft.SubmenuButton(
                content=ft.Text("Themes"),
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text("Light"),
                        leading=ft.Icon(ft.Icons.LIGHT_MODE),
                        on_click=set_light_mode,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Dark"),
                        leading=ft.Icon(ft.Icons.DARK_MODE),
                        on_click=set_dark_mode,
                    ),
                ],
            ),
        ],
    )

    scrollable_content = ft.Column(
        controls=[
            ft.Container(
                content=ft.Container(
                    content=md_view,
                    width=800,
                    padding=20,
                ),
                alignment=ft.Alignment(0, -1),
                expand=True,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    page.add(
        menu_bar,
        ft.Divider(height=1),
        scrollable_content,
    )
    page.on_keyboard_event = on_keyboard

    await init_storage()
    await update_recent_menu()


if __name__ == "__main__":
    ft.run(main)
