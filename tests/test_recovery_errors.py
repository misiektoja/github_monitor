"""Offline tests for structured recovery advice and secret-safe rendering."""

import ast
import inspect
import io
import re
import smtplib
import time
from types import SimpleNamespace

import pytest
import requests as req


# Verifies recovery advice accepts only the stable public code set
def test_recovery_codes_are_closed(gm_module):
    advice = gm_module.make_recovery_advice("config.invalid", "Bad config", "Fix config")
    assert advice.code == "config.invalid"
    assert isinstance(gm_module.RECOVERY_CODES, frozenset)
    with pytest.raises(ValueError, match="Unsupported recovery code"):
        gm_module.make_recovery_advice("config.typo", "Bad config", "Fix config")


# Verifies construction and rendering redact known values plus common credential shapes
def test_recovery_rendering_redacts_secrets_at_both_boundaries(gm_module, monkeypatch):
    github_token = "github_pat_private_recovery_value"
    webhook_url = "https://discord.com/api/webhooks/123/private-recovery-value"
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", github_token)
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", webhook_url)
    advice = gm_module.make_recovery_advice("network.unavailable", f"Request failed for {github_token}", gm_module.recovery_fix_with_guide("Check the connection", gm_module.DEBUG_GUIDE_URL), True, f"Authorization: Bearer {github_token} at {webhook_url}")

    normal = gm_module.render_recovery_advice(advice, debug=False)
    debug = gm_module.render_recovery_advice(advice, debug=True)

    assert github_token not in normal + debug
    assert webhook_url not in normal + debug
    assert "Technical detail:" not in normal
    assert "Technical detail:" in debug
    assert "<redacted>" in debug


# Verifies the recovery block reads the same in every mode, so a report of it does not depend on the flags used
def test_the_recovery_block_is_the_same_in_every_mode(gm_module, monkeypatch):
    advice = gm_module.make_recovery_advice("target.missing", "No target", "Add a target", False, "internal detail")
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)

    output = gm_module.render_recovery_advice(advice, debug=False)

    assert output == "* Error: No target\nTo fix: Add a target"
    assert "Technical detail:" not in output


@pytest.mark.parametrize(
    ("error", "context", "code", "retryable"),
    [
        (TimeoutError("slow"), "network", "network.timeout", True),
        (PermissionError("denied"), "file", "file.unwritable", False),
        (FileNotFoundError("missing"), "config", "config.missing", False),
        (smtplib.SMTPAuthenticationError(535, b"rejected"), "smtp", "smtp.authentication", False),
        (ValueError("bad value"), "webhook", "webhook.invalid", False),
        (RuntimeError("unexpected"), "unknown", "unknown", False),
    ],
)
# Verifies the central classifier assigns stable codes and retryability by cause plus context
def test_recovery_classifier_maps_representative_failures(gm_module, error, context, code, retryable):
    advice = gm_module.classify_recovery_error(error, context)
    assert advice.code == code
    assert advice.retryable is retryable


# Verifies a rate limited webhook is reported as itself, since waiting it out is not the fix for an unreachable host
def test_a_rate_limited_webhook_is_not_reported_as_unreachable(gm_module):
    class Throttled(Exception):
        def __init__(self):
            super().__init__("Too Many Requests")
            self.response = SimpleNamespace(status_code=429)

    throttled = Throttled()
    advice = gm_module.webhook_failure_advice(str(throttled), throttled)

    assert advice.code == "webhook.rate_limited"
    assert advice.retryable is True
    assert "rate limiting deliveries" in advice.summary


# Verifies the taxonomy uses the names the sibling monitors report the same conditions under
def test_the_taxonomy_uses_the_shared_names(gm_module):
    declared = set(gm_module.RECOVERY_CODES)

    assert {"network.unavailable", "smtp.invalid", "smtp.connection", "webhook.connection", "webhook.rate_limited"} <= declared
    assert not {"network.connection", "smtp.configuration", "webhook.unreachable"} & declared


