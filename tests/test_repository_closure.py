"""Verify missing repository items through bounded real HTTP request handling."""

import copy
import json
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlsplit

import pytest
import requests


KINDS = (("issues", "Issues"), ("pulls", "Pull Requests"), ("discussions", "Discussions"))


# Builds repository feeds with independently mutable issue, pull request and discussion lists
def repository(name="monitor"):
    repo = SimpleNamespace(name=name, full_name=f"owner/{name}", description="Repository", fork=False, forks_count=0, stargazers_count=0, subscribers_count=0, html_url=f"https://github.example/owner/{name}", language="Python", created_at=datetime(2025, 1, 1), updated_at=datetime(2025, 1, 1), has_discussions=True, issues=[], pulls=[], discussions=[])
    repo.get_stargazers = lambda: []
    repo.get_subscribers = lambda: []
    repo.get_forks = lambda: []
    repo.get_issues = lambda state: repo.issues
    repo.get_pulls = lambda state: repo.pulls
    repo.get_discussions = lambda schema, states: repo.discussions
    return repo


# Builds an open item using the attributes read by the repository collector
def item(repo, kind, number=60, title="Still open"):
    return SimpleNamespace(number=number, title=title, user=SimpleNamespace(login="author"), author=SimpleNamespace(login="author"), html_url=f"{repo.html_url}/{kind}/{number}", pull_request=None)


# Returns an HTTP response consumed by the normal requests transport
def response_for(request, payload, status=200):
    response = requests.Response()
    response.request = request
    response.url = request.url
    response.status_code = status
    response.headers["Content-Type"] = "application/json"
    response._content = json.dumps(payload).encode()
    return response


# Builds a direct lookup response for the requested type and state
def state_payload(kind, number=60, closed=False) -> dict[str, Any]:
    if kind == "discussions":
        return {"data": {"repository": {"discussion": {"number": number, "closed": closed}}}}
    return {"number": number, "state": "closed" if closed else "open"}


# Collects snapshots through the production reconciliation path
def collect(gm, repos, previous, verifier):
    return gm.github_process_repos(repos, show_progress=False, fetch_identity_lists=False, previous_repos=previous, closure_verifier=verifier)


# Compares collected snapshots through the production notification path
def report(gm, old, new, kind, label):
    gm.check_repo_list_changes(old[kind], new[kind], old[f"{kind}_list"], new[f"{kind}_list"], label, new["name"], new["url"], "owner", "")


@pytest.mark.parametrize("kind,label", KINDS)
# A single incomplete list never emits a closure or a subsequent addition
def test_transient_disappearance_preserves_baseline(gm_module, monkeypatch, kind, label):
    gm = gm_module
    repo = repository()
    getattr(repo, kind).append(item(repo, kind))
    verifier = gm.RepositoryClosureVerifier()
    calls = []
    deliveries = []

    # Keeps the missing item open through its actual HTTP response
    def send(session, request, **kwargs):
        calls.append(request)
        assert session.get_adapter(request.url).max_retries.total == 0
        assert kwargs["allow_redirects"] is False
        return response_for(request, state_payload(kind))

    monkeypatch.setattr(requests.Session, "send", send)
    monkeypatch.setattr(gm, "send_notification_channels", lambda *args: deliveries.append(args))
    baseline = collect(gm, [repo], [], verifier)
    unchanged = collect(gm, [repo], baseline, verifier)
    assert not calls
    getattr(repo, kind).clear()
    missing = collect(gm, [repo], unchanged, verifier)
    report(gm, unchanged[0], missing[0], kind, label)
    assert missing[0][kind] == 1
    assert missing[0][f"{kind}_list"] == baseline[0][f"{kind}_list"]
    getattr(repo, kind).append(item(repo, kind))
    recovered = collect(gm, [repo], missing, verifier)
    report(gm, missing[0], recovered[0], kind, label)
    assert len(calls) == 1
    assert deliveries == []
    assert not verifier.pending


