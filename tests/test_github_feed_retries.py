"""Exercise retry exhaustion through real PyGithub clients and paginated responses."""

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
    assert deliveries == [2, 5]
    output = capsys.readouterr().out
    assert "GitHub rejected the configured token" in output
