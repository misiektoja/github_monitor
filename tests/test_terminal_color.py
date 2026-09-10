"""Terminal colour contract tests for the coloured output layer."""

import ast
import argparse
from io import StringIO
import io
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import github_monitor as monitor


CHANGE_REPORT_LINES = ("* Daily contributions changed for user octocat from 98 to 100 (+2)!", "* Repo 'hello world': number of stars changed from 10 to 12 (+2)", "* Repo 'emoji tools 🛠️' update date changed after 2 days")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Runs one isolated command-line action against the working-tree script
def run_cli(*arguments):
    return subprocess.run([sys.executable, str(PROJECT_ROOT / "github_monitor.py"), *arguments], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)


# Verifies the selected GitHub banner remains exact and version independent
def test_selected_banner_exact_content():
    assert monitor.STARTUP_BANNER == r"""
 .---------------.     ____ _ _   _   _       _
|     /\_/\      |    / ___(_) |_| | | |_   _| |__
|    ( o.o )     |   | |  _| | __| |_| | | | | '_ \
|     > ^ <      |   | |_| | | |_|  _  | |_| | |_) |
|    /     \     |    \____|_|\__|_| |_|\__,_|_.__/
 '---------------'
                      __  __             _ _
                     |  \/  | ___  _ __ (_) |_ ___  _ __
                     | |\/| |/ _ \| '_ \| | __/ _ \| '__|
                     | |  | | (_) | | | | | || (_) | |
                     |_|  |_|\___/|_| |_|_|\__\___/|_|"""


# Verifies the art is portable, bounded and free of trailing whitespace
def test_banner_ascii_width_and_whitespace():
    monitor.STARTUP_BANNER.encode("ascii")
    lines = monitor.STARTUP_BANNER.splitlines()
    assert max(map(len, lines)) <= 90
    assert all(line == line.rstrip() for line in lines)


# Verifies the GitHub wordmark matches the standard FIGlet rows at the shared body column
def test_banner_github_wordmark_rows():
    assert [line[21:] for line in monitor.STARTUP_BANNER.splitlines()[1:6]] == [
        "  ____ _ _   _   _       _",
        " / ___(_) |_| | | |_   _| |__",
        "| |  _| | __| |_| | | | | '_ \\",
        "| |_| | | |_|  _  | |_| | |_) |",
        " \\____|_|\\__|_| |_|\\__,_|_.__/",
    ]


# Verifies the Monitor wordmark matches the standard FIGlet rows at the shared body column
def test_banner_monitor_wordmark_rows():
    assert [line[21:] for line in monitor.STARTUP_BANNER.splitlines()[7:12]] == [
        " __  __             _ _",
        "|  \\/  | ___  _ __ (_) |_ ___  _ __",
        "| |\\/| |/ _ \\| '_ \\| | __/ _ \\| '__|",
        "| |  | | (_) | | | | | || (_) | |",
        "|_|  |_|\\___/|_| |_|_|\\__\\___/|_|",
    ]


# Verifies the printed version stays dynamic and followed by one blank line
def test_banner_dynamic_version_line(monkeypatch, capsys):
    monkeypatch.setattr(monitor, "VERSION", "9.9-test")
    monkeypatch.setattr(monitor, "COLOR_ENABLED", False)
    monitor.print_startup_banner()
    assert capsys.readouterr().out == monitor.STARTUP_BANNER + "\n" + (" " * 21) + "v9.9-test\n\n"


# Verifies GitHub, Monitor and the version share the same body column
def test_banner_version_alignment():
    banner_lines = monitor.STARTUP_BANNER.splitlines()
    github_body_column = banner_lines[3].index("| |  _")
    monitor_body_indent = len(banner_lines[8]) - len(banner_lines[8].lstrip())
    version_indent = len(" " * 21) - len((" " * 21).lstrip())
    assert github_body_column == monitor_body_indent == version_indent


# Verifies version output stays one line and excludes the startup art
def test_version_output_is_machine_friendly():
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout.splitlines() == [f"github_monitor.py v{monitor.VERSION}"]
    assert monitor.STARTUP_BANNER.splitlines()[1] not in result.stdout


# Verifies generated config output begins with content and excludes the startup art
def test_generate_config_output_is_machine_friendly():
    result = run_cli("--generate-config")
    assert result.returncode == 0
    assert result.stdout.startswith("# Optional saved target")
    assert monitor.STARTUP_BANNER.splitlines()[1] not in result.stdout


# Verifies help shows one startup banner
def test_help_shows_one_startup_banner():
    result = run_cli("--help")
    assert result.returncode == 0
    assert result.stdout.count(" .---------------.") == 1


# Enables colour with a deterministic style map
@pytest.fixture
def colored(monkeypatch):
    styles = {name: monitor._build_ansi_sequence(value) for name, value in monitor.DEFAULT_COLOR_THEME.items() if monitor._build_ansi_sequence(value)}
    monkeypatch.setattr(monitor, "COLOR_ENABLED", True)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", styles)
    return styles


# Reads a block the template ships commented out, as the parser would see it once uncommented
def uncomment_block(first_line):
    lines = monitor.CONFIG_BLOCK.split("\n")
    start = next(index for index, line in enumerate(lines) if line.startswith(first_line))
    end = next(index for index in range(start, len(lines)) if lines[index].rstrip() == "# }")
    return "\n".join(line[2:] if line.startswith("# ") else line[1:] for line in lines[start:end + 1])