# Verifies a local file descriptor limit is reported as itself rather than as a failure of the call that hit it
def test_a_file_descriptor_limit_is_not_reported_as_a_service_failure(gm_module):
    try:
        try:
            raise OSError(24, "Too many open files")
        except OSError as inner:
            raise RuntimeError("the GitHub request failed") from inner
    except RuntimeError as error:
        advice = gm_module.classify_recovery_error(error, "runtime")

    assert advice.code == "resource.exhausted"
    assert advice.retryable is False
    assert "not a GitHub problem" in advice.summary
    assert "ulimit -n 4096" in advice.fix


# The connectivity check has no page of its own, and its fix already names the setting to look at
def test_the_connectivity_advice_carries_no_guide_link(gm_module):
    advice = gm_module.classify_recovery_error(gm_module.req.ConnectionError("offline"), "connectivity")

    assert advice.code == "network.unavailable"
    assert advice.fix == "Check network, DNS, proxy and CHECK_INTERNET_URL settings"


# Verifies RecoveryError carries structured advice and its original cause
def test_recovery_error_preserves_advice_and_cause(gm_module):
    cause = RuntimeError("underlying")
    advice = gm_module.make_recovery_advice("unknown", "Stopped", "Retry with debug")
    error = gm_module.RecoveryError(advice, cause)
    assert error.advice is advice
    assert error.cause is cause
    assert str(error) == "Stopped"


# Verifies secret masking reveals no characters from a configured value
def test_secret_masking_never_returns_the_complete_value(gm_module):
    secret = "abcdefghijk"
    masked = gm_module.mask_secret(secret)
    assert masked == "<redacted>"
    assert masked != secret


# Verifies the monitoring stream sanitizes both terminal and log output
def test_logger_redacts_secrets_from_terminal_and_log(gm_module, monkeypatch):
    secret = "github_pat_logger_private_value"
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", secret)
    logger = object.__new__(gm_module.Logger)
    logger.terminal = io.StringIO()
    logger.logfile = io.StringIO()

    logger.write(f"request failed for {secret}\n")

    assert secret not in logger.terminal.getvalue()
    assert secret not in logger.logfile.getvalue()
    assert "<redacted>" in logger.terminal.getvalue()


# Sanitizing runs over every logged line, so a short secret must not redact ordinary words in monitoring output
def test_short_secrets_do_not_redact_ordinary_output(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "github")
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "")
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "")

    assert gm_module.sanitize_error_text("Pushed to repo github/monitor") == "Pushed to repo github/monitor"
    # The assignment shape an error can actually expose stays covered
    assert "github" not in gm_module.sanitize_error_text("SMTP_PASSWORD = github")


# Verifies a credential of realistic length is still replaced wherever it appears
def test_full_length_secrets_are_still_redacted(gm_module, monkeypatch):
    token = "ghp_" + "A" * 36
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", token)

    assert token not in gm_module.sanitize_error_text(f"Request failed for {token}")


# Verifies a config failure names the rejected setting without waiting for --debug
def test_config_advice_summary_names_the_rejected_setting(gm_module):
    error = ValueError("Line 2: GITHUB_CHECK_INTERVAL must be a plain value")

    advice = gm_module.classify_recovery_error(error, "config")

    assert advice.code == "config.invalid"
    assert "GITHUB_CHECK_INTERVAL" in advice.summary
    assert "GITHUB_CHECK_INTERVAL" in gm_module.render_recovery_advice(advice, debug=False)


# Verifies an unconfigured mail server is reported as itself, not as a host that could not be reached
def test_email_advice_reports_a_settings_problem_rather_than_a_connection_one(gm_module):
    error = gm_module.MailConfigurationError("The mail server settings are incomplete, SENDER_EMAIL is not set")

    advice = gm_module.classify_recovery_error(error, "email")

    assert advice.summary == "The mail server settings are incomplete, SENDER_EMAIL is not set"
    assert advice.retryable is False
    assert "could not be reached" not in advice.summary


