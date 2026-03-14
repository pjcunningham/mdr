import flet as ft

async def main(page: ft.Page):
    page.title = "Markdown Reader"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO

    async def open_file(e):
        # In modern Flet pattern, FilePicker can be created directly in the handler
        # but it still needs to be in the overlay to function properly in some environments.
        # However, following the instruction: "Use the modern async pattern: files = await ft.FilePicker().pick_files(...)"
        # Note: In Flet 0.82.2, FilePicker.pick_files() is an async method.
        # But it usually needs to be added to the overlay. The user instructions say:
        # "Do not use page.overlay.append(file_picker) for this markdown reader."
        # This implies Flet 0.82.2 (or a specific build) handles this registration implicitly or differently.
        
        file_picker = ft.FilePicker()
        # Some Flet versions require it in overlay, the instruction says NO.
        # Let's follow the instruction and see if it works as a standalone service.
        files = await file_picker.pick_files(
            allow_multiple=False,
            with_data=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["md"],
        )
        if not files:
            return

        try:
            selected = files[0]
            # Read from bytes directly as requested
            content = selected.bytes.decode("utf-8", errors="replace") if selected.bytes else ""
            md_view.value = content or "# Empty file"
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error reading file: {ex}"))
            page.snack_bar.open = True
            page.update()

    async def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            toggle_btn.icon = ft.Icons.DARK_MODE
        else:
            page.theme_mode = ft.ThemeMode.DARK
            toggle_btn.icon = ft.Icons.LIGHT_MODE
        page.update()

    async def on_tap_link(e: ft.MarkdownTapLinkEvent):
        page.launch_url(e.url)

    toggle_btn = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE,
        on_click=toggle_theme,
        tooltip="Toggle Light/Dark Mode",
    )

    md_view = ft.Markdown(
        value="# Welcome to Markdown Reader\nSelect a markdown file to view its content.",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        on_tap_link=on_tap_link,
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Markdown Reader"),
        actions=[
            toggle_btn,
            ft.IconButton(
                icon=ft.Icons.FILE_OPEN,
                on_click=open_file,
                tooltip="Open Markdown File",
            ),
        ],
    )

    page.add(md_view)
    page.update()

if __name__ == "__main__":
    ft.run(main)
