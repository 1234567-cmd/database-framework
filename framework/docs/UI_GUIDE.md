# Web interface guide

`dbintel ui` runs a local web interface. It uses no CDN and no external assets, so it works offline.

## Start it

```powershell
ui.bat
```

Or `.venv\Scripts\python -m dbintel ui [--port 8765] [--no-open] [--max-upload-mb 2048]`.

The browser opens at `http://127.0.0.1:8765/#token=...`. The token is new at every launch. With `--no-open`, copy the printed address. Press Ctrl+C in the console to stop.

If you see "Open dbintel from its launch link", the token is missing or from an earlier launch. Use the link printed by the current launch.

## Screens

| Screen | Purpose |
|---|---|
| New analysis | Upload files, read a file by path, or connect read-only. Optional query log, manifest, application source folder, profile. Progress by stage with cancel. |
| Dashboard | Score, grade, confidence, cap, category cards, distributions, top priorities, warnings. |
| Findings | Server-side search, filters and sort. Confirmed defects come first by default. Each finding has a shareable link. |
| Tables | Columns, keys, indexes, relationships in and out, dependencies and findings. |
| ER diagram | One domain or one table's neighbours at a time. Pan, zoom, search, current or proposed, Mermaid download. |
| Recommendations | Priority rationale, existing and recommended side by side, SQL, dependencies, rollback, validation. |
| Migration review | Steps with up and down SQL, checks, badges, zip download, sandbox test. |
| Roadmap, Lineage, Architecture, Coverage, Limitations | The remaining report sections. |
| History | Reopen saved runs, delete, compare two by stable finding ID. |

Export is in the top bar: HTML, Markdown, JSON. PDF is made through your browser's print dialog ("Print or save as PDF", then choose Save as PDF).

## Large files

Use **Use a file path** for a large dump. The file is read in place and not copied. Uploads are limited by `--max-upload-mb`, streamed to a private temporary folder and deleted after the run.

## Sandbox test

The sandbox copies the schema to a temporary SQLite file, runs each step and its rollback there, and deletes the copy. It never connects to the source database. You must type or paste the exact plan hash.

| Result | Meaning |
|---|---|
| Passed | The step and its checks ran, and rollback restored the schema where a rollback exists. |
| Failed | A check, statement or rollback failed. The reason is shown. |
| Not testable | The step is manual or uses SQL that cannot run on SQLite. Test it on a server of the target engine with `migrate test --scratch-url`. |

- The latest run uses sample rows held in memory. A live source is closed after reading, so its copy has no rows.
- A saved run is rebuilt from `report.json` and `plan.json`, with schema only, because row data is never stored.
- If a saved run cannot be rebuilt, sandbox testing is disabled and the reason is shown. Re-run the analysis to test it.

There is no apply function. No screen, endpoint or code path applies anything to a source database.

## Security

- Binds only to 127.0.0.1. The `Host` header is checked to block DNS rebinding.
- Every API request needs the per-launch token. A request with a foreign `Origin` is refused.
- Strict Content-Security-Policy with no inline scripts. Database content is placed with text nodes only.
- Passwords stay in memory for that run, reach only the analysis process, and are never written to run files, logs, URLs or error messages.
- One analysis or test runs at a time. Cancel stops the process and leaves no partial run.

## Stored data

Runs are in `reports\ui_runs\<run id>`: `report.html`, `report.md`, `report.json`, `er\`, `migrations\` and a small `summary.json` copied from the report. Delete a run from History.