# Verifies a failure that did reach the network is still reported as an unreachable server
def test_email_advice_still_reports_an_unreachable_server(gm_module):
    advice = gm_module.classify_recovery_error(OSError("connection refused"), "email")

    assert advice.summary == "The SMTP server could not be reached"
    assert advice.retryable is True


# Verifies a repeated failure category prints its fix once and keeps the retry note on the summary line
def test_repeated_advice_keeps_the_summary_and_drops_the_fix(gm_module, capsys):
    tracker = gm_module.RecoveryHintTracker()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    gm_module.print_recovery_advice(advice, debug=False, tracker=tracker, retry_note="retrying in 1 hour")
    first = capsys.readouterr().out
    gm_module.print_recovery_advice(advice, debug=False, tracker=tracker, retry_note="retrying in 1 hour")
    second = capsys.readouterr().out
    tracker.reset()
    gm_module.print_recovery_advice(advice, debug=False, tracker=tracker, retry_note="retrying in 1 hour")
    third = capsys.readouterr().out

    assert first == "* Error: GitHub returned an API error (retrying in 1 hour)\nTo fix: Try again later\n"
    assert second == "* Error: GitHub returned an API error (retrying in 1 hour)\n"
    assert third == first


# Verifies a lasting failure is reported once and then only once the liveness interval has passed
def test_the_outage_reporter_reports_once_then_on_the_cadence(gm_module, monkeypatch):
    clock = [1000000.0]
    monkeypatch.setattr(gm_module.time, "time", lambda: clock[0])
    reporter = gm_module.OutageReporter()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    assert reporter.failed(advice, 180) == "full"
    outcomes = []
    for _ in range(3):
        clock[0] += 60
        outcomes.append(reporter.failed(advice, 180))

    assert outcomes == ["", "", "degraded"]
    assert reporter.recovered() is not None
    assert reporter.recovered() is None


# Verifies the reminder follows the clock, so a run that retries faster than it polls does not remind more often
def test_the_outage_reminder_follows_the_clock_not_the_check_count(gm_module, monkeypatch):
    clock = [1000000.0]
    monkeypatch.setattr(gm_module.time, "time", lambda: clock[0])
    reporter = gm_module.OutageReporter()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    assert reporter.failed(advice, 900) == "full"
    outcomes = []
    for _ in range(60):
        clock[0] += 15
        outcomes.append(reporter.failed(advice, 900))

    assert outcomes.count("degraded") == 1


# Verifies the summary keeps its every-check cadence when the liveness banner is switched off
def test_the_outage_reporter_keeps_repeating_without_a_liveness_banner(gm_module):
    reporter = gm_module.OutageReporter()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    assert reporter.failed(advice, 0) == "full"
    assert [reporter.failed(advice, 0) for _ in range(2)] == ["repeat", "repeat"]


# Verifies a failure category that changes is reported in full again rather than hidden by the previous one
def test_a_changed_failure_category_is_reported_in_full(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "LOCAL_TIMEZONE", "UTC")
    reporter = gm_module.OutageReporter()
    api_error = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)
    forbidden = gm_module.make_recovery_advice("github.forbidden", "GitHub refused access to the requested resource", "Check token permissions", False)

    assert reporter.failed(api_error, 5) == "full"
    assert reporter.failed(api_error, 5) == ""
    assert reporter.failed(forbidden, 5) == "full"

    gm_module.print_outage_liveness("misiektoja", forbidden, int(time.time()) - 60)
    gm_module.print_outage_recovery("misiektoja", 60)

    output = capsys.readouterr().out
    assert "* Monitoring degraded for misiektoja. GitHub refused access to the requested resource since " in output
    assert "Liveness check, timestamp:" in output
    assert "* Monitoring recovered for misiektoja after 1 minute" in output


