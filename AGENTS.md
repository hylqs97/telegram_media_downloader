# Repository Guidelines

## Project Structure & Module Organization

- `media_downloader.py`: CLI entry, orchestration, queue, and workers.
- `module/`: app state/config, bot/web, filters, Pyrogram hooks, cloud upload, and history fetching.
- `utils/`: formatting, metadata, crypto, file, logging, platform, and update code.
- `tests/`: pytest suite; `tests/module/` and `tests/utils/` mirror code.
- `module/templates/`, `module/static/`, and `screenshot/`: web and README assets. Docker files are at the root.

## Build, Test, and Development Commands

- `make install`: install runtime dependencies.
- `make dev_install`: install runtime and dev dependencies.
- `python3 media_downloader.py`: run locally after preparing `config.yaml` and `data.yaml`.
- `make test`: run pytest with doctests, coverage, HTML output, and JUnit XML.
- `make static_type_check`: run mypy over `media_downloader.py`, `utils`, and `module`.
- `make style_check`: run mypy and pylint with `pylintrc`.
- `pre-commit run --all-files`: run Black, isort, mypy, pylint, and file hooks.

## Coding Style & Naming Conventions

- Python: requires 3.7+; CI runs 3.8 through 3.12.
- Formatting: Black plus isort with the Black profile; use 4-space indentation.
- Names: snake_case functions and variables, PascalCase classes, uppercase constants.
- Types: keep or add PEP 484 hints; follow nearby imports.
- Linting: `pylintrc` defines disabled checks and message formatting.

## Testing Guidelines

- Framework: pytest running `unittest.TestCase` classes and `test_*` methods.
- Naming: files use `test_*.py`; classes commonly end in `TestCase`.
- Placement: test near changed code, such as `tests/utils/test_format.py` for `utils/format.py`.
- Mock Telegram, filesystem, and network calls; never require real credentials or live Telegram access.

## Architecture Notes (Quick Map)

- `module/app.py` owns config, `data.yaml` state, task nodes, and status models.
- `media_downloader.py` connects chat config to `download_all_chat`, `download_chat_task`, queue, and workers.
- `module/filter.py` evaluates `download_filter` after `module/pyrogram_extension.py` sets metadata.
- `module/bot.py` and `module/web.py` are user-facing control surfaces.
- For history, filtering, or sorting changes, preserve bounded memory behavior and cover `tests/test_media_downloader.py`.

## Commit & Pull Request Guidelines

Use `<prefix>: <subject>` commit messages. Documented and recent prefixes include `feat`, `docs`, `fix`, `enh`, `refactor`, `style`, `test`, `type`, `ci`, and `chore`. Keep subjects under 80 characters, lowercase, present tense, and without a trailing period; reference issues as `#123` when applicable. PRs need a problem/solution summary, validation commands, tests for behavior changes, and README updates for user-facing changes.

## Security & Configuration Notes

`config.yaml`, `data.yaml`, `sessions/`, `temp/`, `downloads/`, and `log/` can contain API keys, bot tokens, sessions, private chat metadata, or media. Review them before staging; never commit real credentials or private Telegram data.
