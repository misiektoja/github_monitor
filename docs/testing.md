# Testing

The offline test suite covers everything in `github_monitor.py` that can run without network access. GitHub API objects are replaced with test doubles, so the suite needs no GitHub account, no network and no credentials.

## Running the suite

From the repository root:

```sh
pip install -e '.[test]'
python -m pytest
```

`pyproject.toml` puts the repository root first on `sys.path`, so the tests exercise the working tree rather than an installed copy.

Run the linter the same way CI does:

```sh
pip install -e '.[lint]'
python -m ruff check github_monitor.py tests
```

Build this documentation the way CI does, which fails on a broken link or a missing page:

```sh
pip install -r docs/requirements.txt
mkdocs build --strict
```

CI runs all three on every push and pull request, across Python 3.10 through 3.14, and again before anything is published to PyPI.

## What is covered

The test layout mirrors the surfaces a user touches rather than the module layout. See [tests/README.md](https://github.com/misiektoja/github_monitor/blob/main/tests/README.md) for the file-by-file map.

## Conventions

* Keep every test offline. If a code path needs network access, stub it with `monkeypatch` rather than skipping the test.
* Restore module-level globals you change. Tests share one imported module, so a leaked global affects whatever runs next.
* Exported secrets are cleared before every test, because loading a dotenv writes them into `os.environ` and nothing removes them again. Set the one a test needs with `monkeypatch.setenv` inside that test.
* Never use a real GitHub personal access token, SMTP password or webhook URL.

A change to the monitoring loop, authentication or GitHub data handling is not verified by this suite alone. Exercise it against a real account and say so in the pull request, without usernames or credentials.