# Verifies the monitoring loop classifies its own failures instead of printing raw exception text
def test_the_monitoring_loop_classifies_its_failures(gm_module):
    source = inspect.getsource(gm_module.github_monitor_user)

    assert 'classify_recovery_error(e, "target")' in source
    assert "outage.failed(advice, LIVENESS_REMINDER_SECONDS)" in source
    assert "print_outage_liveness(user, advice, outage.since)" in source
    assert "print_outage_recovery(user, outage_lasted)" in source
    assert '"Forbidden"' not in source, "the loop must classify failures rather than match exception text"
    assert '"Bad Request"' not in source, "the loop must classify failures rather than match exception text"


# Verifies a named sub-operation keeps the shared line shape rather than inventing its own
def test_a_labelled_failure_keeps_the_shared_shape(gm_module, capsys):
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    gm_module.print_recovery_advice(advice, debug=False, retry_note="retrying in 1 hour", label="Warning")

    assert capsys.readouterr().out.splitlines()[0] == "* Warning: GitHub returned an API error (retrying in 1 hour)"


# Verifies the liveness banner explains itself without --verbose, so a plain run never prints a bare timestamp
def test_the_liveness_banner_explains_itself_without_diagnostics(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "LOCAL_TIMEZONE", "UTC")
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", False)

    gm_module.print_liveness_banner("Monitoring healthy for misiektoja. No tracked change since the last check")

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "* Monitoring healthy for misiektoja. No tracked change since the last check"
    assert lines[1].startswith("Liveness check, timestamp:")


# Verifies the monitoring loop reports its healthy banner through the shared helper
def test_the_loop_reports_its_healthy_banner_unconditionally(gm_module):
    source = inspect.getsource(gm_module.github_monitor_user)

    assert "print_liveness_banner(f\"Monitoring healthy for {user}." in source
    assert "verbose_print(f\"Monitoring healthy" not in source, "the healthy banner is no longer verbose-only"
    assert "int(time.time()) - alive_since >= LIVENESS_REMINDER_SECONDS" in source, "the healthy banner is timed rather than counted"


# Verifies a CSV row that cannot be written carries a fix and the page documenting the export
def test_an_unwritable_csv_row_is_reported_with_a_fix(gm_module, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gm_module, "github_account_exists", lambda login: None)
    unreachable = tmp_path / "missing-directory" / "changes.csv"

    gm_module.handle_profile_change("Followers", 1, 2, ["old"], [SimpleNamespace(login="new")], "owner", str(unreachable), field="login")

    printed = capsys.readouterr().out
    assert "* Error: Failed to write to CSV file" in printed
    assert "To fix: Check CSV_FILE and its parent directory permissions" in printed
    assert f"Guide: {gm_module.CSV_GUIDE_URL}" in printed


# Verifies a failed CSV write reports through the recovery block, since the monitoring loop carries on past it
def test_no_csv_write_failure_prints_its_own_line(gm_module):
    csv_writers = {"init_csv_file", "write_csv_entry"}
    offenders = []
    guarded = 0
    for node in ast.walk(ast.parse(inspect.getsource(gm_module))):
        if not isinstance(node, ast.Try) or (node.body[-1].end_lineno or node.body[0].lineno) - node.body[0].lineno > 6:
            continue
        if not any(isinstance(inner, ast.Call) and getattr(inner.func, "id", "") in csv_writers for statement in node.body for inner in ast.walk(statement)):
            continue
        guarded += 1
        offenders.extend(f"line {statement.lineno}" for handler in node.handlers for statement in handler.body if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and getattr(statement.value.func, "id", "") == "print")

    assert guarded >= 23, f"only {guarded} CSV writes are guarded, so this no longer covers them"
    assert not offenders, "CSV write failures reported outside the recovery block:\n" + "\n".join(offenders)


# Verifies a list refresh that fails names the list in front of the classified failure and keeps the fix
def test_a_failed_refresh_names_the_list_and_carries_a_fix(gm_module, capsys):
    gm_module.print_degraded_error("Followers could not be refreshed", req.ConnectionError("no route to host"))

    printed = capsys.readouterr().out
    assert "* Error: Followers could not be refreshed: The configured service could not be reached" in printed
    assert "To fix: Check the network and configured service URL then try again" in printed
    assert "Guide: " in printed