@pytest.mark.parametrize("kind,label", KINDS)
# Confirmed closures are reported once while new items remain visible
def test_confirmed_closure_and_new_item_notify_once(gm_module, monkeypatch, kind, label):
    gm = gm_module
    repo = repository()
    getattr(repo, kind).append(item(repo, kind))
    verifier = gm.RepositoryClosureVerifier()
    calls = []
    deliveries = []

    # Confirms only the old item as closed
    def send(session, request, **kwargs):
        calls.append(request)
        payload = state_payload(kind, closed=True)
        if kind == "pulls":
            payload["merged"] = True
        return response_for(request, payload)

    monkeypatch.setattr(requests.Session, "send", send)
    monkeypatch.setattr(gm, "send_notification_channels", lambda *args: deliveries.append(args))
    previous = collect(gm, [repo], [], verifier)
    original = copy.deepcopy(previous)
    setattr(repo, kind, [item(repo, kind, number=61)])
    current = collect(gm, [repo], previous, verifier)
    assert previous == original
    report(gm, previous[0], current[0], kind, label)
    assert current[0][kind] == 1
    assert len(deliveries) == 1
    assert f"Closed {label.lower()}:" in deliveries[0][2]
    assert "#60 Still open" in deliveries[0][2]
    assert "#61 Still open" in deliveries[0][2]
    next_snapshot = collect(gm, [repo], current, verifier)
    report(gm, current[0], next_snapshot[0], kind, label)
    assert len(calls) == 1
    assert len(deliveries) == 1


@pytest.mark.parametrize("kind,label", KINDS)
@pytest.mark.parametrize("failure", [301, 401, 403, 404, 410, 429, 503, "timeout", "invalid_json", "missing_state", "wrong_number"])
# Failed or unusable verification leaves the old state available for a later successful closure
def test_failed_verification_defers_and_recovers(gm_module, monkeypatch, kind, label, failure):
    gm = gm_module
    repo = repository()
    getattr(repo, kind).append(item(repo, kind))
    verifier = gm.RepositoryClosureVerifier()
    calls = []

    # Fails one request without allowing automatic retries or redirect following
    def send(session, request, **kwargs):
        calls.append(request)
        if len(calls) > 1:
            return response_for(request, state_payload(kind, closed=True))
        if failure == "timeout":
            raise requests.Timeout("Synthetic timeout")
        payload = state_payload(kind, number=61 if failure == "wrong_number" else 60, closed=True)
        if failure == "missing_state":
            payload = {"number": 60}
        response = response_for(request, payload, failure if isinstance(failure, int) else 200)
        response.headers["Location"] = "https://elsewhere.example/item"
        if failure == "invalid_json":
            response._content = b"invalid json"
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    previous = collect(gm, [repo], [], verifier)
    getattr(repo, kind).clear()
    deferred = collect(gm, [repo], previous, verifier)
    assert deferred[0][kind] == 1
    assert len(calls) == 1
    closed = collect(gm, [repo], deferred, verifier)
    assert closed[0][kind] == 0
    assert len(calls) == 2


@pytest.mark.parametrize("payload", [{"data": {"repository": None}}, {"data": {"repository": {"discussion": None}}}, {"data": {"repository": {"discussion": {"number": 60, "closed": "true"}}}}, {"data": {"repository": {"discussion": {"number": 60, "closed": True}}}, "errors": [{"message": "Partial response"}]}])
# Null discussion objects and GraphQL errors never establish closure
def test_incomplete_graphql_response_is_not_a_closure(gm_module, monkeypatch, payload):
    monkeypatch.setattr(requests.Session, "send", lambda session, request, **kwargs: response_for(request, payload))
    assert gm_module.github_verify_repository_closure("owner/monitor", "discussions", 60) is None


# One allowance covers every repository and type while deferred checks rotate across cycles
def test_shared_budget_and_fair_rotation(gm_module, monkeypatch):
    gm = gm_module
    repos = [repository("first"), repository("second")]
    for repo in repos:
        for kind, _ in KINDS:
            getattr(repo, kind).append(item(repo, kind))
    verifier = gm.RepositoryClosureVerifier()
    calls = []

    # Leaves all candidates pending to expose starvation or excess requests
    def send(session, request, **kwargs):
        if request.method == "POST":
            variables = json.loads(request.body)["variables"]
            key = (variables["name"], "discussions")
        else:
            path = urlsplit(request.url).path.split("/")
            key = (path[-3], path[-2])
        calls.append(key)
        return response_for(request, {}, 503)

    monkeypatch.setattr(requests.Session, "send", send)
    previous = collect(gm, repos, [], verifier)
    for repo in repos:
        for kind, _ in KINDS:
            getattr(repo, kind).clear()
    current = collect(gm, repos, previous, verifier)
    assert len(calls) == 5
    assert all(repo[kind] == 1 for repo in current for kind, _ in KINDS)
    next_snapshot = collect(gm, repos, current, verifier)
    assert len(calls) == 10
    assert len(set(calls[:6])) == 6
    assert all(repo[kind] == 1 for repo in next_snapshot for kind, _ in KINDS)


