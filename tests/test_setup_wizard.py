"""Offline contract tests for guided setup and the zero-argument welcome."""

import argparse
import io
import os
import select
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "local" / "setup_wizard_test_artifacts"


# Removes ambient GitHub credentials so each wizard test controls authentication explicitly
@pytest.fixture(autouse=True)
def clear_ambient_github_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


# Creates one disposable setup directory under the project local directory
def make_test_directory():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT)


# Reports an interactive in-memory terminal for prompt gating
class FakeTTY(io.StringIO):
    # Reports TTY support without requiring a real terminal
    def isatty(self):
        return True


# Builds the argument surface needed by wizard doctor handoffs
def wizard_parser():
    parser = argparse.ArgumentParser(prog="github_monitor")
    parser.add_argument("username", nargs="?")
    parser.add_argument("--config-file")
    parser.add_argument("--env-file")
    parser.add_argument("--doctor", action="store_true")
    return parser


# Returns a deterministic no-argument prompt reader
def scripted_reader(answers):
    iterator = iter(answers)

    # Returns the next scripted visible answer
    def read():
        return next(iterator)

    return read


# Returns a deterministic hidden prompt reader
def scripted_secret_reader(answers):
    iterator = iter(answers)

    # Returns the next scripted secret without echoing it
    def read(_prompt):
        return next(iterator)

    return read


# Supplies the shortest complete setup path with a validated token
def minimal_setup_answers(run_doctor="n", start_monitoring="n"):
    answers = [
        "https://github.com/octocat/",
        "",  # Persist target
        "",  # Public events
        "",  # Repository changes
        "",  # Contribution changes
        "",  # Polling interval
        "",  # GitHub API URL
        "",  # GitHub web URL
        "",  # Email alerts
        "",  # Webhook alerts
        "",  # Per-target log
        "",  # CSV output
        "",  # Save settings
        run_doctor,
    ]
    if run_doctor == "y":
        answers.append(start_monitoring)
    return answers


# Verifies human durations and profile URLs normalize at the input boundary
@pytest.mark.parametrize(("value", "seconds"), (("120", 120), ("30s", 30), ("2m", 120), ("1.5h", 5400), ("1h 30m", 5400), ("1d", 86400)))
def test_wizard_accepts_human_duration_formats(gm_module, value, seconds):
    assert gm_module.wizard_parse_duration(value) == seconds


# Verifies invalid durations and targets fail instead of being guessed
def test_wizard_rejects_invalid_human_input(gm_module):
    with pytest.raises(ValueError):
        gm_module.wizard_parse_duration("half an hour")
    with pytest.raises(ValueError):
        gm_module.wizard_parse_duration("31536001")
    assert gm_module.wizard_normalize_target("https://github.com/octocat/repos") == ""
    assert gm_module.wizard_normalize_target("bad--") == ""