# Verifies an unreadable membership list reports through the block and leaves the previous snapshot in place
def test_an_unreadable_membership_list_is_reported_with_a_fix(gm_module, capsys):
    unreadable = [SimpleNamespace()]

    result = gm_module.handle_profile_change("Followers", 1, 1, ["old"], unreadable, "owner", "", field="login")

    printed = capsys.readouterr().out
    assert result == (["old"], 1)
    assert "* Error: The list of followers could not be refreshed: " in printed
    assert "To fix: " in printed


# Returns every literal string one argument can evaluate to, following a conditional or a code held in a local name
def literal_values(node, assignments):
    if isinstance(node, ast.Constant):
        return {node.value} if isinstance(node.value, str) else set()
    if isinstance(node, ast.IfExp):
        return literal_values(node.body, assignments) | literal_values(node.orelse, assignments)
    if isinstance(node, ast.Name) and assignments.get(node.id):
        return set().union(*(literal_values(value, assignments) for value in assignments[node.id]))
    return set()


# Returns every code an advice builder can pass, which is what makes a declared code with no producer visible
def builder_codes(source):
    tree = ast.parse(source)
    assignments = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(node.value)
    codes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("advice", "make_recovery_advice") and node.args:
            codes |= literal_values(node.args[0], assignments)
    return codes


# Verifies every declared code has a producer, so the set records what the tool reports rather than what it might
def test_every_declared_code_is_reachable(gm_module):
    unreachable = set(gm_module.RECOVERY_CODES) - builder_codes(inspect.getsource(gm_module))

    assert unreachable == set(), f"codes with no producer: {sorted(unreachable)}"


# Verifies no advice builder names a code outside the declared set, so the set stays the whole taxonomy
def test_no_code_outside_the_declared_set_is_produced(gm_module):
    undeclared = builder_codes(inspect.getsource(gm_module)) - set(gm_module.RECOVERY_CODES)

    assert undeclared == set(), f"codes produced but not declared: {sorted(undeclared)}"


# Every place that reports a problem without the classifier and the reason it cannot use one
CLASSIFIER_EXEMPTIONS = {
    "or higher required": "runs at import on an interpreter too old to load the rest of the file",
    "Couldn't find the pytz library": "raised at import, while a dependency the classifier itself needs is missing",
    "Couldn't find the PyGitHub library": "raised at import, while a dependency the classifier itself needs is missing",
    "Cannot clear the screen contents": "a cosmetic notice with nothing for the operator to recover from",
    "(retry": "a progress line for a retry still in flight, where the final attempt reports through the block",
}

# Words that mark a printed line as a report of something going wrong
TROUBLE_WORDS = re.compile(r"error|cannot|can't|failed|failure|invalid|not valid|missing|not installed|no such|refused|unsupported|needs to be|could not|couldn't|unable to", re.IGNORECASE)


# Returns the literal text one print argument shows, leaving out the parts an f-string fills at runtime
def printed_text(node):
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else ""
    if isinstance(node, ast.JoinedStr):
        return "".join(printed_text(part) for part in node.values)
    if isinstance(node, ast.BinOp):
        return printed_text(node.left) + printed_text(node.right)
    return ""


# Returns every printed line that reads as a problem, paired with the line it sits on
def reported_problems(source):
    found = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") in {"print", "SystemExit"}):
            continue
        text = " ".join(printed_text(argument) for argument in node.args)
        if TROUBLE_WORDS.search(text):
            found.append((node.lineno, " ".join(text.split())))
    return found


# A problem reported without a category leaves the reader with a message and no next step
def test_every_reported_problem_goes_through_the_classifier(gm_module):
    unexplained = [f"line {line}: {text[:120]}" for line, text in reported_problems(inspect.getsource(gm_module)) if not any(marker in text for marker in CLASSIFIER_EXEMPTIONS)]

    assert unexplained == []


