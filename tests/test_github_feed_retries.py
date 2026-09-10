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