# Verifies the config template matches the built-in theme
def test_config_template_theme_matches_the_built_in_theme():
    values = monitor.parse_config_content(monitor.CONFIG_BLOCK, "<built-in-config>")
    commented = monitor.parse_config_content(uncomment_block("# COLOR_THEME = {"), "<built-in-config>")
    assert values["COLORED_OUTPUT"] is True
    assert "COLOR_THEME" not in values
    assert commented["COLOR_THEME"] == monitor.DEFAULT_COLOR_THEME


# Verifies a configuration that sets the commented-out theme is still accepted, since older files all set it
def test_a_config_setting_the_theme_is_still_accepted(tmp_path):
    config = tmp_path / "monitor.conf"
    config.write_text('COLOR_THEME = { "username": "green" }\n', encoding="utf-8")
    assert monitor.parse_config_content(config.read_text(encoding="utf-8"), str(config)) == {"COLOR_THEME": {"username": "green"}}


# Verifies every shipped style resolves or is deliberately empty
def test_default_theme_styles_all_resolve():
    for name, value in monitor.DEFAULT_COLOR_THEME.items():
        assert monitor._build_ansi_sequence(value) or value == "", name


# Verifies the timestamp label stays plain while its value is cyan
def test_timestamp_label_is_uncolored(colored):
    result = monitor._colorize_line("Timestamp:\t\t\tWed 26 Aug 2026, 20:23:03")
    assert monitor.DEFAULT_COLOR_THEME["timestamp_label"] == ""
    assert "timestamp_label" not in colored
    assert result == f"Timestamp:\t\t\t{colored['timestamp_value']}Wed 26 Aug 2026, 20:23:03{monitor.ANSI_RESET}"


# Verifies startup summary labels do not trigger whole-line styles
def test_startup_summary_rows_are_not_block_colored(colored):
    for line in ("* Target:                       octocat", "* Track repository changes:     True", "* Monitor GitHub events:        True"):
        result = monitor._colorize_line(line)
        assert monitor.ANSI_ESCAPE_RE.sub("", result) == line
        assert not result.startswith(colored["info"])


# Verifies startup durations do not become problem lines
def test_startup_summary_timer_rows_are_not_error_colored(colored):
    for line in ("* Polling interval:             30 minutes", "* Liveness output:              12 hours"):
        result = monitor._colorize_line(line)
        assert colored["error"] not in result
        assert colored["duration"] in result


# Verifies debug failures and fallback notices stay outside the error block
@pytest.mark.parametrize("line", ["[DEBUG 15:57:30] GitHub request failed status=403", "* Repository details are unavailable so count-only monitoring will continue"])
def test_diagnostic_details_and_fallback_notices_are_not_error_colored(colored, line):
    assert not monitor._colorize_line(line).startswith(colored["error"])


# Verifies real problem lines keep the error block style
@pytest.mark.parametrize("line", ["* Error: request timeout after 15 seconds", "* Cannot fetch repository details"])
def test_real_problem_lines_stay_error_colored(colored, line):
    assert monitor._colorize_line(line).startswith(colored["error"])


# Verifies static counts stay plain while changes get counter colours
def test_static_counts_stay_plain_and_changes_are_colored(colored):
    for line in ("Followers:\t\t\t98", "Followings:\t\t\t302", "Repositories:\t\t\t41", "Available events:\t\t7"):
        assert monitor._colorize_line(line) == line
    changed = monitor._colorize_line("* Followers changed for user octocat from 98 to 100 (+2)")
    assert f"{colored['count_up']}98{monitor.ANSI_RESET}" in changed
    assert f"{colored['count_up']}(+2){monitor.ANSI_RESET}" in changed


# Verifies line colouring changes only ANSI spans
@pytest.mark.parametrize("line", ["Username:\t\t\tOcto Cat", "Event ID:\t\t\t12345", "Repo name:\t\t\toctocat/Hello World", "Event type:\t\t\tPushEvent", "Repo URL:\t\t\thttps://github.com/octocat/repo", "Timestamp:\t\t\tSun 21 Apr 2024, 15:08:45"])
def test_colorize_line_never_rewrites_the_text(colored, line):
    assert monitor.ANSI_ESCAPE_RE.sub("", monitor._colorize_line(line)) == line


# Verifies each banner line uses only banner colours
def test_startup_banner_uses_only_its_own_colours(colored, capsys):
    monitor.print_startup_banner()
    rendered = monitor.apply_color_to_text(capsys.readouterr().out)
    assert set(monitor.SGR_SEQUENCE_RE.findall(rendered)) <= {colored["header"], colored["info"], monitor.ANSI_RESET}
    for line in monitor.STARTUP_BANNER.splitlines():
        if line:
            assert f"{colored['header']}{line}{monitor.ANSI_RESET}" in rendered


# Verifies banner colouring preserves every character
def test_startup_banner_art_is_unchanged(colored):
    rendered = monitor.apply_color_to_text(monitor.STARTUP_BANNER)
    assert monitor.ANSI_ESCAPE_RE.sub("", rendered) == monitor.STARTUP_BANNER


# Verifies the Setup Wizard heading keeps the newline inside the sibling-style header span
def test_setup_wizard_heading_uses_header_colour(colored):
    output = io.StringIO()
    assert monitor.run_setup_wizard(None, stream=output, interactive=False, show_banner=False) == 1
    assert output.getvalue().startswith(f"{colored['header']}Setup Wizard\n{monitor.ANSI_RESET}\n")


# Verifies labelled GitHub rows use their expected theme parts
@pytest.mark.parametrize(("line", "part"), [("Username:\tOcto Cat", "username"), ("Event ID:\t12345", "id"), ("Repo name:\toctocat/Hello World", "repository"), ("Event type:\tPushEvent", "event"), ("Commit message:\t'Fix setup'", "commit"), ("Object name:\tfeature/colour", "branch"), ("Email:\talerts@example.test", "email")])
def test_labelled_rows_use_the_expected_theme_part(colored, line, part):
    assert colored[part] in monitor._colorize_line(line)


