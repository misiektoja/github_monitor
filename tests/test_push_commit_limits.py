"""Offline tests for the push event commit and changed-file limits."""

from datetime import datetime
from types import SimpleNamespace

import pytest


class FakeEventRepo:
    id = 1
    name = "owner/monitor"
    url = "https://api.github.example/repos/owner/monitor"


class FakeRepo:
    full_name = "owner/monitor"
    html_url = "https://github.example/owner/monitor"
    description = "Repository monitor"

    # Initializes a repository double that records every commit detail request
    def __init__(self, files_per_commit=2):
        self.requested = []
        self.files_per_commit = files_per_commit

    # Returns commit details and records the request the caller spent on them
    def get_commit(self, sha):
        self.requested.append(sha)
        files = [SimpleNamespace(filename=f"file{index}.py", status="modified", additions=1, deletions=1) for index in range(self.files_per_commit)]
        return SimpleNamespace(
            sha=sha,
            commit=SimpleNamespace(message=f"Commit {sha}", author=SimpleNamespace(name="Octo Cat", date=datetime(2026, 7, 25))),
            author=SimpleNamespace(html_url="https://github.example/octocat"),
            html_url=f"https://github.example/owner/monitor/commit/{sha}",
            stats=SimpleNamespace(additions=1, deletions=1, total=2),
            files=files,
        )


class FakeGithub:
    # Returns the repository double every event lookup resolves to
    def __init__(self, repo):
        self.repo = repo

    # Returns the repository double for the monitored event
    def get_repo(self, name):
        assert name == "owner/monitor"
        return self.repo


# Builds a push event whose payload carries the given number of commits
def _push_event(count):
    commits = [{"sha": f"{index:040x}", "message": f"Commit {index}", "author": {"name": "Octo Cat"}} for index in range(1, count + 1)]
    return SimpleNamespace(created_at=datetime(2026, 7, 25), id="event-1", type="PushEvent", repo=FakeEventRepo(), actor=SimpleNamespace(login="octocat", name=None, html_url="https://github.example/octocat"), payload={"ref": "refs/heads/main", "commits": commits})


@pytest.fixture(autouse=True)
# Pins the push limits to their built-in values so one test cannot leak into the next
def push_defaults(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "PUSH_COMMITS_LIMIT", 10)
    monkeypatch.setattr(gm_module, "PUSH_COMMITS_ORDER", "newest")
    monkeypatch.setattr(gm_module, "PUSH_COMMITS_OVERFLOW", "count")
    monkeypatch.setattr(gm_module, "PUSH_FILES_LIMIT", 20)


# Confirms the built-in configuration caps push detail rather than reporting every commit in full
def test_built_in_limits_are_applied_by_default(gm_module):
    built_in = gm_module.parse_config_content(gm_module.CONFIG_BLOCK, "<built-in-config>")
    assert built_in["PUSH_COMMITS_LIMIT"] == 10
    assert built_in["PUSH_COMMITS_ORDER"] == "newest"
    assert built_in["PUSH_COMMITS_OVERFLOW"] == "count"
    assert built_in["PUSH_FILES_LIMIT"] == 20


# Confirms the detailed range keeps the head of the push by default
def test_detail_range_keeps_the_newest_commits(gm_module):
    assert gm_module.push_detail_range(300, limit=10, order="newest") == (290, 300)


# Confirms the detailed range can keep the start of the pushed range instead
def test_detail_range_keeps_the_oldest_commits(gm_module):
    assert gm_module.push_detail_range(300, limit=10, order="oldest") == (0, 10)


# Confirms a push at or below the limit is reported in full
def test_detail_range_covers_a_small_push(gm_module):
    assert gm_module.push_detail_range(4, limit=10, order="newest") == (0, 4)


# Confirms a zero limit turns the cap off
def test_detail_range_without_a_limit_covers_everything(gm_module):
    assert gm_module.push_detail_range(300, limit=0, order="newest") == (0, 300)