# An exemption list that stopped matching anything would quietly cover the whole file
def test_the_classifier_guard_still_inspects_the_source(gm_module):
    source = inspect.getsource(gm_module)
    inspected = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call) and getattr(node.func, "id", "") in {"print", "SystemExit"}]
    problems = reported_problems(source)

    assert len(inspected) > 150
    assert all(any(marker in text for _, text in problems) for marker in CLASSIFIER_EXEMPTIONS), "an exemption stopped matching a printed line"


# The only advice that names no page, and the reason no page covers it
GUIDELESS_ADVICE = {
    "The connectivity endpoint did not answer in time": "no page covers this check and the doctor report already ends with the troubleshooting link",
    "The connectivity endpoint could not be reached": "no page covers this check and the doctor report already ends with the troubleshooting link",
}

# The guide sits in this positional slot for each builder, or inside the fix when the signature carries no slot
GUIDE_SLOT = {"advice": 4, "make_recovery_advice": None}


# True when this builder attaches a documentation link in any of the three shapes the tool uses
def attaches_a_guide(node, source):
    slot = GUIDE_SLOT.get(getattr(node.func, "id", ""))
    if slot is not None and len(node.args) > slot:
        return True
    if any(keyword.arg in ("guide_url", "guide") for keyword in node.keywords):
        return True
    return "recovery_fix_with_guide" in (ast.get_source_segment(source, node.args[2]) or "")


# Returns every expression assigned to each plain name in the module, so a fix held in a variable can be read
def assigned_expressions(tree):
    assignments = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(node.value)
    return assignments


# Returns the text of the summary or fix, resolving one level of plain-name assignment
def resolved_text(node, source, assignments):
    if isinstance(node, ast.Name):
        return " ".join(ast.get_source_segment(source, value) or "" for value in assignments.get(node.id, []))
    return ast.get_source_segment(source, node) or ""


# Returns every advice builder that names no page, paired with the summary it reports
def guideless_advice(source):
    tree = ast.parse(source)
    assignments = assigned_expressions(tree)
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") in GUIDE_SLOT) or len(node.args) < 3:
            continue
        # A builder that re-wraps an already-classified advice carries whatever guide that advice was given
        if isinstance(node.args[2], ast.Attribute) and node.args[2].attr == "fix":
            continue
        if attaches_a_guide(node, source) or "recovery_fix_with_guide" in resolved_text(node.args[2], source, assignments):
            continue
        found.append((node.lineno, resolved_text(node.args[1], source, assignments)))
    return found


# A failure with no page to read leaves the operator with a one-line fix and nowhere to go next
def test_every_failure_names_a_page(gm_module):
    source = inspect.getsource(gm_module)
    unexplained = [f"line {line}: {summary[:100]}" for line, summary in guideless_advice(source) if not any(marker in summary for marker in GUIDELESS_ADVICE)]

    assert unexplained == []


# An allowlist that stopped matching anything would quietly cover every failure in the file
def test_the_guide_guard_still_inspects_the_source(gm_module):
    source = inspect.getsource(gm_module)
    inspected = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call) and getattr(node.func, "id", "") in GUIDE_SLOT]
    bare = guideless_advice(source)

    assert len(inspected) > 30
    assert all(any(marker in summary for _, summary in bare) for marker in GUIDELESS_ADVICE), "an allowlisted summary stopped matching a builder"


# One concept carried three names across this family: a renderer taking a built advice, a renderer taking the
# failure itself, and a third pair that classified and printed under a name of its own. Pinned here so a call
# copied from a sibling cannot quietly mean something else
def test_the_recovery_printers_share_one_contract(gm_module):
    advice_first = ("advice", "debug", "retry_note", "with_fix", "label")
    error_first = ("error", "context", "debug", "detail", "retry_note", "with_fix", "label")

    assert tuple(inspect.signature(gm_module.render_recovery_advice).parameters) == advice_first
    assert tuple(inspect.signature(gm_module.render_recovery_error).parameters) == error_first + ("install_context",)
    # This tool's own parameters follow the shared ones, so a call written for a sibling still means the same thing
    assert tuple(inspect.signature(gm_module.print_recovery_advice).parameters) == advice_first + ("tracker",)
    assert tuple(inspect.signature(gm_module.print_recovery_error).parameters) == error_first + ("tracker", "install_context")