# Verifies bulleted detail rows colour their value like the unbulleted label
@pytest.mark.parametrize(("line", "value", "part"), [(" - Commit message:\t\t'fix(setup): keep the kept default'", "'fix(setup): keep the kept default'", "commit"), (" - Commit author:\tOcto Cat", "Octo Cat", "username"), (" - Commit SHA:\t8ab4f0c", "8ab4f0c", "id")])
def test_bulleted_labelled_rows_colour_their_value(colored, line, value, part):
    assert f"{colored[part]}{value}{monitor.ANSI_RESET}" in monitor._colorize_line(line)


# Verifies each real listing row colours its complete identity token
@pytest.mark.parametrize(("line", "token", "part"), (("🔸 hello-world (fork) ", "hello-world", "repository"), ("- octocat/hello-world [ https://github.com/octocat/hello-world/ ]", "octocat/hello-world", "repository"), ("- hello-world [ https://github.com/octocat/hello-world/ ]", "hello-world", "repository"), ("- octocat [ https://github.com/octocat/ ]", "octocat", "username"), ("- octocat (Octo Cat 🐙)", "octocat (Octo Cat 🐙)", "username")))
def test_listing_rows_use_their_domain_colour(colored, line, token, part):
    result = monitor._colorize_line(line)
    assert f"{colored[part]}{token}{monitor.ANSI_RESET}" in result
    if "https://" in line:
        assert colored["link"] in result


# Verifies doctor markers are coloured without colouring their details
@pytest.mark.parametrize(("marker", "part"), [("PASS", "boolean_true"), ("WARN", "warning"), ("FAIL", "error"), ("SKIP", "info")])
def test_doctor_status_markers_are_colored(colored, marker, part):
    line = f"[{marker}] GitHub token is configured"
    assert monitor._colorize_line(line) == f"{colored[part]}[{marker}]{monitor.ANSI_RESET} GitHub token is configured"


# Verifies presence values use distinct online and offline styles
def test_presence_keywords_pick_the_matching_style(colored):
    assert monitor.colorize_status("public").startswith(colored["status_online"])
    assert monitor.colorize_status("private").startswith(colored["status_offline"])
    assert monitor.colorize_status("unknown").startswith(colored["status_other"])


# Verifies visibility and block values use their actual sentence context
@pytest.mark.parametrize(("line", "token", "part"), (("Public profile:\t\t\tYes", "Yes", "status_online"), ("Public profile:\t\t\tNo", "No", "status_offline"), ("Blocked by the user:\t\tNo", "No", "status_online"), ("Blocked by the user:\t\tYes", "Yes", "status_offline"), ("Blocked by the user:\t\tUnknown", "Unknown", "status_other"), ("* User octocat has changed profile visibility to 'private' !", "private", "status_offline"), ("* User octocat has changed profile visibility to 'public' !", "public", "status_online"), ("* User octocat has blocked you!", "blocked", "status_offline"), ("* User octocat has unblocked you!", "unblocked", "status_online"), ("Repository is now public", "public", "status_online")))
def test_emitted_status_values_use_contextual_status_colours(monkeypatch, line, token, part):
    status_styles = {"status_online": "\x1b[94m", "status_offline": "\x1b[95m", "status_other": "\x1b[97m"}
    monkeypatch.setattr(monitor, "COLOR_ENABLED", True)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", {**monitor._COLOR_STYLES, **status_styles})
    result = monitor._colorize_line(line)
    assert f"{status_styles[part]}{token}{monitor.ANSI_RESET}" in result


# Verifies clock matching rejects ports and partial times
@pytest.mark.parametrize("value", ["00:00", "23:59", "21:07:39", "~21:07:39", "09:15 PM"])
def test_time_color_regex_accepts_only_complete_clock_values(value):
    assert monitor._TIME_ONLY_RE.fullmatch(value)
    for invalid in ("24:00", "12:60", "8000:8000", "abc12:30", "1:12:30"):
        assert monitor._TIME_ONLY_RE.search(invalid) is None


# Verifies hostile controls cannot drive the terminal
@pytest.mark.parametrize(("hostile", "expected"), [("repo\x1b[2Jcleared", "repo[2Jcleared"), ("repo\x1b]0;title\x07", "repo]0;title"), ("visible\rhidden", "visiblehidden"), ("bell\x07 null\x00", "bell null"), ("delete\x7f c1\x1b[3J", "delete c1[3J")])
def test_sanitize_terminal_text_removes_control_sequences(hostile, expected):
    assert monitor.sanitize_terminal_text(hostile) == expected


# Verifies SGR colours and whitespace survive sanitizing
def test_sanitize_terminal_text_keeps_colours_and_layout():
    coloured = "\033[36mInfo\033[0m\tvalue\nnext line"
    assert monitor.sanitize_terminal_text(coloured) == coloured


# Verifies controls between valid SGR spans are removed
def test_sanitize_terminal_text_cleans_between_colour_codes():
    smuggled = "\033[36mlabel\033[0m \x1b[2J\033[31mvalue\033[0m"
    assert monitor.sanitize_terminal_text(smuggled) == "\033[36mlabel\033[0m [2J\033[31mvalue\033[0m"


# Builds one in-memory logger
def make_logger():
    terminal = io.StringIO()
    logfile = io.StringIO()
    logger = monitor.Logger.__new__(monitor.Logger)
    logger.__dict__.update(terminal=terminal, logfile=logfile)
    return logger, terminal, logfile


