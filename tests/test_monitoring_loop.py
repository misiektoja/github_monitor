"""Offline tests for the primary monitoring loop's failure handling and the alerts it delivers."""

import datetime
from itertools import count

import pytest


# Ends one monitoring run deterministically once the harness has counted enough sleeps
class LoopStopped(Exception):
    pass


# Stands in for a repository the monitored account owns
class FakeRepo:
    def __init__(self, name, owner):
        self.name = name
        self.full_name = f"{owner}/{name}"
        self.fork = False
        self.owner = type("Owner", (), {"login": owner})()


# Stands in for one page of results, which the loop both iterates and asks for its total
class FakePage(list):
    @property
    def totalCount(self):
        return len(self)


# Stands in for the account the loop watches, with every field the initial snapshot reads
class FakeUser:
    def __init__(self, login):
        self.login = login
        self.name = "Watched Person"
        self.html_url = f"https://github.com/{login}"
        self.location = self.bio = self.company = self.email = self.blog = None
        self.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
        self.updated_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        self.followers = self.following = self.public_repos = 0

    def get_followers(self):
        return FakePage()

    def get_following(self):
        return FakePage()

    def get_repos(self, type=None):
        return FakePage([FakeRepo("repo", self.login)])

    def get_starred(self):
        return FakePage()

    def get_events(self):
        return FakePage()


# Stands in for the GitHub client, answering the primary loop's lookups from a scripted list of outcomes
class FakeGithub:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.lookups = count(1)

    def get_user(self, login=None):
        if login is None:
            return FakeUser("viewer")
        # The snapshot's own lookup always succeeds, so the scripted outcomes describe the loop's checks only
        if next(self.lookups) == 1:
            return FakeUser(login)
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return FakeUser(login)


# Records every alert the loop hands to the delivery helper and answers with the outcome each call is given
def recording_channels(gm_module, monkeypatch, outcomes):
    calls = []

    def record(notification_type, subject, body, body_html="", email_enabled=False, webhook_enabled=None, **kwargs):
        calls.append({"type": notification_type, "subject": subject, "body": body, "body_html": body_html, "email": bool(email_enabled), "webhook": bool(webhook_enabled)})
        return outcomes[min(len(calls), len(outcomes)) - 1]

    monkeypatch.setattr(gm_module, "ERROR_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_ERROR_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "send_notification_channels", record)
    return calls


# Runs the real loop against the fake client until the given number of sleeps and returns the error alerts it handed out
def error_alerts_for(gm_module, monkeypatch, tmp_path, lookups, delivery_outcomes, stop_after):
    calls = recording_channels(gm_module, monkeypatch, delivery_outcomes)
    sleeps = []
    now = [1_800_000_000.0]

    def stopping_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds
        if len(sleeps) >= stop_after:
            raise LoopStopped

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(gm_module.time, "sleep", stopping_sleep)
    monkeypatch.setattr(gm_module.time, "time", lambda: now[0])
    monkeypatch.setattr(gm_module, "GITHUB_CHECK_INTERVAL", 300)
    monkeypatch.setattr(gm_module, "LIVENESS_REMINDER_SECONDS", 100 * 300)
    monkeypatch.setattr(gm_module, "TRACK_CONTRIB_CHANGES", False)
    monkeypatch.setattr(gm_module, "GET_ALL_REPOS", False)
    monkeypatch.setattr(gm_module, "DEBUG_MODE", False)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", False)
    # The visibility probe reaches the real site, and it is not the check under test
    monkeypatch.setattr(gm_module, "is_profile_public", lambda *arguments, **keywords: True)
    monkeypatch.setattr(gm_module, "create_github_client", lambda *arguments, **keywords: FakeGithub(lookups))
    with pytest.raises(LoopStopped):
        gm_module.github_monitor_user("watched", "")
    return [call for call in calls if call["type"] == "error"]


OUTAGE = RuntimeError("503 Server Error: Service Unavailable")


# An outage used to be printed and never delivered, since only a rejected token or a refused request earned an alert
def test_any_failure_alerts_both_channels_once(gm_module, monkeypatch, tmp_path):
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, [OUTAGE], [(True, True)], 6)

    assert [(call["email"], call["webhook"]) for call in errors] == [(True, True)]
    assert errors[0]["subject"].startswith("github_monitor: ") and errors[0]["subject"].endswith(" (user: watched)")
    assert "To fix:" in errors[0]["body"]
    assert f"retry in {gm_module.display_time(300)}" in errors[0]["body"]