@pytest.mark.parametrize("kind,label", KINDS)
# Editing an item's display text neither consumes verification requests nor emits membership alerts
def test_title_edit_uses_stable_identity(gm_module, monkeypatch, kind, label):
    gm = gm_module
    repo = repository()
    getattr(repo, kind).append(item(repo, kind))
    verifier = gm.RepositoryClosureVerifier()
    deliveries = []
    monkeypatch.setattr(gm, "send_notification_channels", lambda *args: deliveries.append(args))
    monkeypatch.setattr(requests.Session, "send", lambda *args, **kwargs: pytest.fail("Unexpected verification"))
    previous = collect(gm, [repo], [], verifier)
    getattr(repo, kind)[0].title = "Updated title"
    current = collect(gm, [repo], previous, verifier)
    report(gm, previous[0], current[0], kind, label)
    assert "Updated title" in current[0][f"{kind}_list"][0]
    assert deliveries == []


@pytest.mark.parametrize("kind", ["issues", "pulls", "discussions"])
@pytest.mark.parametrize("api_url", ["https://api.github.com", "https://git.example/api/v3/"])
# Verification uses the configured API, current credentials and TLS choice in exactly one request
def test_verification_transport_settings(gm_module, monkeypatch, kind, api_url):
    gm = gm_module
    monkeypatch.setattr(gm, "GITHUB_API_URL", api_url)
    monkeypatch.setattr(gm, "GITHUB_TOKEN", "first-token")
    monkeypatch.setattr(gm, "VERIFY_SSL", False)
    calls = []

    # Checks actual prepared requests and transport options
    def send(session, request, **kwargs):
        calls.append(request)
        if kind == "discussions":
            # A substring check on the fixture URL, not a URL allowlist
            # codeql[py/incomplete-url-substring-sanitization]
            expected = "https://api.github.com/graphql" if "api.github.com" in api_url else "https://git.example/api/graphql"
            assert request.method == "POST"
            assert json.loads(request.body)["variables"] == {"owner": "owner", "name": "monitor", "number": 60}
        else:
            expected = api_url.rstrip("/") + f"/repos/owner/monitor/{kind}/60"
            assert request.method == "GET"
        assert request.url == expected
        assert request.headers["Authorization"] == f"Bearer {gm.GITHUB_TOKEN}"
        assert kwargs["verify"] is False
        assert kwargs["allow_redirects"] is False
        assert kwargs["timeout"] == gm.PYGITHUB_TIMEOUT_SECONDS
        assert session.get_adapter(request.url).max_retries.total == 0
        return response_for(request, state_payload(kind))

    monkeypatch.setattr(requests.Session, "send", send)
    assert gm.github_verify_repository_closure("owner/monitor", kind, 60) is False
    monkeypatch.setattr(gm, "GITHUB_TOKEN", "rotated-token")
    assert gm.github_verify_repository_closure("owner/monitor", kind, 60) is False
    assert len(calls) == 2


@pytest.mark.parametrize("kind,label", KINDS)
# Disabling verification through a loaded configuration restores immediate disappearance alerts
def test_configuration_can_restore_legacy_behavior(gm_module, monkeypatch, tmp_path, kind, label):
    gm = gm_module
    monkeypatch.setattr(gm, "VERIFY_REPOSITORY_CLOSURES", True)
    config = tmp_path / "monitor.conf"
    config.write_text("VERIFY_REPOSITORY_CLOSURES = False\n", encoding="utf-8")
    assert gm.load_config_file(config)
    assert gm.VERIFY_REPOSITORY_CLOSURES is False
    repo = repository()
    getattr(repo, kind).append(item(repo, kind))
    verifier = gm.RepositoryClosureVerifier()
    deliveries = []
    monkeypatch.setattr(gm, "send_notification_channels", lambda *args: deliveries.append(args))
    monkeypatch.setattr(requests.Session, "send", lambda *args, **kwargs: pytest.fail("Verification is disabled"))
    previous = collect(gm, [repo], [], verifier)
    getattr(repo, kind).clear()
    current = collect(gm, [repo], previous, verifier)
    report(gm, previous[0], current[0], kind, label)
    assert current[0][kind] == 0
    assert len(deliveries) == 1
    assert f"Closed {label.lower()}:" in deliveries[0][2]
    getattr(repo, kind).append(item(repo, kind))
    recovered = collect(gm, [repo], current, verifier)
    report(gm, current[0], recovered[0], kind, label)
    assert len(deliveries) == 2
    assert f"Added {label.lower()}:" in deliveries[1][2]


