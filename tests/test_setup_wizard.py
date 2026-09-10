import shlex
"""Offline contract tests for guided setup and the zero-argument welcome."""

from command_expectations import runtime_command
import re
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
from unittest.mock import Mock

import signal
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


# Completes the mail settings a sign-in needs, so a test about the password is not stopped by the guard in front of it
def configure_mail(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(gm_module, "SMTP_USER", "monitor@example.test")
    monkeypatch.setattr(gm_module, "SENDER_EMAIL", "monitor@example.test")
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "alerts@example.test")


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


# Verifies the wait for GitHub is announced the way the sibling wizards announce theirs
def test_the_token_check_says_it_is_waiting_on_github(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    output = io.StringIO()
    token = "github_pat_private_wizard_value"

    gm_module.run_setup_wizard(
        wizard_parser(),
        Path(directory.name) / "monitor.conf",
        Path(directory.name) / ".env-monitor",
        input_func=scripted_reader(minimal_setup_answers()),
        getpass_func=scripted_secret_reader([token]),
        stream=output,
        interactive=True,
        token_validator=lambda entered, _url: "octocat" if entered == token else "",
    )

    transcript = output.getvalue()
    assert "  Checking the token with GitHub ...\n" in transcript
    # Announced before the answer arrives, which is the whole point of the line
    assert transcript.index("Checking the token with GitHub") < transcript.index("GitHub token is valid for user")


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
    assert f"DOTENV_FILE = {str(dotenv_path.resolve())!r}" in config_content
    # The written file is the shipped template with the answers filled in, so the secret keeps its placeholder line
    assert token not in config_content
    assert 'GITHUB_TOKEN = "your_github_classic_personal_access_token"' in config_content
    assert config_content.count("\nWEBHOOK_TEMPLATE = {\n") == 1
    assert "# Optional saved target used when no positional GitHub username is supplied" in config_content
    assert token in dotenv_content
    assert stat.S_IMODE(config_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(dotenv_path.stat().st_mode) == 0o600


# Verifies the configuration renderer keeps the template placeholder for every secret whatever the values hold
def test_the_configuration_renderer_never_writes_a_secret(gm_module):
    values = {name: "leaked-secret-value" for name in gm_module.SECRET_KEYS}
    rendered = gm_module.generate_config_with_current_values(values)

    assert "leaked-secret-value" not in rendered


# Verifies a setting still holding the shipped default keeps the template's own lines rather than a collapsed repr
def test_an_unchanged_setting_keeps_the_template_formatting(gm_module):
    rendered = gm_module.generate_config_with_current_values(dict(gm_module._config_template_defaults()))

    assert rendered == gm_module.CONFIG_BLOCK.strip("\n") + "\n"


# Verifies a changed setting is rewritten in place, replacing every line of the value it stood for
def test_a_changed_setting_replaces_the_whole_template_value(gm_module):
    values = dict(gm_module._config_template_defaults())
    values["WEBHOOK_TEMPLATE"] = {"content": "one line"}
    rendered = gm_module.generate_config_with_current_values(values)

    assert "WEBHOOK_TEMPLATE = {'content': 'one line'}\n" in rendered
    assert gm_module.parse_config_content(rendered)["WEBHOOK_TEMPLATE"] == {"content": "one line"}


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


# Returns a reader that answers the script and then interrupts the next prompt, as Ctrl+C does
def answers_then_interrupt(answers):
    remaining = list(answers)

    def read():
        if not remaining:
            raise KeyboardInterrupt
        return remaining.pop(0)

    return read


# Verifies an interrupt at the doctor offer reports the saved setup instead of a cancellation
def test_interrupting_the_doctor_offer_keeps_the_saved_setup(gm_module, request):
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
        input_func=answers_then_interrupt(minimal_setup_answers()[:-1]),
        getpass_func=scripted_secret_reader([token]),
        stream=output,
        interactive=True,
        token_validator=lambda entered, _url: "octocat" if entered == token else "",
    )

    transcript = output.getvalue()
    assert exit_code == 0
    assert "Setup is saved. Use the commands below when ready." in transcript
    assert "Setup cancelled" not in transcript
    assert "Next steps\n" in transcript
    assert config_path.is_file()


# Verifies an interrupt at the launch offer reports the saved setup and points at the printed command
def test_interrupting_the_launch_offer_keeps_the_saved_setup(gm_module, request):
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
        input_func=answers_then_interrupt(minimal_setup_answers(run_doctor="y")[:-1]),
        getpass_func=scripted_secret_reader([token]),
        stream=output,
        interactive=True,
        token_validator=lambda entered, _url: "octocat" if entered == token else "",
        doctor_runner=lambda *args, **kwargs: 0,
    )

    transcript = output.getvalue()
    assert exit_code == 0
    assert "Setup is saved. Start monitoring with the command above when ready." in transcript
    assert "Setup cancelled" not in transcript
    assert config_path.is_file()


