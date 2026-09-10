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

Build the documentation site the way CI does, which fails on a broken link or a
missing page:

```bash
pip install -r docs/requirements.txt
mkdocs build --strict
```

CI runs all three on every push and pull request, across Python 3.10 through 3.14,
and again before anything is published to PyPI.

## Layout

| File | Area under test |
| --- | --- |
| `test_smtp_error_privacy.py` | Short and escaped passwords in rejected SMTP sign-ins through commands, setup, Doctor and delivery |
| `test_setup_resolution_regressions.py` | Saved dotenv destinations, empty secrets, export precedence and recovery paths |
| `test_dotenv_quoted_keys.py` | Quoted dotenv keys, export prefixes, multiline values and duplicate removal |
| `test_documentation_layout.py` | Unique anchors, main screenshot placement and matching entry-page feature summaries |
| `conftest.py` | Import setup plus shared fixtures: the working-tree module, deterministic globals and the degraded-feature tracker reset between tests |
| `test_config_loading.py` | Config files read as data, rejected content naming its line and setting, and guarded replacement of a generated config |
| `test_daily_contributions.py` | Stable calendar window selection and missing-day handling |
| `test_diagnostic_modes.py` | User-visible verbose and debug transcripts across requests, swallowed exceptions, degraded checks, delivery, files, waits and private-setting sources |
| `test_doctor.py` | Complete doctor transcripts, exit status, dependency states, private-setting sources, offline failures, read-only paths, TTY progress and separately approved real delivery tests |
| `test_event_configuration.py` | Supported event types, intentional 30-event window and retry defaults |
| `test_github_token_setup.py` | Hidden token entry, targeted dotenv updates and refusal to save an invalid token |
| `test_help_screen.py` | The `--help` screen: the shared argument group names, the task-grouped examples and the startup banner |
| `test_install_method_commands.py` | PyPI and downloaded-script detection with portable plus exact POSIX and Windows commands |
| `test_monitoring_loop.py` | The primary monitoring loop driven through outages: the error alert on both channels, once per failure category, retried per channel and re-armed after a recovery |
| `test_profile_fields.py` | Addition, removal and failure handling for nullable profile fields |
| `test_recovery_errors.py` | Closed recovery codes, classification, retryability and layered secret redaction that leaves ordinary output intact |
| `test_repository_contracts.py` | Governance documents, issue templates, action pinning, release gating, the CI contract and the documentation site: its pinned page set, one title per page, no section on two pages, resolving links and the runtime guide URLs |
| `test_repository_metadata.py` | Governance files, citation, funding, line endings, the declared editor style, the pinned linter and release integrity |
| `test_repository_monitoring.py` | Discussion collection, repository snapshots, open and closed notifications, event formatting |
| `test_setup_wizard.py` | Buffered setup, section editing, target and duration normalization, config and dotenv separation, backups, doctor and monitoring handoffs, non-interactive fallback and pseudo-terminal transcripts |
| `test_startup_configuration.py` | Config, dotenv, exported environment and two-phase CLI precedence at startup consumer boundaries |
| `test_removed_identity_notes.py` | The notes printed when a followed account or repository disappears |
| `test_startup_summary_channels.py` | Summary rows naming the webhook provider, the mail server, the masked recipient, the delivery confirmations and the runtime |
| `test_terminal_color.py` | Theme parity, token colours, wrapper order, ANSI-free logs, terminal sanitizing, truncation, progress redraws, setup, Doctor and recovery surfaces |
| `test_tls_verification.py` | Every connection honouring `VERIFY_SSL` and the single shared TLS context builder |
| `test_webhook_notifications.py` | Webhook URL validation, provider detection and per-event notification switches |

## Conventions

* Keep every test offline. If a code path needs network access, stub it with
  `monkeypatch` rather than skipping the test.
* Restore module-level globals you change. Tests share one imported module, so a
  leaked global affects whatever runs next.
* Exported secrets are cleared before every test, because loading a dotenv writes
  them into `os.environ` and nothing removes them again. Set the one a test needs
  with `monkeypatch.setenv` inside that test.
* Replace GitHub calls and notification delivery with test doubles.
* Never use a real GitHub personal access token, SMTP password or webhook URL.

A change to the monitoring loop, authentication or GitHub data handling is not
verified by this suite alone. Exercise it against a real account and say so in the
pull request, without usernames or credentials.
