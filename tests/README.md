# Offline test suite

These tests cover logic in `github_monitor.py` that can run without network
access. GitHub API objects are replaced with test doubles.

## Running

From the repository root:

```bash
pip install -e '.[test]'
python -m pytest
```

`pyproject.toml` puts the repository root first on `sys.path`. `conftest.py`
enforces the same order so tests always use the working tree.

## Layout

| File | Area under test |
| --- | --- |
| `test_daily_contributions.py` | Stable calendar window selection and missing-day handling |
| `test_repository_monitoring.py` | Discussion collection, repository snapshots, open and closed notifications, event formatting |
| `test_profile_fields.py` | Addition, removal and failure handling for nullable profile fields |
| `test_event_configuration.py` | Supported event types, intentional 30-event window and retry defaults |
| `test_repository_metadata.py` | Governance files, citation, funding, line endings, the declared editor style, the pinned linter and release integrity |

## Conventions

* Keep every test offline
* Use the `gm_module` fixture to access the imported module
* Replace GitHub calls and notification delivery with test doubles
* Reset module globals in the autouse fixture when new helpers depend on them
