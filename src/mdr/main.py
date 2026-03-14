import os
import flet as ft

RECENT_FILES_KEY = "recent_files"
MAX_RECENT_FILES = 10
DEFAULT_MARKDOWN = "# Welcome to Markdown Reader\nSelect a markdown file to view its content."


async def main(page: ft.Page):
    page.title = "Markdown Reader"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    prefs = ft.SharedPreferences()

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

    def show_error(message: str):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    async def get_recent_files():
        try:
            value = await prefs.get(RECENT_FILES_KEY)
            return value if isinstance(value, list) else []
        except Exception:
            return []

    async def set_recent_files(recent_files):
        try:
            await prefs.set(RECENT_FILES_KEY, recent_files)
        except Exception as ex:
            show_error(f"Could not save recent files: {ex}")

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
                        content=ft.Text(os.path.basename(file_path)),
                        data=file_path,
                        on_click=lambda e, path=file_path: page.run_task(open_recent_file, path),
                    )
                )

            # Separator
            recent_submenu.controls.append(ft.Divider())

            # Clear recent
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

    async def load_markdown_from_path(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            md_view.value = content or "# Empty file"
            page.update()
            await remember_recent_file(file_path)

        except Exception as ex:
            show_error(f"Error opening file: {ex}")

    async def open_file(e):
        try:
            files = await ft.FilePicker().pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["md"],
            )
        except Exception as ex:
            show_error(f"File picker error: {ex}")
            return

        if not files:
            return

        selected = files[0]

        if getattr(selected, "path", None):
            await load_markdown_from_path(selected.path)
            return

        # Fallback (non-desktop environments)
        try:
            content = selected.bytes.decode("utf-8", errors="replace") if selected.bytes else ""
            md_view.value = content or "# Empty file"
            page.update()
        except Exception as ex:
            show_error(f"Error reading file: {ex}")

    async def open_recent_file(file_path):
        await load_markdown_from_path(file_path)

    async def set_light_mode(e):
        page.theme_mode = ft.ThemeMode.LIGHT
        page.update()

    async def set_dark_mode(e):
        page.theme_mode = ft.ThemeMode.DARK
        page.update()

    async def on_tap_link(e: ft.MarkdownTapLinkEvent):
        page.launch_url(e.url)

    async def on_keyboard(e: ft.KeyboardEvent):
        if e.ctrl and e.key and e.key.lower() == "o":
            await open_file(None)

    md_view.on_tap_link = on_tap_link

    centered_md_view = ft.Container(
        content=md_view,
        width=800,
        alignment=ft.Alignment(0, -1),
        padding=20,
    )

    centered_md_view_wrapper = ft.Column(
        controls=[centered_md_view],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

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

    page.add(menu_bar, centered_md_view_wrapper)
    page.on_keyboard_event = on_keyboard

    await update_recent_menu()


if __name__ == "__main__":
    ft.run(main)
