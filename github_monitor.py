#!/usr/bin/env python3
"""
Author: Michal Szymanski <misiektoja-github@rm-rf.ninja>
v2.7

OSINT tool implementing real-time tracking of GitHub users activities including profile and repositories changes:
https://github.com/misiektoja/github_monitor/

Python pip3 requirements:

PyGithub
requests
python-dateutil
pytz
tzlocal
python-dotenv
colorama (optional, improves classic Windows Command Prompt colour support)
wcwidth (optional, needed by TRUNCATE_CHARS)
"""

VERSION = "2.7"

PROJECT_URL = "https://github.com/misiektoja/github_monitor"
README_URL = f"{PROJECT_URL}/blob/main/README.md"
QUICK_START_GUIDE_URL = f"{README_URL}#quick-start"
CONFIG_GUIDE_URL = f"{README_URL}#configuration"
AUTH_GUIDE_URL = f"{README_URL}#github-personal-access-token"
GITHUB_TOKEN_SETTINGS_URL = "https://github.com/settings/tokens"
NOTIFICATION_GUIDE_URL = f"{README_URL}#email-notifications"
DEBUG_GUIDE_URL = f"{README_URL}#debugging-and-recovery"
TLS_GUIDE_URL = f"{README_URL}#tls-verification"
SUPPORT_GUIDE_URL = f"{PROJECT_URL}/blob/main/SUPPORT.md"
DOCTOR_GUIDE_URL = f"{SUPPORT_GUIDE_URL}#doctor-preflight"

# Shared doctor labels for the two delivery channels, kept identical to the sibling monitors
SMTP_READY_CHECK_LABEL = "SMTP connection and login succeeded"
WEBHOOK_READY_CHECK_LABEL = "Webhook URL, headers and alert choices look valid"
MIN_PYTHON_VERSION = (3, 10)

# ---------------------------
# CONFIGURATION SECTION START
# ---------------------------

CONFIG_BLOCK = """
# Optional saved target used when no positional GitHub username is supplied
# A positional target always overrides this value
TARGET_GITHUB_USERNAME = ""

# Create or review your GitHub personal access tokens at:
# https://github.com/settings/tokens
#
# Preferred method:
#   - Run github_monitor --set-github-token to validate the token and save it through a hidden prompt
# Fallback methods:
#   - Set it as an environment variable (e.g. export GITHUB_TOKEN=...)
#   - Add it manually to ".env" file (GITHUB_TOKEN=...) for persistent use
#   - Pass it at runtime with -t / --github-token (may remain in shell history)
#   - Hard-code it in the code or config file
GITHUB_TOKEN = "your_github_classic_personal_access_token"

# The URL of the GitHub API
#
# For Public Web GitHub use the default: https://api.github.com
# For GitHub Enterprise change to: https://{your_hostname}/api/v3
#
# Can also be set using the -x flag
GITHUB_API_URL = "https://api.github.com"

# The base URL of the GitHub web interface
# Required to check if the profile is public or private
#
# For public GitHub use the default: https://github.com
# For GitHub Enterprise change to: https://{your_hostname}
GITHUB_HTML_URL = "https://github.com"

# SMTP settings for sending email notifications
# If left as-is, no notifications will be sent
#
# Provide the SMTP_PASSWORD secret using one of the following methods:
#   - Set it as an environment variable (e.g. export SMTP_PASSWORD=...)
#   - Add it to ".env" file (SMTP_PASSWORD=...) for persistent use
# Fallback:
#   - Hard-code it in the code or config file
SMTP_HOST = "your_smtp_server_ssl"
SMTP_PORT = 587
SMTP_USER = "your_smtp_user"
SMTP_PASSWORD = "your_smtp_password"
SMTP_SSL = True
SENDER_EMAIL = "your_sender_email"
RECEIVER_EMAIL = "your_receiver_email"

# Whether to send an email when user's profile changes
# Can also be enabled via the -p flag
PROFILE_NOTIFICATION = False

# Whether to send an email when new GitHub events appear
# Can also be enabled via the -s flag
EVENT_NOTIFICATION = False

# Whether to send an email when user's repositories change (stargazers, watchers, forks, issues,
# PRs, discussions, description etc., except for update date)
# Requires TRACK_REPOS_CHANGES to be enabled
# Can also be enabled via the -q flag
REPO_NOTIFICATION = False

# Whether to send an email when user's repositories update date changes
# Can also be enabled via the -u flag
REPO_UPDATE_DATE_NOTIFICATION = False

# Whether to send an email when user's daily contributions count changes
# Requires TRACK_CONTRIB_CHANGES to be enabled
# Can also be enabled via the -y flag
CONTRIB_NOTIFICATION = False

# Whether to send an email on errors
# Can also be disabled via the -e flag
ERROR_NOTIFICATION = True

# ----------------------------
# Webhook Notifications
# ----------------------------

# Master switch for webhook notifications through Discord or ntfy
# Event settings below select which notifications are sent
# Can also be enabled via the --webhook flag
WEBHOOK_ENABLED = False

# Service used to deliver webhook notifications: "discord" or "ntfy"
# Known Discord and ntfy.sh URLs correct a mismatched configured value at runtime
# Can also be set via the --webhook-provider flag
WEBHOOK_PROVIDER = "discord"

# Private destination used to send webhook notifications
# Discord: Edit Channel -> Integrations -> Webhooks -> New Webhook -> Copy Webhook URL
# ntfy: complete topic URL such as https://ntfy.sh/your-private-topic
# Prefer --set-webhook-url, an environment variable or a dotenv file instead of storing this private URL here
# The --webhook-url flag is available for one-run overrides but may leave the private URL in shell history
WEBHOOK_URL = "your_webhook_url"

# Discord display name (leave empty to use the webhook default)
# Applies only when WEBHOOK_PROVIDER is "discord" (ignored by the ntfy provider)
WEBHOOK_USERNAME = "GitHub Monitor"

# Discord avatar URL (leave empty to use the webhook default)
# Applies only when WEBHOOK_PROVIDER is "discord" (ignored by the ntfy provider)
WEBHOOK_AVATAR_URL = ""

# Whether to send a webhook notification when the user's profile changes
# Can also be enabled via the --webhook-profile flag
WEBHOOK_PROFILE_NOTIFICATION = False

# Whether to send a webhook notification when new GitHub events appear
# Can also be enabled via the --webhook-events flag
WEBHOOK_EVENT_NOTIFICATION = False

# Whether to send a webhook notification when the user's repositories change
# Requires TRACK_REPOS_CHANGES to be enabled
# Can also be enabled via the --webhook-repo-changes flag
WEBHOOK_REPO_NOTIFICATION = False

# Whether to send a webhook notification when a repository update date changes
# Requires TRACK_REPOS_CHANGES to be enabled
# Can also be enabled via the --webhook-repo-update-date flag
WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION = False

# Whether to send a webhook notification when the user's daily contributions count changes
# Requires TRACK_CONTRIB_CHANGES to be enabled
# Can also be enabled via the --webhook-daily-contribs flag
WEBHOOK_CONTRIB_NOTIFICATION = False

# Whether to send a webhook notification on monitoring errors
# Can also be enabled via --webhook-errors or disabled via --no-webhook-error-notify
WEBHOOK_ERROR_NOTIFICATION = True

# Optional request headers for advanced webhook integrations
# Values support the same placeholders as WEBHOOK_TEMPLATE
WEBHOOK_HEADERS = {}

# ----------------------------
# Advanced Webhook Settings
# ----------------------------

# Discord-format webhook request payload template
# Applies only when WEBHOOK_PROVIDER is "discord". The "ntfy" provider needs no template and ignores this
# value: it sends the alert body as a native ntfy message with the subject as its title. Use WEBHOOK_HEADERS
# to add ntfy options such as priority or tags
# Supported placeholders include title, description, version, image_url, fields, fields_str, color, timestamp,
# username and avatar_url
WEBHOOK_TEMPLATE = {
    "username": "{username}",
    "avatar_url": "{avatar_url}",
    "allowed_mentions": {
        "parse": [],
    },
    "embeds": [{
        "title": "{title}",
        "description": "{description}",
        "color": "{color}",
        "footer": {
            "text": "GitHub Monitor v{version}",
        },
        "timestamp": "{timestamp}",
    }],
}

# Optional transformations applied to WEBHOOK_TEMPLATE and WEBHOOK_HEADERS values
# Tuple format: (field_to_target, method_name, *optional_arguments)
#
# Examples:
#   [
#       ("title", "upper"),
#       ("description", "replace", "**", ""),
#       ("description", "strip"),
#   ]
WEBHOOK_TRANSFORMS = []

# Optional ntfy access token for Bearer authentication
# Prefer an environment variable or dotenv file instead of storing this token here
NTFY_ACCESS_TOKEN = ""

# How often to check for user profile changes / activities; in seconds
# Can also be set using the -c flag
GITHUB_CHECK_INTERVAL = 1800  # 30 mins

# Set your local time zone so that GitHub API timestamps are converted accordingly (e.g. 'Europe/Warsaw')
# Use this command to list all time zones supported by pytz:
#   python3 -c "import pytz; print('\\n'.join(pytz.all_timezones))"
# If set to 'Auto', the tool will try to detect your local time zone automatically (requires tzlocal)
LOCAL_TIMEZONE = 'Auto'

# Events to monitor
# Use 'ALL' to monitor all available event types
EVENTS_TO_MONITOR = [
    'ALL',
    'PushEvent',
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent',
    'IssuesEvent',
    'CommitCommentEvent',
    'CreateEvent',
    'DeleteEvent',
    'ForkEvent',
    'PublicEvent',
    'GollumEvent',
    'MemberEvent',
    'WatchEvent',
    'ReleaseEvent',
    'DiscussionEvent',
]

# Number of recent events to fetch when a change in the last event ID is detected
# Note: if more than EVENTS_NUMBER events occur between two checks,
# any events older than the most recent EVENTS_NUMBER will be missed
EVENTS_NUMBER = 30  # 1 page

# If True, track user's repository changes (changed stargazers, watchers, forks, issues, PRs, discussions, description, update date etc.)
# Can also be enabled using the -j flag
TRACK_REPOS_CHANGES = False

# Repositories to monitor when TRACK_REPOS_CHANGES is enabled
# Use 'ALL' to monitor all repositories (default behavior)
# Use 'user/repo_name' format to monitor specific repositories for specific users
# If the current user matches the user in the list, that repository will be monitored
# Example: ['user1/repo1', 'user2/repo2', 'user1/repo3']
# Can also be set using the --repos flag (comma-separated repo names only, without user prefix)
# Example: --repos "repo1,repo2,repo3"
# Note: When using a specific list (not 'ALL'), newly created repositories will NOT be
# automatically monitored - only repositories explicitly listed here will be monitored.
REPOS_TO_MONITOR = ['ALL']

# If True, disable event monitoring
# Can also be disabled using the -k flag
DO_NOT_MONITOR_GITHUB_EVENTS = False

# If True, fetch all user repos (owned, forks, collaborations); otherwise, fetch only owned repos
GET_ALL_REPOS = False

# Alert about blocked (403 - TOS violation and 451 - DMCA block) repos in the console output (in monitoring mode)
# In listing mode (-r), blocked repos are always shown
BLOCKED_REPOS = False

# If True, track and log user's daily contributions count changes
# Can also be enabled using the -m flag
TRACK_CONTRIB_CHANGES = False

# How often to print a "liveness check" message to the output; in seconds
# Set to 0 to disable
LIVENESS_CHECK_INTERVAL = 43200  # 12 hours

# URL used to verify internet connectivity at startup
CHECK_INTERNET_URL = GITHUB_API_URL

# Timeout used when checking initial internet connectivity; in seconds
CHECK_INTERNET_TIMEOUT = 5

# Whether to verify TLS certificates on every outbound request
# Only set this to False on a network that intercepts TLS with its own certificate authority
# Switching it off removes the protection against an intercepted connection
VERIFY_SSL = True

# CSV file to write new events & profile changes
# Can also be set using the -b flag
CSV_FILE = ""

# Location of the optional dotenv file which can keep secrets
# If not specified it will try to auto-search for .env files
# To disable auto-search, set this to the literal string "none"
# Can also be set using the --env-file flag
DOTENV_FILE = ""

# Base name for the log file. Output will be saved to github_monitor_<username>.log
# Can include a directory path to specify the location, e.g. ~/some_dir/github_monitor
GITHUB_LOGFILE = "github_monitor"

# Whether to disable logging to github_monitor_<username>.log
# Can also be disabled via the -d flag
DISABLE_LOGGING = False

# Controls conversion of separator-only log lines to ASCII:
#   "Auto" - enable on Windows only (default)
#   "On"   - enable on every operating system
#   "Off"  - preserve Unicode separators in logs
ASCII_LOG_SEPARATORS = "Auto"

# Width of main horizontal line
HORIZONTAL_LINE1 = 105

# Width of horizontal line for repositories list output
HORIZONTAL_LINE2 = 80

# Whether to clear the terminal screen after starting the tool
CLEAR_SCREEN = True

# Whether output includes user-facing decisions, degraded features and complete startup settings
# Independent of DEBUG_MODE, so enable both to see everything
# Can also be enabled via --verbose, which turns it on regardless of this setting
VERBOSE_MODE = False

# Whether output includes sanitized operations, requests, files, retries and poll timing
# Independent of VERBOSE_MODE, so enable both to see everything
# Can also be enabled via --debug, which turns it on regardless of this setting
DEBUG_MODE = False

# Whether to use coloured output in the terminal (auto-disabled if the terminal
# does not appear to support colours or when output is redirected to a file)
# Can also be disabled via the --no-color flag
COLORED_OUTPUT = True

# Colour theme used for different parts of the output
# Keys are logical names used by the tool, values are colour/style strings
# You can combine multiple attributes with spaces or '+', for example:
#   "bright_cyan bold", "yellow", "red underline", "bright_magenta bold underline", "red bold blink"
# Valid colour names: black, red, green, yellow, blue, magenta, cyan, white,
# and their bright_ variants (bright_red, bright_green, ...).
COLOR_THEME = {
    # Headings and commands the wizard tells you to run
    "header": "bright_cyan",
    "section": "bright_white",
    # Identity
    "username": "blue underline",
    "id": "bright_magenta",
    # Presence and visibility status values
    "status_online": "green",
    "status_offline": "red",
    "status_other": "white",
    # GitHub objects
    "repository": "green",
    "event": "bright_green",
    "commit": "bright_yellow",
    "branch": "bright_magenta",
    "duration": "green",
    # Misc
    "timestamp_label": "",
    "timestamp": "cyan",
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "signal": "yellow",
    "email": "bright_cyan",
    "webhook": "bright_blue",
    # Dates
    "date": "magenta",
    "date_range": "magenta",
    # Boolean values
    "boolean_true": "green",
    "boolean_false": "red",
    # Counters and differences
    "count_up": "green",
    "count_down": "red",
    "url": "blue underline",
}

# Max characters per line when printing to screen to avoid line wrapping
# Does not affect log file output
# Set to 999 to auto-detect terminal width
# Applies only when DISABLE_LOGGING is False
# Can also be set via the --truncate flag
TRUNCATE_CHARS = 0

# Maximum number of times to retry a failed GitHub API/network call
NET_MAX_RETRIES = 5

# Base number of seconds to wait before each retry, multiplied by the attempt count
NET_BASE_BACKOFF_SEC = 5

# Value used by signal handlers increasing/decreasing profile/user activity check (GITHUB_CHECK_INTERVAL); in seconds
GITHUB_CHECK_SIGNAL_VALUE = 60  # 1 minute
"""

# -------------------------
# CONFIGURATION SECTION END
# -------------------------

# Default dummy values so linters shut up
# Do not change values below - modify them in the configuration section or config file instead
TARGET_GITHUB_USERNAME = ""
GITHUB_TOKEN = ""
GITHUB_API_URL = ""
GITHUB_HTML_URL = ""
SMTP_HOST = ""
SMTP_PORT = 0
SMTP_USER = ""
SMTP_PASSWORD = ""
SMTP_SSL = False
SENDER_EMAIL = ""
RECEIVER_EMAIL = ""
PROFILE_NOTIFICATION = False
EVENT_NOTIFICATION = False
REPO_NOTIFICATION = False
REPO_UPDATE_DATE_NOTIFICATION = False
CONTRIB_NOTIFICATION = False
ERROR_NOTIFICATION = False
WEBHOOK_ENABLED = False
WEBHOOK_PROVIDER = ""
WEBHOOK_URL = ""
WEBHOOK_USERNAME = ""
WEBHOOK_AVATAR_URL = ""
WEBHOOK_PROFILE_NOTIFICATION = False
WEBHOOK_EVENT_NOTIFICATION = False
WEBHOOK_REPO_NOTIFICATION = False
WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION = False
WEBHOOK_CONTRIB_NOTIFICATION = False
WEBHOOK_ERROR_NOTIFICATION = False
WEBHOOK_HEADERS = {}
WEBHOOK_TEMPLATE = {}
WEBHOOK_TRANSFORMS = []
NTFY_ACCESS_TOKEN = ""
GITHUB_CHECK_INTERVAL = 0
LOCAL_TIMEZONE = ""
EVENTS_TO_MONITOR = []
EVENTS_NUMBER = 0
TRACK_REPOS_CHANGES = False
REPOS_TO_MONITOR = []
DO_NOT_MONITOR_GITHUB_EVENTS = False
GET_ALL_REPOS = False
BLOCKED_REPOS = False
TRACK_CONTRIB_CHANGES = False
LIVENESS_CHECK_INTERVAL = 0
CHECK_INTERNET_URL = ""
CHECK_INTERNET_TIMEOUT = 0
VERIFY_SSL = True
CSV_FILE = ""
DOTENV_FILE = ""
GITHUB_LOGFILE = ""
DISABLE_LOGGING = False
ASCII_LOG_SEPARATORS = "Auto"
HORIZONTAL_LINE1 = 0
HORIZONTAL_LINE2 = 0
CLEAR_SCREEN = False
VERBOSE_MODE = False
DEBUG_MODE = False
COLORED_OUTPUT = False
COLOR_THEME: dict = {}
TRUNCATE_CHARS = 0
NET_MAX_RETRIES = 0
NET_BASE_BACKOFF_SEC = 0
GITHUB_CHECK_SIGNAL_VALUE = 0

exec(CONFIG_BLOCK, globals())

# Default name for the optional config file
DEFAULT_CONFIG_FILENAME = "github_monitor.conf"

# List of secret keys to load from env/config
SECRET_KEYS = ("GITHUB_TOKEN", "SMTP_PASSWORD", "WEBHOOK_URL", "NTFY_ACCESS_TOKEN")

# Effective source name for each configured secret without storing another copy of its value
SECRET_SOURCES = {}

# Version incremented when SIGHUP reloads the GitHub token
GITHUB_AUTH_REFRESH_VERSION = 0

LIVENESS_CHECK_COUNTER = LIVENESS_CHECK_INTERVAL / GITHUB_CHECK_INTERVAL

stdout_bck = None
csvfieldnames = ['Date', 'Type', 'Name', 'Old', 'New']

CLI_CONFIG_PATH = None

# Maximum length for event body text (issue bodies, comment bodies, etc.) before truncation
# Text longer than this will be truncated with safe HTML tag closing
MAX_EVENT_BODY_LENGTH = 3500

# to solve the issue: 'SyntaxError: f-string expression part cannot include a backslash'
nl_ch = "\n"

STARTUP_BANNER = r"""
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


import sys
import importlib.util
import shlex


# Writes the uncoloured startup banner for bootstrap failures
def _write_plain_startup_banner(destination):
    destination.write(STARTUP_BANNER + "\n")
    destination.write(f"{'':21}v{VERSION}\n\n")


# Renders an environment-only doctor report when Python cannot run the full module
def bootstrap_doctor_python_report(stream=None):
    if sys.version_info >= MIN_PYTHON_VERSION:
        return None
    destination = sys.stdout if stream is None else stream
    version = ".".join(str(part) for part in sys.version_info[:3])
    minimum = ".".join(str(part) for part in MIN_PYTHON_VERSION)
    install_command = f"Install Python {minimum} or newer"
    _write_plain_startup_banner(destination)
    destination.write("Running preflight checks. No files will be written. Interactive email and webhook tests run only after separate approval.\n\n")
    destination.write(f"Doctor\n\nEnvironment\n[FAIL] Python {version} is unsupported\n  Minimum supported version: {minimum}\nTo fix: {install_command}\nGuide: {DOCTOR_GUIDE_URL}\n")
    destination.write(f"\nSummary\n  1 check(s) failed, 0 warning(s). Fix the failures above before relying on the tool.\n\nGuide: {DOCTOR_GUIDE_URL}\n")
    destination.flush()
    return 1


if sys.version_info < MIN_PYTHON_VERSION:
    if "--doctor" in sys.argv:
        sys.exit(bootstrap_doctor_python_report())
    print("* Error: Python version 3.10 or higher required !")
    sys.exit(1)


# Renders an environment-only doctor report when required imports prevent full startup
def bootstrap_doctor_dependency_report(module_finder=None, stream=None):
    finder = importlib.util.find_spec if module_finder is None else module_finder
    required = (("requests", "requests"), ("urllib3", "urllib3"), ("python-dateutil", "dateutil"), ("pytz", "pytz"), ("PyGithub", "github"))
    optional = (("python-dotenv", "dotenv", "dotenv discovery and loading"), ("tzlocal", "tzlocal", "automatic timezone detection"))
    availability = {}
    for package_name, module_name in required:
        try:
            availability[package_name] = finder(module_name) is not None
        except (ImportError, AttributeError, ValueError):
            availability[package_name] = False
    if all(availability.values()):
        return None
    destination = sys.stdout if stream is None else stream
    _write_plain_startup_banner(destination)
    destination.write("Running preflight checks. No files will be written. Interactive email and webhook tests run only after separate approval.\n\n")
    destination.write("Doctor\n\nEnvironment\n")
    version = ".".join(str(part) for part in sys.version_info[:3])
    minimum = ".".join(str(part) for part in MIN_PYTHON_VERSION)
    destination.write(f"[PASS] Python {version} is supported\n  Minimum supported version: {minimum}\n")
    failures = 0
    warnings = 0
    for package_name, _ in required:
        if availability[package_name]:
            destination.write(f"[PASS] Required dependency {package_name} is installed\n")
        else:
            failures += 1
            install_command = shlex.join([sys.executable, "-m", "pip", "install", package_name])
            destination.write(f"[FAIL] Required dependency {package_name} is missing\n  The full preflight cannot continue without this package\nTo fix: Install it with: {install_command}\nGuide: {DOCTOR_GUIDE_URL}\n")
    for package_name, module_name, feature in optional:
        try:
            available = finder(module_name) is not None
        except (ImportError, AttributeError, ValueError):
            available = False
        if available:
            destination.write(f"[PASS] Optional dependency {package_name} is installed\n  Used only for {feature}\n")
        else:
            warnings += 1
            install_command = shlex.join([sys.executable, "-m", "pip", "install", package_name])
            destination.write(f"[WARN] Optional dependency {package_name} is not installed\n  {feature.capitalize()} will not work while other features remain available\nTo fix: Install it with: {install_command}\nGuide: {DOCTOR_GUIDE_URL}\n")
    destination.write(f"\nSummary\n  {failures} check(s) failed, {warnings} warning(s). Fix the failures above before relying on the tool.\n\nGuide: {DOCTOR_GUIDE_URL}\n")
    destination.flush()
    return 1


if "--doctor" in sys.argv and not any(flag in sys.argv for flag in ("--help", "-h", "--version")):
    bootstrap_doctor_exit = bootstrap_doctor_dependency_report()
    if bootstrap_doctor_exit is not None:
        sys.exit(bootstrap_doctor_exit)

import time
import os
from datetime import datetime, timezone, date
from dateutil import relativedelta
from dateutil.parser import isoparse
import calendar
import requests as req
import signal
import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import argparse
import ast
import csv
from dataclasses import dataclass, field
import getpass
import subprocess
import tempfile
try:
    import pytz
except ModuleNotFoundError:
    raise SystemExit("Error: Couldn't find the pytz library !\n\nTo install it, run:\n    pip3 install pytz\n\nOnce installed, re-run this tool")
try:
    from tzlocal import get_localzone
except ImportError:
    get_localzone = None
import platform
import re
try:
    from colorama import init as colorama_init
except ImportError:
    colorama_init = None
import ipaddress
import html
try:
    from github import Github, Auth, GithubException, UnknownObjectException
    from github.GithubException import RateLimitExceededException
    from github.GithubException import BadCredentialsException
except ModuleNotFoundError:
    raise SystemExit("Error: Couldn't find the PyGitHub library !\n\nTo install it, run:\n    pip3 install PyGithub\n\nOnce installed, re-run this tool. For more help, visit:\nhttps://github.com/PyGithub/PyGithub")
from itertools import islice
import textwrap
import urllib3
import socket
from typing import Any, Callable, cast
import shutil
from pathlib import Path, PureWindowsPath
from typing import Optional
import datetime as dt
import requests
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

NET_ERRORS = (
    req.exceptions.RequestException,
    urllib3.exceptions.HTTPError,
    socket.gaierror,
    GithubException,
)

WEBHOOK_SESSION = req.Session()

# Keep webhook delivery independent from GitHub API retries and long server timers
WEBHOOK_MAX_ATTEMPTS = 2
WEBHOOK_MAX_RETRY_AFTER_SECONDS = 5.0
WEBHOOK_FALLBACK_RETRY_SECONDS = 1.0
WEBHOOK_TIMEOUT_SECONDS = 10
WEBHOOK_EMBED_TITLE_LIMIT = 256
WEBHOOK_EMBED_DESCRIPTION_LIMIT = 4096
NTFY_MESSAGE_LIMIT_BYTES = 4095
NTFY_TRUNCATION_SUFFIX = "\n\n[Notification truncated to fit ntfy's 4 KB message limit]"
PYGITHUB_TIMEOUT_SECONDS = 15

# Calendar days requested to stabilize one-day contribution count lookups
DAILY_CONTRIBUTION_LOOKBACK_DAYS = 30

# Shortest secret replaced by plain substring search. Sanitizing runs over normal monitoring output, so a
# short value such as a simple SMTP password would otherwise redact ordinary words like repository names.
# Every credential this tool handles is far longer, and shorter ones stay covered by the shape patterns
# in sanitize_error_text that match the assignment and header forms an error can actually expose.
MIN_REDACTABLE_SECRET_LENGTH = 12


# Reports whether separator-only log lines should use ASCII on this system
def ascii_log_separators_enabled():
    mode = str(ASCII_LOG_SEPARATORS).strip().lower()
    if mode not in {"auto", "on", "off"}:
        raise ValueError("ASCII_LOG_SEPARATORS must be 'Auto', 'On' or 'Off'")
    return mode == "on" or (mode == "auto" and platform.system() == "Windows")


# Converts Unicode-only horizontal separator lines to ASCII when configured
def normalize_log_separators(message):
    if not ascii_log_separators_enabled():
        return message
    return re.sub(r"(?m)^─+$", lambda match: match.group(0).replace("─", "-"), message)


# Truncates each line to a display width after tab expansion
def truncate_string_per_line(message, truncate_width, tabsize=8):
    try:
        from wcwidth import wcwidth
    except ImportError:
        return message
    lines = message.split("\n")
    truncated_lines = []
    for line in lines:
        expanded_line = line.expandtabs(tabsize)
        current_width = 0
        truncated = ""
        for char in expanded_line:
            char_width = wcwidth(char)
            if char_width < 0:
                char_width = 0
            if current_width + char_width > truncate_width:
                break
            truncated += char
            current_width += char_width
        truncated_lines.append(truncated)
    return "\n".join(truncated_lines)


# Resolves CLI and configured truncation settings while expanding the terminal-width sentinel
def resolve_truncate_chars(cli_value, configured_value, logging_disabled):
    truncate_chars = configured_value if cli_value is None else cli_value
    if logging_disabled:
        return 0
    if truncate_chars == 999:
        terminal_size = shutil.get_terminal_size()
        print(f"The detected terminal screen width is: {terminal_size.columns} characters\n")
        return terminal_size.columns
    return truncate_chars


# Matches any ANSI escape sequence for terminal sanitizing and plain log output
ANSI_ESCAPE_RE = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")

# Matches the SGR sequences emitted and preserved by the colour layer
SGR_SEQUENCE_RE = re.compile(r"\x1b\[[0-9;]*m")

# Drops every remaining control character except tab and newline
TERMINAL_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


# Removes terminal controls while preserving SGR colours and ordinary layout
def sanitize_terminal_text(message):
    if not isinstance(message, str) or not message:
        return message
    parts = []
    position = 0
    for match in SGR_SEQUENCE_RE.finditer(message):
        parts.append(TERMINAL_CONTROL_RE.sub("", message[position:match.start()]))
        parts.append(match.group(0))
        position = match.end()
    parts.append(TERMINAL_CONTROL_RE.sub("", message[position:]))
    return "".join(parts)


COLOR_ENABLED = False
_COLOR_STYLES: dict = {}

# Default built-in colour theme. Values can be overridden via COLOR_THEME in config
DEFAULT_COLOR_THEME = {
    # Headings and commands the wizard tells you to run
    "header": "bright_cyan",
    "section": "bright_white",
    # Identity
    "username": "blue underline",
    "id": "bright_magenta",
    # Presence and visibility status values
    "status_online": "green",
    "status_offline": "red",
    "status_other": "white",
    # GitHub objects
    "repository": "green",
    "event": "bright_green",
    "commit": "bright_yellow",
    "branch": "bright_magenta",
    "duration": "green",
    # Misc
    "timestamp_label": "",
    "timestamp": "cyan",
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "signal": "yellow",
    "email": "bright_cyan",
    "webhook": "bright_blue",
    # Dates
    "date": "magenta",
    "date_range": "magenta",
    # Boolean values
    "boolean_true": "green",
    "boolean_false": "red",
    # Counters and differences
    "count_up": "green",
    "count_down": "red",
    "url": "blue underline",
}

ANSI_RESET = "\033[0m"

_STYLE_CODES = {
    "bold": "1",
    "dim": "2",
    "underline": "4",
    "blink": "5",
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "bright_black": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
}

_LABEL_STYLES = (
    (("Target:", "Username:", "Token belongs to:", "Event actor login:", "Event actor name:", "Published by:", "Commit author:", "Author:", "Issue author:", "Comment author:", "Discussion comment by:", "Member added:", "Assignee:", "Requested reviewer:"), "username"),
    (("Event ID:", "Review ID:", "Commit SHA:", "Commit SHA reviewed:"), "id"),
    (("Repo name:", "Forked to repo:"), "repository"),
    (("Event type:", "Release name:", "Release tag name:", "Issue title:", "Discussion title:"), "event"),
    (("Commit message:",), "commit"),
    (("Object name:", "Target commitish:", "Branch (default):"), "branch"),
    (("Email:",), "email"),
)

_FROM_TO_COUNT_RE = re.compile(r"(from\s+)(\d+)(\s+to\s+)(\d+)")
_DIFF_COUNT_UP_RE = re.compile(r"(\(\+\d+\))")
_DIFF_COUNT_DOWN_RE = re.compile(r"(\(-\d+\))")
# The separator is a space in prose and an equals sign in the key=value diagnostic fields
_USER_TAG_RE = re.compile(r"((?:GitHub user|for user|by user|of user|Monitoring GitHub user|\buser):?)([\t ]+|=)([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))")
_QUOTED_CONTEXT_RE = re.compile(r"\b(repo|user)\s+$", re.IGNORECASE)
_DURATION_RE = re.compile(r"~?\b[0-9]{1,20}[ \t]{1,20}(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b", re.IGNORECASE)
_LONG_DATE_RE = re.compile(r"\b(?:\w{3}\s+)?\d{1,2}\s+\w{3}(?:\s+\d{2,4})?[\s,]*\d{2}:\d{2}(:\d{2})?(\s*[AP]M)?\b", re.IGNORECASE)
_TIME_ONLY_RE = re.compile(r"(?<![\w:])(~?(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?:\s*[AP]M)?)(?![\w:])", re.IGNORECASE)
_SHORT_RANGE_DATE_RE = re.compile(r"\(\w{3}\s+\d{1,2}\s+\w{3}\s+\d{2}:\d{2}(\s*[AP]M)?\s*-\s*\d{2}:\d{2}(\s*[AP]M)?\)", re.IGNORECASE)
_DATE_RANGE_RE = re.compile(r"\b\w{3}\s+\d{1,2}\s+\w{3}\s+\d{2}:\d{2}(\s*[AP]M)?\s*-\s*\d{2}:\d{2}(\s*[AP]M)?\b", re.IGNORECASE)
_HOUR_RANGE_RE = re.compile(r"\b\d{2}:\d{2}(\s*[AP]M)?\s*-\s*\d{2}:\d{2}(\s*[AP]M)?\b", re.IGNORECASE)
_URL_RE = re.compile(r"(https?://[^\s\]]+)")
_BOOLEAN_TRUE_RE = re.compile(r"\bTrue\b|\bEnabled\b")
_BOOLEAN_FALSE_RE = re.compile(r"\bFalse\b|\bDisabled\b")
_NOTIFICATION_SUMMARY_STATE_RE = re.compile(r"^(\* Notifications \((?:email|webhook)\):\s+)(On|Off)(.*)$")
_PROFILE_VISIBILITY_CHANGE_RE = re.compile(r"(profile visibility to )(')(public|private)(')", re.IGNORECASE)
_BLOCK_CHANGE_RE = re.compile(r"(?<= has )(blocked|unblocked)(?= you!)", re.IGNORECASE)
_REPOSITORY_PUBLIC_RE = re.compile(r"(?<=Repository is now )(public)\b", re.IGNORECASE)
_DEBUG_LINE_RE = re.compile(r"^\[debug \d{2}:\d{2}:\d{2}\]")
_DOCTOR_MARK_RE = re.compile(r"^\[(PASS|WARN|FAIL|SKIP)\]")
_DOCTOR_MARK_STYLES = {"PASS": "boolean_true", "WARN": "warning", "FAIL": "error", "SKIP": "info"}
_QUOTED_CONTENT_RE = re.compile(r"(')([^'\n]*\w[^'\n]*)(')")
_QUOTED_FILE_LIKE_RE = re.compile(r"^[~.]?[\\/]|^[A-Za-z]:[\\/]|\.[A-Za-z0-9]{1,8}$")
_REPOSITORY_LIST_RE = re.compile(r"^(🔸\s+)(\S+?)(\s+\(fork\))?\s*$")
_LINKED_LIST_ITEM_RE = re.compile(r"^(-\s+)([^\s\[]+)(\s+\[\s*)(https?://[^\s\]]+)(\s*\])$")
_USER_LIST_RE = re.compile(r"^(-\s+)([A-Za-z0-9](?:[A-Za-z0-9-]{0,38})(?:\s+\([^)\n]+\))?)$")
_ERROR_LINE_RE = re.compile(r"^(?:\*\s*)?(?:error\b|cannot\b|critical:|failure\b)", re.IGNORECASE)
_WARNING_LINE_RE = re.compile(r"^(?:\*\s*)?warning\b|^caution:", re.IGNORECASE)


# Builds one ANSI SGR sequence from a style description
def _build_ansi_sequence(style_str):
    if not style_str:
        return ""
    codes = []
    for part in re.split(r"[+ ]+", style_str.strip().lower()):
        code = _STYLE_CODES.get(part)
        if code:
            codes.append(code)
    return f"\033[{';'.join(codes)}m" if codes else ""


# Detects whether one output stream supports ANSI colours
def _stream_supports_color(stream):
    try:
        interactive = hasattr(stream, "isatty") and bool(stream.isatty())
    except (OSError, ValueError):
        interactive = False
    if not interactive:
        return False
    if os.getenv("NO_COLOR"):
        return False
    if not (colorama_init and platform.system() == "Windows"):
        term = os.getenv("TERM", "")
        if term.lower() in ("", "dumb", "unknown"):
            return False
    if hasattr(sys.stdin, "isatty") and not sys.stdin.isatty():
        return False
    return True


# Initializes colour output from configuration and terminal capabilities
def init_color_output(stream):
    global COLOR_ENABLED, _COLOR_STYLES
    if colorama_init and platform.system() == "Windows":
        try:
            colorama_init(autoreset=False)
        except (AttributeError, OSError, RuntimeError, ValueError):
            pass
    COLOR_ENABLED = bool(globals().get("COLORED_OUTPUT", False)) and _stream_supports_color(stream)
    if not COLOR_ENABLED:
        _COLOR_STYLES = {}
        return
    user_theme = globals().get("COLOR_THEME") if isinstance(globals().get("COLOR_THEME"), dict) else {}
    theme = {**DEFAULT_COLOR_THEME, **(user_theme or {})}
    _COLOR_STYLES = {name: sequence for name, value in theme.items() if (sequence := _build_ansi_sequence(value))}


# Applies one configured logical colour style to text
def colorize(part, text):
    if not COLOR_ENABLED:
        return text
    start = _COLOR_STYLES.get(part)
    return f"{start}{text}{ANSI_RESET}" if start else text


# Colours one textual presence or visibility status
def colorize_status(status_text):
    status = (status_text or "").strip().lower()
    if status in ("active", "online", "available", "public", "unblocked", "yes"):
        key = "status_online"
    elif status in ("inactive", "offline", "invisible", "private", "blocked", "no"):
        key = "status_offline"
    else:
        key = "status_other"
    return colorize(key, status_text)


# Splits a recognized output label from its value without backtracking
def _split_output_label(value, labels):
    body = value.rstrip("\n")
    cursor = len(body) - len(body.lstrip())
    if body[cursor:cursor + 1] == "*":
        cursor += 1
        cursor += len(body[cursor:]) - len(body[cursor:].lstrip())
    for label in labels:
        if not body.startswith(label, cursor):
            continue
        value_start = cursor + len(label)
        value_start += len(body[value_start:]) - len(body[value_start:].lstrip())
        if value_start == cursor + len(label):
            return None
        return body[:value_start], body[value_start:]
    return None


# Applies a block style while preserving internal highlights
def _apply_style_nested(line, style_name):
    start_style = _COLOR_STYLES.get(style_name)
    if not start_style:
        return line
    line = f"{start_style}{line}{ANSI_RESET}"
    line = line.replace(ANSI_RESET, f"{ANSI_RESET}{start_style}")
    if line.endswith(f"{ANSI_RESET}{start_style}"):
        line = line[:-len(start_style)]
    return line


# Applies one substitution only outside existing colour spans
def _sub_outside_color(pattern, replacement, line):
    if ANSI_RESET not in line:
        return pattern.sub(replacement, line)
    parts = []
    position = 0
    inside = False
    for match in SGR_SEQUENCE_RE.finditer(line):
        segment = line[position:match.start()]
        parts.append(segment if inside else pattern.sub(replacement, segment))
        parts.append(match.group(0))
        inside = match.group(0) != ANSI_RESET
        position = match.end()
    trailing = line[position:]
    parts.append(trailing if inside else pattern.sub(replacement, trailing))
    return "".join(parts)


# Colours one quoted noun value unless it is shaped like a file or path
def _colorize_quoted_name(match, style_name=None):
    name = match.group(2)
    if _QUOTED_FILE_LIKE_RE.search(name):
        return match.group(0)
    context_match = _QUOTED_CONTEXT_RE.search(match.string[:match.start()])
    if context_match:
        noun = context_match.group(1).casefold()
        style_name = {"user": "username", "repo": "repository"}[noun]
    if not style_name:
        return match.group(0)
    return f"{match.group(1)}{colorize(style_name, name)}{match.group(3)}"


# Applies the configured colour rules to one output line
def _colorize_line(line):
    lowered = line.lower()
    notification_match = _NOTIFICATION_SUMMARY_STATE_RE.match(line)
    if notification_match:
        prefix, state, suffix = notification_match.groups()
        return f"{prefix}{colorize('boolean_true' if state == 'On' else 'boolean_false', state)}{suffix}"
    doctor_match = _DOCTOR_MARK_RE.match(line)
    if doctor_match:
        return colorize(_DOCTOR_MARK_STYLES[doctor_match.group(1)], doctor_match.group(0)) + line[doctor_match.end():]
    repository_list_match = _REPOSITORY_LIST_RE.match(line)
    if repository_list_match:
        suffix = repository_list_match.group(3) or ""
        return f"{repository_list_match.group(1)}{colorize('repository', repository_list_match.group(2))}{suffix}"
    linked_list_match = _LINKED_LIST_ITEM_RE.match(line)
    if linked_list_match:
        item = linked_list_match.group(2)
        url_parts = [part for part in urlsplit(linked_list_match.group(4)).path.split("/") if part]
        item_style = "repository" if "/" in item or len(url_parts) >= 2 else "username"
        return f"{linked_list_match.group(1)}{colorize(item_style, item)}{linked_list_match.group(3)}{colorize('url', linked_list_match.group(4))}{linked_list_match.group(5)}"
    user_list_match = _USER_LIST_RE.match(line)
    if user_list_match:
        return f"{user_list_match.group(1)}{colorize('username', user_list_match.group(2))}"
    labeled_value = _split_output_label(line, ("Timestamp:", "Liveness check, timestamp:"))
    if labeled_value:
        label, rest = labeled_value
        colored = f"{colorize('timestamp_label', label)}{colorize('timestamp', rest)}"
        return colored + ("\n" if line.endswith("\n") else "")
    labeled_value = _split_output_label(line, ("Public profile:",))
    if labeled_value:
        label, status = labeled_value
        status_style = "status_online" if status.strip().casefold() == "yes" else "status_offline"
        colored = f"{label}{colorize(status_style, status)}"
        return colored + ("\n" if line.endswith("\n") else "")
    labeled_value = _split_output_label(line, ("Blocked by the user:",))
    if labeled_value:
        label, status = labeled_value
        normalized_status = status.strip().casefold()
        status_style = "status_offline" if normalized_status == "yes" else "status_online" if normalized_status == "no" else "status_other"
        colored = f"{label}{colorize(status_style, status)}"
        return colored + ("\n" if line.endswith("\n") else "")
    if " URL:" in line or _split_output_label(line, ("URL:",)):
        return _sub_outside_color(_URL_RE, lambda match: colorize("url", match.group(0)), line)
    for labels, style_name in _LABEL_STYLES:
        labeled_value = _split_output_label(line, labels)
        if labeled_value:
            label, rest = labeled_value
            colored = f"{label}{colorize(style_name, rest)}"
            return colored + ("\n" if line.endswith("\n") else "")
    line = _sub_outside_color(_USER_TAG_RE, lambda match: f"{match.group(1)}{match.group(2)}{colorize('username', match.group(3))}", line)
    line = _sub_outside_color(_FROM_TO_COUNT_RE, lambda match: f"{match.group(1)}{colorize('count_up' if int(match.group(4)) >= int(match.group(2)) else 'count_down', match.group(2))}{match.group(3)}{colorize('count_up' if int(match.group(4)) >= int(match.group(2)) else 'count_down', match.group(4))}", line)
    line = _sub_outside_color(_DIFF_COUNT_UP_RE, lambda match: colorize("count_up", match.group(0)), line)
    line = _sub_outside_color(_DIFF_COUNT_DOWN_RE, lambda match: colorize("count_down", match.group(0)), line)
    line = _sub_outside_color(_DURATION_RE, lambda match: colorize("duration", match.group(0)), line)
    line = _sub_outside_color(_SHORT_RANGE_DATE_RE, lambda match: colorize("date_range", match.group(0)), line)
    line = _sub_outside_color(_DATE_RANGE_RE, lambda match: colorize("date_range", match.group(0)), line)
    line = _sub_outside_color(_HOUR_RANGE_RE, lambda match: colorize("date_range", match.group(0)), line)
    line = _sub_outside_color(_LONG_DATE_RE, lambda match: colorize("date", match.group(0)), line)
    line = _sub_outside_color(_TIME_ONLY_RE, lambda match: colorize("date", match.group(0)), line)
    line = _sub_outside_color(_URL_RE, lambda match: colorize("url", match.group(0)), line)
    line = _sub_outside_color(_PROFILE_VISIBILITY_CHANGE_RE, lambda match: f"{match.group(1)}{match.group(2)}{colorize_status(match.group(3))}{match.group(4)}", line)
    line = _sub_outside_color(_BLOCK_CHANGE_RE, lambda match: colorize_status(match.group(0)), line)
    line = _sub_outside_color(_REPOSITORY_PUBLIC_RE, lambda match: colorize_status(match.group(0)), line)
    if not line.lstrip().startswith("'"):
        line = _sub_outside_color(_QUOTED_CONTENT_RE, lambda match: _colorize_quoted_name(match), line)
    line = _sub_outside_color(_BOOLEAN_TRUE_RE, lambda match: colorize("boolean_true", match.group(0)), line)
    line = _sub_outside_color(_BOOLEAN_FALSE_RE, lambda match: colorize("boolean_false", match.group(0)), line)
    is_debug_line = bool(_DEBUG_LINE_RE.match(lowered))
    if lowered.startswith("to fix:"):
        line = _apply_style_nested(line, "info")
    elif not is_debug_line and _ERROR_LINE_RE.match(lowered):
        line = _apply_style_nested(line, "error")
    elif _WARNING_LINE_RE.match(lowered):
        line = _apply_style_nested(line, "warning")
    elif "* signal" in lowered and "received" in lowered:
        line = _apply_style_nested(line, "signal")
    elif "sending email" in lowered:
        line = _apply_style_nested(line, "email")
    elif "sending webhook" in lowered:
        line = _apply_style_nested(line, "webhook")
    elif "* info:" in lowered:
        line = _apply_style_nested(line, "info")
    return line


# Applies colour rules to multi-line text while preserving line breaks
def apply_color_to_text(text):
    if not COLOR_ENABLED or not isinstance(text, str):
        return text
    parts = []
    for chunk in text.splitlines(keepends=True):
        if chunk.endswith(("\n", "\r")):
            stripped = chunk.rstrip("\r\n")
            newline = chunk[len(stripped):]
            parts.append(_colorize_line(stripped) + newline)
        else:
            parts.append(_colorize_line(chunk))
    return "".join(parts)


# Writes the startup name line by line with a separately styled version line
def _write_startup_banner(destination):
    destination.write("\n".join(colorize("header", line) if line else line for line in STARTUP_BANNER.splitlines()) + "\n")
    destination.write(colorize("info", f"{'':21}v{VERSION}") + "\n\n")


# Prints the startup banner through a sanitize-only terminal stream
def print_startup_banner():
    _write_startup_banner(terminal_surface_stream(sys.stdout))


# Returns the real terminal behind any number of sanitizing wrappers
def unwrap_terminal_stream(stream):
    while isinstance(stream, TerminalStream):
        stream = stream.terminal
    return stream


# Sanitizes and colours stdout before logging policy is resolved
class TerminalStream(object):
    # Stores the wrapped terminal stream
    def __init__(self, stream, color_output=True):
        self.terminal = stream
        self.color_output = color_output

    # Writes one sanitized and coloured message
    def write(self, message):
        safe_message = sanitize_terminal_text(message)
        self.terminal.write(apply_color_to_text(safe_message) if self.color_output else safe_message)
        self.terminal.flush()

    # Writes one terminal-only message
    def terminal_only(self, message):
        self.write(message)

    # Discards log-only output while logging is disabled
    def log_only(self, message):
        return

    # Flushes the wrapped terminal
    def flush(self):
        self.terminal.flush()

    # Forwards other stream attributes
    def __getattr__(self, name):
        return getattr(self.terminal, name)


# Returns a sanitize-only stream for surfaces that apply explicit semantic styles
def terminal_surface_stream(stream):
    if isinstance(stream, TerminalStream) and not stream.color_output:
        return stream
    while isinstance(stream, (Logger, TerminalStream)):
        stream = stream.terminal
    return TerminalStream(stream, color_output=False)


# Logger class to output messages to stdout and log file
class Logger(object):
    # Opens one line-buffered UTF-8 log while preserving the real terminal stream
    def __init__(self, filename):
        self.terminal = unwrap_terminal_stream(sys.stdout)
        debug_print("Opening output log for append", path=filename)
        try:
            self.logfile = open(filename, "a", buffering=1, encoding="utf-8")
        except Exception as exc:
            debug_print("Opening output log", path=filename, outcome="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        debug_print("Output log opened", path=filename)

    # Writes sanitized output to both the terminal and log
    def write(self, message):
        safe_message = sanitize_terminal_text(sanitize_error_text(message))
        self.logfile.write(normalize_log_separators(ANSI_ESCAPE_RE.sub("", safe_message).expandtabs(8)))
        terminal_message = truncate_string_per_line(safe_message, TRUNCATE_CHARS) if TRUNCATE_CHARS else safe_message
        self.terminal.write(apply_color_to_text(terminal_message))
        self.terminal.flush()
        self.logfile.flush()

    # Flushes both destinations through their line-buffered writes
    def flush(self):
        self.terminal.flush()
        self.logfile.flush()

    # Writes sanitized output only to the terminal
    def terminal_only(self, message):
        safe_message = sanitize_terminal_text(sanitize_error_text(message))
        terminal_message = truncate_string_per_line(safe_message, TRUNCATE_CHARS) if TRUNCATE_CHARS else safe_message
        self.terminal.write(apply_color_to_text(terminal_message))
        self.terminal.flush()

    # Writes sanitized normalized output only to the log
    def log_only(self, message):
        safe_message = sanitize_terminal_text(sanitize_error_text(message))
        self.logfile.write(normalize_log_separators(ANSI_ESCAPE_RE.sub("", safe_message).expandtabs(8)))
        self.logfile.flush()


# Signal handler when user presses Ctrl+C
def signal_handler(sig, frame):
    sys.stdout = stdout_bck
    print('\n* You pressed Ctrl+C, tool is terminated.')
    sys.exit(0)


# Silences the repeated certificate warning once verification is off, so the choice is reported by the summary and the doctor instead of on every request
def apply_tls_verification_setting():
    if not VERIFY_SSL:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Checks internet connectivity using the effective runtime URL and timeout
def check_internet(url=None, timeout=None):
    selected_url = CHECK_INTERNET_URL if url is None else url
    selected_timeout = CHECK_INTERNET_TIMEOUT if timeout is None else timeout
    try:
        debug_http_request("GET", selected_url, "startup connectivity", selected_timeout)
        response = req.get(selected_url, timeout=selected_timeout, verify=VERIFY_SSL)
        debug_http_response("GET", selected_url, "startup connectivity", getattr(response, "status_code", "unknown"))
        return True
    except req.RequestException as e:
        debug_swallowed_exception("Startup connectivity request", e)
        print_recovery_advice(classify_recovery_error(e, "network"))
        return False


# Clears the terminal screen
def clear_screen(enabled=True):
    if not enabled:
        return
    try:
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
    except Exception as exc:
        debug_swallowed_exception("Terminal screen clear", exc)
        print("* Cannot clear the screen contents")


# Converts absolute value of seconds to human readable format
def display_time(seconds, granularity=2):
    intervals = (
        ('years', 31556952),  # approximation
        ('months', 2629746),  # approximation
        ('weeks', 604800),    # 60 * 60 * 24 * 7
        ('days', 86400),      # 60 * 60 * 24
        ('hours', 3600),      # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
    )
    result = []

    if seconds > 0:
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append(f"{value} {name}")
        return ', '.join(result[:granularity])
    else:
        return '0 seconds'


# Calculates time span between two timestamps, accepts timestamp integers, floats and datetime objects
def calculate_timespan(timestamp1, timestamp2, show_weeks=True, show_hours=True, show_minutes=True, show_seconds=True, granularity=3):
    result = []
    intervals = ['years', 'months', 'weeks', 'days', 'hours', 'minutes', 'seconds']
    ts1 = timestamp1
    ts2 = timestamp2

    if isinstance(timestamp1, str):
        try:
            timestamp1 = isoparse(timestamp1)
        except Exception as exc:
            debug_swallowed_exception("First timespan timestamp parsing", exc)
            return ""

    if isinstance(timestamp1, int):
        dt1 = datetime.fromtimestamp(int(ts1), tz=timezone.utc)
    elif isinstance(timestamp1, float):
        ts1 = int(round(ts1))
        dt1 = datetime.fromtimestamp(ts1, tz=timezone.utc)
    elif isinstance(timestamp1, datetime):
        dt1 = timestamp1
        if dt1.tzinfo is None:
            dt1 = pytz.utc.localize(dt1)
        else:
            dt1 = dt1.astimezone(pytz.utc)
        ts1 = int(round(dt1.timestamp()))
    else:
        return ""

    if isinstance(timestamp2, str):
        try:
            timestamp2 = isoparse(timestamp2)
        except Exception as exc:
            debug_swallowed_exception("Second timespan timestamp parsing", exc)
            return ""

    if isinstance(timestamp2, int):
        dt2 = datetime.fromtimestamp(int(ts2), tz=timezone.utc)
    elif isinstance(timestamp2, float):
        ts2 = int(round(ts2))
        dt2 = datetime.fromtimestamp(ts2, tz=timezone.utc)
    elif isinstance(timestamp2, datetime):
        dt2 = timestamp2
        if dt2.tzinfo is None:
            dt2 = pytz.utc.localize(dt2)
        else:
            dt2 = dt2.astimezone(pytz.utc)
        ts2 = int(round(dt2.timestamp()))
    else:
        return ""

    if ts1 >= ts2:
        ts_diff = ts1 - ts2
    else:
        ts_diff = ts2 - ts1
        dt1, dt2 = dt2, dt1

    if ts_diff > 0:
        date_diff = relativedelta.relativedelta(dt1, dt2)
        years = date_diff.years
        months = date_diff.months
        days_total = date_diff.days

        if show_weeks:
            weeks = days_total // 7
            days = days_total % 7
        else:
            weeks = 0
            days = days_total

        hours = date_diff.hours if show_hours or ts_diff <= 86400 else 0
        minutes = date_diff.minutes if show_minutes or ts_diff <= 3600 else 0
        seconds = date_diff.seconds if show_seconds or ts_diff <= 60 else 0

        date_list = [years, months, weeks, days, hours, minutes, seconds]

        for index, interval in enumerate(date_list):
            if interval > 0:
                name = intervals[index]
                if interval == 1:
                    name = name.rstrip('s')
                result.append(f"{interval} {name}")

        return ', '.join(result[:granularity])
    else:
        return '0 seconds'


# Sanitizes HTML content, preserving safe tags while removing dangerous ones
def sanitize_and_preserve_html(text, convert_line_breaks=True, repo_url=None):
    if not text:
        return ""

    safe_tags = {
        'details': ['open'],
        'summary': [],
        'ul': [],
        'ol': [],
        'li': [],
        'a': ['href', 'title'],
        'code': [],
        'pre': [],
        'p': [],
        'br': [],
        'strong': [],
        'b': [],
        'em': [],
        'i': [],
        's': [],
        'strike': [],
        'del': [],
        'img': ['src', 'alt', 'title'],
        'blockquote': [],
        'hr': [],
    }

    code_blocks = []
    code_block_pattern = r'```([\s\S]*?)```'
    code_block_counter = 0

    def replace_code_block(match):
        nonlocal code_block_counter
        code_content = match.group(1)
        placeholder = f"__CODE_BLOCK_{code_block_counter}__"
        code_blocks.append(('<pre><code>' + html.escape(code_content) + '</code></pre>', placeholder))
        code_block_counter += 1
        return placeholder

    text = re.sub(code_block_pattern, replace_code_block, text)

    # Pattern to match HTML tags including multiline (use [\s\S]*? to match any char including newlines)
    tag_pattern = r'<(/)?([a-z][a-z0-9]*)([\s\S]*?)>'

    def sanitize_tag(match):
        closing = match.group(1) == '/'
        tag_name = match.group(2).lower()
        attrs_str = match.group(3) if match.group(3) else ''

        if closing:
            return f'</{tag_name}>' if tag_name in safe_tags else ''

        if tag_name not in safe_tags:
            return ''

        allowed_attrs = safe_tags[tag_name]
        if not allowed_attrs and attrs_str:
            return f'<{tag_name}>'

        attr_pattern = r'(\w+)=["\']([^"\']*)["\']'
        safe_attrs = []
        for attr_match in re.finditer(attr_pattern, attrs_str):
            attr_name = attr_match.group(1).lower()
            attr_value = attr_match.group(2)

            if attr_name in allowed_attrs:
                if attr_name == 'href' or attr_name == 'src':
                    if attr_value.startswith(('http://', 'https://', 'mailto:', '#')):
                        safe_attrs.append(f'{attr_name}="{html.escape(attr_value)}"')
                else:
                    safe_attrs.append(f'{attr_name}="{html.escape(attr_value)}"')

        if safe_attrs:
            return f'<{tag_name} {" ".join(safe_attrs)}>'
        else:
            return f'<{tag_name}>'

    sanitized = re.sub(tag_pattern, sanitize_tag, text, flags=re.IGNORECASE)

    temp_markers = []
    for idx, (code_html, placeholder) in enumerate(code_blocks):
        temp_marker = f"__TEMP_CODE_{idx}__"
        temp_markers.append((temp_marker, code_html))
        sanitized = sanitized.replace(placeholder, temp_marker)

    protected_tags = []
    tag_counter = 0

    valid_tag_pattern = r'</?[a-z][a-z0-9]*(?:\s+[^>]*)?>'

    def protect_tag(match):
        nonlocal tag_counter
        protected_tags.append(match.group(0))
        result = f"__PROTECTED_TAG_{tag_counter}__"
        tag_counter += 1
        return result

    sanitized = re.sub(valid_tag_pattern, protect_tag, sanitized, flags=re.IGNORECASE)

    sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')

    for idx, tag in enumerate(protected_tags):
        sanitized = sanitized.replace(f"__PROTECTED_TAG_{idx}__", tag)

    for temp_marker, code_html in temp_markers:
        sanitized = sanitized.replace(temp_marker, code_html)

    if convert_line_breaks:
        lines = sanitized.split('\n')
        result_lines = []
        prev_was_block = False
        prev_was_empty = False

        for line in lines:
            stripped = line.strip()
            is_block = bool(re.search(r'<(details|summary|ul|ol|li|pre|blockquote|hr|p)[\s>]', stripped, re.IGNORECASE))

            if not stripped:
                if not prev_was_empty and not prev_was_block:
                    result_lines.append('<br>')
                prev_was_empty = True
                prev_was_block = False
            else:
                if is_block:
                    result_lines.append(line)
                    prev_was_block = True
                    prev_was_empty = False
                else:
                    if not prev_was_block and result_lines and not prev_was_empty:
                        result_lines.append('<br>')
                    result_lines.append(line)
                    prev_was_block = False
                    prev_was_empty = False

        sanitized = ''.join(result_lines)

    return sanitized


# Sanitizes a single HTML tag
def sanitize_single_html_tag(html_tag):
    safe_tags = {
        'details': ['open'],
        'summary': [],
        'ul': [],
        'ol': [],
        'li': [],
        'a': ['href', 'title'],
        'code': [],
        'pre': [],
        'p': [],
        'br': [],
        'strong': [],
        'b': [],
        'em': [],
        'i': [],
        's': [],
        'strike': [],
        'del': [],
        'img': ['src', 'alt', 'title'],
        'blockquote': [],
        'hr': [],
    }

    # Pattern to match HTML tags including multiline (use [\s\S]*? to match any char including newlines)
    tag_pattern = r'<(/)?([a-z][a-z0-9]*)([\s\S]*?)>'
    match = re.match(tag_pattern, html_tag, re.IGNORECASE)
    if not match:
        return html.escape(html_tag)

    closing = match.group(1) == '/'
    tag_name = match.group(2).lower()
    attrs_str = match.group(3) if match.group(3) else ''

    if closing:
        return f'</{tag_name}>' if tag_name in safe_tags else ''

    if tag_name not in safe_tags:
        return ''

    allowed_attrs = safe_tags[tag_name]
    if not allowed_attrs and attrs_str:
        return f'<{tag_name}>'

    # Extract attributes, handling whitespace/newlines before attribute names
    attr_pattern = r'\s*(\w+)=["\']([^"\']*)["\']'
    safe_attrs = []
    for attr_match in re.finditer(attr_pattern, attrs_str):
        attr_name = attr_match.group(1).lower()
        attr_value = attr_match.group(2)

        if attr_name in allowed_attrs:
            if attr_name == 'href' or attr_name == 'src':
                if attr_value.startswith(('http://', 'https://', 'mailto:', '#')):
                    safe_attrs.append(f'{attr_name}="{html.escape(attr_value)}"')
            else:
                safe_attrs.append(f'{attr_name}="{html.escape(attr_value)}"')

    if safe_attrs:
        return f'<{tag_name} {" ".join(safe_attrs)}>'
    else:
        return f'<{tag_name}>'


# Converts markdown text to HTML
def markdown_to_html(text, convert_line_breaks=True, repo_url=None):
    if not text:
        return ""

    # Pattern to match HTML tags (both opening and closing), including those that span multiple lines
    # Matches: <tagname...> or </tagname> with attributes that may span lines
    html_tag_pattern = r'</?[a-z][a-z0-9]*(?:[\s\S]*?)>'
    has_html = bool(re.search(html_tag_pattern, text, re.IGNORECASE))

    # Protect code blocks first
    code_blocks = []
    code_block_pattern = r'```([\s\S]*?)```'
    code_block_counter = 0

    def replace_code_block(match):
        nonlocal code_block_counter
        code_content = match.group(1)
        placeholder = f"__CODE_BLOCK_{code_block_counter}__"
        code_blocks.append(('<pre><code>' + html.escape(code_content) + '</code></pre>', placeholder))
        code_block_counter += 1
        return placeholder

    text = re.sub(code_block_pattern, replace_code_block, text)

    # If HTML is present, protect HTML tags during markdown processing, then sanitize them
    html_tags = []
    if has_html:
        html_tag_counter = 0

        def protect_html_tag(match):
            nonlocal html_tag_counter
            html_tags.append(match.group(0))
            # Use a placeholder that won't be processed by markdown (no underscores, asterisks, etc.)
            result = f"PROTECTEDHTMLTAG{html_tag_counter}PROTECTED"
            html_tag_counter += 1
            return result

        text = re.sub(html_tag_pattern, protect_html_tag, text, flags=re.IGNORECASE)

    # Protect markdown link/image patterns from HTML escaping and italic processing
    markdown_pattern_placeholders = []
    markdown_pattern_counter = 0

    def protect_markdown_pattern(match):
        nonlocal markdown_pattern_counter
        markdown_pattern_placeholders.append(match.group(0))
        result = f"__MARKDOWN_PATTERN_{markdown_pattern_counter}__"
        markdown_pattern_counter += 1
        return result

    # Protect image links, images, and links before HTML escaping
    text = re.sub(r'\[!\[([^\]]*)\]\(([^\)]+)\)\]\(([^\)]+)\)', protect_markdown_pattern, text)
    text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', protect_markdown_pattern, text)
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', protect_markdown_pattern, text)

    # Escape HTML (but code blocks, protected HTML tags, and markdown patterns are already protected)
    html_text = html.escape(text)

    # Restore code blocks
    for code_html, placeholder in code_blocks:
        html_text = html_text.replace(placeholder, code_html)

    # Process block-level elements line by line
    lines = html_text.split('\n')
    processed_lines = []
    in_list = False
    list_type = None  # 'ul' or 'ol'
    list_items = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines for now (we'll add them back later)
        if not stripped:
            if in_list:
                # Close current list
                if list_type == 'ul':
                    processed_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                else:
                    processed_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                in_list = False
                list_type = None
                list_items = []
            processed_lines.append('')
            i += 1
            continue

        # Horizontal rules (must be at least 3 dashes/asterisks)
        if re.match(r'^[-*_]{3,}$', stripped):
            processed_lines.append('<hr>')
            i += 1
            continue

        # Headers (# ## ### etc.)
        header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if header_match:
            level = len(header_match.group(1))
            header_text = header_match.group(2)
            processed_lines.append(f'<h{level}>{header_text}</h{level}>')
            i += 1
            continue

        # Blockquotes (>)
        if stripped.startswith('>'):
            quote_text = stripped[1:].strip()
            processed_lines.append(f'<blockquote>{quote_text}</blockquote>')
            i += 1
            continue

        # Lists - be careful not to match "- label:" patterns
        # Check for unordered list (- or *)
        list_match = re.match(r'^(\s*)([-*])\s+(.+)$', line)
        if list_match:
            list_content = list_match.group(3)
            # Don't treat as list if it looks like a label pattern:
            # - Ends with just a colon (with optional whitespace), OR
            # - Matches pattern like "Word:" or "Words:" followed by tabs/spaces (typical label format)
            is_label = (re.search(r':\s*$', list_content) or re.match(r'^[A-Z][a-zA-Z\s]+:\s+\S', list_content))
            if not is_label:
                if not in_list or list_type != 'ul':
                    if in_list:
                        # Close previous list
                        if list_type == 'ol':
                            processed_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                        list_items = []
                    in_list = True
                    list_type = 'ul'

                list_items.append(f'<li>{list_content}</li>')
                i += 1
                continue

        # Check for ordered list (1. 2. etc.)
        ordered_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
        if ordered_match:
            list_content = ordered_match.group(3)

            if not in_list or list_type != 'ol':
                if in_list:
                    # Close previous list
                    if list_type == 'ul':
                        processed_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                    list_items = []
                in_list = True
                list_type = 'ol'

            list_items.append(f'<li>{list_content}</li>')
            i += 1
            continue

        # Not a list item, so close any open list
        if in_list:
            if list_type == 'ul':
                processed_lines.append('<ul>' + ''.join(list_items) + '</ul>')
            else:
                processed_lines.append('<ol>' + ''.join(list_items) + '</ol>')
            in_list = False
            list_type = None
            list_items = []

        # Regular line
        processed_lines.append(line)
        i += 1

    # Close any remaining open list
    if in_list:
        if list_type == 'ul':
            processed_lines.append('<ul>' + ''.join(list_items) + '</ul>')
        else:
            processed_lines.append('<ol>' + ''.join(list_items) + '</ol>')

    html_text = '\n'.join(processed_lines)

    # Process inline elements (but skip code blocks)
    # First, restore and process protected markdown patterns
    for idx, original_pattern in enumerate(markdown_pattern_placeholders):
        placeholder = f"__MARKDOWN_PATTERN_{idx}__"
        escaped_placeholder = html.escape(placeholder)
        # Check both escaped and unescaped placeholders
        if placeholder in html_text or escaped_placeholder in html_text:
            # Process the original pattern (unescaped)
            # Image links
            image_link_match = re.match(r'\[!\[([^\]]*)\]\(([^\)]+)\)\]\(([^\)]+)\)', original_pattern)
            if image_link_match:
                alt_text = image_link_match.group(1)
                image_url = image_link_match.group(2)
                link_url = image_link_match.group(3)
                if repo_url:
                    if image_url and not image_url.startswith(('http://', 'https://', 'data:', '#')):
                        if image_url.startswith('/'):
                            image_url = repo_url.rstrip('/') + '/blob/HEAD' + image_url
                        else:
                            image_url = repo_url.rstrip('/') + '/blob/HEAD/' + image_url
                    if link_url and not link_url.startswith(('http://', 'https://', 'mailto:', '#')):
                        if link_url.startswith('/'):
                            link_url = repo_url.rstrip('/') + '/blob/HEAD' + link_url
                        else:
                            link_url = repo_url.rstrip('/') + '/blob/HEAD/' + link_url
                replacement = f'<a href="{html.escape(link_url)}"><img src="{html.escape(image_url)}" alt="{html.escape(alt_text)}"></a>'
                html_text = html_text.replace(placeholder, replacement)
                html_text = html_text.replace(escaped_placeholder, replacement)
                continue

            # Images
            image_match = re.match(r'!\[([^\]]*)\]\(([^\)]+)\)', original_pattern)
            if image_match:
                alt_text = image_match.group(1)
                image_url = image_match.group(2)
                if repo_url and image_url and not image_url.startswith(('http://', 'https://', 'data:', '#')):
                    if image_url.startswith('/'):
                        absolute_url = repo_url.rstrip('/') + '/blob/HEAD' + image_url
                    else:
                        absolute_url = repo_url.rstrip('/') + '/blob/HEAD/' + image_url
                    replacement = f'<img src="{html.escape(absolute_url)}" alt="{html.escape(alt_text)}">'
                else:
                    replacement = f'<img src="{html.escape(image_url)}" alt="{html.escape(alt_text)}">'
                html_text = html_text.replace(placeholder, replacement)
                html_text = html_text.replace(escaped_placeholder, replacement)
                continue

            # Links
            link_match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', original_pattern)
            if link_match:
                link_text = link_match.group(1)
                link_url = link_match.group(2)
                if repo_url and link_url and not link_url.startswith(('http://', 'https://', 'mailto:', '#')):
                    if link_url.startswith('/'):
                        absolute_url = repo_url.rstrip('/') + '/blob/HEAD' + link_url
                    else:
                        absolute_url = repo_url.rstrip('/') + '/blob/HEAD/' + link_url
                    replacement = f'<a href="{html.escape(absolute_url)}">{html.escape(link_text)}</a>'
                else:
                    replacement = f'<a href="{html.escape(link_url)}">{html.escape(link_text)}</a>'
                html_text = html_text.replace(placeholder, replacement)
                html_text = html_text.replace(escaped_placeholder, replacement)
                continue

    # Process remaining markdown patterns that weren't protected (shouldn't happen, but for safety)
    image_link_pattern = r'\[!\[([^\]]*)\]\(([^\)]+)\)\]\(([^\)]+)\)'

    def convert_image_link(match):
        alt_text = html.unescape(match.group(1))
        image_url = html.unescape(match.group(2))
        link_url = html.unescape(match.group(3))
        if repo_url:
            if image_url and not image_url.startswith(('http://', 'https://', 'data:', '#')):
                if image_url.startswith('/'):
                    image_url = repo_url.rstrip('/') + '/blob/HEAD' + image_url
                else:
                    image_url = repo_url.rstrip('/') + '/blob/HEAD/' + image_url
            if link_url and not link_url.startswith(('http://', 'https://', 'mailto:', '#')):
                if link_url.startswith('/'):
                    link_url = repo_url.rstrip('/') + '/blob/HEAD' + link_url
                else:
                    link_url = repo_url.rstrip('/') + '/blob/HEAD/' + link_url
        return f'<a href="{html.escape(link_url)}"><img src="{html.escape(image_url)}" alt="{html.escape(alt_text)}"></a>'
    html_text = re.sub(image_link_pattern, convert_image_link, html_text)

    # Images
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'

    def convert_image(match):
        alt_text = html.unescape(match.group(1))
        image_url = html.unescape(match.group(2))
        # Convert relative image URLs to absolute if repo_url is provided
        if repo_url and image_url and not image_url.startswith(('http://', 'https://', 'data:', '#')):
            # Use blob/HEAD/ for relative image URLs (GitHub requires branch in path)
            if image_url.startswith('/'):
                absolute_url = repo_url.rstrip('/') + '/blob/HEAD' + image_url
            else:
                absolute_url = repo_url.rstrip('/') + '/blob/HEAD/' + image_url
            return f'<img src="{html.escape(absolute_url)}" alt="{html.escape(alt_text)}">'
        return f'<img src="{html.escape(image_url)}" alt="{html.escape(alt_text)}">'
    html_text = re.sub(image_pattern, convert_image, html_text)

    # Links
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'

    def convert_link(match):
        link_text = html.unescape(match.group(1))
        link_url = html.unescape(match.group(2))
        # Convert relative links to absolute if repo_url is provided
        if repo_url and link_url and not link_url.startswith(('http://', 'https://', 'mailto:', '#')):
            # Use blob/HEAD/ for relative links (GitHub requires branch in path)
            if link_url.startswith('/'):
                absolute_url = repo_url.rstrip('/') + '/blob/HEAD' + link_url
            else:
                absolute_url = repo_url.rstrip('/') + '/blob/HEAD/' + link_url
            return f'<a href="{html.escape(absolute_url)}">{link_text}</a>'
        return f'<a href="{html.escape(link_url)}">{link_text}</a>'
    html_text = re.sub(link_pattern, convert_link, html_text)

    # Strikethrough
    html_text = re.sub(r'~~([^~]+)~~', r'<s>\1</s>', html_text)

    # Bold
    html_text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', html_text)
    html_text = re.sub(r'__([^_]+)__', r'<b>\1</b>', html_text)

    # Italic (must not be part of bold, and not inside HTML attributes)
    # Protect HTML attributes from italic processing
    attr_pattern_placeholders = []
    attr_pattern_counter = 0

    def protect_attr_pattern(match):
        nonlocal attr_pattern_counter
        attr_pattern_placeholders.append(match.group(0))
        # Use placeholder without underscores to avoid italic processing
        result = f"ATTRPATTERN{attr_pattern_counter}ATTR"
        attr_pattern_counter += 1
        return result

    # Protect URLs in HTML attributes (href="...", src="...", alt="...", title="...")
    # This prevents italic processing from affecting URLs inside HTML attributes
    html_text = re.sub(r'(href|src|alt|title)=["\']([^"\']+)["\']', protect_attr_pattern, html_text, flags=re.IGNORECASE)

    html_text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', html_text)
    # Only match italic underscores when they're clearly markdown (word boundaries or spaces/punctuation)
    html_text = re.sub(r'(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])', r'<i>\1</i>', html_text)

    # Restore protected patterns
    for idx, pattern in enumerate(attr_pattern_placeholders):
        html_text = html_text.replace(f"ATTRPATTERN{idx}ATTR", pattern)

    # Inline code (but not inside code blocks)
    html_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_text)

    # Protect URLs inside HTML attributes before converting plain URLs to links
    # This prevents convert_urls_to_links from converting URLs that are already in href/src/alt attributes
    attr_url_placeholders = []
    attr_url_counter = 0

    def protect_attr_url(match):
        nonlocal attr_url_counter
        full_match = match.group(0)
        attr_url_placeholders.append(full_match)
        result = f"__ATTR_URL_{attr_url_counter}__"
        attr_url_counter += 1
        return result

    # Match URLs inside HTML attributes (href="...", src="...", alt="...", title="...")
    attr_url_pattern = r'(href|src|alt|title)=["\'](https?://[^"\']+)["\']'
    html_text = re.sub(attr_url_pattern, protect_attr_url, html_text, flags=re.IGNORECASE)

    # Convert plain URLs to links (avoid double-converting URLs already in <a> tags)
    html_text = convert_urls_to_links(html_text)

    # Convert commit hashes to links if repo_url is provided
    if repo_url:
        html_text = convert_commit_hashes_to_links(html_text, repo_url)

    # Restore protected attribute URLs
    for idx, attr_url in enumerate(attr_url_placeholders):
        html_text = html_text.replace(f"__ATTR_URL_{idx}__", attr_url)

    # If HTML was detected, restore and sanitize the protected HTML tags BEFORE line break conversion
    # This allows the line break logic to properly detect HTML block elements
    if has_html and html_tags:
        for idx, original_html_tag in enumerate(html_tags):
            # Use the same placeholder format that was used during protection
            placeholder = f"PROTECTEDHTMLTAG{idx}PROTECTED"
            if placeholder in html_text:
                sanitized_tag = sanitize_single_html_tag(original_html_tag)
                # Only replace if sanitization returned a valid tag (not empty string)
                if sanitized_tag:
                    html_text = html_text.replace(placeholder, sanitized_tag)
                else:
                    # If tag was filtered out, escape the original tag instead
                    html_text = html_text.replace(placeholder, html.escape(original_html_tag))

    if convert_line_breaks:
        # Line-break handling that respects both text paragraphs and HTML blocks.
        # Rules:
        # - text -> blank -> text        => one <br>
        # - text -> blank -> HTML block  => <br><br> (extra space before big block like <details>)
        # - HTML -> blank -> text        => one <br>
        # - HTML -> blank -> HTML block  => no extra <br>
        lines = html_text.split('\n')
        result_lines = []
        prev_type = None  # 'text' or 'html'
        prev_html_tag = None  # last HTML tag name (e.g., 'ul', 'details', 'a')
        prev_html_had_image = False  # whether previous HTML line contained an <img>
        pending_blank = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                # Defer decision until we see what comes after the blank(s)
                pending_blank = True
                continue

            is_html = stripped.startswith('<')

            if is_html:
                # Detect tag name for smarter spacing rules
                tag_match = re.match(r'<\s*/?\s*([a-zA-Z0-9]+)', stripped)
                tag_name = tag_match.group(1).lower() if tag_match else None

                if prev_type == 'text' and pending_blank:
                    # Text paragraph followed by blank line then HTML block
                    # Only use double break before certain heavy blocks like <details>
                    if tag_name == 'details':
                        result_lines.append('<br><br>')
                    else:
                        result_lines.append('<br>')

                # Always keep HTML lines as-is
                result_lines.append(line)
                prev_type = 'html'
                prev_html_tag = tag_name
                prev_html_had_image = ('<img' in stripped.lower())
                pending_blank = False
            else:
                # Text line (may contain inline HTML like <b>, <a>, etc.)
                if prev_type == 'text':
                    # Consecutive text paragraphs
                    if pending_blank:
                        # Blank line between text paragraphs -> full empty line
                        result_lines.append('<br><br>')
                    else:
                        result_lines.append('<br>')
                elif prev_type == 'html' and pending_blank:
                    # HTML block followed by blank line then text
                    # Avoid extra break after lists (<ul>/<ol>) which already have spacing
                    if prev_html_tag not in ('ul', 'ol'):
                        # If previous HTML line contained an image (e.g., badge), use double break
                        if prev_html_had_image:
                            result_lines.append('<br><br>')
                        else:
                            result_lines.append('<br>')
                result_lines.append(line)
                prev_type = 'text'
                pending_blank = False

        html_text = ''.join(result_lines)

    html_text = convert_github_mentions_to_links(html_text)

    return html_text


# Converts URLs in HTML-escaped text to clickable links
def convert_urls_to_links(text):
    if not text:
        return text

    bracket_pattern = r'\[\s*(https?://[^\s\]]+)\s*\]'
    text = re.sub(bracket_pattern, r'<a href="\1">\1</a>', text)

    # Match URLs but not those inside HTML attributes (href="...", src="...", etc.)
    # This pattern avoids matching URLs that are already inside quotes after = (attribute values)
    url_pattern = r'(?<!href=")(?<!src=")(?<!alt=")(?<!title=")(?<!">)(?<!<a href=")(?<!<img src=")(https?://[^\s<>"]+)'
    text = re.sub(url_pattern, r'<a href="\1">\1</a>', text)

    return text


# Converts GitHub user mentions outside existing links and code to profile links
def convert_github_mentions_to_links(text, github_html_url=None):
    if not text:
        return text

    base_url = (github_html_url or GITHUB_HTML_URL).rstrip('/')
    if not base_url:
        return text

    mention_pattern = r'(?<![a-zA-Z0-9_@])@([a-zA-Z0-9-]{1,39})(?![a-zA-Z0-9_-])'
    parts = re.split(r'(<[^>]+>)', text)
    protected_depth = 0

    for idx, part in enumerate(parts):
        if part.startswith('<'):
            protected_tag = re.match(r'<\s*(/?)\s*(a|code|pre)\b', part, re.IGNORECASE)
            if protected_tag:
                if protected_tag.group(1):
                    protected_depth = max(0, protected_depth - 1)
                elif not part.rstrip().endswith('/>'):
                    protected_depth += 1
            continue

        if protected_depth:
            continue

        def replace_mention(match):
            username = match.group(1)
            if username.startswith('-') or username.endswith('-') or '--' in username:
                return match.group(0)
            profile_url = f"{base_url}/{username}"
            return f'<a href="{html.escape(profile_url, quote=True)}">@{username}</a>'

        parts[idx] = re.sub(mention_pattern, replace_mention, part)

    return ''.join(parts)


# Converts commit hashes (7-40 hex chars) to clickable GitHub links
def convert_commit_hashes_to_links(text, repo_url=None):
    if not text or not repo_url:
        return text

    # Regex for commit hashes: 7 to 40 hex characters, exclude purely numeric strings of length 7-15 which are likely Event IDs
    commit_pattern = r'(?<![a-zA-Z0-9])(?![0-9]{7,15}(?![a-zA-Z0-9]))([a-f0-9]{7,40})(?![a-zA-Z0-9])'

    def replace_hash(match):
        commit_hash = match.group(1)
        # Construct commit URL
        commit_url = f"{repo_url.rstrip('/')}/commit/{commit_hash}"
        return f'<a href="{commit_url}">{commit_hash}</a>'

    # To avoid matching hashes inside tags (like <a href="...">hash</a>) or attributes, we split by tags and only process the non-tag parts
    parts = re.split(r'(<[^>]+>)', text)
    in_anchor = False
    for i in range(len(parts)):
        part = parts[i]
        if part.startswith('<'):
            # Check if this tag opens or closes an anchor
            tag_content = part[1:].lower()
            if tag_content.startswith('a'):
                in_anchor = True
            elif tag_content.startswith('/a'):
                in_anchor = False
        else:
            # If it's not a tag and we're not inside an anchor, process it
            if not in_anchor:
                parts[i] = re.sub(commit_pattern, replace_hash, part)

    return ''.join(parts)


# Converts issue/PR list items to HTML with clickable titles
def convert_issue_pr_items_to_html(text, already_escaped=False):
    if not text:
        return text

    pattern = r'(- )?#(\d+)\s+([^(]+?)\s+\(([^)]+)\)\s+(?:\[\s*)?(https?://[^\s\]]+)(?:\s*\])?'

    def replace_item(match):
        prefix = match.group(1) or ""
        number = match.group(2)
        title = match.group(3).strip()
        user = match.group(4)
        url = match.group(5)

        if already_escaped:
            escaped_title = title
            escaped_user = user
            escaped_url = url
        else:
            escaped_title = html.escape(title)
            escaped_user = html.escape(user)
            escaped_url = html.escape(url)

        return f'{prefix}<a href="{escaped_url}"><b>#{number} {escaped_title}</b></a> ({escaped_user})'

    return re.sub(pattern, replace_item, text)


# Converts plain text to HTML, preserving line breaks and formatting
def text_to_html(text, preserve_newlines=True, convert_urls=True, convert_issue_pr=True, repo_url=None):
    if not text:
        return ""

    html_text = html.escape(text)

    if convert_issue_pr:
        html_text = convert_issue_pr_items_to_html(html_text, already_escaped=True)

    if convert_urls:
        html_text = convert_urls_to_links(html_text)

    if repo_url:
        html_text = convert_commit_hashes_to_links(html_text, repo_url)

    html_text = convert_github_mentions_to_links(html_text)

    if preserve_newlines:
        html_text = html_text.replace('\n', '<br>')

    return html_text


# Formats email body text to HTML
def format_email_body_html(body_text, bold_keys=None, repo_url=None):
    if not body_text:
        return ""

    html_text = text_to_html(body_text, preserve_newlines=True, repo_url=repo_url)

    if bold_keys:
        for key in bold_keys:
            if key:
                escaped_key = html.escape(key)
                html_text = re.sub(
                    re.escape(escaped_key),
                    lambda m: f'<b>{m.group(0)}</b>',
                    html_text,
                    flags=re.IGNORECASE
                )

    return html_text


# Converts event text to HTML, handling markdown in specific fields
def event_text_to_html(event_text, event_type=None, event_payload=None):
    if not event_text:
        return ""

    # Extract repo URL from event text if available
    repo_url = None
    for line in event_text.split('\n'):
        if 'Repo URL:' in line:
            # Extract URL from line like "Repo URL: https://github.com/user/repo"
            match = re.search(r'Repo URL:\s*(https?://[^\s]+)', line)
            if match:
                repo_url = match.group(1)
                break

    lines = event_text.split('\n')
    html_lines = []

    commit_message_style = (
        "background-color: #f8f8f8; padding: 3px 3px; border-radius: 4px; font-size: 1.00em;"
    )

    def style_commit_html(message_html):
        if not message_html:
            return ""
        return f'<span style="{commit_message_style}">{message_html}</span>'

    def remove_closing_quote(text):
        idx = text.rfind("'")
        if idx == -1:
            return text
        return text[:idx] + text[idx + 1:]

    def extract_quoted_message(start_index, initial_fragment):
        fragments = []

        fragment = initial_fragment
        if fragment:
            fragment_stripped = fragment.rstrip()
            if fragment_stripped.endswith("'"):
                fragments.append(remove_closing_quote(fragment))
                return '\n'.join(fragments), start_index + 1
            fragments.append(fragment)
        idx = start_index + 1

        while idx < len(lines):
            current_line = lines[idx]
            stripped = current_line.strip()
            if stripped.endswith("'") and (stripped == "'" or not stripped.startswith("'")):
                fragments.append(remove_closing_quote(current_line))
                idx += 1
                break
            else:
                fragments.append(current_line)
                idx += 1

        return '\n'.join(fragments), idx

    i = 0
    while i < len(lines):
        line = lines[i]

        if "Release notes:" in line:
            if event_payload and event_payload.get("release"):
                release_body = event_payload["release"].get("body", "")
                if release_body:
                    release_html = markdown_to_html(release_body, convert_line_breaks=True, repo_url=repo_url)
                    prefix = line.split("Release notes:")[0].replace('\t', ' ')
                    html_lines.append(f"{html.escape(prefix)}<b>Release notes:</b><br><br>'{release_html}'")
                    i += 1
                    # Skip all lines until we find the closing quote (end of release notes in plaintext)
                    while i < len(lines):
                        if lines[i].strip().endswith("'") and not lines[i].strip().startswith("'"):
                            i += 1
                            break
                        i += 1
                    continue

        if "Commit message:" in line or "- Commit message:" in line or "Commit full message:" in line or "- Commit full message:" in line:
            if ("Commit full message:" in line or "- Commit full message:" in line) and "'" not in line:
                prefix = line.replace('\t', ' ').strip()
                is_dash_variant = "- Commit full message:" in prefix
                if is_dash_variant:
                    prefix_clean = prefix.split("- Commit full message:")[0]
                    label_html = "<b>- Commit full message:</b>"
                else:
                    prefix_clean = prefix.split("Commit full message:")[0]
                    label_html = "<b>Commit full message:</b>"
                i += 1

                while i < len(lines) and not lines[i].strip():
                    i += 1

                if i < len(lines) and "'" in lines[i]:
                    message_line = lines[i]
                    parts = message_line.split("'", 1)
                    if len(parts) > 1:
                        message_text, next_index = extract_quoted_message(i, parts[1])
                        message_html = markdown_to_html(message_text, convert_line_breaks=True, repo_url=repo_url)
                        styled_message = style_commit_html(message_html)
                        html_lines.append(f"{html.escape(prefix_clean)}{label_html}<br><br>'{styled_message}'")
                        i = next_index
                        continue
            elif "'" in line:
                parts = line.split("'", 1)
                if len(parts) > 1:
                    prefix = parts[0].replace('\t', ' ')
                    message_text, next_index = extract_quoted_message(i, parts[1])
                    message_html = markdown_to_html(message_text, convert_line_breaks=True, repo_url=repo_url)
                    styled_message = style_commit_html(message_html)

                    if "- Commit full message:" in prefix:
                        prefix_clean = prefix.split("- Commit full message:")[0]
                        html_lines.append(f"{html.escape(prefix_clean)}<b>- Commit full message:</b><br><br>'{styled_message}'")
                    elif "Commit full message:" in prefix:
                        prefix_clean = prefix.split("Commit full message:")[0]
                        html_lines.append(f"{html.escape(prefix_clean)}<b>Commit full message:</b><br><br>'{styled_message}'")
                    elif "- Commit message:" in prefix:
                        prefix_clean = prefix.split("- Commit message:")[0]
                        html_lines.append(f"{html.escape(prefix_clean)}<b>- Commit message:</b> {styled_message}")
                    else:
                        prefix_clean = prefix.split("Commit message:")[0]
                        html_lines.append(f"{html.escape(prefix_clean)}<b>Commit message:</b> {styled_message}")
                    i = next_index
                    continue
        if "PR description:" in line:
            # Case 1: label and description on the same line
            if "'" in line:
                parts = line.split("'", 1)
                if len(parts) > 1:
                    prefix = parts[0].replace('\t', ' ')
                    description = parts[1]
                    if description.endswith("'"):
                        description = description.rstrip("'")
                        description_html = markdown_to_html(description, convert_line_breaks=True, repo_url=repo_url)
                        html_lines.append(f"{html.escape(prefix)}<b>PR description:</b> '{description_html}'")
                    else:
                        description_lines = [description]
                        i += 1
                        while i < len(lines) and not lines[i].strip().endswith("'"):
                            description_lines.append(lines[i])
                            i += 1
                        if i < len(lines):
                            description_lines.append(lines[i].rstrip("'"))
                        description = '\n'.join(description_lines)
                        description_html = markdown_to_html(description, convert_line_breaks=True, repo_url=repo_url)
                        html_lines.append(f"{html.escape(prefix)}<b>PR description:</b> '{description_html}'")
                    i += 1
                    continue
            else:
                # Case 2: label on its own line, description in following quoted block
                prefix = line.split("PR description:")[0].replace('\t', ' ')
                i += 1
                # Skip empty lines
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines) and "'" in lines[i]:
                    first = lines[i]
                    parts = first.split("'", 1)
                    if len(parts) > 1:
                        description_text, next_index = extract_quoted_message(i, parts[1])
                        description_html = markdown_to_html(description_text, convert_line_breaks=True, repo_url=repo_url)
                        html_lines.append(f"{html.escape(prefix)}<b>PR description:</b><br><br>'{description_html}'")
                        i = next_index
                        continue

        # Handle body-like blocks, bolding the label and interpreting markdown inside the quoted body
        body_keyword_matched = False

        # Special handling for "Previous comment:" which has an intermediate "↳ In reply to..." line
        if "Previous comment:" in line:
            line_stripped = line.strip()
            if line_stripped == "Previous comment:" or line_stripped.startswith("Previous comment:"):
                prefix = line.split("Previous comment:")[0].replace('\t', ' ')
                i += 1

                # Skip blank lines
                while i < len(lines) and not lines[i].strip():
                    i += 1

                # Collect all non-empty lines until we hit the quoted body
                reply_lines = []
                while i < len(lines) and not (lines[i].strip().startswith("'") or (lines[i] and lines[i][0] in [' ', '\t'] and "'" in lines[i])):
                    if lines[i].strip():  # Only collect non-empty lines
                        reply_lines.append(lines[i].strip())
                    i += 1

                # Skip blank lines before body
                while i < len(lines) and not lines[i].strip():
                    i += 1

                # Now look for the quoted body
                if i < len(lines) and "'" in lines[i]:
                    first = lines[i]
                    parts = first.split("'", 1)
                    if len(parts) > 1:
                        body_text, next_index = extract_quoted_message(i, parts[1])
                        body_html = markdown_to_html(body_text, convert_line_breaks=True, repo_url=repo_url)
                        # Build the output with reply lines if present
                        if reply_lines:
                            reply_html = "<br>".join(html.escape(rl) for rl in reply_lines)
                            html_lines.append(f"{html.escape(prefix)}<b>Previous comment:</b><br><br>{reply_html}<br><br>'{body_html}'")
                        else:
                            html_lines.append(f"{html.escape(prefix)}<b>Previous comment:</b><br><br>'{body_html}'")
                        i = next_index
                        body_keyword_matched = True

        # Handle other body keywords (Issue body, Comment body, Review body)
        if not body_keyword_matched:
            for keyword in ["Issue body:", "Comment body:", "Review body:"]:
                if keyword in line:
                    # Case 1: label and body on the same line
                    if "'" in line and line.strip().startswith(keyword):
                        parts = line.split("'", 1)
                        if len(parts) > 1:
                            prefix = parts[0].replace('\t', ' ')
                            body_content = parts[1]
                            if body_content.endswith("'"):
                                body_content = body_content.rstrip("'")
                                body_html = markdown_to_html(body_content, convert_line_breaks=True, repo_url=repo_url)
                                html_lines.append(f"{html.escape(prefix)}<b>{html.escape(keyword)}</b> '{body_html}'")
                                i += 1
                                body_keyword_matched = True
                                break

                    # Case 2: label on its own line, body in a following quoted block
                    if line.strip().startswith(keyword):
                        prefix = line.split(keyword)[0].replace('\t', ' ')
                        i += 1

                        # Skip blank lines
                        while i < len(lines) and not lines[i].strip():
                            i += 1

                        # Look for the first line that starts the quoted body
                        if i < len(lines) and "'" in lines[i]:
                            first = lines[i]
                            parts = first.split("'", 1)
                            if len(parts) > 1:
                                body_text, next_index = extract_quoted_message(i, parts[1])
                                body_html = markdown_to_html(body_text, convert_line_breaks=True, repo_url=repo_url)
                                html_lines.append(f"{html.escape(prefix)}<b>{html.escape(keyword)}</b><br><br>'{body_html}'")
                                i = next_index
                                body_keyword_matched = True
                                break

        if body_keyword_matched:
            continue

        line_no_tabs = line.replace('\t', ' ').strip()

        if not line_no_tabs:
            html_lines.append('')
            i += 1
            continue

        # Check for PR header BEFORE key-value pattern (PR headers match key-value pattern)
        if line_no_tabs.startswith('===') and line_no_tabs.endswith('==='):
            pr_match = re.match(r'^=== PR #(\d+): (.+?) ===$', line_no_tabs)
            if pr_match:
                pr_number = pr_match.group(1)
                pr_title = pr_match.group(2)
                # Convert markdown in PR title (e.g., **bold**, *italic*)
                pr_title_html = markdown_to_html(pr_title, convert_line_breaks=False, repo_url=repo_url)
                html_lines.append(f'=== PR #{pr_number}: <b>{pr_title_html}</b> ===')
                i += 1
                continue

        key_value_pattern = r'^(.+?):\s+(.+)$'
        match = re.match(key_value_pattern, line_no_tabs)

        if match:
            label = match.group(1)
            value = match.group(2)
            label_html = f"<b>{html.escape(label)}:</b>"

            # Remove apostrophes from Description field
            if label.strip() == "Description" and value.startswith("'") and value.endswith("'"):
                value = value[1:-1]  # Remove first and last character (apostrophes)

            # Check if this is a date field that should be highlighted
            date_labels = ['Event date', '- Commit date', 'Created at', 'Closed at', 'Merged at', 'Published at',
                           'Issue date', 'Comment date', 'Review submitted at']
            is_date_label = any(label.strip() == date_label or label.strip().endswith(date_label) for date_label in date_labels)

            # Check if this is an identifier field that should not get markdown conversion
            # These fields contain identifiers (repo names, file names, etc.) that should be escaped, not markdown-processed
            identifier_labels = ['Repo name', 'Asset name', 'Branch name', 'Tag name', 'File name', 'Release tag name']
            is_identifier_label = any(label.strip() == identifier_label or label.strip().endswith(identifier_label) for identifier_label in identifier_labels)

            if value.startswith('http://') or value.startswith('https://'):
                escaped_url = html.escape(value)
                html_lines.append(f"{label_html} <a href=\"{escaped_url}\">{escaped_url}</a>")
            else:
                # Apply date styling if applicable
                if is_date_label:
                    # Check if value contains " by " (e.g., "Merged at: ... by username")
                    if ' by ' in value:
                        date_part, by_part = value.split(' by ', 1)
                        value_to_style = html.escape(date_part)
                        suffix = html.escape(' by ' + by_part)
                    else:
                        value_to_style = html.escape(value)
                        suffix = ''

                    # Bold only the time duration part (e.g., "2 hours, 27 minutes"), not "after"
                    value_html = re.sub(
                        r'\(after\s+([^:]+):\s+([^)]+)\)',
                        r'(after <b>\1</b>: \2)',
                        value_to_style
                    )

                    date_message_style = (
                        "background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: monospace; font-size: 1.00em;"
                    )

                    value_html = f'<span style="{date_message_style}">{value_html}</span>{suffix}'
                elif is_identifier_label:
                    value_html = html.escape(value)
                else:
                    # Non-date, non-identifier values get markdown + URL conversion
                    value_html = markdown_to_html(value, convert_line_breaks=False, repo_url=repo_url)
                    value_html = convert_urls_to_links(value_html)

                html_lines.append(f"{label_html} {value_html}")
        else:
            section_headers = [
                'Changed files list:', 'Removed files:', 'Added files:', 'Modified files:',
                'Closed issues:', 'Opened issues:', 'Reopened issues:',
                'Closed pull requests:', 'Opened pull requests:',
                'Created tags:', 'Deleted tags:', 'Created branches:', 'Deleted branches:',
                'Assets:',
            ]

            # Check if this is a separator line (dots)
            if line_no_tabs and all(c == '.' for c in line_no_tabs):
                html_lines.append('<hr style="border: none; border-top: 1px dotted #ccc; margin: 5px 0;">')
                i += 1
                # Skip next line if it's empty (to avoid double line break)
                if i < len(lines) and not lines[i].strip():
                    i += 1
                continue
            # Check if this line starts with === (commit separator - PR headers already handled above)
            elif line_no_tabs.startswith('===') and line_no_tabs.endswith('==='):
                # Commit separator - bold entire line
                html_lines.append(f'<b>{html.escape(line_no_tabs)}</b>')
                i += 1
                continue
            else:
                # Protect quoted text (file names, strings) from markdown conversion
                quoted_strings = []
                temp_line = line_no_tabs

                import re as re_module
                quote_pattern = r"'([^']+)'"
                for match in re_module.finditer(quote_pattern, temp_line):
                    quoted_strings.append(match.group(1))

                for idx, quoted_str in enumerate(quoted_strings):
                    temp_line = temp_line.replace(f"'{quoted_str}'", f"__QUOTED_{idx}__", 1)

                line_html = markdown_to_html(temp_line, convert_line_breaks=False, repo_url=repo_url)
                line_html = convert_urls_to_links(line_html)

                for idx, quoted_str in enumerate(quoted_strings):
                    escaped_quoted = html.escape(quoted_str)
                    line_html = line_html.replace(f"__QUOTED_{idx}__", f"'<i>{escaped_quoted}</i>'")

                for header in section_headers:
                    if header in line_no_tabs:
                        escaped_header = html.escape(header)
                        line_html = line_html.replace(escaped_header, f'<b>{escaped_header}</b>')
                        break

                html_lines.append(line_html)

        i += 1

    # Join with <br>, then remove <br> between special elements (commit headers, <hr>)
    result = '<br>'.join(html_lines)
    # Remove <br> between commit header and <hr>
    result = re.sub(r'</b><br><hr', r'</b><hr', result)
    # Remove <br> between <hr> and commit header (for multiple commits)
    result = re.sub(r'(<hr[^>]*>)<br><b>===', r'\1<b>===', result)
    # Remove <br> between <hr> and next element (including commit message label)
    result = re.sub(r'(<hr[^>]*>)<br>\s*(<b>|</b>|<span)', r'\1\2', result)
    return result


# Validates the shared SMTP destination, credentials and message fields
def validate_email_settings(subject="Doctor test", body="Doctor test", body_html=""):
    fqdn_re = re.compile(r'(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}\.?$)')
    email_re = re.compile(r'[^@]+@[^@]+\.[^@]+')
    try:
        ipaddress.ip_address(str(SMTP_HOST))
    except ValueError:
        if not fqdn_re.search(str(SMTP_HOST)):
            return "SMTP_HOST must be a valid IP address or fully qualified domain name"
    try:
        port = int(SMTP_PORT)
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        return "SMTP_PORT must be a number from 1 through 65535"
    if not email_re.search(str(SENDER_EMAIL)) or not email_re.search(str(RECEIVER_EMAIL)):
        return "SENDER_EMAIL and RECEIVER_EMAIL must be valid email addresses"
    if not SMTP_USER or not isinstance(SMTP_USER, str) or SMTP_USER == "your_smtp_user" or not SMTP_PASSWORD or not isinstance(SMTP_PASSWORD, str) or SMTP_PASSWORD == "your_smtp_password":
        return "SMTP_USER and SMTP_PASSWORD must contain usable credentials"
    if not subject or not isinstance(subject, str):
        return "The email subject must be a non-empty string"
    if not body and not body_html:
        return "The email body and HTML body cannot both be empty"
    return None


# Closes one SMTP session when there is one, since a failed goodbye must not mask the real result
def smtp_quit_quietly(smtp_object):
    if smtp_object is None:
        return
    try:
        smtp_object.quit()
    except Exception as quit_error:
        debug_print("SMTP quit", outcome="failed", error=f"{type(quit_error).__name__}: {quit_error}")


# Opens one authenticated SMTP session and leaves closing it to the caller
def smtp_connect_and_login(use_ssl, smtp_timeout=15):
    debug_print("SMTP delivery", attempt="1/1", host=SMTP_HOST, port=SMTP_PORT, timeout=f"{smtp_timeout}s", tls=bool(use_ssl), user=mask_secret(SMTP_USER), password=mask_secret(SMTP_PASSWORD))
    smtp_object = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=smtp_timeout)
    try:
        if use_ssl:
            smtp_object.starttls(context=ssl.create_default_context())
        debug_print("SMTP connection established", host=SMTP_HOST, port=SMTP_PORT)
        smtp_object.login(SMTP_USER, SMTP_PASSWORD)
        debug_print("SMTP authentication succeeded", host=SMTP_HOST)
        return smtp_object
    except Exception as connect_error:
        debug_print("SMTP session setup", host=SMTP_HOST, outcome="failed", error=f"{type(connect_error).__name__}: {connect_error}")
        smtp_quit_quietly(smtp_object)
        raise


# Sends email notification
def send_email(subject, body, body_html, use_ssl, smtp_timeout=15):
    validation_error = validate_email_settings(subject, body, body_html)
    if validation_error is not None:
        print(f"Error sending email - SMTP settings are incorrect ({validation_error})")
        return 1

    try:
        smtpObj = smtp_connect_and_login(use_ssl, smtp_timeout=smtp_timeout)
        email_msg = MIMEMultipart('alternative')
        email_msg["From"] = SENDER_EMAIL
        email_msg["To"] = RECEIVER_EMAIL
        email_msg["Subject"] = str(Header(subject, 'utf-8'))

        if body:
            part1 = MIMEText(body, 'plain')
            part1 = MIMEText(body.encode('utf-8'), 'plain', _charset='utf-8')
            email_msg.attach(part1)

        if body_html:
            part2 = MIMEText(body_html, 'html')
            part2 = MIMEText(body_html.encode('utf-8'), 'html', _charset='utf-8')
            email_msg.attach(part2)

        smtpObj.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, email_msg.as_string())
        smtpObj.quit()
        debug_print("SMTP delivery", outcome="OK", host=SMTP_HOST, attempt="1/1")
        verbose_print("Email delivery succeeded")
    except Exception as e:
        debug_print("SMTP delivery", outcome="failed", host=SMTP_HOST, attempt="1/1", error=f"{type(e).__name__}: {e}")
        verbose_print("Email delivery failed")
        print(f"Error sending email: {sanitize_error_text(e)}")
        return 1
    return 0


# Returns all private values currently known to the process
def known_secret_values():
    values = []
    for key in SECRET_KEYS:
        value = globals().get(key)
        if isinstance(value, str) and len(value) >= MIN_REDACTABLE_SECRET_LENGTH and not value.startswith("your_"):
            values.append(value)
    if isinstance(WEBHOOK_HEADERS, dict):
        for name, value in WEBHOOK_HEADERS.items():
            if isinstance(name, str) and name.casefold() == "authorization" and isinstance(value, str) and len(value) >= MIN_REDACTABLE_SECRET_LENGTH:
                values.append(value)
    return values


# Returns a fixed marker for every configured secret without exposing any characters
def mask_secret(value, visible=3):
    if not str(value or ""):
        return "<not set>"
    return "<redacted>"


# Redacts known values and common credential shapes from arbitrary error text
def sanitize_error_text(value):
    text = str(value or "")
    for secret in sorted(known_secret_values(), key=len, reverse=True):
        text = text.replace(secret, "<redacted>")
    patterns = (
        (r"(?m)(\b(?:GITHUB_TOKEN|SMTP_PASSWORD|WEBHOOK_URL|NTFY_ACCESS_TOKEN)\b\s*=\s*).*$", r"\1<redacted>"),
        (r"(?i)(authorization['\"]?\s*[:=]\s*['\"]?(?:bearer|basic)\s+)[^\s,;'\"}]+", r"\1<redacted>"),
        (r"(?i)(['\"]?(?:github_token|smtp_password|webhook_url|ntfy_access_token)['\"]?\s*[:=]\s*['\"]?)[^\s,;'\"}]+", r"\1<redacted>"),
        (r"(?i)\b(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]+\b", "<redacted>"),
        (r"(?i)https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api(?:/v[0-9]+)?/webhooks/[0-9]+/[^\s'\"<>]+", "<redacted>"),
        (r"(?i)([?&](?:access_token|auth|token)=)[^&#\s]+", r"\1<redacted>"),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


# Preserves the original webhook sanitizer name for existing callers
def sanitize_webhook_text(value):
    return sanitize_error_text(value)


# Prints one sanitized user-facing decision only when verbose mode is enabled
def verbose_print(message):
    if VERBOSE_MODE:
        print(f"* {sanitize_error_text(message)}")


# Renders one diagnostic line as an operation followed by comma-separated key=value fields, dropping unset ones
def format_diagnostic_line(operation, fields):
    rendered = ", ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    return f"{operation}: {rendered}" if rendered else str(operation)


# Prints one timestamped sanitized operation only when debug mode is enabled
def debug_print(_operation, **fields):
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = format_diagnostic_line(_operation, fields)
        print(f"[DEBUG {timestamp}] {sanitize_error_text(message)}")


# Redacts credential-bearing request headers before diagnostic output
def sanitize_debug_headers(headers):
    if not isinstance(headers, dict):
        return headers
    sensitive_names = {"authorization", "cookie", "proxy-authorization", "x-api-key"}
    return {name: mask_secret(value) if str(name).casefold() in sensitive_names else sanitize_error_text(value) for name, value in headers.items()}


# Redacts credential-bearing request parameters before diagnostic output
def sanitize_debug_params(params):
    if not isinstance(params, dict):
        return params
    sensitive_names = {"access_token", "auth", "key", "password", "refresh_token", "token"}
    return {name: mask_secret(value) if str(name).casefold() in sensitive_names else sanitize_error_text(value) for name, value in params.items()}


# Returns a diagnostic URL with credentials and optionally its private path removed
def diagnostic_endpoint(url, host_only=False):
    try:
        parsed = urlsplit(str(url or "").strip())
    except ValueError as exc:
        debug_print("Could not parse diagnostic endpoint", outcome="failed", error=f"{type(exc).__name__}: {exc}")
        return "<invalid endpoint>"
    if not parsed.scheme or not parsed.hostname:
        return sanitize_error_text(url)
    port = f":{parsed.port}" if parsed.port else ""
    endpoint = f"{parsed.scheme}://{parsed.hostname}{port}"
    if not host_only:
        endpoint += parsed.path or ""
    return sanitize_error_text(endpoint)


# Logs one outbound HTTP request without exposing private request values
def debug_http_request(method, url, operation, timeout, headers=None, params=None, token=None, host_only=False):
    debug_print(f"HTTP {str(method).upper()}", url=diagnostic_endpoint(url, host_only=host_only), operation=operation, timeout=f"{timeout}s", headers=sanitize_debug_headers(headers) if headers else None, params=sanitize_debug_params(params) if params else None, token=mask_secret(token) if token is not None else None)


# Logs one HTTP response status for a named operation
def debug_http_response(method, url, operation, status):
    debug_print(f"HTTP {str(method).upper()}", url=diagnostic_endpoint(url), operation=operation, status=status)


# Logs one swallowed exception and the feature that degraded because of it
def debug_swallowed_exception(operation, error):
    debug_print(operation, outcome="degraded", error=f"{type(error).__name__}: {error}")


# Reports a tracked feature that cannot produce its alert during the current cycle
def verbose_degraded_feature(feature, alert, error=None):
    verbose_print(f"{feature} is unavailable, so {alert} cannot fire this cycle")
    if error is not None:
        debug_swallowed_exception(feature, error)


# Logs the start of one monitoring poll and returns its monotonic start time
def debug_monitor_check_start(check_number, user):
    debug_print("Starting monitoring check", check=f"#{check_number}", user=user)
    return time.monotonic()


# Logs one completed monitoring poll with its duration and schedule
def debug_monitor_check_timing(check_number, user, started_at, interval):
    duration = max(0.0, time.monotonic() - started_at)
    next_check = datetime.now() + dt.timedelta(seconds=interval)
    debug_print("Completed monitoring check", check=f"#{check_number}", user=user, duration=f"{duration:.3f}s", next=next_check.astimezone().isoformat(), interval=display_time(interval))


# Logs one scheduled wait with its reason and next timestamp
def debug_monitor_wait_timing(reason, interval):
    next_check = datetime.now() + dt.timedelta(seconds=interval)
    debug_print("Waiting", interval=display_time(interval), reason=reason, next=next_check.astimezone().isoformat())


@dataclass(frozen=True)
class InstallContext:
    install_method: str
    operating_system: str
    command_prefix: tuple[str, ...]


# Detects whether the current invocation uses the PyPI command or downloaded script
def detect_install_context(argv0=None, module_path=None, operating_system=None):
    invocation = str(sys.argv[0] if argv0 is None else argv0)
    source_path = str(Path(__file__ if module_path is None else module_path).resolve())
    selected_system = platform.system() if operating_system is None else str(operating_system)
    manual = Path(invocation).suffix.casefold() == ".py"
    prefix = (sys.executable, source_path) if manual else ("github_monitor",)
    return InstallContext("manual" if manual else "pip", selected_system, prefix)


# Returns a readable name for the detected install method
def install_method_display_name(method=None):
    selected = detect_install_context().install_method if method is None else str(method)
    return {"pip": "PyPI install", "manual": "downloaded script"}.get(selected, selected)


# Renders one exact or portable install-aware command with platform quoting
def render_install_command(arguments, install_context=None, exact=True):
    context = detect_install_context() if install_context is None else install_context
    prefix = context.command_prefix
    if not exact:
        executable = "python" if context.operating_system.casefold() == "windows" else "python3"
        path_class = PureWindowsPath if context.operating_system.casefold() == "windows" else Path
        prefix = (executable, path_class(context.command_prefix[-1]).name) if context.install_method == "manual" else ("github_monitor",)
    parts = [*prefix, *(str(argument) for argument in arguments)]
    if context.operating_system.casefold() == "windows":
        return subprocess.list2cmdline(parts)
    return shlex.join(parts)


RECOVERY_CODES = frozenset({
    "auth.github_token_invalid",
    "auth.github_token_missing",
    "config.invalid",
    "config.missing",
    "config.value_invalid",
    "dependency.missing",
    "dotenv.missing",
    "file.exists",
    "file.unreadable",
    "file.unwritable",
    "github.api_error",
    "github.forbidden",
    "github.not_found",
    "github.rate_limited",
    "network.connection",
    "network.timeout",
    "secret.missing",
    "smtp.authentication",
    "smtp.configuration",
    "smtp.delivery",
    "target.missing",
    "target.not_found",
    "target.not_visible",
    "timezone.invalid",
    "webhook.invalid",
    "webhook.rejected",
    "webhook.unreachable",
    "unknown",
})


@dataclass(frozen=True)
class RecoveryAdvice:
    code: str
    summary: str
    fix: str
    retryable: bool
    detail: str = ""
    guide_url: str = ""


class RecoveryError(Exception):
    # Stores structured recovery advice with the original exception when available
    def __init__(self, advice, cause=None):
        self.advice = advice
        self.cause = cause
        super().__init__(advice.summary)


# Constructs validated recovery advice with every user-facing field sanitized
def make_recovery_advice(code, summary, fix, retryable=False, detail="", guide_url=""):
    if code not in RECOVERY_CODES:
        raise ValueError(f"Unsupported recovery code: {code}")
    return RecoveryAdvice(code, sanitize_error_text(summary), sanitize_error_text(fix), bool(retryable), sanitize_error_text(detail), sanitize_error_text(guide_url))


# Renders recovery advice according to the effective diagnostic modes
def render_recovery_advice(advice, verbose=None, debug=None):
    verbose_enabled = VERBOSE_MODE if verbose is None else bool(verbose)
    debug_enabled = DEBUG_MODE if debug is None else bool(debug)
    lines = [f"* Error: {sanitize_error_text(advice.summary)}", f"To fix: {sanitize_error_text(advice.fix)}"]
    if advice.guide_url:
        lines.append(f"Guide: {sanitize_error_text(advice.guide_url)}")
    if verbose_enabled or debug_enabled:
        lines.extend((f"Recovery code: {advice.code}", f"Retryable: {'Yes' if advice.retryable else 'No'}"))
    if debug_enabled and advice.detail:
        lines.append(f"Technical detail: {sanitize_error_text(advice.detail)}")
    return "\n".join(lines)


# Prints one structured recovery message
def print_recovery_advice(advice, verbose=None, debug=None):
    print(render_recovery_advice(advice, verbose=verbose, debug=debug))


# Maps one exception and operation context to stable recovery advice
def classify_recovery_error(error, context="unknown", install_context=None):
    if isinstance(error, RecoveryError):
        return error.advice
    selected_context = str(context or "unknown").casefold()
    detail = f"{type(error).__name__}: {error}"
    token_command = render_install_command(["--set-github-token"], install_context)
    webhook_command = render_install_command(["--set-webhook-url"], install_context)
    config_command = render_install_command(["--generate-config", "github_monitor.conf"], install_context)
    debug_command = render_install_command(["--debug"], install_context)
    if isinstance(error, (req.Timeout, TimeoutError, socket.timeout)):
        return make_recovery_advice("network.timeout", "The network request timed out", "Check connectivity and increase the configured timeout before trying again", True, detail, DEBUG_GUIDE_URL)
    if isinstance(error, (req.ConnectionError, socket.gaierror)):
        return make_recovery_advice("network.connection", "The configured service could not be reached", "Check the network and configured service URL then try again", True, detail, DEBUG_GUIDE_URL)
    if isinstance(error, req.RequestException):
        return make_recovery_advice("network.connection", "The configured service request failed", "Check the network and configured service URL then try again", True, detail, DEBUG_GUIDE_URL)
    if isinstance(error, BadCredentialsException):
        return make_recovery_advice("auth.github_token_invalid", "GitHub rejected the configured token", f"Create or review the token then run: {token_command}", False, detail, AUTH_GUIDE_URL)
    if isinstance(error, RateLimitExceededException):
        return make_recovery_advice("github.rate_limited", "GitHub API rate limiting paused the request", "Wait for the reported reset time before trying again", True, detail, DEBUG_GUIDE_URL)
    if isinstance(error, UnknownObjectException):
        code = "target.not_found" if selected_context == "target" else "github.not_found"
        return make_recovery_advice(code, "GitHub could not find the requested resource", "Check the target name and token access then try again", False, detail, DEBUG_GUIDE_URL)
    if isinstance(error, GithubException):
        status = getattr(error, "status", None)
        if status == 403:
            return make_recovery_advice("github.forbidden", "GitHub refused access to the requested resource", "Check token permissions and resource visibility", False, detail, AUTH_GUIDE_URL)
        retryable = status is None or (isinstance(status, int) and status >= 500)
        return make_recovery_advice("github.api_error", "GitHub returned an API error", f"Try again or run {debug_command} for sanitized technical detail", retryable, detail, DEBUG_GUIDE_URL)
    if isinstance(error, smtplib.SMTPAuthenticationError):
        return make_recovery_advice("smtp.authentication", "The SMTP server rejected the configured credentials", "Check SMTP_USER and replace SMTP_PASSWORD before sending another test", False, detail, NOTIFICATION_GUIDE_URL)
    if isinstance(error, PermissionError):
        return make_recovery_advice("file.unwritable", "A required file could not be written", "Check the destination path and file permissions", False, detail, CONFIG_GUIDE_URL)
    if isinstance(error, FileNotFoundError):
        code = "config.missing" if selected_context == "config" else "dotenv.missing" if selected_context == "dotenv" else "file.unreadable"
        return make_recovery_advice(code, "A required file could not be found", "Check the configured path and try again", False, detail, CONFIG_GUIDE_URL)
    if selected_context == "github_token":
        return make_recovery_advice("auth.github_token_invalid", "GitHub token setup could not be completed", f"Correct the problem then run: {token_command}", False, detail, AUTH_GUIDE_URL)
    if selected_context == "webhook":
        return make_recovery_advice("webhook.invalid", "Webhook setup could not be completed", f"Check the HTTPS destination then run: {webhook_command}", False, detail, NOTIFICATION_GUIDE_URL)
    if selected_context == "email":
        return make_recovery_advice("smtp.configuration", "The SMTP server could not be reached", "Check SMTP_HOST, SMTP_PORT and SMTP_SSL, then confirm the host is reachable from this machine", True, detail, NOTIFICATION_GUIDE_URL)
    if selected_context == "config":
        # The parser already names the line and setting, so the summary carries it instead of only --debug
        reason = sanitize_error_text(error)
        summary = f"The selected configuration is invalid: {reason}" if reason else "The selected configuration is invalid"
        return make_recovery_advice("config.invalid", summary, f"Correct the reported setting, or generate a fresh configuration with: {config_command}", False, detail, CONFIG_GUIDE_URL)
    if selected_context == "timezone":
        return make_recovery_advice("timezone.invalid", "The configured timezone is invalid", "Install tzlocal for automatic detection or set a valid pytz timezone", False, detail, CONFIG_GUIDE_URL)
    return make_recovery_advice("unknown", "An unexpected error stopped the requested action", f"Run the command again with {debug_command} and include the recovery code when asking for help", False, detail, SUPPORT_GUIDE_URL)


# Returns whether a webhook URL is a complete private HTTPS link
def validate_webhook_url(url: Any = None) -> bool:
    selected_url = WEBHOOK_URL if url is None else url
    if not isinstance(selected_url, str) or not selected_url.strip():
        return False
    try:
        parsed = urlsplit(selected_url.strip())
    except ValueError:
        return False
    return parsed.scheme.casefold() == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password and bool(parsed.path.strip("/"))


# Converts a complete ntfy URL or valid ntfy.sh topic name into a complete HTTPS URL
def normalize_ntfy_topic_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.strip()
    if validate_webhook_url(normalized):
        return normalized
    if re.fullmatch(r"[-_A-Za-z0-9]{1,64}", normalized):
        return f"https://ntfy.sh/{normalized}"
    return ""


# Returns the normalized configured webhook provider or an empty string when unsupported
def normalized_webhook_provider(provider: Any = None) -> str:
    selected_provider = WEBHOOK_PROVIDER if provider is None else provider
    if not isinstance(selected_provider, str):
        return ""
    normalized = selected_provider.strip().casefold()
    return normalized if normalized in ("discord", "ntfy") else ""


# Returns enabled email notification category names in display order
def _startup_email_notification_categories():
    settings = (
        (PROFILE_NOTIFICATION, "profile"),
        (EVENT_NOTIFICATION, "events"),
        (REPO_NOTIFICATION, "repositories"),
        (REPO_UPDATE_DATE_NOTIFICATION, "repository updates"),
        (CONTRIB_NOTIFICATION, "contributions"),
        (ERROR_NOTIFICATION, "errors"),
    )
    return [label for enabled, label in settings if enabled]


# Returns enabled webhook notification category names in display order
def _startup_webhook_notification_categories():
    settings = (
        (WEBHOOK_PROFILE_NOTIFICATION, "profile"),
        (WEBHOOK_EVENT_NOTIFICATION, "events"),
        (WEBHOOK_REPO_NOTIFICATION, "repositories"),
        (WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, "repository updates"),
        (WEBHOOK_CONTRIB_NOTIFICATION, "contributions"),
        (WEBHOOK_ERROR_NOTIFICATION, "errors"),
    )
    return [label for enabled, label in settings if WEBHOOK_ENABLED and enabled]


# Formats one notification row with unstarred continuation lines when needed
def _format_startup_notification_line(label, categories):
    prefix = f"* {label:<30}"
    state = "On (" + ", ".join(categories) + ")" if categories else "Off"
    return textwrap.fill(state, width=100, initial_indent=prefix, subsequent_indent=" " * len(prefix), break_long_words=False, break_on_hyphens=False)


# Builds compact startup notification lines for both delivery channels
def _startup_notification_summary_lines():
    enabled_email = _startup_email_notification_categories()
    enabled_webhook = _startup_webhook_notification_categories()
    return [_format_startup_notification_line("Notifications (email):", enabled_email), _format_startup_notification_line("Notifications (webhook):", enabled_webhook)]


@dataclass(frozen=True)
class StartupSummaryRow:
    label: str
    value: str
    concise: bool = False
    full: bool = True
    log: bool = True


# Groups every resolved secret name into the dotenv, environment and configuration buckets the summary prints
def startup_secret_buckets():
    from_dotenv, from_environment, from_config = [], [], []
    for name, source in sorted(SECRET_SOURCES.items()):
        if str(source).startswith("dotenv file"):
            from_dotenv.append(name)
        elif source == "environment":
            from_environment.append(name)
        else:
            from_config.append(name)
    return from_dotenv, from_environment, from_config


# Builds concise and complete startup rows without exposing private values
def build_startup_summary(target, config_path, env_path, output_path):
    install_context = detect_install_context()
    email_categories = _startup_email_notification_categories()
    webhook_categories = _startup_webhook_notification_categories()
    email_state = "On (" + ", ".join(email_categories) + ")" if email_categories else "Off"
    webhook_state = "On (" + ", ".join(webhook_categories) + ")" if webhook_categories else "Off"
    from_dotenv, from_environment, from_config = startup_secret_buckets()
    return [
        StartupSummaryRow("Target", str(target), concise=True),
        StartupSummaryRow("Polling interval", display_time(GITHUB_CHECK_INTERVAL), concise=True),
        StartupSummaryRow("Notifications (email)", email_state, concise=True),
        StartupSummaryRow("Notifications (webhook)", webhook_state, concise=True),
        StartupSummaryRow("Output", str(output_path) if output_path else "Terminal only (logging disabled)", concise=True, full=False, log=False),
        StartupSummaryRow("Output logging", str(output_path) if output_path else "Disabled"),
        StartupSummaryRow("Config", str(config_path) if config_path else "None", concise=True),
        StartupSummaryRow("Dotenv", str(env_path) if env_path else "None", concise=True),
        StartupSummaryRow("GitHub API URL", str(GITHUB_API_URL)),
        StartupSummaryRow("Track repository changes", str(TRACK_REPOS_CHANGES)),
        StartupSummaryRow("Track contribution changes", str(TRACK_CONTRIB_CHANGES)),
        StartupSummaryRow("Monitor GitHub events", str(not DO_NOT_MONITOR_GITHUB_EVENTS)),
        StartupSummaryRow("Owned repositories only", str(not GET_ALL_REPOS)),
        StartupSummaryRow("Liveness output", display_time(LIVENESS_CHECK_INTERVAL) if LIVENESS_CHECK_INTERVAL else "Disabled", concise=bool(LIVENESS_CHECK_INTERVAL)),
        StartupSummaryRow("CSV output", str(CSV_FILE) if CSV_FILE else "Disabled", concise=bool(CSV_FILE)),
        StartupSummaryRow("Terminal truncation", f"{TRUNCATE_CHARS} chars" if TRUNCATE_CHARS else "Disabled", concise=bool(TRUNCATE_CHARS)),
        StartupSummaryRow("Local timezone", str(LOCAL_TIMEZONE)),
        StartupSummaryRow("Install method", install_method_display_name(install_context.install_method)),
        StartupSummaryRow("Secrets from dotenv", ", ".join(from_dotenv) if from_dotenv else "None"),
        StartupSummaryRow("Secrets from environment", ", ".join(from_environment) if from_environment else "None"),
        StartupSummaryRow("Secrets from config file", ", ".join(from_config) if from_config else "None"),
        StartupSummaryRow("TLS verification", "On" if VERIFY_SSL else "Off, server certificates are not checked", concise=not VERIFY_SSL),
        StartupSummaryRow("ASCII log separators", f"{ascii_log_separators_enabled()} (mode: {ASCII_LOG_SEPARATORS})"),
        StartupSummaryRow("Coloured output", f"{COLOR_ENABLED} (setting: {COLORED_OUTPUT})"),
        StartupSummaryRow("Verbose mode", str(VERBOSE_MODE), concise=bool(VERBOSE_MODE)),
        StartupSummaryRow("Debug mode", str(DEBUG_MODE), concise=bool(DEBUG_MODE)),
        StartupSummaryRow("More details", "use --verbose or --debug", concise=True, full=False, log=False),
    ]


# Formats one startup summary row with aligned plain ASCII columns
def format_startup_summary_row(row):
    prefix = f"* {(row.label + ':'):<30}"
    if row.label in ("Notifications (email)", "Notifications (webhook)"):
        return textwrap.fill(row.value, width=100, initial_indent=prefix, subsequent_indent=" " * len(prefix), break_long_words=False, break_on_hyphens=False) + "\n"
    return f"{prefix}{row.value}\n"


# Routes concise or complete startup rows independently to terminal and log destinations
def emit_startup_summary(rows, show_full, stream=None):
    destination = sys.stdout if stream is None else stream
    routed = hasattr(destination, "terminal_only") and hasattr(destination, "log_only")
    for row in rows:
        line = format_startup_summary_row(row)
        if routed and row.full and row.log:
            destination.log_only(line)
        if row.full if show_full else row.concise:
            if routed:
                destination.terminal_only(line)
            else:
                destination.write(line)
    if routed:
        destination.log_only("\n")
        destination.terminal_only("\n")
    else:
        destination.write("\n")
        destination.flush()


# Detects Discord and public ntfy webhook providers from distinctive URL shapes
def detect_webhook_provider(url: Any) -> str:
    if not validate_webhook_url(url):
        return ""
    try:
        parsed = urlsplit(str(url).strip())
    except ValueError:
        return ""
    hostname = parsed.hostname.casefold() if parsed.hostname else ""
    if hostname == "ntfy.sh":
        return "ntfy"
    discord_host = hostname in ("discord.com", "discordapp.com") or hostname.endswith(".discord.com") or hostname.endswith(".discordapp.com")
    discord_path = re.match(r"^/api(?:/v[0-9]+)?/webhooks/[0-9]+/[^/]+/?$", parsed.path) is not None
    return "discord" if discord_host and discord_path else ""


# Returns whether one configured webhook alert is enabled independently of email settings
def webhook_event_enabled(notification_type: str) -> bool:
    settings = {
        "profile": WEBHOOK_PROFILE_NOTIFICATION,
        "event": WEBHOOK_EVENT_NOTIFICATION,
        "repo": WEBHOOK_REPO_NOTIFICATION,
        "repo_update": WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION,
        "contrib": WEBHOOK_CONTRIB_NOTIFICATION,
        "error": WEBHOOK_ERROR_NOTIFICATION,
    }
    return bool(WEBHOOK_ENABLED and settings.get(notification_type, False))


# Returns whether at least one webhook alert category is enabled
def webhook_notifications_enabled() -> bool:
    categories = (WEBHOOK_PROFILE_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION, WEBHOOK_ERROR_NOTIFICATION)
    return bool(WEBHOOK_ENABLED and any(categories))


# Parses a webhook rate-limit delay and caps untrusted server values to a short wait
def webhook_retry_after_seconds(response: Any) -> float:
    candidates = []
    headers = getattr(response, "headers", {}) or {}
    if hasattr(headers, "get"):
        candidates.append(headers.get("Retry-After"))
    try:
        payload = response.json()
    except Exception as exc:
        debug_swallowed_exception("Webhook retry response parsing", exc)
        payload = None
    if isinstance(payload, dict):
        candidates.append(payload.get("retry_after"))
    for candidate in candidates:
        if candidate is None or candidate == "":
            continue
        try:
            seconds = float(candidate)
        except (TypeError, ValueError):
            try:
                retry_at = parsedate_to_datetime(str(candidate))
                seconds = (retry_at - datetime.now(retry_at.tzinfo)).total_seconds()
            except Exception as exc:
                debug_swallowed_exception("Webhook retry timestamp parsing", exc)
                continue
        return max(0.0, min(seconds, WEBHOOK_MAX_RETRY_AFTER_SECONDS))
    return WEBHOOK_FALLBACK_RETRY_SECONDS


# Applies configured placeholders recursively to a webhook template
def format_payload(template: Any, payload: dict) -> Any:
    if isinstance(template, dict):
        return {key: format_payload(value, payload) for key, value in template.items()}
    if isinstance(template, list):
        return [format_payload(value, payload) for value in template]
    if isinstance(template, tuple):
        return tuple(format_payload(value, payload) for value in template)
    if isinstance(template, str):
        if template == "{fields}":
            return payload.get("fields", [])
        if template == "{color}":
            return payload.get("color", 0x2F81F7)
        try:
            return template.format(**payload)
        except KeyError:
            return template
    return template


# Returns a configuration error for unsafe or unsupported webhook customization
def validate_webhook_customization(provider: Any = None) -> Optional[str]:
    selected_provider = normalized_webhook_provider(provider)
    if selected_provider == "discord":
        if not isinstance(WEBHOOK_USERNAME, str):
            return "WEBHOOK_USERNAME must be a string"
        if not isinstance(WEBHOOK_AVATAR_URL, str):
            return "WEBHOOK_AVATAR_URL must be a string"
        if WEBHOOK_AVATAR_URL.strip() and not validate_webhook_url(WEBHOOK_AVATAR_URL):
            return "WEBHOOK_AVATAR_URL must contain a complete HTTPS link without embedded credentials"
        if not isinstance(WEBHOOK_TEMPLATE, (dict, list, str)):
            return "WEBHOOK_TEMPLATE must be a dictionary, list or string"
    if not isinstance(WEBHOOK_TRANSFORMS, (list, tuple)):
        return "WEBHOOK_TRANSFORMS must be a list or tuple"
    for index, transform in enumerate(WEBHOOK_TRANSFORMS):
        if not isinstance(transform, (list, tuple)) or len(transform) < 2 or not isinstance(transform[0], str) or not isinstance(transform[1], str):
            return f"WEBHOOK_TRANSFORMS entry {index + 1} must contain a field name and string method name"
        if transform[1].startswith("_") or not callable(getattr("", transform[1], None)):
            return f"WEBHOOK_TRANSFORMS entry {index + 1} uses an unsupported string method"
    return None


# Applies configured string transformations to one webhook value mapping
def apply_webhook_transforms(payload: dict) -> dict:
    transformed = dict(payload)
    for index, transform in enumerate(WEBHOOK_TRANSFORMS):
        field = transform[0]
        method_name = transform[1]
        if field not in transformed or not isinstance(transformed[field], str):
            continue
        try:
            transformed[field] = getattr(transformed[field], method_name)(*transform[2:])
        except Exception as exc:
            raise ValueError(f"WEBHOOK_TRANSFORMS entry {index + 1} could not apply {field}.{method_name}") from exc
    return transformed


# Builds bounded placeholder values shared by webhook templates, headers and providers
def build_webhook_values(title: str, description: str, notification_type: str, image_url: str = "") -> dict:
    colors = {"profile": 0x2F81F7, "event": 0x8957E5, "repo": 0x238636, "repo_update": 0xD29922, "contrib": 0x1F883D, "error": 0xE74C3C}
    safe_title = sanitize_webhook_text(title)[:WEBHOOK_EMBED_TITLE_LIMIT] or "GitHub Monitor"
    safe_description = sanitize_webhook_text(description)[:WEBHOOK_EMBED_DESCRIPTION_LIMIT]
    username = WEBHOOK_USERNAME.strip()[:80] if isinstance(WEBHOOK_USERNAME, str) else ""
    avatar_url = WEBHOOK_AVATAR_URL.strip() if isinstance(WEBHOOK_AVATAR_URL, str) else ""
    payload = {"title": safe_title, "description": safe_description, "version": VERSION, "image_url": str(image_url or ""), "fields": [], "fields_str": "", "color": colors.get(notification_type, 0x2F81F7), "timestamp": datetime.now().astimezone().isoformat(), "username": username, "avatar_url": avatar_url}
    return apply_webhook_transforms(payload)


# Builds one customized Discord-format payload while keeping mentions disabled
def build_webhook_payload(title: str, description: str, notification_type: str, image_url: str = "", payload_values: Optional[dict] = None) -> Any:
    values = build_webhook_values(title, description, notification_type, image_url) if payload_values is None else payload_values
    try:
        payload = format_payload(WEBHOOK_TEMPLATE, values)
    except Exception as exc:
        raise ValueError("WEBHOOK_TEMPLATE could not be formatted with the supported placeholders") from exc
    if isinstance(payload, dict):
        if payload.get("username") == "":
            payload.pop("username")
        if payload.get("avatar_url") == "":
            payload.pop("avatar_url")
        payload["allowed_mentions"] = {"parse": []}
    return payload


# Truncates text to a UTF-8 byte limit without returning a partial character
def truncate_utf8_bytes(text: str, max_bytes: int, suffix: str = "") -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    encoded_suffix = suffix.encode("utf-8")
    if len(encoded_suffix) >= max_bytes:
        return encoded_suffix[:max_bytes].decode("utf-8", errors="ignore")
    return encoded[:max_bytes - len(encoded_suffix)].decode("utf-8", errors="ignore") + suffix


# Builds one bounded ntfy title and message pair
def build_ntfy_webhook_message(title: str, description: str) -> tuple[str, str]:
    safe_title = sanitize_webhook_text(title)[:WEBHOOK_EMBED_TITLE_LIMIT] or "GitHub Monitor"
    safe_message = truncate_utf8_bytes(sanitize_webhook_text(description), NTFY_MESSAGE_LIMIT_BYTES, NTFY_TRUNCATION_SUFFIX)
    return safe_title, safe_message


# Returns a safe validation error for one custom webhook header mapping
def _validate_webhook_header_mapping(headers: Any) -> Optional[str]:
    if not isinstance(headers, dict):
        return "WEBHOOK_HEADERS must be a dictionary of string header names and values"
    normalized_names = set()
    for name, value in headers.items():
        if not isinstance(name, str) or not re.fullmatch(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+", name):
            return "WEBHOOK_HEADERS contains an invalid HTTP header name"
        normalized_name = name.casefold()
        if normalized_name in normalized_names:
            return "WEBHOOK_HEADERS contains duplicate case-insensitive header names"
        normalized_names.add(normalized_name)
        if not isinstance(value, str):
            return f"WEBHOOK_HEADERS value for {name} must be a string"
        if "\r" in value or "\n" in value:
            return f"WEBHOOK_HEADERS value for {name} must not contain line breaks"
    return None


# Returns a safe configuration error for custom webhook headers or ntfy access tokens
def validate_webhook_headers(provider: Any = None) -> Optional[str]:
    selected_provider = normalized_webhook_provider(provider)
    header_error = _validate_webhook_header_mapping(WEBHOOK_HEADERS)
    if header_error is not None:
        return header_error
    if selected_provider == "ntfy":
        if not isinstance(NTFY_ACCESS_TOKEN, str):
            return "NTFY_ACCESS_TOKEN must be a string"
        token = NTFY_ACCESS_TOKEN.strip()
        if "\r" in token or "\n" in token:
            return "NTFY_ACCESS_TOKEN must not contain line breaks"
        if token.casefold().startswith(("bearer ", "basic ")):
            return "NTFY_ACCESS_TOKEN must contain only the access token without an Authorization scheme"
    return None


# Builds provider-specific headers while formatting placeholders and applying private ntfy authentication
def build_webhook_headers(provider: str, payload: dict) -> dict:
    validation_error = validate_webhook_headers(provider)
    if validation_error is not None:
        raise ValueError(validation_error)
    try:
        formatted_headers = format_payload(WEBHOOK_HEADERS, payload)
    except Exception as exc:
        raise ValueError("WEBHOOK_HEADERS could not be formatted with the supported placeholders") from exc
    formatted_error = _validate_webhook_header_mapping(formatted_headers)
    if formatted_error is not None:
        raise ValueError(formatted_error)
    headers = dict(cast(dict[str, str], formatted_headers))
    if not any(name.casefold() == "user-agent" for name in headers):
        headers["User-Agent"] = f"GitHubMonitor/{VERSION}"
    if provider == "ntfy":
        headers = {name: value for name, value in headers.items() if name.casefold() != "content-type"}
        headers["Content-Type"] = "text/plain; charset=utf-8"
        token = NTFY_ACCESS_TOKEN.strip()
        if token:
            headers = {name: value for name, value in headers.items() if name.casefold() != "authorization"}
            headers["Authorization"] = f"Bearer {token}"
    return headers


# Prints one webhook configuration or delivery failure without exposing private values
def print_webhook_error(message: Any) -> None:
    print(f"Error sending webhook: {sanitize_webhook_text(message)}")


# Sends one webhook request with the destination, deadline and redirect policy every delivery shares
def post_webhook_request(**request_kwargs: Any) -> Any:
    destination = str(WEBHOOK_URL or "").strip()
    # Revalidated here because a dotenv reload can replace the destination after the delivery started
    if not validate_webhook_url(destination):
        raise req.exceptions.InvalidURL("WEBHOOK_URL must contain a complete HTTPS link")
    debug_http_request("POST", destination, "webhook delivery", WEBHOOK_TIMEOUT_SECONDS, headers=request_kwargs.get("headers"), params=request_kwargs.get("params"), token=NTFY_ACCESS_TOKEN or None, host_only=True)
    return WEBHOOK_SESSION.post(destination, timeout=WEBHOOK_TIMEOUT_SECONDS, verify=VERIFY_SSL, allow_redirects=False, **request_kwargs)


# Sends one webhook through an isolated bounded retry path that never uses GitHub retries
def send_webhook(title: str, description: str, notification_type: str = "event", force: bool = False, sleeper: Optional[Callable[[float], None]] = None, image_url: str = "") -> int:
    if not force and not webhook_event_enabled(notification_type):
        verbose_print(f"Webhook delivery skipped because {notification_type} alerts are disabled")
        return 1
    if not validate_webhook_url():
        print_webhook_error("WEBHOOK_URL must contain a complete HTTPS link")
        return 1
    provider = normalized_webhook_provider()
    if not provider:
        print_webhook_error("WEBHOOK_PROVIDER must be discord or ntfy")
        return 1
    customization_error = validate_webhook_customization(provider)
    if customization_error is not None:
        print_webhook_error(customization_error)
        return 1
    header_error = validate_webhook_headers(provider)
    if header_error is not None:
        print_webhook_error(header_error)
        return 1
    try:
        webhook_values = build_webhook_values(title, description, notification_type, image_url)
        request_headers = build_webhook_headers(provider, webhook_values)
        discord_payload = build_webhook_payload(title, description, notification_type, image_url, webhook_values) if provider == "discord" else None
    except ValueError as exc:
        print_webhook_error(exc)
        return 1
    sleep_func = time.sleep if sleeper is None else sleeper
    ntfy_title, ntfy_message = build_ntfy_webhook_message(str(webhook_values["title"]), str(webhook_values["description"])) if provider == "ntfy" else ("", "")
    last_error: Any = None
    for attempt in range(WEBHOOK_MAX_ATTEMPTS):
        try:
            attempt_number = attempt + 1
            debug_print("Webhook delivery", channel=provider, host=diagnostic_endpoint(WEBHOOK_URL, host_only=True), attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}", timeout=f"{WEBHOOK_TIMEOUT_SECONDS}s")
            if provider == "ntfy":
                response = post_webhook_request(data=ntfy_message.encode("utf-8"), params={"title": ntfy_title}, headers=request_headers)
            elif isinstance(discord_payload, str):
                response = post_webhook_request(data=discord_payload, headers=request_headers)
            else:
                response = post_webhook_request(json=discord_payload, headers=request_headers)
            retryable = response.status_code == 429 or 500 <= response.status_code <= 599
            debug_print("Webhook delivery", channel=provider, attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}", status=response.status_code, retryable=retryable)
            if 200 <= response.status_code <= 299:
                verbose_print(f"Webhook delivery through {provider} succeeded")
                debug_print("Webhook delivery", channel=provider, outcome="OK", attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}")
                return 0
            last_error = response
            if not retryable or attempt == WEBHOOK_MAX_ATTEMPTS - 1:
                verbose_print(f"Webhook delivery through {provider} failed")
                debug_print("Webhook delivery", channel=provider, outcome="failed", attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}")
                print_webhook_error(f"HTTP {response.status_code}: {getattr(response, 'text', '')[:200]}")
                return 1
            delay = webhook_retry_after_seconds(response) if response.status_code == 429 else WEBHOOK_FALLBACK_RETRY_SECONDS
            debug_monitor_wait_timing(f"webhook HTTP {response.status_code} retry attempt {attempt_number + 1}/{WEBHOOK_MAX_ATTEMPTS}", delay)
            sleep_func(delay)
        except req.RequestException as exc:
            last_error = exc
            attempt_number = attempt + 1
            debug_print("Webhook delivery", channel=provider, attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}", outcome="failed", error=f"{type(exc).__name__}: {exc}", retryable=attempt < WEBHOOK_MAX_ATTEMPTS - 1)
            if attempt == WEBHOOK_MAX_ATTEMPTS - 1:
                verbose_print(f"Webhook delivery through {provider} failed")
                debug_print("Webhook delivery", channel=provider, outcome="failed", attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}")
                print_webhook_error(exc)
                return 1
            debug_monitor_wait_timing(f"webhook request retry attempt {attempt_number + 1}/{WEBHOOK_MAX_ATTEMPTS}", WEBHOOK_FALLBACK_RETRY_SECONDS)
            sleep_func(WEBHOOK_FALLBACK_RETRY_SECONDS)
    verbose_print(f"Webhook delivery through {provider} failed")
    debug_print("Webhook delivery", channel=provider, outcome="failed", after=f"{WEBHOOK_MAX_ATTEMPTS} attempts")
    print_webhook_error(last_error)
    return 1


# Sends one alert through the independently enabled email and webhook channels
def send_notification_channels(notification_type: str, subject: str, body: str, body_html: str = "", email_enabled: bool = False, webhook_enabled: Optional[bool] = None) -> tuple[bool, bool]:
    email_attempted = bool(email_enabled)
    webhook_attempted = webhook_event_enabled(notification_type) if webhook_enabled is None else bool(webhook_enabled)
    if email_attempted:
        print(f"Sending email notification to {RECEIVER_EMAIL}")
        send_email(subject, body, body_html, SMTP_SSL)
    if webhook_attempted:
        print("Sending webhook notification")
        send_webhook(subject, body, notification_type, force=True)
    return email_attempted, webhook_attempted


# Initializes the CSV file
def init_csv_file(csv_file_name):
    try:
        debug_print("Checking CSV output file", path=csv_file_name)
        if not os.path.isfile(csv_file_name) or os.path.getsize(csv_file_name) == 0:
            debug_print("Opening CSV output for header write", path=csv_file_name)
            with open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
            debug_print("CSV header write succeeded", path=csv_file_name)
    except Exception as e:
        debug_print("CSV initialization", path=csv_file_name, outcome="failed", error=f"{type(e).__name__}: {e}")
        raise RuntimeError(f"Could not initialize CSV file '{csv_file_name}': {sanitize_error_text(e)}")


# Writes CSV entry
def write_csv_entry(csv_file_name, timestamp, object_type, object_name, old, new):
    try:
        debug_print("Opening CSV output for append", path=csv_file_name, record_type=object_type)
        with open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8") as csv_file:
            csvwriter = csv.DictWriter(csv_file, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
            csvwriter.writerow({'Date': timestamp, 'Type': object_type, 'Name': object_name, 'Old': old, 'New': new})
        debug_print("CSV append succeeded", path=csv_file_name, record_type=object_type)
    except Exception as e:
        debug_print("CSV append", path=csv_file_name, record_type=object_type, outcome="failed", error=f"{type(e).__name__}: {e}")
        raise RuntimeError(f"Failed to write to CSV file '{csv_file_name}': {sanitize_error_text(e)}")


# Converts a datetime to local timezone and removes timezone info (naive)
def convert_to_local_naive(dt: datetime | None = None):
    tz = pytz.timezone(LOCAL_TIMEZONE)

    if dt is not None:
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)

        dt_local = dt.astimezone(tz)

        return dt_local.replace(tzinfo=None)
    else:
        return None


# Returns current local time without timezone info (naive)
def now_local_naive():
    return datetime.now(pytz.timezone(LOCAL_TIMEZONE)).replace(microsecond=0, tzinfo=None)


# Returns today's date in LOCAL_TIMEZONE (naive date)
def today_local() -> dt.date:
    return now_local_naive().date()


# Returns the current date/time in human readable format; eg. Sun 21 Apr 2024, 15:08:45
def get_cur_ts(ts_str=""):
    return (f'{ts_str}{calendar.day_abbr[(now_local_naive()).weekday()]} {now_local_naive().strftime("%d %b %Y, %H:%M:%S")}')


# Prints the current date/time in human readable format with separator; eg. Sun 21 Apr 2024, 15:08:45
def print_cur_ts(ts_str=""):
    print(get_cur_ts(str(ts_str)))
    print(f"{'─' * HORIZONTAL_LINE1}\n{'─' * HORIZONTAL_LINE1}")


# Returns the timestamp/datetime object in human readable format (long version); eg. Sun 21 Apr 2024, 15:08:45
def get_date_from_ts(ts):
    tz = pytz.timezone(LOCAL_TIMEZONE)

    if isinstance(ts, str):
        try:
            ts = isoparse(ts)
        except Exception as exc:
            debug_swallowed_exception("Long timestamp parsing", exc)
            return ""

    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = pytz.utc.localize(ts)
        ts_new = ts.astimezone(tz)

    elif isinstance(ts, int):
        ts_new = datetime.fromtimestamp(ts, tz)

    elif isinstance(ts, float):
        ts_rounded = int(round(ts))
        ts_new = datetime.fromtimestamp(ts_rounded, tz)

    else:
        return ""

    return (f'{calendar.day_abbr[ts_new.weekday()]} {ts_new.strftime("%d %b %Y, %H:%M:%S")}')


# Returns the timestamp/datetime object in human readable format (short version); eg.
# Sun 21 Apr 15:08
# Sun 21 Apr 24, 15:08 (if show_year == True and current year is different)
# Sun 21 Apr 25, 15:08 (if always_show_year == True and current year can be the same)
# Sun 21 Apr (if show_hour == False)
# Sun 21 Apr 15:08:32 (if show_seconds == True)
# 21 Apr 15:08 (if show_weekday == False)
def get_short_date_from_ts(ts, show_year=False, show_hour=True, show_weekday=True, show_seconds=False, always_show_year=False):
    tz = pytz.timezone(LOCAL_TIMEZONE)
    if always_show_year:
        show_year = True

    if isinstance(ts, str):
        try:
            ts = isoparse(ts)
        except Exception as exc:
            debug_swallowed_exception("Short timestamp parsing", exc)
            return ""

    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = pytz.utc.localize(ts)
        ts_new = ts.astimezone(tz)

    elif isinstance(ts, int):
        ts_new = datetime.fromtimestamp(ts, tz)

    elif isinstance(ts, float):
        ts_rounded = int(round(ts))
        ts_new = datetime.fromtimestamp(ts_rounded, tz)

    elif isinstance(ts, date):
        ts = datetime.combine(ts, datetime.min.time())
        ts = pytz.utc.localize(ts)
        ts_new = ts.astimezone(tz)

    else:
        return ""

    if show_hour:
        hour_strftime = " %H:%M:%S" if show_seconds else " %H:%M"
    else:
        hour_strftime = ""

    weekday_str = f"{calendar.day_abbr[ts_new.weekday()]} " if show_weekday else ""

    if (show_year and ts_new.year != datetime.now(tz).year) or always_show_year:
        hour_prefix = "," if show_hour else ""
        return f'{weekday_str}{ts_new.strftime(f"%d %b %y{hour_prefix}{hour_strftime}")}'
    else:
        return f'{weekday_str}{ts_new.strftime(f"%d %b{hour_strftime}")}'


# Returns the timestamp/datetime object in human readable format (only hour, minutes and optionally seconds): eg. 15:08:12
def get_hour_min_from_ts(ts, show_seconds=False):
    tz = pytz.timezone(LOCAL_TIMEZONE)

    if isinstance(ts, str):
        try:
            ts = isoparse(ts)
        except Exception as exc:
            debug_swallowed_exception("Hour timestamp parsing", exc)
            return ""

    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = pytz.utc.localize(ts)
        ts_new = ts.astimezone(tz)

    elif isinstance(ts, int):
        ts_new = datetime.fromtimestamp(ts, tz)

    elif isinstance(ts, float):
        ts_rounded = int(round(ts))
        ts_new = datetime.fromtimestamp(ts_rounded, tz)

    else:
        return ""

    out_strf = "%H:%M:%S" if show_seconds else "%H:%M"
    return ts_new.strftime(out_strf)


# Returns the range between two timestamps/datetime objects; eg. Sun 21 Apr 14:09 - 14:15
def get_range_of_dates_from_tss(ts1, ts2, between_sep=" - ", short=False):
    tz = pytz.timezone(LOCAL_TIMEZONE)

    if isinstance(ts1, datetime):
        ts1_new = int(round(ts1.timestamp()))
    elif isinstance(ts1, int):
        ts1_new = ts1
    elif isinstance(ts1, float):
        ts1_new = int(round(ts1))
    else:
        return ""

    if isinstance(ts2, datetime):
        ts2_new = int(round(ts2.timestamp()))
    elif isinstance(ts2, int):
        ts2_new = ts2
    elif isinstance(ts2, float):
        ts2_new = int(round(ts2))
    else:
        return ""

    ts1_strf = datetime.fromtimestamp(ts1_new, tz).strftime("%Y%m%d")
    ts2_strf = datetime.fromtimestamp(ts2_new, tz).strftime("%Y%m%d")

    if ts1_strf == ts2_strf:
        if short:
            out_str = f"{get_short_date_from_ts(ts1_new)}{between_sep}{get_hour_min_from_ts(ts2_new)}"
        else:
            out_str = f"{get_date_from_ts(ts1_new)}{between_sep}{get_hour_min_from_ts(ts2_new, show_seconds=True)}"
    else:
        if short:
            out_str = f"{get_short_date_from_ts(ts1_new)}{between_sep}{get_short_date_from_ts(ts2_new)}"
        else:
            out_str = f"{get_date_from_ts(ts1_new)}{between_sep}{get_date_from_ts(ts2_new)}"

    return str(out_str)


# Checks if the timezone name is correct
def is_valid_timezone(tz_name):
    return tz_name in pytz.all_timezones


# Prints and returns the printed text with new line
def print_v(text=""):
    print(text)
    return text + "\n"


# Signal handler for SIGUSR1 allowing to switch email notifications for user's profile changes
def toggle_profile_changes_notifications_signal_handler(sig, frame):
    global PROFILE_NOTIFICATION
    PROFILE_NOTIFICATION = not PROFILE_NOTIFICATION
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications:\t\t[profile changes = {PROFILE_NOTIFICATION}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGUSR2 allowing to switch email notifications for user's new events
def toggle_new_events_notifications_signal_handler(sig, frame):
    global EVENT_NOTIFICATION
    EVENT_NOTIFICATION = not EVENT_NOTIFICATION
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications:\t\t[new events = {EVENT_NOTIFICATION}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGCONT allowing to switch email notifications for user's repositories changes (except for update date)
def toggle_repo_changes_notifications_signal_handler(sig, frame):
    global REPO_NOTIFICATION
    REPO_NOTIFICATION = not REPO_NOTIFICATION
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications:\t\t[repos changes = {REPO_NOTIFICATION}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGPIPE allowing to switch email notifications for user's repositories update date changes
def toggle_repo_update_date_changes_notifications_signal_handler(sig, frame):
    global REPO_UPDATE_DATE_NOTIFICATION
    REPO_UPDATE_DATE_NOTIFICATION = not REPO_UPDATE_DATE_NOTIFICATION
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications:\t\t[repos update date = {REPO_UPDATE_DATE_NOTIFICATION}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGURG allowing to switch email notifications for user's daily contributions changes
def toggle_contrib_changes_notifications_signal_handler(sig, frame):
    global CONTRIB_NOTIFICATION
    CONTRIB_NOTIFICATION = not CONTRIB_NOTIFICATION
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications:\t\t[contrib changes = {CONTRIB_NOTIFICATION}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGTRAP allowing to increase check timer by GITHUB_CHECK_SIGNAL_VALUE seconds
def increase_check_signal_handler(sig, frame):
    global GITHUB_CHECK_INTERVAL
    GITHUB_CHECK_INTERVAL = GITHUB_CHECK_INTERVAL + GITHUB_CHECK_SIGNAL_VALUE
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* GitHub polling interval:\t[ {display_time(GITHUB_CHECK_INTERVAL)} ]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGABRT allowing to decrease check timer by GITHUB_CHECK_SIGNAL_VALUE seconds
def decrease_check_signal_handler(sig, frame):
    global GITHUB_CHECK_INTERVAL
    if GITHUB_CHECK_INTERVAL - GITHUB_CHECK_SIGNAL_VALUE > 0:
        GITHUB_CHECK_INTERVAL = GITHUB_CHECK_INTERVAL - GITHUB_CHECK_SIGNAL_VALUE
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* GitHub polling interval:\t[ {display_time(GITHUB_CHECK_INTERVAL)} ]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGHUP allowing to reload secrets from .env
def reload_secrets_signal_handler(sig, frame):
    global GITHUB_AUTH_REFRESH_VERSION, WEBHOOK_PROVIDER, SECRET_SOURCES
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")

    # disable autoscan if DOTENV_FILE set to none
    if DOTENV_FILE and DOTENV_FILE.lower() == 'none':
        env_path = None
    else:
        # reload .env if python-dotenv is installed
        try:
            from dotenv import load_dotenv, find_dotenv
            if DOTENV_FILE:
                env_path = DOTENV_FILE
            else:
                env_path = find_dotenv()
            if env_path:
                debug_print("Reading dotenv file for signal reload", path=env_path)
                load_dotenv(env_path, override=True)
                debug_print("Dotenv signal reload succeeded", path=env_path)
            else:
                print("* No .env file found, skipping env-var reload")
        except ImportError as exc:
            debug_swallowed_exception("Dotenv signal reload dependency import", exc)
            env_path = None
            print("* python-dotenv not installed, skipping env-var reload")
        except Exception as exc:
            env_path = None
            verbose_degraded_feature("Private setting reload", "credential refresh", exc)
            print(f"* Dotenv reload failed: {sanitize_error_text(exc)}")

    github_token_changed = False
    webhook_url_changed = False
    if env_path:
        for secret in SECRET_KEYS:
            old_val = globals().get(secret)
            val = os.getenv(secret)
            if val is not None and val != old_val:
                globals()[secret] = val
                SECRET_SOURCES[secret] = "dotenv file reload"
                debug_print("Secret resolution", name=secret, source="dotenv file reload")
                if secret == "GITHUB_TOKEN":
                    github_token_changed = True
                if secret == "WEBHOOK_URL":
                    webhook_url_changed = True
                print(f"* Reloaded {secret} from {env_path}")
    if github_token_changed:
        GITHUB_AUTH_REFRESH_VERSION += 1
    if webhook_url_changed:
        detected_provider = detect_webhook_provider(WEBHOOK_URL)
        if detected_provider and detected_provider != normalized_webhook_provider():
            WEBHOOK_PROVIDER = detected_provider
            print(f"* Updated webhook provider to {detected_provider}")

    print_cur_ts("Timestamp:\t\t\t")


# List subclass used as a safe fallback for paginated responses
class EmptyPaginatedList(list):
    def __init__(self):
        super().__init__()
        self.totalCount = 0


# Creates one timed PyGithub client and records its sanitized connection settings
def create_github_client(operation):
    debug_print("PyGithub client", operation=operation, endpoint=diagnostic_endpoint(GITHUB_API_URL), timeout=f"{PYGITHUB_TIMEOUT_SECONDS}s", token=mask_secret(GITHUB_TOKEN))
    return Github(base_url=GITHUB_API_URL, auth=Auth.Token(GITHUB_TOKEN), timeout=PYGITHUB_TIMEOUT_SECONDS, verify=VERIFY_SSL)


# Logs one named PyGithub operation before its lazy network request is consumed
def debug_github_operation(operation, target=""):
    suffix = f" target={target}" if target else ""
    debug_print("PyGithub", operation=operation, endpoint=diagnostic_endpoint(GITHUB_API_URL), timeout=f"{PYGITHUB_TIMEOUT_SECONDS}s", token=f"{mask_secret(GITHUB_TOKEN)}{suffix}")


# Returns a stable display name for a partially populated PyGithub object
def github_object_name(value):
    return str(getattr(value, "full_name", getattr(value, "name", "resource")))


# Callers wrap a lambda and invoke the result immediately, so a lambda that reads a loop variable is
# evaluated inside the same iteration. Those call sites carry a noqa marker for the loop-binding rule
# Wraps GitHub API call with retry and linear back-off, returning a specified default on failure
def gh_call(fn: Callable[..., Any], retries=NET_MAX_RETRIES, backoff=NET_BASE_BACKOFF_SEC, default: Any = None,) -> Callable[..., Any]:
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        for i in range(1, retries + 1):
            try:
                debug_print("PyGithub retry wrapper", operation=fn.__name__, attempt=f"{i}/{retries}")
                result = fn(*args, **kwargs)
                debug_print("PyGithub retry wrapper", operation=fn.__name__, outcome="OK", attempt=f"{i}/{retries}")
                return result
            except RateLimitExceededException as e:
                headers = getattr(e, "headers", None)

                reset_str = None
                if headers:
                    val = headers.get("X-RateLimit-Reset")
                    if isinstance(val, str):
                        reset_str = val

                sleep_for: int
                if reset_str is not None and reset_str.isdigit():
                    reset_epoch = int(reset_str)
                    sleep_for = max(0, reset_epoch - int(time.time()) + 1)
                else:
                    retry_after_str = None
                    if headers:
                        ra = headers.get("Retry-After")
                        if isinstance(ra, str):
                            retry_after_str = ra
                    if retry_after_str is not None and retry_after_str.isdigit():
                        sleep_for = int(retry_after_str)
                    else:
                        sleep_for = int(backoff * i)

                retryable = i < retries
                debug_print("PyGithub retry wrapper", operation=fn.__name__, outcome="failed", error=f"{type(e).__name__}: {e}", retryable=retryable, attempt=f"{i}/{retries}")
                if retryable:
                    print(f"* {fn.__name__} rate limited, sleeping {sleep_for}s (retry {i}/{retries})")
                    debug_monitor_wait_timing(f"GitHub rate limit before attempt {i + 1}/{retries}", sleep_for)
                    time.sleep(sleep_for)
                continue

            except NET_ERRORS as e:
                retryable = i < retries
                delay = backoff * i
                debug_print("PyGithub retry wrapper", operation=fn.__name__, outcome="failed", error=f"{type(e).__name__}: {e}", retryable=retryable, attempt=f"{i}/{retries}")
                if retryable:
                    print(f"* {fn.__name__} error: {sanitize_error_text(e)} (retry {i}/{retries})")
                    debug_monitor_wait_timing(f"GitHub request retry attempt {i + 1}/{retries}", delay)
                    time.sleep(delay)
        verbose_degraded_feature(f"GitHub operation {fn.__name__}", "its dependent alerts")
        debug_print("PyGithub retry wrapper", operation=fn.__name__, outcome="default", after=f"{retries} attempts")
        return default
    return wrapped


# Prints followers and followings for a GitHub user (-f)
def github_print_followers_and_followings(user):
    user_name_str = user
    user_url = "-"
    followers_count = 0
    followings_count = 0
    followers_list = []
    followings_list = []

    print(f"* Getting followers & followings for user '{user}' ...")

    try:
        g = create_github_client("followers and followings listing")

        debug_github_operation("user profile lookup", user)
        g_user = g.get_user(user)
        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url

        followers_count = g_user.followers
        followings_count = g_user.following

        debug_github_operation("followers listing", user)
        followers_list = g_user.get_followers()
        debug_github_operation("followings listing", user)
        followings_list = g_user.get_following()

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except (UnknownObjectException, BadCredentialsException, RateLimitExceededException):
        raise
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user {user} details: {sanitize_error_text(e)}")

    print(f"\nUsername:\t\t{user_name_str}")
    print(f"User URL:\t\t{user_url}/")
    print(f"GitHub API URL:\t\t{GITHUB_API_URL}")
    print(f"Local timezone:\t\t{LOCAL_TIMEZONE}")

    print(f"\nFollowers:\t\t{followers_count}")

    try:
        if followers_list:

            for follower in followers_list:
                follower_str = f"\n- {follower.login}"
                if follower.name:
                    follower_str += f" ({follower.name})"
                if follower.html_url:
                    follower_str += f"\n[ {follower.html_url}/ ]"
                print(follower_str)
    except Exception as e:
        verbose_degraded_feature("Follower listing", "complete follower output", e)
        print(f"* Cannot fetch user's followers list: {sanitize_error_text(e)}")

    print(f"\nFollowings:\t\t{followings_count}")

    try:
        if followings_list:

            for following in followings_list:
                following_str = f"\n- {following.login}"
                if following.name:
                    following_str += f" ({following.name})"
                if following.html_url:
                    following_str += f"\n[ {following.html_url}/ ]"
                print(following_str)
    except Exception as e:
        verbose_degraded_feature("Following listing", "complete following output", e)
        print(f"* Cannot fetch user's followings list: {sanitize_error_text(e)}")

    g.close()


# Displays a progress bar with percentage and current repo name
def _display_progress(current, total, repo_name: str = "", bar_length: int = 40, is_final: bool = False) -> None:
    if total == 0:
        return

    # Defensive fallback for environments without a real TTY
    try:
        term_width = shutil.get_terminal_size(fallback=(80, 20)).columns
    except Exception as exc:
        debug_swallowed_exception("Terminal width detection", exc)
        term_width = 80

    # Keep a sane minimum – very tiny terminals may still wrap, but that's acceptable
    term_width = max(40, term_width)

    percent = float(current) / total
    percent_str = f"{percent * 100:.1f}%"
    counter_str = f"({current}/{total})"

    # Prepare (possibly truncated) repo name
    display_name = repo_name or ""
    max_name_length = 30
    if display_name and len(display_name) > max_name_length:
        display_name = display_name[:max_name_length] + "..."

    prefix = "Repos"
    name_part = f" - {display_name}" if display_name else ""

    # First, assume we can show prefix + name; compute max bar length that fits
    def compute_bar_len(include_prefix: bool, include_name: bool) -> int:
        base = ""
        if include_prefix:
            base += prefix + " "
        base += "[]"  # placeholder for bar
        base += f" {percent_str} {counter_str}"
        if include_name and name_part:
            base += name_part
        # Leave 1 char margin
        available = term_width - len(base) - 1
        return available

    max_bar_len = compute_bar_len(include_prefix=True, include_name=True)
    show_prefix = True
    show_name = True

    if max_bar_len < 10:
        # Try without repo name
        show_name = False
        max_bar_len = compute_bar_len(include_prefix=True, include_name=False)

    if max_bar_len < 5:
        # Try without prefix as well
        show_prefix = False
        max_bar_len = compute_bar_len(include_prefix=False, include_name=False)

    # Final bar length: at least 3 chars, at most requested bar_length
    bar_len = max(3, min(bar_length, max_bar_len if max_bar_len > 0 else bar_length))

    filled_length = int(bar_len * percent)
    bar = "█" * filled_length + "░" * (bar_len - filled_length)

    parts = []
    if show_prefix:
        parts.append(prefix)
    parts.append(f"[{bar}]")
    parts.append(percent_str)
    parts.append(counter_str)
    if show_name and name_part:
        parts.append(name_part.lstrip())

    progress_str = " ".join(parts)

    terminal_out = stdout_bck if stdout_bck is not None else sys.stdout
    while isinstance(terminal_out, (Logger, TerminalStream)):
        terminal_out = terminal_out.terminal
    progress_str = ANSI_ESCAPE_RE.sub("", sanitize_terminal_text(progress_str))
    previous_width = getattr(_display_progress, "width", 0)
    padded_progress = progress_str + (" " * max(0, previous_width - len(progress_str)))
    _display_progress.width = len(progress_str)

    if is_final:
        terminal_out.write("\r" + padded_progress)
        terminal_out.flush()

        if stdout_bck is not None and isinstance(sys.stdout, Logger):
            sys.stdout.logfile.write(progress_str + "\n")
            sys.stdout.logfile.flush()
    else:
        terminal_out.write("\r" + padded_progress)
        terminal_out.flush()


# Returns open repository discussions as a count and formatted list
def github_get_repo_discussions(repo):
    if not repo.has_discussions:
        return 0, []

    discussion_schema = "id number title createdAt updatedAt author { login } category { name }"
    debug_github_operation("repository discussions listing", getattr(repo, "full_name", getattr(repo, "name", "repository")))
    discussions = list(repo.get_discussions(discussion_schema, states=["OPEN"]))
    discussions_list = [f"#{discussion.number} {discussion.title} ({discussion.author.login if discussion.author else 'ghost'}) [ {repo.html_url}/discussions/{discussion.number} ]" for discussion in discussions]
    return len(discussions), discussions_list


# Processes items from all passed repositories and returns a list of dictionaries
def github_process_repos(repos_list, show_progress=True, fetch_identity_lists=True):
    import logging
    import warnings

    # Suppress urllib3 warnings that might interfere with progress bar
    urllib3.disable_warnings()
    warnings.filterwarnings('ignore')

    list_of_repos = []
    identity_lists_fetched = 0
    if repos_list:
        # Convert to list if it's a generator/iterator to get total count
        repos_list = list(repos_list)
        total_repos = len(repos_list)

        for idx, repo in enumerate(repos_list, 1):
            stargazers_list = None
            subscribers_list = None
            forked_repos = []
            discussion_count = None
            discussions_list = None

            # Update progress bar at start
            if show_progress:
                _display_progress(idx, total_repos, repo.name)
            try:
                repo_created_date = repo.created_at
                repo_updated_date = repo.updated_at

                github_logger = logging.getLogger('github')
                original_level = github_logger.level
                github_logger.setLevel(logging.ERROR)

                try:
                    if fetch_identity_lists:
                        debug_github_operation("repository stargazers listing", github_object_name(repo))
                        stargazers_list = [star.login for star in repo.get_stargazers()]
                        if show_progress:
                            _display_progress(idx, total_repos, repo.name)  # Refresh after stargazers
                        debug_github_operation("repository subscribers listing", github_object_name(repo))
                        subscribers_list = [subscriber.login for subscriber in repo.get_subscribers()]
                        identity_lists_fetched += 1
                        if show_progress:
                            _display_progress(idx, total_repos, repo.name)  # Refresh after subscribers
                    debug_github_operation("repository forks listing", github_object_name(repo))
                    forked_repos = [fork.full_name for fork in repo.get_forks()]
                    if show_progress:
                        _display_progress(idx, total_repos, repo.name)  # Refresh after forks
                except GithubException as e:
                    if e.status in [403, 451]:
                        verbose_degraded_feature(f"Repository details for {repo.name}", "repository change alerts", e)
                        if BLOCKED_REPOS:
                            print(f"\n* Repo '{repo.name}' is blocked, skipping for now: {sanitize_error_text(e)}")
                            print_cur_ts("Timestamp:\t\t\t")
                        if show_progress:
                            _display_progress(idx, total_repos, repo.name)
                        continue
                    raise
                finally:
                    github_logger.setLevel(original_level)

                debug_github_operation("repository open issues listing", github_object_name(repo))
                issues = list(repo.get_issues(state='open'))
                if show_progress:
                    _display_progress(idx, total_repos, repo.name)  # Refresh after issues
                debug_github_operation("repository open pull requests listing", github_object_name(repo))
                pulls = list(repo.get_pulls(state='open'))
                if show_progress:
                    _display_progress(idx, total_repos, repo.name)  # Refresh after pulls
                try:
                    discussion_count, discussions_list = github_get_repo_discussions(repo)
                except Exception as e:
                    verbose_degraded_feature(f"Discussions for {repo.name}", "discussion change alerts", e)
                    print(f"\n* Cannot fetch discussions for repo '{repo.name}', skipping discussions for now: {sanitize_error_text(e)}")
                if show_progress:
                    _display_progress(idx, total_repos, repo.name)  # Refresh after discussions

                real_issues = [i for i in issues if not i.pull_request]
                issue_count = len(real_issues)
                pr_count = len(pulls)

                issues_list = [f"#{i.number} {i.title} ({i.user.login}) [ {i.html_url} ]" for i in real_issues]
                pr_list = [f"#{pr.number} {pr.title} ({pr.user.login}) [ {pr.html_url} ]" for pr in pulls]

                list_of_repos.append({"name": repo.name, "descr": repo.description, "is_fork": repo.fork, "forks": repo.forks_count, "stars": repo.stargazers_count, "subscribers": repo.subscribers_count, "url": repo.html_url, "language": repo.language, "date": repo_created_date, "update_date": repo_updated_date, "stargazers_list": stargazers_list, "forked_repos": forked_repos, "subscribers_list": subscribers_list, "issues": issue_count, "pulls": pr_count, "discussions": discussion_count, "issues_list": issues_list, "pulls_list": pr_list, "discussions_list": discussions_list})
                if show_progress:
                    _display_progress(idx, total_repos, repo.name, is_final=(idx == total_repos))  # Final refresh after successful processing

            except GithubException as e:
                # Skip TOS-blocked (403) and legally blocked (451) repositories
                if e.status in [403, 451]:
                    verbose_degraded_feature(f"Repository details for {repo.name}", "repository change alerts", e)
                    if BLOCKED_REPOS:
                        print(f"\n* Repo '{repo.name}' is blocked, skipping for now: {sanitize_error_text(e)}")
                        print_cur_ts("Timestamp:\t\t\t")
                    if show_progress:
                        _display_progress(idx, total_repos, repo.name, is_final=(idx == total_repos))
                    continue
                else:
                    verbose_degraded_feature(f"Repository details for {repo.name}", "repository change alerts", e)
                    print(f"\n* Cannot process repo '{repo.name}', skipping for now: {sanitize_error_text(e)}")
                    print_cur_ts("Timestamp:\t\t\t")
                    if show_progress:
                        _display_progress(idx, total_repos, repo.name, is_final=(idx == total_repos))
                    continue
            except Exception as e:
                verbose_degraded_feature(f"Repository details for {repo.name}", "repository change alerts", e)
                print(f"\n* Cannot process repo '{repo.name}', skipping for now: {sanitize_error_text(e)}")
                print_cur_ts("Timestamp:\t\t\t")
                if show_progress:
                    _display_progress(idx, total_repos, repo.name, is_final=(idx == total_repos))
                continue

        # Clear progress bar and move to next line (only if progress was shown)
        if show_progress and total_repos > 0:
            # Write newline to terminal
            terminal_out = stdout_bck if stdout_bck is not None else sys.stdout
            terminal_out.write("\n")
            terminal_out.flush()
            # Also write to log file if logging is enabled
            if stdout_bck is not None and isinstance(sys.stdout, Logger):
                sys.stdout.logfile.write("\n")
                sys.stdout.logfile.flush()

            print()
            if fetch_identity_lists:
                repo_label = "repository" if total_repos == 1 else "repositories"
                print(f"- Stargazer/watcher user lists:\tFetched for {identity_lists_fetched}/{total_repos} {repo_label}")
            else:
                print("- Stargazer/watcher user lists:\tSkipped (counts only)")

    return list_of_repos


# Prints a list of public repositories for a GitHub user (-r)
def github_print_repos(user):
    import logging
    user_name_str = user
    user_url = "-"
    repos_count = 0
    repos_list = []

    print(f"* Getting public repositories for user '{user}' ...")

    try:
        g = create_github_client("repository listing")

        debug_github_operation("user profile lookup", user)
        g_user = g.get_user(user)
        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url

        if GET_ALL_REPOS:
            debug_github_operation("all repository listing", user)
            repos_list = g_user.get_repos()
            repos_count = g_user.public_repos
        else:
            debug_github_operation("owned repository listing", user)
            repos_list = [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login]
            repos_count = len(repos_list)

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except (UnknownObjectException, BadCredentialsException, RateLimitExceededException):
        raise
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user {user} details: {sanitize_error_text(e)}")

    print(f"\nUsername:\t\t{user_name_str}")
    print(f"User URL:\t\t{user_url}/")
    print(f"GitHub API URL:\t\t{GITHUB_API_URL}")
    print(f"Owned repos only:\t{not GET_ALL_REPOS}")
    print(f"Local timezone:\t\t{LOCAL_TIMEZONE}")

    print(f"\nRepositories:\t\t{repos_count}\n")

    try:
        if repos_list:
            print("─" * HORIZONTAL_LINE2)
            for repo in repos_list:
                print(f"🔸 {repo.name} {'(fork)' if repo.fork else ''} \n")

                github_logger = logging.getLogger('github')
                original_level = github_logger.level
                github_logger.setLevel(logging.ERROR)

                try:
                    debug_github_operation("repository open pull request count", github_object_name(repo))
                    pr_count = repo.get_pulls(state='open').totalCount
                    issue_count = repo.open_issues_count - pr_count
                except Exception as exc:
                    verbose_degraded_feature(f"Repository counts for {repo.name}", "repository count details", exc)
                    pr_count = "?"
                    issue_count = "?"

                try:
                    print(f" - 🌐 URL:\t\t{repo.html_url}")
                    print(f" - 💻 Language:\t\t{repo.language}")

                    print(f"\n - ⭐ Stars:\t\t{repo.stargazers_count}")
                    print(f" - 🍴 Forks:\t\t{repo.forks_count}")
                    print(f" - 👓 Watchers:\t\t{repo.subscribers_count}")

                    # print(f" - 🐞 Issues+PRs:\t{repo.open_issues_count}")
                    print(f" - 🐞 Issues:\t\t{issue_count}")
                    print(f" - 📬 PRs:\t\t{pr_count}")

                    print(f"\n - 📝 License:\t\t{repo.license.name if repo.license else 'None'}")
                    print(f" - 🌿 Branch (default):\t{repo.default_branch}")

                    print(f"\n - 📅 Created:\t\t{get_date_from_ts(repo.created_at)} ({calculate_timespan(int(time.time()), repo.created_at, granularity=2)} ago)")
                    print(f" - 🔄 Updated:\t\t{get_date_from_ts(repo.updated_at)} ({calculate_timespan(int(time.time()), repo.updated_at, granularity=2)} ago)")
                    print(f" - 🔃 Last push:\t{get_date_from_ts(repo.pushed_at)} ({calculate_timespan(int(time.time()), repo.pushed_at, granularity=2)} ago)")

                    if repo.description:
                        print(f"\n - 📝 Desc:\t\t{repo.description}")
                except GithubException as e:
                    # Inform about TOS-blocked (403) and legally blocked (451) repositories
                    if e.status in [403, 451]:
                        verbose_degraded_feature(f"Repository details for {repo.name}", "complete repository output", e)
                        print(f"\n* Repo '{repo.name}' is blocked: {sanitize_error_text(e)}")
                        print("─" * HORIZONTAL_LINE2)
                        continue
                finally:
                    github_logger.setLevel(original_level)

                print("─" * HORIZONTAL_LINE2)
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user's repositories list: {sanitize_error_text(e)}")

    g.close()


# Prints a list of starred repositories by a GitHub user (-g)
def github_print_starred_repos(user):
    user_name_str = user
    user_url = "-"
    starred_count = 0
    starred_list = []

    print(f"* Getting repositories starred by user '{user}' ...")

    try:
        g = create_github_client("starred repository listing")

        debug_github_operation("user profile lookup", user)
        g_user = g.get_user(user)
        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url

        debug_github_operation("starred repository listing", user)
        starred_list = g_user.get_starred()
        starred_count = starred_list.totalCount

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except (UnknownObjectException, BadCredentialsException, RateLimitExceededException):
        raise
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user {user} details: {sanitize_error_text(e)}")

    print(f"\nUsername:\t\t{user_name_str}")
    print(f"User URL:\t\t{user_url}/")
    print(f"GitHub API URL:\t\t{GITHUB_API_URL}")
    print(f"Local timezone:\t\t{LOCAL_TIMEZONE}")

    print(f"\nRepos starred by user:\t{starred_count}")

    try:
        if starred_list:
            for star in starred_list:
                star_str = f"\n- {star.full_name}"
                if star.html_url:
                    star_str += f" [ {star.html_url}/ ]"
                print(star_str)
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user's starred list: {sanitize_error_text(e)}")

    g.close()


# Returns size in human readable format
def human_readable_size(num):
    value = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


# Formats the given string as a quoted, indented block
def format_body_block(content, indent="    "):
    new_content = f"'{content}'"
    indented = textwrap.indent(new_content.strip(), indent)
    return f"\n{indented}"


# Returns the base web URL for GitHub or GHE (e.g. https://github.com or https://ghe.example.com)
def github_web_base() -> str:
    if "api.github.com" in GITHUB_API_URL:
        return "https://github.com"
    return GITHUB_API_URL.replace("/api/v3", "").rstrip("/")


# Safely truncates text without breaking HTML tags
def safe_truncate_text(text, max_length=MAX_EVENT_BODY_LENGTH):
    if len(text) <= max_length:
        return text

    # Find a safe truncation point - look backwards from max_length
    truncate_at = max_length

    # Check if we're in the middle of an HTML tag by looking backwards
    for i in range(max_length - 1, max(0, max_length - 200), -1):
        if text[i] == '<':
            # Found start of a tag - check if it completes before max_length
            tag_end = text.find('>', i)
            if tag_end != -1 and tag_end < max_length:
                # Tag completes before truncation point, safe to truncate after it
                truncate_at = tag_end + 1
                break
            else:
                # Tag doesn't complete, truncate before it to avoid breaking the tag
                truncate_at = i
                break
        elif text[i] == '>':
            # Found end of a tag, safe to truncate after it
            truncate_at = i + 1
            break

    # Truncate at the safe point
    truncated = text[:truncate_at]

    # Find and close any open HTML tags
    open_tags = []
    tag_pattern = r'<(/)?([a-zA-Z][a-zA-Z0-9]*)[^>]*>'

    for match in re.finditer(tag_pattern, truncated):
        is_closing = match.group(1) == '/'
        tag_name = match.group(2).lower()

        if is_closing:
            # Remove matching opening tag
            if open_tags and open_tags[-1] == tag_name:
                open_tags.pop()
        else:
            # Self-closing tags don't need closing
            if tag_name not in ('img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'):
                open_tags.append(tag_name)

    # Close any remaining open tags in reverse order
    result = truncated
    for tag in reversed(open_tags):
        result += f'</{tag}>'

    result += " ... <cut>"
    return result


# Prints details about passed GitHub event
def github_print_event(event, g, time_passed=False, ts: datetime | None = None):

    event_date: datetime | None = None
    repo_name = ""
    repo_url = ""
    st = ""
    tp = ""
    repo = None

    event_date = event.created_at
    if time_passed and not ts:
        tp = f" ({calculate_timespan(int(time.time()), event_date, show_seconds=False, granularity=2)} ago)"
    elif time_passed and ts:
        # Only show "after" if current event is newer than previous event
        if event_date and ts and event_date > ts:
            tp = f" (after {calculate_timespan(event_date, ts, show_seconds=False, granularity=2)}: {get_short_date_from_ts(ts)})"
        else:
            tp = ""
    st += print_v(f"Event date:\t\t\t{get_date_from_ts(event_date)}{tp}")
    st += print_v(f"Event ID:\t\t\t{event.id}")
    st += print_v(f"Event type:\t\t\t{event.type}")

    if event.repo.id:
        try:
            desc_len = 80
            debug_github_operation("event repository lookup", event.repo.name)
            repo = g.get_repo(event.repo.name)

            # For ForkEvent, prefer the source repo if available
            if event.type == "ForkEvent" and repo is not None:
                try:
                    parent = gh_call(lambda: getattr(repo, "parent", None))()
                    if parent:
                        repo = parent
                except Exception as exc:
                    verbose_degraded_feature("Fork source repository metadata", "complete fork event details", exc)

            repo_name = getattr(repo, "full_name", event.repo.name)

            api_prefix = GITHUB_API_URL.rstrip("/") + "/repos/"
            repo_url = getattr(repo, "html_url", event.repo.url.replace(api_prefix, github_web_base() + "/"))

            st += print_v(f"\nRepo name:\t\t\t{repo_name}")
            st += print_v(f"Repo URL:\t\t\t{repo_url}")

            desc = (repo.description or "") if repo else ""
            cleaned = desc.replace('\n', ' ')
            short_desc = cleaned[:desc_len] + '...' if len(cleaned) > desc_len else cleaned
            if short_desc:
                st += print_v(f"Repo description:\t\t{short_desc}")

        except UnknownObjectException as exc:
            debug_swallowed_exception("Event repository lookup", exc)
            repo = None
            st += print_v("\nRepository not found or has been removed")
        except GithubException as e:
            debug_swallowed_exception("Event repository lookup", e)
            repo = None
            st += print_v(f"\n* Error occurred while getting repo details: {sanitize_error_text(e)}")

    if hasattr(event.actor, 'login'):
        if event.actor.login:
            st += print_v(f"\nEvent actor login:\t\t{event.actor.login}")
    if hasattr(event.actor, 'name'):
        if event.actor.name:
            st += print_v(f"Event actor name:\t\t{event.actor.name}")
    if hasattr(event.actor, 'html_url'):
        if event.actor.html_url:
            st += print_v(f"Event actor URL:\t\t{event.actor.html_url}")

    if event.payload.get("ref"):
        st += print_v(f"\nObject name:\t\t\t{event.payload.get('ref')}")
    if event.payload.get("ref_type"):
        st += print_v(f"Object type:\t\t\t{event.payload.get('ref_type')}")
    if event.payload.get("description"):
        st += print_v(f"Description:\t\t\t{event.payload.get('description')}")

    if event.payload.get("action"):
        st += print_v(f"\nAction:\t\t\t\t{event.payload.get('action')}")

    # Prefer commits from payload when present (older API behavior)
    if event.payload.get("commits"):
        commits = event.payload["commits"]
        commits_total = len(commits)
        st += print_v(f"\nNumber of commits:\t\t{commits_total}")
        for commit_count, commit in enumerate(commits, start=1):
            st += print_v(f"\n=== Commit {commit_count}/{commits_total} ===")
            st += print_v("." * HORIZONTAL_LINE1)

            commit_message = commit['message']
            is_multiline = '\n' in commit_message
            if is_multiline:
                first_line = commit_message.split('\n', 1)[0]
                st += print_v(f" - Commit message:\t\t'{first_line}...'")
            else:
                st += print_v(f" - Commit message:\t\t'{commit_message}'")

            commit_details = None
            if repo:
                debug_github_operation("event commit lookup", commit["sha"])
                commit_details = gh_call(lambda: repo.get_commit(commit["sha"]))()  # noqa: B023

            if commit_details:
                commit_date = commit_details.commit.author.date
                st += print_v(f" - Commit date:\t\t\t{get_date_from_ts(commit_date)}")

            st += print_v(f" - Commit SHA:\t\t\t{commit['sha']}")
            st += print_v(f" - Commit author:\t\t{commit['author']['name']}")

            if commit_details and commit_details.author:
                st += print_v(f" - Commit author URL:\t\t{commit_details.author.html_url}")

            if commit_details:
                st += print_v(f" - Commit URL:\t\t\t{commit_details.html_url}")
                st += print_v(f" - Commit raw patch URL:\t{commit_details.html_url}.patch")

            stats = getattr(commit_details, "stats", None)
            additions = stats.additions if stats else 0
            deletions = stats.deletions if stats else 0
            stats_total = stats.total if stats else 0
            st += print_v(f"\n - Additions/Deletions:\t\t+{additions} / -{deletions} ({stats_total})")

            if commit_details:
                try:
                    file_count = sum(1 for _ in commit_details.files)
                except Exception as exc:
                    verbose_degraded_feature("Commit file list", "complete push event details", exc)
                    file_count = "N/A"
                st += print_v(f" - Files changed:\t\t{file_count}")
                if file_count:
                    st += print_v(f" - Changed files list:")
                    for f in commit_details.files:
                        st += print_v(f"     • '{f.filename}' - {f.status} (+{f.additions} / -{f.deletions})")

            if is_multiline:
                st += print_v(f"\n - Commit full message:")
                st += print_v(f"\n'{commit_message}'")
            else:
                pass
            st += print_v("." * HORIZONTAL_LINE1)

    # Fallback for new Events API where PushEvent no longer includes commit summaries
    elif event.type == "PushEvent" and repo:
        before_sha = event.payload.get("before")
        head_sha = event.payload.get("head") or event.payload.get("after")

        # Debug when payload has no commits
        # st += print_v("\n[debug] PushEvent payload has no 'commits' array; using compare API")
        # st += print_v(f"[debug] before:\t\t\t{before_sha}")
        # st += print_v(f"[debug] head/after:\t\t{head_sha}")
        # if size_hint is not None:
        #     st += print_v(f"[debug] size (hint):\t\t{size_hint}")

        if before_sha and head_sha and before_sha != head_sha:
            try:
                compare = gh_call(lambda: repo.compare(before_sha, head_sha))()
            except Exception as e:
                verbose_degraded_feature("Push comparison", "complete push event details", e)
                compare = None
                st += print_v(f"* Error using compare({before_sha[:12]}...{head_sha[:12]}): {sanitize_error_text(e)}")

            if compare:
                commits = list(compare.commits)
                commits_total = len(commits)
                short_repo = getattr(repo, "full_name", repo_name)
                compare_url = f"{github_web_base()}/{short_repo}/compare/{before_sha[:12]}...{head_sha[:12]}"
                st += print_v(f"\nNumber of commits:\t\t{commits_total}")
                st += print_v(f"Compare URL:\t\t\t{compare_url}")

                for commit_count, c in enumerate(commits, start=1):
                    st += print_v(f"\n=== Commit {commit_count}/{commits_total} ===")
                    st += print_v("." * HORIZONTAL_LINE1)

                    commit_sha = getattr(c, "sha", None) or getattr(c, "id", None)
                    if repo and commit_sha:
                        debug_github_operation("event commit lookup", commit_sha)
                    commit_details = gh_call(lambda: repo.get_commit(commit_sha))() if (repo and commit_sha) else None  # noqa: B023

                    commit_message = commit_details.commit.message if commit_details and commit_details.commit else ""
                    is_multiline = '\n' in commit_message if commit_message else False
                    if commit_message:
                        if is_multiline:
                            first_line = commit_message.split('\n', 1)[0]
                            st += print_v(f" - Commit message:\t\t'{first_line}...'")
                        else:
                            st += print_v(f" - Commit message:\t\t'{commit_message}'")

                    if commit_details:
                        commit_date = commit_details.commit.author.date
                        st += print_v(f" - Commit date:\t\t\t{get_date_from_ts(commit_date)}")

                    if commit_sha:
                        st += print_v(f" - Commit SHA:\t\t\t{commit_sha}")

                    author_name = None
                    if commit_details and commit_details.commit and commit_details.commit.author:
                        author_name = commit_details.commit.author.name
                    st += print_v(f" - Commit author:\t\t{author_name or 'N/A'}")

                    if commit_details and commit_details.author:
                        st += print_v(f" - Commit author URL:\t\t{commit_details.author.html_url}")

                    if commit_details:
                        st += print_v(f" - Commit URL:\t\t\t{commit_details.html_url}")
                        st += print_v(f" - Commit raw patch URL:\t{commit_details.html_url}.patch")

                        stats = getattr(commit_details, "stats", None)
                        additions = stats.additions if stats else 0
                        deletions = stats.deletions if stats else 0
                        stats_total = stats.total if stats else 0
                        st += print_v(f"\n - Additions/Deletions:\t\t+{additions} / -{deletions} ({stats_total})")

                        try:
                            file_count = sum(1 for _ in commit_details.files)
                        except Exception as exc:
                            verbose_degraded_feature("Commit file list", "complete push event details", exc)
                            file_count = "N/A"
                        st += print_v(f" - Files changed:\t\t{file_count}")
                        if file_count and file_count != "N/A":
                            st += print_v(" - Changed files list:")
                            for f in commit_details.files:
                                st += print_v(f"     • '{f.filename}' - {f.status} (+{f.additions} / -{f.deletions})")

                        if is_multiline and commit_message:
                            st += print_v(f"\n - Commit full message:")
                            st += print_v(f"\n'{commit_message}'")

                        st += print_v("." * HORIZONTAL_LINE1)
        else:
            st += print_v("\nNo compare range available (forced push, tag push, or identical before/after)")

    if event.payload.get("commits") == []:
        st += print_v("\nNo new commits (forced push, tag push, branch reset or other ref update)")

    if event.payload.get("release"):
        st += print_v(f"\nRelease name:\t\t\t{event.payload['release'].get('name')}")
        st += print_v(f"Release tag name:\t\t{event.payload['release'].get('tag_name')}")
        st += print_v(f"Release URL:\t\t\t{event.payload['release'].get('html_url')}")

        st += print_v(f"\nPublished by:\t\t\t{event.payload['release']['author']['login']}")
        if event.payload['release']['author'].get('html_url'):
            st += print_v(f"Published by URL:\t\t{event.payload['release']['author']['html_url']}")
        if event.payload['release'].get('published_at'):
            pub_ts = event.payload['release']['published_at']
            st += print_v(f"Published at:\t\t\t{get_date_from_ts(pub_ts)}")
        st += print_v(f"Target commitish:\t\t{event.payload['release'].get('target_commitish')}")
        st += print_v(f"Draft:\t\t\t\t{event.payload['release'].get('draft')}")
        st += print_v(f"Prerelease:\t\t\t{event.payload['release'].get('prerelease')}")

        if event.payload["release"].get("assets"):
            print()
            st += print_v("\nAssets:\n")
            assets = event.payload['release'].get('assets', [])
            for asset in assets:
                size_bytes = asset.get("size", 0)
                st += print_v(f" - Asset name:\t\t\t{asset.get('name')}")
                st += print_v(f" - Asset size:\t\t\t{human_readable_size(size_bytes)}")
                st += print_v(f" - Download URL:\t\t{asset.get('browser_download_url')}")
                if asset != assets[-1]:
                    st += print_v()

        st += print_v(f"\nRelease notes:\n\n'{event.payload['release'].get('body')}'")

    if repo and event.payload.get("pull_request"):
        pr_number = event.payload["pull_request"]["number"]
        debug_github_operation("event pull request lookup", f"{github_object_name(repo)}#{pr_number}")
        pr = repo.get_pull(pr_number)

        st += print_v(f"\n=== PR #{pr.number}: {pr.title} ===")
        st += print_v("." * HORIZONTAL_LINE1)

        st += print_v(f"Author:\t\t\t\t{pr.user.login}")
        st += print_v(f"Author URL:\t\t\t{pr.user.html_url}")
        st += print_v(f"State:\t\t\t\t{pr.state}")
        st += print_v(f"Merged:\t\t\t\t{pr.merged}")
        st += print_v(f"PR URL:\t\t\t\t{pr.html_url}")

        if pr.created_at:
            pr_created_date = get_date_from_ts(pr.created_at)
            st += print_v(f"Created at:\t\t\t{pr_created_date}")
        if pr.closed_at:
            pr_closed_date = get_date_from_ts(pr.closed_at)
            st += print_v(f"Closed at:\t\t\t{pr_closed_date}")
        if pr.merged_at:
            pr_merged_date = get_date_from_ts(pr.merged_at)
            st += print_v(f"Merged at:\t\t\t{pr_merged_date} by {pr.merged_by.login}")

        st += print_v(f"Head → Base:\t\t\t{pr.head.ref} → {pr.base.ref}")
        st += print_v(f"Mergeable state:\t\t{pr.mergeable_state}")

        if pr.labels:
            st += print_v(f"Labels:\t\t\t\t{', '.join(label.name for label in pr.labels)}")

        st += print_v(f"\nCommits:\t\t\t{pr.commits}")
        st += print_v(f"Comments (issue/review):\t{pr.comments} / {pr.review_comments}")

        st += print_v(f"Additions/Deletions:\t\t+{pr.additions} / -{pr.deletions}")
        st += print_v(f"Files changed:\t\t\t{pr.changed_files}")

        if pr.body:
            st += print_v(f"\nPR description:\n\n'{pr.body.strip()}'")

        if pr.requested_reviewers:
            for reviewer in pr.requested_reviewers:
                st += print_v(f"\n - Requested reviewer:\t{reviewer.login} ({reviewer.html_url})")

        if pr.assignees:
            for assignee in pr.assignees:
                st += print_v(f"\nAssignee:\t\t\t{assignee.login} ({assignee.html_url})")

        st += print_v("." * HORIZONTAL_LINE1)

    if event.payload.get("review"):
        review_date = event.payload["review"].get("submitted_at")
        st += print_v(f"\nReview submitted at:\t\t{get_date_from_ts(review_date)}")
        st += print_v(f"Review URL:\t\t\t{event.payload['review'].get('html_url')}")

        if event.payload["review"].get("author_association"):
            st += print_v(f"Author association:\t\t{event.payload['review'].get('author_association')}")

        if event.payload["review"].get("id"):
            st += print_v(f"Review ID:\t\t\t{event.payload['review'].get('id')}")
        if event.payload["review"].get("commit_id"):
            st += print_v(f"Commit SHA reviewed:\t\t{event.payload['review'].get('commit_id')}")
        if event.payload["review"].get("state"):
            st += print_v(f"Review state:\t\t\t{event.payload['review'].get('state')}")
        if event.payload["review"].get("body"):
            review_body = event.payload['review'].get('body')
            if len(review_body) > MAX_EVENT_BODY_LENGTH:
                review_body = safe_truncate_text(review_body)
            st += print_v(f"Review body:")
            st += print_v(format_body_block(review_body))

        if repo:
            try:
                pr_number = event.payload["pull_request"]["number"]
                debug_github_operation("event pull request review lookup", f"{github_object_name(repo)}#{pr_number}")
                pr_obj = repo.get_pull(pr_number)
                debug_github_operation("event pull request review comments listing", f"{github_object_name(repo)}#{pr_number}")
                count = sum(1 for _ in pr_obj.get_single_review_comments(event.payload["review"].get("id")))
                st += print_v(f"Comments in this review:\t{count}")
            except Exception as exc:
                verbose_degraded_feature("Pull request review comment count", "complete review event details", exc)

    if event.payload.get("issue"):
        st += print_v(f"\nIssue title:\t\t\t{event.payload['issue'].get('title')}")

        issue_date = event.payload["issue"].get("created_at")
        st += print_v(f"Issue date:\t\t\t{get_date_from_ts(issue_date)}")

        issue_author = event.payload["issue"].get("user", {}).get("login")
        if issue_author:
            st += print_v(f"Issue author:\t\t\t{issue_author}")

        issue_author_url = event.payload["issue"].get("user", {}).get("html_url")
        if issue_author_url:
            st += print_v(f"Issue author URL:\t\t{issue_author_url}")

        st += print_v(f"Issue URL:\t\t\t{event.payload['issue'].get('html_url')}")

        if event.payload["issue"].get("state"):
            st += print_v(f"Issue state:\t\t\t{event.payload['issue'].get('state')}")

        st += print_v(f"Issue comments:\t\t\t{event.payload['issue'].get('comments', 0)}")

        labels = event.payload["issue"].get("labels", [])
        if labels:
            label_names = ", ".join(label.get("name") for label in labels if label.get("name"))
            if label_names:
                st += print_v(f"Issue labels:\t\t\t{label_names}")

        if event.payload["issue"].get("assignees"):
            assignees = event.payload["issue"].get("assignees")
            for assignee in assignees:
                st += print_v(f" - Assignee name:\t\t{assignee.get('name')}")
                if assignee != assignees[-1]:
                    st += print_v()

        reactions = event.payload["issue"].get("reactions", {})

        reaction_map = {
            "+1": "👍",
            "-1": "👎",
            "laugh": "😄",
            "hooray": "🎉",
            "confused": "😕",
            "heart": "❤️",
            "rocket": "🚀",
            "eyes": "👀",
        }

        reaction_display = []
        for key, emoji in reaction_map.items():
            count = reactions.get(key, 0)
            if count > 0:
                reaction_display.append(f"{emoji} {count}")

        if reaction_display:
            st += print_v(f"Issue reactions:\t\t{' / '.join(reaction_display)}")

        if event.payload["issue"].get("body"):
            issue_body = event.payload['issue'].get('body')
            issue_snippet = issue_body if len(issue_body) <= MAX_EVENT_BODY_LENGTH else safe_truncate_text(issue_body)
            st += print_v(f"\nIssue body:")
            st += print_v(format_body_block(issue_snippet))

    if event.payload.get("comment"):
        comment = event.payload["comment"]

        comment_date = comment.get("created_at")
        st += print_v(f"\nComment date:\t\t\t{get_date_from_ts(comment_date)}")

        comment_author = comment.get("user", {}).get("login")
        if comment_author:
            st += print_v(f"Comment author:\t\t\t{comment_author}")

        comment_author_url = comment.get("user", {}).get("html_url")
        if comment_author_url:
            st += print_v(f"Comment author URL:\t\t{comment_author_url}")

        st += print_v(f"Comment URL:\t\t\t{comment.get('html_url')}")
        if comment.get("path"):
            st += print_v(f"Comment path:\t\t\t{comment.get('path')}")

        comment_body = comment.get("body")
        if comment_body:
            if len(comment_body) > MAX_EVENT_BODY_LENGTH:
                comment_body = safe_truncate_text(comment_body)
            st += print_v(f"\nComment body:")
            st += print_v(format_body_block(comment_body))

        if event.type == "PullRequestReviewCommentEvent":
            parent_id = comment.get("in_reply_to_id")
            if parent_id and repo:
                try:
                    pr_number = event.payload["pull_request"]["number"]
                    debug_github_operation("event pull request comment lookup", f"{github_object_name(repo)}#{pr_number}")
                    pr = repo.get_pull(pr_number)

                    debug_github_operation("event pull request parent comment lookup", parent_id)
                    parent = pr.get_review_comment(parent_id)
                    parent_date = get_date_from_ts(parent.created_at)

                    st += print_v(f"\nPrevious comment:\n\n↳ In reply to {parent.user.login} (@ {parent_date}):")

                    parent_body = parent.body
                    if len(parent_body) > MAX_EVENT_BODY_LENGTH:
                        parent_body = safe_truncate_text(parent_body)
                    st += print_v(format_body_block(parent_body))

                    st += print_v(f"\nPrevious comment URL:\t\t{parent.html_url}")
                except Exception as e:
                    verbose_degraded_feature("Parent pull request comment", "complete comment event details", e)
                    st += print_v(f"\n* Could not fetch parent comment (ID {parent_id}): {sanitize_error_text(e)}")
            else:
                st += print_v("\n(This is the first comment in its thread)")
        elif event.type in ("IssueCommentEvent", "CommitCommentEvent"):
            if repo:

                comment_id = comment["id"]
                comment_created = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00"))

                if event.type == "IssueCommentEvent":

                    issue_number = event.payload["issue"]["number"]
                    debug_github_operation("event issue lookup", f"{github_object_name(repo)}#{issue_number}")
                    issue = repo.get_issue(issue_number)

                    virtual_comment_list = []

                    if issue.body:
                        virtual_comment_list.append({
                            "id": f"issue-{issue.id}",  # fake ID so it doesn't collide
                            "created_at": issue.created_at,
                            "user": issue.user,
                            "body": issue.body,
                            "html_url": issue.html_url
                        })

                    debug_github_operation("event issue comments listing", f"{github_object_name(repo)}#{issue_number}")
                    for c in issue.get_comments():
                        virtual_comment_list.append({
                            "id": c.id,
                            "created_at": c.created_at,
                            "user": c.user,
                            "body": c.body,
                            "html_url": c.html_url
                        })

                    previous = None
                    for c in virtual_comment_list:
                        if c["id"] == comment_id or (isinstance(c["id"], int) and c["id"] == comment_id):
                            continue

                        if c["created_at"] < comment_created:
                            if not previous or c["created_at"] > previous["created_at"]:
                                previous = c

                    if previous:
                        prev_date = get_date_from_ts(previous["created_at"])
                        st += print_v(f"\nPrevious comment:\n\n↳ In reply to {previous['user'].login} (@ {prev_date}):")

                        parent_body = previous["body"]
                        if len(parent_body) > MAX_EVENT_BODY_LENGTH:
                            parent_body = safe_truncate_text(parent_body)
                        st += print_v(format_body_block(parent_body))

                        st += print_v(f"\nPrevious comment URL:\t\t{previous['html_url']}")
                    else:
                        st += print_v("\n(This is the first comment in this thread)")

                elif event.type == "CommitCommentEvent":
                    commit_sha = comment["commit_id"]
                    debug_github_operation("event commit comments listing", commit_sha)
                    comments = list(repo.get_commit(commit_sha).get_comments())

                    previous = None
                    for c in comments:
                        if c.id == comment_id:
                            continue
                        if c.created_at < comment_created:
                            if not previous or c.created_at > previous.created_at:
                                previous = c

                    if previous:
                        prev_date = get_date_from_ts(previous.created_at)
                        st += print_v(f"\nPrevious comment:\n\n↳ In reply to {previous.user.login} (@ {prev_date}):")

                        parent_body = previous.body
                        if len(parent_body) > MAX_EVENT_BODY_LENGTH:
                            parent_body = safe_truncate_text(parent_body)
                        st += print_v(format_body_block(parent_body))

                        st += print_v(f"\nPrevious comment URL:\t\t{previous.html_url}")
                    else:
                        st += print_v("\n(This is the first comment in this thread)")

    if event.payload.get("forkee"):
        st += print_v(f"\nForked to repo:\t\t\t{event.payload['forkee'].get('full_name')}")
        st += print_v(f"Forked to repo (URL):\t\t{event.payload['forkee'].get('html_url')}")

    if event.type == "MemberEvent":
        member_login = event.payload.get("member", {}).get("login")
        member_role = event.payload.get("membership", {}).get("role")
        if member_login:
            st += print_v(f"\nMember added:\t\t\t{member_login}")
            member_url = event.payload.get("member", {}).get("html_url")
            if member_url:
                st += print_v(f"Member added URL:\t\t{member_url}")
        if member_role:
            st += print_v(f"Permission level:\t\t{member_role}")

    if event.type == "PublicEvent":
        st += print_v("\nRepository is now public")

    if event.type == "DiscussionEvent":
        discussion_title = event.payload.get("discussion", {}).get("title")
        discussion_url = event.payload.get("discussion", {}).get("html_url")
        discussion_category = event.payload.get("discussion", {}).get("category", {}).get("name")
        if discussion_title:
            st += print_v(f"\nDiscussion title:\t\t{discussion_title}")
        if discussion_url:
            st += print_v(f"Discussion URL:\t\t\t{discussion_url}")
        if discussion_category:
            st += print_v(f"Discussion category:\t\t{discussion_category}")

    if event.type == "DiscussionCommentEvent":
        comment_author = event.payload.get("comment", {}).get("user", {}).get("login")
        comment_body = event.payload.get("comment", {}).get("body")
        if comment_author:
            st += print_v(f"\nDiscussion comment by:\t\t{comment_author}")
        if comment_body:
            if len(comment_body) > MAX_EVENT_BODY_LENGTH:
                comment_body = safe_truncate_text(comment_body)
            st += print_v(f"\nComment body:")
            st += print_v(format_body_block(comment_body))

    return event_date, repo_name, repo_url, st


# Lists recent events for the user (-l) and potentially dumps the entries to CSV file (if -b is used)
def github_list_events(user, number, csv_file_name):
    events = []
    available_events = 0

    try:
        if csv_file_name:
            init_csv_file(csv_file_name)
    except Exception as e:
        verbose_degraded_feature("Recent event CSV initialization", "event CSV records", e)
        print(f"* Error: {sanitize_error_text(e)}")

    list_operation = "* Listing & saving" if csv_file_name else "* Listing"

    print(f"{list_operation} {number} recent events for '{user}' ...\n")

    try:
        g = create_github_client("recent event listing")

        debug_github_operation("user profile lookup", user)
        g_user = g.get_user(user)
        debug_github_operation("recent event listing", user)
        all_events = list(g_user.get_events())
        total_available = len(all_events)
        events = all_events[:number]
        available_events = len(events)

        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except Exception as e:
        verbose_degraded_feature("Recent event listing", "recent event output", e)
        print(f"* Cannot fetch user details: {sanitize_error_text(e)}")
        return

    print(f"Username:\t\t\t{user_name_str}")
    print(f"User URL:\t\t\t{user_url}/")
    print(f"GitHub API URL:\t\t\t{GITHUB_API_URL}")
    if csv_file_name:
        print(f"CSV export enabled:\t\t{bool(csv_file_name)}" + (f" ({csv_file_name})" if csv_file_name else ""))
    print(f"Local timezone:\t\t\t{LOCAL_TIMEZONE}")
    print(f"Available events:\t\t{total_available}")
    print(f"\n{'─' * HORIZONTAL_LINE1}\n{'─' * HORIZONTAL_LINE1}")

    if available_events == 0:
        print("There are no events yet")
    else:
        try:
            event_number_map = {id(event): event_index + 1 for event_index, event in enumerate(events)}

            for event in reversed(events):

                if event.type in EVENTS_TO_MONITOR or 'ALL' in EVENTS_TO_MONITOR:
                    event_number = event_number_map[id(event)]
                    print(f"Event number:\t\t\t#{event_number}")
                    try:
                        event_date, repo_name, repo_url, event_text = github_print_event(event, g)
                    except Exception as e:
                        verbose_degraded_feature("Event detail rendering", "complete event output", e)
                        print(f"\n* Warning, cannot fetch all event details, skipping: {sanitize_error_text(e)}")
                        print_cur_ts("\nTimestamp:\t\t\t")
                        continue
                    try:
                        if csv_file_name:
                            write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                    except Exception as e:
                        print(f"* Error: {sanitize_error_text(e)}")
                    print_cur_ts("\nTimestamp:\t\t\t")
        except Exception as e:
            verbose_degraded_feature("Recent event iteration", "recent event output", e)
            print(f"* Cannot fetch events: {sanitize_error_text(e)}")


# Detects and reports changes in a user's profile-level entities (followers, followings, public repos, starred repos)
def handle_profile_change(label, count_old, count_new, list_old, raw_list, user, csv_file_name, field):
    try:
        list_new = []
        list_new = [getattr(item, field) for item in raw_list]
        if not list_new and count_new > 0:
            verbose_degraded_feature(f"{label} identities", f"{label.lower()} membership alerts")
            return list_old, count_old
    except Exception as e:
        verbose_degraded_feature(f"{label} list", f"{label.lower()} change alerts", e)
        print(f"* Error while trying to get the list of {label.lower()}: {sanitize_error_text(e)}")
        print_cur_ts("Timestamp:\t\t\t")
        return list_old, count_old

    new_count = len(list_new)
    old_count = len(list_old)

    if list_new == list_old:
        return list_old, count_old

    diff = new_count - old_count

    diff_str = f"+{diff}" if diff > 0 else f"{diff}"

    label_context = "by" if label.lower() in ["followings", "starred repos"] else "for"

    if diff == 0:
        print(f"* {label} list changed {label_context} user {user}\n")
    else:
        print(f"* {label} number changed {label_context} user {user} from {old_count} to {new_count} ({diff_str})\n")
        try:
            if csv_file_name:
                write_csv_entry(csv_file_name, now_local_naive(), f"{label} Count", user, old_count, new_count)
        except Exception as e:
            print(f"* Error: {sanitize_error_text(e)}")

    added_list_str = ""
    removed_list_str = ""
    added_mbody = ""
    removed_mbody = ""

    removed_items = list(set(list_old) - set(list_new))
    added_items = list(set(list_new) - set(list_old))

    removed_mbody_html = ""
    removed_list_str_html = ""
    added_mbody_html = ""
    added_list_str_html = ""

    if removed_items:
        print(f"Removed {label.lower()}:\n")
        removed_mbody = f"\nRemoved {label.lower()}:\n\n"
        removed_mbody_html = f"<br><b>Removed {html.escape(label.lower())}:</b><br><br>"
        web_base = github_web_base()
        for item in removed_items:
            item_url = (f"{web_base}/{item}/" if label.lower() in ["followers", "followings", "starred repos"]
                        else f"{web_base}/{user}/{item}/")

            print(f"- {item} [ {item_url} ]")
            removed_list_str += f"- {item} [ {item_url} ]\n"
            removed_list_str_html += f"- <a href=\"{html.escape(item_url)}\">{html.escape(item)}</a><br>"
            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), f"Removed {label[:-1]}", user, item, "")
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")
        print()

    if added_items:
        print(f"Added {label.lower()}:\n")
        added_mbody = f"\nAdded {label.lower()}:\n\n"
        added_mbody_html = f"<br><b>Added {html.escape(label.lower())}:</b><br><br>"
        web_base = github_web_base()
        for item in added_items:
            item_url = (f"{web_base}/{item}/" if label.lower() in ["followers", "followings", "starred repos"]
                        else f"{web_base}/{user}/{item}/")
            print(f"- {item} [ {item_url} ]")
            added_list_str += f"- {item} [ {item_url} ]\n"
            added_list_str_html += f"- <a href=\"{html.escape(item_url)}\">{html.escape(item)}</a><br>"
            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), f"Added {label[:-1]}", user, "", item)
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")
        print()

    if diff == 0:
        m_subject = f"GitHub user {user} {label.lower()} list changed"
        m_body = (f"{label} list changed {label_context} user {user}\n"
                  f"{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
        m_body_html = (
            f"<html><head></head><body>"
            f"{label} list changed {label_context} user <b>{html.escape(user)}</b><br>"
            f"{removed_mbody_html if removed_items else ''}{removed_list_str_html if removed_items else ''}"
            f"{added_mbody_html if added_items else ''}{added_list_str_html if added_items else ''}<br>"
            f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
            f"</body></html>"
        )
    else:
        m_subject = f"GitHub user {user} {label.lower()} number has changed! ({diff_str}, {old_count} -> {new_count})"
        m_body = (f"{label} number changed {label_context} user {user} from {old_count} to {new_count} ({diff_str})\n"
                  f"{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
        m_body_html = (
            f"<html><head></head><body>"
            f"{label} number changed {label_context} user <b>{html.escape(user)}</b> from <b>{old_count}</b> to <b>{new_count}</b> (<b>{html.escape(diff_str)}</b>)<br>"
            f"{removed_mbody_html if removed_items else ''}{removed_list_str_html if removed_items else ''}"
            f"{added_mbody_html if added_items else ''}{added_list_str_html if added_items else ''}<br>"
            f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
            f"</body></html>"
        )

    send_notification_channels("profile", m_subject, m_body, m_body_html, PROFILE_NOTIFICATION)

    print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
    print_cur_ts("Timestamp:\t\t\t")
    return list_new, new_count


# Detects and reports changes in repository-level entities such as stargazers, watchers, forks, issues, pull requests and discussions
def check_repo_list_changes(count_old, count_new, list_old, list_new, label, repo_name, repo_url, user, csv_file_name):
    if list_old is None or list_new is None:
        if count_old == count_new:
            verbose_degraded_feature(f"{label} identities for {repo_name}", f"{label.lower()} membership alerts")
            return

        diff = count_new - count_old
        diff_str = f"{'+' if diff > 0 else ''}{diff}"
        print(f"* Repo '{repo_name}': number of {label.lower()} changed from {count_old} to {count_new} ({diff_str})\n* Repo URL: {repo_url}")
        try:
            if csv_file_name:
                write_csv_entry(csv_file_name, now_local_naive(), f"Repo {label} Count", repo_name, count_old, count_new)
        except Exception as e:
            print(f"* Error: {sanitize_error_text(e)}")

        m_subject = f"GitHub user {user} number of {label.lower()} for repo '{repo_name}' has changed! ({diff_str}, {count_old} -> {count_new})"
        m_body = (f"* Repo '{repo_name}': number of {label.lower()} changed from {count_old} to {count_new} ({diff_str})\n"
                  f"* Repo URL: {repo_url}\n\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
        m_body_html = (
            f"<html><head></head><body>"
            f"* Repo '<b>{html.escape(repo_name)}</b>': number of {html.escape(label.lower())} changed from <b>{count_old}</b> to <b>{count_new}</b> (<b>{html.escape(diff_str)}</b>)<br>"
            f"* Repo URL: <a href=\"{html.escape(repo_url)}\">{html.escape(repo_url)}</a><br><br>"
            f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
            f"</body></html>"
        )

        send_notification_channels("repo", m_subject, m_body, m_body_html, REPO_NOTIFICATION)
        print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
        print_cur_ts("Timestamp:\t\t\t")
        return

    if not list_new and count_new > 0:
        verbose_degraded_feature(f"{label} identities for {repo_name}", f"{label.lower()} membership alerts")
        return

    old_count = len(list_old)
    new_count = len(list_new)

    if list_old == list_new:
        return

    diff = new_count - old_count

    diff_str = f"{'+' if diff > 0 else ''}{diff}"

    if diff == 0:
        print(f"* Repo '{repo_name}': {label.lower()} list changed\n* Repo URL: {repo_url}")
    else:
        print(f"* Repo '{repo_name}': number of {label.lower()} changed from {old_count} to {new_count} ({diff_str})\n* Repo URL: {repo_url}")
        try:
            if csv_file_name:
                write_csv_entry(csv_file_name, now_local_naive(), f"Repo {label} Count", repo_name, old_count, new_count)
        except Exception as e:
            print(f"* Error: {sanitize_error_text(e)}")

    added_list_str = ""
    removed_list_str = ""
    added_mbody = ""
    removed_mbody = ""

    added_list_str_html = ""
    removed_list_str_html = ""
    added_mbody_html = ""
    removed_mbody_html = ""

    removed_items = list(set(list_old) - set(list_new))
    added_items = list(set(list_new) - set(list_old))

    # If lists are different but sets are the same (just reordered or duplicates), no actual change
    if not removed_items and not added_items:
        return

    removal_text = "Closed" if label in ["Issues", "Pull Requests", "Discussions"] else "Removed"

    if list_old != list_new:
        print()

        if removed_items:
            print(f"{removal_text} {label.lower()}:\n")
            removed_mbody = f"\n{removal_text} {label.lower()}:\n\n"
            removed_mbody_html = f"<br><b>{html.escape(removal_text)} {html.escape(label.lower())}:</b><br><br>"
            for item in removed_items:
                item_line = f"- {item} [ {github_web_base()}/{item}/ ]" if label.lower() in ["stargazers", "watchers", "forks"] else f"- {item}"
                print(item_line)
                removed_list_str += item_line + "\n"

                if label.lower() in ["stargazers", "watchers", "forks"]:
                    item_url = f"{github_web_base()}/{item}/"
                    removed_list_str_html += f"- <a href=\"{html.escape(item_url)}\">{html.escape(item)}</a><br>"
                elif label in ["Issues", "Pull Requests", "Discussions"]:
                    match = re.match(r'#(\d+)\s+(.+?)\s+\(([^)]+)\)\s+\[\s*([^\]]+)\s*\]', item)
                    if match:
                        num, title, user_item, url = (value.strip() for value in match.groups())
                        removed_list_str_html += f"- <a href=\"{html.escape(url)}\"><b>#{num} {html.escape(title)}</b></a> ({html.escape(user_item)})<br>"
                    else:
                        removed_list_str_html += f"- {html.escape(item)}<br>"
                else:
                    removed_list_str_html += f"- {html.escape(item)}<br>"

                try:
                    if csv_file_name:
                        value = item.rsplit("(", 1)[0].strip() if label in ["Issues", "Pull Requests", "Discussions"] else item
                        write_csv_entry(csv_file_name, now_local_naive(), f"{removal_text} {label[:-1]}", repo_name, value, "")
                except Exception as e:
                    print(f"* Error: {sanitize_error_text(e)}")
            print()

        if added_items:
            print(f"Added {label.lower()}:\n")
            added_mbody = f"\nAdded {label.lower()}:\n\n"
            added_mbody_html = f"<br><b>Added {html.escape(label.lower())}:</b><br><br>"
            for item in added_items:
                item_line = f"- {item} [ {github_web_base()}/{item}/ ]" if label.lower() in ["stargazers", "watchers", "forks"] else f"- {item}"
                print(item_line)
                added_list_str += item_line + "\n"

                if label.lower() in ["stargazers", "watchers", "forks"]:
                    item_url = f"{github_web_base()}/{item}/"
                    added_list_str_html += f"- <a href=\"{html.escape(item_url)}\">{html.escape(item)}</a><br>"
                elif label in ["Issues", "Pull Requests", "Discussions"]:
                    match = re.match(r'#(\d+)\s+(.+?)\s+\(([^)]+)\)\s+\[\s*([^\]]+)\s*\]', item)
                    if match:
                        num, title, user_item, url = (value.strip() for value in match.groups())
                        added_list_str_html += f"- <a href=\"{html.escape(url)}\"><b>#{num} {html.escape(title)}</b></a> ({html.escape(user_item)})<br>"
                    else:
                        added_list_str_html += f"- {html.escape(item)}<br>"
                else:
                    added_list_str_html += f"- {html.escape(item)}<br>"

                try:
                    if csv_file_name:
                        value = item.rsplit("(", 1)[0].strip() if label in ["Issues", "Pull Requests", "Discussions"] else item
                        write_csv_entry(csv_file_name, now_local_naive(), f"Added {label[:-1]}", repo_name, "", value)
                except Exception as e:
                    print(f"* Error: {sanitize_error_text(e)}")
            print()

    if diff == 0:
        m_subject = f"GitHub user {user} {label.lower()} list changed for repo '{repo_name}'!"
        m_body = (f"* Repo '{repo_name}': {label.lower()} list changed\n"
                  f"* Repo URL: {repo_url}\n{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
        m_body_html = (
            f"<html><head></head><body>"
            f"* Repo '<b>{html.escape(repo_name)}</b>': {html.escape(label.lower())} list changed<br>"
            f"* Repo URL: <a href=\"{html.escape(repo_url)}\">{html.escape(repo_url)}</a><br>"
            f"{removed_mbody_html}{removed_list_str_html}"
            f"{added_mbody_html}{added_list_str_html}<br>"
            f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
            f"</body></html>"
        )
    else:
        m_subject = f"GitHub user {user} number of {label.lower()} for repo '{repo_name}' has changed! ({diff_str}, {old_count} -> {new_count})"
        m_body = (f"* Repo '{repo_name}': number of {label.lower()} changed from {old_count} to {new_count} ({diff_str})\n"
                  f"* Repo URL: {repo_url}\n{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
        m_body_html = (
            f"<html><head></head><body>"
            f"* Repo '<b>{html.escape(repo_name)}</b>': number of {html.escape(label.lower())} changed from <b>{old_count}</b> to <b>{new_count}</b> (<b>{html.escape(diff_str)}</b>)<br>"
            f"* Repo URL: <a href=\"{html.escape(repo_url)}\">{html.escape(repo_url)}</a><br>"
            f"{removed_mbody_html}{removed_list_str_html}"
            f"{added_mbody_html}{added_list_str_html}<br>"
            f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
            f"</body></html>"
        )

    send_notification_channels("repo", m_subject, m_body, m_body_html, REPO_NOTIFICATION)
    print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
    print_cur_ts("Timestamp:\t\t\t")


# Finds an optional config file
def find_config_file(cli_path=None):
    """
    Search for an optional config file in:
      1) CLI-provided path (must exist if given)
      2) ./{DEFAULT_CONFIG_FILENAME}
      3) ~/.{DEFAULT_CONFIG_FILENAME}
      4) script-directory/{DEFAULT_CONFIG_FILENAME}
    """

    if cli_path:
        p = Path(os.path.expanduser(cli_path))
        debug_print("Checking explicit configuration", path=p)
        return str(p) if p.is_file() else None

    candidates = [
        Path.cwd() / DEFAULT_CONFIG_FILENAME,
        Path.home() / f".{DEFAULT_CONFIG_FILENAME}",
        Path(__file__).parent / DEFAULT_CONFIG_FILENAME,
    ]

    for p in candidates:
        debug_print("Checking discovered configuration", path=p)
        if p.is_file():
            debug_print("Selected discovered configuration", path=p)
            return str(p)
    debug_print("No configuration file selected")
    return None


# Returns the raw --config-file value before argparse runs
def early_config_file_argument(arguments=None):
    values = list(sys.argv[1:] if arguments is None else arguments)
    for index, argument in enumerate(values):
        if argument == "--config-file" and index + 1 < len(values):
            return values[index + 1]
        if argument.startswith("--config-file="):
            return argument.split("=", 1)[1]
    return None


# Applies terminal settings needed before argument parsing and leaves failures for normal config loading
def apply_early_output_config():
    global CLEAR_SCREEN, COLORED_OUTPUT
    try:
        cli_path = early_config_file_argument()
        if cli_path is not None and cli_path.casefold() == "none":
            return
        expanded_path = os.path.expanduser(cli_path) if cli_path else None
        config_path = find_config_file(expanded_path)
        if not config_path:
            return
        values = parse_config_content(Path(config_path).read_text(encoding="utf-8"), str(config_path))
    except (MemoryError, OSError, RecursionError, SyntaxError, UnicodeError, ValueError):
        return
    if isinstance(values.get("CLEAR_SCREEN"), bool):
        CLEAR_SCREEN = values["CLEAR_SCREEN"]
    if isinstance(values.get("COLORED_OUTPUT"), bool):
        COLORED_OUTPUT = values["COLORED_OUTPUT"]


# Settings an older version wrote that this version no longer defines, ignored instead of rejected
RETIRED_CONFIG_SETTINGS = frozenset(())


# Collects the setting names the built-in configuration template defines
def _config_allowed_names():
    template_tree = ast.parse(CONFIG_BLOCK, "<built-in-config>", "exec")
    return frozenset(statement.targets[0].id for statement in template_tree.body if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name))


# Parses allowlisted literal config assignments without executing any file content
def parse_config_content(content, filename="<config>", retired_out=None, reference_values=None):
    tree = ast.parse(content, filename, "exec")
    allowed_names = _config_allowed_names()
    parsed_values = {}
    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            raise ValueError(f"Line {getattr(statement, 'lineno', '?')}: only NAME = value assignments are allowed")
        name = statement.targets[0].id
        if name in RETIRED_CONFIG_SETTINGS and name not in allowed_names:
            if retired_out is not None and name not in retired_out:
                retired_out.append(name)
            continue
        if name not in allowed_names:
            raise ValueError(f"Line {statement.lineno}: unsupported configuration setting {name!r}")
        # One setting may reuse another, which the built-in template does and existing configs copy
        if isinstance(statement.value, ast.Name):
            referenced = statement.value.id
            if referenced not in allowed_names:
                raise ValueError(f"Line {statement.lineno}: {name} may only reference another configuration setting")
            source = parsed_values if referenced in parsed_values else (reference_values if reference_values is not None else globals())
            if referenced not in source:
                raise ValueError(f"Line {statement.lineno}: {name} references {referenced!r} before it has a value")
            parsed_values[name] = source[referenced]
            continue
        try:
            parsed_values[name] = ast.literal_eval(statement.value)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError) as exc:
            raise ValueError(f"Line {statement.lineno}: {name} must be a plain value such as a number, string, True, False, None, list, tuple or dict") from exc
    return parsed_values


# Validates config content through the same restricted parser used at startup
def validate_config_content(content, filename="<generated-config>"):
    parse_config_content(content, filename)


# Reports settings an older version wrote that this version no longer defines
def describe_retired_settings(names, quoted_path):
    listed = ", ".join(sorted(names))
    return f"Config file {quoted_path} contains settings this version no longer uses, which were ignored: {listed}"


# Loads a config file as data and applies only recognized literal settings
def load_config_file(config_path, namespace=None, report_errors=True, loaded_names_out=None, diagnostic_overrides=None, error_out=None, retired_names_out=None):
    selected_namespace = globals() if namespace is None else namespace
    retired_settings = []
    try:
        debug_print("Reading configuration file", path=config_path)
        content = Path(config_path).read_text(encoding="utf-8")
        debug_print("Configuration file read succeeded", path=config_path, bytes=len(content.encode('utf-8')))
        # Parsed as data rather than executed, so a config file picked up from the working directory cannot run code
        parsed_values = parse_config_content(content, str(config_path), retired_settings)
        selected_namespace.update(parsed_values)
        if diagnostic_overrides is not None:
            verbose_override, debug_override = diagnostic_overrides
            if verbose_override:
                selected_namespace["VERBOSE_MODE"] = True
            if debug_override:
                selected_namespace["DEBUG_MODE"] = True
        if loaded_names_out is not None:
            loaded_names_out.update(parsed_values)
        if retired_names_out is not None:
            retired_names_out.update(retired_settings)
        if retired_settings and report_errors:
            print(f"* Note: {describe_retired_settings(retired_settings, chr(39) + str(config_path) + chr(39))}")
        debug_print("Configuration applied", path=config_path, settings=len(parsed_values), retired=len(retired_settings))
        verbose_print(f"Loaded {len(parsed_values)} settings from the configuration file")
        return True
    except SyntaxError as exc:
        detail = f"Config file '{config_path}' has invalid Python syntax"
        if exc.lineno is not None:
            detail += f" at line {exc.lineno}"
        if exc.text:
            detail += f" | Source: {exc.text.rstrip()}"
        detail += f" | Parser: {exc.msg}"
    # Checked before ValueError because UnicodeDecodeError derives from it
    except UnicodeDecodeError:
        detail = f"Config file '{config_path}' is not valid UTF-8"
    except ValueError as exc:
        detail = f"Config file '{config_path}' contains unsupported content: {exc}"
    except Exception as exc:
        detail = f"Config file '{config_path}' failed with {type(exc).__name__}: {exc}"
    debug_print("Configuration load", path=config_path, outcome="failed", error=detail)
    if error_out is not None:
        error_out.append(detail)
    if report_errors:
        config_command = render_install_command(["--generate-config", "github_monitor.conf"])
        advice = make_recovery_advice("config.invalid", detail, f"Keep only documented SETTING = value lines with plain literal values or regenerate with: {config_command}", False, detail, CONFIG_GUIDE_URL)
        print_recovery_advice(advice)
    return False


# Loads the selected dotenv file then applies every exported secret independently of that file
def load_startup_secrets(env_file=None, configured_settings=None, report_errors=True, errors_out=None):
    global DOTENV_FILE, SECRET_SOURCES
    if env_file is not None:
        DOTENV_FILE = os.path.expanduser(env_file)
    elif DOTENV_FILE:
        DOTENV_FILE = os.path.expanduser(DOTENV_FILE)

    configured_names = set(configured_settings or ())
    environment_values = {secret: os.environ[secret] for secret in SECRET_KEYS if secret in os.environ}
    dotenv_keys = set()
    if DOTENV_FILE and DOTENV_FILE.casefold() == "none":
        env_path = None
        debug_print("Dotenv loading disabled by configuration or command line")
    else:
        try:
            from dotenv import dotenv_values, find_dotenv, load_dotenv

            if DOTENV_FILE:
                env_path = DOTENV_FILE
                if not os.path.isfile(env_path):
                    debug_print("Dotenv file not found", path=env_path)
                    detail = f"Dotenv file '{env_path}' does not exist"
                    if errors_out is not None:
                        errors_out.append(detail)
                    if report_errors:
                        print(f"* Warning: {detail}\n")
                else:
                    debug_print("Reading dotenv file", path=env_path)
                    dotenv_keys = {str(name) for name in dotenv_values(env_path) if name in SECRET_KEYS}
                    load_dotenv(env_path, override=False)
                    debug_print("Dotenv file loaded", path=env_path, secret_names=sorted(dotenv_keys))
            else:
                env_path = find_dotenv() or None
                if env_path:
                    debug_print("Reading discovered dotenv file", path=env_path)
                    dotenv_keys = {str(name) for name in dotenv_values(env_path) if name in SECRET_KEYS}
                    load_dotenv(env_path, override=False)
                    debug_print("Discovered dotenv file loaded", path=env_path, secret_names=sorted(dotenv_keys))
                else:
                    debug_print("No dotenv file discovered")
        except ImportError as exc:
            debug_swallowed_exception("Dotenv dependency import", exc)
            env_path = DOTENV_FILE if DOTENV_FILE else None
            if env_path:
                install_command = shlex.join([sys.executable, "-m", "pip", "install", "python-dotenv"])
                detail = f"Cannot load dotenv file '{env_path}' because python-dotenv is not installed"
                if errors_out is not None:
                    errors_out.append(detail)
                if report_errors:
                    print(f"* Warning: {detail}\n\nTo install it, run:\n    {install_command}\n\nOnce installed, re-run this tool\n")
        except Exception as exc:
            env_path = DOTENV_FILE if DOTENV_FILE else None
            verbose_degraded_feature("Dotenv loading", "dotenv-based private settings", exc)
            advice = make_recovery_advice("file.unreadable", "The dotenv file could not be read", "Check DOTENV_FILE and its permissions or disable it with --env-file none", False, f"{type(exc).__name__}: {exc}", CONFIG_GUIDE_URL)
            if errors_out is not None:
                errors_out.append(advice.summary + f": {advice.detail}")
            if report_errors:
                print_recovery_advice(advice)

    SECRET_SOURCES = {}
    for secret in SECRET_KEYS:
        value = os.getenv(secret)
        if value is not None:
            globals()[secret] = value
        if secret in environment_values:
            SECRET_SOURCES[secret] = "environment"
        elif secret in dotenv_keys and value is not None:
            SECRET_SOURCES[secret] = "dotenv file"
        elif secret in configured_names and globals().get(secret):
            SECRET_SOURCES[secret] = "configuration file"
        elif isinstance(globals().get(secret), str) and globals().get(secret) and not globals().get(secret).startswith("your_"):
            SECRET_SOURCES[secret] = "built-in configuration"
    if SECRET_SOURCES:
        for secret, source in SECRET_SOURCES.items():
            debug_print("Secret resolution", name=secret, source=source)
    else:
        debug_print("No private settings were resolved from config, dotenv or environment")
    return env_path


# Applies startup CLI overrides before any check consumes effective configuration
def apply_startup_cli_overrides(args, configured_settings=None):
    global GITHUB_TOKEN, GITHUB_API_URL, CHECK_INTERNET_URL, SECRET_SOURCES
    configured_names = set(configured_settings or ())
    previous_api_url = GITHUB_API_URL
    connectivity_follows_api = "CHECK_INTERNET_URL" not in configured_names or CHECK_INTERNET_URL == previous_api_url
    if args.github_token is not None:
        GITHUB_TOKEN = args.github_token
        SECRET_SOURCES["GITHUB_TOKEN"] = "command line"
        debug_print("Secret resolution name=GITHUB_TOKEN source=command line")
    if args.github_url is not None:
        GITHUB_API_URL = args.github_url
    if connectivity_follows_api:
        CHECK_INTERNET_URL = GITHUB_API_URL


# Applies only explicitly supplied diagnostic flags without erasing saved defaults
def apply_diagnostic_cli_overrides(args):
    global VERBOSE_MODE, DEBUG_MODE
    if getattr(args, "verbose", None) is True:
        VERBOSE_MODE = True
    if getattr(args, "debug", None) is True:
        DEBUG_MODE = True


# Represents a safe GitHub token setup or validation failure
class GitHubTokenConfigurationError(ValueError):
    pass


# Resolves the dotenv path used for private secret persistence
def resolve_secret_env_path(env_file=None, action_name="Private secret setup") -> Path:
    selected = env_file if env_file is not None else DOTENV_FILE
    if isinstance(selected, str) and selected.casefold() == "none":
        raise ValueError(f"{action_name} requires a dotenv destination")
    path = Path(selected).expanduser() if selected else Path.cwd() / ".env"
    return path.resolve()


# Matches one dotenv assignment, tolerating the export prefix used when the same file is sourced by a shell
def match_dotenv_assignment(line: Any, key: str):
    return re.match(rf"^(\s*(?:export\s+)?){re.escape(key)}\s*=", str(line))


# Renders one quoted dotenv assignment, keeping the export prefix of the line it replaces
def render_dotenv_assignment(key: str, value: str, prefix: str = "") -> str:
    return f'{prefix}{key}="{value.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"'


# Returns whether one dotenv file already assigns the requested key
def dotenv_contains_key(path: Path, key: str) -> bool:
    if not path.exists():
        debug_print("Dotenv key check skipped because file does not exist", path=path, key=key)
        return False
    debug_print("Reading dotenv file for key check", path=path, key=key)
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        debug_print("Dotenv key check read", path=path, key=key, outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    debug_print("Dotenv key check read succeeded", path=path, key=key)
    return any(match_dotenv_assignment(line, key) for line in content.splitlines())


# Updates one dotenv assignment while preserving unrelated lines
def update_dotenv_value(path: Path, key: str, value: str) -> None:
    if not path.parent.is_dir():
        raise FileNotFoundError(f"Dotenv parent directory does not exist: {path.parent}")
    debug_print("Reading private settings file before update", path=path, key=key, exists=path.exists())
    try:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
    except Exception as exc:
        debug_print("Private settings file read", path=path, key=key, outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    output_lines = []
    replaced = False
    for line in existing.splitlines():
        match = match_dotenv_assignment(line, key)
        if match:
            if not replaced:
                output_lines.append(render_dotenv_assignment(key, value, match.group(1)))
                replaced = True
            continue
        output_lines.append(line)
    if not replaced:
        output_lines.append(render_dotenv_assignment(key, value))
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as dotenv_file:
            dotenv_file.write("\n".join(output_lines) + "\n")
    except Exception as exc:
        debug_print("Private settings file update", path=path, key=key, outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    debug_print("Private settings file update succeeded", path=path, key=key, mode="0600")
    verbose_print(f"Saved {key} in the private settings file")


# Validates one GitHub token without exposing it in errors or output
def validate_github_token(token: Any, api_url: Any = None, request_get: Optional[Callable[..., Any]] = None) -> str:
    if not isinstance(token, str) or not token.strip() or token.strip() == "your_github_classic_personal_access_token":
        raise GitHubTokenConfigurationError("No valid GitHub token was entered and the dotenv file was not changed")
    selected_token = token.strip()
    if "\r" in selected_token or "\n" in selected_token:
        raise GitHubTokenConfigurationError("The GitHub token contains invalid line breaks and the dotenv file was not changed")
    selected_api_url = GITHUB_API_URL if api_url is None else api_url
    if not isinstance(selected_api_url, str) or not selected_api_url.strip():
        raise GitHubTokenConfigurationError("GITHUB_API_URL is empty and the dotenv file was not changed")
    if not validate_github_endpoint_url(selected_api_url):
        raise GitHubTokenConfigurationError("GITHUB_API_URL must be a complete HTTPS URL without embedded credentials, query parameters or fragments")
    endpoint = selected_api_url.strip().rstrip("/") + "/user"
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {selected_token}", "User-Agent": f"GitHubMonitor/{VERSION}"}
    get_request = req.get if request_get is None else request_get
    try:
        debug_http_request("GET", endpoint, "GitHub token validation", 10, headers=headers, token=selected_token)
        response = get_request(endpoint, headers=headers, timeout=10, allow_redirects=False, verify=VERIFY_SSL)
        debug_http_response("GET", endpoint, "GitHub token validation", getattr(response, "status_code", "unknown"))
    except req.RequestException as exc:
        debug_print("GitHub token validation request", outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise GitHubTokenConfigurationError("Could not reach the configured GitHub API while validating the token and the dotenv file was not changed") from None
    status_code = getattr(response, "status_code", None)
    if status_code in (401, 403):
        raise GitHubTokenConfigurationError("GitHub rejected the entered token and the dotenv file was not changed")
    if status_code != 200:
        raise GitHubTokenConfigurationError(f"GitHub token validation returned HTTP {status_code} and the dotenv file was not changed")
    try:
        payload = response.json()
    except Exception as exc:
        debug_swallowed_exception("GitHub token validation response parsing", exc)
        payload = None
    login = payload.get("login") if isinstance(payload, dict) else None
    if not isinstance(login, str) or not login.strip():
        raise GitHubTokenConfigurationError("GitHub token validation returned an invalid user response and the dotenv file was not changed")
    return login.strip()


# Validates and safely stores one privately entered GitHub token
def run_set_github_token(env_file=None, api_url=None, interactive=None, input_func=None, getpass_func=None, config_path=None, install_context=None) -> str:
    global DEBUG_MODE
    destination = resolve_secret_env_path(env_file, "--set-github-token")
    terminal_is_interactive = sys.stdin.isatty() if interactive is None else interactive
    if not terminal_is_interactive:
        raise GitHubTokenConfigurationError("--set-github-token requires an interactive terminal so the token stays hidden")
    prompt = input if input_func is None else input_func
    if dotenv_contains_key(destination, "GITHUB_TOKEN"):
        try:
            confirmed = prompt(f"Replace GITHUB_TOKEN in '{destination}'? [y/N]: ").strip().casefold() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            confirmed = False
        if not confirmed:
            raise GitHubTokenConfigurationError("GITHUB_TOKEN replacement was cancelled and the dotenv file was not changed")
    print("* Create or review GitHub tokens at: https://github.com/settings/tokens")
    hidden_prompt = getpass.getpass if getpass_func is None else getpass_func
    previous_debug_mode = DEBUG_MODE
    DEBUG_MODE = False
    try:
        token = hidden_prompt("Enter GitHub token privately: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise GitHubTokenConfigurationError("GITHUB_TOKEN entry was cancelled and the dotenv file was not changed") from None
    finally:
        DEBUG_MODE = previous_debug_mode
    print("* Validating the entered GitHub token before changing the dotenv file ...")
    login = validate_github_token(token, api_url=api_url)
    try:
        update_dotenv_value(destination, "GITHUB_TOKEN", token)
    except Exception as exc:
        debug_print("Private settings file update", path=destination, key="GITHUB_TOKEN", outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise GitHubTokenConfigurationError(f"Could not save GITHUB_TOKEN in '{destination}'. Check the path and file permissions") from None
    paths = []
    if config_path:
        paths.extend(("--config-file", str(config_path)))
    paths.extend(("--env-file", str(destination)))
    if api_url is not None:
        paths.extend(("--github-url", str(api_url)))
    print(f"* GitHub token validation succeeded for user: {login}")
    print(f"* Updated private settings file: {destination}")
    print()
    _wizard_print_command(sys.stdout, "Check setup again:", render_install_command(["--doctor", "GITHUB_USERNAME"] + paths, install_context))
    _wizard_print_command(sys.stdout, "After Doctor passes, start monitoring:", render_install_command(["GITHUB_USERNAME"] + paths, install_context))
    return str(destination)


# Checks and safely stores one privately entered webhook URL
def run_set_webhook_url(env_file=None, interactive=None, input_func=None, getpass_func=None, config_path=None, install_context=None) -> str:
    global DEBUG_MODE
    destination = resolve_secret_env_path(env_file, "--set-webhook-url")
    terminal_is_interactive = sys.stdin.isatty() if interactive is None else interactive
    if not terminal_is_interactive:
        raise ValueError("--set-webhook-url requires an interactive terminal so the webhook URL stays hidden")
    prompt = input if input_func is None else input_func
    if dotenv_contains_key(destination, "WEBHOOK_URL"):
        try:
            confirmed = prompt(f"Replace the saved webhook URL in '{destination}'? [y/N]: ").strip().casefold() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            confirmed = False
        if not confirmed:
            raise ValueError("Webhook setup was cancelled and the dotenv file was not changed")
    hidden_prompt = getpass.getpass if getpass_func is None else getpass_func
    previous_debug_mode = DEBUG_MODE
    DEBUG_MODE = False
    try:
        webhook_url = hidden_prompt("Paste the Discord or ntfy webhook URL (input hidden): ").strip()
    except (EOFError, KeyboardInterrupt):
        raise ValueError("Webhook setup was cancelled and the dotenv file was not changed") from None
    finally:
        DEBUG_MODE = previous_debug_mode
    if not validate_webhook_url(webhook_url):
        raise ValueError("That does not look like a complete HTTPS webhook URL and the dotenv file was not changed")
    update_dotenv_value(destination, "WEBHOOK_URL", webhook_url)
    paths = []
    if config_path:
        paths.extend(("--config-file", str(config_path)))
    paths.extend(("--env-file", str(destination)))
    print("* Webhook URL looks valid")
    print(f"* Updated private settings file: {destination}")
    print()
    _wizard_print_command(sys.stdout, "Send a test webhook:", render_install_command(["--send-test-webhook"] + paths, install_context))
    _wizard_print_command(sys.stdout, "Check setup again:", render_install_command(["--doctor", "GITHUB_USERNAME"] + paths, install_context))
    return str(destination)


# Resolves an executable path by checking if it's a valid file or searching in $PATH
def resolve_executable(path):
    if os.path.isfile(path) and os.access(path, os.X_OK):
        return path

    found = shutil.which(path)
    if found:
        return found

    raise FileNotFoundError(f"Could not find executable '{path}'")


# Checks if the authenticated user (token's owner) is blocked by user
def is_blocked_by(user):
    try:

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

        user_endpoint = f"{GITHUB_API_URL}/user"
        debug_http_request("GET", user_endpoint, "authenticated viewer lookup for block detection", 15, headers=headers, token=GITHUB_TOKEN)
        response = req.get(user_endpoint, headers=headers, timeout=15, verify=VERIFY_SSL)
        debug_http_response("GET", user_endpoint, "authenticated viewer lookup for block detection", response.status_code)
        if response.status_code != 200:
            verbose_degraded_feature("Block status", "block and unblock alerts")
            return None
        me_login = response.json().get("login", "").lower()
        if user.lower() == me_login:
            return False

        graphql_endpoint = GITHUB_API_URL.rstrip("/") + "/graphql"
        query = """
        query($login: String!) {
          user(login: $login) {
            viewerCanFollow
          }
        }
        """
        payload = {"query": query, "variables": {"login": user}}
        debug_http_request("POST", graphql_endpoint, "target block relationship lookup", 15, headers=headers, token=GITHUB_TOKEN)
        response_graphql = req.post(graphql_endpoint, json=payload, headers=headers, timeout=15, verify=VERIFY_SSL)
        debug_http_response("POST", graphql_endpoint, "target block relationship lookup", response_graphql.status_code)

        if response_graphql.status_code == 404:
            verbose_degraded_feature("Block status", "block and unblock alerts")
            return None

        if not response_graphql.ok:
            verbose_degraded_feature("Block status", "block and unblock alerts")
            return None

        data = response_graphql.json()
        can_follow = (data.get("data", {}).get("user", {}).get("viewerCanFollow", True))
        return not bool(can_follow)

    except Exception as exc:
        verbose_degraded_feature("Block status", "block and unblock alerts", exc)
        return None


# Return the total number of repositories the user has starred (faster than via PyGithub)
def get_starred_count(user):
    try:

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

        graphql_endpoint = f"{GITHUB_API_URL.rstrip('/')}/graphql"
        query = """
        query($login:String!){
          user(login:$login){
            starredRepositories{
              totalCount
            }
          }
        }
        """
        payload = {"query": query, "variables": {"login": user}}
        debug_http_request("POST", graphql_endpoint, "starred repository count", 15, headers=headers, token=GITHUB_TOKEN)
        response = req.post(graphql_endpoint, json=payload, headers=headers, timeout=15, verify=VERIFY_SSL)
        debug_http_response("POST", graphql_endpoint, "starred repository count", response.status_code)

        if not response.ok:
            verbose_degraded_feature("Starred repository count", "starred repository change alerts")
            return 0

        data = response.json()

        return (data.get("data", {}).get("user", {}).get("starredRepositories", {}).get("totalCount", 0))

    except Exception as exc:
        verbose_degraded_feature("Starred repository count", "starred repository change alerts", exc)
        return 0


# Returns True if the user's GitHub page shows "activity is private"
def has_private_banner(user):
    try:
        url = f"{GITHUB_HTML_URL.rstrip('/')}/{user}"
        debug_http_request("GET", url, "public profile visibility page", 15)
        r = req.get(url, timeout=15, verify=VERIFY_SSL)
        debug_http_response("GET", url, "public profile visibility page", r.status_code)
        return r.ok and "activity is private" in r.text.lower()
    except Exception as exc:
        verbose_degraded_feature("Profile visibility", "profile visibility alerts", exc)
        return False


# Returns True if the user's GitHub profile is public
def is_profile_public(g: Github, user, new_account_days=30):

    if has_private_banner(user):
        return False

    try:
        debug_github_operation("public profile lookup", user)
        u = g.get_user(user)

        if any([
            u.followers > 0,
            u.following > 0,
            get_starred_count(user) > 0,
        ]):
            return True

        try:
            debug_print("PyGithub", operation="recent public event probe", endpoint=diagnostic_endpoint(GITHUB_API_URL), timeout=f"{PYGITHUB_TIMEOUT_SECONDS}s", token=mask_secret(GITHUB_TOKEN), target=user)
            events_iter = iter(u.get_events())
            next(events_iter)
            return True
        except StopIteration as exc:
            debug_swallowed_exception("Recent public event probe returned no events", exc)
        except GithubException as exc:
            verbose_degraded_feature("Public profile detection", "profile visibility alerts", exc)

    except GithubException as exc:
        verbose_degraded_feature("Public profile detection", "profile visibility alerts", exc)

    return False


# Returns a dict mapping 'YYYY-MM-DD' -> int contribution count for the range
# Handles long date ranges by splitting into year-long chunks
def get_daily_contributions(username: str, start: Optional[dt.date] = None, end: Optional[dt.date] = None, token: Optional[str] = None) -> dict:
    if token is None:
        raise ValueError("GitHub token is required")

    today = dt.date.today()
    if start is None:
        start = today
    if end is None:
        end = today

    # GitHub's contribution calendar API has limitations - typically only returns last year
    # For longer periods, we need to split into year-long chunks
    out = {}

    # Split into year-long chunks (max 1 year per request)
    current_start = start
    while current_start <= end:
        # Calculate end date for this chunk (1 year from start, or the requested end date, whichever is earlier)
        # Use relativedelta to handle leap years correctly (e.g., Feb 29, 2024 -> Feb 28, 2025)
        next_year_date = current_start + relativedelta.relativedelta(years=1)
        chunk_end = min(
            next_year_date - dt.timedelta(days=1),
            end
        )

        url = GITHUB_API_URL.rstrip("/") + "/graphql"
        headers = {
            "Authorization": f"Bearer {token}",
            "Time-Zone": LOCAL_TIMEZONE,
        }

        tz = pytz.timezone(LOCAL_TIMEZONE)
        start_w = current_start - dt.timedelta(days=1)
        end_w_exclusive = chunk_end + dt.timedelta(days=1)
        start_iso = tz.localize(dt.datetime.combine(start_w, dt.time.min)).isoformat()
        end_iso = tz.localize(dt.datetime.combine(end_w_exclusive, dt.time.min)).isoformat()

        query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }"""

        variables = {"login": username, "from": start_iso, "to": end_iso}
        debug_http_request("POST", url, "daily contribution calendar", 30, headers=headers, token=token)
        r = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=30, verify=VERIFY_SSL)
        debug_http_response("POST", url, "daily contribution calendar", r.status_code)
        r.raise_for_status()
        data = r.json()

        # Check for errors in the response
        if "errors" in data:
            raise RuntimeError(f"GraphQL API errors: {data['errors']}")

        # Check if user exists
        if data.get("data", {}).get("user") is None:
            raise ValueError(f"User '{username}' not found")

        # Safely access nested data
        contrib_collection = data.get("data", {}).get("user", {}).get("contributionsCollection")
        if contrib_collection is None:
            raise RuntimeError(f"No contributions data returned for user '{username}'")

        contrib_calendar = contrib_collection.get("contributionCalendar")
        if contrib_calendar is None:
            # For very old dates, GitHub may not have data - skip this chunk
            print(f"Warning: No contribution calendar data available for {current_start} to {chunk_end}, skipping...")
            current_start = chunk_end + dt.timedelta(days=1)
            continue

        weeks = contrib_calendar.get("weeks")
        if weeks is None:
            print(f"Warning: No weeks data available for {current_start} to {chunk_end}, skipping...")
            current_start = chunk_end + dt.timedelta(days=1)
            continue

        # Process the weeks data
        for w in weeks:
            contribution_days = w.get("contributionDays", [])
            for d in contribution_days:
                date_str = d.get("date")
                if not date_str:
                    continue
                try:
                    date_obj = dt.date.fromisoformat(date_str)
                    if start <= date_obj <= end:
                        out[date_str] = d.get("contributionCount", 0)
                except ValueError as exc:
                    debug_swallowed_exception("Contribution calendar date parsing", exc)
                    continue

        # Move to next chunk
        current_start = chunk_end + dt.timedelta(days=1)

    return out


# Returns a stable contribution count for one day from a wider calendar window
def get_daily_contributions_count(username: str, day: dt.date, token: str) -> int:
    date_key = day.isoformat()
    window_start = day - dt.timedelta(days=DAILY_CONTRIBUTION_LOOKBACK_DAYS - 1)
    data = get_daily_contributions(username, window_start, day, token)
    if date_key not in data:
        raise RuntimeError(f"No contribution count returned for {username} on {date_key}")
    return data[date_key]


# Checks count for today and decides whether to notify based on stored state.
def check_daily_contribs(username: str, token: str, state: dict, min_delta: int = 1, fail_threshold: int = 3) -> tuple[bool, int, bool]:
    day = today_local()

    try:
        curr = get_daily_contributions_count(username, day, token=token)
        state["consecutive_failures"] = 0
        state["last_error"] = None
    except Exception as e:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        state["last_error"] = sanitize_error_text(f"{type(e).__name__}: {e}")
        verbose_degraded_feature("Daily contribution count", "daily contribution change alerts", e)
        error_notify = state["consecutive_failures"] >= fail_threshold
        return False, state.get("count", 0), error_notify

    prev_day = state.get("day")
    prev_cnt = state.get("count")

    # New day -> reset baseline silently
    if prev_day != day:
        state["day"] = day
        state["count"] = curr
        state["prev_count"] = curr
        return False, curr, False  # no notify on rollover

    # Same day -> notify if change >= threshold
    if prev_cnt is not None and abs(curr - prev_cnt) >= min_delta:
        state["prev_count"] = prev_cnt
        state["count"] = curr
        return True, curr, False

    # No change
    state["count"] = curr
    return False, curr, False


# Returns whether a nullable profile field was fetched successfully and changed
def has_nullable_profile_field_changed(value, previous, unavailable):
    return value is not unavailable and value != previous


# Reports one unavailable profile field whose change alert cannot be evaluated
def report_unavailable_profile_field(label, value, unavailable):
    if value is unavailable:
        verbose_degraded_feature(f"Profile {label}", f"{label} change alerts")


# Monitors activity of the specified GitHub user
def github_monitor_user(user, csv_file_name):

    try:
        if csv_file_name:
            init_csv_file(csv_file_name)
    except Exception as e:
        print(f"* Error: {sanitize_error_text(e)}")

    followers_count = 0
    followings_count = 0
    repos_count = 0
    starred_count = 0
    available_events = 0
    events = []
    repos_list = []
    event_date: datetime | None = None
    blocked = None
    public = False
    contrib_state = {}
    contrib_curr = 0

    print("Sneaking into GitHub like a ninja ...")

    try:
        g = create_github_client("monitor initialization")
        auth_refresh_version = GITHUB_AUTH_REFRESH_VERSION
        debug_github_operation("authenticated viewer profile lookup")
        g_user_myself = g.get_user()
        user_myself_login = g_user_myself.login
        user_myself_name = g_user_myself.name
        user_myself_url = g_user_myself.html_url

        debug_github_operation("monitored user profile lookup", user)
        g_user = g.get_user(user)
        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url
        location = g_user.location
        bio = g_user.bio
        company = g_user.company
        email = g_user.email
        blog = g_user.blog
        account_created_date = g_user.created_at
        account_updated_date = g_user.updated_at

        followers_count = g_user.followers
        followings_count = g_user.following

        debug_github_operation("followers listing", user)
        followers_list = g_user.get_followers()
        debug_github_operation("followings listing", user)
        followings_list = g_user.get_following()

        if GET_ALL_REPOS:
            debug_github_operation("all repository listing", user)
            repos_list = g_user.get_repos()
            repos_count = g_user.public_repos
        else:
            debug_github_operation("owned repository listing", user)
            repos_list = [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login]
            repos_count = len(repos_list)

        debug_github_operation("starred repository listing", user)
        starred_list = g_user.get_starred()
        starred_count = starred_list.totalCount

        public = is_profile_public(g, user)
        blocked = is_blocked_by(user) if public else None

        if TRACK_CONTRIB_CHANGES:
            contrib_curr = get_daily_contributions_count(user, today_local(), token=GITHUB_TOKEN)
            contrib_state = {
                "day": today_local(),
                "count": contrib_curr,
                "prev_count": contrib_curr
            }

        if not DO_NOT_MONITOR_GITHUB_EVENTS:
            debug_github_operation("recent event listing", user)
            events = list(islice(g_user.get_events(), EVENTS_NUMBER))
            available_events = len(events)

    except Exception as e:
        print(f"\n* Error: {sanitize_error_text(e)}")
        sys.exit(1)

    last_event_id = 0
    last_event_ts: datetime | None = None
    events_list_of_ids = set()

    if not DO_NOT_MONITOR_GITHUB_EVENTS:
        if available_events:
            try:
                for event in reversed(events):
                    events_list_of_ids.add(event.id)

                newest = events[0]
                last_event_id = newest.id
                if last_event_id:
                    last_event_ts = newest.created_at
            except Exception as e:
                verbose_degraded_feature("Initial event identifiers", "new event alerts", e)
                print(f"\n* Cannot get event IDs / timestamps: {sanitize_error_text(e)}\n")

    followers_old_count = followers_count
    followings_old_count = followings_count
    repos_old_count = repos_count
    starred_old_count = starred_count

    user_name_old = user_name
    location_old = location
    bio_old = bio
    company_old = company
    email_old = email
    blog_old = blog
    blocked_old = blocked
    public_old = public

    last_event_id_old = last_event_id
    last_event_ts_old = last_event_ts
    events_list_of_ids_old = events_list_of_ids.copy()

    user_myself_name_str = user_myself_login
    if user_myself_name:
        user_myself_name_str += f" ({user_myself_name})"

    print(f"\nToken belongs to:\t\t{user_myself_name_str}" + f"\n\t\t\t\t[ {user_myself_url} ]" if user_myself_url else "")

    user_name_str = user_login
    if user_name:
        user_name_str += f" ({user_name})"

    print(f"\nUsername:\t\t\t{user_name_str}")
    print(f"User URL:\t\t\t{user_url}/")

    if location:
        print(f"Location:\t\t\t{location}")

    if company:
        print(f"Company:\t\t\t{company}")

    if email:
        print(f"Email:\t\t\t\t{email}")

    if blog:
        print(f"Blog URL:\t\t\t{blog}")

    print(f"\nPublic profile:\t\t\t{'Yes' if public else 'No'}")
    print(f"Blocked by the user:\t\t{'Unknown' if blocked is None else ('Yes' if blocked else 'No')}")

    print(f"\nAccount creation date:\t\t{get_date_from_ts(account_created_date)} ({calculate_timespan(int(time.time()), account_created_date, show_seconds=False)} ago)")
    print(f"Account updated date:\t\t{get_date_from_ts(account_updated_date)} ({calculate_timespan(int(time.time()), account_updated_date, show_seconds=False)} ago)")
    account_updated_date_old = account_updated_date

    print(f"\nFollowers:\t\t\t{followers_count}")
    print(f"Followings:\t\t\t{followings_count}")
    print(f"Repositories:\t\t\t{repos_count}")
    print(f"Starred repos:\t\t\t{starred_count}")
    if TRACK_CONTRIB_CHANGES:
        print(f"Today's contributions:\t\t{contrib_curr}")

    if not DO_NOT_MONITOR_GITHUB_EVENTS:
        print(f"Available events:\t\t{available_events}{'+' if available_events == EVENTS_NUMBER else ''}")

    if bio:
        print(f"\nBio:\n\n'{bio}'")

    print_cur_ts("\nTimestamp:\t\t\t")

    list_of_repos = []
    if repos_list and TRACK_REPOS_CHANGES:
        # Filter repos for detailed monitoring only (keep full repos_list for profile change detection)
        repos_list_filtered = repos_list
        if 'ALL' not in REPOS_TO_MONITOR:
            repos_list_filtered = []
            for repo in repos_list:
                # Check if repo matches any entry in REPOS_TO_MONITOR
                should_monitor = False
                for monitor_entry in REPOS_TO_MONITOR:
                    if '/' in monitor_entry:
                        # Format: 'user/repo_name' - check if user matches and repo matches
                        monitor_user, monitor_repo = monitor_entry.split('/', 1)
                        if monitor_user == user_login and monitor_repo == repo.name:
                            should_monitor = True
                            break
                    else:
                        # Format: just 'repo_name' (from CLI) - check if repo name matches for current user
                        if monitor_entry == repo.name and repo.owner.login == user_login:
                            should_monitor = True
                            break
                if should_monitor:
                    repos_list_filtered.append(repo)

        try:
            list_of_repos = github_process_repos(repos_list_filtered, fetch_identity_lists=(user_login.casefold() == user_myself_login.casefold()))
        except Exception as e:
            verbose_degraded_feature("Initial repository details", "repository detail alerts", e)
            print(f"* Cannot process list of public repositories: {sanitize_error_text(e)}")
        print_cur_ts("\nTimestamp:\t\t\t")

    list_of_repos_old = list_of_repos

    if not DO_NOT_MONITOR_GITHUB_EVENTS:
        print(f"Latest event:\n")

        if available_events == 0:
            print("There are no events yet")
        else:
            try:
                github_print_event(events[0], g, True)
            except Exception as e:
                verbose_degraded_feature("Initial event details", "complete event alerts", e)
                print(f"\n* Warning: cannot fetch last event details: {sanitize_error_text(e)}")

        print_cur_ts("\nTimestamp:\t\t\t")

    followers_old = []
    followings_old = []
    repos_old = []
    starred_old = []

    try:
        followers_old = [follower.login for follower in followers_list]
        followings_old = [following.login for following in followings_list]
        repos_old = [repo.name for repo in repos_list]
        starred_old = [star.full_name for star in starred_list]
    except Exception as e:
        print(f"* Error: {sanitize_error_text(e)}")
        sys.exit(1)

    verbose_print(f"Initial snapshot completed for {user}")
    debug_monitor_wait_timing("initial monitoring interval", GITHUB_CHECK_INTERVAL)
    time.sleep(GITHUB_CHECK_INTERVAL)
    alive_counter = 0
    email_sent = False
    profile_field_unavailable = object()
    check_number = 0

    # Primary loop
    while True:
        check_number += 1
        check_started_at = debug_monitor_check_start(check_number, user)

        try:
            if auth_refresh_version != GITHUB_AUTH_REFRESH_VERSION:
                g = create_github_client("monitor authentication reload")
                debug_github_operation("authenticated viewer profile lookup after reload")
                g_user_myself = g.get_user()
                user_myself_login = g_user_myself.login
                user_myself_name = g_user_myself.name
                user_myself_url = g_user_myself.html_url
                auth_refresh_version = GITHUB_AUTH_REFRESH_VERSION
                print("* GitHub API client recreated after token reload")
            debug_github_operation("monitored user profile refresh", user)
            g_user = g.get_user(user)
            email_sent = False

        except (GithubException, Exception) as e:
            safe_error = sanitize_error_text(e)
            verbose_degraded_feature("Monitored user refresh", "all profile, repository and event alerts", e)
            print(f"* Error, retrying in {display_time(GITHUB_CHECK_INTERVAL)}: {safe_error}")

            should_notify = False
            reason_msg = None

            if isinstance(e, BadCredentialsException):
                reason_msg = "GitHub token might not be valid anymore (bad credentials error)!"
            else:
                matched = next((msg for msg in ["Forbidden", "Bad Request"] if msg in str(e)), None)
                if matched:
                    reason_msg = f"Session might not be valid ('{matched}' error)"

            if reason_msg:
                print(f"* {reason_msg}")
                should_notify = True

            if should_notify and (ERROR_NOTIFICATION or webhook_event_enabled("error")) and not email_sent:
                m_subject = f"github_monitor: session error! (user: {user})"
                m_body = f"{reason_msg}\n{safe_error}{get_cur_ts(nl_ch + nl_ch + 'Timestamp: ')}"
                m_body_html = (
                    f"<html><head></head><body>"
                    f"<b>{html.escape(reason_msg or '')}</b><br>"
                    f"{html.escape(safe_error)}{get_cur_ts('<br><br>Timestamp: ')}"
                    f"</body></html>"
                )
                send_notification_channels("error", m_subject, m_body, m_body_html, ERROR_NOTIFICATION)
                email_sent = True

            print_cur_ts("Timestamp:\t\t\t")
            debug_monitor_wait_timing("monitored user refresh failure", GITHUB_CHECK_INTERVAL)
            time.sleep(GITHUB_CHECK_INTERVAL)
            continue

        # Changed followings
        try:
            debug_github_operation("followings refresh", user)
            followings_raw = list(gh_call(g_user.get_following)())
            followings_count = gh_call(lambda: g_user.following)()  # noqa: B023
        except NET_ERRORS as e:
            verbose_degraded_feature("Followings", "following change alerts", e)
            print(f"* Error while fetching followings: {sanitize_error_text(e)}")
            print_cur_ts("Timestamp:\t\t\t")
            followings_raw = None
            followings_count = None

        if followings_raw is not None and followings_count is not None:
            followings_old, followings_old_count = handle_profile_change("Followings", followings_old_count, followings_count, followings_old, followings_raw, user, csv_file_name, field="login")

        # Changed followers
        try:
            debug_github_operation("followers refresh", user)
            followers_raw = list(gh_call(g_user.get_followers)())
            followers_count = gh_call(lambda: g_user.followers)()  # noqa: B023
        except NET_ERRORS as e:
            verbose_degraded_feature("Followers", "follower change alerts", e)
            print(f"* Error while fetching followers: {sanitize_error_text(e)}")
            print_cur_ts("Timestamp:\t\t\t")
            followers_raw = None
            followers_count = None

        if followers_raw is not None and followers_count is not None:
            followers_old, followers_old_count = handle_profile_change("Followers", followers_old_count, followers_count, followers_old, followers_raw, user, csv_file_name, field="login")

        # Changed public repositories
        try:
            if GET_ALL_REPOS:
                debug_github_operation("all repository refresh", user)
                repos_raw = list(gh_call(g_user.get_repos)())
                repos_count = gh_call(lambda: g_user.public_repos)()  # noqa: B023
            else:
                debug_github_operation("owned repository refresh", user)
                repos_raw = list(gh_call(lambda: [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login])())  # noqa: B023
                repos_count = len(repos_raw)
        except NET_ERRORS as e:
            verbose_degraded_feature("Repositories", "repository change alerts", e)
            print(f"* Error while fetching repositories: {sanitize_error_text(e)}")
            print_cur_ts("Timestamp:\t\t\t")
            repos_raw = None
            repos_count = None

        if repos_raw is not None and repos_count is not None:
            repos_old, repos_old_count = handle_profile_change("Repos", repos_old_count, repos_count, repos_old, repos_raw, user, csv_file_name, field="name")

        # Changed starred repositories
        try:
            debug_github_operation("starred repository refresh", user)
            starred_raw = gh_call(g_user.get_starred)()
            if starred_raw is not None:
                starred_list = list(starred_raw)
                starred_count = starred_raw.totalCount
            else:
                starred_list = None
                starred_count = None
        except NET_ERRORS as e:
            verbose_degraded_feature("Starred repositories", "starred repository change alerts", e)
            print(f"* Error while fetching starred repositories: {sanitize_error_text(e)}")
            print_cur_ts("Timestamp:\t\t\t")
            starred_list = None
            starred_count = None

        if starred_list is not None and starred_count is not None:
            starred_old, starred_old_count = handle_profile_change("Starred Repos", starred_old_count, starred_count, starred_old, starred_list, user, csv_file_name, field="full_name")

        # Changed contributions in a day
        if TRACK_CONTRIB_CHANGES:
            contrib_notify, contrib_curr, contrib_error_notify = check_daily_contribs(user, GITHUB_TOKEN, contrib_state, min_delta=1, fail_threshold=3)
            if contrib_error_notify and (ERROR_NOTIFICATION or webhook_event_enabled("error")):
                failures = contrib_state.get("consecutive_failures", 0)
                last_err = contrib_state.get("last_error", "Unknown error")
                err_msg = f"Error: GitHub daily contributions check failed {failures} times. Last error: {last_err}\n"
                print(err_msg)
                err_msg_html = (
                    f"<html><head></head><body>"
                    f"Error: GitHub daily contributions check failed <b>{failures}</b> times. Last error: <b>{html.escape(str(last_err))}</b><br>"
                    f"{get_cur_ts('<br>Timestamp: ')}"
                    f"</body></html>"
                )
                send_notification_channels("error", f"GitHub monitor errors for {user}", err_msg + get_cur_ts(nl_ch + "Timestamp: "), err_msg_html, ERROR_NOTIFICATION)

            if contrib_notify:
                contrib_old = contrib_state.get("prev_count")
                print(f"* Daily contributions changed for user {user} on {get_short_date_from_ts(contrib_state['day'], show_hour=False)} from {contrib_old} to {contrib_curr}!\n")

                try:
                    if csv_file_name:
                        write_csv_entry(csv_file_name, now_local_naive(), "Daily Contribs", user, contrib_old, contrib_curr)
                except Exception as e:
                    print(f"* Error: {sanitize_error_text(e)}")

                m_subject = f"GitHub user {user} daily contributions changed from {contrib_old} to {contrib_curr}!"
                m_body = (f"GitHub user {user} daily contributions changed on {get_short_date_from_ts(contrib_state['day'], show_hour=False)} from {contrib_old} to {contrib_curr}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
                m_body_html = (
                    f"<html><head></head><body>"
                    f"GitHub user <b>{html.escape(user)}</b> daily contributions changed on <b>{html.escape(get_short_date_from_ts(contrib_state['day'], show_hour=False))}</b> from <b>{contrib_old}</b> to <b>{contrib_curr}</b><br><br>"
                    f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                    f"</body></html>"
                )

                send_notification_channels("contrib", m_subject, m_body, m_body_html, CONTRIB_NOTIFICATION)

                print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
                print_cur_ts("Timestamp:\t\t\t")

        # Changed bio
        bio = gh_call(lambda: g_user.bio, default=profile_field_unavailable)()  # noqa: B023
        report_unavailable_profile_field("bio", bio, profile_field_unavailable)
        if has_nullable_profile_field_changed(bio, bio_old, profile_field_unavailable):
            print(f"* Bio has changed for user {user} !\n")
            print(f"Old bio:\n\n{bio_old}\n")
            print(f"New bio:\n\n{bio}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Bio", user, bio_old, bio)
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} bio has changed!"
            m_body = f"GitHub user {user} bio has changed\n\nOld bio:\n\n{bio_old}\n\nNew bio:\n\n{bio}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
            bio_old_html = markdown_to_html(bio_old, convert_line_breaks=True) if bio_old else ""
            bio_html = markdown_to_html(bio, convert_line_breaks=True) if bio else ""
            m_body_html = (
                f"<html><head></head><body>"
                f"GitHub user <b>{html.escape(user)}</b> bio has changed<br><br>"
                f"Old bio:<br><br>{bio_old_html}<br><br>"
                f"New bio:<br><br>{bio_html}<br><br>"
                f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                f"</body></html>"
            )

            send_notification_channels("profile", m_subject, m_body, m_body_html, PROFILE_NOTIFICATION)

            bio_old = bio
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed location
        location = gh_call(lambda: g_user.location, default=profile_field_unavailable)()  # noqa: B023
        report_unavailable_profile_field("location", location, profile_field_unavailable)
        if has_nullable_profile_field_changed(location, location_old, profile_field_unavailable):
            print(f"* Location has changed for user {user} !\n")
            print(f"Old location:\t\t\t{location_old}\n")
            print(f"New location:\t\t\t{location}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Location", user, location_old, location)
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} location has changed!"
            m_body = f"GitHub user {user} location has changed\n\nOld location: {location_old}\n\nNew location: {location}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
            m_body_html = (
                f"<html><head></head><body>"
                f"GitHub user <b>{html.escape(user)}</b> location has changed<br><br>"
                f"Old location: <b>{html.escape(location_old or '')}</b><br><br>"
                f"New location: <b>{html.escape(location or '')}</b><br><br>"
                f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                f"</body></html>"
            )

            send_notification_channels("profile", m_subject, m_body, m_body_html, PROFILE_NOTIFICATION)

            location_old = location
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed user name
        user_name = gh_call(lambda: g_user.name, default=profile_field_unavailable)()  # noqa: B023
        report_unavailable_profile_field("name", user_name, profile_field_unavailable)
        if has_nullable_profile_field_changed(user_name, user_name_old, profile_field_unavailable):
            print(f"* User name has changed for user {user} !\n")
            print(f"Old user name:\t\t\t{user_name_old}\n")
            print(f"New user name:\t\t\t{user_name}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "User Name", user, user_name_old, user_name)
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} name has changed!"
            m_body = f"GitHub user {user} name has changed\n\nOld user name: {user_name_old}\n\nNew user name: {user_name}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
            m_body_html = (
                f"<html><head></head><body>"
                f"GitHub user <b>{html.escape(user)}</b> name has changed<br><br>"
                f"Old user name: <b>{html.escape(user_name_old or '')}</b><br><br>"
                f"New user name: <b>{html.escape(user_name or '')}</b><br><br>"
                f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                f"</body></html>"
            )

            send_notification_channels("profile", m_subject, m_body, m_body_html, PROFILE_NOTIFICATION)

            user_name_old = user_name
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed company
        company = gh_call(lambda: g_user.company, default=profile_field_unavailable)()  # noqa: B023
        report_unavailable_profile_field("company", company, profile_field_unavailable)
        if has_nullable_profile_field_changed(company, company_old, profile_field_unavailable):
            print(f"* User company has changed for user {user} !\n")
            print(f"Old company:\t\t\t{company_old}\n")
            print(f"New company:\t\t\t{company}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Company", user, company_old, company)
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} company has changed!"
            m_body = f"GitHub user {user} company has changed\n\nOld company: {company_old}\n\nNew company: {company}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
            m_body_html = (
                f"<html><head></head><body>"
                f"GitHub user <b>{html.escape(user)}</b> company has changed<br><br>"
                f"Old company: <b>{html.escape(company_old or '')}</b><br><br>"
                f"New company: <b>{html.escape(company or '')}</b><br><br>"
                f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                f"</body></html>"
            )

            send_notification_channels("profile", m_subject, m_body, m_body_html, PROFILE_NOTIFICATION)

            company_old = company
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed email
        email = gh_call(lambda: g_user.email, default=profile_field_unavailable)()  # noqa: B023
        report_unavailable_profile_field("email", email, profile_field_unavailable)
        if has_nullable_profile_field_changed(email, email_old, profile_field_unavailable):
            print(f"* User email has changed for user {user} !\n")
            print(f"Old email:\t\t\t{email_old}\n")
            print(f"New email:\t\t\t{email}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Email", user, email_old, email)
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} email has changed!"
            m_body = f"GitHub user {user} email has changed\n\nOld email: {email_old}\n\nNew email: {email}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
            m_body_html = (
                f"<html><head></head><body>"
                f"GitHub user <b>{html.escape(user)}</b> email has changed<br><br>"
                f"Old email: <b>{html.escape(email_old or '')}</b><br><br>"
                f"New email: <b>{html.escape(email or '')}</b><br><br>"
                f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                f"</body></html>"
            )

            send_notification_channels("profile", m_subject, m_body, m_body_html, PROFILE_NOTIFICATION)

            email_old = email
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed blog URL
        blog = gh_call(lambda: g_user.blog, default=profile_field_unavailable)()  # noqa: B023
        report_unavailable_profile_field("blog URL", blog, profile_field_unavailable)
        if has_nullable_profile_field_changed(blog, blog_old, profile_field_unavailable):
            print(f"* User blog URL has changed for user {user} !\n")
            print(f"Old blog URL:\t\t\t{blog_old}\n")
            print(f"New blog URL:\t\t\t{blog}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Blog URL", user, blog_old, blog)
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} blog URL has changed!"
            m_body = f"GitHub user {user} blog URL has changed\n\nOld blog URL: {blog_old}\n\nNew blog URL: {blog}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            send_notification_channels("profile", m_subject, m_body, "", PROFILE_NOTIFICATION)

            blog_old = blog
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed account update date
        account_updated_date = gh_call(lambda: g_user.updated_at)()  # noqa: B023
        if account_updated_date is not None and account_updated_date != account_updated_date_old:
            print(f"* User account has been updated for user {user} ! (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})\n")
            print(f"Old account update date:\t{get_date_from_ts(account_updated_date_old)}\n")
            print(f"New account update date:\t{get_date_from_ts(account_updated_date)}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, convert_to_local_naive(account_updated_date), "Account Update Date", user, convert_to_local_naive(account_updated_date_old), convert_to_local_naive(account_updated_date))
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} account has been updated! (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})"
            m_body = f"GitHub user {user} account has been updated (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})\n\nOld account update date: {get_date_from_ts(account_updated_date_old)}\n\nNew account update date: {get_date_from_ts(account_updated_date)}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            send_notification_channels("profile", m_subject, m_body, "", PROFILE_NOTIFICATION)

            account_updated_date_old = account_updated_date
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Profile visibility changed
        public = is_profile_public(g, user)
        if public != public_old:

            def _get_profile_status(public):
                return "public" if public else "private"

            print(f"* User {user} has changed profile visibility to '{_get_profile_status(public)}' !\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Profile Visibility", user, _get_profile_status(public_old), _get_profile_status(public))
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} has changed profile visibility to '{_get_profile_status(public)}' !"
            m_body = f"GitHub user {user} has changed profile visibility to '{_get_profile_status(public)}' !\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            send_notification_channels("profile", m_subject, m_body, "", PROFILE_NOTIFICATION)

            public_old = public
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Blocked status changed
        blocked = is_blocked_by(user) if public else None

        if blocked is not None and blocked_old is None:
            blocked_old = blocked

        elif None not in (blocked_old, blocked) and blocked != blocked_old:

            def _get_blocked_status(blocked, public):
                return 'Unknown' if blocked is None else ('Yes' if blocked else 'No')

            print(f"* User {user} has {'blocked' if blocked else 'unblocked'} you!\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Block Status", user, _get_blocked_status(blocked_old, public), _get_blocked_status(blocked, public))
            except Exception as e:
                print(f"* Error: {sanitize_error_text(e)}")

            m_subject = f"GitHub user {user} has {'blocked' if blocked else 'unblocked'} you!"
            m_body = f"GitHub user {user} has {'blocked' if blocked else 'unblocked'} you!\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            send_notification_channels("profile", m_subject, m_body, "", PROFILE_NOTIFICATION)

            blocked_old = blocked
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        list_of_repos = []

        # Changed repos details
        if TRACK_REPOS_CHANGES:

            if GET_ALL_REPOS:
                repos_list = gh_call(g_user.get_repos)()
            else:
                debug_github_operation("owned repository detail refresh", user)
                repos_list = gh_call(lambda: [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login])()  # noqa: B023

            # Filter repos for detailed monitoring only (keep full repos_list for profile change detection)
            repos_list_filtered = repos_list
            if repos_list is not None and 'ALL' not in REPOS_TO_MONITOR:
                repos_list_filtered = []
                for repo in repos_list:
                    # Check if repo matches any entry in REPOS_TO_MONITOR
                    should_monitor = False
                    for monitor_entry in REPOS_TO_MONITOR:
                        if '/' in monitor_entry:
                            # Format: 'user/repo_name' - check if user matches and repo matches
                            monitor_user, monitor_repo = monitor_entry.split('/', 1)
                            if monitor_user == user_login and monitor_repo == repo.name:
                                should_monitor = True
                                break
                        else:
                            # Format: just 'repo_name' (from CLI) - check if repo name matches for current user
                            if monitor_entry == repo.name and repo.owner.login == user_login:
                                should_monitor = True
                                break
                    if should_monitor:
                        repos_list_filtered.append(repo)

            if repos_list_filtered is not None:
                try:
                    list_of_repos = github_process_repos(repos_list_filtered, show_progress=False, fetch_identity_lists=(user_login.casefold() == user_myself_login.casefold()))
                    list_of_repos_ok = True
                except Exception as e:
                    list_of_repos = list_of_repos_old
                    verbose_degraded_feature("Repository detail refresh", "repository detail alerts", e)
                    print(f"* Cannot process list of public repositories, keeping old list: {sanitize_error_text(e)}")
                    list_of_repos_ok = False

                if list_of_repos_ok:

                    for repo in list_of_repos:
                        r_name = repo.get("name")
                        r_descr = repo.get("descr", "")
                        r_forks = repo.get("forks", 0)
                        r_stars = repo.get("stars", 0)
                        r_subscribers = repo.get("subscribers", 0)
                        r_url = repo.get("url", "")
                        r_update = repo.get("update_date")
                        r_stargazers_list = repo.get("stargazers_list")
                        r_subscribers_list = repo.get("subscribers_list")
                        r_forked_repos = repo.get("forked_repos")
                        r_issues = repo.get("issues")
                        r_pulls = repo.get("pulls")
                        r_discussions = repo.get("discussions")
                        r_issues_list = repo.get("issues_list")
                        r_pulls_list = repo.get("pulls_list")
                        r_discussions_list = repo.get("discussions_list")

                        for repo_old in list_of_repos_old:
                            r_name_old = repo_old.get("name")
                            if r_name_old == r_name:
                                r_descr_old = repo_old.get("descr", "")
                                r_forks_old = repo_old.get("forks", 0)
                                r_stars_old = repo_old.get("stars", 0)
                                r_subscribers_old = repo_old.get("subscribers", 0)
                                r_update_old = repo_old.get("update_date")
                                r_stargazers_list_old = repo_old.get("stargazers_list")
                                r_subscribers_list_old = repo_old.get("subscribers_list")
                                r_forked_repos_old = repo_old.get("forked_repos")
                                r_issues_old = repo_old.get("issues")
                                r_pulls_old = repo_old.get("pulls")
                                r_discussions_old = repo_old.get("discussions")
                                r_issues_list_old = repo_old.get("issues_list")
                                r_pulls_list_old = repo_old.get("pulls_list")
                                r_discussions_list_old = repo_old.get("discussions_list")

                                # Update date for repo changed
                                if r_update != r_update_old:
                                    r_message = f"* Repo '{r_name}' update date changed (after {calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)})\n* Repo URL: {r_url}\n\nOld repo update date:\t{get_date_from_ts(r_update_old)}\n\nNew repo update date:\t{get_date_from_ts(r_update)}\n"
                                    print(r_message)
                                    try:
                                        if csv_file_name:
                                            write_csv_entry(csv_file_name, now_local_naive(), "Repo Update Date", r_name, convert_to_local_naive(r_update_old), convert_to_local_naive(r_update))
                                    except Exception as e:
                                        print(f"* Error: {sanitize_error_text(e)}")
                                    m_subject = f"GitHub user {user} repo '{r_name}' update date has changed ! (after {calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)})"
                                    m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
                                    timespan_str = calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)
                                    m_body_html = (
                                        f"<html><head></head><body>"
                                        f"* Repo '<b>{html.escape(r_name)}</b>' update date changed (after <b>{html.escape(timespan_str)}</b>)<br>"
                                        f"* Repo URL: <a href=\"{html.escape(r_url)}\">{html.escape(r_url)}</a><br><br>"
                                        f"Old repo update date: <b>{html.escape(get_date_from_ts(r_update_old))}</b><br><br>"
                                        f"New repo update date: <b>{html.escape(get_date_from_ts(r_update))}</b><br><br>"
                                        f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                                        f"</body></html>"
                                    )
                                    send_notification_channels("repo_update", m_subject, m_body, m_body_html, REPO_UPDATE_DATE_NOTIFICATION)
                                    print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
                                    print_cur_ts("Timestamp:\t\t\t")

                                # Number of stars for repo changed
                                check_repo_list_changes(r_stars_old, r_stars, r_stargazers_list_old, r_stargazers_list, "Stargazers", r_name, r_url, user, csv_file_name)

                                # Number of watchers/subscribers for repo changed
                                check_repo_list_changes(r_subscribers_old, r_subscribers, r_subscribers_list_old, r_subscribers_list, "Watchers", r_name, r_url, user, csv_file_name)

                                # Number of forks for repo changed
                                check_repo_list_changes(r_forks_old, r_forks, r_forked_repos_old, r_forked_repos, "Forks", r_name, r_url, user, csv_file_name)

                                # Number of issues for repo changed
                                check_repo_list_changes(r_issues_old, r_issues, r_issues_list_old, r_issues_list, "Issues", r_name, r_url, user, csv_file_name)

                                # Number of PRs for repo changed
                                check_repo_list_changes(r_pulls_old, r_pulls, r_pulls_list_old, r_pulls_list, "Pull Requests", r_name, r_url, user, csv_file_name)

                                # Number of discussions for repo changed
                                if r_discussions is not None and r_discussions_old is not None:
                                    check_repo_list_changes(r_discussions_old, r_discussions, r_discussions_list_old, r_discussions_list, "Discussions", r_name, r_url, user, csv_file_name)
                                elif r_discussions is None:
                                    verbose_degraded_feature(f"Discussions for {r_name}", "discussion change alerts")
                                    repo["discussions"] = r_discussions_old
                                    repo["discussions_list"] = r_discussions_list_old

                                # Repo description changed
                                if r_descr != r_descr_old:
                                    r_message = f"* Repo '{r_name}' description changed from:\n\n'{r_descr_old}'\n\nto:\n\n'{r_descr}'\n\n* Repo URL: {r_url}\n"
                                    print(r_message)
                                    try:
                                        if csv_file_name:
                                            write_csv_entry(csv_file_name, now_local_naive(), "Repo Description", r_name, r_descr_old, r_descr)
                                    except Exception as e:
                                        print(f"* Error: {sanitize_error_text(e)}")
                                    m_subject = f"GitHub user {user} repo '{r_name}' description has changed !"
                                    m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
                                    r_descr_old_html = markdown_to_html(r_descr_old, convert_line_breaks=True) if r_descr_old else ""
                                    r_descr_html = markdown_to_html(r_descr, convert_line_breaks=True) if r_descr else ""
                                    m_body_html = (
                                        f"<html><head></head><body>"
                                        f"* Repo '<b>{html.escape(r_name)}</b>' description changed from:<br><br>"
                                        f"'{r_descr_old_html}'<br><br>"
                                        f"to:<br><br>"
                                        f"'{r_descr_html}'<br><br>"
                                        f"* Repo URL: <a href=\"{html.escape(r_url)}\">{html.escape(r_url)}</a><br><br>"
                                        f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                                        f"</body></html>"
                                    )
                                    send_notification_channels("repo", m_subject, m_body, m_body_html, REPO_NOTIFICATION)
                                    print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
                                    print_cur_ts("Timestamp:\t\t\t")

                    list_of_repos_old = list_of_repos

        # New GitHub events
        if not DO_NOT_MONITOR_GITHUB_EVENTS:
            debug_github_operation("recent event refresh", user)
            events = list(gh_call(lambda: list(islice(g_user.get_events(), EVENTS_NUMBER)))())  # noqa: B023
            if events is not None:
                available_events = len(events)
                if available_events == 0:
                    last_event_id = 0
                    last_event_ts = None
                else:
                    try:
                        newest = events[0]
                        last_event_id = newest.id
                        if last_event_id:
                            last_event_ts = newest.created_at
                    except Exception as e:
                        last_event_id = 0
                        last_event_ts = None
                        verbose_degraded_feature("Newest event identifiers", "new event alerts", e)
                        print(f"* Cannot get last event ID / timestamp: {sanitize_error_text(e)}")
                        print_cur_ts("Timestamp:\t\t\t")

                events_list_of_ids = set()
                first_new = True

                # New events showed up
                if last_event_id and last_event_id != last_event_id_old:

                    for event in reversed(events):

                        events_list_of_ids.add(event.id)

                        if event.id in events_list_of_ids_old:
                            continue

                        if event.type in EVENTS_TO_MONITOR or 'ALL' in EVENTS_TO_MONITOR:

                            event_date = None
                            repo_name = ""
                            repo_url = ""
                            event_text = ""

                            try:
                                event_date, repo_name, repo_url, event_text = github_print_event(event, g, first_new, last_event_ts_old)
                            except Exception as e:
                                verbose_degraded_feature("New event details", "complete event alerts", e)
                                print(f"\n* Warning, cannot fetch all event details: {sanitize_error_text(e)}")

                            first_new = False

                            if event_date and repo_name and event_text:

                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                                except Exception as e:
                                    print(f"* Error: {sanitize_error_text(e)}")

                                m_subject = f"GitHub user {user} has new {event.type} (repo: {repo_name})"
                                m_body = f"GitHub user {user} has new {event.type} event\n\n{event_text}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
                                event_payload = None
                                try:
                                    if hasattr(event, 'payload'):
                                        event_payload = event.payload
                                except Exception as exc:
                                    verbose_degraded_feature("Event payload", "complete event notification details", exc)
                                event_text_html = event_text_to_html(event_text, event.type, event_payload)
                                m_body_html = (
                                    f"<html><head></head><body>"
                                    f"GitHub user <b>{html.escape(user)}</b> has new <b>{html.escape(event.type)}</b> event<br><br>"
                                    f"{event_text_html}<br>"
                                    f"Check interval: <b>{html.escape(display_time(GITHUB_CHECK_INTERVAL))}</b> ({html.escape(get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True))}){get_cur_ts('<br>Timestamp: ')}"
                                    f"</body></html>"
                                )

                                send_notification_channels("event", m_subject, m_body, m_body_html, EVENT_NOTIFICATION)

                            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
                            print_cur_ts("Timestamp:\t\t\t")

                    last_event_id_old = last_event_id
                    last_event_ts_old = last_event_ts
                    events_list_of_ids_old = events_list_of_ids.copy()
            else:
                verbose_degraded_feature("Recent events", "new event alerts")

        alive_counter += 1

        if LIVENESS_CHECK_COUNTER and alive_counter >= LIVENESS_CHECK_COUNTER:
            verbose_print(f"Monitoring healthy for {user}. No tracked change since the last check")
            print_cur_ts("Liveness check, timestamp:\t")
            alive_counter = 0

        verbose_print(f"Monitoring check #{check_number} completed for {user}")
        debug_monitor_check_timing(check_number, user, check_started_at, GITHUB_CHECK_INTERVAL)
        debug_monitor_wait_timing("normal monitoring interval", GITHUB_CHECK_INTERVAL)
        time.sleep(GITHUB_CHECK_INTERVAL)


# Applies validated one-run webhook command-line overrides to runtime settings
def apply_webhook_cli_overrides(args: argparse.Namespace, parser: argparse.ArgumentParser, report_warnings=True) -> None:
    global WEBHOOK_ENABLED, WEBHOOK_URL, WEBHOOK_PROVIDER, WEBHOOK_PROFILE_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION, WEBHOOK_ERROR_NOTIFICATION, SECRET_SOURCES
    if args.webhook_provider is not None:
        WEBHOOK_PROVIDER = str(args.webhook_provider)
    if args.webhook_url is not None:
        if not validate_webhook_url(args.webhook_url):
            parser.error("--webhook-url must contain a complete HTTPS link without embedded credentials")
        WEBHOOK_URL = str(args.webhook_url).strip()
        WEBHOOK_ENABLED = True
        SECRET_SOURCES["WEBHOOK_URL"] = "command line"
        debug_print("Secret resolution name=WEBHOOK_URL source=command line")
    if args.webhook_enabled is not None:
        WEBHOOK_ENABLED = args.webhook_enabled
    if args.webhook_profile is True:
        WEBHOOK_ENABLED = True
        WEBHOOK_PROFILE_NOTIFICATION = True
    if args.webhook_events is True:
        WEBHOOK_ENABLED = True
        WEBHOOK_EVENT_NOTIFICATION = True
    if args.webhook_repo_changes is True:
        WEBHOOK_ENABLED = True
        WEBHOOK_REPO_NOTIFICATION = True
    if args.webhook_repo_update_date is True:
        WEBHOOK_ENABLED = True
        WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION = True
    if args.webhook_daily_contribs is True:
        WEBHOOK_ENABLED = True
        WEBHOOK_CONTRIB_NOTIFICATION = True
    if args.webhook_errors is not None:
        WEBHOOK_ERROR_NOTIFICATION = args.webhook_errors
        if args.webhook_errors:
            WEBHOOK_ENABLED = True
    if args.webhook_provider is None:
        detected_provider = detect_webhook_provider(WEBHOOK_URL)
        configured_provider = normalized_webhook_provider()
        if detected_provider and detected_provider != configured_provider:
            WEBHOOK_PROVIDER = detected_provider
            verbose_print(f"Selected webhook provider {detected_provider} from the destination URL")
            if report_warnings:
                print(f"* Warning: Configured webhook provider did not match the URL. Using {detected_provider}.")


# Applies monitoring, output and email command-line overrides to effective settings
def apply_monitoring_cli_overrides(args: argparse.Namespace, parser: argparse.ArgumentParser, strict=True) -> None:
    global CSV_FILE, DISABLE_LOGGING, PROFILE_NOTIFICATION, EVENT_NOTIFICATION, REPO_NOTIFICATION, REPO_UPDATE_DATE_NOTIFICATION, ERROR_NOTIFICATION, GITHUB_CHECK_INTERVAL, LIVENESS_CHECK_COUNTER, DO_NOT_MONITOR_GITHUB_EVENTS, TRACK_REPOS_CHANGES, REPOS_TO_MONITOR, GET_ALL_REPOS, CONTRIB_NOTIFICATION, TRACK_CONTRIB_CHANGES, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION
    if args.check_interval is not None:
        GITHUB_CHECK_INTERVAL = args.check_interval
    if args.csv_file is not None:
        CSV_FILE = os.path.expanduser(args.csv_file)
    elif CSV_FILE:
        CSV_FILE = os.path.expanduser(CSV_FILE)
    if args.disable_logging is True:
        DISABLE_LOGGING = True
    if args.notify_profile is True:
        PROFILE_NOTIFICATION = True
    if args.notify_events is True:
        EVENT_NOTIFICATION = True
    if args.notify_repo_changes is True:
        REPO_NOTIFICATION = True
    if args.notify_repo_update_date is True:
        REPO_UPDATE_DATE_NOTIFICATION = True
    if args.notify_daily_contribs is True:
        CONTRIB_NOTIFICATION = True
    if args.notify_errors is False:
        ERROR_NOTIFICATION = False
    if args.track_repos_changes is True:
        TRACK_REPOS_CHANGES = True
    if args.repos is not None:
        if not TRACK_REPOS_CHANGES:
            if strict:
                parser.error("--repos requires -j/--track-repos-changes to be enabled")
        else:
            REPOS_TO_MONITOR = [repo.strip() for repo in args.repos.split(',') if repo.strip()]
    if args.track_contribs_changes is True:
        TRACK_CONTRIB_CHANGES = True
    if args.no_monitor_events is True:
        DO_NOT_MONITOR_GITHUB_EVENTS = True
    if args.get_all_repos is True:
        GET_ALL_REPOS = True
    if not TRACK_REPOS_CHANGES:
        REPO_NOTIFICATION = False
        REPO_UPDATE_DATE_NOTIFICATION = False
        WEBHOOK_REPO_NOTIFICATION = False
        WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION = False
    if not TRACK_CONTRIB_CHANGES:
        CONTRIB_NOTIFICATION = False
        WEBHOOK_CONTRIB_NOTIFICATION = False
    if DO_NOT_MONITOR_GITHUB_EVENTS:
        EVENT_NOTIFICATION = False
        WEBHOOK_EVENT_NOTIFICATION = False
    intervals_valid = type(GITHUB_CHECK_INTERVAL) is int and GITHUB_CHECK_INTERVAL > 0 and isinstance(LIVENESS_CHECK_INTERVAL, (int, float)) and not isinstance(LIVENESS_CHECK_INTERVAL, bool) and LIVENESS_CHECK_INTERVAL >= 0
    LIVENESS_CHECK_COUNTER = LIVENESS_CHECK_INTERVAL / GITHUB_CHECK_INTERVAL if intervals_valid else 0


# Returns the final log file path without creating its directory or file
def resolve_output_log_path(username):
    log_path = Path(os.path.expanduser(GITHUB_LOGFILE))
    if log_path.parent != Path('.'):
        if log_path.suffix == "":
            log_path = log_path.parent / f"{log_path.name}_{username or 'target'}.log"
    elif log_path.suffix == "":
        log_path = Path(f"{log_path.name}_{username or 'target'}.log")
    return log_path


@dataclass(frozen=True)
class DoctorCheck:
    section: str
    status: str
    label: str
    detail: str = ""
    fix: str = ""
    guide: str = DOCTOR_GUIDE_URL


@dataclass
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)
    github_token: str = ""
    authenticated_login: str = ""
    github_client: Any = None
    target_profile: Any = None
    target_name: str = ""
    email_ready: bool = False
    webhook_ready: bool = False

    # Adds one validated result row to the report
    def add(self, section, status, label, detail="", fix="", guide=DOCTOR_GUIDE_URL):
        normalized_status = str(status).upper()
        if normalized_status not in {"PASS", "WARN", "FAIL", "SKIP"}:
            raise ValueError(f"Unsupported doctor status {status}")
        if normalized_status != "PASS" and not fix:
            raise ValueError(f"Doctor {normalized_status} rows require a fix")
        self.checks.append(DoctorCheck(section, normalized_status, label, detail, fix, guide))

    # Counts failed checks including approved delivery tests
    @property
    def failure_count(self):
        return sum(check.status == "FAIL" for check in self.checks)

    # Counts warnings while excluding declined optional tests
    @property
    def warning_count(self):
        return sum(check.status == "WARN" for check in self.checks)


class DoctorProgress:
    # Resolves the real terminal beneath a logger wrapper
    def __init__(self, stream=None):
        self.stream = sys.stdout if stream is None else stream
        self.terminal = self.stream
        while isinstance(self.terminal, (Logger, TerminalStream)):
            self.terminal = self.terminal.terminal
        self.width = 0

    # Writes one transient progress label only to an interactive terminal
    def show(self, label):
        self.clear()
        if VERBOSE_MODE or DEBUG_MODE:
            return
        try:
            interactive = bool(self.terminal.isatty())
        except Exception as exc:
            debug_swallowed_exception("Doctor terminal detection", exc)
            interactive = False
        if not interactive:
            return
        safe_label = ANSI_ESCAPE_RE.sub("", sanitize_terminal_text(str(label)))
        message = f"* Checking {safe_label} ..."
        self.terminal.write(message + "\r")
        self.terminal.flush()
        self.width = len(message)

    # Erases any transient progress text without affecting piped output
    def clear(self):
        if not self.width:
            return
        self.terminal.write(" " * self.width + "\r")
        self.terminal.flush()
        self.width = 0


# Returns whether one importable dependency is available to this runtime
def doctor_dependency_available(module_name, module_finder=None):
    finder = importlib.util.find_spec if module_finder is None else module_finder
    try:
        return finder(module_name) is not None
    except Exception as exc:
        debug_swallowed_exception(f"Dependency lookup for {module_name}", exc)
        return False


# Adds Python, required dependency, optional dependency and install checks
def doctor_check_environment(report, module_finder=None):
    version = platform.python_version()
    minimum = ".".join(str(part) for part in MIN_PYTHON_VERSION)
    if sys.version_info >= MIN_PYTHON_VERSION:
        report.add("Environment", "PASS", f"Python {version} is supported", f"Minimum supported version: {minimum}")
    else:
        report.add("Environment", "FAIL", f"Python {version} is unsupported", f"Minimum supported version: {minimum}", f"Install Python {minimum} or newer")
    required = (("requests", "requests"), ("urllib3", "urllib3"), ("python-dateutil", "dateutil"), ("pytz", "pytz"), ("PyGithub", "github"))
    for package_name, module_name in required:
        if doctor_dependency_available(module_name, module_finder):
            report.add("Environment", "PASS", f"Required dependency {package_name} is installed")
        else:
            install_command = shlex.join([sys.executable, "-m", "pip", "install", package_name])
            report.add("Environment", "FAIL", f"Required dependency {package_name} is missing", "The monitor cannot run its required path without this package", f"Install it with: {install_command}")
    optional = (("python-dotenv", "dotenv", "dotenv discovery and loading"), ("tzlocal", "tzlocal", "automatic timezone detection"))
    for package_name, module_name, feature in optional:
        if doctor_dependency_available(module_name, module_finder):
            report.add("Environment", "PASS", f"Optional dependency {package_name} is installed", f"Used only for {feature}")
        else:
            install_command = shlex.join([sys.executable, "-m", "pip", "install", package_name])
            report.add("Environment", "WARN", f"Optional dependency {package_name} is not installed", f"{feature.capitalize()} will not work while other features remain available", f"Install it with: {install_command}")


# Returns whether a URL is a complete credential-free HTTPS endpoint
def validate_github_endpoint_url(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value.strip())
    except ValueError as exc:
        debug_swallowed_exception("GitHub endpoint parsing", exc)
        return False
    return parsed.scheme.casefold() == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment


# Adds configuration, dotenv, private-setting and core value checks
def doctor_check_configuration(report, args, parser):
    global CLI_CONFIG_PATH, LOCAL_TIMEZONE
    config_discovery_disabled = isinstance(args.config_file, str) and args.config_file.casefold() == "none"
    if args.config_file and not config_discovery_disabled:
        CLI_CONFIG_PATH = os.path.expanduser(args.config_file)
    elif config_discovery_disabled:
        CLI_CONFIG_PATH = None
    cfg_path = None if config_discovery_disabled else find_config_file(CLI_CONFIG_PATH)
    configured_settings = set()
    config_errors = []
    retired_settings = set()
    if config_discovery_disabled:
        report.add("Configuration", "PASS", "Configuration discovery is disabled", "No configuration file was requested")
    elif CLI_CONFIG_PATH and not cfg_path:
        report.add("Configuration", "FAIL", "Configuration file was not found", f"Requested path: {CLI_CONFIG_PATH}", "Correct --config-file or generate a new configuration with --generate-config")
    elif cfg_path:
        loaded = load_config_file(cfg_path, report_errors=False, loaded_names_out=configured_settings, diagnostic_overrides=(args.verbose is True, args.debug is True), error_out=config_errors, retired_names_out=retired_settings)
        if loaded:
            report.add("Configuration", "PASS", "Configuration file loaded", f"Path: {cfg_path}")
        else:
            report.add("Configuration", "FAIL", "Configuration file could not be loaded", config_errors[0] if config_errors else f"Path: {cfg_path}", "Keep only documented SETTING = value lines with plain literal values or regenerate the file")
    else:
        report.add("Configuration", "PASS", "No configuration file selected", "Built-in defaults and other configured sources remain available")
    if retired_settings:
        listed = ", ".join(sorted(retired_settings))
        report.add("Configuration", "WARN", "Retired configuration settings were ignored", listed, "Remove the retired settings from the configuration file")
    apply_diagnostic_cli_overrides(args)
    dotenv_errors = []
    env_path = load_startup_secrets(args.env_file, configured_settings, report_errors=False, errors_out=dotenv_errors)
    apply_startup_cli_overrides(args, configured_settings)
    apply_webhook_cli_overrides(args, parser, report_warnings=False)
    if args.repos is not None and not (TRACK_REPOS_CHANGES or args.track_repos_changes is True):
        report.add("Configuration", "FAIL", "Repository selection cannot take effect", "--repos requires repository detail tracking", "Add --track-repos-changes or remove --repos")
    apply_monitoring_cli_overrides(args, parser, strict=False)
    if DOTENV_FILE and DOTENV_FILE.casefold() == "none":
        report.add("Configuration", "PASS", "Dotenv loading is disabled", "No dotenv file was requested")
    elif env_path and os.path.isfile(env_path) and not dotenv_errors:
        report.add("Configuration", "PASS", "Dotenv file loaded", f"Path: {env_path}")
    elif dotenv_errors:
        report.add("Configuration", "WARN", "Dotenv file could not be loaded", dotenv_errors[0], "Correct --env-file, install python-dotenv or disable dotenv loading with --env-file none")
    else:
        report.add("Configuration", "PASS", "No dotenv file selected", "Exported environment variables and config values remain available")
    source_order = ("dotenv file", "environment", "configuration file", "built-in configuration", "command line")
    source_labels = {"dotenv file": "Secrets loaded from the dotenv file", "environment": "Secrets loaded from the environment", "configuration file": "Secrets loaded from the configuration file", "built-in configuration": "Secrets loaded from the built-in configuration", "command line": "Secrets loaded from the command line"}
    source_rows = 0
    for source in source_order:
        names = sorted(name for name, actual_source in SECRET_SOURCES.items() if actual_source == source)
        if names:
            report.add("Configuration", "PASS", source_labels[source], ", ".join(names))
            source_rows += 1
    if not source_rows:
        report.add("Configuration", "PASS", "No secrets loaded", "No private setting source contributed a usable value")
    if VERIFY_SSL:
        report.add("Configuration", "PASS", "TLS certificate verification is on", "Every outbound request checks the server certificate")
    else:
        report.add("Configuration", "WARN", "TLS certificate verification is off", "VERIFY_SSL is False, so an intercepted connection cannot be told apart from the real service", "Set VERIFY_SSL back to True unless this network intercepts TLS with its own certificate authority", TLS_GUIDE_URL)
    if validate_github_endpoint_url(GITHUB_API_URL):
        report.add("Configuration", "PASS", "GitHub API URL is valid", diagnostic_endpoint(GITHUB_API_URL))
    else:
        report.add("Configuration", "FAIL", "GitHub API URL is invalid", sanitize_error_text(GITHUB_API_URL) or "No URL configured", "Set GITHUB_API_URL to a complete HTTPS URL without credentials, query parameters or fragments")
    if validate_github_endpoint_url(GITHUB_HTML_URL):
        report.add("Configuration", "PASS", "GitHub web URL is valid", diagnostic_endpoint(GITHUB_HTML_URL))
    else:
        report.add("Configuration", "FAIL", "GitHub web URL is invalid", sanitize_error_text(GITHUB_HTML_URL) or "No URL configured", "Set GITHUB_HTML_URL to a complete HTTPS URL without credentials, query parameters or fragments")
    if LOCAL_TIMEZONE == "Auto":
        if get_localzone is None:
            report.add("Configuration", "FAIL", "Automatic timezone detection is unavailable", "LOCAL_TIMEZONE is Auto but tzlocal is unavailable", "Install tzlocal or set LOCAL_TIMEZONE to a valid pytz timezone")
        else:
            try:
                detected_timezone = str(get_localzone())
            except Exception as exc:
                detected_timezone = ""
                debug_swallowed_exception("Doctor timezone detection", exc)
            if detected_timezone and is_valid_timezone(detected_timezone):
                LOCAL_TIMEZONE = detected_timezone
                report.add("Configuration", "PASS", "Local timezone can be detected", detected_timezone)
            else:
                report.add("Configuration", "FAIL", "Automatic timezone detection failed", "tzlocal did not return a supported timezone", "Set LOCAL_TIMEZONE to a valid pytz timezone")
    elif is_valid_timezone(LOCAL_TIMEZONE):
        report.add("Configuration", "PASS", "Local timezone is valid", str(LOCAL_TIMEZONE))
    else:
        report.add("Configuration", "FAIL", "Local timezone is invalid", sanitize_error_text(LOCAL_TIMEZONE), "Set LOCAL_TIMEZONE to a valid pytz timezone")
    if type(GITHUB_CHECK_INTERVAL) is int and GITHUB_CHECK_INTERVAL > 0:
        report.add("Configuration", "PASS", "Polling interval is valid", display_time(GITHUB_CHECK_INTERVAL))
    else:
        report.add("Configuration", "FAIL", "Polling interval is invalid", str(GITHUB_CHECK_INTERVAL), "Set GITHUB_CHECK_INTERVAL or --check-interval to a positive number of seconds")
    if TARGET_GITHUB_USERNAME:
        saved_target = wizard_normalize_target(TARGET_GITHUB_USERNAME)
        if saved_target:
            report.add("Configuration", "PASS", "Saved GitHub target is valid", saved_target)
        else:
            report.add("Configuration", "FAIL", "Saved GitHub target is invalid", sanitize_error_text(TARGET_GITHUB_USERNAME), "Set TARGET_GITHUB_USERNAME to a GitHub username or complete profile URL")
    if isinstance(CHECK_INTERNET_TIMEOUT, (int, float)) and not isinstance(CHECK_INTERNET_TIMEOUT, bool) and CHECK_INTERNET_TIMEOUT > 0:
        report.add("Configuration", "PASS", "Connectivity timeout is valid", f"{CHECK_INTERNET_TIMEOUT} seconds")
    else:
        report.add("Configuration", "FAIL", "Connectivity timeout is invalid", str(CHECK_INTERNET_TIMEOUT), "Set CHECK_INTERNET_TIMEOUT to a positive number of seconds")
    if type(EVENTS_NUMBER) is int and EVENTS_NUMBER > 0:
        report.add("Configuration", "PASS", "Recent event window is valid", f"{EVENTS_NUMBER} events")
    else:
        report.add("Configuration", "FAIL", "Recent event window is invalid", str(EVENTS_NUMBER), "Set EVENTS_NUMBER to a positive integer")
    retry_policy_valid = type(NET_MAX_RETRIES) is int and NET_MAX_RETRIES > 0 and isinstance(NET_BASE_BACKOFF_SEC, (int, float)) and not isinstance(NET_BASE_BACKOFF_SEC, bool) and NET_BASE_BACKOFF_SEC >= 0
    if retry_policy_valid:
        report.add("Configuration", "PASS", "GitHub retry policy is valid", f"Attempts: {NET_MAX_RETRIES} | Base backoff: {NET_BASE_BACKOFF_SEC} seconds")
    else:
        report.add("Configuration", "FAIL", "GitHub retry policy is invalid", f"NET_MAX_RETRIES={NET_MAX_RETRIES} | NET_BASE_BACKOFF_SEC={NET_BASE_BACKOFF_SEC}", "Use a positive retry count and a non-negative base backoff")
    if isinstance(LIVENESS_CHECK_INTERVAL, (int, float)) and not isinstance(LIVENESS_CHECK_INTERVAL, bool) and LIVENESS_CHECK_INTERVAL >= 0:
        report.add("Configuration", "PASS", "Liveness interval is valid", "Disabled" if not LIVENESS_CHECK_INTERVAL else display_time(LIVENESS_CHECK_INTERVAL))
    else:
        report.add("Configuration", "FAIL", "Liveness interval is invalid", str(LIVENESS_CHECK_INTERVAL), "Set LIVENESS_CHECK_INTERVAL to zero or a positive number of seconds")
    if DO_NOT_MONITOR_GITHUB_EVENTS:
        report.add("Configuration", "PASS", "Event type selection is not required", "GitHub event monitoring is disabled")
    elif isinstance(EVENTS_TO_MONITOR, (list, tuple)) and any(isinstance(value, str) and value.strip() for value in EVENTS_TO_MONITOR):
        report.add("Configuration", "PASS", "Event type selection is valid", f"Configured entries: {len(EVENTS_TO_MONITOR)}")
    else:
        report.add("Configuration", "FAIL", "Event type selection is invalid", "No usable event type is configured", "Add ALL or at least one supported event name to EVENTS_TO_MONITOR")
    try:
        ascii_log_separators_enabled()
        report.add("Configuration", "PASS", "Log separator mode is valid", str(ASCII_LOG_SEPARATORS))
    except ValueError as exc:
        report.add("Configuration", "FAIL", "Log separator mode is invalid", str(exc), "Set ASCII_LOG_SEPARATORS to Auto, On or Off")
    return cfg_path, env_path


# Adds a live token validation result and retains authenticated state for later checks
def doctor_check_authentication(report, request_get=None):
    report.github_token = str(GITHUB_TOKEN or "")
    if not report.github_token or report.github_token == "your_github_classic_personal_access_token":
        token_command = render_install_command(["--set-github-token"])
        report.add("Authentication", "FAIL", "GitHub token is missing", "No usable GITHUB_TOKEN was resolved", f"Create a token then run: {token_command}", AUTH_GUIDE_URL)
        return
    try:
        report.authenticated_login = validate_github_token(report.github_token, request_get=request_get)
        report.add("Authentication", "PASS", "GitHub token was accepted", f"Authenticated as: {report.authenticated_login}")
    except Exception as exc:
        detail = sanitize_error_text(exc).replace(" and the dotenv file was not changed", "")
        report.add("Authentication", "FAIL", "GitHub token validation failed", f"{type(exc).__name__}: {detail}", "Check the token, its access and GITHUB_API_URL then run doctor again", AUTH_GUIDE_URL)


# Adds one bounded connectivity check for the configured startup endpoint
def doctor_check_connectivity(report, request_get=None):
    if not validate_github_endpoint_url(CHECK_INTERNET_URL):
        report.add("Connectivity", "FAIL", "Connectivity check URL is invalid", sanitize_error_text(CHECK_INTERNET_URL) or "No URL configured", "Set CHECK_INTERNET_URL to a complete HTTPS URL")
        return
    get_request = req.get if request_get is None else request_get
    try:
        debug_http_request("GET", CHECK_INTERNET_URL, "doctor connectivity", CHECK_INTERNET_TIMEOUT)
        response = get_request(CHECK_INTERNET_URL, timeout=CHECK_INTERNET_TIMEOUT, allow_redirects=False, verify=VERIFY_SSL)
        status = getattr(response, "status_code", None)
        debug_http_response("GET", CHECK_INTERNET_URL, "doctor connectivity", status)
    except Exception as exc:
        report.add("Connectivity", "FAIL", "Configured connectivity endpoint is unreachable", f"{type(exc).__name__}: {sanitize_error_text(exc)}", "Check network, DNS, proxy and CHECK_INTERNET_URL settings")
        return
    if isinstance(status, int) and status < 500:
        report.add("Connectivity", "PASS", "Configured connectivity endpoint responded", f"{diagnostic_endpoint(CHECK_INTERNET_URL)} returned HTTP {status}")
    else:
        report.add("Connectivity", "FAIL", "Configured connectivity endpoint returned an error", f"HTTP {status}", "Retry later or correct CHECK_INTERNET_URL")


# Adds a target lookup and retains the fetched profile for feed checks
def doctor_check_target(report, github_factory=None):
    if not report.target_name:
        command = render_install_command(["GITHUB_USERNAME", "--doctor"])
        report.add("Target", "WARN", "No GitHub target was provided", "Nothing can be monitored until a username is supplied", f"Run doctor again with a target: {command}", QUICK_START_GUIDE_URL)
        return
    if not report.authenticated_login:
        report.add("Target", "FAIL", "GitHub target could not be checked", f"Target: {report.target_name}", "Fix GitHub authentication then run doctor again", AUTH_GUIDE_URL)
        return
    try:
        report.github_client = create_github_client("doctor target validation") if github_factory is None else github_factory()
        debug_github_operation("doctor target lookup", report.target_name)
        report.target_profile = report.github_client.get_user(report.target_name)
        resolved_login = str(getattr(report.target_profile, "login", report.target_name))
        report.add("Target", "PASS", "GitHub target is accessible", f"Resolved login: {resolved_login}")
    except Exception as exc:
        report.add("Target", "FAIL", "GitHub target is not accessible", f"{type(exc).__name__}: {sanitize_error_text(exc)}", "Check the username, token access and GitHub Enterprise endpoint then run doctor again", QUICK_START_GUIDE_URL)


# Evaluates one lazy PyGithub feed without retaining its potentially large contents
def doctor_probe_feed(operation, iterable_factory):
    debug_github_operation(operation)
    iterator = iter(iterable_factory())
    next(iterator, None)


# Adds monitoring feed, feature and read-only output path checks
def doctor_check_monitoring(report, contribution_checker=None):
    if report.target_name and report.target_profile is None:
        report.add("Monitoring", "FAIL", "Core monitoring feeds could not be checked", "A reachable target profile is required", "Fix the Target section then run doctor again")
    elif report.target_profile is not None:
        feed_checks = [("Repository feed is accessible", "doctor repository feed", lambda: report.target_profile.get_repos(type='owner')), ("Starred repository feed is accessible", "doctor starred repository feed", report.target_profile.get_starred)]
        if not DO_NOT_MONITOR_GITHUB_EVENTS:
            feed_checks.append(("Recent event feed is accessible", "doctor recent event feed", report.target_profile.get_events))
        for label, operation, factory in feed_checks:
            try:
                doctor_probe_feed(operation, factory)
                report.add("Monitoring", "PASS", label)
            except Exception as exc:
                report.add("Monitoring", "FAIL", label.replace(" is accessible", " is unavailable"), f"{type(exc).__name__}: {sanitize_error_text(exc)}", "Check target visibility, token access and GitHub API availability")
        if DO_NOT_MONITOR_GITHUB_EVENTS:
            report.add("Monitoring", "PASS", "GitHub event monitoring is disabled", "No event feed check was needed")
    if TRACK_REPOS_CHANGES:
        if REPOS_TO_MONITOR:
            report.add("Monitoring", "PASS", "Repository detail tracking is enabled", f"Selection: {', '.join(str(value) for value in REPOS_TO_MONITOR)}")
        else:
            report.add("Monitoring", "WARN", "Repository detail tracking has no selected repositories", "No repository detail alerts can fire", "Set REPOS_TO_MONITOR or pass --repos")
    else:
        report.add("Monitoring", "PASS", "Repository detail tracking is disabled")
    if TRACK_CONTRIB_CHANGES and report.target_profile is not None:
        checker = get_daily_contributions_count if contribution_checker is None else contribution_checker
        try:
            checker(report.target_name, today_local(), report.github_token)
            report.add("Monitoring", "PASS", "Daily contribution feed is accessible")
        except Exception as exc:
            report.add("Monitoring", "FAIL", "Daily contribution feed is unavailable", f"{type(exc).__name__}: {sanitize_error_text(exc)}", "Check token access, timezone and GitHub GraphQL availability")
    elif TRACK_CONTRIB_CHANGES:
        report.add("Monitoring", "FAIL", "Daily contribution feed could not be checked", "A reachable target profile is required", "Fix the Target section then run doctor again")
    else:
        report.add("Monitoring", "PASS", "Daily contribution tracking is disabled")


# Returns the nearest existing parent used for a read-only path permission check
def doctor_existing_parent(path):
    candidate = Path(path).expanduser()
    parent = candidate if candidate.is_dir() else candidate.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    return parent


# Adds one read-only output destination check without creating anything
def doctor_add_path_check(report, label, path):
    selected = Path(path).expanduser()
    if selected.exists():
        writable = selected.is_file() and os.access(selected, os.W_OK)
        detail = f"Path: {selected}"
    else:
        parent = doctor_existing_parent(selected)
        writable = parent.is_dir() and os.access(parent, os.W_OK)
        detail = f"Path: {selected} | Existing parent: {parent}"
    if writable:
        report.add("Configuration", "PASS", f"{label} appears writable", detail)
    else:
        report.add("Configuration", "FAIL", f"{label} is not writable: {selected}", detail, f"Choose a writable path for the {label.lower()} or correct its parent permissions")


# Adds read-only checks for each file monitoring would write
def doctor_check_output_paths(report):
    if CSV_FILE:
        doctor_add_path_check(report, "CSV destination", CSV_FILE)
    else:
        report.add("Configuration", "PASS", "CSV logging is disabled", "No CSV file will be written")
    if DISABLE_LOGGING:
        report.add("Configuration", "PASS", "Output logging is disabled", "No log file will be written")
    elif report.target_name:
        doctor_add_path_check(report, "Log destination", resolve_output_log_path(report.target_name))
    else:
        # The log file name carries the target, so it is only resolved once a target is known
        report.add("Configuration", "PASS", "Log destination will be finalized after a target is selected", f"Base path: {Path(os.path.expanduser(GITHUB_LOGFILE))}")


# Returns whether email settings indicate that any alert can fire
def doctor_email_alerts_enabled():
    selected = (PROFILE_NOTIFICATION, EVENT_NOTIFICATION, REPO_NOTIFICATION, REPO_UPDATE_DATE_NOTIFICATION, CONTRIB_NOTIFICATION)
    configured_destination = not str(SMTP_HOST).startswith("your_smtp_server_")
    return any(selected) or bool(ERROR_NOTIFICATION and configured_destination)


# Returns the user-facing spelling of one selected webhook provider
def webhook_provider_display_name(provider=None):
    normalized = normalized_webhook_provider(provider)
    selected = WEBHOOK_PROVIDER if provider is None else provider
    return "Discord" if normalized == "discord" else "ntfy" if normalized == "ntfy" else sanitize_error_text(selected)


# Confirms the SMTP sign-in without sending anything, so a rejected login is reported before monitoring starts
def doctor_add_smtp_login_check(report):
    smtp_object = None
    try:
        smtp_object = smtp_connect_and_login(SMTP_SSL, smtp_timeout=5)
    except Exception as exc:
        advice = classify_recovery_error(exc, "email")
        report.add("Notifications", "FAIL", advice.summary, advice.detail, advice.fix, advice.guide_url or NOTIFICATION_GUIDE_URL)
        return
    finally:
        smtp_quit_quietly(smtp_object)
    report.email_ready = True
    report.add("Notifications", "PASS", SMTP_READY_CHECK_LABEL, f"Alerts: {', '.join(_startup_email_notification_categories())}. No email was sent during this passive check")


# Adds channel readiness checks and stores structural delivery-test readiness
def doctor_check_notifications(report):
    if not doctor_email_alerts_enabled():
        report.add("Notifications", "PASS", "Email notifications are disabled", "No SMTP connection was attempted and no email was sent")
    else:
        email_error = validate_email_settings()
        if email_error is not None:
            report.add("Notifications", "WARN", "Email alerts are enabled but unusable", email_error, "Correct SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL and RECEIVER_EMAIL", NOTIFICATION_GUIDE_URL)
        else:
            doctor_add_smtp_login_check(report)
    if not WEBHOOK_ENABLED:
        report.add("Notifications", "PASS", "Webhook alerts are disabled", "No webhook was sent")
        return
    selected_webhook_types = any((WEBHOOK_PROFILE_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION))
    if not selected_webhook_types and not WEBHOOK_ERROR_NOTIFICATION:
        report.add("Notifications", "WARN", "Webhook alerts have no usable alert choices", "The channel is enabled but no selected alert can fire", "Enable at least one webhook alert type or disable WEBHOOK_ENABLED", NOTIFICATION_GUIDE_URL)
        return
    if not validate_webhook_url(WEBHOOK_URL):
        report.add("Notifications", "WARN", "Webhook alerts have no valid destination", "WEBHOOK_URL must be a complete supported HTTPS destination", "Set WEBHOOK_URL with --set-webhook-url or disable WEBHOOK_ENABLED", NOTIFICATION_GUIDE_URL)
        return
    provider = normalized_webhook_provider()
    customization_error = validate_webhook_customization(provider)
    header_error = validate_webhook_headers(provider)
    if not provider:
        report.add("Notifications", "WARN", "Webhook provider is invalid", sanitize_error_text(WEBHOOK_PROVIDER), "Set WEBHOOK_PROVIDER to discord or ntfy", NOTIFICATION_GUIDE_URL)
    elif customization_error is not None:
        report.add("Notifications", "WARN", "Webhook customization is invalid", customization_error, "Correct WEBHOOK_TEMPLATE, WEBHOOK_USERNAME, WEBHOOK_AVATAR_URL or WEBHOOK_TRANSFORMS", NOTIFICATION_GUIDE_URL)
    elif header_error is not None:
        report.add("Notifications", "WARN", "Webhook headers are invalid", header_error, "Correct WEBHOOK_HEADERS or NTFY_ACCESS_TOKEN", NOTIFICATION_GUIDE_URL)
    else:
        report.webhook_ready = True
        report.add("Notifications", "PASS", f"{WEBHOOK_READY_CHECK_LABEL} for {webhook_provider_display_name()}", f"Alerts: {', '.join(_startup_webhook_notification_categories())}. The private link was not displayed. No webhook was sent during this passive check")


# Sanitizes one doctor field and keeps it on a single output-contract line
def sanitize_doctor_text(value):
    return " ".join(sanitize_error_text(value).splitlines()).strip()


# Renders one doctor result while sanitizing every user-visible field
def render_doctor_check(check, stream=None):
    destination = sys.stdout if stream is None else stream
    marker = colorize(_DOCTOR_MARK_STYLES[check.status], f"[{check.status}]")
    destination.write(f"{marker} {sanitize_doctor_text(check.label)}\n")
    if check.detail:
        destination.write(f"  {sanitize_doctor_text(check.detail)}\n")
    if check.status != "PASS":
        destination.write(colorize("info", f"To fix: {sanitize_doctor_text(check.fix)}") + "\n")
        destination.write(f"Guide: {colorize('url', sanitize_doctor_text(check.guide))}\n")


# Renders fixed-order report sections with exactly one blank line between them
def render_doctor_sections(report, stream=None):
    destination = sys.stdout if stream is None else stream
    current_section = None
    for check in report.checks:
        if check.section == "Optional delivery tests":
            continue
        if check.section != current_section:
            destination.write(f"\n{colorize('section', check.section)}\n")
            current_section = check.section
        render_doctor_check(check, destination)


# Returns whether stdin supports separate interactive delivery approvals
def doctor_input_is_interactive(input_stream=None):
    source = sys.stdin if input_stream is None else input_stream
    try:
        return bool(source.isatty())
    except Exception as exc:
        debug_swallowed_exception("Doctor input terminal detection", exc)
        return False


# Returns whether doctor output is attached to a real terminal instead of a pipe
def doctor_output_is_interactive(stream=None):
    destination = sys.stdout if stream is None else stream
    terminal = getattr(destination, "terminal", destination)
    try:
        return bool(terminal.isatty())
    except Exception as exc:
        debug_swallowed_exception("Doctor output terminal detection", exc)
        return False


# Reads one default-no delivery approval without exposing any private setting
def ask_doctor_approval(prompt, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    destination.write(colorize("info", f"{prompt} [y/N]: "))
    destination.flush()
    try:
        answer = input_func()
    except (EOFError, KeyboardInterrupt):
        destination.write("\n")
        return False
    return str(answer).strip().casefold() in {"y", "yes"}


# Offers separately approved real delivery tests only on interactive stdin
def doctor_run_optional_delivery_tests(report, input_func=input, input_stream=None, stream=None, email_sender=None, webhook_sender=None):
    if not (report.email_ready or report.webhook_ready) or not doctor_input_is_interactive(input_stream) or not doctor_output_is_interactive(stream):
        return
    destination = sys.stdout if stream is None else stream
    destination.write("\n" + colorize("section", "Optional delivery tests") + "\n\n")
    destination.write("Doctor will not write files. Each approved test sends one real message.\n\n")
    send_email_func = send_email if email_sender is None else email_sender
    send_webhook_func = send_webhook if webhook_sender is None else webhook_sender
    if report.email_ready:
        approved = ask_doctor_approval("Send one test email now? This will deliver a real message", input_func, destination)
        if approved:
            result = send_email_func("github_monitor doctor test", "This real test message confirms that doctor can deliver email.", "", SMTP_SSL, smtp_timeout=5)
            if result == 0:
                check = DoctorCheck("Optional delivery tests", "PASS", "Test email was delivered", f"Destination: {RECEIVER_EMAIL}")
            else:
                check = DoctorCheck("Optional delivery tests", "FAIL", "Test email delivery failed", "The SMTP delivery function returned an error", "Review the SMTP error above and correct the email settings", NOTIFICATION_GUIDE_URL)
        else:
            check = DoctorCheck("Optional delivery tests", "SKIP", "Test email was not sent", "You declined the real delivery test", "Run doctor again and approve the email test when ready", NOTIFICATION_GUIDE_URL)
        report.checks.append(check)
        render_doctor_check(check, destination)
    if report.webhook_ready:
        provider = webhook_provider_display_name()
        approved = ask_doctor_approval(f"Send one test webhook through {provider} now? This will publish a real notification", input_func, destination)
        if approved:
            result = send_webhook_func("GitHub Monitor doctor test", "This real test notification confirms that doctor can deliver webhooks.", "event", force=True)
            if result == 0:
                check = DoctorCheck("Optional delivery tests", "PASS", f"Test webhook through {provider} was delivered", f"Destination host: {diagnostic_endpoint(WEBHOOK_URL, host_only=True)}")
            else:
                check = DoctorCheck("Optional delivery tests", "FAIL", f"Test webhook through {provider} failed", "The webhook delivery function returned an error", "Review the webhook error above and correct the destination settings", NOTIFICATION_GUIDE_URL)
        else:
            check = DoctorCheck("Optional delivery tests", "SKIP", f"Test webhook through {provider} was not sent", "You declined the real delivery test", "Run doctor again and approve the webhook test when ready", NOTIFICATION_GUIDE_URL)
        report.checks.append(check)
        render_doctor_check(check, destination)


# Renders the single actionable doctor verdict and guide URL
def render_doctor_summary(report, stream=None):
    destination = sys.stdout if stream is None else stream
    destination.write("\n" + colorize("header", "Summary") + "\n")
    if report.failure_count:
        destination.write(colorize("error", f"  {report.failure_count} check(s) failed, {report.warning_count} warning(s). Fix the failures above before relying on the tool.") + "\n")
    elif report.warning_count:
        destination.write(colorize("warning", f"  All critical checks passed with {report.warning_count} warning(s). Review the warnings above.") + "\n")
    else:
        destination.write(colorize("boolean_true", "  All checks passed. You are good to go!") + "\n")
    destination.write(f"\nGuide: {colorize('url', DOCTOR_GUIDE_URL)}\n")


# Runs the complete read-only preflight and returns its healthcheck exit code
def run_doctor_preflight(args, parser, request_get=None, github_factory=None, contribution_checker=None, module_finder=None, input_func=input, input_stream=None, stream=None, email_sender=None, webhook_sender=None, show_banner=True):
    destination = terminal_surface_stream(sys.stdout if stream is None else stream)
    if show_banner:
        _write_startup_banner(destination)
    destination.write("Running preflight checks. No files will be written. Interactive email and webhook tests run only after separate approval.\n\n")
    report = DoctorReport(target_name=str(args.username or ""))
    progress = DoctorProgress(destination)
    try:
        progress.show("environment")
        doctor_check_environment(report, module_finder)
        progress.show("configuration")
        progress.clear()
        doctor_check_configuration(report, args, parser)
        if not report.target_name:
            report.target_name = wizard_normalize_target(TARGET_GITHUB_USERNAME)
        doctor_check_output_paths(report)
        colour_stream = destination
        while isinstance(colour_stream, (Logger, TerminalStream)):
            colour_stream = colour_stream.terminal
        init_color_output(colour_stream)
        progress.show("authentication")
        doctor_check_authentication(report, request_get)
        progress.show("connectivity")
        doctor_check_connectivity(report, request_get)
        progress.show("target")
        doctor_check_target(report, github_factory)
        progress.show("monitoring feeds")
        doctor_check_monitoring(report, contribution_checker)
        progress.show("notifications")
        doctor_check_notifications(report)
    finally:
        progress.clear()
    destination.write(colorize("header", "Doctor") + "\n")
    # The install method is context rather than a check: it cannot fail, so it is stated once here
    # instead of taking a result row that no marker describes
    destination.write(f"Detected install method: {colorize('username', detect_install_context().install_method)}\n")
    render_doctor_sections(report, destination)
    doctor_run_optional_delivery_tests(report, input_func, input_stream, destination, email_sender, webhook_sender)
    render_doctor_summary(report, destination)
    destination.flush()
    return 1 if report.failure_count else 0


WIZARD_SECTION_KEYS = {
    "Target": ("TARGET_GITHUB_USERNAME", "DO_NOT_MONITOR_GITHUB_EVENTS", "TRACK_REPOS_CHANGES", "TRACK_CONTRIB_CHANGES"),
    "Polling": ("GITHUB_CHECK_INTERVAL",),
    "Authentication": ("GITHUB_API_URL", "GITHUB_HTML_URL"),
    "Email": ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_SSL", "SENDER_EMAIL", "RECEIVER_EMAIL", "PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION", "ERROR_NOTIFICATION"),
    "Webhook": ("WEBHOOK_ENABLED", "WEBHOOK_PROVIDER", "WEBHOOK_PROFILE_NOTIFICATION", "WEBHOOK_EVENT_NOTIFICATION", "WEBHOOK_REPO_NOTIFICATION", "WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION", "WEBHOOK_CONTRIB_NOTIFICATION", "WEBHOOK_ERROR_NOTIFICATION"),
    "Destinations": ("CSV_FILE", "DISABLE_LOGGING", "DOTENV_FILE"),
}
WIZARD_SECRET_KEYS = {"Authentication": ("GITHUB_TOKEN",), "Email": ("SMTP_PASSWORD",), "Webhook": ("WEBHOOK_URL", "NTFY_ACCESS_TOKEN")}
WIZARD_CONFIG_ORDER = tuple(name for names in WIZARD_SECTION_KEYS.values() for name in names)


# Writes one coloured wizard heading at the requested level
def _wizard_heading(destination, text, part="section"):
    destination.write("\n" + colorize(part, text) + "\n")


# Writes one labelled command with sibling-style indentation and spacing
def _wizard_print_command(destination, label, command, suffix=""):
    destination.write(f"{label}\n")
    destination.write(f"    {colorize('section', command)}{colorize('info', suffix) if suffix else ''}\n\n")


# Writes the detected installation method and selected setup files
def _wizard_print_setup_destinations(destination, context, state):
    destination.write(f"Detected install method: {colorize('username', context.install_method)}\n")
    destination.write(f"Configuration:          {state.config_path}\n")
    destination.write(f"Dotenv:                 {state.dotenv_path}\n")


# The theme part each setup summary row draws its value in, for rows whose value has a known kind
WIZARD_SUMMARY_VALUE_STYLES = {"Target": "username", "Polling interval": "duration", "GitHub API": "url"}


# Colours one setup summary value from its row label
def _wizard_summary_value(label, value):
    text = str(value)
    part = WIZARD_SUMMARY_VALUE_STYLES.get(label)
    if part:
        return colorize(part, text)
    if text.startswith("enabled") or text == "complete":
        return colorize("boolean_true", text)
    if text in ("disabled", "incomplete"):
        return colorize("boolean_false", text)
    return text


# Signals a clean interactive cancellation before any wizard files are written
class WizardCancelled(Exception):
    pass


@dataclass
class WizardSetupState:
    target: str
    config_path: Path
    dotenv_path: Path
    install_context: InstallContext
    values: dict[str, Any]
    secrets: dict[str, str]
    baseline_values: dict[str, Any]
    baseline_secrets: dict[str, str]
    preserved_values: dict[str, Any] = field(default_factory=dict)
    authenticated_login: str = ""
    environment_token_available: bool = False
    persist_target: bool = True

    # Reports whether doctor can exercise an authenticated real path
    @property
    def authentication_complete(self):
        return bool(self.secrets.get("GITHUB_TOKEN") or self.environment_token_available)


# Normalizes a GitHub username or profile URL to one canonical username
def wizard_normalize_target(value):
    selected = str(value).strip()
    if "://" in selected:
        try:
            parsed = urlsplit(selected)
        except ValueError:
            return ""
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname or len(parts) != 1:
            return ""
        selected = parts[0]
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", selected):
        return ""
    return selected


# Parses one human duration and returns a positive whole number of seconds
def wizard_parse_duration(value):
    selected = str(value).strip().casefold()
    if not selected:
        raise ValueError("Enter a duration such as 120, 2m, 1.5h, 1h 30m or 1d")
    if selected.isdigit():
        seconds = int(selected)
        if seconds <= 0:
            raise ValueError("The duration must be at least one second")
        if seconds > 31536000:
            raise ValueError("Use a positive duration no longer than one year")
        return seconds
    position = 0
    total = 0.0
    matches = list(re.finditer(r"\s*(\d+(?:\.\d+)?)\s*([smhd])", selected))
    for match in matches:
        if selected[position:match.start()].strip():
            raise ValueError("Use seconds, minutes, hours or days such as 30s, 2m, 1.5h, 1h 30m or 1d")
        amount = float(match.group(1))
        total += amount * {"s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2)]
        position = match.end()
    if not matches or selected[position:].strip() or total <= 0 or total > 31536000:
        raise ValueError("Use a positive duration no longer than one year")
    seconds = round(total)
    if seconds <= 0:
        raise ValueError("The duration must be at least one second")
    return seconds


# Renders raw seconds plus a compact readable duration for wizard defaults and summaries
def wizard_format_duration(seconds):
    remaining = int(seconds)
    parts = []
    for suffix, count in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        value, remaining = divmod(remaining, count)
        if value:
            parts.append(f"{value}{suffix}")
    raw = f"{seconds}s"
    readable = " ".join(parts) or raw
    return raw if readable == raw else f"{raw} - {readable}"


# Prompts until the user enters a positive duration or accepts the readable default
def wizard_ask_duration(label, default, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    while True:
        answer = wizard_read_answer(f"{label} [{wizard_format_duration(default)}]: ", input_func, destination)
        if not answer:
            return int(default)
        try:
            return wizard_parse_duration(answer)
        except ValueError:
            destination.write(colorize("warning", "  Enter a positive duration such as 120, 2m, 1.5h, 1h 30m or 1d.") + "\n")


# Reads one wizard answer after rendering its prompt to the selected stream
def wizard_read_answer(prompt, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    destination.write(colorize("info", prompt))
    destination.flush()
    try:
        return str(input_func()).strip()
    except (EOFError, KeyboardInterrupt) as exc:
        destination.write("\n")
        raise WizardCancelled from exc


# Reads one hidden wizard answer while forcing debug output off around the secret path
def wizard_read_secret(prompt, getpass_func=None, stream=None):
    global DEBUG_MODE
    destination = sys.stdout if stream is None else stream
    destination.write(colorize("info", prompt))
    destination.flush()
    hidden_prompt = getpass.getpass if getpass_func is None else getpass_func
    previous_debug_mode = DEBUG_MODE
    DEBUG_MODE = False
    try:
        return str(hidden_prompt("")).strip()
    except (EOFError, KeyboardInterrupt) as exc:
        destination.write("\n")
        raise WizardCancelled from exc
    finally:
        DEBUG_MODE = previous_debug_mode


# Reads a yes or no answer with an explicit default and retries invalid input
def wizard_ask_yes_no(prompt, default=False, input_func=input, stream=None):
    suffix = " [Y/n]: " if default else " [y/N]: "
    destination = sys.stdout if stream is None else stream
    while True:
        answer = wizard_read_answer(prompt + suffix, input_func, destination).casefold()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        destination.write(colorize("warning", "  Please answer 'y' or 'n'.") + "\n")


# Offers the one way out after an entry the wizard cannot use, so declining keeps every answer already given
def wizard_offer_retry(label, consequence="", input_func=input, stream=None):
    if consequence:
        return not wizard_ask_yes_no(f"Continue without the {label}? {consequence}", False, input_func, stream)
    return wizard_ask_yes_no(f"Try entering the {label} again?", True, input_func, stream)


# Reads one numbered choice and returns its stable value
def wizard_ask_choice(prompt, choices, default, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    destination.write("\n")
    destination.write(colorize("info", prompt) + "\n")
    for index, (_, label, description) in enumerate(choices, 1):
        marker = " (default)" if choices[index - 1][0] == default else ""
        destination.write(f"  {colorize('username', str(index))}. {label}{colorize('info', marker)}\n")
        destination.write(f"     {description}\n")
    while True:
        answer = wizard_read_answer(f"Choose [1-{len(choices)}]: ", input_func, destination)
        if not answer:
            return default
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1][0]
        destination.write(colorize("warning", f"  Enter a number between 1 and {len(choices)}.") + "\n")


# Reads one text value with a shown default and optional validation
def wizard_ask_text(label, default="", validator=None, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    shown_default = f" [{default}]" if default not in (None, "") else ""
    while True:
        answer = wizard_read_answer(f"{label}{shown_default}: ", input_func, destination)
        selected = str(default) if not answer else answer
        if validator is None:
            return selected
        error = validator(selected)
        if not error:
            return selected
        destination.write(colorize("warning", f"That value is not valid: {error}") + "\n")
        if not wizard_offer_retry(label, input_func=input_func, stream=destination):
            return str(default)


# Returns a concise validation error for one general HTTPS service endpoint
def wizard_https_url_error(value):
    try:
        parsed = urlsplit(str(value).strip())
    except ValueError:
        return "enter a complete HTTPS URL"
    if parsed.scheme.casefold() != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return "enter a complete HTTPS URL without credentials, a query or a fragment"
    return ""


# Returns a concise validation error for one wizard email configuration
def wizard_email_settings_error(values, secrets):
    host = str(values.get("SMTP_HOST", ""))
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r"(?=.{4,253}\Z)((?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}\.?", host):
            return "SMTP host must be a valid IP address or fully qualified domain name"
    try:
        port = int(values.get("SMTP_PORT", 0))
    except (TypeError, ValueError):
        return "SMTP port must be a number from 1 through 65535"
    if not 1 <= port <= 65535:
        return "SMTP port must be a number from 1 through 65535"
    email_pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"
    if not re.fullmatch(email_pattern, str(values.get("SENDER_EMAIL", ""))) or not re.fullmatch(email_pattern, str(values.get("RECEIVER_EMAIL", ""))):
        return "sender and receiver must be valid email addresses"
    if not str(values.get("SMTP_USER", "")).strip() or not secrets.get("SMTP_PASSWORD"):
        return "SMTP username and password are required"
    return ""


# Loads safe baseline values from existing config and dotenv files without applying them globally
def build_wizard_state(config_path, dotenv_path, install_context=None):
    selected_config = Path(config_path).expanduser().resolve()
    selected_dotenv = Path(dotenv_path).expanduser().resolve()
    if selected_config == selected_dotenv:
        raise ValueError("Configuration and dotenv must use different files")
    defaults = parse_config_content(CONFIG_BLOCK, "<built-in-config>")
    existing_values = {}
    if selected_config.exists():
        debug_print("Reading setup baseline configuration", path=selected_config)
        existing_values = parse_config_content(selected_config.read_text(encoding="utf-8"), str(selected_config), reference_values=defaults)
    values = dict(defaults)
    values.update(existing_values)
    secrets = {}
    if selected_dotenv.exists():
        debug_print("Reading setup baseline dotenv", path=selected_dotenv)
        try:
            from dotenv import dotenv_values
            secrets.update({str(name): str(value) for name, value in dotenv_values(selected_dotenv).items() if name in SECRET_KEYS and value is not None})
        except Exception as exc:
            raise ValueError(f"Dotenv file '{selected_dotenv}' could not be read: {type(exc).__name__}: {exc}") from None
    for name in SECRET_KEYS:
        configured = existing_values.pop(name, None)
        if name not in secrets and isinstance(configured, str) and configured and not configured.startswith("your_"):
            secrets[name] = configured
    values["DOTENV_FILE"] = str(selected_dotenv)
    baseline_values = dict(values)
    baseline_secrets = dict(secrets)
    preserved = {name: value for name, value in existing_values.items() if name not in SECRET_KEYS}
    context = detect_install_context() if install_context is None else install_context
    target = wizard_normalize_target(values.get("TARGET_GITHUB_USERNAME", ""))
    return WizardSetupState(target, selected_config, selected_dotenv, context, values, secrets, baseline_values, baseline_secrets, preserved, environment_token_available=bool(os.environ.get("GITHUB_TOKEN")), persist_target=bool(target) if target else True)


# Restores one wizard section to its pre-wizard values before recollecting it
def wizard_reset_section(state, section):
    for name in WIZARD_SECTION_KEYS[section]:
        state.values[name] = state.baseline_values[name]
    for name in WIZARD_SECRET_KEYS.get(section, ()):
        if name in state.baseline_secrets:
            state.secrets[name] = state.baseline_secrets[name]
        else:
            state.secrets.pop(name, None)
    if section == "Target":
        state.target = wizard_normalize_target(state.values.get("TARGET_GITHUB_USERNAME", ""))
        state.persist_target = bool(state.target) if state.target else True
    if section == "Authentication":
        state.authenticated_login = ""


# Collects the target and core monitoring feature choices
def wizard_collect_target(state, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    while True:
        entered = wizard_ask_text("GitHub username or profile URL", state.target, input_func=input_func, stream=destination)
        normalized = wizard_normalize_target(entered)
        if normalized:
            state.target = normalized
            if normalized != entered:
                destination.write(f"Using normalized GitHub username: {normalized}\n")
            break
        destination.write(colorize("warning", "That target is not valid. Enter a GitHub username or full profile URL.") + "\n")
    state.persist_target = wizard_ask_yes_no("Persist this target in the generated config?", state.persist_target, input_func, destination)
    state.values["TARGET_GITHUB_USERNAME"] = state.target if state.persist_target else ""
    state.values["DO_NOT_MONITOR_GITHUB_EVENTS"] = not wizard_ask_yes_no("Monitor public GitHub events?", not bool(state.values["DO_NOT_MONITOR_GITHUB_EVENTS"]), input_func, destination)
    state.values["TRACK_REPOS_CHANGES"] = wizard_ask_yes_no("Track detailed repository changes?", bool(state.values["TRACK_REPOS_CHANGES"]), input_func, destination)
    state.values["TRACK_CONTRIB_CHANGES"] = wizard_ask_yes_no("Track daily contribution changes?", bool(state.values["TRACK_CONTRIB_CHANGES"]), input_func, destination)


# Collects a human polling interval while retaining the existing automatic timezone setting
def wizard_collect_polling(state, input_func=input, stream=None):
    seconds = int(state.values["GITHUB_CHECK_INTERVAL"])
    state.values["GITHUB_CHECK_INTERVAL"] = wizard_ask_duration("GitHub polling interval (seconds or use s/m/h/d)", seconds, input_func, stream)


# Collects GitHub endpoints and optionally validates a hidden token
def wizard_collect_authentication(state, input_func=input, getpass_func=None, stream=None, token_validator=None):
    destination = sys.stdout if stream is None else stream
    state.values["GITHUB_API_URL"] = wizard_ask_text("GitHub API URL", str(state.values["GITHUB_API_URL"]), lambda value: "" if validate_github_endpoint_url(value) else "enter a complete HTTPS GitHub API URL", input_func, destination)
    state.values["GITHUB_HTML_URL"] = wizard_ask_text("GitHub web URL", str(state.values["GITHUB_HTML_URL"]), wizard_https_url_error, input_func, destination)
    destination.write(f"Create or view your GitHub personal access token: {colorize('url', GITHUB_TOKEN_SETTINGS_URL)}\n")
    existing = bool(state.secrets.get("GITHUB_TOKEN") or state.environment_token_available)
    if existing and not wizard_ask_yes_no("Replace the GitHub token already configured?", False, input_func, destination):
        return
    validator = validate_github_token if token_validator is None else token_validator
    while True:
        token = wizard_read_secret("GitHub token: ", getpass_func, destination)
        if not token:
            # Monitoring cannot run without it, so leaving it unset has to be a decision rather than a fallthrough
            if not wizard_offer_retry("GitHub token", "Nothing can be monitored until one is set", input_func, destination):
                if "GITHUB_TOKEN" in state.baseline_secrets:
                    state.secrets["GITHUB_TOKEN"] = state.baseline_secrets["GITHUB_TOKEN"]
                else:
                    state.secrets.pop("GITHUB_TOKEN", None)
                return
            continue
        destination.write(colorize("info", "Validating the GitHub token before saving ...") + "\n")
        try:
            login = validator(token, state.values["GITHUB_API_URL"])
        except Exception as exc:
            destination.write(colorize("error", f"Token validation failed: {sanitize_error_text(exc)}") + "\n")
            # A token GitHub keeps rejecting cannot be corrected from inside the loop, so the wizard must be leavable here too
            if not wizard_offer_retry("GitHub token", input_func=input_func, stream=destination):
                return
            continue
        state.secrets["GITHUB_TOKEN"] = token
        state.authenticated_login = str(login)
        destination.write(f"GitHub token is valid for user: {colorize('username', state.authenticated_login)}\n")
        return


# Collects optional email delivery settings and alert choices
def wizard_collect_email(state, input_func=input, getpass_func=None, stream=None):
    destination = sys.stdout if stream is None else stream
    configured_destination = not str(state.values["SMTP_HOST"]).startswith("your_smtp_server_")
    enabled_default = any(bool(state.values[name]) for name in ("PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION")) or bool(state.values["ERROR_NOTIFICATION"] and configured_destination)
    if not wizard_ask_yes_no("Configure email notifications?", enabled_default, input_func, destination):
        for name in ("PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION", "ERROR_NOTIFICATION"):
            state.values[name] = False
        return
    state.values["SMTP_HOST"] = wizard_ask_text("SMTP host", "" if str(state.values["SMTP_HOST"]).startswith("your_") else state.values["SMTP_HOST"], input_func=input_func, stream=destination)
    state.values["SMTP_PORT"] = int(wizard_ask_text("SMTP port", state.values["SMTP_PORT"], lambda value: "" if str(value).isdigit() and 1 <= int(value) <= 65535 else "enter a number from 1 through 65535", input_func, destination))
    state.values["SMTP_USER"] = wizard_ask_text("SMTP username", "" if str(state.values["SMTP_USER"]).startswith("your_") else state.values["SMTP_USER"], input_func=input_func, stream=destination)
    if wizard_ask_yes_no("Set or replace the SMTP password now?", not bool(state.secrets.get("SMTP_PASSWORD")), input_func, destination):
        password = wizard_read_secret("SMTP password: ", getpass_func, destination)
        if password:
            state.secrets["SMTP_PASSWORD"] = password
    state.values["SMTP_SSL"] = wizard_ask_yes_no("Use STARTTLS for SMTP?", bool(state.values["SMTP_SSL"]), input_func, destination)
    state.values["SENDER_EMAIL"] = wizard_ask_text("Sender email", "" if str(state.values["SENDER_EMAIL"]).startswith("your_") else state.values["SENDER_EMAIL"], input_func=input_func, stream=destination)
    state.values["RECEIVER_EMAIL"] = wizard_ask_text("Receiver email", "" if str(state.values["RECEIVER_EMAIL"]).startswith("your_") else state.values["RECEIVER_EMAIL"], input_func=input_func, stream=destination)
    validation_error = wizard_email_settings_error(state.values, state.secrets)
    if validation_error:
        destination.write(colorize("warning", f"Email settings are incomplete: {validation_error}") + "\n")
        destination.write(colorize("warning", "Email alerts will stay disabled. Review this section to correct them.") + "\n")
        for name in ("PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION", "ERROR_NOTIFICATION"):
            state.values[name] = False
        return
    state.values["PROFILE_NOTIFICATION"] = wizard_ask_yes_no("Email profile changes?", bool(state.values["PROFILE_NOTIFICATION"]), input_func, destination)
    state.values["EVENT_NOTIFICATION"] = False if state.values["DO_NOT_MONITOR_GITHUB_EVENTS"] else wizard_ask_yes_no("Email new GitHub events?", bool(state.values["EVENT_NOTIFICATION"]), input_func, destination)
    state.values["REPO_NOTIFICATION"] = False if not state.values["TRACK_REPOS_CHANGES"] else wizard_ask_yes_no("Email detailed repository changes?", bool(state.values["REPO_NOTIFICATION"]), input_func, destination)
    state.values["REPO_UPDATE_DATE_NOTIFICATION"] = False if not state.values["TRACK_REPOS_CHANGES"] else wizard_ask_yes_no("Email repository update date changes?", bool(state.values["REPO_UPDATE_DATE_NOTIFICATION"]), input_func, destination)
    state.values["CONTRIB_NOTIFICATION"] = False if not state.values["TRACK_CONTRIB_CHANGES"] else wizard_ask_yes_no("Email daily contribution changes?", bool(state.values["CONTRIB_NOTIFICATION"]), input_func, destination)
    state.values["ERROR_NOTIFICATION"] = wizard_ask_yes_no("Email monitoring errors?", True, input_func, destination)


# Switches the channel and every alert it owns off together, so a half-configured webhook cannot be written
def wizard_disable_webhook(state):
    state.values["WEBHOOK_ENABLED"] = False
    for name in WIZARD_SECTION_KEYS["Webhook"]:
        if name.endswith("_NOTIFICATION"):
            state.values[name] = False


# Collects optional Discord or ntfy delivery settings and alert choices
def wizard_collect_webhook(state, input_func=input, getpass_func=None, stream=None):
    destination = sys.stdout if stream is None else stream
    if not wizard_ask_yes_no("Set up webhook alerts (Discord, ntfy etc.)?", bool(state.values["WEBHOOK_ENABLED"]), input_func, destination):
        wizard_disable_webhook(state)
        return
    provider = wizard_ask_choice("Webhook provider", (("discord", "Discord", "Send alerts to a Discord webhook URL."), ("ntfy", "ntfy", "Send alerts to an ntfy topic URL.")), normalized_webhook_provider(state.values["WEBHOOK_PROVIDER"]) or "discord", input_func, destination)
    state.values["WEBHOOK_PROVIDER"] = provider
    if wizard_ask_yes_no("Set or replace the webhook destination now?", not bool(state.secrets.get("WEBHOOK_URL")), input_func, destination):
        while True:
            entered = wizard_read_secret(f"Paste the {webhook_provider_display_name(provider)} webhook URL: ", getpass_func, destination)
            normalized = normalize_ntfy_topic_url(entered) if provider == "ntfy" else entered
            detected = detect_webhook_provider(normalized)
            valid = bool(normalized and validate_webhook_url(normalized) and (provider == "ntfy" or detected == "discord"))
            if valid:
                state.secrets["WEBHOOK_URL"] = normalized
                break
            # Nothing can be delivered without a destination, so giving up has to stay reachable from the prompt
            if not str(entered).strip():
                if not wizard_offer_retry("webhook URL", "Webhook alerts stay off until one is set", input_func, destination):
                    break
                continue
            destination.write(colorize("warning", f"That is not a valid {'Discord webhook URL' if provider == 'discord' else 'ntfy topic or HTTPS topic URL'}.") + "\n")
            if not wizard_offer_retry("webhook URL", input_func=input_func, stream=destination):
                break
    if provider == "ntfy" and wizard_ask_yes_no("Set or replace an optional ntfy access token?", False, input_func, destination):
        access_token = wizard_read_secret("ntfy access token: ", getpass_func, destination)
        if "\r" in access_token or "\n" in access_token or access_token.casefold().startswith(("bearer ", "basic ")):
            destination.write(colorize("warning", "The ntfy token was ignored because it contains an authorization scheme or line break.") + "\n")
        elif access_token:
            state.secrets["NTFY_ACCESS_TOKEN"] = access_token
    if not state.secrets.get("WEBHOOK_URL"):
        wizard_disable_webhook(state)
        destination.write(colorize("warning", "Webhook alerts will stay disabled until a destination is saved.") + "\n")
        return
    state.values["WEBHOOK_ENABLED"] = True
    state.values["WEBHOOK_PROFILE_NOTIFICATION"] = wizard_ask_yes_no("Webhook profile changes?", bool(state.values["WEBHOOK_PROFILE_NOTIFICATION"]), input_func, destination)
    state.values["WEBHOOK_EVENT_NOTIFICATION"] = False if state.values["DO_NOT_MONITOR_GITHUB_EVENTS"] else wizard_ask_yes_no("Webhook new GitHub events?", bool(state.values["WEBHOOK_EVENT_NOTIFICATION"]), input_func, destination)
    state.values["WEBHOOK_REPO_NOTIFICATION"] = False if not state.values["TRACK_REPOS_CHANGES"] else wizard_ask_yes_no("Webhook detailed repository changes?", bool(state.values["WEBHOOK_REPO_NOTIFICATION"]), input_func, destination)
    state.values["WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION"] = False if not state.values["TRACK_REPOS_CHANGES"] else wizard_ask_yes_no("Webhook repository update date changes?", bool(state.values["WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION"]), input_func, destination)
    state.values["WEBHOOK_CONTRIB_NOTIFICATION"] = False if not state.values["TRACK_CONTRIB_CHANGES"] else wizard_ask_yes_no("Webhook daily contribution changes?", bool(state.values["WEBHOOK_CONTRIB_NOTIFICATION"]), input_func, destination)
    state.values["WEBHOOK_ERROR_NOTIFICATION"] = wizard_ask_yes_no("Webhook monitoring errors?", True, input_func, destination)


# Collects log and CSV output destinations
def wizard_collect_destinations(state, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    state.values["DISABLE_LOGGING"] = not wizard_ask_yes_no("Write the normal per-target log file?", not bool(state.values["DISABLE_LOGGING"]), input_func, destination)
    csv_default = str(state.values["CSV_FILE"] or "")
    state.values["CSV_FILE"] = wizard_ask_text("Optional CSV output path (blank disables it)", csv_default, input_func=input_func, stream=destination)
    state.values["DOTENV_FILE"] = str(state.dotenv_path)


# Collects every wizard section in the shared output order
def wizard_collect_all(state, input_func=input, getpass_func=None, stream=None, token_validator=None):
    destination = sys.stdout if stream is None else stream
    wizard_collect_target(state, input_func, stream)
    destination.write("\n")
    wizard_collect_polling(state, input_func, stream)
    destination.write("\n")
    wizard_collect_authentication(state, input_func, getpass_func, stream, token_validator)
    destination.write("\n")
    wizard_collect_email(state, input_func, getpass_func, stream)
    destination.write("\n")
    wizard_collect_webhook(state, input_func, getpass_func, stream)
    destination.write("\n")
    wizard_collect_destinations(state, input_func, stream)


# Returns the alert categories one answer set enables, using the same labels the startup summary prints
def _wizard_notification_categories(values, prefix=""):
    labels = (("PROFILE_NOTIFICATION", "profile"), ("EVENT_NOTIFICATION", "events"), ("REPO_NOTIFICATION", "repositories"), ("REPO_UPDATE_DATE_NOTIFICATION", "repository updates"), ("CONTRIB_NOTIFICATION", "contributions"), ("ERROR_NOTIFICATION", "errors"))
    return [label for name, label in labels if values.get(prefix + name)]


# Renders one complete masked setup summary before any file is changed
def wizard_render_summary(state, stream=None):
    destination = sys.stdout if stream is None else stream
    email_categories = _wizard_notification_categories(state.values)
    webhook_categories = _wizard_notification_categories(state.values, "WEBHOOK_") if state.values["WEBHOOK_ENABLED"] else []
    webhook_state = f"enabled ({webhook_provider_display_name(state.values['WEBHOOK_PROVIDER'])})" if state.values["WEBHOOK_ENABLED"] else "disabled"
    _wizard_heading(destination, "Setup summary", "header")
    rows = [
        ("Target", state.target),
        ("Persist target", "yes" if state.persist_target else "no"),
        ("Polling interval", wizard_format_duration(state.values["GITHUB_CHECK_INTERVAL"])),
        ("GitHub API", state.values["GITHUB_API_URL"]),
        ("Authentication status", "complete" if state.authentication_complete else "incomplete"),
        ("Email", "enabled" if email_categories else "disabled"),
        ("Email notifications", ", ".join(email_categories) if email_categories else "none"),
        ("Webhook", webhook_state),
        ("Webhook alerts", ", ".join(webhook_categories) if webhook_categories else "none"),
        ("Output log", "enabled" if not state.values["DISABLE_LOGGING"] else "disabled"),
        ("CSV output", state.values["CSV_FILE"] or "disabled"),
        ("Config destination", state.config_path),
        ("Dotenv destination", state.dotenv_path),
        ("Install method", install_method_display_name(state.install_context.install_method)),
    ]
    if state.authenticated_login:
        rows.insert(5, ("Authenticated user", state.authenticated_login))
    width = max(len(label) for label, _ in rows) + 1
    for label, value in rows:
        destination.write(f"  {(label + ':'):<{width}} {_wizard_summary_value(label, value)}\n")


# Recollects one selected section while preserving every other answer
def wizard_edit_section(state, input_func=input, getpass_func=None, stream=None, token_validator=None):
    destination = sys.stdout if stream is None else stream
    sections = (
        ("Target", "Target and persistence", "Change the GitHub profile, whether it is saved and monitoring feature choices."),
        ("Polling", "Polling interval", "Change how often GitHub is checked."),
        ("Authentication", "Authentication", "Change GitHub endpoints or the access token."),
        ("Email", "Email notifications", "Change email delivery and alert choices."),
        ("Webhook", "Webhook alerts", "Change Discord or ntfy delivery and alert choices."),
        ("Destinations", "Output files", "Change log and CSV output settings."),
        ("return", "Return to summary", "Keep every current answer and show the summary again."),
    )
    selected = wizard_ask_choice("Which setup section should be changed?", sections, "Target", input_func, destination)
    if selected == "return":
        return
    wizard_reset_section(state, selected)
    collectors = {
        "Target": lambda: wizard_collect_target(state, input_func, destination),
        "Polling": lambda: wizard_collect_polling(state, input_func, destination),
        "Authentication": lambda: wizard_collect_authentication(state, input_func, getpass_func, destination, token_validator),
        "Email": lambda: wizard_collect_email(state, input_func, getpass_func, destination),
        "Webhook": lambda: wizard_collect_webhook(state, input_func, getpass_func, destination),
        "Destinations": lambda: wizard_collect_destinations(state, input_func, destination),
    }
    collectors[selected]()


# Reviews the complete setup until the user saves or confirms discard
def wizard_review_setup(state, input_func=input, getpass_func=None, stream=None, token_validator=None):
    destination = sys.stdout if stream is None else stream
    while True:
        wizard_render_summary(state, destination)
        actions = (
            ("save", "Save settings", "Write the displayed settings to the selected files."),
            ("edit", "Review or change settings", "Edit one section without losing the other answers."),
            ("discard", "Discard answers and exit", "Leave the destination files unchanged."),
        )
        action = wizard_ask_choice("What would you like to do?", actions, "save", input_func, destination)
        if action == "save":
            return True
        if action == "edit":
            wizard_edit_section(state, input_func, getpass_func, destination, token_validator)
            continue
        if wizard_ask_yes_no("Discard all entered answers and exit?", False, input_func, destination):
            return False
        destination.write(colorize("info", "  Setup answers retained.") + "\n")


# Renders the complete data-only configuration selected by the wizard
def render_wizard_config(state):
    selected = dict(state.preserved_values)
    for name in WIZARD_CONFIG_ORDER:
        selected[name] = state.values[name]
    selected["DOTENV_FILE"] = str(state.dotenv_path)
    ordered_names = [name for name in WIZARD_CONFIG_ORDER if name in selected]
    ordered_names.extend(sorted(name for name in selected if name not in ordered_names and name not in SECRET_KEYS))
    lines = ["# Generated by github_monitor --setup", "# Secrets are stored in the separate dotenv file.", ""]
    lines.extend(f"{name} = {selected[name]!r}" for name in ordered_names)
    content = "\n".join(lines) + "\n"
    validate_config_content(content, str(state.config_path))
    return content


# Updates selected dotenv assignments in memory while preserving unrelated lines
def render_wizard_dotenv(state):
    try:
        existing = state.dotenv_path.read_text(encoding="utf-8") if state.dotenv_path.exists() else ""
    except Exception as exc:
        raise ValueError(f"Dotenv file '{state.dotenv_path}' could not be read: {type(exc).__name__}: {exc}") from None
    lines = existing.splitlines()
    for key, value in state.secrets.items():
        if key not in SECRET_KEYS or not value:
            continue
        if "\r" in value or "\n" in value or "\x00" in value:
            raise ValueError(f"{key} contains an unsupported line break or null byte")
        replaced = False
        updated = []
        for line in lines:
            match = match_dotenv_assignment(line, key)
            if match:
                if not replaced:
                    updated.append(render_dotenv_assignment(key, value, match.group(1)))
                    replaced = True
            else:
                updated.append(line)
        if not replaced:
            updated.append(render_dotenv_assignment(key, value))
        lines = updated
    return "\n".join(lines) + ("\n" if lines else "")


# Creates a unique fsynced mode-0600 backup before replacing one existing file
def backup_wizard_file(path, timestamp=None):
    if not path.exists():
        return None
    stamp = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    original = path.read_bytes()
    for suffix in range(100):
        discriminator = "" if suffix == 0 else f".{suffix}"
        backup_path = path.with_name(f"{path.name}.{stamp}{discriminator}.bak")
        try:
            descriptor = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        with os.fdopen(descriptor, "wb") as backup_file:
            backup_file.write(original)
            backup_file.flush()
            os.fsync(backup_file.fileno())
        return backup_path
    raise FileExistsError(f"Could not create a unique backup for '{path}'")


# Prepares one fsynced mode-0600 temporary file beside its final destination
def prepare_wizard_atomic_file(path, content):
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        os.chmod(temporary_path, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output_file:
            output_file.write(content)
            output_file.flush()
            os.fsync(output_file.fileno())
    except Exception as exc:
        try:
            os.close(descriptor)
        except OSError as close_error:
            debug_swallowed_exception("Setup temporary descriptor cleanup", close_error)
        temporary_path.unlink(missing_ok=True)
        debug_print("Setup temporary file write", path=path, outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    return temporary_path


# Confirms replacing one existing generated configuration, or requires --force outside a terminal
def confirm_generated_config_replacement(destination, force=False, interactive=None, input_func=input):
    if not destination.exists() or force:
        return True
    try:
        terminal_is_interactive = bool(sys.stdin.isatty()) if interactive is None else bool(interactive)
    except Exception as exc:
        debug_swallowed_exception("Generated configuration terminal detection", exc)
        terminal_is_interactive = False
    if not terminal_is_interactive:
        raise FileExistsError(f"Config file '{destination}' already exists. Re-run with --force to replace it after a timestamped backup.")
    try:
        answer = str(input_func(f"Config file '{destination}' exists. Replace it and create a timestamped backup? [y/N]: ")).strip().casefold()
    except (EOFError, KeyboardInterrupt):
        print()
        answer = ""
    return answer in {"y", "yes"}


# Writes one generated configuration atomically after backing up any existing destination
def write_generated_config(output_file, content, force=False, interactive=None, input_func=input):
    destination = Path(os.path.expanduser(str(output_file)))
    if not confirm_generated_config_replacement(destination, force, interactive, input_func):
        return None, False
    backup_path = backup_wizard_file(destination) if destination.exists() else None
    if backup_path is not None:
        debug_print("Generated configuration backup written", path=backup_path)
    temporary_path = prepare_wizard_atomic_file(destination, content)
    try:
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    return backup_path, True


# Saves both wizard files only after validation, backup and temporary writes succeed
def save_wizard_files(state):
    for path in (state.config_path, state.dotenv_path):
        if not path.parent.is_dir():
            raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    config_content = render_wizard_config(state)
    dotenv_content = render_wizard_dotenv(state)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backups = (backup_wizard_file(state.config_path, timestamp), backup_wizard_file(state.dotenv_path, timestamp))
    prepared = []
    try:
        # Appended one at a time so a failure on the second file still exposes the first for cleanup
        for path, content in ((state.config_path, config_content), (state.dotenv_path, dotenv_content)):
            prepared.append(prepare_wizard_atomic_file(path, content))
        os.replace(prepared[0], state.config_path)
        os.replace(prepared[1], state.dotenv_path)
        os.chmod(state.config_path, 0o600)
        os.chmod(state.dotenv_path, 0o600)
    finally:
        for temporary_path in prepared:
            temporary_path.unlink(missing_ok=True)
    debug_print("Setup configuration write succeeded", path=state.config_path)
    debug_print("Setup dotenv write succeeded", path=state.dotenv_path)
    return backups


# Builds the exact install-aware argument list used after setup
def wizard_monitor_arguments(state):
    arguments = [] if state.persist_target else [state.target]
    return [*arguments, "--config-file", str(state.config_path), "--env-file", str(state.dotenv_path)]


# Runs the complete buffered setup interaction and optional doctor handoff
def run_setup_wizard(parser, config_path=None, env_file=None, input_func=input, getpass_func=None, input_stream=None, stream=None, interactive=None, install_context=None, token_validator=None, doctor_runner=None, monitor_launcher=None, show_banner=True):
    destination = terminal_surface_stream(sys.stdout if stream is None else stream)
    source = sys.stdin if input_stream is None else input_stream
    try:
        terminal_is_interactive = bool(source.isatty()) if interactive is None else bool(interactive)
    except Exception as exc:
        debug_swallowed_exception("Setup input terminal detection", exc)
        terminal_is_interactive = False
    context = detect_install_context() if install_context is None else install_context
    selected_config = Path(config_path or (Path.cwd() / DEFAULT_CONFIG_FILENAME)).expanduser().resolve()
    selected_dotenv = Path(env_file or (Path.cwd() / ".env")).expanduser().resolve()
    if show_banner:
        _write_startup_banner(destination)
    if not terminal_is_interactive:
        generate_command = render_install_command(["--generate-config", str(selected_config)], context)
        destination.write(colorize("header", "Setup Wizard\n") + "\n")
        destination.write(colorize("warning", "The setup wizard needs an interactive terminal (TTY).") + "\n")
        destination.write("Run --setup from an interactive shell or use --generate-config and edit the files manually.\n")
        _wizard_print_command(destination, "Generate a config manually with:", generate_command)
        destination.write(f"Guide: {colorize('url', QUICK_START_GUIDE_URL)}\n")
        return 1
    try:
        state = build_wizard_state(selected_config, selected_dotenv, context)
        destination.write(colorize("header", "Setup Wizard\n") + "\n")
        destination.write("This asks a few questions and writes a ready-to-run configuration.\n")
        destination.write("Press Enter to accept the shown default. Ctrl+C cancels.\n\n")
        destination.write("Secrets go to the dotenv file. Non-secret settings go to the config file.\n\n")
        _wizard_print_setup_destinations(destination, context, state)
        destination.write("\n")
        wizard_collect_all(state, input_func, getpass_func, destination, token_validator)
        if not wizard_review_setup(state, input_func, getpass_func, destination, token_validator):
            destination.write("\n" + colorize("warning", "Setup cancelled. Destination files were not changed.") + "\n")
            return 1
        backups = save_wizard_files(state)
    except WizardCancelled:
        destination.write(colorize("warning", "Setup cancelled. Destination files were not changed.") + "\n")
        return 1
    except Exception as exc:
        advice = classify_recovery_error(exc, "config")
        destination.write("\n")
        destination.write(apply_color_to_text(render_recovery_advice(advice)) + "\n")
        return 1
    config_backup, dotenv_backup = backups
    saved_rows = [("Configuration:", state.config_path)]
    if config_backup is not None:
        saved_rows.append(("Backup:", config_backup))
    saved_rows.append(("Secrets:" if state.secrets else "Dotenv:", state.dotenv_path))
    if dotenv_backup is not None:
        saved_rows.append(("Dotenv backup:", dotenv_backup))
    saved_width = max(len(label) for label, _ in saved_rows) + 1
    _wizard_heading(destination, "Saved files", "header")
    for label, path in saved_rows:
        destination.write(f"  {label:<{saved_width}}{path}\n")
    monitor_arguments = wizard_monitor_arguments(state)
    doctor_arguments = ["--doctor", *monitor_arguments]
    doctor_exit = None
    try:
        if state.authentication_complete:
            destination.write("\n")
            if wizard_ask_yes_no("Run doctor now? It writes no files and offers real delivery tests only with separate approval.", True, input_func, destination):
                destination.write("\n")
                doctor_args = parser.parse_args(doctor_arguments)
                runner = run_doctor_preflight if doctor_runner is None else doctor_runner
                doctor_exit = runner(doctor_args, parser, input_func=input_func, input_stream=source, stream=destination, show_banner=False)
    except WizardCancelled:
        destination.write(colorize("warning", "Setup is saved. Use the commands below when ready.") + "\n")
    _wizard_heading(destination, "Next steps", "header")
    _wizard_print_command(destination, "Check setup again:", render_install_command(doctor_arguments, context))
    start_label = "After Doctor passes, start monitoring:" if doctor_exit not in (None, 0) else "Start monitoring:"
    _wizard_print_command(destination, start_label, render_install_command(monitor_arguments, context))
    destination.write(f"Guide: {colorize('url', QUICK_START_GUIDE_URL)}\n")
    if doctor_exit == 0:
        try:
            start_now = wizard_ask_yes_no("Start monitoring now? Monitoring will continue until Ctrl+C.", True, input_func, destination)
        except WizardCancelled:
            start_now = False
            destination.write(colorize("warning", "Setup is saved. Start monitoring with the command above when ready.") + "\n")
        if start_now and monitor_launcher is not None:
            return int(monitor_launcher(monitor_arguments) or 0)
    return 0


# Prints the sibling-style first-run actions and optionally launches guided setup
def run_zero_argument_welcome(parser, input_func=input, input_stream=None, stream=None, install_context=None, setup_runner=None, show_banner=True):
    destination = terminal_surface_stream(sys.stdout if stream is None else stream)
    source = sys.stdin if input_stream is None else input_stream
    context = detect_install_context() if install_context is None else install_context
    if show_banner:
        _write_startup_banner(destination)
    try:
        interactive = bool(source.isatty())
    except Exception as exc:
        debug_swallowed_exception("Welcome input terminal detection", exc)
        interactive = False
    prefix = render_install_command([], context, exact=False)
    destination.write("For <github_target>, use a GitHub username or complete profile URL.\n\n")
    _wizard_print_command(destination, "Quickest start (already configured):", f"{prefix} <github_target>")
    setup_suffix = "   (or just answer Y below)" if interactive else ""
    _wizard_print_command(destination, "Easiest start (guided setup wizard):", f"{prefix} --setup", setup_suffix)
    _wizard_print_command(destination, "Check setup before monitoring:", f"{prefix} --doctor <github_target>")
    destination.write(f"Full options: {colorize('section', prefix + ' --help')}\n")
    destination.write(f"\nGuide:        {colorize('url', QUICK_START_GUIDE_URL)}\n")
    if not interactive:
        return 1
    destination.write("\n")
    if not wizard_ask_yes_no("Run the guided setup wizard now?", True, input_func, destination):
        return 0
    destination.write("\n")
    runner = run_setup_wizard if setup_runner is None else setup_runner
    return runner(parser, input_func=input_func, input_stream=source, stream=destination, interactive=True, install_context=context, show_banner=False)


# Restarts argument handling with the wizard's saved monitoring command
def launch_wizard_monitoring(arguments):
    original_argv = list(sys.argv)
    sys.argv = [original_argv[0], *arguments]
    try:
        main()
    finally:
        sys.argv = original_argv
    return 0


# Parses command-line settings and starts the requested GitHub Monitor action
def main():
    global CLI_CONFIG_PATH, DOTENV_FILE, LOCAL_TIMEZONE, LIVENESS_CHECK_COUNTER, GITHUB_TOKEN, GITHUB_API_URL, CSV_FILE, DISABLE_LOGGING, GITHUB_LOGFILE, PROFILE_NOTIFICATION, EVENT_NOTIFICATION, REPO_NOTIFICATION, REPO_UPDATE_DATE_NOTIFICATION, ERROR_NOTIFICATION, GITHUB_CHECK_INTERVAL, SMTP_PASSWORD, stdout_bck, DO_NOT_MONITOR_GITHUB_EVENTS, TRACK_REPOS_CHANGES, REPOS_TO_MONITOR, GET_ALL_REPOS, CONTRIB_NOTIFICATION, TRACK_CONTRIB_CHANGES, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION, VERBOSE_MODE, DEBUG_MODE, COLORED_OUTPUT, TRUNCATE_CHARS, TARGET_GITHUB_USERNAME

    if "--verbose" in sys.argv:
        VERBOSE_MODE = True
    if "--debug" in sys.argv:
        DEBUG_MODE = True

    if "--generate-config" in sys.argv and "--doctor" not in sys.argv and "--setup" not in sys.argv:
        config_content = CONFIG_BLOCK.strip("\n") + "\n"
        # Check if a filename was provided after --generate-config
        try:
            idx = sys.argv.index("--generate-config")
            if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("-"):
                # Write directly to file to avoid PowerShell UTF-16 redirection issues
                output_file = sys.argv[idx + 1]
                debug_print("Opening generated configuration for write", path=output_file)
                backup_path, written = write_generated_config(output_file, config_content, force="--force" in sys.argv)
                if not written:
                    print("Config was not replaced. The existing file is unchanged.")
                    sys.exit(1)
                debug_print("Generated configuration write succeeded", path=output_file, bytes=len(config_content.encode('utf-8')))
                print(f"Config written to: {output_file}")
                if backup_path is not None:
                    print(f"Previous config backed up to: {backup_path}")
                sys.exit(0)
        except (ValueError, IndexError) as exc:
            debug_swallowed_exception("Generated configuration argument resolution", exc)
        except FileExistsError as exc:
            advice = make_recovery_advice("file.exists", "The generated configuration would replace an existing file", str(exc), False, f"{type(exc).__name__}: {exc}", CONFIG_GUIDE_URL)
            print_recovery_advice(advice)
            sys.exit(1)
        except OSError as exc:
            debug_print("Generated configuration write", path=locals().get('output_file', '<unknown>'), outcome="failed", error=f"{type(exc).__name__}: {exc}")
            advice = make_recovery_advice("file.unwritable", "The generated configuration could not be written", "Check the destination path and file permissions", False, f"{type(exc).__name__}: {exc}", CONFIG_GUIDE_URL)
            print_recovery_advice(advice)
            sys.exit(1)
        # No filename provided so write to stdout buffer as UTF-8
        sys.stdout.buffer.write(config_content.encode("utf-8"))
        sys.stdout.buffer.flush()
        sys.exit(0)

    if "--version" in sys.argv:
        print(f"{os.path.basename(sys.argv[0])} v{VERSION}")
        sys.exit(0)

    stdout_bck = sys.stdout

    # Screen clearing and the startup banner happen before argparse, so their output settings are resolved first
    apply_early_output_config()
    if "--no-color" in sys.argv:
        COLORED_OUTPUT = False
    init_color_output(stdout_bck)
    if not isinstance(sys.stdout, TerminalStream):
        sys.stdout = TerminalStream(sys.stdout)

    if len(sys.argv) > 1 and "--setup" not in sys.argv:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    keep_cli_history = any(flag in sys.argv for flag in ("--doctor", "--set-github-token", "--set-webhook-url"))
    if CLEAR_SCREEN and (VERBOSE_MODE or DEBUG_MODE):
        verbose_print("Terminal clearing was skipped so diagnostic output remains visible")
        debug_print("Terminal screen clear skipped because diagnostic mode is active")
    clear_screen(CLEAR_SCREEN and sys.stdout.isatty() and not (VERBOSE_MODE or DEBUG_MODE) and not keep_cli_history)
    print_startup_banner()

    parser = argparse.ArgumentParser(
        prog="github_monitor",
        description=(f"Monitor a GitHub user's profile and activity with customizable email alerts [ {PROJECT_URL}/ ]"), formatter_class=argparse.RawTextHelpFormatter
    )

    # Positional
    parser.add_argument(
        "username",
        nargs="?",
        metavar="GITHUB_USERNAME",
        help="GitHub username",
        type=str
    )

    # Version, just to list in help, it is handled earlier
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{VERSION}"
    )

    # Configuration & dotenv files
    conf = parser.add_argument_group("Configuration & dotenv files")
    conf.add_argument(
        "--config-file",
        dest="config_file",
        metavar="PATH",
        help="Location of the optional config file",
    )
    conf.add_argument(
        "--generate-config",
        dest="generate_config",
        nargs="?",
        const=True,
        metavar="FILENAME",
        help="Print default config template and exit (on Windows PowerShell specify a filename to avoid redirect encoding issues)",
    )
    conf.add_argument(
        "--force",
        dest="force",
        action="store_true",
        help="With --generate-config, replace an existing file without prompting after a timestamped backup",
    )
    conf.add_argument(
        "--setup",
        dest="setup",
        action="store_true",
        help="Run the interactive setup wizard and save config plus dotenv files",
    )
    conf.add_argument(
        "--env-file",
        dest="env_file",
        metavar="PATH",
        help="Path to optional dotenv file (auto-search if not set, disable with 'none')",
    )
    conf.add_argument(
        "--set-webhook-url",
        dest="set_webhook_url",
        action="store_true",
        help="Save a Discord or ntfy webhook URL through a hidden prompt",
    )

    # API settings
    creds = parser.add_argument_group("API settings")
    token_input = creds.add_mutually_exclusive_group()
    token_input.add_argument(
        "--set-github-token",
        dest="set_github_token",
        action="store_true",
        help="Validate and save a GitHub token through a hidden prompt"
    )
    token_input.add_argument(
        "-t", "--github-token",
        dest="github_token",
        metavar="GITHUB_TOKEN",
        type=str,
        help="GitHub personal access token for this run (may remain in shell history)"
    )
    creds.add_argument(
        "-x", "--github-url",
        dest="github_url",
        metavar="GITHUB_URL",
        type=str,
        help="GitHub API URL"
    )

    # Notifications
    notify = parser.add_argument_group("Notifications")
    notify.add_argument(
        "-p", "--notify-profile",
        dest="notify_profile",
        action="store_true",
        default=None,
        help="Email when user's profile changes"
    )
    notify.add_argument(
        "-s", "--notify-events",
        dest="notify_events",
        action="store_true",
        default=None,
        help="Email when new GitHub events appear"
    )
    notify.add_argument(
        "-q", "--notify-repo-changes",
        dest="notify_repo_changes",
        action="store_true",
        default=None,
        help="Email when user's repositories change (stargazers, watchers, forks, issues, PRs, discussions, description etc., except for update date)"
    )
    notify.add_argument(
        "-u", "--notify-repo-update-date",
        dest="notify_repo_update_date",
        action="store_true",
        default=None,
        help="Email when user's repositories update date changes"
    )
    notify.add_argument(
        "-y", "--notify-daily-contribs",
        dest="notify_daily_contribs",
        action="store_true",
        default=None,
        help="Email when user's daily contributions count changes"
    )
    notify.add_argument(
        "-e", "--no-error-notify",
        dest="notify_errors",
        action="store_false",
        default=None,
        help="Disable email on errors"
    )
    notify.add_argument(
        "--send-test-email",
        dest="send_test_email",
        action="store_true",
        help="Send test email to verify SMTP settings"
    )

    webhook_notify = parser.add_argument_group("Webhook notifications")
    webhook_toggle = webhook_notify.add_mutually_exclusive_group()
    webhook_toggle.add_argument(
        "--webhook",
        dest="webhook_enabled",
        action="store_true",
        default=None,
        help="Enable the configured webhook alerts"
    )
    webhook_toggle.add_argument(
        "--no-webhook",
        dest="webhook_enabled",
        action="store_false",
        default=None,
        help="Disable the configured webhook alerts"
    )
    webhook_notify.add_argument(
        "--webhook-url",
        dest="webhook_url",
        metavar="URL",
        type=str,
        help="Use one Discord webhook or ntfy topic URL for this run (may remain in shell history)"
    )
    webhook_notify.add_argument(
        "--webhook-provider",
        dest="webhook_provider",
        choices=("discord", "ntfy"),
        help="Webhook request format for this run (default: configured provider)"
    )
    webhook_notify.add_argument(
        "--webhook-profile",
        dest="webhook_profile",
        action="store_true",
        default=None,
        help="Send a webhook alert when the user's profile changes"
    )
    webhook_notify.add_argument(
        "--webhook-events",
        dest="webhook_events",
        action="store_true",
        default=None,
        help="Send a webhook alert when new GitHub events appear"
    )
    webhook_notify.add_argument(
        "--webhook-repo-changes",
        dest="webhook_repo_changes",
        action="store_true",
        default=None,
        help="Send a webhook alert when the user's repositories change"
    )
    webhook_notify.add_argument(
        "--webhook-repo-update-date",
        dest="webhook_repo_update_date",
        action="store_true",
        default=None,
        help="Send a webhook alert when a repository update date changes"
    )
    webhook_notify.add_argument(
        "--webhook-daily-contribs",
        dest="webhook_daily_contribs",
        action="store_true",
        default=None,
        help="Send a webhook alert when the user's daily contributions count changes"
    )
    webhook_error_toggle = webhook_notify.add_mutually_exclusive_group()
    webhook_error_toggle.add_argument(
        "--webhook-errors",
        dest="webhook_errors",
        action="store_true",
        default=None,
        help="Send webhook alerts when monitoring has a problem"
    )
    webhook_error_toggle.add_argument(
        "--no-webhook-error-notify",
        dest="webhook_errors",
        action="store_false",
        default=None,
        help="Disable webhook alerts when monitoring has a problem"
    )
    webhook_notify.add_argument(
        "--send-test-webhook",
        dest="send_test_webhook",
        action="store_true",
        help="Send one test webhook without starting monitoring"
    )

    # Intervals & timers
    times = parser.add_argument_group("Intervals & timers")
    times.add_argument(
        "-c", "--check-interval",
        dest="check_interval",
        metavar="SECONDS",
        type=int,
        help="Time between monitoring checks, in seconds"
    )

    # Listing
    listing = parser.add_argument_group("Listing")
    listing.add_argument(
        "-r", "--list-repos",
        dest="list_repos",
        action="store_true",
        default=None,
        help="List user's repositories with stats"
    )
    listing.add_argument(
        "-g", "--list-starred-repos",
        dest="list_starred_repos",
        action="store_true",
        default=None,
        help="List user's starred repositories"
    )
    listing.add_argument(
        "-f", "--list-followers-followings",
        dest="list_followers_and_followings",
        action="store_true",
        default=None,
        help="List user's followers & followings"
    )
    listing.add_argument(
        "-l", "--list-recent-events",
        dest="list_recent_events",
        action="store_true",
        default=None,
        help="List user's recent GitHub events"
    )
    listing.add_argument(
        "-n", "--recent-events-count",
        dest="recent_events_count",
        metavar="N",
        type=int,
        help="Number of events to list (use with -l)"
    )

    # Features & output
    opts = parser.add_argument_group("Features & output")
    opts.add_argument(
        "--doctor",
        dest="doctor",
        action="store_true",
        help="Run a comprehensive read-only setup preflight and exit"
    )
    opts.add_argument(
        "-j", "--track-repos-changes",
        dest="track_repos_changes",
        action="store_true",
        default=None,
        help="Track user's repository changes (changed stargazers, watchers, forks, issues, PRs, discussions, description, update date etc.)"
    )
    opts.add_argument(
        "-k", "--no-monitor-events",
        dest="no_monitor_events",
        action="store_true",
        default=None,
        help="Disable event monitoring"
    )
    opts.add_argument(
        "-a", "--get-all-repos",
        dest="get_all_repos",
        action="store_true",
        default=None,
        help="Fetch all user repos (owned, forks, collaborations)"
    )
    opts.add_argument(
        "-b", "--csv-file",
        dest="csv_file",
        metavar="CSV_FILE",
        type=str,
        help="Write new events & profile changes to CSV"
    )
    opts.add_argument(
        "-d", "--disable-logging",
        dest="disable_logging",
        action="store_true",
        default=None,
        help="Disable logging to github_monitor_<username>.log"
    )
    opts.add_argument(
        "--no-color",
        dest="no_color",
        action="store_true",
        default=None,
        help="Disable coloured output in the terminal"
    )
    opts.add_argument(
        "--truncate",
        dest="truncate",
        metavar="N",
        type=int,
        help="Max characters per screen line (not log), use 999 to auto-detect terminal width, ignored if -d is set"
    )
    opts.add_argument(
        "-m", "--track-contribs-changes",
        dest="track_contribs_changes",
        action="store_true",
        default=None,
        help="Track user's daily contributions count and log changes"
    )
    opts.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        default=None,
        help="Show user-facing decisions, degraded features and the complete startup summary"
    )
    opts.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        default=None,
        help="Show sanitized operations, requests, files, retries and monitoring timing"
    )
    opts.add_argument(
        "--repos",
        dest="repos",
        metavar="REPO_LIST",
        type=str,
        help="Comma-separated list of repository names to monitor (only when -j/--track-repos-changes is enabled). Overrides REPOS_TO_MONITOR config. Example: --repos \"repo1,repo2,repo3\""
    )

    args = parser.parse_args()

    if args.username:
        normalized_target = wizard_normalize_target(args.username)
        if not normalized_target:
            parser.error("GITHUB_USERNAME must be a GitHub username or complete profile URL")
        args.username = normalized_target

    if args.setup:
        allowed = {"setup", "config_file", "env_file", "verbose", "debug", "no_color"}
        incompatible = [name for name, value in vars(args).items() if name not in allowed and value not in (None, False)]
        if incompatible:
            parser.error("--setup can only be combined with --config-file, --env-file, --verbose or --debug")
        if isinstance(args.env_file, str) and args.env_file.casefold() == "none":
            parser.error("--setup requires a dotenv destination and cannot use --env-file none")
        sys.exit(run_setup_wizard(parser, args.config_file, args.env_file, monitor_launcher=launch_wizard_monitoring, show_banner=False))

    if args.set_github_token and args.set_webhook_url:
        parser.error("--set-github-token cannot be combined with --set-webhook-url")

    # Reached only when --generate-config did not already handle and exit, so --force would do nothing here
    if args.force:
        parser.error("--force only applies to --generate-config with a filename")

    apply_diagnostic_cli_overrides(args)

    if args.doctor:
        incompatible = (args.setup, args.generate_config, args.set_github_token, args.set_webhook_url, args.send_test_email, args.send_test_webhook, args.list_repos, args.list_starred_repos, args.list_followers_and_followings, args.list_recent_events)
        if any(incompatible):
            parser.error("--doctor cannot be combined with setup, listing or one-shot delivery commands")
        sys.exit(run_doctor_preflight(args, parser, show_banner=False))

    config_discovery_disabled = isinstance(args.config_file, str) and args.config_file.casefold() == "none"
    if args.config_file and not config_discovery_disabled:
        CLI_CONFIG_PATH = os.path.expanduser(args.config_file)
    elif config_discovery_disabled:
        CLI_CONFIG_PATH = None

    cfg_path = None if config_discovery_disabled else find_config_file(CLI_CONFIG_PATH)
    configured_settings = set()

    if not cfg_path and CLI_CONFIG_PATH:
        config_command = render_install_command(["--generate-config", "github_monitor.conf"])
        advice = make_recovery_advice("config.missing", f"Config file '{CLI_CONFIG_PATH}' does not exist", f"Correct --config-file or generate a new configuration with: {config_command}", False, f"FileNotFoundError: {CLI_CONFIG_PATH}", CONFIG_GUIDE_URL)
        print_recovery_advice(advice)
        sys.exit(1)

    if cfg_path:
        if not load_config_file(cfg_path, loaded_names_out=configured_settings, diagnostic_overrides=(args.verbose is True, args.debug is True)):
            sys.exit(1)

    apply_diagnostic_cli_overrides(args)
    apply_tls_verification_setting()
    env_path = load_startup_secrets(args.env_file, configured_settings)
    apply_startup_cli_overrides(args, configured_settings)
    if args.no_color is True:
        COLORED_OUTPUT = False
    init_color_output(stdout_bck)

    if not args.username and TARGET_GITHUB_USERNAME:
        saved_target = wizard_normalize_target(TARGET_GITHUB_USERNAME)
        if not saved_target:
            advice = make_recovery_advice("config.value_invalid", "The saved GitHub target is invalid", "Set TARGET_GITHUB_USERNAME to a GitHub username or complete profile URL", False, f"Rejected target: {TARGET_GITHUB_USERNAME}", CONFIG_GUIDE_URL)
            print_recovery_advice(advice)
            sys.exit(1)
        args.username = saved_target

    if len(sys.argv) == 1 and not args.username:
        sys.exit(run_zero_argument_welcome(parser, show_banner=False))

    if args.set_github_token:
        try:
            run_set_github_token(args.env_file, api_url=args.github_url, config_path=cfg_path)
        except Exception as e:
            print_recovery_advice(classify_recovery_error(e, "github_token"))
            sys.exit(1)
        sys.exit(0)

    if args.set_webhook_url:
        try:
            run_set_webhook_url(args.env_file, config_path=cfg_path)
        except Exception as e:
            print_recovery_advice(classify_recovery_error(e, "webhook"))
            sys.exit(1)
        sys.exit(0)

    apply_webhook_cli_overrides(args, parser)
    apply_monitoring_cli_overrides(args, parser)

    try:
        TRUNCATE_CHARS = resolve_truncate_chars(args.truncate, TRUNCATE_CHARS, DISABLE_LOGGING)
    except OSError as exc:
        print_recovery_advice(classify_recovery_error(exc, "terminal"))
        sys.exit(1)

    if type(GITHUB_CHECK_INTERVAL) is not int or GITHUB_CHECK_INTERVAL <= 0:
        advice = make_recovery_advice("config.value_invalid", "The GitHub polling interval is invalid", "Set GITHUB_CHECK_INTERVAL or --check-interval to a positive number of seconds", False, f"GITHUB_CHECK_INTERVAL={GITHUB_CHECK_INTERVAL}", CONFIG_GUIDE_URL)
        print_recovery_advice(advice)
        sys.exit(1)

    local_tz = None
    if LOCAL_TIMEZONE == "Auto":
        if get_localzone is not None:
            try:
                local_tz = get_localzone()
            except Exception as exc:
                debug_swallowed_exception("Local timezone detection", exc)
        if local_tz:
            LOCAL_TIMEZONE = str(local_tz)
        else:
            advice = make_recovery_advice("timezone.invalid", "The local timezone could not be detected", "Install tzlocal for automatic detection or set LOCAL_TIMEZONE to a valid pytz timezone", False, "tzlocal did not return a timezone", CONFIG_GUIDE_URL)
            print_recovery_advice(advice)
            sys.exit(1)
    else:
        if not is_valid_timezone(LOCAL_TIMEZONE):
            advice = make_recovery_advice("timezone.invalid", f"Configured LOCAL_TIMEZONE '{LOCAL_TIMEZONE}' is not valid", "Set LOCAL_TIMEZONE to a valid pytz timezone name", False, f"Rejected timezone: {LOCAL_TIMEZONE}", CONFIG_GUIDE_URL)
            print_recovery_advice(advice)
            sys.exit(1)

    if not check_internet():
        sys.exit(1)

    if args.send_test_email:
        print("* Sending test email notification ...\n")
        if send_email("github_monitor: test email", "This is test email - your SMTP settings seems to be correct !", "", SMTP_SSL, smtp_timeout=5) == 0:
            print("* Email sent successfully !")
        else:
            sys.exit(1)
        sys.exit(0)

    if args.send_test_webhook:
        print("* Sending test webhook notification ...\n")
        if send_webhook("GitHub Monitor test", "Your webhook alerts are set up correctly.", "event", force=True) == 0:
            print("* Webhook sent successfully !")
        else:
            sys.exit(1)
        sys.exit(0)

    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_classic_personal_access_token":
        token_command = render_install_command(["--set-github-token"])
        advice = make_recovery_advice("auth.github_token_missing", "No usable GitHub token is configured", f"Create a token then run: {token_command}", False, "GITHUB_TOKEN is empty or still uses the generated placeholder", AUTH_GUIDE_URL)
        print_recovery_advice(advice)
        sys.exit(1)

    if not args.username:
        advice = make_recovery_advice("target.missing", "A GitHub username is required", "Add GITHUB_USERNAME to the monitoring command", False, "The positional GITHUB_USERNAME argument was empty", QUICK_START_GUIDE_URL)
        print_recovery_advice(advice)
        sys.exit(1)

    if not GITHUB_API_URL:
        advice = make_recovery_advice("config.value_invalid", "GITHUB_API_URL is empty", "Set GITHUB_API_URL in config or pass --github-url with a complete HTTPS API URL", False, "The effective GITHUB_API_URL was empty", CONFIG_GUIDE_URL)
        print_recovery_advice(advice)
        sys.exit(1)

    if args.list_followers_and_followings:
        try:
            github_print_followers_and_followings(args.username)
        except Exception as e:
            print_recovery_advice(classify_recovery_error(e, "target"))
            sys.exit(1)
        sys.exit(0)

    if args.list_repos:
        try:
            github_print_repos(args.username)
        except Exception as e:
            print_recovery_advice(classify_recovery_error(e, "target"))
            sys.exit(1)
        sys.exit(0)

    if args.list_starred_repos:
        try:
            github_print_starred_repos(args.username)
        except Exception as e:
            print_recovery_advice(classify_recovery_error(e, "target"))
            sys.exit(1)
        sys.exit(0)

    if CSV_FILE:
        try:
            debug_print("Opening CSV output for startup write check", path=CSV_FILE)
            with open(CSV_FILE, 'a', newline='', buffering=1, encoding="utf-8") as _:
                pass
            debug_print("CSV startup write check succeeded", path=CSV_FILE)
        except Exception as e:
            debug_print("CSV startup write check", path=CSV_FILE, outcome="failed", error=f"{type(e).__name__}: {e}")
            advice = classify_recovery_error(e, "file")
            if advice.code == "unknown":
                advice = make_recovery_advice("file.unwritable", "The CSV file cannot be opened for writing", "Check CSV_FILE and its parent directory permissions", False, f"{type(e).__name__}: {e}", CONFIG_GUIDE_URL)
            print_recovery_advice(advice)
            sys.exit(1)

    if args.list_recent_events:
        if args.recent_events_count and args.recent_events_count > 0:
            events_n = args.recent_events_count
        else:
            events_n = 5
        try:
            github_list_events(args.username, events_n, CSV_FILE)
        except Exception as e:
            print_recovery_advice(classify_recovery_error(e, "target"))
            sys.exit(1)
        sys.exit(0)

    try:
        ascii_log_separators_enabled()
    except ValueError as e:
        advice = make_recovery_advice("config.value_invalid", "ASCII_LOG_SEPARATORS is invalid", "Set ASCII_LOG_SEPARATORS to Auto, On or Off", False, f"{type(e).__name__}: {e}", CONFIG_GUIDE_URL)
        print_recovery_advice(advice)
        sys.exit(1)

    if not DISABLE_LOGGING:
        log_path = resolve_output_log_path(args.username)
        try:
            debug_print("Ensuring output log directory exists", path=log_path.parent)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            debug_print("Output log directory ready", path=log_path.parent)
            FINAL_LOG_PATH = str(log_path)
            sys.stdout = Logger(FINAL_LOG_PATH)
        except Exception as e:
            advice = make_recovery_advice("file.unwritable", "The output log could not be opened", "Check GITHUB_LOGFILE and its parent directory permissions or use --disable-logging", False, f"{type(e).__name__}: {e}", CONFIG_GUIDE_URL)
            print_recovery_advice(advice)
            sys.exit(1)
    else:
        FINAL_LOG_PATH = None

    if SMTP_HOST.startswith("your_smtp_server_"):
        EVENT_NOTIFICATION = False
        PROFILE_NOTIFICATION = False
        REPO_NOTIFICATION = False
        REPO_UPDATE_DATE_NOTIFICATION = False
        CONTRIB_NOTIFICATION = False
        ERROR_NOTIFICATION = False

    startup_rows = build_startup_summary(args.username, cfg_path, env_path, FINAL_LOG_PATH)
    emit_startup_summary(startup_rows, show_full=bool(VERBOSE_MODE or DEBUG_MODE))

    out = f"\nMonitoring GitHub user {args.username}"
    print(out)
    # print("-" * len(out))
    print("─" * HORIZONTAL_LINE1)

    # We define signal handlers only for Linux, Unix & MacOS since Windows has limited number of signals supported
    if platform.system() != 'Windows':
        signal.signal(signal.SIGUSR1, toggle_profile_changes_notifications_signal_handler)
        signal.signal(signal.SIGUSR2, toggle_new_events_notifications_signal_handler)
        signal.signal(signal.SIGCONT, toggle_repo_changes_notifications_signal_handler)
        signal.signal(signal.SIGPIPE, toggle_repo_update_date_changes_notifications_signal_handler)
        signal.signal(signal.SIGURG, toggle_contrib_changes_notifications_signal_handler)
        signal.signal(signal.SIGTRAP, increase_check_signal_handler)
        signal.signal(signal.SIGABRT, decrease_check_signal_handler)
        signal.signal(signal.SIGHUP, reload_secrets_signal_handler)

    github_monitor_user(args.username, CSV_FILE)

    sys.stdout = stdout_bck
    sys.exit(0)


if __name__ == "__main__":
    main()