# Verifies terminal colour and ANSI-free file output
def test_logger_colors_the_terminal_and_keeps_the_log_plain(colored, monkeypatch):
    monkeypatch.setattr(monitor, "TRUNCATE_CHARS", 0)
    logger, terminal, logfile = make_logger()
    logger.write("Username:\t\t\tOcto Cat\n")
    logger.log_only(f"{colored['error']}failure{monitor.ANSI_RESET}\n")
    assert colored["username"] in terminal.getvalue()
    assert monitor.ANSI_ESCAPE_RE.search(logfile.getvalue()) is None


# Verifies truncation measures plain text before colouring
def test_truncation_runs_before_colour_is_applied(colored, monkeypatch):
    monkeypatch.setattr(monitor, "TRUNCATE_CHARS", 20)
    logger, terminal, _ = make_logger()
    logger.write("Username:\tOcto Cat The Very Long Display Name\n")
    plain = monitor.ANSI_ESCAPE_RE.sub("", terminal.getvalue()).rstrip("\n")
    assert len(plain.expandtabs(8)) == 20
    assert colored["username"] in terminal.getvalue()


# Verifies the early stream colours after removing controls
def test_terminal_stream_colors_and_sanitizes(colored):
    terminal = io.StringIO()
    monitor.TerminalStream(terminal).write("Username:\tOcto\x1b[2J Cat\n")
    assert colored["username"] in terminal.getvalue()
    assert "\x1b[2J" not in terminal.getvalue()


# Records progress output without a live terminal
class RecordingProgressStream:
    # Starts an empty output record
    def __init__(self):
        self.values = []

    # Reports the terminal capability required by progress output
    def isatty(self):
        return True

    # Records one progress write
    def write(self, text):
        self.values.append(text)

    # Leaves recorded output immediately available
    def flush(self):
        pass


# Verifies doctor progress has no ANSI and erases visible width
def test_doctor_progress_line_is_never_colored(colored, monkeypatch):
    terminal = RecordingProgressStream()
    monkeypatch.setattr(monitor, "VERBOSE_MODE", False)
    monkeypatch.setattr(monitor, "DEBUG_MODE", False)
    progress = monitor.DoctorProgress(terminal)
    progress.show(f"{colored['error']}authentication{monitor.ANSI_RESET}")
    progress.clear()
    assert "\x1b" not in "".join(terminal.values)
    assert terminal.values[-1] == " " * len("* Checking authentication ...") + "\r"


# Verifies doctor progress unwraps all output wrappers
def test_doctor_terminal_stream_unwraps_output_wrappers():
    real_terminal = io.StringIO()
    logger, _, _ = make_logger()
    logger.__dict__["terminal"] = monitor.TerminalStream(real_terminal)
    assert monitor.DoctorProgress(logger).terminal is real_terminal


# Verifies support detection honours environment contracts
def test_stream_support_detection_honours_environment(monkeypatch):
    monkeypatch.setattr(monitor.sys, "stdin", type("Stdin", (), {"isatty": lambda self: True})())
    interactive = type("Stream", (), {"isatty": lambda self: True})()
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert monitor._stream_supports_color(interactive) is True
    assert monitor._stream_supports_color(type("Stream", (), {"isatty": lambda self: False})()) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert monitor._stream_supports_color(interactive) is False
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("TERM", "dumb")
    assert monitor._stream_supports_color(interactive) is False


