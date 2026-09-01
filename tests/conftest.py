"""Shared pytest fixtures and import setup for the offline test suite.

These tests never touch the network. They import the single-file
``github_monitor`` module and use test doubles for GitHub API objects.
"""

import os
import sys

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
elif sys.path.index(_PROJECT_ROOT) != 0:
    sys.path.remove(_PROJECT_ROOT)
    sys.path.insert(0, _PROJECT_ROOT)

import github_monitor as gm


# Fails fast when pytest imports an installed module instead of the working tree
def _assert_in_repo_module() -> None:
    resolved = os.path.abspath(gm.__file__)
    expected = os.path.join(_PROJECT_ROOT, "github_monitor.py")
    assert resolved == expected, f"Tests imported the wrong github_monitor module\n  imported: {resolved}\n  expected: {expected}"


_assert_in_repo_module()


@pytest.fixture
# Exposes the imported module to every test
def gm_module():
    return gm


@pytest.fixture(autouse=True)
# Resets module globals used by offline helpers to deterministic values
def deterministic_globals(monkeypatch):
    monkeypatch.setattr(gm, "LOCAL_TIMEZONE", "UTC", raising=False)
    monkeypatch.setattr(gm, "GITHUB_CHECK_INTERVAL", 60, raising=False)
    monkeypatch.setattr(gm, "VERBOSE_MODE", False, raising=False)
    monkeypatch.setattr(gm, "DEBUG_MODE", False, raising=False)
    monkeypatch.setattr(gm, "SECRET_SOURCES", {}, raising=False)
    monkeypatch.setattr(gm, "REPO_NOTIFICATION", False, raising=False)
    monkeypatch.setattr(gm, "PROFILE_NOTIFICATION", False, raising=False)
    monkeypatch.setattr(gm, "RECEIVER_EMAIL", "alerts@example.test", raising=False)
    monkeypatch.setattr(gm, "SMTP_SSL", True, raising=False)
    monkeypatch.setattr(gm, "CSV_FILE", "", raising=False)
    yield
