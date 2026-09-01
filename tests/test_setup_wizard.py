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
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        run_doctor,
    ]
    if run_doctor == "y":
        answers.append(start_monitoring)
    return answers


# Verifies human durations and profile URLs normalize at the input boundary
@pytest.mark.parametrize(("value", "seconds"), (("30s", 30), ("2m", 120), ("1.5h", 5400), ("1h 30m", 5400), ("1d", 86400)))
def test_wizard_accepts_human_duration_formats(gm_module, value, seconds):
    assert gm_module.wizard_parse_duration(value) == seconds


# Verifies invalid durations and targets fail instead of being guessed
def test_wizard_rejects_invalid_human_input(gm_module):
    with pytest.raises(ValueError):
        gm_module.wizard_parse_duration("half an hour")
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
    assert transcript.startswith(f"GitHub Monitoring Tool\n                     v{gm_module.VERSION}\n\nSetup Wizard\n\n")
    assert transcript.index("Target\n") < transcript.index("Polling\n") < transcript.index("Authentication\n")
    assert transcript.index("Setup summary\n") < transcript.index("Saved files\n") < transcript.index("Next steps\n")
    assert "Detected install method: manual" in transcript
    assert transcript.count("Install method:") == 1
    assert transcript.count("manual") >= 2
    assert "Recommended setup monitors" not in transcript
    assert "Using normalized GitHub username: octocat" in transcript
    assert "<redacted>" in transcript
    assert token not in transcript
    config_content = config_path.read_text(encoding="utf-8")
    dotenv_content = dotenv_path.read_text(encoding="utf-8")
    assert gm_module.parse_config_content(config_content, str(config_path))["GITHUB_CHECK_INTERVAL"] == 1800
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
    assert "Setup cancelled. No files were written." in output.getvalue()
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
    assert doctor_calls[0].username == "octocat"
    assert monitor_calls == [["octocat", "--config-file", str(config_path), "--env-file", str(dotenv_path)]]
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
    assert transcript.startswith(f"GitHub Monitoring Tool\n                     v{gm_module.VERSION}\n\nFor <github_target>, use a GitHub username or complete profile URL.\n\n")
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
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "--setup", "--config-file", str(config_path), "--env-file", str(dotenv_path)])

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 1
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
    )
    os.close(slave)
    os.write(master, b"octocat\n\n\n\n\n\n\n\nn\n\n\n\n\n\n")
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
    assert transcript.index("Setup Wizard") < transcript.index("Target\n") < transcript.index("Setup summary\n") < transcript.index("Saved files\n") < transcript.index("Next steps\n")
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