# Verifies piped stdin disables colours
def test_piped_stdin_disables_color(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(monitor.sys, "stdin", type("Stdin", (), {"isatty": lambda self: False})())
    assert monitor._stream_supports_color(type("Stream", (), {"isatty": lambda self: True})()) is False


# Verifies partial themes merge over built-in values
def test_config_theme_overrides_only_named_parts(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monkeypatch.setattr(monitor, "COLOR_THEME", {"username": "red bold"})
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor._COLOR_STYLES["username"] == "\033[31;1m"
    assert monitor._COLOR_STYLES["repository"] == monitor._build_ansi_sequence(monitor.DEFAULT_COLOR_THEME["repository"])


# Verifies disabled output clears all styles
def test_disabled_color_output_clears_the_style_map(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", False)
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor.COLOR_ENABLED is False
    assert monitor._COLOR_STYLES == {}
    assert monitor.apply_color_to_text("Username:\tOcto Cat\n") == "Username:\tOcto Cat\n"


# Verifies early config applies appearance before argparse
def test_early_output_config_reads_terminal_appearance(monkeypatch, tmp_path):
    config = tmp_path / "github_monitor.conf"
    config.write_text("CLEAR_SCREEN = False\nCOLORED_OUTPUT = False\n", encoding="utf-8")
    monkeypatch.setattr(monitor.sys, "argv", ["github_monitor.py", "--config-file", str(config)])
    monkeypatch.setattr(monitor, "CLEAR_SCREEN", True)
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monitor.apply_early_output_config()
    assert monitor.CLEAR_SCREEN is False
    assert monitor.COLORED_OUTPUT is False


# Verifies broken early config leaves defaults unchanged
def test_early_output_config_ignores_a_broken_config(monkeypatch, tmp_path):
    config = tmp_path / "github_monitor.conf"
    config.write_text("import os\n", encoding="utf-8")
    monkeypatch.setattr(monitor.sys, "argv", ["github_monitor.py", "--config-file", str(config)])
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monitor.apply_early_output_config()
    assert monitor.COLORED_OUTPUT is True


# Verifies the none sentinel skips discovery
def test_early_output_config_skips_disabled_discovery(monkeypatch):
    calls = []
    monkeypatch.setattr(monitor.sys, "argv", ["github_monitor.py", "--config-file", "none"])
    monkeypatch.setattr(monitor, "find_config_file", lambda path=None: calls.append(path))
    monitor.apply_early_output_config()
    assert calls == []


# Verifies both config flag spellings are scanned
@pytest.mark.parametrize(("arguments", "expected"), [(["--config-file", "/tmp/one.conf"], "/tmp/one.conf"), (["--config-file=/tmp/two.conf"], "/tmp/two.conf"), (["--verbose"], None), (["--config-file"], None)])
def test_early_config_file_argument_scan(arguments, expected):
    assert monitor.early_config_file_argument(arguments) == expected


# Verifies the CLI disable wins over configuration
def test_no_color_flag_disables_colored_output(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", False)
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor.COLOR_ENABLED is False


# Verifies Logger bypasses the early colour stream
def test_logger_unwraps_the_early_terminal_stream(colored, monkeypatch, tmp_path):
    raw = io.StringIO()
    monkeypatch.setattr(monitor.sys, "stdout", monitor.TerminalStream(raw))
    monkeypatch.setattr(monitor, "TRUNCATE_CHARS", 0)
    logger = monitor.Logger(str(tmp_path / "monitor.log"))
    try:
        logger.write("Timestamp:\t\t\tWed 26 Aug 2026, 20:23:03\n")
    finally:
        logger.logfile.close()
    assert logger.terminal is raw
    assert raw.getvalue() == f"Timestamp:\t\t\t{colored['timestamp_value']}Wed 26 Aug 2026, 20:23:03{monitor.ANSI_RESET}\n"


# Verifies nested early streams reach the terminal
def test_unwrap_terminal_stream_reaches_the_real_terminal():
    raw = io.StringIO()
    assert monitor.unwrap_terminal_stream(raw) is raw
    assert monitor.unwrap_terminal_stream(monitor.TerminalStream(monitor.TerminalStream(raw))) is raw


# Verifies later rules cannot reclaim a coloured span
def test_inline_rules_do_not_reclaim_already_colored_text(colored):
    result = monitor._colorize_line("[ date: Sun 16 Feb 2025, 14:34:06 - 1 year ago ]")
    assert result.count(colored["date"]) == 1
    assert result == f"[ date: {colored['date']}Sun 16 Feb 2025, 14:34:06{monitor.ANSI_RESET} - {colored['duration']}1 year{monitor.ANSI_RESET} ago ]"


# Verifies repository names keep spaces and punctuation
@pytest.mark.parametrize("name", ["3 AM Sessions", "BDSM (dark tools)", "Tools / Actions / Hooks", "Tomorrowland (TML) 🛠️", "Nocturne_Rewired"])
def test_names_with_slashes_and_brackets_are_still_colored(colored, name):
    result = monitor._colorize_line(f"* Repo '{name}' changed")
    assert f"{colored['repository']}{name}{monitor.ANSI_RESET}" in result


# Verifies quoted paths stay plain
@pytest.mark.parametrize("value", ["monitor_state.json", "/data/github.log", "~/logs/output.txt", "C:\\Users\\me\\state.json"])
def test_quoted_file_and_path_values_stay_plain(colored, value):
    line = f"* Repo '{value}' loaded"
    assert monitor._colorize_line(line) == line


# Verifies downloaded-script descriptions stay plain
def test_downloaded_script_quoted_description_stays_plain(colored):
    line = "'A repository description with spaces / punctuation.'"
    assert monitor._colorize_line(line) == line


# Verifies change reports are not painted end to end
@pytest.mark.parametrize("line", CHANGE_REPORT_LINES)
def test_change_reports_are_not_painted_end_to_end(colored, line):
    result = monitor._colorize_line(line)
    assert monitor.ANSI_ESCAPE_RE.sub("", result) == line
    assert not result.startswith("\x1b")


# Verifies only problems get whole-line styles
def test_only_problem_lines_are_painted_end_to_end(colored):
    for line, part in (("* Error: could not reach GitHub", "error"), ("* Warning: something odd", "warning")):
        assert monitor._colorize_line(line).startswith(colored[part])


# Verifies every theme key has a source consumer
def test_every_theme_part_is_used():
    source = Path(monitor.__file__).read_text(encoding="utf-8")
    looked_up = set(re.findall(r"""colorize\(\s*["']([a-z_]+)["']""", source))
    looked_up |= set(re.findall(r"""_apply_style_nested\([^,]+,\s*["']([a-z_]+)["']""", source))
    looked_up |= set(re.findall(r"""(?:style_name|key) = ["']([a-z_]+)["']""", source))
    looked_up |= set(re.findall(r""",\s*["']([a-z_]+)["']\),?\s*$""", source, re.M))
    marks = re.search(r"_DOCTOR_MARK_STYLES = \{(.*?)\}", source, re.S)
    assert marks is not None
    looked_up |= set(re.findall(r""":\s*["']([a-z_]+)["']""", marks.group(1)))
    assert not set(monitor.DEFAULT_COLOR_THEME) - looked_up


# Verifies the published theme table lists every shipped key once
def test_documented_theme_keys_match_the_built_in_theme():
    usage = (Path(monitor.__file__).parent / "docs" / "usage.md").read_text(encoding="utf-8")
    section = usage.split("## Terminal Colours", 1)[1].split("## Coloring Log Output with GRC", 1)[0]
    documented = re.findall(r"^\| `([a-z_]+)` \|", section, re.M)
    assert len(documented) == len(set(documented))
    assert set(documented) == set(monitor.DEFAULT_COLOR_THEME)


# Verifies a config written against the pre-rename 'url' and 'timestamp' keys still colours links and timestamps
def test_legacy_theme_keys_still_apply(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monkeypatch.setattr(monitor, "COLOR_THEME", {"url": "red", "timestamp": "green"})
    monkeypatch.setattr(monitor, "COLOR_ENABLED", False)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", {})
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor._COLOR_STYLES["link"] == monitor._build_ansi_sequence("red")
    assert monitor._COLOR_STYLES["timestamp_value"] == monitor._build_ansi_sequence("green")


# Verifies the current key name wins when a config sets both the old and the new name
def test_current_theme_key_wins_over_the_legacy_name(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monkeypatch.setattr(monitor, "COLOR_THEME", {"url": "red", "link": "green"})
    monkeypatch.setattr(monitor, "COLOR_ENABLED", False)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", {})
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor._COLOR_STYLES["link"] == monitor._build_ansi_sequence("green")


# Verifies the target uses username colour everywhere
@pytest.mark.parametrize("line", ["Monitoring GitHub user octocat", "User 'octocat' not found", "Getting repositories for user 'octocat'", "Username:\t\t\toctocat", "* Target:                       octocat"])
def test_target_username_uses_the_username_colour_everywhere(colored, line):
    result = monitor._colorize_line(line)
    assert monitor.ANSI_ESCAPE_RE.sub("", result) == line
    assert f"{colored['username']}octocat{monitor.ANSI_RESET}" in result
    assert colored["repository"] not in result


# Verifies prose following the word "user" is not mistaken for a login
@pytest.mark.parametrize("line", ["- Stargazer/watcher user lists:\tFetched for 16/16 repositories", "* Error: The user details could not be read: boom", "Old user name:\t\t\tOcto Cat", "* Monitored user refresh failed"])
def test_prose_after_the_word_user_is_not_coloured(colored, line):
    result = monitor._colorize_line(line)
    assert monitor.ANSI_ESCAPE_RE.sub("", result) == line
    assert colored["username"] not in result


# Verifies display names with spaces are complete
def test_display_name_still_uses_the_name_colour(colored):
    result = monitor._colorize_line("Username:\t\t\tOcto Cat 🐙")
    assert f"{colored['username']}Octo Cat 🐙{monitor.ANSI_RESET}" in result


# Verifies setup destinations and commands are coloured
def test_setup_surface_is_coloured(colored):
    output = io.StringIO()
    context = SimpleNamespace(install_method="pip")
    state = SimpleNamespace(config_path=Path("monitor.conf"), dotenv_path=Path(".env"))
    monitor._wizard_print_setup_destinations(output, context, state)
    monitor._wizard_print_command(output, "Check setup again:", "github_monitor --doctor GITHUB_USERNAME")
    rendered = output.getvalue()
    assert f"Detected install method: {colored['username']}pip{monitor.ANSI_RESET}" in rendered
    assert f"{colored['section']}github_monitor --doctor GITHUB_USERNAME{monitor.ANSI_RESET}" in rendered


# Verifies wizard prompts and menus are coloured
def test_wizard_prompt_and_menu_are_coloured(colored):
    output = io.StringIO()
    monitor.wizard_ask_choice("Pick one", (("first", "First", "Use the first choice."), ("second", "Second", "Use the second choice.")), "second", lambda: "1", output)
    rendered = output.getvalue()
    assert f"{colored['info']}Pick one{monitor.ANSI_RESET}" in rendered
    assert f"{colored['username']}1{monitor.ANSI_RESET}. First" in rendered
    assert f"{colored['info']} (default){monitor.ANSI_RESET}" in rendered
    assert f"{colored['info']}Choose [1-2]: {monitor.ANSI_RESET}" in rendered


# Verifies doctor headings and verdicts are coloured
def test_doctor_report_headings_are_coloured(colored):
    report = monitor.DoctorReport()
    report.add("Environment", "PASS", "Python is supported", "Plain detail 30 seconds")
    output = io.StringIO()
    output.write(monitor.colorize("header", "Doctor") + "\n")
    monitor.render_doctor_sections(report, output)
    monitor.render_doctor_summary(report, output)
    rendered = output.getvalue()
    assert f"{colored['header']}Doctor{monitor.ANSI_RESET}" in rendered
    assert f"{colored['header']}Summary{monitor.ANSI_RESET}" in rendered
    assert f"{colored['section']}Environment{monitor.ANSI_RESET}" in rendered
    assert f"{colored['duration']}30 seconds" not in rendered


# Verifies explicit surfaces bypass the general line colouriser in the real wrapper stack
def test_explicit_surface_stream_avoids_a_second_colour_pass(colored):
    raw = io.StringIO()
    wrapped = monitor.TerminalStream(raw)
    destination = monitor.terminal_surface_stream(wrapped)
    destination.write(monitor.colorize("header", "Doctor") + "\n")
    destination.write("  Detail: 30 seconds\n")
    rendered = raw.getvalue()
    assert rendered.count(colored["header"]) == 1
    assert f"{colored['duration']}30 seconds" not in rendered


# Verifies recovery advice uses info and URL colours
def test_recovery_guidance_uses_the_info_colour(colored):
    result = monitor._colorize_line(f"To fix: Retry at {monitor.CONFIG_GUIDE_URL}")
    assert result.startswith(colored["info"])
    assert colored["link"] in result


# Verifies names remain visible inside whole-line styles
def test_name_palette_differs_from_every_whole_line_style():
    for name in ("username", "id", "repository", "event", "commit", "branch"):
        for block in ("info", "warning", "error", "signal", "email", "webhook"):
            assert monitor.DEFAULT_COLOR_THEME[name] != monitor.DEFAULT_COLOR_THEME[block], f"{name} matches {block}"


# Verifies repository progress contains no ANSI escapes
def test_repository_progress_line_has_no_ansi_escapes(colored, monkeypatch):
    terminal = RecordingProgressStream()
    monkeypatch.setattr(monitor, "stdout_bck", terminal)
    monkeypatch.setattr(monitor.shutil, "get_terminal_size", lambda fallback=(80, 20): type("Size", (), {"columns": 80})())
    monkeypatch.setattr(monitor, "_progress_line_width", 0)
    monitor._display_progress(1, 2, f"{colored['repository']}repo{monitor.ANSI_RESET}")
    assert "\x1b" not in "".join(terminal.values)
    assert terminal.values[-1].startswith("\rRepos [")


# Verifies truncation measures what is displayed, so colour codes do not eat into the visible width
def test_truncation_measures_display_width_not_escape_sequences():
    pytest.importorskip("wcwidth")

    truncated = monitor.truncate_string_per_line("\x1b[31m0123456789ABCDEF\x1b[0m", 10)

    assert re.sub(r"\x1b\[[0-9;]*m", "", truncated) == "0123456789"


# Verifies a double-width character costs two columns, so a CJK title does not wrap past the limit
def test_truncation_counts_double_width_characters():
    pytest.importorskip("wcwidth")

    assert monitor.truncate_string_per_line("原神原神原神", 4) == "原神"


# Verifies each line is measured on its own rather than the whole message being cut at one offset
def test_truncation_applies_to_every_line():
    pytest.importorskip("wcwidth")

    assert monitor.truncate_string_per_line("abcdef\nabcdef", 3) == "abc\nabc"


# Verifies truncation still applies without wcwidth, counting one column per character, skipping colour codes and closing the cut colour
def test_truncation_falls_back_to_one_column_per_character_without_wcwidth(monkeypatch):
    monkeypatch.setitem(sys.modules, "wcwidth", None)

    assert monitor.truncate_string_per_line("\x1b[31m0123456789ABCDEF\x1b[0m\n原神原神", 4) == "\x1b[31m0123\x1b[0m\n原神原神"


# Verifies indented wizard hints stay plain, matching the five tools that never coloured them
def test_indented_wizard_hints_are_not_colored():
    source = (PROJECT_ROOT / "github_monitor.py").read_text(encoding="utf-8")

    coloured = re.findall(r'colorize\("warning", f?"  [^"]*', source)

    # The doctor summary sentence is the one indented line all seven colour
    assert [line for line in coloured if "All critical checks passed" not in line] == []


# Verifies the TLS row colours its state word, the one setting whose off state weakens a security property
def test_the_tls_row_colours_its_state(colored):
    on_row = monitor._colorize_line("* TLS verification:             On")
    off_row = monitor._colorize_line("* TLS verification:             Off, server certificates are not checked")

    assert on_row == f"* TLS verification:             {colored['boolean_true']}On{monitor.ANSI_RESET}"
    assert off_row == f"* TLS verification:             {colored['boolean_false']}Off{monitor.ANSI_RESET}, server certificates are not checked"


HELP_SAMPLE = """usage: monitor [-h] [--config-file PATH] [TARGET]

positional arguments:
  TARGET                The target to monitor

Configuration & dotenv files:
  --config-file PATH    Path to a config file
  -m, --check-interval SECONDS
                        Time between checks (default: 60)

Examples:

Getting started:
  # Guided setup, see https://example.invalid/guide/
  python3 monitor.py --setup <target>

Guide: https://example.invalid/guide/
"""

HELP_SAMPLE_EPILOG = HELP_SAMPLE[HELP_SAMPLE.index("Examples:"):]


# Enables colour with the shipped theme and returns the escape sequence of every part
@pytest.fixture
def help_palette(monkeypatch):
    styles = {name: monitor._build_ansi_sequence(value) for name, value in monitor.DEFAULT_COLOR_THEME.items() if monitor._build_ansi_sequence(value)}
    monkeypatch.setattr(monitor, "COLOR_ENABLED", True)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", styles)
    return styles


# Returns the sample help screen with the help palette applied
@pytest.fixture
def colored_help(help_palette):
    return monitor.colorize_help_text(HELP_SAMPLE, HELP_SAMPLE_EPILOG)


# Verifies colouring changes no character of the screen, since argparse laid out its columns on the plain text
def test_the_coloured_help_keeps_the_plain_layout(colored_help):
    assert monitor.ANSI_ESCAPE_RE.sub("", colored_help) == HELP_SAMPLE


# Verifies the argument groups and the example tasks share one heading colour, the anchors the reader scans for
def test_the_help_headings_carry_the_heading_colour(help_palette, colored_help):
    for heading in ("positional arguments:", "Configuration & dotenv files:", "Examples:", "Getting started:"):
        assert f"{help_palette['help_heading']}{heading}{monitor.ANSI_RESET}" in colored_help


# Verifies an option name and the value it takes are coloured apart, in the usage block and in the option rows
def test_the_help_option_names_and_their_values_are_coloured_apart(help_palette, colored_help):
    option = f"{help_palette['help_option']}--config-file{monitor.ANSI_RESET}"
    metavar = f"{help_palette['help_metavar']}PATH{monitor.ANSI_RESET}"

    assert f"{option} {metavar}" in colored_help
    assert f"[{option} {metavar}]" in colored_help
    assert f"{help_palette['help_usage']}usage:{monitor.ANSI_RESET}" in colored_help
    assert f"{help_palette['help_metavar']}TARGET{monitor.ANSI_RESET}                The target to monitor" in colored_help


# Verifies the examples separate the comment from the command and mark the value the reader has to replace
def test_the_help_examples_mark_comments_commands_and_placeholders(help_palette, colored_help):
    assert f"{help_palette['help_comment']}  # Guided setup" in colored_help
    assert f"{help_palette['help_command']}  python3 monitor.py --setup" in colored_help
    assert f"{help_palette['help_placeholder']}<target>{monitor.ANSI_RESET}" in colored_help


# Verifies a default note is dimmed and a documentation link keeps the shared link colour
def test_the_help_default_notes_and_links_stay_secondary(help_palette, colored_help):
    assert f"{help_palette['help_default']}(default: 60){monitor.ANSI_RESET}" in colored_help
    assert f"{help_palette['link']}https://example.invalid/guide/{monitor.ANSI_RESET}" in colored_help


# Verifies the help screen stays plain while colour is switched off, so --no-color and NO_COLOR clear all of it
def test_the_help_palette_switches_off_with_colour():
    assert monitor.colorize_help_text(HELP_SAMPLE, HELP_SAMPLE_EPILOG) == HELP_SAMPLE


# Verifies the finished help screen reaches the terminal untouched, past the colouriser that paints monitoring output
def test_the_help_screen_is_not_repainted_by_the_monitoring_rules(help_palette):
    buffer = StringIO()
    parser = monitor.ColoredHelpParser(prog="monitor", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--config-file", metavar="PATH", help="Path to a config file")
    parser.print_help(monitor.TerminalStream(buffer))

    written = buffer.getvalue()
    assert written == parser.format_help()
    assert help_palette["help_option"] in written


# Verifies a cut line closes the colour it opened, so the truncated tail does not paint every line printed after it
def test_a_truncated_line_closes_its_open_colour():
    pytest.importorskip("wcwidth")

    assert monitor.truncate_string_per_line("\x1b[31m0123456789ABCDEF\x1b[0m", 10) == "\x1b[31m0123456789" + monitor.ANSI_RESET


# Verifies no extra reset is added when the colour closed before the cut or the line was never cut
def test_a_closed_or_uncut_colour_gains_no_extra_reset():
    pytest.importorskip("wcwidth")

    assert monitor.truncate_string_per_line("\x1b[31m0123\x1b[0m456789ABCDEF", 10) == "\x1b[31m0123\x1b[0m456789"
    assert monitor.truncate_string_per_line("\x1b[31m0123\x1b[0m", 10) == "\x1b[31m0123\x1b[0m"
    assert monitor.truncate_string_per_line("0123456789ABCDEF", 10) == "0123456789"


# Verifies the setup screens colour their links, since they print before the output stream colouriser is installed
def test_setup_screen_links_are_coloured(monkeypatch):
    link = monitor._build_ansi_sequence(monitor.DEFAULT_COLOR_THEME["link"])
    monkeypatch.setattr(monitor, "COLOR_ENABLED", True)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", {"link": link})

    assert monitor.colorize_links("Guide: https://example.test/page") == f"Guide: {link}https://example.test/page{monitor.ANSI_RESET}"


# Verifies no setup screen prints a link without colouring it, which is how a plain link gets in
def test_no_setup_screen_prints_a_plain_link():
    setup = re.compile(r"^(?:run_setup_wizard|run_scrobble_health_setup_wizard|_wizard_|run_set_|run_browser_cookie_import|print_welcome_screen|print_doctor_next_steps|print_spotify_scrobble_app_guidance)")
    tree = ast.parse(Path(monitor.__file__).read_text(encoding="utf-8"))
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    plain = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print"):
            continue
        nested = list(ast.walk(node))
        prints_link = any(isinstance(item, ast.Constant) and isinstance(item.value, str) and "http" in item.value for item in nested) or any(isinstance(item, ast.Name) and "URL" in item.id for item in nested)
        coloured = any(isinstance(item, ast.Name) and item.id in ("colorize", "colorize_links") for item in nested)
        owner, current = "", parents.get(node)
        while current is not None:
            if isinstance(current, ast.FunctionDef):
                owner = current.name
                break
            current = parents.get(current)
        if prints_link and not coloured and setup.match(owner):
            plain.append(f"{owner}:{node.lineno}")

    assert plain == []


# Verifies a fix block keeps its guide line a link while the rest of the block stays informational
def test_a_fix_block_guide_line_is_a_link(monkeypatch):
    link = monitor._build_ansi_sequence(monitor.DEFAULT_COLOR_THEME["link"])
    info = monitor._build_ansi_sequence(monitor.DEFAULT_COLOR_THEME["info"])
    monkeypatch.setattr(monitor, "COLOR_ENABLED", True)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", {"link": link, "info": info})

    assert monitor.colorize_fix_line("To fix: Set the key then re-run") == f"{info}To fix: Set the key then re-run{monitor.ANSI_RESET}"
    assert monitor.colorize_fix_line("Guide: https://example.test/page") == f"Guide: {link}https://example.test/page{monitor.ANSI_RESET}"
    assert 'colorize("info", f"Guide:' not in Path(monitor.__file__).read_text(encoding="utf-8")


# Verifies the early peek carries the theme, since --help is printed and exited from inside argparse before the config load
def test_the_early_output_config_carries_the_help_theme(monkeypatch, tmp_path):
    (tmp_path / "github_monitor.conf").write_text('COLOR_THEME = {"help_heading": "bright_red"}\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(monitor, "COLOR_THEME", {})
    monkeypatch.setattr(monitor, "CONFIG_DISCOVERY_DISABLED", False)
    monkeypatch.setattr(monitor.sys, "argv", ["github_monitor", "--help"])

    monitor.apply_early_output_config()

    assert monitor.COLOR_THEME == {"help_heading": "bright_red"}
