"""Offline tests for deleted-account and deleted-repository notes on removed list items."""

from types import SimpleNamespace


# Confirms removed_item_note covers each supported list type and stays quiet for other labels
def test_removed_item_note_variants(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: False)
    monkeypatch.setattr(gm_module, "github_repo_exists", lambda full_name: False)
    assert gm_module.removed_item_note("Stargazers", "ghosted") == " (account no longer exists)"
    assert gm_module.removed_item_note("Watchers", "ghosted") == " (account no longer exists)"
    assert gm_module.removed_item_note("Followers", "ghosted") == " (account no longer exists)"
    assert gm_module.removed_item_note("Followings", "ghosted") == " (account no longer exists)"
    assert gm_module.removed_item_note("Forks", "ghosted/monitor") == " (owner account no longer exists)"
    assert gm_module.removed_item_note("Starred Repos", "ghosted/monitor") == " (repository no longer exists)"
    assert gm_module.removed_item_note("Repos", "gone", "owner") == " (repository no longer exists)"
    assert gm_module.removed_item_note("Discussions", "#7 How should this work? (octocat)") == ""


# Confirms failed or positive existence checks leave removed items unannotated
def test_removed_item_note_requires_confirmed_absence(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: True)
    assert gm_module.removed_item_note("Stargazers", "active") == ""
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: None)
    assert gm_module.removed_item_note("Stargazers", "flaky") == ""


# Confirms removed stargazers with deleted accounts are annotated in console output and email HTML
def test_removed_stargazer_notes_deleted_account(gm_module, monkeypatch, capsys):
    emails = []
    monkeypatch.setattr(gm_module, "GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setattr(gm_module, "REPO_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "send_email", lambda *args, **kwargs: emails.append((args, kwargs)) or 0)
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: False)
    gm_module.check_repo_list_changes(1, 0, ["ghosted"], [], "Stargazers", "monitor", "https://github.com/owner/monitor", "owner", "")
    output = capsys.readouterr().out
    assert "- ghosted [ https://github.com/ghosted/ ] (account no longer exists)" in output
    assert emails[0][0][1].count("(account no longer exists)") == 1
    assert '<a href="https://github.com/ghosted/">ghosted</a> (account no longer exists)<br>' in emails[0][0][2]


# Confirms removed stargazers with live accounts stay unannotated
def test_removed_stargazer_with_live_account_has_no_note(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: True)
    gm_module.check_repo_list_changes(1, 0, ["active"], [], "Stargazers", "monitor", "https://github.com/owner/monitor", "owner", "")
    output = capsys.readouterr().out
    assert "- active [ https://github.com/active/ ]" in output
    assert "no longer exists" not in output


# Confirms removed forks check the fork owner's login and annotate deleted owners
def test_removed_fork_notes_deleted_owner(gm_module, monkeypatch, capsys):
    checked = []
    monkeypatch.setattr(gm_module, "GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: checked.append(login) or False)
    gm_module.check_repo_list_changes(1, 0, ["ghosted/monitor"], [], "Forks", "monitor", "https://github.com/owner/monitor", "owner", "")
    output = capsys.readouterr().out
    assert checked == ["ghosted"]
    assert "- ghosted/monitor [ https://github.com/ghosted/monitor/ ] (owner account no longer exists)" in output


# Confirms removed followers with deleted accounts are annotated while added items stay plain
def test_removed_follower_notes_deleted_account(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: False)
    result = gm_module.handle_profile_change("Followers", 1, 1, ["ghosted"], [SimpleNamespace(login="active")], "owner", "", field="login")
    output = capsys.readouterr().out
    assert "- ghosted [ https://github.com/ghosted/ ] (account no longer exists)" in output
    assert "- active [ https://github.com/active/ ]\n" in output
    assert result == (["active"], 1)
