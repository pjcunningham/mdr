# Markdown Reader
A basic Markdown reader built with [Flet](https://flet.dev/).

## Features
- Support for Dark Mode.
- Simple Markdown viewing.
- File picking.

## How to Run
To run the application, use the following command:
```bash
uv run python src/mdr/main.py
```

## How to Test
To run the tests, use:
```bash
uv run pytest
```

## How to Build Windows Executable
To build a standalone Windows executable, use the following command:
```bash
uv run flet pack src/mdr/main.py -n mdr --icon assets/mdr_icon.ico --product-name "Markdown Reader" --company-name "Borsuk Software Engineering Ltd"
```
This will create a `dist` folder containing the `mdr.exe` executable.
Make sure to place your icon in the `assets` folder (or adjust the path accordingly).
