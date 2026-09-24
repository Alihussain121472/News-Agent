# Python Practice Hub

The authenticated hub is available at `/user/python` and is linked from the member dashboard. It uses the existing Flask session and PostgreSQL connection; no separate login or public API is introduced.

## Deploy setup

The production build runs `python scripts/setup_practice.py`. The script downloads the pinned CPython 3.12 WASI binary, verifies its SHA-256 checksum, and installs the pinned guest-only pytest packages into `.practice-runtime/packages`. The Render, Docker, and `build.sh` definitions call it. An existing manually configured Render service must use `bash build.sh` or append `&& python scripts/setup_practice.py` to its build command. If deploying another way, run that script once during the image build; do not run it on each web request.

The existing database startup migration creates `python_practice_state` and `python_practice_jobs`. Both tables reference `registered_users`, are owner-scoped by the server session, enable row-level security, and revoke direct `anon`/`authenticated` access. No user password or email is required by the feature.

## Runtime boundaries

Learner code runs in CPython 3.12 inside WebAssembly. Each run has a 10-second wall-clock limit, 128 MiB memory limit, 16 KiB combined output limit, 1 MB per virtual text file, 32 files, and a server execution rate limit. There is no network, host filesystem, shell, subprocess, binary file, or arbitrary package access. `pytest` is available for in-memory assertions and `unittest` exercises. The server keeps reference solutions and hidden cases out of the browser response.

## Local verification

Install the normal requirements, run `python scripts/setup_practice.py`, then run `python -m unittest discover -s tests/practice -p 'test_*.py' -v`. The tests cover all reference solutions, syntax and runtime errors, timeouts, Stop, memory/output limits, host capability isolation, hidden-test privacy, authentication, draft ownership, quizzes, and assessment recovery. `python scripts/preview_practice.py --email YOUR_AUTHORIZED_TEST_EMAIL` prepares a local session without changing the account password or sending mail, then serves the normal app at `http://127.0.0.1:5055/user/python`.

## Visibility and release verification

The member dashboard has an always-visible Practice Hub card, a desktop sidebar link, and a mobile navigation link. `/python` and `/dashboard/python` redirect to `/user/python`. Signed-out visitors are sent to the existing login page. A 404 at `/user/python` means the new code has not been deployed. After release, verify the authenticated dashboard, the Hub bootstrap response (`runtime_ready: true`), an actual Run/Submit, and saved progress after a refresh. The Hub's stylesheet does not depend on rebuilding Tailwind.

Course scope follows the ten official CS50P sections. Exercises and explanations are original, and the official notes and full lecture are linked from each module. Video timestamps are intentionally omitted unless verified.

## Recovery and assessment updates

Quiz attempts save each selection, resume after refresh, and offer explained review and a separate missed-question retry. Full-quiz averages and best scores exclude shorter retry attempts. Repeating an attempt submission does not add another result. Practice drafts save standard input and command-line arguments as well as code; assessment drafts remain separate from practice drafts.

Each new Grand Test selects one coding problem and one quiz question per chapter. Its numbered review checklist shows answered questions and saved review flags. The timer remains active throughout the Hub, and final submission waits for queued saves. Practice grading and new practice quizzes are unavailable during an active assessment. Reloading during grading reconnects to the existing grading job.

Python writes are unbuffered so already-produced output survives Stop and timeouts. Virtual text files implement read/write permissions, exclusive creation, append, seek and truncate, including `pathlib` text reads/writes, within the existing memory-only sandbox. General filesystem operations and binary files remain unsupported.
