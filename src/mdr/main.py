import json
import os
import re
import asyncio
from pathlib import Path

import flet as ft

MAX_RECENT_FILES = 10
DEFAULT_MARKDOWN = "# Welcome to Markdown Reader\nSelect a markdown file to view its content."
AUTO_RELOAD_INTERVAL_SECONDS = 1.5


async def main(page: ft.Page):
    page.title = "Markdown Reader"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ft.Colors.SURFACE

    current_file_path = None
    current_file_mtime = None
    recent_files_path = None
    auto_reload_enabled = True
    suppress_next_reload = False

    md_view = ft.Markdown(
        value=DEFAULT_MARKDOWN,
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        auto_follow_links=False,
    )

    def get_reader_width(page_width) -> int:
        if not page_width:
            return 900
        return max(320, min(1100, int(page_width * 0.9)))

    def show_message(message: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()

    toc_column = ft.Column(
        controls=[],
        spacing=4,
        tight=True,
        scroll=ft.ScrollMode.AUTO,
    )

    toc_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Contents", weight=ft.FontWeight.BOLD, size=16),
                ft.Divider(height=8),
                toc_column,
            ],
            spacing=0,
            tight=True,
        ),
        width=260,
        padding=ft.Padding.all(16),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border_radius=12,
        visible=False,
    )

    reader_container = ft.Container(
        content=md_view,
        width=get_reader_width(page.width),
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        border_radius=12,
    )

    recent_submenu = ft.SubmenuButton(
        content=ft.Text("Open Recent"),
        controls=[],
        leading=ft.Icon(ft.Icons.HISTORY),
    )

    def slugify_heading(text: str) -> str:
        slug = text.strip().lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_-]+", "-", slug)
        return slug.strip("-")

    def extract_headings(markdown_text: str):
        headings = []
        lines = markdown_text.splitlines()

        in_fenced_code = False
        fence_marker = None

        for line in lines:
            stripped = line.rstrip()

            if stripped.startswith("```") or stripped.startswith("~~~"):
                marker = stripped[:3]
                if not in_fenced_code:
                    in_fenced_code = True
                    fence_marker = marker
                elif marker == fence_marker:
                    in_fenced_code = False
                    fence_marker = None
                continue

            if in_fenced_code:
                continue

            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                if title:
                    headings.append(
                        {
                            "level": level,
                            "title": title,
                            "slug": slugify_heading(title),
                        }
                    )

        return headings

    def build_toc(markdown_text: str):
        headings = extract_headings(markdown_text)
        toc_column.controls.clear()

        if not headings:
            toc_column.controls.append(
                ft.Text("No headings found", italic=True, color=ft.Colors.OUTLINE)
            )
            toc_panel.visible = False
            return

        for item in headings:
            indent = max(0, item["level"] - 1) * 12
            toc_column.controls.append(
                ft.Container(
                    content=ft.Text(
                        item["title"],
                        size=14,
                        no_wrap=False,
                    ),
                    padding=ft.Padding.only(left=indent, right=8, top=6, bottom=6),
                    border_radius=6,
                )
            )

        toc_panel.visible = True

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

    def read_markdown_file(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_file_mtime(file_path: str):
        try:
            return os.path.getmtime(file_path)
        except Exception:
            return None

    async def render_markdown(content: str):
        md_view.value = content or "# Empty file"
        build_toc(content)
        page.update()

    async def load_markdown_from_path(file_path, remember=True):
        nonlocal current_file_path, current_file_mtime, suppress_next_reload

        try:
            content = read_markdown_file(file_path)
            current_file_path = file_path
            current_file_mtime = get_file_mtime(file_path)
            suppress_next_reload = True

            await render_markdown(content)

            if remember:
                await remember_recent_file(file_path)

        except Exception as ex:
            show_message(f"Error opening file: {ex}")

    async def open_file(e):
        nonlocal current_file_path, current_file_mtime, suppress_next_reload

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
            current_file_path = None
            current_file_mtime = None
            suppress_next_reload = False
            await render_markdown(content)
        except Exception as ex:
            show_message(f"Error reading file: {ex}")

    async def open_recent_file(file_path):
        await load_markdown_from_path(file_path)

    async def reload_file(e=None):
        if not current_file_path:
            show_message("No file is currently open to reload.")
            return
        await load_markdown_from_path(current_file_path, remember=False)

    async def toggle_auto_reload(e=None):
        nonlocal auto_reload_enabled
        auto_reload_enabled = not auto_reload_enabled
        auto_reload_item.checked = auto_reload_enabled
        page.update()

    async def watch_current_file():
        nonlocal current_file_mtime, suppress_next_reload

        while True:
            await asyncio.sleep(AUTO_RELOAD_INTERVAL_SECONDS)

            if not auto_reload_enabled or not current_file_path:
                continue

            latest_mtime = get_file_mtime(current_file_path)
            if latest_mtime is None or current_file_mtime is None:
                continue

            if suppress_next_reload:
                suppress_next_reload = False
                continue

            if latest_mtime != current_file_mtime:
                try:
                    content = read_markdown_file(current_file_path)
                    current_file_mtime = latest_mtime
                    await render_markdown(content)
                    show_message("File reloaded automatically.")
                except Exception as ex:
                    show_message(f"Auto-reload failed: {ex}")

    async def set_light_mode(e):
        page.theme_mode = ft.ThemeMode.LIGHT
        page.update()

    async def set_dark_mode(e):
        page.theme_mode = ft.ThemeMode.DARK
        page.update()

    async def on_tap_link(e: ft.MarkdownTapLinkEvent):
        url = e.data if hasattr(e, "data") and e.data else getattr(e, "url", None)
        if url:
            page.launch_url(url)

    async def on_keyboard(e: ft.KeyboardEvent):
        if e.ctrl and e.key:
            key = e.key.lower()
            if key == "o":
                await open_file(None)
            elif key == "r":
                await reload_file(None)

    def on_resize(e):
        available_width = page.width or 1200

        has_toc = len(toc_column.controls) > 0 and not (
                len(toc_column.controls) == 1
                and isinstance(toc_column.controls[0], ft.Text)
                and toc_column.controls[0].value == "No headings found"
        )

        toc_panel.visible = has_toc

        reserved_for_toc = 300 if has_toc else 40
        reader_container.width = max(
            320,
            min(1100, int((available_width - reserved_for_toc) * 0.92)),
        )

        page.update()

    md_view.on_tap_link = on_tap_link

    auto_reload_item = ft.MenuItemButton(
        content=ft.Text("Auto Reload"),
        leading=ft.Icon(ft.Icons.SYNC),
        on_click=toggle_auto_reload,
        close_on_click=False,
    )
    auto_reload_item.checked = auto_reload_enabled

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
                    auto_reload_item,
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

    content_row = ft.Row(
        controls=[
            ft.Container(
                content=reader_container,
                alignment=ft.Alignment(0, -1),
                expand=True,
                padding=ft.Padding.symmetric(horizontal=16, vertical=16),
            ),
            ft.Container(
                content=toc_panel,
                padding=ft.Padding.only(top=16, right=16, bottom=16),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    scrollable_content = ft.Column(
        controls=[content_row],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
    )

    page.add(
        menu_bar,
        ft.Divider(height=1),
        scrollable_content,
    )
    page.on_keyboard_event = on_keyboard
    page.on_resized = on_resize

    await init_storage()
    await update_recent_menu()
    on_resize(None)
    page.run_task(watch_current_file)


if __name__ == "__main__":
    ft.run(main)
