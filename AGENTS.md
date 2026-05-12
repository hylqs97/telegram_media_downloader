# Repository Guidelines

## Project Structure & Module Organization

`media_downloader.py` is the main CLI entry point and orchestrates Telegram downloads. `module/` contains application state, bot/web handlers, filtering, Pyrogram extensions, cloud-drive upload logic, templates, and static web assets. `utils/` holds shared helpers for formatting, metadata, crypto, file management, logging, and update checks. Tests mirror these areas under `tests/`, with `tests/module/` and `tests/utils/` for module-specific coverage. `README.md` and `README_CN.md` document user setup; `screenshot/` stores README media. Docker support lives in `Dockerfile` and `docker-compose.yaml`.

## Build, Test, and Local Verification

Run commands from the repository root:

- `make install`: install runtime dependencies from `requirements.txt`.
- `make dev_install`: install runtime and development dependencies.
- `python3 media_downloader.py`: run the downloader locally after preparing `config.yaml` and `data.yaml`.
- `make test`: run pytest with doctests, coverage, HTML coverage output, and JUnit XML under `${TEST_ARTIFACTS}` or `/tmp/coverage`.
- `make static_type_check`: run mypy over `media_downloader.py`, `utils`, and `module`.
- `make style_check`: run mypy and pylint using `pylintrc`.
- `pre-commit run --all-files`: run configured Black, isort, mypy, pylint, whitespace, and end-of-file hooks.

## Coding Style & Naming Conventions

Follow PEP 8 with Black formatting and isort using the Black profile. Use 4-space indentation, snake_case functions and variables, PascalCase classes, and uppercase constants. Keep type hints on new or changed Python code; prefer `from typing import List, Optional, Union` style imports where the project already uses them. Preserve existing docstring style for modules, classes, and helper functions.

## Testing Guidelines

Tests use pytest to run `unittest.TestCase` classes and `test_*` methods. Add focused tests near the changed area, such as `tests/utils/test_format.py` for `utils/format.py` or `tests/module/test_app.py` for `module/app.py`. Use mocks for Telegram, filesystem, and network behavior rather than requiring real credentials or live Telegram access.

## Commit & Pull Request Guidelines

Use the documented commit format `<prefix>: <subject>`, with prefixes such as `docs`, `fix`, `enh`, `refactor`, `style`, `test`, `type`, and `ci`. Keep subjects under 80 characters, lowercase, present tense, and without a trailing period; reference GitHub issues as `#123` when applicable. Pull requests should include a clear title and description, update tests for behavior changes, and update `README.md` when user-facing features or configuration change.

## Security & Configuration Notes

`config.yaml`, `data.yaml`, `sessions/`, `temp/`, `downloads/`, and `log/` may contain credentials, Telegram session data, or downloaded media during local runs. Review these paths carefully before staging changes, and avoid committing real API keys, bot tokens, or private chat data.