# Generated configurations enable verification and reject ambiguous on/off values during validation
def test_configuration_default_and_boolean_validation(gm_module, monkeypatch, tmp_path):
    gm = gm_module
    config = tmp_path / "generated.conf"
    gm.write_generated_config(config, gm.CONFIG_BLOCK, interactive=False)
    values = {}
    assert gm.load_config_file(config, namespace=values)
    assert values["VERIFY_REPOSITORY_CLOSURES"] is True
    monkeypatch.setattr(gm, "VERIFY_REPOSITORY_CLOSURES", "False")
    assert any(error.startswith("VERIFY_REPOSITORY_CLOSURES must be True or False") for error in gm.runtime_boolean_errors())


class MonitorComplete(BaseException):
    pass


@pytest.mark.parametrize("enabled", [True, False])
# The real monitoring loop preserves a transient disappearance and still reports a later closure
def test_monitoring_loop_applies_verification_setting(gm_module, monkeypatch, restored_globals, enabled):
    gm = gm_module
    monkeypatch.setattr(gm, "stdout_bck", None)
    monkeypatch.setattr(gm.time, "sleep", lambda seconds: None)
    settings = {"GITHUB_TOKEN": "synthetic-token", "GITHUB_CHECK_INTERVAL": 0, "NET_MAX_RETRIES": 1, "TRACK_REPOS_CHANGES": True, "VERIFY_REPOSITORY_CLOSURES": enabled, "TRACK_CONTRIB_CHANGES": False, "DO_NOT_MONITOR_GITHUB_EVENTS": True, "WEBHOOK_ENABLED": False, "ERROR_NOTIFICATION": False, "LIVENESS_REMINDER_SECONDS": 0, "GET_ALL_REPOS": False, "REPOS_TO_MONITOR": ["ALL"]}
    for name, value in settings.items():
        monkeypatch.setattr(gm, name, value)
    cycle = 0
    verifications = []
    deliveries = []

    # Supplies the complete profile fields read by PyGithub and the monitor
    def profile(login):
        return {"login": login, "id": 1, "type": "User", "name": login, "url": f"https://api.github.com/users/{login}", "html_url": f"https://github.com/{login}", "followers": 0, "following": 0, "public_repos": 1, "created_at": "2020-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z", "bio": None, "location": None, "company": None, "email": None, "blog": ""}

    # Drives actual lazy PyGithub objects and direct verification through controlled HTTP responses
    def send(session, request, **kwargs):
        nonlocal cycle
        path = urlsplit(request.url).path
        if path == "/users/watched":
            cycle += 1
            if cycle == 6:
                raise MonitorComplete
            return response_for(request, profile("watched"))
        if path == "/user":
            return response_for(request, profile("viewer"))
        if path == "/users/watched/repos":
            payload = {"id": 1, "name": "monitor", "full_name": "watched/monitor", "owner": profile("watched"), "url": "https://api.github.com/repos/watched/monitor", "html_url": "https://github.com/watched/monitor", "description": "Repository", "fork": False, "forks_count": 0, "stargazers_count": 0, "subscribers_count": 0, "language": "Python", "has_discussions": False, "created_at": "2020-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}
            return response_for(request, [payload])
        if path == "/repos/watched/monitor/issues":
            payload = [{"number": 60, "title": "Open issue", "user": profile("author"), "pull_request": None, "state": "open", "url": "https://api.github.com/repos/watched/monitor/issues/60", "html_url": "https://github.com/watched/monitor/issues/60"}] if cycle in (1, 3) else []
            return response_for(request, payload)
        if path == "/repos/watched/monitor/issues/60":
            verifications.append(cycle)
            return response_for(request, state_payload("issues", closed=cycle >= 4))
        if path in ("/repos/watched/monitor/forks", "/repos/watched/monitor/pulls") or path.startswith("/users/watched/"):
            return response_for(request, [])
        if path == "/graphql":
            return response_for(request, {"data": {"user": {"viewerCanFollow": True}}})
        if request.url.startswith("https://github.com/"):
            response = response_for(request, {})
            response._content = b"<html><body>Activity is private</body></html>"
            return response
        pytest.fail(f"Unexpected request: {request.method} {request.url}")

    monkeypatch.setattr(requests.Session, "send", send)
    monkeypatch.setattr(gm, "send_notification_channels", lambda *args: deliveries.append(args) or (False, False))
    with pytest.raises(MonitorComplete):
        gm.github_monitor_user("watched", "")
    repo_alerts = [args for args in deliveries if args[0] == "repo"]
    assert verifications == ([2, 4] if enabled else [])
    assert len(repo_alerts) == (1 if enabled else 3)
    assert "Closed issues:" in repo_alerts[-1][2]