# Drives the real wizard path and verifies reviewed values are split across safe files
def test_setup_wizard_writes_reviewed_config_and_secrets(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    output = io.StringIO()
    token = "github_pat_private_wizard_value"

    exit_code = gm_module.run_setup_wizard(
        wizard_parser(),
        config_path,
        dotenv_path,
        input_func=scripted_reader(minimal_setup_answers()),
        getpass_func=scripted_secret_reader([token]),
        stream=output,
        interactive=True,
        token_validator=lambda entered, _url: "octocat" if entered == token else "",
    )

    assert exit_code == 0
    transcript = output.getvalue()
    assert transcript.startswith(gm_module.STARTUP_BANNER + f"\n                     v{gm_module.VERSION}\n\nSetup Wizard\n\n")
    assert transcript.index("GitHub username or profile URL") < transcript.index("GitHub polling interval (seconds or use s/m/h/d)") < transcript.index("Create or view your GitHub personal access token:")
    assert transcript.index("Setup summary\n") < transcript.index("Saved files\n") < transcript.index("Next steps\n")
    assert "\nTarget\n" not in transcript
    assert "\nPolling\n" not in transcript
    assert "\nAuthentication\n" not in transcript
    assert "Detected install method: manual" in transcript
    assert transcript.count("Install method:") == 1
    assert "downloaded script" in transcript.split("Setup summary")[1]
    assert "Recommended setup monitors" not in transcript
    assert "Using normalized GitHub username: octocat" in transcript
    assert "Persist target:" in transcript
    assert "Authentication status:" in transcript
    assert "GitHub polling interval (seconds or use s/m/h/d) [1800s - 30m]: " in transcript
    assert "Local timezone" not in transcript
    assert "Configure email notifications? [y/N]: " in transcript
    assert "Set up webhook alerts (Discord, ntfy etc.)? [y/N]: " in transcript
    assert token not in transcript
    config_content = config_path.read_text(encoding="utf-8")
    dotenv_content = dotenv_path.read_text(encoding="utf-8")
    assert gm_module.parse_config_content(config_content, str(config_path))["GITHUB_CHECK_INTERVAL"] == 1800
    assert gm_module.parse_config_content(config_content, str(config_path))["TARGET_GITHUB_USERNAME"] == "octocat"
    assert f"DOTENV_FILE = {str(dotenv_path)!r}" in config_content
    assert "GITHUB_TOKEN" not in config_content
    assert token in dotenv_content
    assert stat.S_IMODE(config_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(dotenv_path.stat().st_mode) == 0o600


# Verifies cancellation cannot leave a partial config or dotenv file
def test_setup_wizard_cancellation_writes_nothing(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    answers = iter(["octocat", "", ""])

    # Interrupts after several collected answers
    def cancel_reader():
        try:
            return next(answers)
        except StopIteration:
            raise KeyboardInterrupt

    output = io.StringIO()
    exit_code = gm_module.run_setup_wizard(wizard_parser(), config_path, dotenv_path, input_func=cancel_reader, stream=output, interactive=True)

    assert exit_code == 1
    assert "Setup cancelled. Destination files were not changed." in output.getvalue()
    assert not config_path.exists()
    assert not dotenv_path.exists()


# Verifies existing files receive unique mode-0600 backups and unrelated dotenv data survives
def test_setup_save_backs_up_both_files_and_migrates_config_secrets(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    config_original = "GITHUB_CHECK_INTERVAL = 60\nGITHUB_TOKEN = 'legacy-config-token'\n"
    dotenv_original = 'UNRELATED="keep"\nGITHUB_TOKEN="old-dotenv-token"\n'
    config_path.write_text(config_original, encoding="utf-8")
    dotenv_path.write_text(dotenv_original, encoding="utf-8")
    state = gm_module.build_wizard_state(config_path, dotenv_path)
    state.target = "octocat"
    state.values["GITHUB_CHECK_INTERVAL"] = 300
    state.secrets["GITHUB_TOKEN"] = "new-private-token"

    backups = gm_module.save_wizard_files(state)

    assert len(backups) == 2
    assert backups[0].read_text(encoding="utf-8") == config_original
    assert backups[1].read_text(encoding="utf-8") == dotenv_original
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in backups)
    assert "GITHUB_TOKEN" not in config_path.read_text(encoding="utf-8")
    dotenv_content = dotenv_path.read_text(encoding="utf-8")
    assert 'UNRELATED="keep"' in dotenv_content
    assert 'GITHUB_TOKEN="new-private-token"' in dotenv_content


# Verifies section editing changes only the selected section before save
def test_setup_review_can_edit_one_section_without_losing_other_answers(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")
    state.target = "octocat"
    state.values["TRACK_REPOS_CHANGES"] = True
    answers = scripted_reader(["2", "2", "5m", "", ""])

    save = gm_module.wizard_review_setup(state, answers, stream=io.StringIO())

    assert save is True
    assert state.target == "octocat"
    assert state.values["TRACK_REPOS_CHANGES"] is True
    assert state.values["GITHUB_CHECK_INTERVAL"] == 300


# Verifies a blank required token retries unless the user explicitly accepts an unusable setup
def test_setup_token_prompt_explains_source_and_gates_empty_input(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")
    output = io.StringIO()
    token = "github_pat_private_wizard_value"

    gm_module.wizard_collect_authentication(state, scripted_reader(["", "", "n"]), scripted_secret_reader(["", token]), output, lambda entered, _url: "octocat" if entered == token else "")

    transcript = output.getvalue()
    assert f"Create or view your GitHub personal access token: {gm_module.GITHUB_TOKEN_SETTINGS_URL}" in transcript
    assert "Continue without the GitHub token? Nothing can be monitored until one is set [y/N]: " in transcript
    assert state.secrets["GITHUB_TOKEN"] == token
    assert state.authenticated_login == "octocat"


# Builds one wizard state in a disposable directory
def fresh_wizard_state(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    return gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")


# Verifies a value the validator refuses can be given up on, keeping the setting that was already there
def test_setup_rejected_value_can_be_abandoned(gm_module):
    output = io.StringIO()

    answer = gm_module.wizard_ask_text("GitHub API URL", "https://api.github.com", lambda value: "" if value == "https://api.github.com" else "enter a complete HTTPS GitHub API URL", scripted_reader(["not-a-url", "n"]), output)

    assert answer == "https://api.github.com"
    assert "Try entering the GitHub API URL again? [Y/n]: " in output.getvalue()


# Verifies accepting the blank token offer leaves setup usable to finish rather than asking forever
def test_setup_token_prompt_can_be_left_unset(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    output = io.StringIO()

    gm_module.wizard_collect_authentication(state, scripted_reader(["", "", "y"]), scripted_secret_reader([""]), output, lambda entered, _url: "octocat")

    assert "GITHUB_TOKEN" not in state.secrets
    assert "Continue without the GitHub token? Nothing can be monitored until one is set [y/N]: " in output.getvalue()


# Verifies a token GitHub refuses is offered again, since a truncated paste is the common case
def test_setup_rejected_token_is_asked_again(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    output = io.StringIO()
    token = "github_pat_private_wizard_value"

    def validator(entered, _url):
        if entered != token:
            raise gm_module.GitHubTokenConfigurationError("GitHub rejected the configured token")
        return "octocat"

    gm_module.wizard_collect_authentication(state, scripted_reader(["", "", "y"]), scripted_secret_reader(["truncated", token]), output, validator)

    assert state.secrets["GITHUB_TOKEN"] == token
    assert "Try entering the GitHub token again? [Y/n]: " in output.getvalue()


# Verifies a token GitHub keeps refusing can be given up on, since it cannot be corrected from inside the loop
def test_setup_rejected_token_can_be_abandoned(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    output = io.StringIO()

    def validator(_entered, _url):
        raise gm_module.GitHubTokenConfigurationError("GitHub rejected the configured token")

    gm_module.wizard_collect_authentication(state, scripted_reader(["", "", "n"]), scripted_secret_reader(["truncated"]), output, validator)

    assert "GITHUB_TOKEN" not in state.secrets


# Verifies a blank destination is told apart from a malformed one and that skipping it leaves the channel off
def test_setup_blank_webhook_url_is_worded_as_a_blank_one(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    state.values["WEBHOOK_ERROR_NOTIFICATION"] = True
    output = io.StringIO()

    gm_module.wizard_collect_webhook(state, scripted_reader(["y", "", "y"]), scripted_secret_reader([""]), output)

    transcript = output.getvalue()
    assert "Continue without the webhook URL? Webhook alerts stay off until one is set [y/N]: " in transcript
    assert "does not look like" not in transcript
    assert state.values["WEBHOOK_ENABLED"] is False
    assert state.values["WEBHOOK_ERROR_NOTIFICATION"] is False
    assert "WEBHOOK_URL" not in state.secrets


# Verifies a destination the wizard cannot use can be given up on, which leaves the channel and its alerts off
def test_setup_malformed_webhook_url_can_be_abandoned(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    state.values["WEBHOOK_ERROR_NOTIFICATION"] = True
    output = io.StringIO()

    gm_module.wizard_collect_webhook(state, scripted_reader(["y", "", "n"]), scripted_secret_reader(["not-a-url"]), output)

    transcript = output.getvalue()
    assert "That does not look like a complete HTTPS webhook URL. Copy it from the webhook service and try again." in transcript
    assert "Try entering the webhook URL again? [Y/n]: " in transcript
    assert state.values["WEBHOOK_ENABLED"] is False
    assert state.values["WEBHOOK_ERROR_NOTIFICATION"] is False
    assert "WEBHOOK_URL" not in state.secrets


# Verifies declining the whole webhook section switches its alerts off with it, not only the master switch
def test_setup_declining_webhooks_turns_every_webhook_alert_off(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    state.values["WEBHOOK_ERROR_NOTIFICATION"] = True
    state.values["WEBHOOK_PROFILE_NOTIFICATION"] = True
    output = io.StringIO()

    gm_module.wizard_collect_webhook(state, scripted_reader(["n"]), scripted_secret_reader([]), output)

    assert state.values["WEBHOOK_ENABLED"] is False
    assert state.values["WEBHOOK_ERROR_NOTIFICATION"] is False
    assert state.values["WEBHOOK_PROFILE_NOTIFICATION"] is False


# Verifies review menus use the shared labels, descriptions and validation messages
def test_setup_review_menu_matches_the_shared_monitor_wording(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")
    state.target = "octocat"
    output = io.StringIO()
    answers = scripted_reader(["wrong", "2", "7", "1", "", "", "", ""])

    assert gm_module.wizard_review_setup(state, answers, stream=output) is True

    transcript = output.getvalue()
    assert "Save settings (default)" in transcript
    assert "Write the displayed settings to the selected files." in transcript
    assert "Review or change settings" in transcript
    assert "Discard answers and exit" in transcript
    assert "Which setup section should be changed?" in transcript
    assert "Return to summary" in transcript
    assert "  Enter a number between 1 and 3." in transcript


# Verifies yes or no retries use the same short guidance as sibling monitors
def test_setup_yes_no_retry_matches_the_shared_wording(gm_module):
    output = io.StringIO()

    assert gm_module.wizard_ask_yes_no("Continue?", input_func=scripted_reader(["maybe", "y"]), stream=output) is True
    assert "  Please answer 'y' or 'n'." in output.getvalue()


# Verifies successful doctor can hand the exact saved command to monitoring
def test_setup_wizard_hands_off_to_doctor_then_monitoring(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    output = io.StringIO()
    doctor_calls = []
    monitor_calls = []

    # Records the doctor namespace and reports a healthy setup
    def doctor_runner(args, _parser, **_kwargs):
        doctor_calls.append(args)
        return 0

    # Records the monitoring arguments without starting an infinite loop
    def monitor_launcher(arguments):
        monitor_calls.append(arguments)
        return 0

    exit_code = gm_module.run_setup_wizard(
        wizard_parser(),
        config_path,
        dotenv_path,
        input_func=scripted_reader(minimal_setup_answers("y", "y")),
        getpass_func=scripted_secret_reader(["private-token"]),
        stream=output,
        interactive=True,
        token_validator=lambda _token, _url: "octocat",
        doctor_runner=doctor_runner,
        monitor_launcher=monitor_launcher,
    )

    assert exit_code == 0
    assert doctor_calls[0].doctor is True
    assert doctor_calls[0].username is None
    assert monitor_calls == [["--config-file", str(config_path), "--env-file", str(dotenv_path)]]
    assert "Run doctor now? It writes no files and offers real delivery tests only with separate approval." in output.getvalue()
    assert "Start monitoring now? Monitoring will continue until Ctrl+C." in output.getvalue()
    assert output.getvalue().count("[Y/n]: ") >= 2


# Verifies non-interactive setup explains the safe manual alternative and writes nothing
def test_setup_wizard_non_interactive_fallback_is_explicit(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    output = io.StringIO()

    exit_code = gm_module.run_setup_wizard(wizard_parser(), config_path, dotenv_path, stream=output, interactive=False)

    assert exit_code == 1
    assert "The setup wizard needs an interactive terminal (TTY)." in output.getvalue()
    assert "Run --setup from an interactive shell or use --generate-config and edit the files manually." in output.getvalue()
    assert "--generate-config" in output.getvalue()
    assert gm_module.QUICK_START_GUIDE_URL in output.getvalue()
    assert not config_path.exists()
    assert not dotenv_path.exists()


# Verifies the welcome matches the sibling-style transcript and launches setup after approval
def test_zero_argument_welcome_offers_guided_setup_on_a_tty(gm_module):
    output = io.StringIO()
    input_stream = FakeTTY()
    calls = []

    # Records the setup handoff without running its question sequence
    def setup_runner(_parser, **kwargs):
        calls.append(kwargs)
        return 7

    context = gm_module.InstallContext("manual", "Linux", ("/private/runtime/python3", "/private/install/github_monitor.py"))
    exit_code = gm_module.run_zero_argument_welcome(wizard_parser(), scripted_reader(["y"]), input_stream, output, install_context=context, setup_runner=setup_runner)

    transcript = output.getvalue()
    assert exit_code == 7
    assert transcript.startswith(gm_module.STARTUP_BANNER + f"\n                     v{gm_module.VERSION}\n\nFor <github_target>, use a GitHub username or complete profile URL.\n\n")
    assert "Quickest start (already configured):\n    python3 github_monitor.py <github_target>\n\n" in transcript
    assert "Easiest start (guided setup wizard):\n    python3 github_monitor.py --setup   (or just answer Y below)\n\n" in transcript
    assert "Check setup before monitoring:\n    python3 github_monitor.py --doctor <github_target>\n\n" in transcript
    assert "Full options: python3 github_monitor.py --help" in transcript
    assert "/private/" not in transcript
    assert "Run the guided setup wizard now? [Y/n]: " in transcript
    assert gm_module.QUICK_START_GUIDE_URL in transcript
    assert calls[0]["show_banner"] is False
    assert calls[0]["interactive"] is True


# Verifies a non-interactive welcome does not emit a prompt that cannot be answered
def test_zero_argument_welcome_non_interactive_has_no_prompt(gm_module):
    output = io.StringIO()

    exit_code = gm_module.run_zero_argument_welcome(wizard_parser(), stream=output, input_stream=io.StringIO())

    assert exit_code == 1
    assert "Run the guided setup wizard now?" not in output.getvalue()
    assert "python3 github_monitor.py" in output.getvalue()
    assert str(PROJECT_ROOT) not in output.getvalue()


# Verifies the empty CLI path reaches the welcome instead of argparse help
def test_zero_argument_cli_prints_welcome(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    monkeypatch.chdir(directory.name)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor"])
    monkeypatch.setattr(gm_module.sys, "stdin", io.StringIO())

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    transcript = capsys.readouterr().out
    assert exit_error.value.code == 1
    assert "For <github_target>, use a GitHub username or complete profile URL." in transcript
    assert "Easiest start (guided setup wizard):" in transcript
    assert "usage:" not in transcript


# Verifies saved targets shorten generated commands while positional targets remain available
def test_saved_target_shortens_commands_without_removing_positional_override(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    config_path.write_text("TARGET_GITHUB_USERNAME = 'saved-user'\n", encoding="utf-8")

    state = gm_module.build_wizard_state(config_path, dotenv_path)

    assert state.target == "saved-user"
    assert state.persist_target is True
    assert gm_module.wizard_monitor_arguments(state) == ["--config-file", str(config_path), "--env-file", str(dotenv_path)]
    state.target = "positional-user"
    state.persist_target = False
    assert gm_module.wizard_monitor_arguments(state)[0] == "positional-user"


# Drives the bare CLI path and verifies a saved target starts monitoring instead of reopening welcome
def test_zero_argument_cli_uses_saved_target(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / gm_module.DEFAULT_CONFIG_FILENAME
    config_path.write_text("TARGET_GITHUB_USERNAME = 'saved-user'\nGITHUB_TOKEN = 'private-test-token'\nLOCAL_TIMEZONE = 'Europe/Warsaw'\nDISABLE_LOGGING = True\n", encoding="utf-8")
    monitored = []
    monkeypatch.chdir(directory.name)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor"])
    monkeypatch.setattr(gm_module.sys, "stdin", io.StringIO())
    monkeypatch.setattr(gm_module, "check_internet", lambda: True)
    monkeypatch.setattr(gm_module, "github_monitor_user", lambda username, _csv: monitored.append(username))
    monkeypatch.setattr(gm_module.signal, "signal", lambda *_args: None)

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 0
    assert monitored == ["saved-user"]
    assert "For <github_target>" not in capsys.readouterr().out


# Verifies regular CLI actions accept the same complete profile URL advertised by setup
def test_doctor_cli_normalizes_complete_profile_url(gm_module, monkeypatch):
    captured = []
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "--doctor", "https://github.com/octocat/"])
    monkeypatch.setattr(gm_module, "run_doctor_preflight", lambda args, _parser, **_kwargs: captured.append(args.username) or 0)

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 0
    assert captured == ["octocat"]


# Verifies an invalid discovered config remains visible before the welcome can replace it
def test_zero_argument_cli_reports_invalid_discovered_config_first(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    Path(directory.name, gm_module.DEFAULT_CONFIG_FILENAME).write_text("UNKNOWN_SETTING = True\n", encoding="utf-8")
    monkeypatch.chdir(directory.name)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor"])
    monkeypatch.setattr(gm_module.sys, "stdin", io.StringIO())

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    transcript = capsys.readouterr().out
    assert exit_error.value.code == 1
    assert "unsupported configuration setting 'UNKNOWN_SETTING'" in transcript
    assert "For <github_target>" not in transcript


# Verifies help exposes setup and main uses the non-interactive fallback before monitoring
def test_setup_cli_path_is_exposed_and_does_not_start_monitoring(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    clear_calls = []
    monkeypatch.setattr(gm_module, "CLEAR_SCREEN", True)
    monkeypatch.setattr(gm_module, "clear_screen", lambda enabled: clear_calls.append(enabled))
    monkeypatch.setattr(gm_module.TerminalStream, "isatty", lambda self: True, raising=False)
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "--setup", "--config-file", str(config_path), "--env-file", str(dotenv_path)])

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 1
    assert clear_calls == [True]
    assert "The setup wizard needs an interactive terminal (TTY)." in capsys.readouterr().out
    assert not config_path.exists()
    assert not dotenv_path.exists()


# Drives the real CLI through a pseudo-terminal and checks the rendered block contract
@pytest.mark.skipif(sys.platform == "win32", reason="The standard library pty module is POSIX-only")
def test_setup_cli_pseudo_terminal_transcript_has_stable_order_and_spacing(gm_module, request):
    import pty
    import termios

    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    master, slave = pty.openpty()
    attributes = termios.tcgetattr(slave)
    attributes[3] &= ~termios.ECHO
    termios.tcsetattr(slave, termios.TCSANOW, attributes)
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "github_monitor.py"), "--setup", "--config-file", str(config_path), "--env-file", str(dotenv_path)],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        cwd=PROJECT_ROOT,
        close_fds=True,
        env={**os.environ, "GITHUB_TOKEN": "github_pat_existing_test_value"},
    )
    os.close(slave)
    os.write(master, b"octocat\n" + b"\n" * 7 + b"n\n" + b"\n" * 5 + b"n\n")
    chunks = []
    deadline = time.monotonic() + 10
    while process.poll() is None and time.monotonic() < deadline:
        readable, _, _ = select.select([master], [], [], 0.1)
        if readable:
            try:
                chunks.append(os.read(master, 65536))
            except OSError:
                break
    if process.poll() is None:
        process.kill()
        process.wait(timeout=2)
    while True:
        try:
            chunk = os.read(master, 65536)
        except OSError:
            break
        if not chunk:
            break
        chunks.append(chunk)
    os.close(master)
    transcript = b"".join(chunks).decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "")

    assert process.returncode == 0, transcript
    assert transcript.index("Setup Wizard") < transcript.index("GitHub username or profile URL") < transcript.index("Setup summary\n") < transcript.index("Saved files\n") < transcript.index("Next steps\n")
    assert "\n\n\n" not in transcript
    assert config_path.exists()
    assert dotenv_path.exists()


# A dotenv sourced by a shell uses export, and appending beside that line would leave the old secret on disk
def test_wizard_replaces_an_exported_secret_in_place(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    dotenv = Path(directory.name) / ".env"
    dotenv.write_text('export GITHUB_TOKEN="github_pat_old_stale_value"\nUNRELATED="keep"\n#GITHUB_TOKEN="commented"\n', encoding="utf-8")
    state = gm_module.build_wizard_state(Path(directory.name) / "w.conf", dotenv)
    state.secrets["GITHUB_TOKEN"] = "github_pat_new_rotated_value"

    rendered = gm_module.render_wizard_dotenv(state)

    assert "github_pat_old_stale_value" not in rendered
    assert 'export GITHUB_TOKEN="github_pat_new_rotated_value"' in rendered
    assert 'UNRELATED="keep"' in rendered
    assert '#GITHUB_TOKEN="commented"' in rendered


# Verifies a failure writing the second file leaves no temporary file beside the destinations
def test_setup_save_failure_leaves_no_temporary_files(gm_module, monkeypatch, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    state = gm_module.build_wizard_state(Path(directory.name) / "w.conf", Path(directory.name) / "w.env")
    state.target = "octocat"
    real_prepare = gm_module.prepare_wizard_atomic_file
    monkeypatch.setattr(gm_module, "prepare_wizard_atomic_file", lambda path, content: (_ for _ in ()).throw(OSError(28, "No space left on device")) if path == state.dotenv_path else real_prepare(path, content))

    with pytest.raises(OSError):
        gm_module.save_wizard_files(state)

    assert [entry.name for entry in Path(directory.name).iterdir() if entry.name.endswith(".tmp")] == []


# Returns the visible answers for one complete mail server section
def email_answers():
    return ["y", "smtp.example.test", "587", "", "monitor@example.test", "monitor@example.test", "alerts@example.test"]


# Verifies the mail server questions are asked in the shared order with the saved values offered back
def test_setup_email_prefills_saved_answers_in_the_shared_order(gm_module, request, monkeypatch):
    state = fresh_wizard_state(gm_module, request)
    state.values.update({"SMTP_HOST": "smtp.saved.test", "SMTP_USER": "saved@example.test", "SENDER_EMAIL": "saved@example.test", "RECEIVER_EMAIL": "alerts@example.test"})
    state.secrets["SMTP_PASSWORD"] = "saved-password"
    monkeypatch.setattr(gm_module, "wizard_verify_smtp", lambda values, secrets: None)
    output = io.StringIO()

    gm_module.wizard_collect_email(state, scripted_reader(["y", "", "", "", "", "", "", ""]), scripted_secret_reader([""]), output)

    transcript = output.getvalue()
    assert transcript.index("SMTP host [smtp.saved.test]: ") < transcript.index("SMTP port [587]: ") < transcript.index("Enable TLS/SSL for SMTP?")
    assert transcript.index("Enable TLS/SSL for SMTP?") < transcript.index("SMTP username [saved@example.test]: ") < transcript.index("Sender email [saved@example.test]: ")
    assert transcript.index("Sender email [saved@example.test]: ") < transcript.index("Receiver email [alerts@example.test]: ") < transcript.index("SMTP password: ")
    assert "Set or replace the SMTP password now?" not in transcript
    assert state.secrets["SMTP_PASSWORD"] == "saved-password"


# Verifies the wizard signs in with exactly the answers just given, so a wrong password is caught during setup
def test_setup_email_signs_in_with_the_collected_mail_server(gm_module, request, monkeypatch):
    state = fresh_wizard_state(gm_module, request)
    attempts = []
    monkeypatch.setattr(gm_module, "wizard_verify_smtp", lambda values, secrets: attempts.append((dict(values), dict(secrets))) or None)
    output = io.StringIO()

    gm_module.wizard_collect_email(state, scripted_reader(email_answers() + [""]), scripted_secret_reader(["private-password"]), output)

    assert len(attempts) == 1
    values, secrets = attempts[0]
    assert [values[name] for name in gm_module.WIZARD_SMTP_CONFIG_KEYS] == ["smtp.example.test", 587, True, "monitor@example.test", "monitor@example.test", "alerts@example.test"]
    assert secrets["SMTP_PASSWORD"] == "private-password"
    assert "The mail server accepted the sign-in. No email was sent." in output.getvalue()
    assert state.values["PROFILE_NOTIFICATION"] is True
    assert state.values["ERROR_NOTIFICATION"] is True
    assert state.values["CONTRIB_NOTIFICATION"] is False


# Verifies a refused sign-in offers the mail server questions again rather than saving settings that cannot work
def test_setup_refused_mail_server_sign_in_offers_another_attempt(gm_module, request, monkeypatch):
    state = fresh_wizard_state(gm_module, request)
    advice = gm_module.make_recovery_advice("smtp.authentication", "The SMTP server rejected the configured credentials", "Use an app password", False, "535 authentication failed")
    results = [advice, None]
    monkeypatch.setattr(gm_module, "wizard_verify_smtp", lambda values, secrets: results.pop(0))
    output = io.StringIO()

    gm_module.wizard_collect_email(state, scripted_reader(email_answers() + ["y"] + email_answers()[1:] + [""]), scripted_secret_reader(["wrong-password", "right-password"]), output)

    transcript = output.getvalue()
    assert "The SMTP server rejected the configured credentials: 535 authentication failed" in transcript
    assert "To fix: Use an app password" in transcript
    assert transcript.count("SMTP host") == 2
    assert state.secrets["SMTP_PASSWORD"] == "right-password"
    assert state.values["ERROR_NOTIFICATION"] is True


# Verifies giving up on a refused sign-in switches every email alert off instead of saving settings that cannot work
def test_setup_abandoned_mail_server_sign_in_switches_email_off(gm_module, request, monkeypatch):
    state = fresh_wizard_state(gm_module, request)
    advice = gm_module.make_recovery_advice("smtp.authentication", "The SMTP server rejected the configured credentials", "Use an app password", False, "535 authentication failed")
    monkeypatch.setattr(gm_module, "wizard_verify_smtp", lambda values, secrets: advice)
    output = io.StringIO()

    gm_module.wizard_collect_email(state, scripted_reader(email_answers() + ["n"]), scripted_secret_reader(["wrong-password"]), output)

    assert "Email notifications stay off until the mail server accepts the settings." in output.getvalue()
    assert all(state.values[name] is False for name in gm_module.WIZARD_EMAIL_NOTIFICATION_KEYS)


# Verifies an unreachable mail server keeps the answers, since being offline is the usual reason a correct setup fails here
def test_setup_unreachable_mail_server_keeps_the_answers(gm_module, request, monkeypatch):
    state = fresh_wizard_state(gm_module, request)
    advice = gm_module.make_recovery_advice("smtp.configuration", "The SMTP server could not be reached", "Check SMTP_HOST", True)
    monkeypatch.setattr(gm_module, "wizard_verify_smtp", lambda values, secrets: advice)
    output = io.StringIO()

    gm_module.wizard_collect_email(state, scripted_reader(email_answers() + ["n", ""]), scripted_secret_reader(["private-password"]), output)

    assert "The settings were kept without being checked. Run --doctor to check the sign-in again." in output.getvalue()
    assert state.values["SMTP_HOST"] == "smtp.example.test"
    assert state.values["ERROR_NOTIFICATION"] is True


# Verifies the custom preset only offers alerts the current tracking settings can produce
def test_setup_custom_email_preset_skips_untracked_alerts(gm_module, request, monkeypatch):
    state = fresh_wizard_state(gm_module, request)
    state.values.update({"TRACK_REPOS_CHANGES": False, "TRACK_CONTRIB_CHANGES": False})
    monkeypatch.setattr(gm_module, "wizard_verify_smtp", lambda values, secrets: None)
    output = io.StringIO()

    gm_module.wizard_collect_email(state, scripted_reader(email_answers() + ["3", "y", "n", "y"]), scripted_secret_reader(["private-password"]), output)

    transcript = output.getvalue()
    assert "Email on detailed repository changes?" not in transcript
    assert "Email on daily contribution changes?" not in transcript
    assert state.values["PROFILE_NOTIFICATION"] is True
    assert state.values["EVENT_NOTIFICATION"] is False
    assert state.values["ERROR_NOTIFICATION"] is True
    assert state.values["REPO_NOTIFICATION"] is False


# Verifies a saved ntfy token can be disabled without being displayed and is removed from the dotenv file
def test_setup_saved_ntfy_token_can_be_disabled(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    state.secrets["NTFY_ACCESS_TOKEN"] = "tk_saved_token"
    state.dotenv_path.write_text('NTFY_ACCESS_TOKEN = "tk_saved_token"\nWEBHOOK_URL = "https://ntfy.sh/private-topic"\n', encoding="utf-8")
    output = io.StringIO()

    gm_module.wizard_collect_ntfy_access_token(state, scripted_reader(["3"]), scripted_secret_reader([]), output)

    assert state.secrets["NTFY_ACCESS_TOKEN"] == ""
    assert "tk_saved_token" not in output.getvalue()
    assert "NTFY_ACCESS_TOKEN" not in gm_module.render_wizard_dotenv(state)
