# Show and open chat download directories

This ExecPlan follows `docs/plans.md` and is maintained as implementation proceeds.

## Purpose / Big Picture

The chat task table currently identifies a download only by Telegram ID. Display
the chat title, retain the ID and message checkpoint, and show the local save
directory. A local Windows user can click an existing directory to open File
Explorer. This opens the directory on the service computer, not on a remote
browser's computer. Missing directories must not be created just by viewing the UI.

## Progress

- [x] (2026-10-25) Inspect the table, download path rules, and live service.
- [x] (2026-10-25) Add stable directory resolution and asynchronous chat title lookup.
- [x] (2026-10-25) Add a local-only directory-opening endpoint and table controls.
- [x] (2026-10-25) Verify 53 passing regression tests, one skip, and 29 browser checks.
- [x] (2026-10-25) Deploy at port 5000, preserve checkpoints/retries, restore the prior task, and verify a real Explorer window.

## Surprises & Discoveries

The current installation uses `chat_title` then `media_datetime` under
`F:\telegram`. Guessing a directory from the numeric ID would be wrong. A
directory shared by all of a chat's downloads ends at the first date/type
component; components following that cannot be flattened into a fictitious path.
The existing service also has a chat marked running with zero discovered tasks,
so validation must not stop it without checking current activity again.

The bundled Layui version has no `layui-icon-folder` glyph. Use its existing
`layui-icon-file` glyph instead. The pinned mypy defaults to Python 3.7 and
cannot parse the installed MarkupSafe stub; limiting imports and selecting 3.8
exposes only the pre-existing Any-return error at `module/web.py:204`. Black
also identifies two pre-existing formatting differences in `test_app.py`;
new tests and the changed production modules pass formatting/import checks.

## Decision Log

Keep title metadata in memory and obtain it from the existing Telegram client
asynchronously, at most once per chat per five minutes. Directory display must
not trigger downloads or poll Telegram on every table refresh. Record titles
seen by the existing download path function too. No credentials or download
checkpoint format changes are needed.

The user explicitly approved backing up state, restarting the real service, and
restoring the currently scanning task. The independent preview passed all
browser checks before changing the real service.

Accept only a configured chat ID, never a browser-provided filesystem path.
Require a logged-in, loopback, same-origin JSON POST with a loopback Host before
opening a directory. Resolve real paths and enforce containment under the
configured download root, including junction/symlink targets. Use `os.startfile`
with a directory, without shell command construction. Disable the control for
missing, unresolved, unsupported, remote, or out-of-root paths.

## Context and Orientation

`module/app.py` owns `ChatDownloadConfig` and `get_file_save_path`, which joins
the configured save root with ordered path components. `module/web.py` owns the
Flask routes and the configured Pyrogram client. `module/templates/index.html`
builds the Layui task table and `module/static/css/index.css` styles it. The
existing app is served at port 5000; use port 5001 for isolated preview checks.

## Plan of Work

Add an optional cached title to `ChatDownloadConfig` and a directory helper to
`Application` that stops before the first per-file path component. Extend
`get_chat_configs` with title, absolute directory, and availability fields. Queue
bounded title lookups on the application's existing event loop. Add the guarded
`open_chat_directory` POST endpoint. Render the title, ID, checkpoint, and a
folder-icon path command in the existing identity column; preserve rule editing,
task controls, escaping, and responsive layout. Document the local Windows
restriction in both READMEs.

## Concrete Steps

Work from `D:\IdeaProjects\telegram_media_downloader`. Use the existing virtual
environment and run the following after implementation:

    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
    .\.venv\Scripts\python.exe -m pytest tests/module/test_web.py tests/module/test_app.py tests/test_media_downloader.py -q --disable-warnings
    git diff --check

Run an isolated Flask preview with fake application state and mock directory
opening for browser validation. Inspect desktop and 375px screenshots and use
Playwright to click the directory control, check its JSON request, and exercise
missing-directory, opening-failure, and malicious-title escaping cases.

## Validation and Acceptance

Tests must show correct roots for ID/title/date/type ordering, unresolved titles,
and shared save roots. Mock all Telegram and Explorer operations. Flask tests
must reject arbitrary paths, unknown chats, non-loopback callers/hosts,
cross-origin requests, form posts, missing directories, and paths escaping the
root. The browser must preserve task controls, have no JavaScript errors or page
overflow, and show the full path in a tooltip with wrapping on narrow screens.
Recheck real downloads before any service replacement. If active work remains,
keep the service running and request approval before restarting it.

## Idempotence and Recovery

No media, configuration rules, or retry/checkpoint state is changed by directory
display/opening. Tests use temporary directories. Before any approved service
restart, back up `config.yaml` and `data.yaml` under ignored `.codex-run`, persist
task state through the existing stop action only when safe, and recheck the
checkpoint and retries afterward. Do not stage private runtime data or the
pre-existing untracked file `d`.

## Artifacts and Notes

Browser artifacts belong under ignored `output/playwright/`. Record final test
counts and the actual live/preview URLs here after verification.

The isolated preview at `http://127.0.0.1:5001/?view=chats` passed 29 browser
assertions, including a real HTTP request through the guarded endpoint with a
mock Explorer, failure/retry, busy state, keyboard activation, escaped titles,
existing edit actions, and no page overflow at widths 320/375/768/1280/1440/1920.
Screenshots are `output/playwright/directory-desktop.png` and
`output/playwright/directory-mobile.png`. No JavaScript runtime errors occurred;
the intentionally simulated HTTP 500 was the only console error.

Final focused regression command including `tests/utils/test_format.py`:

    53 passed, 1 skipped, 319 warnings in 3.98s

The real service is running at `http://127.0.0.1:5000/?view=chats`. State backups
before and after persistence are in
`.codex-run/before-directory-ui-restart-20261025-191551/`. The replacement
service parent/listener PIDs were 3960/18592 at verification, with logs under
`.codex-run/media_downloader-directories-20261025-191618.*.log`. The completed
task's next message checkpoint advanced by the existing save logic, and its one
retry entry was retained. The formerly scanning task was restarted and became
active. Both configured titles and existing directories resolved successfully.

An actual click through the real page returned success, and Windows Shell COM
confirmed an Explorer window at the exact requested existing directory. No media
file was opened. The live page console had zero errors. The isolated preview and
automated browser were then closed; port 5000 remains the production service.

## Interfaces and Dependencies

Use existing Flask, Pyrogram, jQuery, Layui, pytest/unittest, and Python standard
library APIs only. The new API is `POST /open_chat_directory` with JSON
`{"chat_id": "..."}`. It returns JSON `code: 0` on success, otherwise `code: 1`
and a stable `error` identifier that the Chinese UI translates.

## Outcomes & Retrospective

Implementation, isolated verification, and real service deployment are complete.
The existing service was restarted only after explicit approval and backup;
checkpoints/retries survived and the previously running task was restored.
No media or download rules were changed by the feature itself. Existing mypy
and old-test formatting issues remain outside the scope of this feature.

Plan created on 2026-10-25 after inspecting live task state and configured path
ordering; the separate preview avoids interrupting an active scan.

Updated on 2026-10-25 with regression/browser results and the approved deployment
step. The preview opener remained mocked throughout browser testing.

Updated on 2026-10-25 after real deployment and Windows Explorer verification;
all planned milestones are complete and test-only global Flask state is restored
after each new unit test.