# Confirms an oversized push spends one request per detailed commit and none on the rest
def test_large_push_only_requests_details_for_the_kept_commits(gm_module, capsys):
    repo = FakeRepo()
    _, _, _, text = gm_module.github_print_event(_push_event(25), FakeGithub(repo))
    capsys.readouterr()
    assert len(repo.requested) == 10
    assert "Number of commits:\t\t25" in text
    assert "Detailed commits:\t\t10 of 25 (newest)" in text
    assert "=== Commit 16/25 ===" in text
    assert "=== Commit 15/25 ===" not in text


# Confirms the summary mode gives the commits left undetailed one line each
def test_skipped_commits_can_be_summarized(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "PUSH_COMMITS_OVERFLOW", "summary")
    _, _, _, text = gm_module.github_print_event(_push_event(25), FakeGithub(FakeRepo()))
    capsys.readouterr()
    assert "Commits 1-15 (summary only):" in text
    assert f"• {1:040x}"[:14] in text
    assert "- 'Commit 1'" in text


# Confirms the built-in overflow mode replaces the skipped commits with a single line
def test_skipped_commits_are_reported_as_a_count(gm_module, capsys):
    _, _, _, text = gm_module.github_print_event(_push_event(25), FakeGithub(FakeRepo()))
    capsys.readouterr()
    assert "Commits 1-15 not reported in full (15 commits, PUSH_COMMITS_LIMIT is 10)" in text
    assert "(summary only)" not in text


# Confirms the oldest order details the start of the pushed range
def test_oldest_order_details_the_start_of_the_push(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "PUSH_COMMITS_ORDER", "oldest")
    _, _, _, text = gm_module.github_print_event(_push_event(25), FakeGithub(FakeRepo()))
    capsys.readouterr()
    assert "Detailed commits:\t\t10 of 25 (oldest)" in text
    assert "=== Commit 10/25 ===" in text
    assert "Commits 11-25 not reported in full" in text


# Confirms a push within the limit reports every commit in full and adds no limit notice
def test_small_push_is_reported_in_full(gm_module, capsys):
    repo = FakeRepo()
    _, _, _, text = gm_module.github_print_event(_push_event(3), FakeGithub(repo))
    capsys.readouterr()
    assert len(repo.requested) == 3
    assert "Detailed commits:" not in text
    assert "summary only" not in text


# Confirms one commit cannot fill the report with changed-file lines
def test_changed_file_list_is_capped(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "PUSH_FILES_LIMIT", 3)
    _, _, _, text = gm_module.github_print_event(_push_event(1), FakeGithub(FakeRepo(files_per_commit=10)))
    capsys.readouterr()
    assert "Files changed:\t\t10" in text
    assert "file2.py" in text
    assert "file4.py" not in text
    assert "... and 7 more files" in text


# Confirms every changed file is listed when the file limit is off
def test_changed_file_list_can_be_uncapped(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "PUSH_FILES_LIMIT", 0)
    _, _, _, text = gm_module.github_print_event(_push_event(1), FakeGithub(FakeRepo(files_per_commit=10)))
    capsys.readouterr()
    assert "file9.py" in text
    assert "more files" not in text


# Confirms unusable push limits are reported rather than silently ignored
@pytest.mark.parametrize(("name", "value", "expected"), [("PUSH_COMMITS_LIMIT", -1, "PUSH_COMMITS_LIMIT must be an integer zero or greater"), ("PUSH_FILES_LIMIT", "many", "PUSH_FILES_LIMIT must be an integer zero or greater"), ("PUSH_COMMITS_ORDER", "middle", "PUSH_COMMITS_ORDER must be 'newest' or 'oldest'"), ("PUSH_COMMITS_OVERFLOW", "", "PUSH_COMMITS_OVERFLOW must be 'summary' or 'count'")])
def test_invalid_push_settings_are_reported(gm_module, monkeypatch, name, value, expected):
    monkeypatch.setattr(gm_module, name, value)
    assert any(error.startswith(expected) for error in gm_module.runtime_configuration_errors())