# The guide link sits under the fix in the HTML body too, since HTML renders the newline the fix carries as a space
def test_the_guide_link_keeps_its_own_line_in_the_html_body(gm_module, monkeypatch, tmp_path):
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, [OUTAGE], [(True, True)], 6)

    parts = errors[0]["body_html"].split("<br>")
    fix_index = next(index for index, part in enumerate(parts) if part.startswith("To fix: "))
    assert parts[fix_index + 1].startswith("Guide: https://")
    assert "\n" not in parts[fix_index]


# A failure that changes category is a different failure, so it earns each channel a new alert
def test_a_changed_failure_category_earns_a_new_alert(gm_module, monkeypatch, tmp_path):
    rejected = gm_module.GithubException(401, {"message": "Bad credentials"}, None)
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, [OUTAGE, OUTAGE, OUTAGE, rejected], [(True, True)], 6)

    assert len(errors) == 2
    assert errors[0]["subject"] != errors[1]["subject"]


# Each channel is tracked on its own, so the one that failed is retried while the one that landed is left alone
def test_a_failed_channel_is_retried_and_a_delivered_one_is_not(gm_module, monkeypatch, tmp_path):
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, [OUTAGE], [(True, False), (False, True)], 6)

    assert [(call["email"], call["webhook"]) for call in errors] == [(True, True), (False, True)]


# A run that recovered and fails again is in a new outage, which deserves its own alert
def test_a_new_outage_after_a_recovery_alerts_again(gm_module, monkeypatch, tmp_path):
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, [OUTAGE, OUTAGE, None, OUTAGE], [(True, True)], 6)

    assert [(call["email"], call["webhook"]) for call in errors] == [(True, True), (True, True)]


# A failure the loop can retry away is alerted only once the outage has lasted the alert delay, which the second
# failing check of a poller this slow already is, while the first failing check reaches nobody
@pytest.mark.parametrize("stop_after,expected", [(2, []), (3, [(True, True)])])
def test_a_retryable_failure_is_alerted_once_the_outage_has_lasted(gm_module, monkeypatch, tmp_path, stop_after, expected):
    service_outage = gm_module.GithubException(503, {"message": "Service Unavailable"}, None)
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, [service_outage], [(True, True)], stop_after)

    assert [(call["email"], call["webhook"]) for call in errors] == expected


# A failure nothing here can retry away is alerted on the first check, since waiting would change nothing
def test_a_failure_that_cannot_clear_itself_is_alerted_at_once(gm_module, monkeypatch, tmp_path):
    rejected = gm_module.GithubException(401, {"message": "Bad credentials"}, None)
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, [rejected], [(True, True)], 2)

    assert len(errors) == 1


# Verifies an internet outage that classifies as a timeout on one check and as unreachable on the next is one
# outage, so it is reported once on screen and alerted once
def test_an_internet_outage_that_flaps_is_one_outage(gm_module, monkeypatch, tmp_path, capsys):
    flapping = [gm_module.req.Timeout("timed out"), gm_module.req.ConnectionError("refused")] * 6
    errors = error_alerts_for(gm_module, monkeypatch, tmp_path, flapping, [(True, True)], 12)

    output = capsys.readouterr().out
    assert output.count("* Error:") == 1
    assert output.count("To fix: ") == 1
    assert "Monitoring failure changed" not in output
    assert len(errors) == 1


# Verifies a reported outage that starts failing differently is still one outage, so the change is one line
# rather than a second report
def test_a_second_failure_category_is_noted_in_one_line(gm_module, monkeypatch, tmp_path, capsys):
    error_alerts_for(gm_module, monkeypatch, tmp_path, [OUTAGE, OUTAGE, OUTAGE, gm_module.req.Timeout("timed out")], [(True, True)], 8)

    lines = capsys.readouterr().out.splitlines()
    reports = [line for line in lines if line.startswith("* Error:")]
    changes = [number for number, line in enumerate(lines) if line.startswith("* Monitoring failure changed for watched. ")]
    assert len(reports) == 1
    assert len(changes) == 1 and lines[changes[0]].endswith("The network request timed out")
    assert lines[changes[0] + 1].startswith("Timestamp:")
    assert "\n".join(lines).count("To fix: ") == 1


# Verifies a lasting outage is reported once and then carried by the hourly reminder with a count of its checks
def test_a_lasting_outage_is_carried_by_the_hourly_reminder(gm_module, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gm_module, "OUTAGE_REMINDER_SECONDS", 900)
    error_alerts_for(gm_module, monkeypatch, tmp_path, [OUTAGE], [(True, True)], 10)

    output = capsys.readouterr().out
    assert output.count("* Error:") == 1
    assert output.count("To fix: ") == 1
    # One sleep precedes the loop, so nine five-minute checks follow and every third one is at the reminder interval
    assert output.count("* Monitoring degraded for watched. ") == 2
    assert ", 4 failed checks\n" in output and ", 7 failed checks\n" in output
    assert output.count("Liveness check, timestamp:") == 2
