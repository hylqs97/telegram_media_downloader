# Download Manager Redesign

## Purpose

Redesign the existing Flask download manager as a compact Chinese work surface. A user should see configured chat tasks, their processed counts and retry counts, edit size/date/expression filters, start or stop a chat, pause or continue the global queue, and inspect active or completed transfers. All existing backend endpoints, form field names, table identifiers, and Telegram state must survive. Download counters must not be relabeled as successful downloads: the backend's finish count includes other terminal results.

## Progress

- [x] (2026-10-25) Read the Hallmark skill, redesign and app-screen guidance; inspect existing templates, routes, repository instructions and current Git status.
- [x] (2026-10-25) User confirmed Chinese, compact operational layout and preservation of existing functionality.
- [x] (2026-10-25 18:30 +08:00) Captured the original page and recorded its fields, submit control and screenshot baseline.
- [x] (2026-10-25 18:38 +08:00) Implemented the Wayfind app theme, task workspace and responsive rule editor without modifying downloader code.
- [x] (2026-10-25 18:46 +08:00) Verified 39 browser checks at five viewport widths; 34 existing tests passed and one was skipped. Hallmark compiled-source checks report zero Floor or Reflex findings and preserve all eight fields and the handler.
- [x] (2026-10-25 18:49 +08:00) Waited for all 123 real tasks to reach terminal results, persisted progress through the existing endpoint, backed up settings, restarted the service and verified HTTP 200 with the new template on port 5000.

## Surprises & Discoveries

The only pre-existing untracked file is `d`; leave it alone. Tracked source is clean. Configuration, sessions, logs and media are private runtime data and must not enter the diff. The repository refers to `.agent/PLANS.md`, but the actual execution-plan specification is `docs/plans.md`; this plan follows it. The current web UI uses Layui tables and date pickers plus inline jQuery handlers, not a separate frontend build.

The old pause button displayed the reverse action label. This was corrected while preserving the endpoint's action-value mapping. Laydate parses min/max strings asynchronously before storing object limits; the original unconditional object assignment caused a runtime error when opening dates. The new synchronizer preserves strings until initialization has completed and updates structured limits afterward.

The Hallmark scanner cannot resolve Flask `url_for` in raw Jinja, so compiled markup was separately checked using `.codex-run/hallmark-compile.py`. Third-party Layui styles were excluded from app-source linting and included in real browser checks. The live before/after comparison reports four review notes: real transfer numbers changed as downloads finished and the process restarted; Chinese text has a different word count; the raw Jinja page was not rendered as a standalone HTML file or included in the stylesheet-only render invocation. These are not missing controls. The compiled comparison preserves eight of eight fields and the original inline handler; the browser tests verify all write routes using intercepted requests.

## Decision Log

- Decision: Use Hallmark app-screen scope, based on the dealt Wayfind theme, with system sans text for Chinese and tabular figures.
  Rationale: The page is a frequently used task manager, so an operational table, a compact editor, and restrained state colours are more useful than marketing layouts or decorative imagery. App scope explicitly allows system typography.
  Date/Author: 2026-10-25, Codex.
- Decision: Keep the Flask routes and Layui library. Preserve form fields, script hooks and the three existing views.
  Rationale: The redesign should change presentation while respecting the live service and user data.
  Date/Author: 2026-10-25, Codex.
- Decision: Validate writes against isolated browser fixtures or a preview, not the real Telegram queue.
  Rationale: Saving or deleting real chat settings is not needed to test presentation.
  Date/Author: 2026-10-25, Codex.
- Decision: Reload the actual server only after active work reached 123/123 processed tasks.
  Rationale: Flask cached the original template. Saving through the existing stop-chat endpoint persisted message ID 1650 and reduced the retry list to one before a controlled restart. No unfinished transfer was interrupted.
  Date/Author: 2026-10-25, Codex.

## Outcomes & Retrospective

The Chinese manager is running at http://127.0.0.1:5000. It has a compact header and metrics row, three URL-persistent views, a task ledger, an adjacent rule editor, responsive mobile rows, labelled icon actions, keyboard tab navigation, request busy/error states and preserved date validation. Source changes are frontend CSS/template, README notes and this plan. No commit or push was performed.

Validation: 39 browser checks passed, including save and failed-save retention, form reset, date adjustment, start/stop, delete cancellation/confirmation, queue pause/continue semantics, arrow-key navigation, failed-load retry, and all three views without document overflow at 320, 375, 768, 1280 and 1920 pixels. Existing tests: 34 passed, one skipped. Final rendered app checks: zero Floor failures and zero Reflex findings. The in-thread finish review found two defects, both resolved. A tooltip and dialog-primary style triggered the F4 heuristic; the stamp records why these do not introduce multiple primary actions on the main screen.