# Verifies an existing configuration is backed up mode-0600, the replaced dotenv is not copied and unrelated dotenv data survives
def test_setup_save_backs_up_only_the_config_and_migrates_config_secrets(gm_module, request):
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

    config_backup = gm_module.save_wizard_files(state)

    assert Path(config_backup).read_text(encoding="utf-8") == config_original
    assert stat.S_IMODE(Path(config_backup).stat().st_mode) == 0o600
    assert [entry.name for entry in Path(directory.name).iterdir() if entry.name.endswith(".bak")] == [Path(config_backup).name]
    written_config = config_path.read_text(encoding="utf-8")
    assert "legacy-config-token" not in written_config and "new-private-token" not in written_config
    assert 'GITHUB_TOKEN = "your_github_classic_personal_access_token"' in written_config
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
    assert monitor_calls == [["--config-file", str(config_path.resolve()), "--env-file", str(dotenv_path.resolve())]]
    assert "Run doctor now? It writes no files and offers real delivery tests only with separate approval." in output.getvalue()
    assert "Start monitoring now? Monitoring will continue until Ctrl+C." in output.getvalue()
    assert output.getvalue().count("[Y/n]: ") >= 2


# Verifies setup reached from the no-argument welcome still starts monitoring, which relies on the default launcher
def test_zero_argument_welcome_setup_starts_monitoring(gm_module, request, monkeypatch):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    monkeypatch.chdir(directory.name)
    output = io.StringIO()
    launched = []

    monkeypatch.setattr(gm_module, "validate_github_token", lambda _token, _url: "octocat")
    monkeypatch.setattr(gm_module, "run_doctor", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(gm_module.getpass, "getpass", lambda _prompt="": "private-token")
    monkeypatch.setattr(gm_module, "launch_wizard_monitoring", lambda arguments: launched.append(arguments) or 0)

    exit_code = gm_module.print_welcome_screen(
        wizard_parser(),
        scripted_reader(["y", *minimal_setup_answers("y", "y")]),
        FakeTTY(),
        output,
    )

    assert exit_code == 0
    assert launched == [["--config-file", str((Path(directory.name) / gm_module.DEFAULT_CONFIG_FILENAME).resolve()), "--env-file", str((Path(directory.name) / ".env").resolve())]]


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
    exit_code = gm_module.print_welcome_screen(wizard_parser(), scripted_reader(["y"]), input_stream, output, install_context=context, setup_runner=setup_runner)

    transcript = output.getvalue()
    assert exit_code == 7
    assert transcript.startswith(gm_module.STARTUP_BANNER + f"\n                     v{gm_module.VERSION}\n\nFor <github_target>, use a GitHub username or complete profile URL.\n\n")
    assert runtime_command("Quickest start (already configured):\n    python3 github_monitor.py <github_target>\n\n", prefix=shlex.join(context.command_prefix)) in transcript
    assert runtime_command("Easiest start (guided setup wizard):\n    python3 github_monitor.py --setup   (or just answer Y below)\n\n", prefix=shlex.join(context.command_prefix)) in transcript
    assert runtime_command("Check setup before monitoring:\n    python3 github_monitor.py --doctor <github_target>\n\n", prefix=shlex.join(context.command_prefix)) in transcript
    assert runtime_command("Full options: python3 github_monitor.py --help", prefix=shlex.join(context.command_prefix)) in transcript
    assert "/private/runtime/python3 /private/install/github_monitor.py" in transcript
    assert "Run the guided setup wizard now? [Y/n]: " in transcript
    assert gm_module.QUICK_START_GUIDE_URL in transcript
    assert calls[0]["show_banner"] is False
    assert calls[0]["interactive"] is True


# Verifies a non-interactive welcome does not emit a prompt that cannot be answered
def test_zero_argument_welcome_non_interactive_has_no_prompt(gm_module):
    output = io.StringIO()

    exit_code = gm_module.print_welcome_screen(wizard_parser(), stream=output, input_stream=io.StringIO())

    assert exit_code == 1
    assert "Run the guided setup wizard now?" not in output.getvalue()
    assert runtime_command("python3 github_monitor.py") in output.getvalue()
    assert str(PROJECT_ROOT) in output.getvalue()


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
    dotenv_path.write_text("", encoding="utf-8")

    state = gm_module.build_wizard_state(config_path, dotenv_path)

    assert state.target == "saved-user"
    assert state.persist_target is True
    assert gm_module.wizard_monitor_arguments(state) == ["--config-file", str(config_path.resolve()), "--env-file", str(dotenv_path.resolve())]
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
    monkeypatch.setattr(gm_module, "run_doctor", lambda args, _parser, **_kwargs: captured.append(args.username) or 0)

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
    # A pty makes stdout a terminal, so the wizard colours its headings and the ordering checks need the plain text
    transcript = gm_module.ANSI_ESCAPE_RE.sub("", b"".join(chunks).decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", ""))

    assert process.returncode == 0, transcript
    assert transcript.index("Setup Wizard") < transcript.index("GitHub username or profile URL") < transcript.index("Setup summary\n") < transcript.index("Saved files\n") < transcript.index("Next steps\n")
    assert "\n\n\n" not in transcript
    assert config_path.exists()
    # No token was entered, so the run leaves no empty dotenv beside the config
    assert not dotenv_path.exists()


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
    state.secrets["GITHUB_TOKEN"] = "github_pat_test_value"
    real_prepare = gm_module.prepare_wizard_atomic_file
    monkeypatch.setattr(gm_module, "prepare_wizard_atomic_file", lambda path, content: (_ for _ in ()).throw(OSError(28, "No space left on device")) if path == state.dotenv_path else real_prepare(path, content))

    with pytest.raises(OSError):
        gm_module.save_wizard_files(state)

    assert [entry.name for entry in Path(directory.name).iterdir() if entry.name.endswith(".tmp")] == []


# Returns the visible answers for one complete mail server section
def email_answers():
    return ["y", "smtp.example.test", "587", "", "monitor@example.test", "monitor@example.test", "alerts@example.test"]


# Verifies a CSV answer without an extension is saved as a .csv file while an explicit extension is left alone
def test_the_csv_answer_gains_a_csv_extension_when_it_has_none(gm_module, request):
    state = fresh_wizard_state(gm_module, request)

    for typed, expected in (("activity", "activity.csv"), ("activity.csv", "activity.csv"), ("activity.txt", "activity.txt")):
        gm_module.wizard_collect_destinations(state, scripted_reader(["y", "y", typed]), io.StringIO())
        assert state.values["CSV_FILE"] == expected


# Verifies declining CSV output clears a saved path, which the path prompt alone could never do
def test_declining_csv_output_clears_a_saved_path(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    state.values["CSV_FILE"] = "saved.csv"

    gm_module.wizard_collect_destinations(state, scripted_reader(["y", "n"]), io.StringIO())

    assert state.values["CSV_FILE"] == ""


# Verifies a declined email section clears the mail server, so the written config cannot contradict the summary
def test_a_declined_email_section_clears_the_mail_server(gm_module, request):
    state = fresh_wizard_state(gm_module, request)
    state.values.update({"SMTP_HOST": "smtp.saved.test", "SMTP_USER": "saved@example.test", "SENDER_EMAIL": "saved@example.test", "RECEIVER_EMAIL": "alerts@example.test"})
    state.secrets["SMTP_PASSWORD"] = "saved-password"

    gm_module.wizard_collect_email(state, scripted_reader(["n"]), scripted_secret_reader([""]), io.StringIO())

    defaults = gm_module._config_template_defaults()
    assert all(state.values[name] == defaults[name] for name in gm_module.WIZARD_SMTP_CONFIG_KEYS)
    assert "SMTP_PASSWORD" not in state.secrets


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
    advice = gm_module.make_recovery_advice("smtp.connection", "The SMTP server could not be reached", "Check SMTP_HOST", True)
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


# Verifies the one-shot command signs in before the password reaches the dotenv file
def test_set_smtp_password_signs_in_before_saving(gm_module, request, monkeypatch, capsys):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    destination = Path(directory.name) / ".env-monitor"
    destination.write_text("UNRELATED=stay\n", encoding="utf-8")
    sign_in = Mock(return_value="monitor@example.test")
    configure_mail(gm_module, monkeypatch)

    result = gm_module.run_set_smtp_password(str(destination), interactive=True, getpass_func=lambda prompt: "app-password", sign_in=sign_in)

    assert result == str(destination.resolve())
    sign_in.assert_called_once_with("app-password", timeout=gm_module.WIZARD_SMTP_TIMEOUT)
    saved = destination.read_text(encoding="utf-8")
    assert "UNRELATED=stay" in saved
    assert 'SMTP_PASSWORD="app-password"' in saved
    output = capsys.readouterr().out
    assert "signing in to smtp.example.test as monitor@example.test" in output
    assert "The mail server accepted the password for monitor@example.test" in output
    assert "app-password" not in output


# Verifies a password the mail server refuses leaves the dotenv file untouched
def test_set_smtp_password_keeps_the_dotenv_file_on_a_refused_sign_in(gm_module, request, monkeypatch):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    destination = Path(directory.name) / ".env-monitor"
    destination.write_text("UNRELATED=stay\n", encoding="utf-8")
    configure_mail(gm_module, monkeypatch)
    refuse = Mock(side_effect=gm_module.smtplib.SMTPAuthenticationError(535, b"authentication failed"))

    with pytest.raises(gm_module.RecoveryError):
        gm_module.run_set_smtp_password(str(destination), interactive=True, getpass_func=lambda prompt: "wrong", sign_in=refuse)

    assert destination.read_text(encoding="utf-8") == "UNRELATED=stay\n"
    assert gm_module.classify_recovery_error(refuse.side_effect, "email").code == "smtp.authentication"


# Several providers quote the credentials back in the rejection reply. The sign-in has already restored the
# previous password by then, so the value that was tried has to reach the redaction from the caller
def test_a_reply_quoting_the_password_is_redacted(gm_module, request, monkeypatch, capsys):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    destination = Path(directory.name) / ".env-monitor"
    configure_mail(gm_module, monkeypatch)
    echo = Mock(side_effect=gm_module.smtplib.SMTPAuthenticationError(535, b"5.7.8 Not accepted. Sent: pass=app-password-value"))

    with pytest.raises(gm_module.RecoveryError) as error:
        gm_module.run_set_smtp_password(str(destination), interactive=True, getpass_func=lambda prompt: "app-password-value", sign_in=echo)

    advice = error.value.advice
    rendered = " ".join((advice.summary, advice.fix, advice.detail))
    assert "app-password-value" not in rendered
    assert "<redacted>" in advice.detail
    assert advice.code == "smtp.authentication"
    assert "app-password-value" not in capsys.readouterr().out
    assert not destination.exists()


# Verifies the command refuses to prompt without an interactive terminal
def test_set_smtp_password_requires_a_terminal(gm_module):
    with pytest.raises(ValueError, match="interactive terminal"):
        gm_module.run_set_smtp_password(interactive=False, getpass_func=Mock(side_effect=AssertionError("prompted")))


# Verifies the sign-in uses the configured mail server and restores the password it borrowed
def test_smtp_sign_in_uses_the_configured_mail_server(gm_module, monkeypatch):
    session = Mock()
    connect = Mock(return_value=session)
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", connect)
    monkeypatch.setattr(gm_module, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(gm_module, "SMTP_PORT", 587)
    monkeypatch.setattr(gm_module, "SMTP_USER", "monitor@example.test")
    monkeypatch.setattr(gm_module, "SENDER_EMAIL", "monitor@example.test")
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "alerts@example.test")
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "saved")
    monkeypatch.setattr(gm_module, "SMTP_SSL", True)

    assert gm_module.smtp_sign_in("entered", timeout=5) == "monitor@example.test"

    connect.assert_called_once_with(True, smtp_timeout=5)
    session.quit.assert_called_once()
    assert gm_module.SMTP_PASSWORD == "saved"


# Verifies incomplete mail settings are reported before the password is asked for, not after the sign-in fails
def test_incomplete_mail_settings_are_refused_before_the_prompt(gm_module, tmp_path, monkeypatch):
    destination = tmp_path / ".env-monitor"
    monkeypatch.setattr(gm_module, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(gm_module, "SMTP_USER", "monitor@example.test")
    monkeypatch.setattr(gm_module, "SENDER_EMAIL", "")
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "")

    with pytest.raises(gm_module.MailConfigurationError) as raised:
        gm_module.run_set_smtp_password(str(destination), interactive=True, getpass_func=Mock(side_effect=AssertionError("hidden prompt used")), sign_in=Mock(side_effect=AssertionError("signed in")))

    assert str(raised.value) == "The mail server settings are incomplete, SENDER_EMAIL and RECEIVER_EMAIL are not set"
    assert not destination.exists()


# Verifies a host still holding its shipped placeholder counts as unset, so a first run is not sent to it
def test_a_placeholder_mail_host_is_refused_before_the_prompt(gm_module, tmp_path, monkeypatch):
    destination = tmp_path / ".env-monitor"
    configure_mail(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "SMTP_HOST", "your_smtp_server_ssl")

    with pytest.raises(gm_module.MailConfigurationError) as raised:
        gm_module.run_set_smtp_password(str(destination), interactive=True, getpass_func=Mock(side_effect=AssertionError("hidden prompt used")), sign_in=Mock(side_effect=AssertionError("signed in")))

    assert str(raised.value) == "The mail server settings are incomplete, SMTP_HOST is not set"


# Verifies incomplete mail server settings are reported instead of a bare connection failure
def test_smtp_sign_in_reports_incomplete_settings(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", Mock(side_effect=AssertionError("connected")))
    monkeypatch.setattr(gm_module, "SMTP_HOST", "your_smtp_server_ssl")

    with pytest.raises(ValueError, match="settings are incomplete"):
        gm_module.smtp_sign_in("entered")


# Verifies a blank password is refused rather than saved as an empty secret
def test_smtp_sign_in_refuses_a_blank_password(gm_module):
    with pytest.raises(ValueError, match="No SMTP password"):
        gm_module.smtp_sign_in("")


# Verifies Ctrl+C at the welcome offer reports one line instead of a traceback
def test_interrupting_the_welcome_offer_reports_a_cancellation(gm_module):
    output = io.StringIO()

    def interrupt():
        raise KeyboardInterrupt

    exit_code = gm_module.print_welcome_screen(wizard_parser(), interrupt, FakeTTY(), output, setup_runner=lambda *args, **kwargs: pytest.fail("the wizard ran after being interrupted"))

    assert exit_code == 1
    assert "Setup cancelled." in output.getvalue()


# Verifies a prompt runs with Python's default Ctrl+C behavior, so the signal handler cannot pre-empt it
def test_prompts_restore_the_default_interrupt_handler(gm_module):
    observed = {}

    def answer():
        observed["during"] = signal.getsignal(signal.SIGINT)
        return "value"

    previous_handler = signal.signal(signal.SIGINT, gm_module.signal_handler)
    try:
        assert gm_module.wizard_read_answer("Prompt: ", answer, io.StringIO()) == "value"
        assert observed["during"] is signal.default_int_handler
        assert signal.getsignal(signal.SIGINT) is gm_module.signal_handler
    finally:
        signal.signal(signal.SIGINT, previous_handler)


# Verifies a destination that cannot be written is refused before the first question is asked
def test_an_unwritable_destination_is_refused_before_any_question(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    output = io.StringIO()

    def refuse_every_question():
        raise AssertionError("Setup asked a question before checking its destinations")

    exit_code = gm_module.run_setup_wizard(wizard_parser(), "/github_monitor_unwritable_root.conf", Path(directory.name) / ".env", input_func=refuse_every_question, stream=output, interactive=True)

    transcript = output.getvalue()
    assert exit_code == 1
    assert "Configuration destination is not writable" in transcript
    assert "To fix:" in transcript


# Verifies a directory given as a destination is refused rather than failing at the save step
def test_a_directory_destination_is_refused(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    output = io.StringIO()

    exit_code = gm_module.run_setup_wizard(wizard_parser(), directory.name, Path(directory.name) / ".env", stream=output, interactive=True)

    assert exit_code == 1
    assert "must be a file path, not a directory" in output.getvalue()


# Verifies an existing config is replaced only after the user agrees, and that a backup is kept
def test_an_existing_config_is_replaced_only_after_it_is_agreed_to(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    config_path.write_text("# earlier config\n", encoding="utf-8")
    dotenv_path = Path(directory.name) / ".env-monitor"
    output = io.StringIO()
    token = "github_pat_private_wizard_value"

    exit_code = gm_module.run_setup_wizard(
        wizard_parser(),
        config_path,
        dotenv_path,
        input_func=scripted_reader(["y", *minimal_setup_answers()]),
        getpass_func=scripted_secret_reader([token]),
        stream=output,
        interactive=True,
        token_validator=lambda entered, _url: "octocat" if entered == token else "",
    )

    backups = [path for path in Path(directory.name).iterdir() if path.name.startswith("monitor.conf.")]
    assert exit_code == 0
    assert "exists. A timestamped backup is kept. Rebuild it from your answers" in output.getvalue()
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "# earlier config\n"


# Verifies an existing config can be kept by sending the run to another path instead
def test_an_existing_config_can_be_redirected_to_another_path(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    config_path.write_text("# earlier config\n", encoding="utf-8")
    elsewhere = Path(directory.name) / "elsewhere.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    output = io.StringIO()
    token = "github_pat_private_wizard_value"

    exit_code = gm_module.run_setup_wizard(
        wizard_parser(),
        config_path,
        dotenv_path,
        input_func=scripted_reader(["n", str(elsewhere), *minimal_setup_answers()]),
        getpass_func=scripted_secret_reader([token]),
        stream=output,
        interactive=True,
        token_validator=lambda entered, _url: "octocat" if entered == token else "",
    )

    assert exit_code == 0
    assert config_path.read_text(encoding="utf-8") == "# earlier config\n"
    assert "TARGET_GITHUB_USERNAME" in elsewhere.read_text(encoding="utf-8")


# Verifies declining to replace an existing config and naming no alternative ends the run without writing
def test_declining_an_existing_config_without_an_alternative_writes_nothing(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    config_path.write_text("# earlier config\n", encoding="utf-8")
    dotenv_path = Path(directory.name) / ".env-monitor"
    output = io.StringIO()

    exit_code = gm_module.run_setup_wizard(wizard_parser(), config_path, dotenv_path, input_func=scripted_reader(["n", ""]), stream=output, interactive=True)

    assert exit_code == 1
    assert config_path.read_text(encoding="utf-8") == "# earlier config\n"
    assert not dotenv_path.exists()
    assert "Setup cancelled. Destination files were not changed." in output.getvalue()


# Verifies an interrupted entry reports the cancel itself instead of a mail server that was never contacted
def test_an_interrupted_secret_entry_is_not_reported_as_an_unreachable_server(gm_module, tmp_path, monkeypatch):
    destination = tmp_path / ".env"
    configure_mail(gm_module, monkeypatch)

    def interrupt(prompt=""):
        raise KeyboardInterrupt

    with pytest.raises(gm_module.RecoveryError) as raised:
        gm_module.run_set_smtp_password(str(destination), interactive=True, getpass_func=interrupt, sign_in=Mock(side_effect=AssertionError("signed in")))

    advice = gm_module.classify_recovery_error(raised.value, "email")
    assert advice.summary == "SMTP password setup was cancelled and the dotenv file was not changed"
    assert advice.code == "secret.entry"
    assert advice.fix == gm_module.recovery_fix_with_guide("Run --set-smtp-password again when you have the value ready", gm_module.SMTP_GUIDE_URL)
    assert not destination.exists()


# Verifies a declined replacement reports the kept value rather than a cancelled entry
def test_a_declined_secret_replacement_reports_the_kept_value(gm_module, tmp_path, monkeypatch):
    destination = tmp_path / ".env"
    destination.write_text('SMTP_PASSWORD="original"\n', encoding="utf-8")
    configure_mail(gm_module, monkeypatch)

    with pytest.raises(gm_module.RecoveryError) as raised:
        gm_module.run_set_smtp_password(str(destination), interactive=True, input_func=lambda prompt: "n", getpass_func=Mock(side_effect=AssertionError("hidden prompt used")))

    assert raised.value.advice.summary == "The saved SMTP password was left as it is and the dotenv file was not changed"
    assert "answer y to replace the saved value" in raised.value.advice.fix
    assert destination.read_text(encoding="utf-8") == 'SMTP_PASSWORD="original"\n'


# Verifies a run that stores no secret writes no dotenv, names none in its commands and still offers the doctor
def test_a_run_without_a_token_writes_no_dotenv_and_still_offers_doctor(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config_path = Path(directory.name) / "monitor.conf"
    dotenv_path = Path(directory.name) / ".env-monitor"
    output = io.StringIO()
    answers = ["https://github.com/octocat/", "", "", "", "", "", "", "", "y", "", "", "", "", "", "n"]

    exit_code = gm_module.run_setup_wizard(wizard_parser(), config_path, dotenv_path, input_func=scripted_reader(answers), getpass_func=scripted_secret_reader([""]), stream=output, interactive=True)

    transcript = output.getvalue()
    assert exit_code == 0
    assert config_path.exists()
    assert not dotenv_path.exists()
    assert "Dotenv:" not in transcript.split("Saved files")[1]
    assert "--env-file" not in transcript
    assert "Run doctor now? It writes no files and offers real delivery tests only with separate approval." in transcript


# Verifies every setup block heading is followed by one blank line, the way the sibling wizards print them
def test_every_setup_block_heading_is_followed_by_one_blank_line(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    output = io.StringIO()

    gm_module.run_setup_wizard(wizard_parser(), Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor", input_func=scripted_reader(minimal_setup_answers()), getpass_func=scripted_secret_reader(["private-token"]), stream=output, interactive=True, token_validator=lambda _token, _url: "octocat")

    transcript = output.getvalue()
    for heading in ("Setup summary", "Saved files", "Next steps"):
        assert f"\n{heading}\n\n" in transcript
    assert "\n\n\n" not in transcript


# Verifies the screen closes with the same blank line with or without a terminal to answer the offer
def test_zero_argument_welcome_closes_with_a_blank_line(gm_module):
    output = io.StringIO()

    exit_code = gm_module.print_welcome_screen(wizard_parser(), stream=output, input_stream=io.StringIO())

    assert exit_code == 1
    assert output.getvalue().endswith(f"{gm_module.QUICK_START_GUIDE_URL}\n\n")

# Verifies the guide link opens the setup page the sibling monitors link, with no section fragment
def test_the_welcome_guide_link_opens_the_shared_setup_page(gm_module):
    assert gm_module.QUICK_START_GUIDE_URL.endswith("/setup-and-first-run/")


# Verifies a config destination switched off is refused, rather than writing settings to a file named 'none'
def test_setup_refuses_a_config_destination_switched_off(tmp_path):
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "github_monitor.py"), "--setup", "--config-file", "none"], cwd=tmp_path, capture_output=True, text=True, check=False)

    assert result.returncode == 1
    assert "* Error: --setup has nowhere to write the configuration" in result.stdout
    assert "To fix: Replace '--config-file none' with a writable path, or drop the flag to write github_monitor.conf in the current directory" in result.stdout
    assert "Guide: https://misiektoja.github.io/github_monitor/configuration/#configuration-file" in result.stdout
    assert "usage:" not in result.stderr
    assert not (tmp_path / "none").exists()


# Verifies a dotenv destination switched off is refused with the flag to replace and the secrets guide
def test_setup_refuses_a_dotenv_destination_switched_off(tmp_path):
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "github_monitor.py"), "--setup", "--env-file", "none"], cwd=tmp_path, capture_output=True, text=True, check=False)

    assert result.returncode == 1
    assert "* Error: --setup has nowhere to write the private settings" in result.stdout
    assert "To fix: Replace '--env-file none' with a writable path, or drop the flag to write .env in the current directory" in result.stdout
    assert "Guide: https://misiektoja.github.io/github_monitor/configuration/#storing-secrets" in result.stdout
    assert "usage:" not in result.stderr


# Verifies the token outcome lines carry the same two-space indent the sibling monitors give them
def test_setup_token_outcome_lines_are_indented_under_the_notice(gm_module, request):
    token = "github_pat_private_wizard_value"

    # The hidden prompt shares this stream and ends without a newline, so only the outcome lines are compared
    def outcome_line(secrets, validator, fragment):
        state = fresh_wizard_state(gm_module, request)
        stream = io.StringIO()
        gm_module.wizard_collect_authentication(state, scripted_reader(["", "", "n"]), scripted_secret_reader(secrets), stream, validator)
        plain = gm_module.ANSI_ESCAPE_RE.sub("", stream.getvalue())
        return next(line for line in plain.splitlines() if fragment in line)

    def reject(_entered, _url):
        raise gm_module.GitHubTokenConfigurationError("GitHub rejected the configured token")

    accepted = outcome_line([token], lambda _entered, _url: "octocat", "valid for user")
    refused = outcome_line(["truncated"], reject, "validation failed")

    assert accepted == "  GitHub token is valid for user: octocat"
    assert refused.startswith("  Token validation failed: "), refused


# Verifies the review can move the configuration file, since the summary shows a destination it could not change
def test_the_destination_section_moves_the_configuration_file(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    moved = Path(directory.name) / "elsewhere"
    moved.mkdir()
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")

    gm_module.wizard_collect_file_destinations(state, scripted_reader([str(moved / "monitor.conf"), ""]), stream=io.StringIO())

    assert state.config_path == (moved / "monitor.conf").resolve()
    assert state.dotenv_path == (Path(directory.name) / ".env-monitor").resolve()


# Verifies moving the dotenv re-asks every section holding a secret, since a kept secret was never queued
def test_moving_the_dotenv_destination_re_asks_the_secret_sections(gm_module, monkeypatch, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    asked = []
    for name in ("wizard_collect_authentication", "wizard_collect_email", "wizard_collect_webhook"):
        monkeypatch.setattr(gm_module, name, lambda *args, section=name, **kwargs: asked.append(section))
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")
    moved = Path(directory.name) / ".env-moved"
    transcript = io.StringIO()

    gm_module.wizard_collect_file_destinations(state, scripted_reader(["", str(moved)]), stream=transcript)

    assert state.dotenv_path == moved.resolve()
    assert state.values["DOTENV_FILE"] == str(moved.resolve())
    assert asked == ["wizard_collect_authentication", "wizard_collect_email", "wizard_collect_webhook"]
    assert "The dotenv destination changed" in transcript.getvalue()


# Verifies one file cannot hold both, since saving the configuration would overwrite the secrets beside it
def test_the_dotenv_destination_cannot_be_the_configuration_file(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")
    transcript = io.StringIO()

    gm_module.wizard_collect_file_destinations(state, scripted_reader(["", str(Path(directory.name) / "monitor.conf"), ""]), stream=transcript)

    assert state.dotenv_path == (Path(directory.name) / ".env-monitor").resolve()
    assert "has to be a different file" in transcript.getvalue()


# Verifies an unusable target can be abandoned, so the question is not a loop the user can only leave with Ctrl+C
def test_an_unusable_target_can_be_abandoned(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")
    stream = io.StringIO()

    # A rejected target, then continue without one, which ends the section before the persist question
    gm_module.wizard_collect_target(state, scripted_reader(["https://github.com/one/two", "y"]), stream)

    written = stream.getvalue()
    assert "That target is not valid" in written
    assert "Continue without the GitHub username?" in written
    assert "No target selected. Nothing can be monitored until one is set." in written
    assert "Persist this target" not in written
    assert state.values["TARGET_GITHUB_USERNAME"] == ""


# Verifies asking for the target again after a rejected answer keeps the question open
def test_a_rejected_target_can_be_entered_again(gm_module, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    state = gm_module.build_wizard_state(Path(directory.name) / "monitor.conf", Path(directory.name) / ".env-monitor")
    stream = io.StringIO()

    gm_module.wizard_collect_target(state, scripted_reader(["https://github.com/one/two", "n", "misiektoja", "y", "n", "n", "n"]), stream)

    assert state.target == "misiektoja"
    assert state.values["TARGET_GITHUB_USERNAME"] == "misiektoja"


# Verifies the port question rejects a number no TCP port can be, instead of saving it for the doctor to reject
def test_the_smtp_port_question_rejects_a_number_above_the_port_range(gm_module):
    answers = iter(["70000", "y", "2525"])
    destination = io.StringIO()

    chosen = gm_module.wizard_ask_positive_int("SMTP port", 587, maximum=65535, input_func=lambda: next(answers), stream=destination)

    assert chosen == 2525
    assert "  Enter a whole number from 1 through 65535." in destination.getvalue()


# Verifies declining the retry offer keeps the saved value rather than asking the same question forever
def test_declining_the_retry_offer_keeps_the_saved_number(gm_module):
    answers = iter(["70000", "n"])
    destination = io.StringIO()

    assert gm_module.wizard_ask_positive_int("SMTP port", 587, maximum=65535, input_func=lambda: next(answers), stream=destination) == 587


# Verifies a required question says so and asks again, which is the contract the other six already had
def test_a_required_question_says_the_value_is_required(gm_module):
    answers = iter(["", "y", "smtp.example.com"])
    destination = io.StringIO()

    answer = gm_module.wizard_ask_text("SMTP host", "", input_func=lambda: next(answers), stream=destination, required=True)

    assert answer == "smtp.example.com"
    assert "  This value is required." in destination.getvalue()


# Verifies an operator who declines the retry offer leaves a required question empty rather than looping
def test_a_declined_required_question_returns_empty(gm_module):
    answers = iter(["", "n"])
    destination = io.StringIO()

    assert gm_module.wizard_ask_text("SMTP host", "", input_func=lambda: next(answers), stream=destination, required=True) == ""


# Verifies declining the retry offer after a value the wizard cannot use keeps the default rather than asking again
def test_a_rejected_duration_keeps_the_default(gm_module):
    answers = iter(["later", "n"])
    destination = io.StringIO()

    assert gm_module.wizard_ask_duration("GitHub polling interval (seconds or use s/m/h/d)", 60, input_func=lambda: next(answers), stream=destination) == 60
    written = destination.getvalue()
    assert "  Keeping 60s - 1m." in written
    # The hint the question carries belongs in the prompt, not in the offer that repeats it
    assert "Try entering the GitHub polling interval again? [Y/n]: " in written


# Verifies the backup name every tool in this family writes, so one documented shape covers them all
def test_the_backup_carries_the_family_name_and_mode(tmp_path, gm_module):
    destination = tmp_path / "monitor.conf"
    destination.write_text("SETTING = 1\n", encoding="utf-8")

    backup_path = gm_module.create_timestamped_backup(destination)

    assert re.fullmatch(r"monitor\.conf\.\d{14}\.bak", Path(backup_path).name)
    assert Path(backup_path).read_text(encoding="utf-8") == "SETTING = 1\n"
    assert stat.S_IMODE(Path(backup_path).stat().st_mode) == 0o600


# Verifies a second backup in the same second takes its own name rather than overwriting the first
def test_a_second_backup_in_the_same_second_keeps_the_first(tmp_path, gm_module):
    destination = tmp_path / "monitor.conf"
    destination.write_text("first\n", encoding="utf-8")
    first = gm_module.create_timestamped_backup(destination)
    destination.write_text("second\n", encoding="utf-8")

    second = gm_module.create_timestamped_backup(destination)

    assert first != second
    assert Path(first).read_text(encoding="utf-8") == "first\n"
    assert Path(second).read_text(encoding="utf-8") == "second\n"


# Verifies a destination that is not there yet earns no backup, since there is nothing to copy
def test_a_missing_destination_earns_no_backup(tmp_path, gm_module):
    assert gm_module.create_timestamped_backup(tmp_path / "absent.conf") is None


# Verifies an explicit colour theme survives a config rebuild, since the template ships the setting commented out
def test_a_rebuilt_config_keeps_an_explicit_color_theme(gm_module):
    values = dict(gm_module._config_template_defaults())
    values["COLOR_THEME"] = {"header": "bright_red"}

    rendered = gm_module.generate_config_with_current_values(values)

    assert gm_module.parse_config_content(rendered, "<generated>")["COLOR_THEME"] == {"header": "bright_red"}


# Verifies the shipped default stays commented out, so a rebuild does not pin a theme the user never chose
def test_a_rebuilt_config_leaves_the_default_theme_commented(gm_module):
    rendered = gm_module.generate_config_with_current_values(dict(gm_module._config_template_defaults()))

    assert "\nCOLOR_THEME = {" not in rendered