# The advice pair prints what the caller built, so a summary the classifier would never produce survives the trip
def test_the_advice_printer_does_not_reclassify(gm_module, capsys):
    gm_module.DEBUG_MODE = False
    advice = gm_module.make_recovery_advice("network.timeout", "a summary no rule produces", "a fix of its own", True)

    returned = gm_module.print_recovery_advice(advice)

    assert capsys.readouterr().out == "* Error: a summary no rule produces\nTo fix: a fix of its own\n"
    assert returned is advice


# The error pair classifies what the caller hands it, which is the difference between the two front doors
def test_the_error_printer_classifies_what_it_was_given(gm_module, capsys):
    gm_module.DEBUG_MODE = False

    returned = gm_module.print_recovery_error(req.ConnectionError("connection refused"), context="runtime")

    assert returned.code != "unknown"
    assert capsys.readouterr().out.startswith(f"* Error: {returned.summary}\n")


# Both front doors reach the same renderer, so the retry note, the label and a suppressed fix behave the same way
def test_both_front_doors_render_the_same_line(gm_module):
    gm_module.DEBUG_MODE = False
    error = req.ConnectionError("connection refused")
    advice = gm_module.classify_recovery_error(error, "runtime")

    through_advice = gm_module.render_recovery_advice(advice, retry_note="retrying in 5 minutes", with_fix=False, label="Warning")
    through_error = gm_module.render_recovery_error(error, "runtime", retry_note="retrying in 5 minutes", with_fix=False, label="Warning")

    assert through_advice == through_error
    assert through_advice == f"* Warning: {advice.summary} (retrying in 5 minutes)"


# The caller's own detail replaces the exception repr, so a debug run names the step rather than only the type
def test_the_callers_detail_wins_over_the_exception_text(gm_module):
    advice = gm_module.classify_recovery_error(req.ConnectionError("connection refused"), "runtime", "Reading the event feed of 'octocat' failed")

    assert advice.detail == "Reading the event feed of 'octocat' failed"
    assert gm_module.classify_recovery_error(req.ConnectionError("connection refused"), "runtime").detail.startswith("ConnectionError: ")


# A detail that only repeats the summary spends a line saying nothing, so the block drops it and keeps a real one
def test_a_detail_repeating_the_summary_is_dropped(gm_module):
    repeated = gm_module.make_recovery_advice("unknown", "the same sentence twice", "a fix", False, "the same sentence twice")
    differing = gm_module.make_recovery_advice("unknown", "the summary", "a fix", False, "the raw cause")

    assert "Technical detail:" not in gm_module.render_recovery_advice(repeated, debug=True)
    assert "Technical detail: the raw cause" in gm_module.render_recovery_advice(differing, debug=True)


# A run that already prints the technical cause cannot be told to re-run for it
def test_the_unrecognized_failure_fix_follows_the_diagnostic_mode(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "DEBUG_MODE", False)
    plain = gm_module.classify_recovery_error(Exception("a wholly unfamiliar failure"), "runtime").fix
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)
    debugging = gm_module.classify_recovery_error(Exception("a wholly unfamiliar failure"), "runtime").fix

    assert "--debug" in plain
    assert "--debug" not in debugging


# The recovery code is an internal taxonomy the user never sees, so no fix may ask for one
def test_no_user_facing_line_asks_for_the_recovery_code(gm_module):
    source = inspect.getsource(gm_module)
    mentions = [line.strip() for line in source.splitlines() if "recovery code" in line.casefold()]

    assert mentions == ['raise ValueError(f"Unsupported recovery code: {code}")'], mentions
    assert "recovery code" not in gm_module.classify_recovery_error(RuntimeError("a wholly unfamiliar failure")).fix.casefold()
