# Offline test suite

These tests cover logic in `github_monitor.py` that can run without network access.
GitHub API objects are replaced with test doubles.

## Running

From the repository root:

```bash
pip install -e '.[test]'
python -m pytest
```

`pyproject.toml` puts the repository root first on `sys.path`. `conftest.py`
enforces the same order so tests always use the working tree.

Lint the same way CI does:

```bash
pip install -e '.[lint]'
python -m ruff check github_monitor.py tests
```

CI runs both on every push and pull request, across Python 3.10 through 3.14,
and again before anything is published to PyPI.

## Layout

| File | Area under test |
| --- | --- |
| `test_config_loading.py` | Config files read as data, rejected content naming its line and setting, and guarded replacement of a generated config |
| `test_daily_contributions.py` | Stable calendar window selection and missing-day handling |
| `test_diagnostic_modes.py` | User-visible verbose and debug transcripts across requests, swallowed exceptions, degraded checks, delivery, files, waits and private-setting sources |
| `test_doctor.py` | Complete doctor transcripts, exit status, dependency states, private-setting sources, offline failures, read-only paths, TTY progress and separately approved real delivery tests |
| `test_event_configuration.py` | Supported event types, intentional 30-event window and retry defaults |
| `test_github_token_setup.py` | Hidden token entry, targeted dotenv updates and refusal to save an invalid token |
| `test_install_method_commands.py` | PyPI and standalone install detection with POSIX and Windows command rendering |
| `test_profile_fields.py` | Addition, removal and failure handling for nullable profile fields |
| `test_recovery_errors.py` | Closed recovery codes, classification, retryability and layered secret redaction that leaves ordinary output intact |
| `test_repository_contracts.py` | Governance documents, issue templates, action pinning, release gating and the CI contract |
| `test_repository_metadata.py` | Governance files, citation, funding, line endings, the declared editor style, the pinned linter and release integrity |
| `test_repository_monitoring.py` | Discussion collection, repository snapshots, open and closed notifications, event formatting |
| `test_setup_wizard.py` | Buffered setup, section editing, target and duration normalization, config and dotenv separation, backups, doctor and monitoring handoffs, non-interactive fallback and pseudo-terminal transcripts |
| `test_startup_configuration.py` | Config, dotenv, exported environment and two-phase CLI precedence at startup consumer boundaries |
| `test_terminal_color.py` | Theme parity, token colours, wrapper order, ANSI-free logs, terminal sanitizing, truncation, progress redraws, setup, Doctor and recovery surfaces |
| `test_webhook_notifications.py` | Webhook URL validation, provider detection and per-event notification switches |

## Conventions

* Keep every test offline. If a code path needs network access, stub it with
  `monkeypatch` rather than skipping the test.
* Restore module-level globals you change. Tests share one imported module, so a
  leaked global affects whatever runs next.
* Replace GitHub calls and notification delivery with test doubles.
* Never use a real GitHub personal access token, SMTP password or webhook URL.

A change to the monitoring loop, authentication or GitHub data handling is not
verified by this suite alone. Exercise it against a real account and say so in the
pull request, without usernames or credentials.
