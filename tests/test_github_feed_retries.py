"""Exercise retry exhaustion through real PyGithub clients and paginated responses."""

import ast
import inspect
import json
from urllib.parse import urlsplit

import pytest
import requests


# Stops the infinite monitor after a failed check and a subsequent successful check
class MonitorComplete(BaseException):
    pass


# Supplies the profile fields that the real PyGithub objects read during monitoring
def profile_payload(login):
    return {"login": login, "id": 1, "type": "User", "name": login, "url": f"https://api.github.com/users/{login}", "html_url": f"https://github.com/{login}", "followers": 1, "following": 1, "public_repos": 1, "created_at": "2020-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z", "bio": None, "location": None, "company": None, "email": None, "blog": ""}


# Builds a real HTTP response for the library's normal status and payload handling
def github_response(request, payload, status=200):
    response = requests.Response()
    response.request = request
    response.url = request.url
    response.status_code = status
    response.headers["Content-Type"] = "application/json"
    response._content = json.dumps(payload).encode()
    return response


@pytest.mark.parametrize("fail_detail", [False, True])
# Preserves one unavailable repository while monitoring other repositories and recovering its changes
def test_repository_details_recover_without_losing_the_comparison(gm_module, monkeypatch, capsys, restored_globals, fail_detail):
    gm = gm_module
    settings = {"GITHUB_TOKEN": "synthetic-token", "GITHUB_CHECK_INTERVAL": 0, "NET_MAX_RETRIES": 1, "NET_BASE_BACKOFF_SEC": 0, "TRACK_REPOS_CHANGES": True, "TRACK_CONTRIB_CHANGES": False, "DO_NOT_MONITOR_GITHUB_EVENTS": True, "WEBHOOK_ENABLED": False, "ERROR_NOTIFICATION": False, "LIVENESS_REMINDER_SECONDS": 0}
    for key, value in settings.items():
        monkeypatch.setattr(gm, key, value)
    lookups = 0
    failures = []

    # Returns complete metadata with a change made during the failed detail check
    def repository(name):
        return {"id": 1 if name == "alpha" else 2, "name": name, "full_name": f"watched/{name}", "owner": profile_payload("watched"), "url": f"https://api.github.com/repos/watched/{name}", "html_url": f"https://github.com/watched/{name}", "description": "changed description" if lookups >= 2 else "original description", "fork": False, "forks_count": 0, "stargazers_count": 0, "subscribers_count": 0, "language": "Python", "has_discussions": False, "created_at": "2020-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}

    # Substitutes HTTP responses while retaining real clients, lazy objects and iterators
    def send(session, request, **kwargs):
        nonlocal lookups
        path = urlsplit(request.url).path
        if path == "/users/watched":
            lookups += 1
            if lookups == 5:
                raise MonitorComplete
            payload = profile_payload("watched")
            payload.update(followers=0, following=0, public_repos=2)
            return github_response(request, payload)
        if path == "/user":
            return github_response(request, profile_payload("viewer"))
        if path == "/users/watched/repos":
            return github_response(request, [repository("alpha"), repository("beta")])
        if path == "/repos/watched/alpha/forks" and lookups == 2 and fail_detail:
            failures.append(path)
            return github_response(request, {"message": "API rate limit exceeded"}, 403)
        if path.startswith("/repos/watched/") and path.endswith(("/forks", "/issues", "/pulls")):
            return github_response(request, [])
        if path == "/graphql":
            return github_response(request, {"data": {"user": {"viewerCanFollow": True}}})
        if request.url.startswith("https://github.com/"):
            response = github_response(request, {})
            response._content = b"<html><body>Activity is private</body></html>"
            return response
        if path.startswith("/users/watched/"):
            return github_response(request, [])
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    monkeypatch.setattr(requests.Session, "send", send)
    with pytest.raises(MonitorComplete):
        gm.github_monitor_user("watched", "")
    output = capsys.readouterr().out
    assert len(failures) == int(fail_detail)
    assert output.count("Repo 'alpha' description changed from:") == 1
    assert output.count("Repo 'beta' description changed from:") == 1
    assert "Stargazers identities" not in output
    assert "Watchers identities" not in output
    assert "The monitoring check did not return usable data" not in output


@pytest.mark.parametrize("feed,all_repos,detail_only", [("following", False, False), ("followers", False, False), ("repos", False, False), ("repos", True, False), ("starred", False, False), ("events", False, False), ("repos", False, True), ("repos", True, True)])
# Retries lazy feed failures and resumes monitoring without reporting unchanged items as removed
def test_failed_feed_keeps_its_snapshot_and_monitoring_continues(gm_module, monkeypatch, capsys, restored_globals, feed, all_repos, detail_only):
    gm = gm_module
    for key, value in {"GITHUB_TOKEN": "synthetic-token", "GITHUB_CHECK_INTERVAL": 0, "NET_MAX_RETRIES": 2, "NET_BASE_BACKOFF_SEC": 0, "GET_ALL_REPOS": all_repos, "TRACK_REPOS_CHANGES": detail_only, "TRACK_CONTRIB_CHANGES": False, "DO_NOT_MONITOR_GITHUB_EVENTS": False, "WEBHOOK_ENABLED": False, "ERROR_NOTIFICATION": False, "EVENT_NOTIFICATION": False, "LIVENESS_REMINDER_SECONDS": 0}.items():
        monkeypatch.setattr(gm, key, value)
    lookups = 0
    failures = []
    repo_refresh_requests = 0

    # Fails only the selected feed during the first refresh and leaves subsequent responses unchanged
    def send(session, request, **kwargs):
        nonlocal lookups, repo_refresh_requests
        path = urlsplit(request.url).path
        if path == "/users/watched":
            lookups += 1
            if lookups == 4:
                raise MonitorComplete
            payload = profile_payload("watched")
            if detail_only:
                payload["public_repos"] = 0
            return github_response(request, payload)
        if path == "/user":
            return github_response(request, profile_payload("viewer"))
        if path == "/users/watched/repos" and lookups == 2:
            repo_refresh_requests += 1
        if path == f"/users/watched/{feed}" and lookups == 2 and (not detail_only or repo_refresh_requests > 1):
            failures.append(request.url)
            return github_response(request, {"message": "API rate limit exceeded"}, 403)
        if request.url.startswith("https://github.com/"):
            response = github_response(request, {})
            response._content = b"<html><body>Activity is private</body></html>"
            return response
        if path in ("/users/watched/following", "/users/watched/followers"):
            return github_response(request, [profile_payload("friend")])
        if path in ("/users/watched/repos", "/users/watched/starred"):
            if detail_only and path.endswith("/repos"):
                return github_response(request, [])
            return github_response(request, [{"id": 2, "name": "repo", "full_name": "watched/repo", "fork": False, "owner": profile_payload("watched"), "url": "https://api.github.com/repos/watched/repo"}])
        if path == "/users/watched/events":
            return github_response(request, [])
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    monkeypatch.setattr(requests.sessions.Session, "send", send)
    with pytest.raises(MonitorComplete):
        gm.github_monitor_user("watched", "")

    output = capsys.readouterr().out
    assert len(failures) == 2
    assert "could not be refreshed" in output
    assert "Removed" not in output and "removed" not in output


# Resolves retry settings after configuration loads and preserves the final real library exception
def test_retry_settings_reach_the_request_and_preserve_failure(gm_module, monkeypatch, tmp_path):
    config = tmp_path / "monitor.conf"
    config.write_text("NET_MAX_RETRIES=1\nNET_BASE_BACKOFF_SEC=0\n", encoding="utf-8")
    monkeypatch.setattr(gm_module, "NET_MAX_RETRIES", gm_module.NET_MAX_RETRIES)
    monkeypatch.setattr(gm_module, "NET_BASE_BACKOFF_SEC", gm_module.NET_BASE_BACKOFF_SEC)
    assert gm_module.load_config_file(config)
    calls = []

    # Returns a rate limit through the real client's HTTP transport
    def send(session, request, **kwargs):
        calls.append(request.url)
        return github_response(request, {"message": "API rate limit exceeded"}, 403)

    monkeypatch.setattr(requests.sessions.Session, "send", send)
    client = gm_module.Github(auth=gm_module.Auth.Token("synthetic-token"))
    with pytest.raises(gm_module.RateLimitExceededException) as caught:
        gm_module.gh_call(lambda: list(client.get_user("watched").get_events()), raise_on_failure=True)()
    assert caught.value.status == 403
    assert len(calls) == 1


@pytest.mark.parametrize("feed", ["following", "followers", "repos", "starred", "events"])
# Alerts once per failed-feed outage and re-arms only after a complete successful check
def test_failed_feed_alerts_until_whole_check_recovers(gm_module, monkeypatch, capsys, restored_globals, feed):
    gm = gm_module
    settings = {"GITHUB_TOKEN": "synthetic-token", "GITHUB_CHECK_INTERVAL": 0, "NET_MAX_RETRIES": 1, "NET_BASE_BACKOFF_SEC": 0, "TRACK_REPOS_CHANGES": False, "TRACK_CONTRIB_CHANGES": False, "DO_NOT_MONITOR_GITHUB_EVENTS": False, "WEBHOOK_ENABLED": True, "WEBHOOK_ERROR_NOTIFICATION": True, "WEBHOOK_PROVIDER": "ntfy", "WEBHOOK_URL": "https://ntfy.sh/synthetic-test-topic", "ERROR_NOTIFICATION": False, "EVENT_NOTIFICATION": False, "LIVENESS_REMINDER_SECONDS": 0}
    for key, value in settings.items():
        monkeypatch.setattr(gm, key, value)
    lookups = 0
    deliveries = []

    # Returns repeated feed failures around one healthy check through the real PyGithub transport
    def send(session, request, **kwargs):
        nonlocal lookups
        path = urlsplit(request.url).path
        if request.url.startswith("https://ntfy.sh/"):
            deliveries.append(lookups)
            return github_response(request, {"id": "synthetic-delivery"})
        if path == "/users/watched":
            lookups += 1
            if lookups == 6:
                raise MonitorComplete
            payload = profile_payload("watched")
            payload.update(followers=0, following=0, public_repos=0)
            return github_response(request, payload)
        if path == "/graphql":
            return github_response(request, {"data": {"user": {"viewerCanFollow": True}}})
        if path == "/user":
            return github_response(request, profile_payload("viewer"))
        if path == f"/users/watched/{feed}" and lookups in {2, 3, 5}:
            return github_response(request, {"message": "Bad credentials"}, 401)
        if request.url.startswith("https://github.com/"):
            response = github_response(request, {})
            response._content = b"<html><body>Activity is private</body></html>"
            return response
        if path in {"/users/watched/following", "/users/watched/followers", "/users/watched/repos", "/users/watched/starred", "/users/watched/events"}:
            return github_response(request, [])
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    monkeypatch.setattr(requests.Session, "send", send)
    with pytest.raises(MonitorComplete):
        gm.github_monitor_user("watched", "")
    # The failed feed alerts on check 2, the complete check on 4 answers it with a recovery alert and check 5 fails again
    assert deliveries == [2, 4, 5]
    output = capsys.readouterr().out
    assert "GitHub rejected the configured token" in output


# Every monitoring request the tool makes, whichever transport it uses
RETRYING_FEEDS = {
    "starred count": lambda gm: gm.get_starred_count("watched"),
    "profile visibility": lambda gm: gm.has_private_banner("watched"),
    "block status": lambda gm: gm.is_blocked_by("watched"),
    "daily contributions": lambda gm: gm.get_daily_contributions("watched", token="synthetic-token"),
}


# Installs a transport that refuses every request and counts the attempts it was given
def refusing_transport(monkeypatch, calls, error=None):
    def send(session, request, **kwargs):
        calls.append(request.url)
        raise error or requests.ConnectionError("Connection refused")

    monkeypatch.setattr(requests.sessions.Session, "send", send)


@pytest.mark.parametrize("feed", sorted(RETRYING_FEEDS))
# One blip must not kill one feed while another rides it out, so every feed shares the same retry schedule
def test_every_monitoring_feed_retries_a_transport_failure(gm_module, monkeypatch, restored_globals, feed):
    gm = gm_module
    monkeypatch.setattr(gm, "GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(gm, "NET_MAX_RETRIES", 3)
    monkeypatch.setattr(gm, "NET_BASE_BACKOFF_SEC", 0)
    calls = []
    refusing_transport(monkeypatch, calls)

    try:
        RETRYING_FEEDS[feed](gm)
    except Exception:
        # Some feeds report the failure to their caller and some swallow it, but both retried first
        pass

    assert len(calls) == 3


# A check that already proved the network unreachable learns nothing from making every later feed wait for it
def test_a_confirmed_outage_stops_the_later_calls_from_retrying(gm_module, monkeypatch, restored_globals):
    gm = gm_module
    monkeypatch.setattr(gm, "GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(gm, "NET_MAX_RETRIES", 4)
    monkeypatch.setattr(gm, "NET_BASE_BACKOFF_SEC", 0)
    calls = []
    refusing_transport(monkeypatch, calls)

    gm.get_starred_count("watched")
    first = len(calls)
    gm.has_private_banner("watched")

    assert first == 4
    assert len(calls) - first == 1
    assert gm.NET_OUTAGE_CONFIRMED is True


# The breaker must not outlast the outage, so a call that gets through arms the full schedule again
def test_a_call_that_gets_through_rearms_the_retry_schedule(gm_module, monkeypatch, restored_globals):
    gm = gm_module
    monkeypatch.setattr(gm, "GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(gm, "NET_MAX_RETRIES", 3)
    monkeypatch.setattr(gm, "NET_BASE_BACKOFF_SEC", 0)
    monkeypatch.setattr(gm, "NET_OUTAGE_CONFIRMED", True)
    calls = []

    def send(session, request, **kwargs):
        calls.append(request.url)
        if len(calls) == 1:
            return github_response(request, {"data": {"user": {"starredRepositories": {"totalCount": 7}}}})
        raise requests.ConnectionError("Connection refused")

    monkeypatch.setattr(requests.sessions.Session, "send", send)

    assert gm.get_starred_count("watched") == 7
    assert gm.NET_OUTAGE_CONFIRMED is False
    gm.has_private_banner("watched")
    assert len(calls) - 1 == 3


# A failure that answers the same way every time is not worth a schedule, and a local limit gets worse for one
@pytest.mark.parametrize("error", [None, "descriptors"])
def test_a_permanent_failure_is_not_retried(gm_module, monkeypatch, restored_globals, error):
    gm = gm_module
    monkeypatch.setattr(gm, "GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(gm, "NET_MAX_RETRIES", 5)
    monkeypatch.setattr(gm, "NET_BASE_BACKOFF_SEC", 0)
    calls = []

    if error == "descriptors":
        refusing_transport(monkeypatch, calls, requests.ConnectionError("Connection failed"))
        monkeypatch.setattr(gm, "is_too_many_open_files", lambda failure: True)
    else:
        def send(session, request, **kwargs):
            calls.append(request.url)
            return github_response(request, {"message": "Not Found"}, 404)

        monkeypatch.setattr(requests.sessions.Session, "send", send)

    client = gm.Github(auth=gm.Auth.Token("synthetic-token"))
    with pytest.raises(BaseException):
        gm.gh_call(lambda: client.get_user("watched").name, operation="Profile name", raise_on_failure=True)()

    assert len(calls) == 1


# A retry line and the degraded notice that follows it report one fetch, so a reader must not see two names
@pytest.mark.parametrize("feed,name", [("starred count", "Starred repository count"), ("profile visibility", "Profile visibility"), ("block status", "Block status")])
def test_a_retry_line_and_its_degraded_notice_name_one_feed(gm_module, monkeypatch, capsys, restored_globals, feed, name):
    gm = gm_module
    monkeypatch.setattr(gm, "GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(gm, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm, "NET_MAX_RETRIES", 2)
    monkeypatch.setattr(gm, "NET_BASE_BACKOFF_SEC", 0)
    refusing_transport(monkeypatch, [])

    RETRYING_FEEDS[feed](gm)

    output = capsys.readouterr().out
    assert f"* {name} failed:" in output
    assert f"{name}: unavailable" in output


# Collects the labels a retry line prints beside the feature names a degraded notice reports
def retry_labels_and_feature_names(gm):
    tree = ast.parse(inspect.getsource(gm))
    raising, features = set(), set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        if name == "gh_call":
            operation = keywords.get("operation")
            raises = keywords.get("raise_on_failure")
            if isinstance(operation, ast.Constant) and isinstance(raises, ast.Constant) and raises.value:
                raising.add(operation.value)
        if name == "verbose_degraded_feature" and node.args and isinstance(node.args[0], ast.Constant):
            features.add(node.args[0].value)
    return raising, features


# A fetch whose caller reports it under another name reads as two separate failures a few lines apart
def test_every_retry_label_matches_the_feature_its_caller_reports(gm_module):
    raising, features = retry_labels_and_feature_names(gm_module)

    assert raising, "the sweep stopped finding raising calls, update its matching"
    assert not raising - features, "a retry line names a fetch its degraded notice calls something else: " + ", ".join(sorted(raising - features))