Live data limits remain: the transfer list is session-local, and the backend does not expose per-row freshness or detailed failure categories. The UI deliberately calls these pending transfer records and processed task counts rather than claiming all records are actively transmitting or successfully downloaded.

## Context and Orientation

`module/templates/index.html` owns the dashboard and its jQuery handlers. The page calls `/get_chat_configs`, `/get_download_status`, `/get_download_list`, `/save_chat_config`, `/delete_chat_config`, `/start_chat_download`, `/stop_chat_download`, and `/set_download_state`. `module/static/css/index.css` styles the dashboard. `module/web.py` renders it and exposes these routes. The existing login page is outside this redesign. The process listens on port 5000. A separate preview can render the same template on a free port without starting Telegram or writing personal configuration. Hallmark lives in `C:/Users/40368/.codex/skills/hallmark`.

## Plan of Work

Record the original page with Hallmark's `sloplint.mjs --before --scope app` and its running URL. Generate `module/static/css/tokens.css` and `base.css` using the theme scaffold, then fill the app tokens and replace dashboard CSS. Recompose `index.html` around a compact header, a single metrics row, the existing three tabs, a task table and its inline rule editor. Keep the IDs and `lay-filter` hooks used by the current event handlers. Translate labels and add accessible icon labels using the existing Layui icon set. Expose request errors and busy states in the frontend and retain validation, date constraints and delete confirmation.

Run the Hallmark redesign comparison and inspect screenshots at desktop and mobile sizes. Use Playwright to exercise view navigation, date validation, form reset, edit, save, start/stop, delete cancellation/confirmation and request failure handling with intercepted API responses. Keep a record of any honest limits in the backend data rather than inventing success metrics.

## Concrete Steps

From `D:/IdeaProjects/telegram_media_downloader`, run Node scripts using the absolute Hallmark path. Install the browser-only checker under the ignored `.codex-run/hallmark-tools` directory, without adding runtime npm dependencies to the Python app. Set `HALLMARK_PUPPETEER` to that directory and use the installed Chrome for `sloplint`. The normal app command remains `.venv/Scripts/python.exe -u media_downloader.py`. Use `python -m compileall -q media_downloader.py module utils` and the relevant existing pytest suite to check compatibility.

## Validation and Acceptance

The page must render a working management surface at its reported local URL. Every previous field, route, event hook and action remains usable. Empty and failed loads have readable states. Desktop and mobile layouts show the item identity and controls without page-wide horizontal scroll; long file paths remain inspectable. Tabs are keyboard accessible. Buttons have names and focus rings, request actions keep a stable size and show failure honestly. The token stylesheet is the only source of colours and font families in the redesigned CSS. The Hallmark render check and before/after comparison run, with any remaining limitations reported explicitly.

## Idempotence and Recovery

All feature edits are limited to presentation, documentation and local QA artifacts. Do not manually alter configuration, retry IDs, Telegram session files or media directories. Preserve runtime progress through the existing API before a controlled service reload. The pre-reload settings backup is `.codex-run/before-ui-reload-20261025-184741`; it contains personal data and remains ignored. A failed checker can be rerun. Git diff provides a reviewable source change; private screenshots and fixtures stay in ignored artifact directories. Do not create commits or push without the user's request.

## Artifacts and Notes

Hallmark records live under `.hallmark/` or the ignored `.codex-run` QA area. Before/after screenshots and a comparison HTML document are acceptance evidence, not application assets. The new interface itself is the product visual; app scope requires no decorative photos.

## Interfaces and Dependencies

Use Flask/Jinja, Layui's existing table, form, date and icon APIs, and jQuery AJAX. `get_chat_configs` returns `code`, `data`, `count`; each row includes `chat_id`, `status`, `last_read_message_id`, file-size limits, date limits, `download_filter`, `finish_task`, `total_task`, `progress` and `ids_to_retry`. Download rows include `chat`, `id`, `filename`, `total_size`, `download_progress`, `download_speed` and `save_path`. Keep these contracts and the queue-state action mapping intact.

Revision note (2026-10-25): Initial plan written after source inspection and user direction confirmation.
Revision note (2026-10-25 18:49 +08:00): Recorded implementation, successful validation, scanner limitations, the two corrected UI defects and the controlled reload after real downloads finished.
