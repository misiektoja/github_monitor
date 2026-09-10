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
wcwidth (optional, measures wide characters correctly when TRUNCATE_CHARS is set)
"""

VERSION = "2.7"

PROJECT_URL = "https://github.com/misiektoja/github_monitor"
DOCUMENTATION_URL = "https://misiektoja.github.io/github_monitor"
QUICK_START_GUIDE_URL = f"{DOCUMENTATION_URL}/setup-and-first-run/"
CONFIG_GUIDE_URL = f"{DOCUMENTATION_URL}/configuration/#configuration-file"
INSTALL_GUIDE_URL = f"{DOCUMENTATION_URL}/installation/"
CSV_GUIDE_URL = f"{DOCUMENTATION_URL}/usage/#csv-export"
INTERVALS_GUIDE_URL = f"{DOCUMENTATION_URL}/configuration/#check-intervals"
AUTH_GUIDE_URL = f"{DOCUMENTATION_URL}/setup-and-first-run/#github-personal-access-token"
GITHUB_TOKEN_SETTINGS_URL = "https://github.com/settings/tokens"
SECRETS_GUIDE_URL = f"{DOCUMENTATION_URL}/configuration/#storing-secrets"
SMTP_GUIDE_URL = f"{DOCUMENTATION_URL}/configuration/#smtp-settings"
WEBHOOK_GUIDE_URL = f"{DOCUMENTATION_URL}/configuration/#webhook-settings"
DEBUG_GUIDE_URL = f"{DOCUMENTATION_URL}/troubleshooting/#verbose-and-debug-output"
TLS_GUIDE_URL = f"{DOCUMENTATION_URL}/configuration/#tls-verification"
SUPPORT_GUIDE_URL = f"{DOCUMENTATION_URL}/about/#support"
DOCTOR_GUIDE_URL = f"{DOCUMENTATION_URL}/troubleshooting/#doctor-preflight"

# Shared doctor labels for the two delivery channels, kept identical to the sibling monitors
SMTP_READY_CHECK_LABEL = "SMTP connection and login succeeded"
WEBHOOK_READY_CHECK_LABEL = "Webhook URL, headers and alert choices look valid"

# The label every sibling monitor uses when email alerts are on but the settings they would use cannot deliver
EMAIL_UNUSABLE_CHECK_LABEL = "Email alerts are enabled but unusable"

# Declared once so the startup gate, the packaging metadata and the doctor environment check cannot disagree
MINIMUM_PYTHON_VERSION = (3, 10)
MINIMUM_PYTHON_VERSION_TEXT = ".".join(str(part) for part in MINIMUM_PYTHON_VERSION)

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

# Optional ntfy access token for Bearer authentication
# Prefer an environment variable or dotenv file instead of storing this token here
NTFY_ACCESS_TOKEN = ""

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
LIVENESS_CHECK_INTERVAL = 86400  # 24 hours

# URL used to verify internet connectivity at startup
CHECK_INTERNET_URL = GITHUB_API_URL

# Timeout used when checking initial internet connectivity; in seconds
CHECK_INTERNET_TIMEOUT = 5

# Whether to verify TLS certificates on every outbound connection, email delivery included
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

# Max characters per line when printing to screen to avoid line wrapping
# Does not affect log file output
# Set to 999 to auto-detect terminal width
# Applies only when DISABLE_LOGGING is False
# Can also be set via the --truncate flag
TRUNCATE_CHARS = 0

# Width of main horizontal line
HORIZONTAL_LINE1 = 105

# Width of horizontal line for repositories list output
HORIZONTAL_LINE2 = 80

# Whether to clear the terminal screen after starting the tool
CLEAR_SCREEN = True

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
# The defaults below are what the tool uses while this block stays commented out. Uncomment it to override
# them and keep only the lines you want to change, so the rest keep following the tool's own defaults.
# COLOR_THEME = {
#     # Headings and commands the wizard tells you to run
#     "header": "bright_cyan",
#     "section": "bright_white",
#     # Identity
#     "username": "bright_cyan underline",
#     "id": "bright_magenta",
#     # Presence and visibility status values
#     "status_online": "green",
#     "status_offline": "red",
#     "status_other": "white",
#     # GitHub objects
#     "repository": "green",
#     "event": "bright_green",
#     "commit": "bright_yellow",
#     "branch": "bright_magenta",
#     "duration": "green",
#     # Misc
#     "timestamp_label": "",
#     "timestamp_value": "cyan",
#     "info": "cyan",
#     "warning": "yellow",
#     "error": "red",
#     "signal": "yellow",
#     "email": "bright_cyan",
#     "webhook": "bright_blue",
#     # Dates
#     "date": "magenta",
#     "date_range": "magenta",
#     # Boolean values
#     "boolean_true": "green",
#     "boolean_false": "red",
#     # Counters and differences
#     "count_up": "green",
#     "count_down": "red",
#     "link": "blue underline",
#     # Help screen
#     "help_heading": "bright_cyan bold",
#     "help_usage": "bright_white bold",
#     "help_option": "bright_green",
#     "help_metavar": "yellow",
#     "help_placeholder": "bright_magenta",
#     "help_command": "bright_white",
#     "help_comment": "bright_black",
#     "help_default": "bright_black",
# }

# Whether output includes user-facing decisions, degraded features and complete startup settings
# Independent of DEBUG_MODE, so enable both to see everything
# Can also be enabled via --verbose, which turns it on regardless of this setting
VERBOSE_MODE = False

# Whether output includes sanitized operations, requests, files, retries and poll timing
# Independent of VERBOSE_MODE, so enable both to see everything
# Can also be enabled via --debug, which turns it on regardless of this setting
DEBUG_MODE = False

# Whether verbose output confirms each delivered email and webhook alert
# Applies only when VERBOSE_MODE is enabled
DELIVERY_CONFIRMATIONS = True

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
NTFY_ACCESS_TOKEN = ""
WEBHOOK_TEMPLATE = {}
WEBHOOK_TRANSFORMS = []
GITHUB_CHECK_INTERVAL = 0
LOCAL_TIMEZONE = ""

# How LOCAL_TIMEZONE was arrived at, which decides the row doctor prints for it
LOCAL_TIMEZONE_STATE = "config"
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
TRUNCATE_CHARS = 0
HORIZONTAL_LINE1 = 0
HORIZONTAL_LINE2 = 0
# Counts the reports printed so far, so a check can tell whether it said anything before the banner claims it was quiet
REPORTS_PRINTED = 0
CLEAR_SCREEN = False
COLORED_OUTPUT = False
COLOR_THEME: dict = {}

# True once monitoring has printed its header, so a verbose notice after that closes its own block
MONITORING_ACTIVE = False

# True while a verbose line is waiting for the timestamp trailer that closes its block
PENDING_NOTICE_BLOCK = False

# Features already reported unavailable, mapped to the alert they block, so a lasting outage is reported once
DEGRADED_FEATURES: dict = {}

# Features reported unavailable during the check in progress, so the rest can be reported as recovered
DEGRADED_FEATURES_SEEN: set = set()

VERBOSE_MODE = False
DEBUG_MODE = False
DELIVERY_CONFIRMATIONS = True
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

# Every layer that can supply a secret, so a source outside the set is a typo rather than a new layer
SECRET_SOURCE_ORDER = ("built-in configuration", "configuration file", "dotenv file", "dotenv file reload", "environment", "command line")

# Version incremented when SIGHUP reloads the GitHub token
GITHUB_AUTH_REFRESH_VERSION = 0

# Seconds rather than checks, because a failing run usually retries on a different interval than a healthy one
LIVENESS_REMINDER_SECONDS = LIVENESS_CHECK_INTERVAL if LIVENESS_CHECK_INTERVAL > 0 else 0
# How long a failure the tool can retry away must last before it is alerted, a failure it cannot is alerted at once
ERROR_ALERT_AFTER_SECONDS = 300  # 5 minutes
# How long a channel that could not deliver an error alert waits before the next attempt, doubled on every further failure up to the cap
ERROR_ALERT_RETRY_SECONDS = 300  # 5 minutes
ERROR_ALERT_RETRY_MAX_SECONDS = 3600  # 1 hour


# Tracks the error alert per channel: what was delivered, and how long a channel that failed waits before the next attempt
class ErrorAlertState:
    # Starts with nothing delivered and no channel on hold
    def __init__(self) -> None:
        self.email_sent = False
        self.webhook_sent = False
        self.email_failures = 0
        self.webhook_failures = 0
        self.email_retry_at = 0
        self.webhook_retry_at = 0

    # Forgets the delivered alert and any hold, so the next failure earns each channel a new one
    def reset(self) -> None:
        self.__init__()

    # Tells whether a channel still owes the alert and its wait after a failed attempt, if any, has passed
    def pending(self, channel: str, enabled, now: int) -> bool:
        return bool(enabled) and not getattr(self, f"{channel}_sent") and now >= getattr(self, f"{channel}_retry_at")

    # Records one attempt, holding a channel that failed for a growing wait so a broken server is not dialled on every check
    def record(self, channel: str, attempted: bool, delivered: bool, now: int) -> None:
        if not attempted:
            return
        if delivered:
            setattr(self, f"{channel}_sent", True)
            setattr(self, f"{channel}_failures", 0)
            setattr(self, f"{channel}_retry_at", 0)
            return
        failures = getattr(self, f"{channel}_failures") + 1
        delay = min(ERROR_ALERT_RETRY_SECONDS * 2 ** (failures - 1), ERROR_ALERT_RETRY_MAX_SECONDS)
        setattr(self, f"{channel}_failures", failures)
        setattr(self, f"{channel}_retry_at", now + delay)
        print(f"* The {channel} alert is on hold for {display_time(delay)} after {failures} {'attempt' if failures == 1 else 'attempts'}, then tried again")


stdout_bck = None
csvfieldnames = ['Date', 'Type', 'Name', 'Old', 'New']

CLI_CONFIG_PATH = None

# Set when --config-file none switches discovery off, so no later lookup can find a file the run rejected
CONFIG_DISCOVERY_DISABLED = False

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
import platform


# Writes the uncoloured startup banner for bootstrap failures
def _write_plain_startup_banner(destination):
    destination.write(STARTUP_BANNER + "\n")
    destination.write(f"{'':21}v{VERSION}\n\n")


# Renders an environment-only doctor report when Python cannot run the full module
def bootstrap_doctor_python_report(stream=None):
    if sys.version_info >= MINIMUM_PYTHON_VERSION:
        return None
    destination = sys.stdout if stream is None else stream
    version = ".".join(str(part) for part in sys.version_info[:3])
    install_command = f"Install Python {MINIMUM_PYTHON_VERSION_TEXT} or newer"
    _write_plain_startup_banner(destination)
    destination.write("Running preflight checks. No files will be written. Interactive email and webhook tests run only after separate approval.\n\n")
    destination.write(f"Doctor\n\nEnvironment\n[FAIL] Python {version} is unsupported\n  Minimum supported version: {MINIMUM_PYTHON_VERSION_TEXT}\n  To fix: {install_command}\n")
    destination.write(f"\nSummary\n  1 check(s) failed, 0 warning(s). Fix the failures above before relying on the tool.\n\nGuide: {DOCTOR_GUIDE_URL}\n")
    destination.flush()
    return 1


if sys.version_info < MINIMUM_PYTHON_VERSION:
    if "--doctor" in sys.argv:
        sys.exit(bootstrap_doctor_python_report())
    print(f"* Error: Python version {MINIMUM_PYTHON_VERSION_TEXT} or higher required !")
    sys.exit(1)


# Renders an environment-only doctor report when required imports prevent full startup
def bootstrap_doctor_dependency_report(module_finder=None, stream=None):
    finder = importlib.util.find_spec if module_finder is None else module_finder
    required = (("requests", "requests"), ("urllib3", "urllib3"), ("python-dateutil", "dateutil"), ("pytz", "pytz"), ("PyGithub", "github"))
    optional = (("python-dotenv", "dotenv", "dotenv discovery and loading"), ("tzlocal", "tzlocal", "automatic timezone detection"))
    # The classic Command Prompt is the only place this library changes anything, so a machine it cannot affect is not warned about a package it does not need
    if platform.system() == "Windows":
        optional += (("colorama", "colorama", "coloured output in the classic Windows Command Prompt"),)
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
    destination.write(f"[PASS] Python {version} is supported\n  Minimum supported version: {MINIMUM_PYTHON_VERSION_TEXT}\n")
    failures = 0
    warnings = 0
    for package_name, _ in required:
        if availability[package_name]:
            destination.write(f"[PASS] Required dependency {package_name} is installed\n")
        else:
            failures += 1
            install_command = shlex.join([sys.executable, "-m", "pip", "install", package_name])
            destination.write(f"[FAIL] Required dependency {package_name} is missing\n  The full preflight cannot continue without this package\n  To fix: Install it with: {install_command}\n")
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
            destination.write(f"[WARN] Optional dependency {package_name} is not installed\n  {feature[:1].upper() + feature[1:]} will not work while other features remain available\n  To fix: Install it with: {install_command}\n")
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


# Truncates each line to a display width, expanding tabs and counting double-width characters correctly
def truncate_string_per_line(message, truncate_width, tabsize=8):
    try:
        from wcwidth import wcwidth
    except ImportError:
        # Without wcwidth every character costs one column, so truncation still applies and only wide characters are measured short
        wcwidth = len
    truncated_lines = []
    for line in message.split("\n"):
        expanded_line = line.expandtabs(tabsize)
        current_width = 0
        truncated = []
        position = 0
        style_open = False
        while position < len(expanded_line):
            # A colour sequence is copied through free of charge, so styling never eats into the visible width
            escape = SGR_SEQUENCE_RE.match(expanded_line, position)
            if escape:
                truncated.append(escape.group(0))
                style_open = escape.group(0) not in ("\x1b[0m", "\x1b[m")
                position = escape.end()
                continue
            char = expanded_line[position]
            char_width = wcwidth(char)
            if char_width is None or char_width < 0:
                char_width = 0
            if current_width + char_width > truncate_width:
                # The cut may have dropped the reset, which would leave the colour running into every later line
                if style_open:
                    truncated.append(ANSI_RESET)
                break
            truncated.append(char)
            current_width += char_width
            position += 1
        truncated_lines.append("".join(truncated))
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
    "username": "bright_cyan underline",
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
    "timestamp_value": "cyan",
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
    "link": "blue underline",
    # Help screen
    "help_heading": "bright_cyan bold",
    "help_usage": "bright_white bold",
    "help_option": "bright_green",
    "help_metavar": "yellow",
    "help_placeholder": "bright_magenta",
    "help_command": "bright_white",
    "help_comment": "bright_black",
    "help_default": "bright_black",
}

# COLOR_THEME key names used by older releases, still honoured so an existing config keeps working
_THEME_KEY_ALIASES = {"url": "link", "timestamp": "timestamp_value"}

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
# The separator is a space in prose and an equals sign in the key=value diagnostic fields.
# A bare "user" needs a colon or an equals sign and a login is never followed by a colon, so labels
# such as "user lists:" and "fetch user details:" stay uncoloured
_USER_TAG_RE = re.compile(r"((?:GitHub|for|by|of|fetch)[\t ]+user:?|\buser[:=])([\t ]+|(?<==))([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))(?![A-Za-z0-9:-])")
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
# The TLS row reports a word rather than a boolean, and its off state is the one setting that weakens
# a security property, so the state word is coloured like a boolean
_TLS_STATE_RE = re.compile(r"^(\* TLS verification:\s+)(On|Off)(.*)$")
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
    # A config written against an older key name still wins over the default, unless it also sets the current name
    for legacy_name, current_name in _THEME_KEY_ALIASES.items():
        if user_theme and legacy_name in user_theme and current_name not in user_theme:
            theme[current_name] = user_theme[legacy_name]
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
    # Detail lines are bulleted with either marker, so the label sits behind one of them
    if body[cursor:cursor + 1] in ("*", "-") and body[cursor + 1:cursor + 2].isspace():
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
    tls_match = _TLS_STATE_RE.match(line)
    if tls_match:
        prefix, state, suffix = tls_match.groups()
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
        return f"{linked_list_match.group(1)}{colorize(item_style, item)}{linked_list_match.group(3)}{colorize('link', linked_list_match.group(4))}{linked_list_match.group(5)}"
    user_list_match = _USER_LIST_RE.match(line)
    if user_list_match:
        return f"{user_list_match.group(1)}{colorize('username', user_list_match.group(2))}"
    labeled_value = _split_output_label(line, ("Timestamp:", "Liveness check, timestamp:"))
    if labeled_value:
        label, rest = labeled_value
        colored = f"{colorize('timestamp_label', label)}{colorize('timestamp_value', rest)}"
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
        return _sub_outside_color(_URL_RE, lambda match: colorize("link", match.group(0)), line)
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
    line = _sub_outside_color(_URL_RE, lambda match: colorize("link", match.group(0)), line)
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


# Colours every link in a line, for the screens printed before the output stream colouriser is installed
def colorize_links(text):
    return _sub_outside_color(_URL_RE, lambda mo: colorize("link", mo.group(0)), text)


# Colours one line of a fix block the way the output stream colours it, keeping its guide line a link
def colorize_fix_line(line):
    return colorize_links(line) if line.lstrip().startswith("Guide: ") else colorize("info", line)


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


# Help screen parts. argparse measures its column layout on the plain text, so the palette is applied to the
# finished help screen rather than to the pieces argparse assembles and the layout stays identical
_HELP_USAGE_LABEL = "usage:"
_HELP_HEADING_RE = re.compile(r"^\S.*:$")
_HELP_OPTION_ROW_RE = re.compile(r"^( {2,})(-{1,2}[^\s,]+(?:, *--?[^\s,]+)*)(.*)$")
_HELP_POSITIONAL_ROW_RE = re.compile(r"^( {2,})([A-Z][A-Z0-9_]*)( {2,}.*)$")
_HELP_COLUMN_GAP_RE = re.compile(r" {2,}")
# A value placeholder is an upper-case metavar, a choice list or an angle-bracket name, including a
# colon-joined pair of them
_HELP_METAVAR_RE = re.compile(r"\{[^}]*\}|<[^>]+>|\b[A-Z][A-Z0-9_]*(?::[A-Z][A-Z0-9_]*)*\b")
_HELP_OPTION_RE = re.compile(r"(?<![\w-])(--?[A-Za-z][\w-]*)")
_HELP_PLACEHOLDER_RE = re.compile(r"<[^>]+>")
_HELP_DEFAULT_RE = re.compile(r"\(default:[^)]*\)")


# Colours the links and the default notes inside one line of help prose
def _colorize_help_prose(line):
    line = _URL_RE.sub(lambda match: colorize("link", match.group(1)), line)
    return _HELP_DEFAULT_RE.sub(lambda match: colorize("help_default", match.group(0)), line)


# Colours the option names and the value placeholders of one usage line or option column
def _colorize_help_signature(text):
    text = _HELP_METAVAR_RE.sub(lambda match: colorize("help_metavar", match.group(0)), text)
    return _sub_outside_color(_HELP_OPTION_RE, lambda match: colorize("help_option", match.group(1)), text)


# Colours the usage block, the group headings and the option rows of the help screen
def _colorize_help_body(text):
    lines = []
    in_usage = False
    for line in text.split("\n"):
        if line.startswith(_HELP_USAGE_LABEL):
            in_usage = True
            lines.append(colorize("help_usage", _HELP_USAGE_LABEL) + _colorize_help_signature(line[len(_HELP_USAGE_LABEL):]))
            continue
        if in_usage:
            if line.strip():
                lines.append(_colorize_help_signature(line))
                continue
            in_usage = False
        if _HELP_HEADING_RE.match(line):
            lines.append(colorize("help_heading", line))
            continue
        option_row = _HELP_OPTION_ROW_RE.match(line)
        if option_row:
            indent, names, remainder = option_row.groups()
            gap = _HELP_COLUMN_GAP_RE.search(remainder)
            metavars, description = (remainder[:gap.start()], remainder[gap.start():]) if gap else (remainder, "")
            lines.append(indent + _colorize_help_signature(names + metavars) + _colorize_help_prose(description))
            continue
        positional_row = _HELP_POSITIONAL_ROW_RE.match(line)
        if positional_row:
            indent, name, description = positional_row.groups()
            lines.append(indent + colorize("help_metavar", name) + _colorize_help_prose(description))
            continue
        lines.append(_colorize_help_prose(line))
    return "\n".join(lines)


# Colours the examples of the help epilog: the task headings, the comments and the commands to run
def _colorize_help_epilog(text):
    lines = []
    for line in text.split("\n"):
        if _HELP_HEADING_RE.match(line):
            lines.append(colorize("help_heading", line))
            continue
        if not line.strip() or not line.startswith(" "):
            lines.append(_colorize_help_prose(line))
            continue
        if line.lstrip().startswith("#"):
            comment = _apply_style_nested(_colorize_help_prose(line), "help_comment")
            lines.append(comment)
            continue
        placeholders = _HELP_PLACEHOLDER_RE.sub(lambda match: colorize("help_placeholder", match.group(0)), line)
        command = _apply_style_nested(placeholders, "help_command")
        lines.append(command)
    return "\n".join(lines)


# Colours one finished help screen, leaving its column layout untouched
def colorize_help_text(text, epilog=None):
    if not COLOR_ENABLED or not isinstance(text, str) or not text:
        return text
    examples = (epilog or "").strip("\n")
    start = text.rfind(examples) if examples else -1
    if start == -1:
        return _colorize_help_body(text)
    return _colorize_help_body(text[:start]) + _colorize_help_epilog(text[start:])


# Parser that colours its own help screen and writes it past the output colouriser, which would otherwise
# repaint the finished help with the rules meant for monitoring output
class ColoredHelpParser(argparse.ArgumentParser):
    # Returns the help screen with the help palette already applied
    def format_help(self) -> str:
        return colorize_help_text(super().format_help(), self.epilog)

    # Writes one parser message straight to the terminal behind any colouring wrapper
    def _print_message(self, message, file=None) -> None:
        if not message:
            return
        stream = sys.stderr if file is None else file
        target = unwrap_terminal_stream(stream)
        target.write(sanitize_terminal_text(message))
        flush = getattr(target, "flush", None)
        if callable(flush):
            flush()


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


# Reads one answer with Python's default Ctrl+C behavior, so the prompt reports the outcome instead of the signal handler
def read_interactively(reader, *args, **kwargs):
    try:
        previous_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, signal.default_int_handler)
    except (ValueError, OSError):
        # Handlers can only be replaced from the main thread, which is where every prompt runs
        return reader(*args, **kwargs)
    try:
        return reader(*args, **kwargs)
    finally:
        try:
            signal.signal(signal.SIGINT, previous_handler)
        except (ValueError, OSError):
            pass


# Silences the repeated certificate warning once verification is off, so the choice is reported by the summary and the doctor instead of on every request
def apply_tls_verification_setting():
    if not VERIFY_SSL:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Returns the TLS context SMTP uses, unverified while VERIFY_SSL is off so email follows the same switch as every other connection
def smtp_ssl_context():
    context = ssl.create_default_context()
    if not VERIFY_SSL:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


# The last connectivity failure, so a quiet caller can classify it instead of the check printing it
LAST_CONNECTIVITY_ERROR = None


# Checks internet connectivity using the effective runtime URL and timeout
def check_internet(url=None, timeout=None, quiet=False, operation="startup connectivity", request_get=None):
    global LAST_CONNECTIVITY_ERROR
    selected_url = CHECK_INTERNET_URL if url is None else url
    selected_timeout = CHECK_INTERNET_TIMEOUT if timeout is None else timeout
    get_request = req.get if request_get is None else request_get
    LAST_CONNECTIVITY_ERROR = None
    try:
        debug_http_request("GET", selected_url, operation, selected_timeout)
        response = get_request(selected_url, timeout=selected_timeout, verify=VERIFY_SSL)
        # Any answer proves the network path works, so the status code is left to the checks that call the API
        debug_http_response("GET", selected_url, operation, getattr(response, "status_code", "unknown"))
        return True
    except req.RequestException as e:
        LAST_CONNECTIVITY_ERROR = e
        debug_swallowed_exception(f"{operation[:1].upper() + operation[1:]} request", e)
        # Quiet callers render the failure themselves, which doctor needs so nothing lands on its progress line
        if not quiet:
            print_recovery_error(e, "connectivity")
        return False


# Clears the terminal screen
def clear_screen(enabled=True):
    if not enabled:
        return
    # Don't clear screen if stdout is redirected (not a TTY)
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return
    try:
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
    except Exception as exc:
        debug_swallowed_exception("Terminal screen clear", exc)
        print("* Cannot clear the screen contents")


# Commands that print a one-shot result and exit, so the screen keeps whatever is already on it
KEEP_HISTORY_FLAGS = ("--set-github-token", "--set-smtp-password", "--set-webhook-url", "--doctor", "--send-test-email", "--send-test-webhook", "--help", "-h")


# Returns True when the running command is a one-shot whose output has to stay scrollable
def keep_terminal_history() -> bool:
    return any(flag in sys.argv for flag in KEEP_HISTORY_FLAGS)


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


# Reports the first unusable email setting as a doctor detail and an action that names the same settings
def email_settings_problem():
    fqdn_re = re.compile(r'(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}\.?$)')
    email_re = re.compile(r'[^@]+@[^@]+\.[^@]+')
    try:
        ipaddress.ip_address(str(SMTP_HOST))
    except ValueError:
        if not fqdn_re.search(str(SMTP_HOST)):
            return ("SMTP_HOST is not a valid IP address or hostname", "Correct SMTP_HOST or turn the email alerts off")
    try:
        port = int(SMTP_PORT)
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        return ("SMTP_PORT is not a port number between 1 and 65535", "Correct SMTP_PORT or turn the email alerts off")
    if not email_re.search(str(SENDER_EMAIL)) or not email_re.search(str(RECEIVER_EMAIL)):
        return ("SENDER_EMAIL or RECEIVER_EMAIL is not an email address", "Correct SENDER_EMAIL and RECEIVER_EMAIL or turn the email alerts off")
    if not SMTP_USER or not isinstance(SMTP_USER, str) or SMTP_USER == "your_smtp_user" or not SMTP_PASSWORD or not isinstance(SMTP_PASSWORD, str) or SMTP_PASSWORD == "your_smtp_password":
        return ("SMTP_USER or SMTP_PASSWORD is empty or still set to its placeholder", "Set SMTP_USER and SMTP_PASSWORD or turn the email alerts off")
    return None


# Validates the shared SMTP destination, credentials and message fields
def validate_email_settings(subject="Doctor test", body="Doctor test", body_html=""):
    problem = email_settings_problem()
    if problem is not None:
        return problem[0]
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
            smtp_object.starttls(context=smtp_ssl_context())
        debug_print("SMTP connection established", host=SMTP_HOST, port=SMTP_PORT)
        smtp_login(smtp_object, SMTP_USER, SMTP_PASSWORD)
        debug_print("SMTP authentication succeeded", host=SMTP_HOST)
        return smtp_object
    except Exception as connect_error:
        debug_print("SMTP session setup", host=SMTP_HOST, outcome="failed", error=f"{type(connect_error).__name__}: {connect_error}")
        smtp_quit_quietly(smtp_object)
        raise


# Returns the advice for an SMTP setting or message field that makes a delivery impossible
def email_settings_advice(validation_error, install_context=None):
    return make_recovery_advice("smtp.invalid", f"The SMTP settings are incorrect: {validation_error}", recovery_fix_with_guide(f"Check SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL and RECEIVER_EMAIL then run: {render_command(['--send-test-email'], install_context=install_context)}", SMTP_GUIDE_URL), False)


# Sends email notification
def send_email(subject, body, body_html, use_ssl, smtp_timeout=15):
    validation_error = validate_email_settings(subject, body, body_html)
    if validation_error is not None:
        print_recovery_advice(email_settings_advice(validation_error))
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
        verbose_delivery_print(f"Email delivered to {RECEIVER_EMAIL}: '{subject}'")
    except Exception as e:
        debug_print("SMTP delivery", outcome="failed", host=SMTP_HOST, attempt="1/1", error=f"{type(e).__name__}: {e}")
        print_recovery_error(e, "email")
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
def sanitize_error_text(value, extra_secrets=()):
    text = str(value or "")
    # A value being checked before it is saved is held by the caller and by no global, so it is passed in instead
    entered = [secret for secret in extra_secrets if isinstance(secret, str) and len(secret) >= MIN_REDACTABLE_SECRET_LENGTH]
    for secret in sorted(known_secret_values() + entered, key=len, reverse=True):
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


# Prints one delivery confirmation in verbose mode unless DELIVERY_CONFIRMATIONS turns them off
def verbose_delivery_print(message):
    if DELIVERY_CONFIRMATIONS:
        verbose_print(message)


# Prints verbose-only notices as one block, so a standalone line is not left without the timestamp trailer
def verbose_notice(*messages):
    if not VERBOSE_MODE or not messages:
        return
    for message in messages:
        verbose_print(message)
    # Before monitoring starts the notice belongs to the startup screen, which the monitoring header closes
    if MONITORING_ACTIVE:
        print_cur_ts("Timestamp:\t\t\t")


# Marks the point where output stops being the startup screen, so later notices close their own block
def mark_monitoring_started():
    global MONITORING_ACTIVE
    MONITORING_ACTIVE = True


# Closes the block of verbose lines a check printed on its own, so they are never left without a timestamp
def close_pending_notice_block():
    if PENDING_NOTICE_BLOCK:
        print_cur_ts("Timestamp:\t\t\t")


# Returns whether a configured value is a real value rather than an unedited placeholder
def secret_is_set(value):
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith("your_")


# Returns the diagnostic fields describing one secret, reporting presence alone since GitHub issues no secret at a fixed length
def secret_fields(value):
    return {"value": "set" if secret_is_set(value) else "not set"}


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


# Reports a tracked feature that cannot produce its alert, once per outage rather than on every check
def verbose_degraded_feature(feature, alert, error=None):
    global PENDING_NOTICE_BLOCK
    if error is not None:
        debug_swallowed_exception(feature, error)
    else:
        debug_print(feature, outcome="degraded", alert=alert)
    if MONITORING_ACTIVE:
        DEGRADED_FEATURES_SEEN.add(feature)
        # An outage that lasts is news once, so the repeats are left to debug until the feature works again
        if DEGRADED_FEATURES.get(feature) == alert:
            return
        DEGRADED_FEATURES[feature] = alert
    verbose_print(f"{feature} is unavailable, so {alert} cannot fire")
    # A degraded feature can be reported from inside a report, so the check closes the block instead of this line
    if VERBOSE_MODE and MONITORING_ACTIVE:
        PENDING_NOTICE_BLOCK = True


# Forgets every tracked outage, so the checks that follow report the state they find rather than an older one
def reset_degraded_features():
    DEGRADED_FEATURES.clear()
    DEGRADED_FEATURES_SEEN.clear()


# Reports every feature that was unavailable before this check and worked during it
def report_recovered_features():
    global PENDING_NOTICE_BLOCK
    recovered = [(feature, alert) for feature, alert in DEGRADED_FEATURES.items() if feature not in DEGRADED_FEATURES_SEEN]
    for feature, alert in recovered:
        del DEGRADED_FEATURES[feature]
        verbose_print(f"{feature} is available again, so {alert} can fire again")
    DEGRADED_FEATURES_SEEN.clear()
    if recovered and VERBOSE_MODE and MONITORING_ACTIVE:
        PENDING_NOTICE_BLOCK = True


# Logs the start of one monitoring poll and returns its monotonic start time
def debug_monitor_check_start(check_number, user):
    debug_print("Starting monitoring check", check=f"#{check_number}", user=user)
    return time.monotonic()


# Logs one completed monitoring poll with its duration and schedule
def debug_monitor_check_timing(check_number, user, started_at, interval):
    duration = max(0.0, time.monotonic() - started_at)
    next_check = datetime.now() + dt.timedelta(seconds=interval)
    debug_print("Completed monitoring check", check=f"#{check_number}", user=user, outcome="OK", duration=f"{duration:.3f}s", next=next_check.astimezone().isoformat(), interval=display_time(interval))


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
    prefix = (sys.executable, source_path) if manual else (sys.executable, "-m", "github_monitor")
    return InstallContext("manual" if manual else "pip", selected_system, prefix)


# Returns a readable name for the detected install method
def install_method_display_name(method=None):
    selected = detect_install_context().install_method if method is None else str(method)
    return {"pip": "PyPI install", "manual": "downloaded script"}.get(selected, selected)


# True when a command writes the dotenv file itself, so it refuses an --env-file that switches dotenv loading off
def command_writes_dotenv(arguments=()):
    return any(str(argument) == "--setup" or str(argument).startswith("--set-") for argument in arguments)


# True when a command writes the config file itself, so it refuses a --config-file that switches discovery off
def command_writes_config(arguments=()):
    return any(str(argument) == "--setup" for argument in arguments)


# Returns the --config-file and --env-file arguments this run was given, skipping any the caller already passed
def active_path_arguments(arguments=()):
    given = {str(argument) for argument in arguments}
    paths = []
    active_config = CLI_CONFIG_PATH or ("none" if CONFIG_DISCOVERY_DISABLED else None)
    # The "none" sentinel is carried so the printed command checks the setup this run checked, except into a
    # command that writes the config file, since those refuse the sentinel at their own argument gate
    if active_config and "--config-file" not in given and not (str(active_config).casefold() == "none" and command_writes_config(arguments)):
        paths.extend(("--config-file", str(active_config)))
    # The "none" sentinel is carried so the printed command checks the setup this run checked, except into a
    # command that writes the dotenv file, since those refuse the sentinel at their own argument gate
    if DOTENV_FILE and "--env-file" not in given and not (str(DOTENV_FILE).casefold() == "none" and command_writes_dotenv(arguments)):
        paths.extend(("--env-file", str(DOTENV_FILE)))
    return paths


# The documentation placeholders a printed command carries unquoted, because the reader replaces them before running it
COMMAND_PLACEHOLDERS = frozenset(("<github_target>",))


# Renders one command argument for the shell, leaving a <placeholder> as documentation for the reader to replace
def quote_command_argument(argument, windows=False):
    text = str(argument)
    # Matched exactly rather than by shape, since any other angle-bracket value is user-derived and would otherwise reach the shell unquoted
    if text in COMMAND_PLACEHOLDERS:
        return text
    return subprocess.list2cmdline([text]) if windows else shlex.quote(text)


# Reads only the persisted target from a config file, so a printed command can omit a positional the config already supplies
def config_file_target(config_path):
    if not config_path or str(config_path).casefold() == "none":
        return ""
    namespace = {}
    if not load_config_file(config_path, namespace=namespace, report_errors=False):
        return ""
    return str(namespace.get("TARGET_GITHUB_USERNAME") or "")


# Returns the config a printed command should name, so a run started with discovery off cannot point the reader
# at a file it deliberately ignored
def resolved_command_config(config_path=None):
    # A path the caller was given is what the command names, so a stale discovery flag cannot override it
    if config_path is not None:
        return "none" if str(config_path).casefold() == "none" else config_path
    return "none" if CONFIG_DISCOVERY_DISABLED else find_config_file()


# Returns the targets for the printed doctor and monitoring commands, dropping one the effective config already supplies
def command_targets(explicit_target=None, saved_target=None, placeholder="<github_target>"):
    saved = str(saved_target or "")
    known = str(explicit_target or "") or saved
    if not known:
        # Monitoring cannot run without a target, so it keeps the placeholder while the doctor reports the gap itself
        return None, placeholder
    printed = None if known == saved else known
    return printed, printed


# Renders one install-aware command with platform quoting, carrying the paths this run was given
def render_command(arguments=None, include_paths=True, *, install_context=None, exact=True):
    context = detect_install_context() if install_context is None else install_context
    prefix = context.command_prefix
    if not exact:
        executable = "python" if context.operating_system.casefold() == "windows" else "python3"
        path_class = PureWindowsPath if context.operating_system.casefold() == "windows" else Path
        prefix = (executable, path_class(context.command_prefix[-1]).name) if context.install_method == "manual" else ("github_monitor",)
    selected = [str(argument) for argument in (arguments or ())]
    parts = [*prefix, *selected]
    if include_paths:
        parts.extend(active_path_arguments(selected))
    windows = context.operating_system.casefold() == "windows"
    return " ".join(quote_command_argument(part, windows) for part in parts)


# One sentence for every surface that reports the startup connectivity check
CONNECTIVITY_ENDPOINT_FIX = "Check network, DNS, proxy and CHECK_INTERNET_URL settings"


RECOVERY_CODES = frozenset({
    "auth.github_token_invalid",
    "auth.github_token_missing",
    "config.insecure",
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
    "network.timeout",
    "resource.exhausted",
    "network.unavailable",
    "secret.entry",
    "smtp.authentication",
    "smtp.connection",
    "smtp.delivery",
    "smtp.invalid",
    "target.missing",
    "target.not_found",
    "timezone.invalid",
    "webhook.connection",
    "webhook.invalid",
    "webhook.rate_limited",
    "webhook.rejected",
    "unknown",
})


@dataclass(frozen=True)
class RecoveryAdvice:
    code: str
    summary: str
    fix: str
    retryable: bool
    detail: str = ""


class RecoveryError(Exception):
    # Stores structured recovery advice with the original exception when available
    def __init__(self, advice, cause=None):
        self.advice = advice
        self.cause = cause
        super().__init__(advice.summary)


# Constructs validated recovery advice with every user-facing field sanitized
def make_recovery_advice(code, summary, fix, retryable=False, detail=""):
    if code not in RECOVERY_CODES:
        raise ValueError(f"Unsupported recovery code: {code}")
    return RecoveryAdvice(code, sanitize_error_text(summary), sanitize_error_text(fix), bool(retryable), sanitize_error_text(detail))


# Adds a directly relevant documentation link on its own line
def recovery_fix_with_guide(fix, guide_url):
    return f"{fix}\nGuide: {guide_url}"


# Escapes text for an HTML email body and keeps its line breaks, which HTML would otherwise collapse into spaces
def html_text(text):
    return html.escape(text).replace("\n", "<br>")


# Returns the advice a cancelled secret entry reports, worded the same way by every one-shot secret command
def secret_entry_cancelled_advice(subject, flag, guide_url):
    return make_recovery_advice("secret.entry", f"{subject[:1].upper()}{subject[1:]} setup was cancelled and the dotenv file was not changed", recovery_fix_with_guide(f"Run {flag} again when you have the value ready", guide_url), False)


# Returns the advice a declined secret replacement reports, worded the same way by every one-shot secret command
def secret_replacement_declined_advice(subject, flag, guide_url, plural=False):
    kept = "were left as they are" if plural else "was left as it is"
    return make_recovery_advice("secret.entry", f"The saved {subject} {kept} and the dotenv file was not changed", recovery_fix_with_guide(f"Run {flag} again and answer y to replace the saved value", guide_url), False)


# Renders recovery advice according to the effective diagnostic modes
def render_recovery_advice(advice, debug=None, retry_note="", with_fix=True, label="Error"):
    debug_enabled = DEBUG_MODE if debug is None else bool(debug)
    lines = [f"* {label}: {sanitize_error_text(advice.summary)}" + (f" ({retry_note})" if retry_note else "")]
    if not with_fix:
        return lines[0]
    lines.append(f"To fix: {sanitize_error_text(advice.fix)}")
    # A detail that only repeats the summary spends a line saying nothing
    if debug_enabled and advice.detail and advice.detail != advice.summary:
        lines.append(f"Technical detail: {sanitize_error_text(advice.detail)}")
    return "\n".join(lines)


# Prints one built advice through the shared recovery block and returns it
def print_recovery_advice(advice, debug=None, retry_note="", with_fix=True, label="Error", tracker=None):
    print(render_recovery_advice(advice, debug, retry_note, with_fix and (tracker is None or tracker.should_render(advice)), label))
    return advice


# Classifies one failure and renders it through the shared recovery block
def render_recovery_error(error=None, context="runtime", debug=None, detail="", retry_note="", with_fix=True, label="Error", install_context=None):
    return render_recovery_advice(classify_recovery_error(error, context, detail, install_context), debug, retry_note, with_fix, label)


# Classifies one failure, prints it through the shared recovery block and returns its stable advice
def print_recovery_error(error=None, context="runtime", debug=None, detail="", retry_note="", with_fix=True, label="Error", tracker=None, install_context=None):
    return print_recovery_advice(classify_recovery_error(error, context, detail, install_context), debug, retry_note, with_fix, label, tracker)


# Suppresses a repeated fix paragraph until the failure category changes or a check succeeds
class RecoveryHintTracker:
    # Starts with no category recorded, so the first failure is always reported in full
    def __init__(self):
        self.last_code = None

    # Reports whether this category is new and therefore worth printing the fix for again
    def should_render(self, advice):
        if advice.code == self.last_code:
            return False
        self.last_code = advice.code
        return True

    # Clears the suppression after a successful check
    def reset(self):
        self.last_code = None


# Decides how a lasting failure is reported: in full when it is new, then on the liveness cadence while it lasts
# How long a reported failure may go on before the run reminds about it, whatever the liveness banner is set to
OUTAGE_REMINDER_SECONDS = 3600  # 1 hour


# Returns the family a failure code belongs to, so the DNS and timeout failures of one internet outage count as one
def outage_family(code):
    return "network" if str(code or "").startswith("network.") else str(code or "")


class OutageReporter:
    # Starts with no failure recorded and reports a new retryable failure once confirm_checks checks in a row failed
    def __init__(self, confirm_checks=1):
        self.confirm_checks = max(1, confirm_checks)
        self.code = None
        self.since = 0
        self.reported_at = 0
        self.failures = 0
        self.reported = False

    # Records one failed check and returns "full" when the failure is to be reported in full, "changed" when a
    # reported outage moved to another failure family, "reminder" once OUTAGE_REMINDER_SECONDS passed since the
    # last report or "" while nothing new is to be said
    def failed(self, advice):
        now = int(time.time())
        if not self.code:
            self.since = now
        self.failures += 1
        changed = self.code is not None and outage_family(advice.code) != outage_family(self.code)
        self.code = advice.code
        if not self.reported:
            # A failure the tool cannot retry away is reported at once, one it can waits for the next check to confirm it
            if advice.retryable and self.failures < self.confirm_checks:
                return ""
            self.reported = True
            self.reported_at = now
            return "full"
        if changed:
            self.reported_at = now
            return "changed" if advice.retryable else "full"
        # Timed rather than counted, because a failing run usually retries on a different interval than a healthy one
        if now - self.reported_at >= OUTAGE_REMINDER_SECONDS:
            self.reported_at = now
            return "reminder"
        return ""

    # Clears the failure after a successful check and returns how long it lasted, or None when nothing was reported
    def recovered(self):
        lasted = int(time.time()) - self.since if self.code and self.reported else None
        self.code = None
        self.since = 0
        self.reported_at = 0
        self.failures = 0
        self.reported = False
        return lasted


# Reports that nothing changed, so a quiet run still says it is alive on the liveness cadence
def print_liveness_banner(message):
    print(f"* {sanitize_error_text(message)}")
    print_cur_ts("Liveness check, timestamp:\t")


# Reminds about a lasting failure once an hour, so a broken run still says it is alive without repeating itself
def print_outage_liveness(target, advice, since, failures=0):
    count = f", {failures} failed {'check' if failures == 1 else 'checks'}" if failures else ""
    print(f"* Monitoring degraded for {target}. {advice.summary} since {get_date_from_ts(since)}{count}")
    print_cur_ts("Liveness check, timestamp:\t")


# Notes that a reported outage now fails differently, in one line rather than a second full report
def print_outage_change(target, advice):
    print(f"* Monitoring failure changed for {target}. {advice.summary}")


# Reports that a failure cleared, since a throttled failure no longer stops printing when it is over
def print_outage_recovery(target, lasted):
    print(f"* Monitoring recovered for {target} after {display_time(max(1, lasted))}")
    print_cur_ts("Timestamp:\t\t\t")


# Yields the exception and each cause or context up to max_depth, to walk an exception chain
def iter_exc_chain(error, max_depth=8):
    current = error
    for _ in range(max_depth):
        if current is None:
            return
        yield current
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)


# Reports whether any exception in the chain is the local file descriptor limit rather than a remote failure
def is_too_many_open_files(error):
    for current in iter_exc_chain(error):
        if isinstance(current, OSError) and getattr(current, "errno", None) == 24:
            return True
        message = str(current).lower()
        if "too many open files" in message or re.search(r"\berrno 24\b", message):
            return True
    return False


# Returns the next step for a failure no rule recognized, since a run already printing the technical cause cannot be told to re-run for it
def unknown_failure_fix(debug_command):
    return "Open an issue with this output if the failure continues" if DEBUG_MODE else f"Run the command again with {debug_command} to see the technical cause"


# Maps one exception and operation context to stable recovery advice
def classify_recovery_error(error, context="runtime", detail="", install_context=None):
    if isinstance(error, RecoveryError):
        return error.advice
    selected_context = str(context or "unknown").casefold()
    # The caller knows which step failed, the exception only knows how, so its own text wins when it has one
    detail = str(detail) if detail else f"{type(error).__name__}: {error}"
    token_command = render_command(["--set-github-token"], install_context=install_context)
    webhook_command = render_command(["--set-webhook-url"], install_context=install_context)
    config_command = render_command(["--generate-config", "github_monitor.conf"], install_context=install_context, include_paths=False)
    debug_command = render_command(["--debug"], install_context=install_context)
    # Checked ahead of every context, since a local descriptor limit is not a failure of whatever call hit it
    if error is not None and is_too_many_open_files(error):
        return make_recovery_advice("resource.exhausted", "This process ran out of file descriptors, which is a local limit and not a GitHub problem", recovery_fix_with_guide("Raise the file descriptor limit, for example with 'ulimit -n 4096', or set LimitNOFILE= if you run under systemd, then restart the tool", DEBUG_GUIDE_URL), False, detail)
    if selected_context == "connectivity":
        # Classified from the error, because a failed endpoint check has one answer whatever the exception was
        timed_out = isinstance(error, (req.Timeout, TimeoutError, socket.timeout))
        summary = "The connectivity endpoint did not answer in time" if timed_out else "The connectivity endpoint could not be reached"
        # No guide, because no page covers this check and the doctor report already ends with the troubleshooting link
        return make_recovery_advice("network.timeout" if timed_out else "network.unavailable", summary, CONNECTIVITY_ENDPOINT_FIX, True, detail)
    if isinstance(error, (req.Timeout, TimeoutError, socket.timeout)):
        return make_recovery_advice("network.timeout", "The network request timed out", recovery_fix_with_guide("Check connectivity and increase the configured timeout before trying again", DEBUG_GUIDE_URL), True, detail)
    if isinstance(error, (req.ConnectionError, socket.gaierror)):
        return make_recovery_advice("network.unavailable", "The configured service could not be reached", recovery_fix_with_guide("Check the network and configured service URL then try again", DEBUG_GUIDE_URL), True, detail)
    if isinstance(error, req.RequestException):
        return make_recovery_advice("network.unavailable", "The configured service request failed", recovery_fix_with_guide("Check the network and configured service URL then try again", DEBUG_GUIDE_URL), True, detail)
    if isinstance(error, BadCredentialsException):
        return make_recovery_advice("auth.github_token_invalid", "GitHub rejected the configured token", recovery_fix_with_guide(f"Create or review the token then run: {token_command}", AUTH_GUIDE_URL), False, detail)
    if isinstance(error, RateLimitExceededException):
        return make_recovery_advice("github.rate_limited", "GitHub API rate limiting paused the request", recovery_fix_with_guide("Wait for the reported reset time before trying again", DEBUG_GUIDE_URL), True, detail)
    if isinstance(error, UnknownObjectException):
        code = "target.not_found" if selected_context == "target" else "github.not_found"
        return make_recovery_advice(code, "GitHub could not find the requested resource", recovery_fix_with_guide("Check the target name and token access then try again", DEBUG_GUIDE_URL), False, detail)
    if isinstance(error, GithubException):
        status = getattr(error, "status", None)
        if status == 403:
            return make_recovery_advice("github.forbidden", "GitHub refused access to the requested resource", recovery_fix_with_guide("Check token permissions and resource visibility", AUTH_GUIDE_URL), False, detail)
        retryable = status is None or (isinstance(status, int) and status >= 500)
        return make_recovery_advice("github.api_error", "GitHub returned an API error", recovery_fix_with_guide(f"Try again or run {debug_command} for sanitized technical detail", DEBUG_GUIDE_URL), retryable, detail)
    if isinstance(error, smtplib.SMTPAuthenticationError):
        return make_recovery_advice("smtp.authentication", "The SMTP server rejected the configured credentials", recovery_fix_with_guide("Check SMTP_USER and replace SMTP_PASSWORD before sending another test", SMTP_GUIDE_URL), False, detail)
    if isinstance(error, PermissionError):
        return make_recovery_advice("file.unwritable", "A required file could not be written", recovery_fix_with_guide("Check the destination path and file permissions", CONFIG_GUIDE_URL), False, detail)
    if isinstance(error, FileNotFoundError):
        code = "config.missing" if selected_context == "config" else "dotenv.missing" if selected_context == "dotenv" else "file.unreadable"
        return make_recovery_advice(code, "A required file could not be found", recovery_fix_with_guide("Check the configured path and try again", CONFIG_GUIDE_URL), False, detail)
    if selected_context == "github_token":
        return make_recovery_advice("auth.github_token_invalid", "GitHub token setup could not be completed", recovery_fix_with_guide(f"Correct the problem then run: {token_command}", AUTH_GUIDE_URL), False, detail)
    if selected_context == "webhook":
        return make_recovery_advice("webhook.invalid", "Webhook setup could not be completed", recovery_fix_with_guide(f"Check the HTTPS destination then run: {webhook_command}", WEBHOOK_GUIDE_URL), False, detail)
    if selected_context == "email":
        # A settings problem is reported as itself. Only a failure that actually reached the network is
        # described as one, so an unconfigured mail server is not reported as an unreachable host
        # A server that refused the message is not a server that could not be reached, so the fix names the addresses
        if isinstance(error, (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError)):
            return make_recovery_advice("smtp.delivery", "The mail server refused the message", recovery_fix_with_guide("Check SENDER_EMAIL and RECEIVER_EMAIL, then confirm the server accepts mail from this sender", SMTP_GUIDE_URL), False, detail)
        if isinstance(error, MailConfigurationError):
            return make_recovery_advice("smtp.invalid", sanitize_error_text(error), recovery_fix_with_guide("Set the named settings in the config file, or run --setup, then run the command again", SMTP_GUIDE_URL), False, detail)
        return make_recovery_advice("smtp.connection", "The SMTP server could not be reached", recovery_fix_with_guide("Check SMTP_HOST, SMTP_PORT and SMTP_SSL, then confirm the host is reachable from this machine", SMTP_GUIDE_URL), True, detail)
    if selected_context == "config":
        # The parser already names the line and setting, so the summary carries it instead of only --debug
        reason = sanitize_error_text(error)
        summary = f"The selected configuration is invalid: {reason}" if reason else "The selected configuration is invalid"
        return make_recovery_advice("config.invalid", summary, recovery_fix_with_guide(f"Correct the reported setting, or generate a fresh configuration with: {config_command}", CONFIG_GUIDE_URL), False, detail)
    if selected_context == "timezone":
        return make_recovery_advice("timezone.invalid", "The configured timezone is invalid", recovery_fix_with_guide("Install tzlocal for automatic detection or set a valid pytz timezone", CONFIG_GUIDE_URL), False, detail)
    return make_recovery_advice("unknown", "An unexpected error stopped the requested action", recovery_fix_with_guide(unknown_failure_fix(debug_command), SUPPORT_GUIDE_URL), False, detail)


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


@dataclass(frozen=True)
class StartupSummaryRow:
    label: str
    value: str
    concise: bool = False
    full: bool = True


# Records where one secret resolved from and traces it, so a later layer overwrites the earlier answer instead of adding to it
def record_secret_source(name, source, value=None):
    if source not in SECRET_SOURCE_ORDER:
        raise ValueError(f"Unsupported secret source: {source}")
    resolved = globals().get(name) if value is None else value
    # A placeholder is not a value, so it earns neither a source nor a row
    if not secret_is_set(resolved):
        SECRET_SOURCES.pop(name, None)
        return
    SECRET_SOURCES[name] = source
    debug_print("Secret resolution", name=name, source=source, **secret_fields(resolved))


# Groups every resolved secret name into the four buckets the summary prints, one per source that can supply one
def startup_secret_buckets():
    from_dotenv, from_environment, from_config, from_command_line = [], [], [], []
    for name, source in sorted(SECRET_SOURCES.items()):
        if not secret_is_set(globals().get(name)):
            continue
        if str(source).startswith("dotenv file"):
            from_dotenv.append(name)
        elif source == "environment":
            from_environment.append(name)
        elif source == "command line":
            from_command_line.append(name)
        else:
            from_config.append(name)
    return from_dotenv, from_environment, from_config, from_command_line


# Renders the --help examples: one heading per task, then a comment and the command it describes
def render_help_examples(groups, guide_url):
    blocks = []
    for title, entries in groups:
        block = [f"{title}:"]
        for comment, command in entries:
            if len(block) > 1:
                block.append("")
            block.extend(f"  # {line}" for line in comment.split("\n"))
            if command:
                block.append(f"  {command}")
        blocks.append("\n".join(block))
    return "Examples:\n\n" + "\n\n".join(blocks) + f"\n\nGuide: {guide_url}\n"


# Returns the --help epilog, listing the commands worth knowing rather than every command there is
def help_examples():
    prefix = render_command([], include_paths=False)
    groups = (
        ("Getting started", (
            ("Guided setup, recommended for the first run", f"{prefix} --setup"),
            ("Or save a GitHub token through a hidden prompt", f"{prefix} --set-github-token"),
            ("Check the setup before relying on it", f"{prefix} --doctor <github_target>"),
            ("Start monitoring", f"{prefix} <github_target>"),
        )),
        ("Notifications", (
            ("Email on profile changes and new events", f"{prefix} <github_target> -p -s"),
            ("Send one test email", f"{prefix} --send-test-email"),
            ("Send one test webhook", f"{prefix} --send-test-webhook"),
        )),
        ("Information and diagnostics", (
            ("List the user's repositories with stats", f"{prefix} -r <github_target>"),
            ("Trace what the tool is doing", f"{prefix} <github_target> --debug"),
        )),
    )
    return render_help_examples(groups, QUICK_START_GUIDE_URL)


# Hides the middle of an address's local part, so a log can be shared while the reader can still spot a typo
def mask_email_address(address):
    text = str(address or "").strip()
    local, at_sign, domain = text.partition("@")
    if not at_sign or not local or not domain:
        return text
    masked = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}" if len(local) > 2 else f"{local[0]}{'*' * (len(local) - 1)}"
    return f"{masked}@{domain}"


# Names the mail server this run would use, leaving out the account that signs in to it
def startup_email_transport():
    if not SMTP_HOST or not SMTP_PORT:
        return "Not configured"
    return f"{SMTP_HOST}:{SMTP_PORT} ({'STARTTLS' if SMTP_SSL else 'TLS off'})"


# Names the configured webhook service and whether the channel is switched on, which are two separate settings
def startup_webhook_provider():
    if not normalized_webhook_provider() or not str(WEBHOOK_URL or "").strip():
        return "Not configured"
    return f"{webhook_provider_display_name()} ({'enabled' if WEBHOOK_ENABLED else 'disabled'})"


# Builds concise and complete startup rows without exposing private values
def build_startup_summary(target, config_path, env_path, output_path):
    install_context = detect_install_context()
    email_categories = _startup_email_notification_categories()
    webhook_categories = _startup_webhook_notification_categories()
    email_state = "On (" + ", ".join(email_categories) + ")" if email_categories else "Off"
    webhook_state = "On (" + ", ".join(webhook_categories) + ")" if webhook_categories else "Off"
    from_dotenv, from_environment, from_config, from_command_line = startup_secret_buckets()
    return [
        StartupSummaryRow("Target", str(target), concise=True),
        StartupSummaryRow("Polling interval", display_time(GITHUB_CHECK_INTERVAL), concise=True),
        StartupSummaryRow("Notifications (email)", email_state, concise=True),
        StartupSummaryRow("Email transport", startup_email_transport()),
        StartupSummaryRow("Email recipient", mask_email_address(RECEIVER_EMAIL) if RECEIVER_EMAIL else "Not configured"),
        StartupSummaryRow("Notifications (webhook)", webhook_state, concise=True),
        StartupSummaryRow("Webhook provider", startup_webhook_provider()),
        StartupSummaryRow("Delivery confirmations", str(DELIVERY_CONFIRMATIONS)),
        StartupSummaryRow("Output", str(output_path) if output_path else "Terminal only (logging disabled)", concise=True, full=False),
        StartupSummaryRow("Output logging", str(output_path) if output_path else "Disabled"),
        StartupSummaryRow("Config", str(config_path) if config_path else ("Discovery disabled" if CONFIG_DISCOVERY_DISABLED else "None"), concise=True),
        StartupSummaryRow("Dotenv", str(env_path) if env_path else "None", concise=True),
        StartupSummaryRow("GitHub API URL", str(GITHUB_API_URL)),
        StartupSummaryRow("Track repository changes", str(TRACK_REPOS_CHANGES)),
        StartupSummaryRow("Track contribution changes", str(TRACK_CONTRIB_CHANGES)),
        StartupSummaryRow("Monitor GitHub events", str(not DO_NOT_MONITOR_GITHUB_EVENTS)),
        StartupSummaryRow("Owned repositories only", str(not GET_ALL_REPOS)),
        StartupSummaryRow("Liveness output", display_time(LIVENESS_CHECK_INTERVAL) if LIVENESS_CHECK_INTERVAL else "Disabled", concise=bool(LIVENESS_CHECK_INTERVAL)),
        StartupSummaryRow("CSV output", str(CSV_FILE) if CSV_FILE else "Disabled", concise=bool(CSV_FILE)),
        StartupSummaryRow("Terminal truncation", f"{TRUNCATE_CHARS} chars" if TRUNCATE_CHARS else "Disabled", concise=bool(TRUNCATE_CHARS)),
        StartupSummaryRow("Process id", str(os.getpid())),
        StartupSummaryRow("Python version", platform.python_version()),
        StartupSummaryRow("Operating system", f"{platform.platform(terse=True)} ({platform.machine()})"),
        StartupSummaryRow("Local timezone", str(LOCAL_TIMEZONE)),
        StartupSummaryRow("Install method", install_method_display_name(install_context.install_method)),
        StartupSummaryRow("Secrets from dotenv", ", ".join(from_dotenv) if from_dotenv else "None"),
        StartupSummaryRow("Secrets from environment", ", ".join(from_environment) if from_environment else "None"),
        StartupSummaryRow("Secrets from config file", ", ".join(from_config) if from_config else "None"),
        StartupSummaryRow("Secrets from command line", ", ".join(from_command_line) if from_command_line else "None"),
        StartupSummaryRow("TLS verification", "On" if VERIFY_SSL else "Off, server certificates are not checked", concise=not VERIFY_SSL),
        StartupSummaryRow("ASCII log separators", f"{ascii_log_separators_enabled()} (mode: {ASCII_LOG_SEPARATORS})"),
        StartupSummaryRow("Coloured output", f"{COLOR_ENABLED} (setting: {COLORED_OUTPUT})"),
        StartupSummaryRow("Verbose mode", str(VERBOSE_MODE), concise=bool(VERBOSE_MODE)),
        StartupSummaryRow("Debug mode", str(DEBUG_MODE), concise=bool(DEBUG_MODE)),
        StartupSummaryRow("More details", "use --verbose or --debug", concise=True, full=False),
    ]


# Rows that detail the channel named right above them, indented so the block reads as one setting with its details
STARTUP_SUMMARY_NESTED_LABELS = ("Email transport", "Email recipient", "Email images", "Webhook provider", "ntfy images")


# Formats one startup summary row with aligned plain ASCII columns
def format_startup_summary_row(row):
    indent = "  " if row.label in STARTUP_SUMMARY_NESTED_LABELS else ""
    prefix = f"* {indent}{(row.label + ':'):<{30 - len(indent)}}"
    if row.label in ("Notifications (email)", "Notifications (webhook)"):
        return textwrap.fill(row.value, width=100, initial_indent=prefix, subsequent_indent=" " * len(prefix), break_long_words=False, break_on_hyphens=False) + "\n"
    return f"{prefix}{row.value}\n"


# Routes concise or complete startup rows independently to terminal and log destinations
def emit_startup_summary(rows, show_full, stream=None):
    destination = sys.stdout if stream is None else stream
    log_only = getattr(destination, "log_only", None)
    terminal_only = getattr(destination, "terminal_only", None)
    # A stream that does not split its output has no log file to hold the full view, so those writes go nowhere
    routed = log_only is not None and terminal_only is not None
    write_log = log_only or (lambda line: None)
    write_terminal = terminal_only or destination.write
    for row in rows:
        line = format_startup_summary_row(row)
        if row.full:
            write_log(line)
        if row.full if show_full else row.concise:
            write_terminal(line)
    write_log("\n")
    write_terminal("\n")
    if not routed:
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


# Returns the HTTP status a webhook failure carries, whether it arrived as a response or as an exception holding one
def webhook_failure_status(source: Any) -> Optional[int]:
    status = getattr(source, "status_code", None)
    if not isinstance(status, int):
        status = getattr(getattr(source, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


# Returns the service response body a webhook failure carries, kept for the technical detail line --debug prints
def webhook_failure_detail(source: Any) -> str:
    body = getattr(getattr(source, "response", source), "text", "")
    return str(body)[:200] if isinstance(body, str) else ""


# Maps one webhook configuration or delivery failure to the advice naming the setting or condition to check
def webhook_failure_advice(message: Any, source: Any = None) -> RecoveryAdvice:
    origin = message if source is None else source
    summary = sanitize_webhook_text(message)
    lowered = summary.casefold()
    webhook_command = render_command(["--send-test-webhook"])
    detail = webhook_failure_detail(origin) or summary
    status = webhook_failure_status(origin)
    if status == 429 or "rate limit" in lowered:
        return make_recovery_advice("webhook.rate_limited", "The webhook service is rate limiting deliveries", recovery_fix_with_guide("Reduce how many alert types are enabled, or wait for the service to accept deliveries again", WEBHOOK_GUIDE_URL), True, detail)
    if any(term in lowered for term in ("must contain", "must be discord", "could not be formatted", "header", "priority", "tags")):
        return make_recovery_advice("webhook.invalid", summary or "The webhook configuration is not usable", recovery_fix_with_guide(f"Check WEBHOOK_URL, WEBHOOK_PROVIDER and the alert settings then run: {webhook_command}", WEBHOOK_GUIDE_URL), False, detail)
    if any(term in lowered for term in ("could not be reached", "connection", "timed out", "timeout")):
        return make_recovery_advice("webhook.connection", "The webhook service could not be reached", recovery_fix_with_guide("Check connectivity and the webhook host, then try again", WEBHOOK_GUIDE_URL), True, detail)
    return make_recovery_advice("webhook.rejected", summary or "The webhook service refused the delivery", recovery_fix_with_guide(f"Confirm the webhook still exists and the URL is current then run: {webhook_command}", WEBHOOK_GUIDE_URL), status is not None and status >= 500, detail)


# Reports one webhook configuration or delivery failure through the recovery block, without exposing private values
def print_webhook_error(message: Any, source: Any = None) -> None:
    print_recovery_advice(webhook_failure_advice(message, source))


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
                verbose_delivery_print(f"Webhook delivered through {webhook_provider_display_name(provider)}: '{webhook_values['title']}'")
                debug_print("Webhook delivery", channel=provider, outcome="OK", attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}")
                return 0
            last_error = response
            if not retryable or attempt == WEBHOOK_MAX_ATTEMPTS - 1:
                debug_print("Webhook delivery", channel=provider, outcome="failed", attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}")
                print_webhook_error(f"The webhook service returned HTTP {response.status_code}", response)
                return 1
            delay = webhook_retry_after_seconds(response) if response.status_code == 429 else WEBHOOK_FALLBACK_RETRY_SECONDS
            debug_monitor_wait_timing(f"webhook HTTP {response.status_code} retry attempt {attempt_number + 1}/{WEBHOOK_MAX_ATTEMPTS}", delay)
            sleep_func(delay)
        except req.RequestException as exc:
            last_error = exc
            attempt_number = attempt + 1
            debug_print("Webhook delivery", channel=provider, attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}", outcome="failed", error=f"{type(exc).__name__}: {exc}", retryable=attempt < WEBHOOK_MAX_ATTEMPTS - 1)
            if attempt == WEBHOOK_MAX_ATTEMPTS - 1:
                debug_print("Webhook delivery", channel=provider, outcome="failed", attempt=f"{attempt_number}/{WEBHOOK_MAX_ATTEMPTS}")
                print_webhook_error(exc)
                return 1
            debug_monitor_wait_timing(f"webhook request retry attempt {attempt_number + 1}/{WEBHOOK_MAX_ATTEMPTS}", WEBHOOK_FALLBACK_RETRY_SECONDS)
            sleep_func(WEBHOOK_FALLBACK_RETRY_SECONDS)
    debug_print("Webhook delivery", channel=provider, outcome="failed", after=f"{WEBHOOK_MAX_ATTEMPTS} attempts")
    print_webhook_error("The webhook delivery did not complete", last_error)
    return 1


# Sends one alert through the independently enabled email and webhook channels
def send_notification_channels(notification_type: str, subject: str, body: str, body_html: str = "", email_enabled: bool = False, webhook_enabled: Optional[bool] = None) -> tuple[bool, bool]:
    email_attempted = bool(email_enabled)
    webhook_attempted = webhook_event_enabled(notification_type) if webhook_enabled is None else bool(webhook_enabled)
    email_delivered = False
    webhook_delivered = False
    if email_attempted:
        print(f"Sending email notification to {RECEIVER_EMAIL}")
        email_delivered = send_email(subject, body, body_html, SMTP_SSL) == 0
    if webhook_attempted:
        print(f"Sending webhook notification via {webhook_provider_display_name()}")
        webhook_delivered = send_webhook(subject, body, notification_type, force=True) == 0
    # Delivery, not the attempt, so a channel that failed is retried while one that succeeded is not resent
    return email_delivered, webhook_delivered


# Reports a step that failed and left its output or alerts degraded, naming the step in front of the classified failure
def print_degraded_error(subject, error, label="Error"):
    advice = classify_recovery_error(error)
    print_recovery_advice(make_recovery_advice(advice.code, f"{subject}: {advice.summary}", advice.fix, advice.retryable, advice.detail), label=label)


# Returns the advice an optional library that is missing carries, naming what the run loses and how to install it
def missing_dependency_advice(package, effect, alternative=""):
    return make_recovery_advice("dependency.missing", f"{effect} because the optional '{package}' library is missing", recovery_fix_with_guide(f"Install it with: {shlex.join([sys.executable, '-m', 'pip', 'install', package])}" + (f". {alternative}" if alternative else ""), INSTALL_GUIDE_URL), False)


# Reports a CSV row or header that could not be written, which never stops a monitoring cycle
def print_csv_write_error(error):
    print_recovery_advice(make_recovery_advice("file.unwritable", str(error), recovery_fix_with_guide("Check CSV_FILE and its parent directory permissions", CSV_GUIDE_URL), False, f"{type(error).__name__}: {error}"))


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
    global PENDING_NOTICE_BLOCK, REPORTS_PRINTED
    PENDING_NOTICE_BLOCK = False
    REPORTS_PRINTED += 1
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


TIMEZONE_CHECK_LABELS = {"config": "Local timezone is valid", "auto": "Local timezone can be detected", "auto_unavailable": "Automatic timezone detection is unavailable", "auto_failed": "Automatic timezone detection failed", "invalid": "Local timezone is invalid"}


# Resolves LOCAL_TIMEZONE and the state doctor reports it with, returning advice when no zone could be determined
def resolve_local_timezone():
    global LOCAL_TIMEZONE, LOCAL_TIMEZONE_STATE

    LOCAL_TIMEZONE_STATE = "config"
    timezone_advice = None
    local_tz = None
    if LOCAL_TIMEZONE == "Auto":
        if get_localzone is not None:
            try:
                local_tz = get_localzone()
            except Exception as exc:
                debug_swallowed_exception("Local timezone detection", exc)
        if local_tz and is_valid_timezone(str(local_tz)):
            LOCAL_TIMEZONE = str(local_tz)
            LOCAL_TIMEZONE_STATE = "auto"
        elif get_localzone is None:
            LOCAL_TIMEZONE_STATE = "auto_unavailable"
            timezone_advice = make_recovery_advice("timezone.invalid", "The local timezone could not be detected", recovery_fix_with_guide("Install tzlocal for automatic detection or set LOCAL_TIMEZONE to a valid pytz timezone", CONFIG_GUIDE_URL), False, "LOCAL_TIMEZONE is Auto but tzlocal is unavailable")
        else:
            LOCAL_TIMEZONE_STATE = "auto_failed"
            timezone_advice = make_recovery_advice("timezone.invalid", "The local timezone could not be detected", recovery_fix_with_guide("Set LOCAL_TIMEZONE to a valid pytz timezone", CONFIG_GUIDE_URL), False, "tzlocal did not return a supported timezone")
    elif not is_valid_timezone(LOCAL_TIMEZONE):
        LOCAL_TIMEZONE_STATE = "invalid"
        timezone_advice = make_recovery_advice("timezone.invalid", f"Configured LOCAL_TIMEZONE '{LOCAL_TIMEZONE}' is not valid", recovery_fix_with_guide("Set LOCAL_TIMEZONE to a valid pytz timezone name", CONFIG_GUIDE_URL), False, f"Time zone: {LOCAL_TIMEZONE}")
    return timezone_advice


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
            print_recovery_advice(missing_dependency_advice("python-dotenv", "The env-var reload was skipped"), label="Warning")
        except Exception as exc:
            env_path = None
            verbose_degraded_feature("Private setting reload", "credential refresh", exc)
            print_degraded_error("The dotenv reload failed", exc)

    github_token_changed = False
    webhook_url_changed = False
    if env_path:
        for secret in SECRET_KEYS:
            old_val = globals().get(secret)
            val = os.getenv(secret)
            if val is not None and val != old_val:
                globals()[secret] = val
                # A placeholder written back into the dotenv file clears the secret rather than becoming one
                if secret_is_set(val):
                    record_secret_source(secret, "dotenv file reload", val)
                else:
                    # A cleared secret is a change the trace has to show, which the recorder stays silent about
                    SECRET_SOURCES.pop(secret, None)
                    debug_print("Secret resolution", name=secret, source="nowhere", **secret_fields(val))
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
            print(f"* Updated webhook provider to {webhook_provider_display_name(detected_provider)}")

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
# Retries a GitHub operation with current settings and either returns its fallback or raises the final failure
def gh_call(fn: Callable[..., Any], retries=None, backoff=None, default: Any = None, *, raise_on_failure=False) -> Callable[..., Any]:
    retries = NET_MAX_RETRIES if retries is None else retries
    backoff = NET_BASE_BACKOFF_SEC if backoff is None else backoff
    # Keeps the original exception available to callers that must distinguish an unavailable feed from an empty one
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        last_error = None
        for i in range(1, retries + 1):
            try:
                debug_print("PyGithub retry wrapper", operation=fn.__name__, attempt=f"{i}/{retries}")
                result = fn(*args, **kwargs)
                debug_print("PyGithub retry wrapper", operation=fn.__name__, outcome="OK", attempt=f"{i}/{retries}")
                return result
            except RateLimitExceededException as e:
                last_error = e
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
                last_error = e
                retryable = i < retries
                delay = backoff * i
                debug_print("PyGithub retry wrapper", operation=fn.__name__, outcome="failed", error=f"{type(e).__name__}: {e}", retryable=retryable, attempt=f"{i}/{retries}")
                if retryable:
                    print(f"* {fn.__name__} error: {sanitize_error_text(e)} (retry {i}/{retries})")
                    debug_monitor_wait_timing(f"GitHub request retry attempt {i + 1}/{retries}", delay)
                    time.sleep(delay)
        verbose_degraded_feature(f"GitHub operation {fn.__name__}", "its dependent alerts")
        if raise_on_failure and last_error is not None:
            raise last_error
        debug_print("PyGithub retry wrapper", operation=fn.__name__, outcome="default", after=f"{retries} attempts")
        return default
    return wrapped


# Returns True when the login still resolves to a GitHub account, False when it does not and None when the check fails
def github_account_exists(login):
    try:
        g = create_github_client("account existence check")
        debug_github_operation("account existence check", login)
        g.get_user(login)
        return True
    except UnknownObjectException:
        return False
    except Exception as e:
        debug_print("PyGithub", operation="account existence check", outcome="failed", error=f"{type(e).__name__}: {e}", target=login)
        return None


# Returns True when the owner/repo path still resolves to a repository, False when it does not and None when the check fails
def github_repo_exists(full_name):
    try:
        g = create_github_client("repository existence check")
        debug_github_operation("repository existence check", full_name)
        g.get_repo(full_name)
        return True
    except UnknownObjectException:
        return False
    except Exception as e:
        debug_print("PyGithub", operation="repository existence check", outcome="failed", error=f"{type(e).__name__}: {e}", target=full_name)
        return None


# Builds a bracketed note when a removed list item vanished because its account or repository is gone, empty otherwise
def removed_item_note(label, item, user=None):
    label_lower = label.lower()
    if label_lower in ("stargazers", "watchers", "followers", "followings"):
        if github_account_exists(item) is False:
            return " (account no longer exists)"
    elif label_lower == "forks":
        if github_account_exists(item.split("/", 1)[0]) is False:
            return " (owner account no longer exists)"
    elif label_lower == "starred repos":
        if github_repo_exists(item) is False:
            return " (repository no longer exists)"
    elif label_lower == "repos" and user:
        if github_repo_exists(f"{user}/{item}") is False:
            return " (repository no longer exists)"
    return ""


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
        print_degraded_error("The follower list could not be read", e)

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
        print_degraded_error("The following list could not be read", e)

    g.close()


# The width of the progress line drawn last, so the next one pads over whatever the previous one left on screen
_progress_line_width = 0


# Displays a progress bar with percentage and current repo name
def _display_progress(current, total, repo_name: str = "", bar_length: int = 40, is_final: bool = False) -> None:
    global _progress_line_width

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
    padded_progress = progress_str + (" " * max(0, _progress_line_width - len(progress_str)))
    _progress_line_width = len(progress_str)

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
                    print()
                    print_degraded_error(f"Discussions for repo '{repo.name}' were skipped", e)
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
                    print()
                    print_degraded_error(f"Repo '{repo.name}' was skipped", e)
                    print_cur_ts("Timestamp:\t\t\t")
                    if show_progress:
                        _display_progress(idx, total_repos, repo.name, is_final=(idx == total_repos))
                    continue
            except Exception as e:
                verbose_degraded_feature(f"Repository details for {repo.name}", "repository change alerts", e)
                print()
                print_degraded_error(f"Repo '{repo.name}' was skipped", e)
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
        print_csv_write_error(e)

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
        print_degraded_error("The user details could not be read", e)
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
                        print()
                        print_degraded_error("Some event details are missing", e, label="Warning")
                        print_cur_ts("\nTimestamp:\t\t\t")
                        continue
                    try:
                        if csv_file_name:
                            write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                    except Exception as e:
                        print_csv_write_error(e)
                    print_cur_ts("\nTimestamp:\t\t\t")
        except Exception as e:
            verbose_degraded_feature("Recent event iteration", "recent event output", e)
            print_degraded_error("The event list could not be read", e)


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
        print_degraded_error(f"The list of {label.lower()} could not be refreshed", e)
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
            print_csv_write_error(e)

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

            note = removed_item_note(label, item, user)
            print(f"- {item} [ {item_url} ]{note}")
            removed_list_str += f"- {item} [ {item_url} ]{note}\n"
            removed_list_str_html += f"- <a href=\"{html.escape(item_url)}\">{html.escape(item)}</a>{html.escape(note)}<br>"
            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), f"Removed {label[:-1]}", user, item, "")
            except Exception as e:
                print_csv_write_error(e)
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
                print_csv_write_error(e)
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
            print_csv_write_error(e)

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
            print_csv_write_error(e)

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
                note = removed_item_note(label, item)
                item_line = f"- {item} [ {github_web_base()}/{item}/ ]{note}" if label.lower() in ["stargazers", "watchers", "forks"] else f"- {item}"
                print(item_line)
                removed_list_str += item_line + "\n"

                if label.lower() in ["stargazers", "watchers", "forks"]:
                    item_url = f"{github_web_base()}/{item}/"
                    removed_list_str_html += f"- <a href=\"{html.escape(item_url)}\">{html.escape(item)}</a>{html.escape(note)}<br>"
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
                    print_csv_write_error(e)
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
                    print_csv_write_error(e)
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


# Keeps argparse from colouring its own help, so the help screen is coloured by this tool alone and --no-color is
# not left with a second palette to silence. From Python 3.14 argparse colours the help by default on a terminal
def argparse_color_kwargs() -> dict[str, Any]:
    return {"color": False} if sys.version_info >= (3, 14) else {}


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
    global CLEAR_SCREEN, COLORED_OUTPUT, COLOR_THEME
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
    # --help is printed and exited from inside argparse, long before the config load, so the help_* overrides
    # have to be here or they could never colour the one screen they name. Unusable styles are dropped downstream
    if isinstance(values.get("COLOR_THEME"), dict):
        COLOR_THEME = values["COLOR_THEME"]


# Settings an older version wrote that this version no longer defines, ignored instead of rejected
RETIRED_CONFIG_SETTINGS = frozenset(())

# Settings the template ships commented out so the built-in default applies, still accepted from a config file
COMMENTED_CONFIG_SETTINGS = frozenset({"COLOR_THEME"})


# Collects the setting names the built-in configuration template defines
def _config_allowed_names():
    template_tree = ast.parse(CONFIG_BLOCK, "<built-in-config>", "exec")
    return frozenset(statement.targets[0].id for statement in template_tree.body if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name)) | COMMENTED_CONFIG_SETTINGS


# Returns the literal values the built-in config template ships with, used to clear a section the user declined
def _config_template_defaults():
    template_tree = ast.parse(CONFIG_BLOCK, "<built-in-config>", "exec")
    defaults = {}
    for statement in template_tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            continue
        try:
            defaults[statement.targets[0].id] = ast.literal_eval(statement.value)
        except ValueError:
            continue
    return defaults


# Returns the parsed value with a legacy numeric on/off setting read as the boolean it stands for
def _normalized_config_value(name, value, defaults):
    # 0 and 1 were accepted for these settings before the values were checked, so they still mean off and on
    if isinstance(value, int) and not isinstance(value, bool) and value in (0, 1) and isinstance(defaults.get(name), bool):
        return bool(value)
    return value


# Parses allowlisted literal config assignments without executing any file content
def parse_config_content(content, filename="<config>", retired_out=None, reference_values=None):
    tree = ast.parse(content, filename, "exec")
    allowed_names = _config_allowed_names()
    template_defaults = _config_template_defaults()
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
            parsed_values[name] = _normalized_config_value(name, ast.literal_eval(statement.value), template_defaults)
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
        config_command = render_command(["--generate-config", "github_monitor.conf"], include_paths=False)
        advice = make_recovery_advice("config.invalid", detail, recovery_fix_with_guide(f"Keep only documented SETTING = value lines with plain literal values or regenerate with: {config_command}", CONFIG_GUIDE_URL), False, detail)
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
    # An empty export is a shell-profile leftover rather than a value, so it is dropped before the dotenv load,
    # which would otherwise keep it and leave the file's value unused
    for secret in SECRET_KEYS:
        if os.environ.get(secret) == "":
            os.environ.pop(secret)
    environment_values = {secret: os.environ[secret] for secret in SECRET_KEYS if os.environ.get(secret)}
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
                advice = missing_dependency_advice("python-dotenv", f"The dotenv file '{env_path}' was not loaded", "Or export the secrets as environment variables")
                if errors_out is not None:
                    errors_out.append(advice.summary)
                if report_errors:
                    print_recovery_advice(advice, label="Warning")
        except Exception as exc:
            env_path = DOTENV_FILE if DOTENV_FILE else None
            verbose_degraded_feature("Dotenv loading", "dotenv-based private settings", exc)
            advice = make_recovery_advice("file.unreadable", "The dotenv file could not be read", recovery_fix_with_guide("Check DOTENV_FILE and its permissions or disable it with --env-file none", CONFIG_GUIDE_URL), False, f"{type(exc).__name__}: {exc}")
            if errors_out is not None:
                errors_out.append(advice.summary + f": {advice.detail}")
            if report_errors:
                print_recovery_advice(advice)

    SECRET_SOURCES = {}
    for secret in SECRET_KEYS:
        value = os.getenv(secret)
        if value is not None:
            globals()[secret] = value
        # An unedited placeholder is not a configured secret, whichever layer it arrived from
        if not secret_is_set(globals().get(secret)):
            continue
        if secret in environment_values:
            source = "environment"
        elif secret in dotenv_keys and value is not None:
            source = "dotenv file"
        elif secret in configured_names:
            source = "configuration file"
        else:
            source = "built-in configuration"
        record_secret_source(secret, source)
    return env_path


# Reports that no layer supplied a secret, called once the command line has had its say so the answer is final
def trace_unresolved_secrets():
    if not SECRET_SOURCES:
        debug_print("No private settings were resolved from config, dotenv, environment or the command line")


# Applies startup CLI overrides before any check consumes effective configuration
def apply_startup_cli_overrides(args, configured_settings=None):
    global GITHUB_TOKEN, GITHUB_API_URL, CHECK_INTERNET_URL, SECRET_SOURCES
    configured_names = set(configured_settings or ())
    previous_api_url = GITHUB_API_URL
    connectivity_follows_api = "CHECK_INTERNET_URL" not in configured_names or CHECK_INTERNET_URL == previous_api_url
    if args.github_token is not None:
        GITHUB_TOKEN = args.github_token
        record_secret_source("GITHUB_TOKEN", "command line")
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
    # A line break inside a value would split the assignment, so it is escaped rather than written through
    escaped = value.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34)).replace("\r", "\\r").replace("\n", "\\n")
    return f'{prefix}{key}="{escaped}"'


# Returns whether one dotenv file already assigns the requested key
def _dotenv_contains_key(path: Path, key: str) -> bool:
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
    return any(binding.key == key for binding in _dotenv_bindings(content))


# Returns the dotenv parser's own bindings for one file's text, where a quoted value written across several lines is one binding
def _dotenv_bindings(text):
    from io import StringIO
    from dotenv.parser import parse_stream
    return list(parse_stream(StringIO(text)))


# Rewrites complete dotenv bindings while preserving unrelated content
def render_private_settings(existing, updates):
    output_parts = []
    replaced = set()
    # Rebuilt from the parser's own bindings rather than physical lines, since a quoted value can span several
    # of them and replacing only the first leaves the rest of the old secret behind as broken syntax
    for binding in _dotenv_bindings(existing):
        original = binding.original.string
        blank_prefix = original[:len(original) - len(original.lstrip("\r\n"))]
        if binding.key is None or binding.key not in updates:
            output_parts.append(original)
            continue
        # A secret cleared by its owner is removed rather than emptied, so a disabled value cannot linger here
        if binding.key in replaced or not updates[binding.key]:
            output_parts.append(blank_prefix)
            replaced.add(binding.key)
            continue
        replaced.add(binding.key)
        # An already exported assignment is rewritten in place. Appending a second one would leave the old
        # credential on disk, with only the load order deciding which one wins
        head = original[len(blank_prefix):]
        # Keep key quotes out of the indentation and export prefix
        written_prefix = head[:head.index(binding.key)].rstrip("'")
        output_parts.append(f"{blank_prefix}{render_dotenv_assignment(binding.key, updates[binding.key], written_prefix)}\n")
    content = "".join(output_parts)
    # A file that did not end in a newline would otherwise take the first new assignment onto its last line
    if content and not content.endswith("\n"):
        content += "\n"
    for key, value in updates.items():
        if key not in replaced and value:
            content += f"{render_dotenv_assignment(key, value)}\n"
    # Checked before it replaces the file, so a rewrite can never publish a secret the next run cannot read back
    rewritten = {binding.key: binding.value for binding in _dotenv_bindings(content) if binding.key is not None}
    if any(rewritten.get(key, "") != value for key, value in updates.items()):
        raise ValueError("The dotenv update would not store the requested values")
    return content


# Atomically replaces dotenv assignments with owner-only permissions while preserving unrelated lines
def update_dotenv_file(destination, updates):
    if not hasattr(updates, "items"):
        raise TypeError("Dotenv updates must be a mapping")
    path = Path(destination).expanduser()
    for key, value in updates.items():
        if key not in SECRET_KEYS:
            raise ValueError(f"Refusing to write an unknown dotenv key: {key}")
        if not isinstance(value, str):
            raise TypeError(f"Dotenv value for {key} must be a string")
    if not path.parent.is_dir():
        raise FileNotFoundError(f"Dotenv parent directory does not exist: {path.parent}")
    debug_print("Reading private settings file before update", path=path, exists=path.exists())
    try:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
    except Exception as exc:
        debug_print("Private settings file read", path=path, outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    content = render_private_settings(existing, updates)
    temporary_path = None
    try:
        # Follow an existing symlink as the original writer did, then replace only its target after the write succeeds
        target = path.resolve()
        temporary_path = prepare_wizard_atomic_file(target, content)
        os.replace(temporary_path, target)
    except Exception as exc:
        debug_print("Private settings file update", path=path, outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    debug_print("Private settings file update succeeded", path=path, mode="0600")
    for key, value in updates.items():
        verbose_print(f"{'Saved' if value else 'Removed'} {key} in the private settings file")
    return {"path": str(path), "updated_keys": tuple(updates)}


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
    if _dotenv_contains_key(destination, "GITHUB_TOKEN"):
        try:
            confirmed = read_interactively(prompt, f"Replace the saved GitHub token in '{destination}'? [y/N]: ").strip().casefold() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            print()
            raise RecoveryError(secret_entry_cancelled_advice("GitHub token", "--set-github-token", AUTH_GUIDE_URL)) from None
        if not confirmed:
            raise RecoveryError(secret_replacement_declined_advice("GitHub token", "--set-github-token", AUTH_GUIDE_URL))
    print(colorize_links("* Create or review GitHub tokens at: https://github.com/settings/tokens"))
    hidden_prompt = getpass.getpass if getpass_func is None else getpass_func
    previous_debug_mode = DEBUG_MODE
    DEBUG_MODE = False
    try:
        token = read_interactively(hidden_prompt, "Enter GitHub token privately: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise RecoveryError(secret_entry_cancelled_advice("GitHub token", "--set-github-token", AUTH_GUIDE_URL)) from None
    finally:
        DEBUG_MODE = previous_debug_mode
    print("* Checking the entered GitHub token before changing the dotenv file ...")
    login = validate_github_token(token, api_url=api_url)
    try:
        update_dotenv_file(destination, {"GITHUB_TOKEN": token})
    except Exception as exc:
        debug_print("Private settings file update", path=destination, key="GITHUB_TOKEN", outcome="failed", error=f"{type(exc).__name__}: {exc}")
        raise GitHubTokenConfigurationError(f"Could not save GITHUB_TOKEN in '{destination}'. Check the path and file permissions") from None
    paths = []
    if config_path or CONFIG_DISCOVERY_DISABLED:
        paths.extend(("--config-file", str(resolved_command_config(config_path))))
    paths.extend(("--env-file", str(destination)))
    if api_url is not None:
        paths.extend(("--github-url", str(api_url)))
    print(f"* GitHub token validation succeeded for user: {login}")
    print(f"* Updated private settings file: {destination}")
    print()
    doctor_target, monitor_target = command_targets(None, config_file_target(resolved_command_config(config_path)))
    _wizard_print_command(sys.stdout, "Check setup again:", render_command(["--doctor"] + ([doctor_target] if doctor_target else []) + paths, install_context=install_context))
    _wizard_print_command(sys.stdout, "After Doctor passes, start monitoring:", render_command(([monitor_target] if monitor_target else []) + paths, install_context=install_context))
    return str(destination)


# Checks and safely stores one privately entered webhook URL
def run_set_webhook_url(env_file=None, interactive=None, input_func=None, getpass_func=None, config_path=None, install_context=None) -> str:
    global DEBUG_MODE
    destination = resolve_secret_env_path(env_file, "--set-webhook-url")
    terminal_is_interactive = sys.stdin.isatty() if interactive is None else interactive
    if not terminal_is_interactive:
        raise ValueError("--set-webhook-url requires an interactive terminal so the webhook URL stays hidden")
    prompt = input if input_func is None else input_func
    if _dotenv_contains_key(destination, "WEBHOOK_URL"):
        try:
            confirmed = read_interactively(prompt, f"Replace the saved webhook URL in '{destination}'? [y/N]: ").strip().casefold() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            print()
            raise RecoveryError(secret_entry_cancelled_advice("webhook URL", "--set-webhook-url", WEBHOOK_GUIDE_URL)) from None
        if not confirmed:
            raise RecoveryError(secret_replacement_declined_advice("webhook URL", "--set-webhook-url", WEBHOOK_GUIDE_URL))
    hidden_prompt = getpass.getpass if getpass_func is None else getpass_func
    previous_debug_mode = DEBUG_MODE
    DEBUG_MODE = False
    try:
        webhook_url = read_interactively(hidden_prompt, "Paste the Discord or ntfy webhook URL (input hidden): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise RecoveryError(secret_entry_cancelled_advice("webhook URL", "--set-webhook-url", WEBHOOK_GUIDE_URL)) from None
    finally:
        DEBUG_MODE = previous_debug_mode
    if not validate_webhook_url(webhook_url):
        raise ValueError("That does not look like a complete HTTPS webhook URL and the dotenv file was not changed")
    update_dotenv_file(destination, {"WEBHOOK_URL": webhook_url})
    paths = []
    if config_path or CONFIG_DISCOVERY_DISABLED:
        paths.extend(("--config-file", str(resolved_command_config(config_path))))
    paths.extend(("--env-file", str(destination)))
    print("* Webhook URL looks valid")
    print(f"* Updated private settings file: {destination}")
    print()
    _wizard_print_command(sys.stdout, "Send a test webhook:", render_command(["--send-test-webhook"] + paths, install_context=install_context))
    _wizard_print_command(sys.stdout, "Check setup again:", render_command(["--doctor"] + paths, install_context=install_context))
    return str(destination)


# Represents a mail server that is not configured well enough for a password to be checked against it
class MailConfigurationError(ValueError):
    pass


# The settings a sign-in needs before a password can be checked against the mail server
MAIL_SIGN_IN_SETTINGS = ("SMTP_HOST", "SMTP_USER", "SENDER_EMAIL", "RECEIVER_EMAIL")


# Returns the mail settings a sign-in needs that are still empty or still hold their shipped placeholder
def mail_sign_in_settings_missing():
    return [name for name in MAIL_SIGN_IN_SETTINGS if not secret_is_set(str(globals().get(name) or ""))]


# Joins setting names into the phrase a message reads out, for example "SMTP_HOST and SMTP_USER"
def join_setting_names(names, conjunction):
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} {conjunction} {names[-1]}"


# Signs in while removing the attempted password from SMTP rejection replies before they can be rendered
def smtp_login(connection, username, password):
    try:
        return connection.login(username, password)
    except smtplib.SMTPResponseException as error:
        reply = error.smtp_error
        if password:
            if isinstance(reply, bytes):
                reply = reply.replace(str(password).encode("utf-8"), b"<redacted>")
            else:
                reply = str(reply).replace(str(password), "<redacted>")
        error.smtp_error = reply
        error.args = (error.smtp_code, reply)
        raise


# Signs in to the configured mail server with one entered password, so nothing is saved that cannot deliver
def smtp_sign_in(password, timeout=5):
    global SMTP_PASSWORD

    candidate = str(password or "")
    if not candidate or candidate == "your_smtp_password":
        raise ValueError("No SMTP password was entered and the dotenv file was not changed")
    settings_problem = wizard_email_settings_error({name: globals()[name] for name in WIZARD_SMTP_CONFIG_KEYS}, {"SMTP_PASSWORD": candidate})
    if settings_problem:
        raise ValueError(f"The mail server settings are incomplete: {settings_problem}")
    previous_password = SMTP_PASSWORD
    SMTP_PASSWORD = candidate
    smtp_object = None
    try:
        smtp_object = smtp_connect_and_login(SMTP_SSL, smtp_timeout=timeout)
    finally:
        if smtp_object is not None:
            smtp_quit_quietly(smtp_object)
        SMTP_PASSWORD = previous_password
    return str(SMTP_USER)


# Privately checks one SMTP password against the mail server and atomically stores it
def run_set_smtp_password(env_file=None, interactive=None, input_func=None, getpass_func=None, config_path=None, install_context=None, sign_in=None) -> str:
    global DEBUG_MODE
    destination = resolve_secret_env_path(env_file, "--set-smtp-password")
    terminal_is_interactive = sys.stdin.isatty() if interactive is None else interactive
    if not terminal_is_interactive:
        raise ValueError("--set-smtp-password requires an interactive terminal so the password stays hidden")
    # Checked before the prompts, so nobody types a password only to be told the mail server was never configured
    missing = mail_sign_in_settings_missing()
    if missing:
        names = join_setting_names(missing, "and")
        raise MailConfigurationError(f"The mail server settings are incomplete, {names} {'is' if len(missing) == 1 else 'are'} not set")
    prompt = input if input_func is None else input_func
    if _dotenv_contains_key(destination, "SMTP_PASSWORD"):
        try:
            confirmed = read_interactively(prompt, f"Replace the saved SMTP password in '{destination}'? [y/N]: ").strip().casefold() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            print()
            raise RecoveryError(secret_entry_cancelled_advice("SMTP password", "--set-smtp-password", SMTP_GUIDE_URL)) from None
        if not confirmed:
            raise RecoveryError(secret_replacement_declined_advice("SMTP password", "--set-smtp-password", SMTP_GUIDE_URL))
    print(f"* The password is checked by signing in to {SMTP_HOST} as {SMTP_USER}. Nothing is sent")
    hidden_prompt = getpass.getpass if getpass_func is None else getpass_func
    previous_debug_mode = DEBUG_MODE
    DEBUG_MODE = False
    try:
        smtp_password = str(read_interactively(hidden_prompt, "Enter the SMTP password (input hidden): ")).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise RecoveryError(secret_entry_cancelled_advice("SMTP password", "--set-smtp-password", SMTP_GUIDE_URL)) from None
    finally:
        DEBUG_MODE = previous_debug_mode
    check = smtp_sign_in if sign_in is None else sign_in
    try:
        signed_in_user = check(smtp_password, timeout=WIZARD_SMTP_TIMEOUT)
    except RecoveryError:
        raise
    except Exception as exc:
        # The sign-in restores the previous password before the failure reaches here, so the value that was tried
        # is passed to the redaction explicitly rather than left to the global it would otherwise read
        raise RecoveryError(classify_recovery_error(exc, context="email", detail=sanitize_error_text(exc, (smtp_password,)), install_context=install_context), exc) from None
    update_dotenv_file(destination, {"SMTP_PASSWORD": smtp_password})
    paths = []
    if config_path or CONFIG_DISCOVERY_DISABLED:
        paths.extend(("--config-file", str(resolved_command_config(config_path))))
    paths.extend(("--env-file", str(destination)))
    print(f"* The mail server accepted the password for {signed_in_user}")
    print(f"* Updated private settings file: {destination}")
    print()
    _wizard_print_command(sys.stdout, "Send a test email:", render_command(["--send-test-email"] + paths, install_context=install_context))
    _wizard_print_command(sys.stdout, "Check setup again:", render_command(["--doctor"] + paths, install_context=install_context))
    return str(destination)


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

    mark_monitoring_started()

    try:
        if csv_file_name:
            init_csv_file(csv_file_name)
    except Exception as e:
        print_csv_write_error(e)

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
        print()
        print_recovery_error(e, detail=f"Reading the event feed of '{user}' failed: {e}")
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
                print()
                print_degraded_error("The event identifiers could not be read", e)
                print()

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
            print_degraded_error("The public repository list could not be processed", e)
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
                print()
                print_degraded_error("The last event details could not be read", e, label="Warning")

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
        print_recovery_error(e, detail=f"Reading the initial profile snapshot of '{user}' failed: {e}")
        sys.exit(1)

    verbose_notice(f"Initial snapshot completed for {user}")
    # The snapshot names its features differently from the checks, so its outages are not carried into the loop
    reset_degraded_features()
    debug_monitor_wait_timing("initial monitoring interval", GITHUB_CHECK_INTERVAL)
    time.sleep(GITHUB_CHECK_INTERVAL)
    alive_since = int(time.time())
    # The error alert is tracked once per channel and per outage
    error_alert = ErrorAlertState()
    monitor_recovery_tracker = RecoveryHintTracker()
    outage = OutageReporter()
    profile_field_unavailable = object()
    check_number = 0

    # Primary loop
    while True:
        check_number += 1
        reports_before_check = REPORTS_PRINTED
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
            error_alert.reset()
            monitor_recovery_tracker.reset()
            outage_lasted = outage.recovered()
            if outage_lasted is not None:
                print_outage_recovery(user, outage_lasted)

        except (GithubException, Exception) as e:
            verbose_degraded_feature("Monitored user refresh", "all profile, repository and event alerts", e)
            advice = classify_recovery_error(e, "target")

            # A failure that has not changed is left to the liveness cadence rather than repeated every check
            outage_outcome = outage.failed(advice)
            delivery_reported = False
            if outage_outcome == "full":
                print_recovery_advice(advice, tracker=monitor_recovery_tracker, retry_note=f"retrying in {display_time(GITHUB_CHECK_INTERVAL)}")
            elif outage_outcome == "changed":
                print_outage_change(user, advice)
            elif outage_outcome == "reminder":
                print_outage_liveness(user, advice, outage.since, outage.failures)

            m_subject = f"github_monitor: {advice.summary} (user: {user})"
            m_body = f"{advice.summary}\n\nTo fix: {advice.fix}\n\nGitHub Monitor will retry in {display_time(GITHUB_CHECK_INTERVAL)}.{get_cur_ts(nl_ch + nl_ch + 'Timestamp: ')}"
            m_body_html = f"<html><head></head><body><b>{html_text(advice.summary)}</b><br><br>To fix: {html_text(advice.fix)}<br><br>GitHub Monitor will retry in {html.escape(display_time(GITHUB_CHECK_INTERVAL))}.{get_cur_ts('<br><br>Timestamp: ')}</body></html>"
            # Attempted on every failing check rather than only on the report, so a channel that failed is tried again
            # A failure the tool can retry away is alerted once the outage has lasted ERROR_ALERT_AFTER_SECONDS, one it cannot at once
            alert_due = not advice.retryable or int(time.time()) - outage.since >= ERROR_ALERT_AFTER_SECONDS
            now = int(time.time())
            error_email_pending = alert_due and error_alert.pending("email", ERROR_NOTIFICATION, now)
            error_webhook_pending = alert_due and error_alert.pending("webhook", webhook_event_enabled("error"), now)
            if error_email_pending or error_webhook_pending:
                email_delivered, webhook_delivered = send_notification_channels("error", m_subject, m_body, m_body_html, error_email_pending, error_webhook_pending)
                error_alert.record("email", error_email_pending, email_delivered, now)
                error_alert.record("webhook", error_webhook_pending, webhook_delivered, now)
                delivery_reported = True

            # A retry can reach the screen on a check the outage reporter keeps quiet, and a delivery line
            # with nothing under it reads as a run that stopped there
            if outage_outcome in ("full", "changed") or delivery_reported:
                print_cur_ts("Timestamp:\t\t\t")
            debug_print("Completed monitoring check", check=f"#{check_number}", user=user, outcome="failed", code=advice.code, error=f"{type(e).__name__}: {e}")
            debug_monitor_wait_timing("monitored user refresh failure", GITHUB_CHECK_INTERVAL)
            time.sleep(GITHUB_CHECK_INTERVAL)
            continue

        # Changed followings
        try:
            debug_github_operation("followings refresh", user)
            followings_raw = gh_call(lambda: list(g_user.get_following()), raise_on_failure=True)()  # noqa: B023
            followings_count = gh_call(lambda: g_user.following)()  # noqa: B023
        except NET_ERRORS as e:
            verbose_degraded_feature("Followings", "following change alerts", e)
            print_degraded_error("Followings could not be refreshed", e)
            print_cur_ts("Timestamp:\t\t\t")
            followings_raw = None
            followings_count = None

        if followings_raw is not None and followings_count is not None:
            followings_old, followings_old_count = handle_profile_change("Followings", followings_old_count, followings_count, followings_old, followings_raw, user, csv_file_name, field="login")

        # Changed followers
        try:
            debug_github_operation("followers refresh", user)
            followers_raw = gh_call(lambda: list(g_user.get_followers()), raise_on_failure=True)()  # noqa: B023
            followers_count = gh_call(lambda: g_user.followers)()  # noqa: B023
        except NET_ERRORS as e:
            verbose_degraded_feature("Followers", "follower change alerts", e)
            print_degraded_error("Followers could not be refreshed", e)
            print_cur_ts("Timestamp:\t\t\t")
            followers_raw = None
            followers_count = None

        if followers_raw is not None and followers_count is not None:
            followers_old, followers_old_count = handle_profile_change("Followers", followers_old_count, followers_count, followers_old, followers_raw, user, csv_file_name, field="login")

        # Changed public repositories
        try:
            if GET_ALL_REPOS:
                debug_github_operation("all repository refresh", user)
                repos_raw = gh_call(lambda: list(g_user.get_repos()), raise_on_failure=True)()  # noqa: B023
                repos_count = gh_call(lambda: g_user.public_repos)()  # noqa: B023
            else:
                debug_github_operation("owned repository refresh", user)
                repos_raw = gh_call(lambda: [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login], raise_on_failure=True)()  # noqa: B023
                repos_count = len(repos_raw)
        except NET_ERRORS as e:
            verbose_degraded_feature("Repositories", "repository change alerts", e)
            print_degraded_error("Repositories could not be refreshed", e)
            print_cur_ts("Timestamp:\t\t\t")
            repos_raw = None
            repos_count = None

        if repos_raw is not None and repos_count is not None:
            repos_old, repos_old_count = handle_profile_change("Repos", repos_old_count, repos_count, repos_old, repos_raw, user, csv_file_name, field="name")

        # Changed starred repositories
        try:
            debug_github_operation("starred repository refresh", user)
            starred_list = gh_call(lambda: list(g_user.get_starred()), raise_on_failure=True)()  # noqa: B023
            starred_count = len(starred_list)
        except NET_ERRORS as e:
            verbose_degraded_feature("Starred repositories", "starred repository change alerts", e)
            print_degraded_error("Starred repositories could not be refreshed", e)
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
                    print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

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
                print_csv_write_error(e)

            m_subject = f"GitHub user {user} has {'blocked' if blocked else 'unblocked'} you!"
            m_body = f"GitHub user {user} has {'blocked' if blocked else 'unblocked'} you!\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            send_notification_channels("profile", m_subject, m_body, "", PROFILE_NOTIFICATION)

            blocked_old = blocked
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        list_of_repos = []

        # Changed repos details
        if TRACK_REPOS_CHANGES:

            try:
                if GET_ALL_REPOS:
                    repos_list = gh_call(lambda: list(g_user.get_repos()), raise_on_failure=True)()  # noqa: B023
                else:
                    debug_github_operation("owned repository detail refresh", user)
                    repos_list = gh_call(lambda: [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login], raise_on_failure=True)()  # noqa: B023
            except NET_ERRORS as e:
                repos_list = None
                verbose_degraded_feature("Repository detail feed", "repository detail alerts", e)
                print_degraded_error("The repository detail feed could not be refreshed, so the previous snapshot is kept", e)
                print_cur_ts("Timestamp:\t\t\t")

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
                    print_degraded_error("The public repository list could not be refreshed, so the previous one is kept", e)
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
                                        print_csv_write_error(e)
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
                                        print_csv_write_error(e)
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
            try:
                events = gh_call(lambda: list(islice(g_user.get_events(), EVENTS_NUMBER)), raise_on_failure=True)()  # noqa: B023
            except NET_ERRORS as e:
                events = None
                verbose_degraded_feature("Recent events", "new event alerts", e)
                print_degraded_error("Recent events could not be refreshed, so the previous snapshot is kept", e)
                print_cur_ts("Timestamp:\t\t\t")
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
                        print_degraded_error("The last event identifier could not be read", e)
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
                                print()
                                print_degraded_error("Some event details are missing", e, label="Warning")

                            first_new = False

                            if event_date and repo_name and event_text:

                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                                except Exception as e:
                                    print_csv_write_error(e)

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

        report_recovered_features()
        close_pending_notice_block()

        # The banner speaks for a quiet check, so anything this one reported restarts the clock instead of being contradicted by it
        if REPORTS_PRINTED != reports_before_check:
            alive_since = int(time.time())
        elif LIVENESS_REMINDER_SECONDS and int(time.time()) - alive_since >= LIVENESS_REMINDER_SECONDS:
            print_liveness_banner(f"Monitoring healthy for {user}. No tracked change since the last check")
            alive_since = int(time.time())

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
        record_secret_source("WEBHOOK_URL", "command line")
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
            verbose_print(f"Selected webhook provider {webhook_provider_display_name(detected_provider)} from the destination URL")
            if report_warnings:
                print(f"* Warning: Configured webhook provider did not match the URL. Using {webhook_provider_display_name(detected_provider)}.")


# Applies monitoring, output and email command-line overrides to effective settings
def apply_monitoring_cli_overrides(args: argparse.Namespace, parser: argparse.ArgumentParser, strict=True) -> None:
    global CSV_FILE, DISABLE_LOGGING, PROFILE_NOTIFICATION, EVENT_NOTIFICATION, REPO_NOTIFICATION, REPO_UPDATE_DATE_NOTIFICATION, ERROR_NOTIFICATION, GITHUB_CHECK_INTERVAL, LIVENESS_REMINDER_SECONDS, DO_NOT_MONITOR_GITHUB_EVENTS, TRACK_REPOS_CHANGES, REPOS_TO_MONITOR, GET_ALL_REPOS, CONTRIB_NOTIFICATION, TRACK_CONTRIB_CHANGES, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION
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
    LIVENESS_REMINDER_SECONDS = int(LIVENESS_CHECK_INTERVAL) if intervals_valid and LIVENESS_CHECK_INTERVAL else 0


# Returns the final log file path without creating its directory or file
def resolve_output_log_path(username):
    log_path = Path(os.path.expanduser(GITHUB_LOGFILE))
    if log_path.parent != Path('.'):
        if log_path.suffix == "":
            log_path = log_path.parent / f"{log_path.name}_{username or 'target'}.log"
    elif log_path.suffix == "":
        log_path = Path(f"{log_path.name}_{username or 'target'}.log")
    return log_path


# The four shared status markers. A fifth neutral marker is the single biggest source of drift between these
# tools, because every state it would cover is a state the others already call PASS
DOCTOR_STATUSES = ("PASS", "WARN", "FAIL", "SKIP")

# A check interval below this invites the GitHub rate limiter, which stops the tool seeing anything
DOCTOR_MIN_SAFE_CHECK_INTERVAL = 30


@dataclass(frozen=True)
class DoctorCheck:
    section: str
    status: str
    label: str
    detail: str = ""
    advice: Optional[RecoveryAdvice] = None


# Builds one validated doctor row, which is where the status, the required action and a duplicated detail are decided
def make_doctor_check(section, status, label, detail="", advice=None):
    normalized_status = str(status).upper()
    if normalized_status not in DOCTOR_STATUSES:
        raise ValueError(f"Unsupported doctor status {status}")
    # A row the user has to act on is useless without an action, so the row is rejected rather than printed bare
    if normalized_status in ("WARN", "FAIL") and (advice is None or not advice.fix):
        raise ValueError(f"Doctor {normalized_status} rows require a fix")
    # Several advice objects carry the same text as their summary and printing it twice reads as two problems
    return DoctorCheck(section, normalized_status, label, "" if str(detail).strip() == str(label).strip() else detail, advice)


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

    # Adds one validated result row to the report and returns it, so a row rendered on its own is still validated here
    def add(self, section, status, label, detail="", advice=None):
        check = make_doctor_check(section, status, label, detail, advice)
        self.checks.append(check)
        return check

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
    if sys.version_info >= MINIMUM_PYTHON_VERSION:
        report.add("Environment", "PASS", f"Python {version} is supported", f"Minimum supported version: {MINIMUM_PYTHON_VERSION_TEXT}")
    else:
        advice = make_recovery_advice("dependency.missing", f"Python {version} is unsupported", recovery_fix_with_guide(f"Install Python {MINIMUM_PYTHON_VERSION_TEXT} or newer", INSTALL_GUIDE_URL), False)
        report.add("Environment", "FAIL", advice.summary, f"Minimum supported version: {MINIMUM_PYTHON_VERSION_TEXT}", advice)
    required = (("requests", "requests"), ("urllib3", "urllib3"), ("python-dateutil", "dateutil"), ("pytz", "pytz"), ("PyGithub", "github"))
    for package_name, module_name in required:
        if doctor_dependency_available(module_name, module_finder):
            report.add("Environment", "PASS", f"Required dependency {package_name} is installed")
        else:
            install_command = shlex.join([sys.executable, "-m", "pip", "install", package_name])
            advice = make_recovery_advice("dependency.missing", f"Required dependency {package_name} is missing", recovery_fix_with_guide(f"Install it with: {install_command}", INSTALL_GUIDE_URL), False)
            report.add("Environment", "FAIL", advice.summary, "The monitor cannot run its required path without this package", advice)
    optional = (("python-dotenv", "dotenv", "dotenv discovery and loading"), ("tzlocal", "tzlocal", "automatic timezone detection"))
    # The classic Command Prompt is the only place this library changes anything, so a machine it cannot affect is not warned about a package it does not need
    if platform.system() == "Windows":
        optional += (("colorama", "colorama", "coloured output in the classic Windows Command Prompt"),)
    for package_name, module_name, feature in optional:
        if doctor_dependency_available(module_name, module_finder):
            report.add("Environment", "PASS", f"Optional dependency {package_name} is installed", f"Used only for {feature}")
        else:
            install_command = shlex.join([sys.executable, "-m", "pip", "install", package_name])
            advice = make_recovery_advice("dependency.missing", f"Optional dependency {package_name} is not installed", recovery_fix_with_guide(f"Install it with: {install_command}", INSTALL_GUIDE_URL), False)
            report.add("Environment", "WARN", advice.summary, f"{feature[:1].upper() + feature[1:]} will not work. Every other feature is unaffected", advice)


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


# Names every on/off setting holding something other than True or False, since a string such as "false" would count as on
def runtime_boolean_errors():
    errors = []
    for statement in ast.parse(CONFIG_BLOCK, "<built-in-config>", "exec").body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, bool):
            value = globals().get(statement.targets[0].id)
            if not isinstance(value, bool):
                errors.append(f"{statement.targets[0].id} must be True or False, not {value!r}")
    return errors


# Returns all type and range errors in settings that control runtime timing or counts
def runtime_configuration_errors():
    errors = []
    positive_numbers = (("CHECK_INTERNET_TIMEOUT", CHECK_INTERNET_TIMEOUT),)
    nonnegative_numbers = (("LIVENESS_CHECK_INTERVAL", LIVENESS_CHECK_INTERVAL), ("NET_BASE_BACKOFF_SEC", NET_BASE_BACKOFF_SEC))
    positive_integers = (("GITHUB_CHECK_INTERVAL", GITHUB_CHECK_INTERVAL), ("EVENTS_NUMBER", EVENTS_NUMBER), ("NET_MAX_RETRIES", NET_MAX_RETRIES))
    for name, value in positive_numbers:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            errors.append(f"{name} must be a number greater than zero, not {value!r}")
    for name, value in nonnegative_numbers:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            errors.append(f"{name} must be a number zero or greater, not {value!r}")
    for name, value in positive_integers:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"{name} must be an integer greater than zero, not {value!r}")
    if not isinstance(SMTP_PORT, int) or isinstance(SMTP_PORT, bool) or not 1 <= SMTP_PORT <= 65535:
        errors.append(f"SMTP_PORT must be an integer from 1 through 65535, not {SMTP_PORT!r}")
    return errors


# Adds configuration, dotenv, private-setting and core value checks
def doctor_check_configuration(report, args, parser):
    global CLI_CONFIG_PATH, CONFIG_DISCOVERY_DISABLED, LOCAL_TIMEZONE
    CONFIG_DISCOVERY_DISABLED = isinstance(args.config_file, str) and args.config_file.casefold() == "none"
    if args.config_file and not CONFIG_DISCOVERY_DISABLED:
        CLI_CONFIG_PATH = os.path.expanduser(args.config_file)
    elif CONFIG_DISCOVERY_DISABLED:
        CLI_CONFIG_PATH = None
    cfg_path = None if CONFIG_DISCOVERY_DISABLED else find_config_file(CLI_CONFIG_PATH)
    configured_settings = set()
    config_errors = []
    retired_settings = set()
    if CONFIG_DISCOVERY_DISABLED:
        report.add("Configuration", "PASS", "No configuration file selected", "Using built-in defaults and command-line overrides")
    elif CLI_CONFIG_PATH and not cfg_path:
        advice = make_recovery_advice("config.missing", "Configuration file was not found", recovery_fix_with_guide("Correct --config-file or generate a new configuration with --generate-config", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, f"Requested path: {CLI_CONFIG_PATH}", advice)
    elif cfg_path:
        loaded = load_config_file(cfg_path, report_errors=False, loaded_names_out=configured_settings, diagnostic_overrides=(args.verbose is True, args.debug is True), error_out=config_errors, retired_names_out=retired_settings)
        if loaded:
            report.add("Configuration", "PASS", "Configuration file loaded", f"Path: {cfg_path}")
        else:
            advice = make_recovery_advice("config.invalid", "Configuration file could not be loaded", recovery_fix_with_guide("Keep only documented SETTING = value lines with plain literal values or regenerate the file", CONFIG_GUIDE_URL), False)
            report.add("Configuration", "FAIL", advice.summary, config_errors[0] if config_errors else f"Path: {cfg_path}", advice)
    else:
        report.add("Configuration", "PASS", "No configuration file selected", "Using built-in defaults and command-line overrides")
    if retired_settings:
        listed = ", ".join(sorted(retired_settings))
        advice = make_recovery_advice("config.invalid", "Retired configuration settings were ignored", recovery_fix_with_guide("Remove the retired settings from the configuration file", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "WARN", advice.summary, listed, advice)
    apply_diagnostic_cli_overrides(args)
    dotenv_errors = []
    env_path = load_startup_secrets(args.env_file, configured_settings, report_errors=False, errors_out=dotenv_errors)
    apply_startup_cli_overrides(args, configured_settings)
    apply_webhook_cli_overrides(args, parser, report_warnings=False)
    trace_unresolved_secrets()
    if args.repos is not None and not (TRACK_REPOS_CHANGES or args.track_repos_changes is True):
        advice = make_recovery_advice("config.invalid", "Repository selection cannot take effect", recovery_fix_with_guide("Add --track-repos-changes or remove --repos", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, "--repos requires repository detail tracking", advice)
    apply_monitoring_cli_overrides(args, parser, strict=False)
    if DOTENV_FILE and DOTENV_FILE.casefold() == "none":
        report.add("Configuration", "PASS", "No dotenv file selected", "Using environment variables and other configured sources")
    elif env_path and os.path.isfile(env_path) and not dotenv_errors:
        report.add("Configuration", "PASS", "Dotenv file loaded", f"Path: {env_path}")
    elif dotenv_errors:
        advice = make_recovery_advice("file.unreadable", "Dotenv file could not be loaded", recovery_fix_with_guide("Correct --env-file, install python-dotenv or disable dotenv loading with --env-file none", SECRETS_GUIDE_URL), False)
        report.add("Configuration", "WARN", advice.summary, dotenv_errors[0], advice)
    else:
        report.add("Configuration", "PASS", "No dotenv file selected", "Using environment variables and other configured sources")
    source_order = ("dotenv file", "environment", "configuration file", "built-in configuration", "command line")
    source_labels = {"dotenv file": "Secrets loaded from the dotenv file", "environment": "Secrets loaded from the environment", "configuration file": "Secrets loaded from the configuration file", "built-in configuration": "Secrets loaded from the built-in configuration", "command line": "Secrets loaded from the command line"}
    source_rows = 0
    for source in source_order:
        names = sorted(name for name, actual_source in SECRET_SOURCES.items() if actual_source == source)
        if names:
            report.add("Configuration", "PASS", source_labels[source], ", ".join(names))
            source_rows += 1
    if not source_rows:
        report.add("Configuration", "PASS", "No secrets loaded", "Nothing was read from a dotenv file, the environment, the configuration file or the command line")
    if VERIFY_SSL:
        report.add("Configuration", "PASS", "TLS certificate verification is on", "Every outbound request checks the server certificate")
    else:
        advice = make_recovery_advice("config.insecure", "TLS certificate verification is off", recovery_fix_with_guide("Set VERIFY_SSL back to True unless this network intercepts TLS with its own certificate authority", TLS_GUIDE_URL), False)
        report.add("Configuration", "WARN", advice.summary, "VERIFY_SSL is False, so an intercepted connection cannot be told apart from the real service", advice)
    if not validate_github_endpoint_url(GITHUB_API_URL):
        advice = make_recovery_advice("config.value_invalid", "GitHub API URL is invalid", recovery_fix_with_guide("Set GITHUB_API_URL to a complete HTTPS URL without credentials, query parameters or fragments", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, sanitize_error_text(GITHUB_API_URL) or "No URL configured", advice)
    if not validate_github_endpoint_url(GITHUB_HTML_URL):
        advice = make_recovery_advice("config.value_invalid", "GitHub web URL is invalid", recovery_fix_with_guide("Set GITHUB_HTML_URL to a complete HTTPS URL without credentials, query parameters or fragments", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, sanitize_error_text(GITHUB_HTML_URL) or "No URL configured", advice)
    timezone_advice = resolve_local_timezone()
    timezone_label = TIMEZONE_CHECK_LABELS[LOCAL_TIMEZONE_STATE]
    if timezone_advice is not None:
        report.add("Configuration", "FAIL", timezone_label, timezone_advice.detail, timezone_advice)
        # The report still stamps timestamps, so it falls back rather than stopping before the diagnosis
        LOCAL_TIMEZONE = "UTC"
    else:
        report.add("Configuration", "PASS", timezone_label, f"Time zone: {LOCAL_TIMEZONE}")
    if isinstance(GITHUB_CHECK_INTERVAL, (int, float)) and not isinstance(GITHUB_CHECK_INTERVAL, bool) and 0 < GITHUB_CHECK_INTERVAL < DOCTOR_MIN_SAFE_CHECK_INTERVAL:
        advice = make_recovery_advice("github.rate_limited", "Check intervals are short", recovery_fix_with_guide(f"Raise GITHUB_CHECK_INTERVAL to at least {DOCTOR_MIN_SAFE_CHECK_INTERVAL} seconds", INTERVALS_GUIDE_URL), True)
        report.add("Configuration", "WARN", advice.summary, f"{display_time(GITHUB_CHECK_INTERVAL)} between checks", advice)
    numeric_errors = runtime_configuration_errors()
    if numeric_errors:
        advice = make_recovery_advice("config.value_invalid", "One or more numeric settings are invalid", recovery_fix_with_guide("Correct the reported settings in the configuration file", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, "Invalid numeric settings: " + "; ".join(numeric_errors), advice)
    boolean_errors = runtime_boolean_errors()
    if boolean_errors:
        advice = make_recovery_advice("config.value_invalid", "One or more on/off settings are invalid", recovery_fix_with_guide("Set the reported settings to True or False in the configuration file", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, "Invalid on/off settings: " + "; ".join(boolean_errors), advice)
    if TARGET_GITHUB_USERNAME and not wizard_normalize_target(TARGET_GITHUB_USERNAME):
        advice = make_recovery_advice("config.value_invalid", "Saved GitHub target is invalid", recovery_fix_with_guide("Set TARGET_GITHUB_USERNAME to a GitHub username or complete profile URL", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, sanitize_error_text(TARGET_GITHUB_USERNAME), advice)
    event_types_valid = isinstance(EVENTS_TO_MONITOR, (list, tuple)) and any(isinstance(value, str) and value.strip() for value in EVENTS_TO_MONITOR)
    if not DO_NOT_MONITOR_GITHUB_EVENTS and not event_types_valid:
        advice = make_recovery_advice("config.value_invalid", "Event type selection is invalid", recovery_fix_with_guide("Add ALL or at least one supported event name to EVENTS_TO_MONITOR", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, "No usable event type is configured", advice)
    try:
        ascii_log_separators_enabled()
    except ValueError as exc:
        advice = make_recovery_advice("config.value_invalid", "Log separator mode is invalid", recovery_fix_with_guide("Set ASCII_LOG_SEPARATORS to Auto, On or Off", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, str(exc), advice)
    return cfg_path, env_path


# Adds a live token validation result and retains authenticated state for later checks
def doctor_check_authentication(report, request_get=None):
    report.github_token = str(GITHUB_TOKEN or "")
    if not report.github_token or report.github_token == "your_github_classic_personal_access_token":
        token_command = render_command(["--set-github-token"])
        advice = make_recovery_advice("auth.github_token_missing", "GitHub token is missing", recovery_fix_with_guide(f"Create a token then run: {token_command}", AUTH_GUIDE_URL), False)
        report.add("Authentication", "FAIL", advice.summary, "No usable GITHUB_TOKEN was resolved", advice)
        return
    try:
        report.authenticated_login = validate_github_token(report.github_token, request_get=request_get)
        report.add("Authentication", "PASS", "GitHub token was accepted", f"Authenticated as: {report.authenticated_login}")
    except Exception as exc:
        detail = sanitize_error_text(exc).replace(" and the dotenv file was not changed", "")
        advice = make_recovery_advice("auth.github_token_invalid", "GitHub token validation failed", recovery_fix_with_guide("Check the token, its access and GITHUB_API_URL then run doctor again", AUTH_GUIDE_URL), False)
        report.add("Authentication", "FAIL", advice.summary, f"{type(exc).__name__}: {detail}", advice)


# Adds one bounded connectivity check for the configured startup endpoint
def doctor_check_connectivity(report, request_get=None):
    if not validate_github_endpoint_url(CHECK_INTERNET_URL):
        row_advice = make_recovery_advice("config.value_invalid", "The connectivity endpoint URL is invalid", recovery_fix_with_guide("Set CHECK_INTERNET_URL to a complete HTTPS URL", CONFIG_GUIDE_URL), False)
        report.add("Connectivity", "FAIL", row_advice.summary, sanitize_error_text(CHECK_INTERNET_URL) or "No URL configured", row_advice)
        return
    # The same check the monitor runs at startup, so doctor cannot disagree with it about the same endpoint
    if check_internet(quiet=True, operation="doctor connectivity", request_get=request_get):
        report.add("Connectivity", "PASS", "The connectivity endpoint is reachable", f"Endpoint: {diagnostic_endpoint(CHECK_INTERNET_URL)}")
        return
    # The row names the endpoint, so the technical cause goes where the other tools put it
    advice = classify_recovery_error(LAST_CONNECTIVITY_ERROR, "connectivity")
    report.add("Connectivity", "FAIL", advice.summary, f"Endpoint: {diagnostic_endpoint(CHECK_INTERNET_URL)}", advice)


# Adds a target lookup and retains the fetched profile for feed checks
def doctor_check_target(report, github_factory=None):
    if not report.target_name:
        command = render_command(["<github_target>", "--doctor"])
        advice = make_recovery_advice("target.missing", "No GitHub target was provided", recovery_fix_with_guide(f"Run doctor again with a target: {command}", QUICK_START_GUIDE_URL), False)
        report.add("Target", "WARN", advice.summary, "Nothing will be monitored until one is given", advice)
        return
    if not report.authenticated_login:
        report.add("Target", "SKIP", "The monitored profile was not checked", "The GitHub token did not validate, so no lookup was attempted")
        return
    try:
        report.github_client = create_github_client("doctor target validation") if github_factory is None else github_factory()
        debug_github_operation("doctor target lookup", report.target_name)
        report.target_profile = report.github_client.get_user(report.target_name)
        resolved_login = str(getattr(report.target_profile, "login", report.target_name))
        report.add("Target", "PASS", "GitHub target is accessible", f"Resolved login: {resolved_login}")
    except Exception as exc:
        advice = make_recovery_advice("target.not_found", "GitHub target is not accessible", recovery_fix_with_guide("Check the username, token access and GitHub Enterprise endpoint then run doctor again", QUICK_START_GUIDE_URL), False)
        report.add("Target", "FAIL", advice.summary, f"{type(exc).__name__}: {sanitize_error_text(exc)}", advice)


# Evaluates one lazy PyGithub feed without retaining its potentially large contents
def doctor_probe_feed(operation, iterable_factory):
    debug_github_operation(operation)
    iterator = iter(iterable_factory())
    next(iterator, None)


# Adds monitoring feed, feature and read-only output path checks
def doctor_check_monitoring(report, contribution_checker=None):
    if report.target_name and report.target_profile is None:
        report.add("Monitoring", "SKIP", "Core monitoring feeds were not checked", "The target profile was not fetched, so no feed was probed")
    elif report.target_profile is not None:
        feed_checks = [("Repository feed is accessible", "doctor repository feed", lambda: report.target_profile.get_repos(type='owner')), ("Starred repository feed is accessible", "doctor starred repository feed", report.target_profile.get_starred)]
        if not DO_NOT_MONITOR_GITHUB_EVENTS:
            feed_checks.append(("Recent event feed is accessible", "doctor recent event feed", report.target_profile.get_events))
        for label, operation, factory in feed_checks:
            try:
                doctor_probe_feed(operation, factory)
                report.add("Monitoring", "PASS", label)
            except Exception as exc:
                advice = make_recovery_advice("github.api_error", label.replace(" is accessible", " is unavailable"), recovery_fix_with_guide("Check target visibility, token access and GitHub API availability", DEBUG_GUIDE_URL), False)
                report.add("Monitoring", "FAIL", advice.summary, f"{type(exc).__name__}: {sanitize_error_text(exc)}", advice)
        if DO_NOT_MONITOR_GITHUB_EVENTS:
            report.add("Monitoring", "PASS", "GitHub event monitoring is disabled", "No event feed check was needed")
    if TRACK_REPOS_CHANGES:
        if REPOS_TO_MONITOR:
            report.add("Monitoring", "PASS", "Repository detail tracking is enabled", f"Selection: {', '.join(str(value) for value in REPOS_TO_MONITOR)}")
        else:
            advice = make_recovery_advice("config.value_invalid", "Repository detail tracking has no selected repositories", recovery_fix_with_guide("Set REPOS_TO_MONITOR or pass --repos", CONFIG_GUIDE_URL), False)
            report.add("Monitoring", "WARN", advice.summary, "No repository detail alerts can fire", advice)
    else:
        report.add("Monitoring", "PASS", "Repository detail tracking is disabled")
    if TRACK_CONTRIB_CHANGES and report.target_profile is not None:
        checker = get_daily_contributions_count if contribution_checker is None else contribution_checker
        try:
            checker(report.target_name, today_local(), report.github_token)
            report.add("Monitoring", "PASS", "Daily contribution feed is accessible")
        except Exception as exc:
            advice = make_recovery_advice("github.api_error", "Daily contribution feed is unavailable", recovery_fix_with_guide("Check token access, timezone and GitHub GraphQL availability", DEBUG_GUIDE_URL), False)
            report.add("Monitoring", "FAIL", advice.summary, f"{type(exc).__name__}: {sanitize_error_text(exc)}", advice)
    elif TRACK_CONTRIB_CHANGES:
        report.add("Monitoring", "SKIP", "Daily contribution feed was not checked", "The target profile was not fetched, so no lookup was attempted")
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
        detail = f"Path: {selected}"
    if writable:
        report.add("Configuration", "PASS", f"{label} appears writable", detail)
    else:
        advice = make_recovery_advice("file.unwritable", f"{label} is not writable: {selected}", recovery_fix_with_guide(f"Choose a writable path for the {label.lower()} or correct its parent permissions", CONFIG_GUIDE_URL), False)
        report.add("Configuration", "FAIL", advice.summary, detail, advice)


# Adds read-only checks for each file monitoring would write
def doctor_check_output_paths(report):
    if CSV_FILE:
        doctor_add_path_check(report, "CSV destination", CSV_FILE)
    else:
        report.add("Configuration", "PASS", "CSV logging is disabled")
    if DISABLE_LOGGING:
        report.add("Configuration", "PASS", "Output logging is disabled")
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
        report.add("Notifications", "FAIL", advice.summary, advice.detail, advice)
        return
    finally:
        smtp_quit_quietly(smtp_object)
    report.email_ready = True
    report.add("Notifications", "PASS", SMTP_READY_CHECK_LABEL, f"Alerts: {', '.join(_startup_email_notification_categories())}. No email was sent during this passive check")


# Adds the doctor row for email alerts whose settings cannot deliver, worded the same way by every sibling monitor
def doctor_add_email_unusable_check(report, detail, fix):
    advice = make_recovery_advice("smtp.invalid", EMAIL_UNUSABLE_CHECK_LABEL, recovery_fix_with_guide(fix, SMTP_GUIDE_URL), False, detail)
    report.add("Notifications", "WARN", advice.summary, detail, advice)


# Adds channel readiness checks and stores structural delivery-test readiness
def doctor_check_notifications(report):
    problem = email_settings_problem()
    if not _startup_email_notification_categories() and problem is None:
        advice = make_recovery_advice("smtp.invalid", "Email is configured but no alert types are selected", recovery_fix_with_guide("Turn on at least one email alert in the configuration file", SMTP_GUIDE_URL), False)
        report.add("Notifications", "WARN", advice.summary, "Nothing would ever be emailed", advice)
    elif not doctor_email_alerts_enabled():
        report.add("Notifications", "PASS", "Email notifications are disabled", "No SMTP connection was attempted and no email was sent")
    else:
        if problem is not None:
            doctor_add_email_unusable_check(report, *problem)
        else:
            doctor_add_smtp_login_check(report)
    # The error alert ships on by default, so it alone cannot mean the channel was meant to be on
    deliberate_webhook_types = any((WEBHOOK_PROFILE_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION))
    if not WEBHOOK_ENABLED and not deliberate_webhook_types:
        report.add("Notifications", "PASS", "Webhook alerts are disabled")
        return
    if not WEBHOOK_ENABLED:
        advice = make_recovery_advice("webhook.invalid", "Webhook alert types are selected but webhooks are switched off", recovery_fix_with_guide("Set WEBHOOK_ENABLED to True, or turn the alert types off", WEBHOOK_GUIDE_URL), False)
        report.add("Notifications", "WARN", advice.summary, "Nothing would ever be delivered", advice)
        return
    if not validate_webhook_url(WEBHOOK_URL):
        advice = make_recovery_advice("webhook.invalid", "WEBHOOK_URL must contain a complete HTTPS link", recovery_fix_with_guide("Set WEBHOOK_URL with --set-webhook-url or disable WEBHOOK_ENABLED", WEBHOOK_GUIDE_URL), False)
        report.add("Notifications", "FAIL", advice.summary, "The destination is not a complete supported HTTPS link", advice)
        return
    provider = normalized_webhook_provider()
    customization_error = validate_webhook_customization(provider)
    header_error = validate_webhook_headers(provider)
    if not provider:
        advice = make_recovery_advice("webhook.invalid", "Webhook provider is invalid", recovery_fix_with_guide("Set WEBHOOK_PROVIDER to discord or ntfy", WEBHOOK_GUIDE_URL), False)
        report.add("Notifications", "FAIL", advice.summary, sanitize_error_text(WEBHOOK_PROVIDER), advice)
    elif customization_error is not None:
        advice = make_recovery_advice("webhook.invalid", "Webhook customization is invalid", recovery_fix_with_guide("Correct WEBHOOK_TEMPLATE, WEBHOOK_USERNAME, WEBHOOK_AVATAR_URL or WEBHOOK_TRANSFORMS", WEBHOOK_GUIDE_URL), False)
        report.add("Notifications", "FAIL", advice.summary, customization_error, advice)
    elif header_error is not None:
        advice = make_recovery_advice("webhook.invalid", "Webhook headers are invalid", recovery_fix_with_guide("Correct WEBHOOK_HEADERS or NTFY_ACCESS_TOKEN", WEBHOOK_GUIDE_URL), False)
        report.add("Notifications", "FAIL", advice.summary, header_error, advice)
    elif not deliberate_webhook_types and not WEBHOOK_ERROR_NOTIFICATION:
        advice = make_recovery_advice("webhook.invalid", "Webhook alerts are on but no alert types are selected", recovery_fix_with_guide("Turn on at least one webhook alert in the configuration file, or set WEBHOOK_ENABLED to False", WEBHOOK_GUIDE_URL), False)
        report.add("Notifications", "WARN", advice.summary, "Nothing would ever be delivered", advice)
    else:
        report.webhook_ready = True
        report.add("Notifications", "PASS", f"{WEBHOOK_READY_CHECK_LABEL} for {webhook_provider_display_name()}", f"Alerts: {', '.join(_startup_webhook_notification_categories())}. The private link was not displayed. No webhook was sent during this passive check")


# Sanitizes one doctor field and keeps it on a single output-contract line
def sanitize_doctor_text(value):
    return " ".join(sanitize_error_text(value).splitlines()).strip()


# Renders one doctor result while sanitizing every user-visible field
def print_doctor_check(check, *, stream=None):
    destination = sys.stdout if stream is None else stream
    marker = colorize(_DOCTOR_MARK_STYLES[check.status], f"[{check.status}]")
    destination.write(f"{marker} {sanitize_doctor_text(check.label)}\n")
    if check.detail:
        # The report is written to a sanitize-only surface, so the link colour every other line gets from the stream is applied here
        destination.write(f"  {colorize_links(sanitize_doctor_text(check.detail))}\n")
    if check.status != "PASS" and check.advice is not None:
        # The fix carries its own guide line, so each line is indented and styled on its own
        for advice_line in f"To fix: {check.advice.fix}".splitlines():
            destination.write(f"  {colorize_fix_line(sanitize_doctor_text(advice_line))}\n")


# The fixed section order the report renders in, chosen so each section depends only on the ones above it
DOCTOR_SECTIONS = ("Environment", "Configuration", "Authentication", "Connectivity", "Target", "Monitoring", "Notifications")


# Renders every non-empty section in the fixed order with exactly one blank line between them
def render_doctor_sections(report, stream=None):
    destination = sys.stdout if stream is None else stream
    for section in DOCTOR_SECTIONS:
        section_checks = [check for check in report.checks if check.section == section]
        if not section_checks:
            continue
        destination.write(f"\n{colorize('section', section)}\n")
        for check in section_checks:
            print_doctor_check(check, stream=destination)


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
    while True:
        destination.write(colorize("info", f"{prompt} [y/N]: "))
        destination.flush()
        try:
            answer = str(read_interactively(input_func)).strip().casefold()
        except EOFError:
            destination.write("\nDelivery test skipped.\n")
            return False
        except KeyboardInterrupt:
            # Ctrl+C ends the run here the way it does anywhere else, rather than only declining this one test
            signal_handler(signal.SIGINT, None)
            raise
        if not answer or answer in ("n", "no"):
            return False
        if answer in ("y", "yes"):
            return True
        # An unreadable answer is re-asked rather than counted as consent or as a refusal the user did not give
        destination.write("  Please answer 'y' or 'n'." + "\n")


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
            result = send_email_func("github_monitor: doctor test email", "This test email was sent after approval in --doctor. Your SMTP delivery settings work.", "", SMTP_SSL, smtp_timeout=5)
            if result == 0:
                check = report.add("Optional delivery tests", "PASS", "Doctor test email delivered", "One real test email was sent after confirmation")
            else:
                advice = make_recovery_advice("smtp.connection", "Doctor test email delivery failed", recovery_fix_with_guide("Review the SMTP error above and correct the email settings", SMTP_GUIDE_URL), True)
                check = report.add("Optional delivery tests", "FAIL", advice.summary, "The approved test email could not be delivered", advice)
        else:
            check = report.add("Optional delivery tests", "SKIP", "Test email was not sent", "You declined the real delivery test. Run doctor again and approve the email test when ready")
        print_doctor_check(check, stream=destination)
    if report.webhook_ready:
        provider = webhook_provider_display_name()
        approved = ask_doctor_approval(f"Send one test webhook through {provider} now? This will publish a real notification", input_func, destination)
        if approved:
            result = send_webhook_func("github_monitor: doctor test webhook", "This test notification was sent after approval in --doctor. Your webhook delivery settings work.", "event", force=True)
            if result == 0:
                check = report.add("Optional delivery tests", "PASS", f"Doctor test webhook through {provider} delivered", "One real test webhook was sent after confirmation")
            else:
                advice = make_recovery_advice("webhook.connection", f"Doctor test webhook through {provider} delivery failed", recovery_fix_with_guide("Review the webhook error above and correct the destination settings", WEBHOOK_GUIDE_URL), True)
                check = report.add("Optional delivery tests", "FAIL", advice.summary, "The approved test webhook could not be delivered", advice)
        else:
            check = report.add("Optional delivery tests", "SKIP", f"Test webhook through {provider} was not sent", "You declined the real delivery test. Run doctor again and approve the webhook test when ready")
        print_doctor_check(check, stream=destination)


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
    destination.write("\n" + colorize_links(f"Guide: {DOCTOR_GUIDE_URL}") + "\n")


# Runs the complete read-only preflight and returns its healthcheck exit code
def run_doctor(args, parser, request_get=None, github_factory=None, contribution_checker=None, module_finder=None, input_func=input, input_stream=None, stream=None, email_sender=None, webhook_sender=None, show_banner=True):
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
        progress.show("connectivity")
        doctor_check_connectivity(report, request_get)
        progress.show("authentication")
        doctor_check_authentication(report, request_get)
        progress.show("the monitored profile")
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
    "FileDestinations": (),
}
WIZARD_SECRET_KEYS = {"Authentication": ("GITHUB_TOKEN",), "Email": ("SMTP_PASSWORD",), "Webhook": ("WEBHOOK_URL", "NTFY_ACCESS_TOKEN")}
WIZARD_CONFIG_ORDER = tuple(name for names in WIZARD_SECTION_KEYS.values() for name in names)

# The mail server settings the wizard collects, and how long its sign-in check waits for the server
WIZARD_SMTP_CONFIG_KEYS = ("SMTP_HOST", "SMTP_PORT", "SMTP_SSL", "SMTP_USER", "SENDER_EMAIL", "RECEIVER_EMAIL")
WIZARD_SMTP_TIMEOUT = 5

# The alert settings each channel owns, so one preset answer can switch the whole channel on
WIZARD_EMAIL_NOTIFICATION_KEYS = ("PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION", "ERROR_NOTIFICATION")
WIZARD_WEBHOOK_NOTIFICATION_KEYS = ("WEBHOOK_PROFILE_NOTIFICATION", "WEBHOOK_EVENT_NOTIFICATION", "WEBHOOK_REPO_NOTIFICATION", "WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION", "WEBHOOK_CONTRIB_NOTIFICATION", "WEBHOOK_ERROR_NOTIFICATION")


# Writes one coloured wizard heading at the requested level
def _wizard_heading(destination, text, part="section"):
    destination.write("\n" + colorize(part, text) + "\n\n")


# Writes one labelled command with sibling-style indentation and spacing
def _wizard_print_command(destination, label, command, suffix=""):
    destination.write(f"{label}\n")
    destination.write(f"    {colorize('section', command)}{colorize('info', suffix) if suffix else ''}\n\n")


# Writes the command that starts monitoring with the files this run checked, so a report read on its own
# ends with the next action rather than leaving the reader to assemble the command
def print_doctor_next_steps(destination, target=None, saved_target=None, doctor_exit=0):
    _wizard_heading(destination, "Next steps", "header")
    label = "After Doctor passes, start monitoring:" if doctor_exit else "Start monitoring:"
    monitor_target = command_targets(target, saved_target)[1]
    _wizard_print_command(destination, label, render_command([monitor_target] if monitor_target else []))
    destination.write(f"Guide: {colorize('link', QUICK_START_GUIDE_URL)}\n")


# Walks up to the first directory that exists, so a destination under a missing folder can still be judged
def wizard_nearest_existing_parent(path):
    candidate = Path(path).expanduser()
    if candidate.exists():
        return candidate if candidate.is_dir() else candidate.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


# Checks one setup destination without creating or modifying it, so an unwritable path is caught before any question
def wizard_validate_destination(path, label):
    resolved = Path(path).expanduser().resolve()
    if resolved.exists() and resolved.is_dir():
        raise ValueError(f"{label} must be a file path, not a directory")
    parent = wizard_nearest_existing_parent(resolved)
    if not parent.is_dir():
        raise ValueError(f"{label} does not have a usable parent directory")
    if not os.access(str(parent), os.W_OK):
        raise ValueError(f"{label} is not writable through parent '{parent}'")
    return resolved


# Confirms replacing an existing config before any question is asked, so a long run cannot end in a surprise
def wizard_choose_config_destination(config_path, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    selected = Path(config_path)
    while selected.exists() and not wizard_ask_yes_no(f"Configuration file '{selected}' exists. A timestamped backup is kept. Rebuild it from your answers, starting from its current settings?", False, input_func, destination):
        alternative = wizard_ask_text("Another config destination or leave empty to cancel", input_func=input_func, stream=destination)
        if not alternative:
            return None
        try:
            selected = wizard_validate_destination(alternative, "Configuration destination")
        except ValueError as exc:
            destination.write(f"  {exc}." + "\n")
    return selected


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


# Trims the parenthetical hint from a question, so the retry offer that repeats it stays one readable line
def wizard_retry_label(label):
    return label.split(" (")[0].strip()


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
            destination.write("  Enter a positive duration such as 120, 2m, 1.5h, 1h 30m or 1d." + "\n")
            if not wizard_offer_retry(wizard_retry_label(label), input_func=input_func, stream=destination):
                destination.write(f"  Keeping {wizard_format_duration(default)}.\n")
                return int(default)


# Reads one wizard answer after rendering its prompt to the selected stream
def wizard_read_answer(prompt, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    destination.write(colorize("info", prompt))
    destination.flush()
    try:
        return str(read_interactively(input_func)).strip()
    except (EOFError, KeyboardInterrupt) as exc:
        destination.write("\n")
        raise WizardCancelled from exc


# Reads one hidden wizard answer while forcing debug output off around the secret path
def wizard_read_secret(label, getpass_func=None, stream=None):
    global DEBUG_MODE
    destination = sys.stdout if stream is None else stream
    destination.write(colorize("info", f"{label}: "))
    destination.flush()
    hidden_prompt = getpass.getpass if getpass_func is None else getpass_func
    previous_debug_mode = DEBUG_MODE
    DEBUG_MODE = False
    try:
        return str(read_interactively(hidden_prompt, "")).strip()
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
        destination.write("  Please answer 'y' or 'n'." + "\n")


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
        destination.write(f"  Enter a number between 1 and {len(choices)}." + "\n")


# Reads one text value with a shown default and optional validation
def wizard_ask_text(label, default="", validator=None, input_func=input, stream=None, required=False):
    destination = sys.stdout if stream is None else stream
    shown_default = f" [{default}]" if default not in (None, "") else ""
    while True:
        answer = wizard_read_answer(f"{label}{shown_default}: ", input_func, destination)
        selected = str(default) if not answer else answer
        if required and not selected:
            destination.write("  This value is required.\n")
            if not wizard_offer_retry(label, input_func=input_func, stream=destination):
                return ""
            continue
        if validator is None:
            return selected
        error = validator(selected)
        if not error:
            return selected
        destination.write(f"  That value is not valid: {error}\n")
        if not wizard_offer_retry(label, input_func=input_func, stream=destination):
            return str(default)


# Asks for a whole number inside the accepted range, keeping the saved value when the retry offer is declined
def wizard_ask_positive_int(label, default, maximum=None, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    while True:
        answer = wizard_ask_text(label, str(default), input_func=input_func, stream=destination, required=True)
        # An empty answer means the retry offer was declined, so the default stands instead of asking again
        if not answer:
            return int(default)
        parsed = int(answer) if str(answer).isdigit() else 0
        if parsed > 0 and (maximum is None or parsed <= maximum):
            return parsed
        destination.write(f"  Enter a whole number from 1 through {maximum}.\n" if maximum is not None else "  Enter a positive whole number.\n")
        # A value the helper cannot use is a rejected entry, so it gets the same way out an empty one gets
        if not wizard_offer_retry(wizard_retry_label(label), input_func=input_func, stream=destination):
            destination.write(f"  Keeping {default}.\n")
            return int(default)


# Returns a saved value fit to show as a prompt default, so a shipped placeholder is never offered back
def wizard_default(value):
    text = str(value or "")
    return "" if not text.strip() or text.startswith("your_") else text


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
def build_wizard_state(config_path, dotenv_path, install_context=None, *, env_file_explicit=True):
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
    if not env_file_explicit and existing_values.get("DOTENV_FILE"):
        if str(existing_values["DOTENV_FILE"]).casefold() == "none":
            raise ValueError("Setup needs a writable dotenv destination. Pass --env-file PATH to choose one.")
        selected_dotenv = wizard_validate_destination(existing_values["DOTENV_FILE"], "Dotenv destination")
    if selected_config == selected_dotenv:
        raise ValueError("Configuration and dotenv must use different files")
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
        if name not in secrets and secret_is_set(configured):
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
        destination.write("  That target is not valid. Enter a GitHub username or full profile URL.\n")
        # Leaving the target unset has to be a decision rather than a loop the user can only leave with Ctrl+C
        if not wizard_offer_retry("GitHub username", "Nothing can be monitored until one is set", input_func, destination):
            break
    # A declined target ends the section, so nothing asks about persisting a target that does not exist
    if not state.target:
        destination.write("  No target selected. Nothing can be monitored until one is set. Run --setup again or pass the target on the command line.\n")
        state.values["TARGET_GITHUB_USERNAME"] = ""
        return
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
    destination.write(f"Create or view your GitHub personal access token: {colorize('link', GITHUB_TOKEN_SETTINGS_URL)}\n")
    existing = bool(state.secrets.get("GITHUB_TOKEN") or state.environment_token_available)
    if existing and not wizard_ask_yes_no("Replace the GitHub token already configured?", False, input_func, destination):
        return
    validator = validate_github_token if token_validator is None else token_validator
    while True:
        token = wizard_read_secret("GitHub token", getpass_func, destination)
        if not token:
            # Monitoring cannot run without it, so leaving it unset has to be a decision rather than a fallthrough
            if not wizard_offer_retry("GitHub token", "Nothing can be monitored until one is set", input_func, destination):
                if "GITHUB_TOKEN" in state.baseline_secrets:
                    state.secrets["GITHUB_TOKEN"] = state.baseline_secrets["GITHUB_TOKEN"]
                else:
                    state.secrets.pop("GITHUB_TOKEN", None)
                return
            continue
        destination.write("  Checking the token with GitHub ...\n")
        try:
            login = validator(token, state.values["GITHUB_API_URL"])
        except Exception as exc:
            destination.write(colorize("error", f"  Token validation failed: {sanitize_error_text(exc)}") + "\n")
            # A token GitHub keeps rejecting cannot be corrected from inside the loop, so the wizard must be leavable here too
            if not wizard_offer_retry("GitHub token", input_func=input_func, stream=destination):
                return
            continue
        state.secrets["GITHUB_TOKEN"] = token
        state.authenticated_login = str(login)
        destination.write(f"  GitHub token is valid for user: {colorize('username', state.authenticated_login)}\n")
        return


# Returns one declined section to the built-in template values, so nothing the user turned down is written
def wizard_clear_section(state, config_keys, secret_keys=()):
    defaults = _config_template_defaults()
    for name in config_keys:
        if name in defaults:
            state.values[name] = defaults[name]
        else:
            state.values.pop(name, None)
    for name in secret_keys:
        state.secrets.pop(name, None)


# Switches every email alert off together, so an abandoned answer cannot leave half a mail server configured
def wizard_disable_email(state):
    wizard_clear_section(state, WIZARD_SMTP_CONFIG_KEYS, ("SMTP_PASSWORD",))
    for name in WIZARD_EMAIL_NOTIFICATION_KEYS:
        state.values[name] = False


# Reports which email alerts the current tracking settings can actually produce
def wizard_available_email_alerts(state, prefix=""):
    return {
        f"{prefix}PROFILE_NOTIFICATION": True,
        f"{prefix}EVENT_NOTIFICATION": not state.values["DO_NOT_MONITOR_GITHUB_EVENTS"],
        f"{prefix}REPO_NOTIFICATION": bool(state.values["TRACK_REPOS_CHANGES"]),
        f"{prefix}REPO_UPDATE_DATE_NOTIFICATION": bool(state.values["TRACK_REPOS_CHANGES"]),
        f"{prefix}CONTRIB_NOTIFICATION": bool(state.values["TRACK_CONTRIB_CHANGES"]),
        f"{prefix}ERROR_NOTIFICATION": True,
    }


# Signs in to the collected mail server without sending anything, so a refused login is caught during setup
def wizard_verify_smtp(values, secrets):
    names = WIZARD_SMTP_CONFIG_KEYS + ("SMTP_PASSWORD",)
    previous = {name: globals()[name] for name in names}
    smtp_object = None
    try:
        globals().update({name: values[name] for name in WIZARD_SMTP_CONFIG_KEYS})
        # A password kept from an earlier run is the one the sign-in has to prove
        globals()["SMTP_PASSWORD"] = secrets.get("SMTP_PASSWORD") or previous["SMTP_PASSWORD"]
        smtp_object = smtp_connect_and_login(SMTP_SSL, smtp_timeout=WIZARD_SMTP_TIMEOUT)
        return None
    except Exception as exc:
        return classify_recovery_error(exc, "email")
    finally:
        if smtp_object is not None:
            smtp_quit_quietly(smtp_object)
        globals().update(previous)


# Reports the outcome of the sign-in check: True to continue, False to ask again, None to switch email off
def wizard_smtp_sign_in_accepted(state, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    destination.write("  Checking the sign-in with the mail server ...\n")
    advice = wizard_verify_smtp(state.values, state.secrets)
    if advice is None:
        destination.write("  The mail server accepted the sign-in. No email was sent.\n")
        return True
    destination.write(f"  {advice.summary}: {advice.detail}" if advice.detail else f"  {advice.summary}" + "\n")
    destination.write(f"  To fix: {advice.fix}\n")
    if wizard_offer_retry("mail server settings", input_func=input_func, stream=destination):
        return False
    if advice.retryable:
        # Being offline is the usual reason a correct setup fails here, so the answers are kept rather than discarded
        destination.write("  The settings were kept without being checked. Run --doctor to check the sign-in again.\n")
        return True
    destination.write("  Email notifications stay off until the mail server accepts the settings." + "\n")
    return None


# Collects optional email delivery settings and alert choices
def wizard_collect_email(state, input_func=input, getpass_func=None, stream=None):
    destination = sys.stdout if stream is None else stream
    configured_destination = not str(state.values["SMTP_HOST"]).startswith("your_smtp_server_")
    enabled_default = any(bool(state.values[name]) for name in ("PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION")) or bool(state.values["ERROR_NOTIFICATION"] and configured_destination)
    if not wizard_ask_yes_no("Configure email notifications?", enabled_default, input_func, destination):
        wizard_disable_email(state)
        return
    while True:
        state.values["SMTP_HOST"] = wizard_ask_text("SMTP host", wizard_default(state.values["SMTP_HOST"]), input_func=input_func, stream=destination, required=True)
        state.values["SMTP_PORT"] = wizard_ask_positive_int("SMTP port", state.values["SMTP_PORT"], maximum=65535, input_func=input_func, stream=destination)
        state.values["SMTP_SSL"] = wizard_ask_yes_no("Enable TLS/SSL for SMTP?", bool(state.values["SMTP_SSL"]), input_func, destination)
        state.values["SMTP_USER"] = wizard_ask_text("SMTP username", wizard_default(state.values["SMTP_USER"]), input_func=input_func, stream=destination, required=True)
        state.values["SENDER_EMAIL"] = wizard_ask_text("Sender email", wizard_default(state.values["SENDER_EMAIL"]), input_func=input_func, stream=destination, required=True)
        state.values["RECEIVER_EMAIL"] = wizard_ask_text("Receiver email", wizard_default(state.values["RECEIVER_EMAIL"]), input_func=input_func, stream=destination, required=True)
        # A blank answer keeps the password already saved in the dotenv file
        password = wizard_read_secret("SMTP password", getpass_func, destination)
        if password:
            state.secrets["SMTP_PASSWORD"] = password
        validation_error = wizard_email_settings_error(state.values, state.secrets)
        if validation_error:
            destination.write(f"  Email settings are incomplete: {validation_error}" + "\n")
            if wizard_offer_retry("mail server settings", input_func=input_func, stream=destination):
                continue
            destination.write("  Email notifications stay off until every mail server setting is answered." + "\n")
            wizard_disable_email(state)
            return
        outcome = wizard_smtp_sign_in_accepted(state, input_func, destination)
        if outcome is None:
            wizard_disable_email(state)
            return
        if outcome:
            break
    available = wizard_available_email_alerts(state)
    preset = wizard_ask_choice("Which email notifications should be enabled?", (
        ("recommended", "Status and errors, recommended", "Profile changes, new GitHub events and monitoring errors."),
        ("all", "Every supported event", "Enables every email notification the tracking settings allow."),
        ("custom", "Custom", "Choose each notification type separately."),
    ), "recommended", input_func, destination)
    if preset == "custom":
        destination.write("\n")
        questions = (
            ("PROFILE_NOTIFICATION", "Email on profile changes?"),
            ("EVENT_NOTIFICATION", "Email on new GitHub events?"),
            ("REPO_NOTIFICATION", "Email on detailed repository changes?"),
            ("REPO_UPDATE_DATE_NOTIFICATION", "Email on repository update date changes?"),
            ("CONTRIB_NOTIFICATION", "Email on daily contribution changes?"),
            ("ERROR_NOTIFICATION", "Email monitoring errors?"),
        )
        for name, question in questions:
            state.values[name] = available[name] and wizard_ask_yes_no(question, False, input_func, destination)
        return
    recommended = ("PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "ERROR_NOTIFICATION")
    for name, usable in available.items():
        state.values[name] = usable and (preset == "all" or name in recommended)


# Switches the channel and every alert it owns off together, so a half-configured webhook cannot be written
def wizard_disable_webhook(state):
    wizard_clear_section(state, ("WEBHOOK_PROVIDER",), ("WEBHOOK_URL", "NTFY_ACCESS_TOKEN"))
    state.values["WEBHOOK_ENABLED"] = False
    for name in WIZARD_SECTION_KEYS["Webhook"]:
        if name.endswith("_NOTIFICATION"):
            state.values[name] = False


# Collects an optional ntfy access token without displaying or contacting the service
def wizard_collect_ntfy_access_token(state, input_func=input, getpass_func=None, stream=None):
    destination = sys.stdout if stream is None else stream
    if state.secrets.get("NTFY_ACCESS_TOKEN"):
        choice = wizard_ask_choice("Which ntfy authentication should be used?", (
            ("keep", "Keep the saved access token", "Keeps the private value without displaying or changing it."),
            ("replace", "Paste a new access token", "Uses a hidden prompt then saves the replacement in .env."),
            ("remove", "Do not use an access token", "Disables the saved token. Authentication in the topic URL still works."),
        ), "keep", input_func, destination)
        if choice == "keep":
            return
        if choice == "remove":
            state.secrets["NTFY_ACCESS_TOKEN"] = ""
            destination.write("  The saved ntfy access token will be disabled without being displayed.\n")
            return
    elif not wizard_ask_yes_no("Authenticate this ntfy topic with a separate access token?", False, input_func, destination):
        destination.write("  No separate access token selected. Authentication already present in the topic URL still works.\n")
        return
    while True:
        access_token = wizard_read_secret("Paste the ntfy access token only", getpass_func, destination)
        if not access_token or ("\r" not in access_token and "\n" not in access_token and not access_token.casefold().startswith(("bearer ", "basic "))):
            if access_token:
                state.secrets["NTFY_ACCESS_TOKEN"] = access_token
            return
        destination.write("  Paste only the access token without a Bearer or Basic prefix." + "\n")
        if not wizard_offer_retry("ntfy access token", input_func=input_func, stream=destination):
            return


# Collects optional Discord or ntfy delivery settings and alert choices
def wizard_collect_webhook(state, input_func=input, getpass_func=None, stream=None):
    destination = sys.stdout if stream is None else stream
    if not wizard_ask_yes_no("Set up webhook alerts (Discord, ntfy etc.)?", bool(state.values["WEBHOOK_ENABLED"]), input_func, destination):
        wizard_disable_webhook(state)
        return
    provider = wizard_ask_choice("Which webhook service should receive alerts?", (
        ("discord", "Discord", "Sends a Discord embed to one channel webhook."),
        ("ntfy", "ntfy", "Sends a native notification to one ntfy topic URL."),
    ), normalized_webhook_provider(state.values["WEBHOOK_PROVIDER"]) or "discord", input_func, destination)
    state.values["WEBHOOK_PROVIDER"] = provider
    if provider == "discord":
        destination.write("  In Discord: Edit Channel > Integrations > Webhooks > New Webhook > Copy Webhook URL.\n")
    else:
        destination.write("  In ntfy: choose a hard-to-guess topic. Paste its complete topic URL, or just the topic name when it is hosted on ntfy.sh.\n")
    replace_webhook = True
    if state.secrets.get("WEBHOOK_URL"):
        replace_webhook = wizard_ask_choice("Which webhook URL should be used?", (
            ("keep", "Keep the saved URL", "Keeps the private value without displaying or changing it."),
            ("replace", "Paste a new URL", "Uses a hidden prompt then saves the new private value in .env."),
        ), "keep", input_func, destination) == "replace"
    if replace_webhook:
        while True:
            entered = wizard_read_secret("Paste the Discord webhook URL" if provider == "discord" else "Paste the ntfy topic URL or ntfy.sh topic name", getpass_func, destination)
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
            if provider == "ntfy":
                destination.write("  Enter a complete HTTPS ntfy topic URL or a topic name containing up to 64 letters, numbers, dashes or underscores." + "\n")
            else:
                destination.write("  That does not look like a complete HTTPS webhook URL. Copy it from the webhook service and try again." + "\n")
            if not wizard_offer_retry("webhook URL", input_func=input_func, stream=destination):
                break
    if provider == "ntfy":
        wizard_collect_ntfy_access_token(state, input_func, getpass_func, destination)
    if not state.secrets.get("WEBHOOK_URL"):
        wizard_disable_webhook(state)
        destination.write("  Webhook alerts will stay disabled until a destination is saved." + "\n")
        return
    state.values["WEBHOOK_ENABLED"] = True
    available = wizard_available_email_alerts(state, "WEBHOOK_")
    preset = wizard_ask_choice("Which webhook alerts should be sent?", (
        ("recommended", "Status and errors, recommended", "Profile changes, new GitHub events and monitoring errors."),
        ("all", "Every supported alert", "Enables every webhook alert the tracking settings allow."),
        ("custom", "Custom", "Choose each webhook alert separately."),
    ), "recommended", input_func, destination)
    if preset == "custom":
        destination.write("\n")
        questions = (
            ("WEBHOOK_PROFILE_NOTIFICATION", "Send a webhook alert on profile changes?"),
            ("WEBHOOK_EVENT_NOTIFICATION", "Send a webhook alert on new GitHub events?"),
            ("WEBHOOK_REPO_NOTIFICATION", "Send a webhook alert on detailed repository changes?"),
            ("WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION", "Send a webhook alert on repository update date changes?"),
            ("WEBHOOK_CONTRIB_NOTIFICATION", "Send a webhook alert on daily contribution changes?"),
            ("WEBHOOK_ERROR_NOTIFICATION", "Send a webhook alert on monitoring errors?"),
        )
        for name, question in questions:
            state.values[name] = available[name] and wizard_ask_yes_no(question, False, input_func, destination)
        return
    recommended = ("WEBHOOK_PROFILE_NOTIFICATION", "WEBHOOK_EVENT_NOTIFICATION", "WEBHOOK_ERROR_NOTIFICATION")
    for name, usable in available.items():
        state.values[name] = usable and (preset == "all" or name in recommended)


# Adds the .csv extension when the answer carries none, so a bare name still names a CSV file
def wizard_normalize_csv_path(answer):
    text = str(answer).strip()
    if not text or Path(text).suffix:
        return text
    return text + ".csv"


# Collects log and CSV output destinations
def wizard_collect_destinations(state, input_func=input, stream=None):
    destination = sys.stdout if stream is None else stream
    state.values["DISABLE_LOGGING"] = not wizard_ask_yes_no("Write the normal per-target log file?", not bool(state.values["DISABLE_LOGGING"]), input_func, destination)
    csv_default = str(state.values["CSV_FILE"] or "")
    # Asked as its own question, since Enter on the path prompt takes the shown default and so could never clear a saved one
    if wizard_ask_yes_no("Write a CSV file of the changes?", bool(csv_default), input_func, destination):
        state.values["CSV_FILE"] = wizard_normalize_csv_path(wizard_ask_text("CSV output path", csv_default, input_func=input_func, stream=destination, required=True))
    else:
        state.values["CSV_FILE"] = ""
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


# Returns a validation error when one answered setup destination cannot be written
def wizard_destination_error(value, label):
    try:
        wizard_validate_destination(value, label)
    except ValueError as exc:
        return str(exc)
    return ""


# Changes where setup writes, re-asking the sections that hold secrets when the dotenv destination moves
def wizard_collect_file_destinations(state, input_func=input, getpass_func=None, stream=None, token_validator=None):
    destination = sys.stdout if stream is None else stream
    config_text = wizard_ask_text("Configuration file destination", str(state.config_path), lambda value: wizard_destination_error(value, "Configuration destination"), input_func, destination, required=True)
    selected_config = wizard_validate_destination(config_text, "Configuration destination")
    if selected_config != state.config_path:
        chosen_config = wizard_choose_config_destination(selected_config, input_func, destination)
        # Giving up on every offered path keeps the current destination rather than cancelling the whole setup
        if chosen_config is not None:
            state.config_path = chosen_config
    while True:
        env_text = wizard_ask_text("Dotenv file destination", str(state.dotenv_path), lambda value: wizard_destination_error(value, "Dotenv destination"), input_func, destination, required=True)
        if env_text.casefold() == "none":
            destination.write("  Setup needs a writable dotenv file and cannot use 'none'." + "\n")
            continue
        selected_env = wizard_validate_destination(env_text, "Dotenv destination")
        # One file cannot hold both, since saving the configuration would overwrite the secrets beside it
        if selected_env == state.config_path:
            destination.write("  The dotenv file has to be a different file from the configuration." + "\n")
            continue
        break
    state.values["DOTENV_FILE"] = str(selected_env)
    if selected_env == state.dotenv_path:
        return
    state.dotenv_path = selected_env
    # A secret kept rather than retyped was never queued, so it would be missing from a dotenv file that just moved
    destination.write(colorize("info", "  The dotenv destination changed. Re-enter authentication and notification settings that may contain secrets.") + "\n")
    wizard_collect_authentication(state, input_func, getpass_func, destination, token_validator)
    destination.write("\n")
    wizard_collect_email(state, input_func, getpass_func, destination)
    destination.write("\n")
    wizard_collect_webhook(state, input_func, getpass_func, destination)


# Recollects one selected section while preserving every other answer
def wizard_edit_section(state, input_func=input, getpass_func=None, stream=None, token_validator=None):
    destination = sys.stdout if stream is None else stream
    sections = (
        ("Target", "Target", "Change the GitHub profile that is monitored and the monitoring feature choices."),
        ("Polling", "Polling interval", "Change how often GitHub is checked."),
        ("Authentication", "Authentication", "Change GitHub endpoints or the access token."),
        ("Email", "Email notifications", "Change SMTP details and email events."),
        ("Webhook", "Webhook alerts", "Change Discord or ntfy details and events."),
        ("Destinations", "Output files", "Change log and CSV output settings."),
        ("FileDestinations", "File destinations", "Change the configuration or dotenv output path."),
        ("return", "Return to summary", "Keep every current answer."),
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
        "FileDestinations": lambda: wizard_collect_file_destinations(state, input_func, getpass_func, destination, token_validator),
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


# Renders an explicit assignment for a setting the template ships commented out, so overrides the user wrote
# survive a rewrite instead of being replaced by the commented default
def _rendered_commented_setting(variable, values):
    value = values.get(variable)
    if not isinstance(value, dict) or not value:
        return []
    lines = ["", f"{variable} = {{"]
    lines.extend(f"    {repr(str(name))}: {repr(str(setting))}," for name, setting in value.items())
    lines.append("}")
    return lines


# Renders one configuration file from the built-in template with the chosen values substituted in
def generate_config_with_current_values(config_values):
    tree = ast.parse(CONFIG_BLOCK, "<built-in-config>", "exec")
    template_defaults = _config_template_defaults()
    replacements = {}
    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            continue
        name = statement.targets[0].id
        # A secret belongs in the dotenv file, so its template placeholder stays even when the running values hold the real one
        if name not in config_values or name in SECRET_KEYS:
            continue
        # A setting still holding what the template ships keeps the template's own lines, so a multi-line
        # value such as WEBHOOK_TEMPLATE is not collapsed into one unreadable line by a wizard that changed nothing
        if name in template_defaults and config_values[name] == template_defaults[name] and type(config_values[name]) is type(template_defaults[name]):
            continue
        replacements[name] = (statement.lineno, getattr(statement, "end_lineno", statement.lineno), repr(config_values[name]))
    lines = CONFIG_BLOCK.strip("\n").split("\n")
    # The template keeps its own leading blank line, so template line numbers are one ahead of this list
    offset = 1 if CONFIG_BLOCK.startswith("\n") else 0
    commented_pattern = re.compile(r"^#\s*([A-Z][A-Z0-9_]*)\s*=\s*\{$")
    commented_block = ""
    skip_until = 0
    output = []
    for number, line in enumerate(lines, 1):
        template_line = number + offset
        if template_line < skip_until:
            continue
        replaced = next((name for name, (start, _end, _value) in replacements.items() if start == template_line), None)
        if replaced is None:
            output.append(line)
            stripped = line.strip()
            commented_match = commented_pattern.match(stripped)
            if commented_match and commented_match.group(1) in COMMENTED_CONFIG_SETTINGS:
                commented_block = commented_match.group(1)
            elif commented_block and stripped == "# }":
                output.extend(_rendered_commented_setting(commented_block, config_values))
                commented_block = ""
            continue
        start, end, rendered = replacements[replaced]
        output.append(f"{replaced} = {rendered}")
        skip_until = end + 1
    return "\n".join(output) + "\n"


# Renders the configuration the wizard writes: the shipped template with the chosen and preserved values substituted in
def render_wizard_config(state):
    selected = dict(state.preserved_values)
    for name in WIZARD_CONFIG_ORDER:
        selected[name] = state.values[name]
    selected["DOTENV_FILE"] = str(state.dotenv_path)
    content = generate_config_with_current_values(selected)
    validate_config_content(content, str(state.config_path))
    return content


# Updates selected dotenv assignments in memory while preserving unrelated lines
def render_wizard_dotenv(state):
    existing = state.dotenv_path.read_text(encoding="utf-8") if state.dotenv_path.exists() else ""
    updates = {key: value for key, value in state.secrets.items() if key in SECRET_KEYS}
    return render_private_settings(existing, updates)


# Copies an existing file to a timestamped owner-only .bak beside it, returning the backup path or None when there was nothing to copy
def create_timestamped_backup(destination, attempts=100):
    destination_path = Path(destination).expanduser()
    if not destination_path.is_file():
        return None
    existing_bytes = destination_path.read_bytes()
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for attempt in range(attempts):
        suffix = f".{stamp}.bak" if attempt == 0 else f".{stamp}-{attempt}.bak"
        backup_path = destination_path.with_name(destination_path.name + suffix)
        try:
            # O_EXCL so a backup can never overwrite an earlier one, even under a concurrent run
            descriptor = os.open(str(backup_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            continue
        try:
            with os.fdopen(descriptor, "wb") as backup_file:
                backup_file.write(existing_bytes)
                backup_file.flush()
                os.fsync(backup_file.fileno())
        except Exception as exc:
            debug_print("Backup write", path=str(backup_path), outcome="failed", error=f"{type(exc).__name__}: {exc}")
            try:
                os.unlink(str(backup_path))
            except OSError:
                pass
            raise
        return str(backup_path)
    raise OSError(f"Could not create a unique backup for '{destination_path}' after {attempts} attempts")


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


# Raised when an existing config is not replaced because nobody could confirm it, as opposed to a path in the way of writing one
class ConfigExistsError(FileExistsError):
    pass


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
        raise ConfigExistsError(f"Config file '{destination}' already exists. Re-run with --force to replace it after a timestamped backup.")
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
    backup_path = create_timestamped_backup(destination) if destination.exists() else None
    if backup_path is not None:
        debug_print("Generated configuration backup written", path=backup_path)
    temporary_path = prepare_wizard_atomic_file(destination, content)
    try:
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    return backup_path, True


# Saves both wizard files only after validation, the configuration backup and temporary writes succeed
def save_wizard_files(state):
    for path in (state.config_path, state.dotenv_path):
        if not path.parent.is_dir():
            raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    config_content = render_wizard_config(state)
    dotenv_content = render_wizard_dotenv(state)
    # Only the configuration is backed up: a copy of the credentials being replaced is the one thing not worth keeping
    config_backup = create_timestamped_backup(state.config_path)
    # A dotenv with nothing in it is noise beside the config, so an empty one is never created
    destinations = [(state.config_path, config_content)]
    if dotenv_content.strip() or state.dotenv_path.exists():
        destinations.append((state.dotenv_path, dotenv_content))
    prepared = []
    try:
        # Appended one at a time so a failure on the second file still exposes the first for cleanup
        for path, content in destinations:
            prepared.append(prepare_wizard_atomic_file(path, content))
        for (path, _), temporary_path in zip(destinations, prepared, strict=True):
            os.replace(temporary_path, path)
            os.chmod(path, 0o600)
    finally:
        for temporary_path in prepared:
            temporary_path.unlink(missing_ok=True)
    for path, _ in destinations:
        debug_print("Setup file write succeeded", path=path)
    return config_backup


# Builds the exact install-aware argument list used after setup
def wizard_monitor_arguments(state):
    arguments = [] if state.persist_target else [state.target]
    # A dotenv nothing was written to does not exist, so naming it would point the command at a missing file
    dotenv_arguments = ["--env-file", str(state.dotenv_path)] if state.dotenv_path.exists() else []
    return [*arguments, "--config-file", str(state.config_path), *dotenv_arguments]


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
        destination.write(colorize("header", "Setup Wizard\n") + "\n")
        destination.write("The setup wizard needs an interactive terminal (TTY).\n")
        destination.write("Run --setup from an interactive shell or use --generate-config and edit the files manually.\n")
        destination.write(f"Guide: {QUICK_START_GUIDE_URL}\n")
        return 1
    try:
        selected_config = wizard_validate_destination(selected_config, "Configuration destination")
        selected_dotenv = wizard_validate_destination(selected_dotenv, "Dotenv destination")
    except ValueError as exc:
        destination.write(apply_color_to_text(render_recovery_advice(classify_recovery_error(exc, "config"))) + "\n")
        return 1
    try:
        state = build_wizard_state(selected_config, selected_dotenv, context, env_file_explicit=env_file is not None)
        destination.write(colorize("header", "Setup Wizard\n") + "\n")
        destination.write("This asks a few questions and writes a ready-to-run configuration.\n")
        destination.write("Press Enter to accept the shown default. Ctrl+C cancels.\n\n")
        destination.write("Secrets go to the dotenv file. Non-secret settings go to the config file.\n\n")
        _wizard_print_setup_destinations(destination, context, state)
        destination.write("\n")
        # Asked before anything else, so a config that has to be replaced is agreed to rather than discovered at Save
        chosen_config = wizard_choose_config_destination(state.config_path, input_func, destination)
        if chosen_config is None:
            destination.write("\n" + colorize("warning", "Setup cancelled. Destination files were not changed.") + "\n")
            return 1
        if chosen_config != state.config_path:
            state = build_wizard_state(chosen_config, selected_dotenv, context, env_file_explicit=env_file is not None)
            destination.write("\n")
        wizard_collect_all(state, input_func, getpass_func, destination, token_validator)
        if not wizard_review_setup(state, input_func, getpass_func, destination, token_validator):
            destination.write("\n" + colorize("warning", "Setup cancelled. Destination files were not changed.") + "\n")
            return 1
        config_backup = save_wizard_files(state)
    except WizardCancelled:
        destination.write(colorize("warning", "Setup cancelled. Destination files were not changed.") + "\n")
        return 1
    except Exception as exc:
        advice = classify_recovery_error(exc, "config")
        destination.write("\n")
        destination.write(apply_color_to_text(render_recovery_advice(advice)) + "\n")
        return 1
    saved_rows = [("Configuration:", state.config_path)]
    if config_backup is not None:
        saved_rows.append(("Backup:", Path(config_backup)))
    if state.dotenv_path.exists():
        saved_rows.append(("Secrets:" if state.secrets else "Dotenv:", state.dotenv_path))
    saved_width = max(len(label) for label, _ in saved_rows) + 1
    _wizard_heading(destination, "Saved files", "header")
    for label, path in saved_rows:
        destination.write(f"  {label:<{saved_width}}{path}\n")
    monitor_arguments = wizard_monitor_arguments(state)
    doctor_arguments = ["--doctor", *monitor_arguments]
    doctor_exit = None
    try:
        # The doctor's FAIL row is the most useful thing a user with a missing credential can see
        if state.target:
            destination.write("\n")
            if wizard_ask_yes_no("Run doctor now? It writes no files and offers real delivery tests only with separate approval.", True, input_func, destination):
                destination.write("\n")
                doctor_args = parser.parse_args(doctor_arguments)
                runner = run_doctor if doctor_runner is None else doctor_runner
                doctor_exit = runner(doctor_args, parser, input_func=input_func, input_stream=source, stream=destination, show_banner=False)
    except WizardCancelled:
        destination.write(colorize("warning", "Setup is saved. Use the commands below when ready.") + "\n")
    _wizard_heading(destination, "Next steps", "header")
    _wizard_print_command(destination, "Check setup again:", render_command(doctor_arguments, install_context=context, include_paths=False))
    start_label = "After Doctor passes, start monitoring:" if doctor_exit not in (None, 0) else "Start monitoring:"
    _wizard_print_command(destination, start_label, render_command(monitor_arguments, install_context=context, include_paths=False))
    destination.write(f"Guide: {colorize('link', QUICK_START_GUIDE_URL)}\n")
    if doctor_exit == 0:
        try:
            start_now = wizard_ask_yes_no("Start monitoring now? Monitoring will continue until Ctrl+C.", True, input_func, destination)
        except WizardCancelled:
            start_now = False
            destination.write(colorize("warning", "Setup is saved. Start monitoring with the command above when ready.") + "\n")
        if start_now:
            launcher = launch_wizard_monitoring if monitor_launcher is None else monitor_launcher
            return int(launcher(monitor_arguments) or 0)
    return 0


# Prints the sibling-style first-run actions and optionally launches guided setup
def print_welcome_screen(parser, input_func=input, input_stream=None, stream=None, install_context=None, setup_runner=None, show_banner=True):
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
    prefix = render_command([], install_context=context, include_paths=False)
    destination.write("For <github_target>, use a GitHub username or complete profile URL.\n\n")
    _wizard_print_command(destination, "Quickest start (already configured):", f"{prefix} <github_target>")
    setup_suffix = "   (or just answer Y below)" if interactive else ""
    _wizard_print_command(destination, "Easiest start (guided setup wizard):", f"{prefix} --setup", setup_suffix)
    _wizard_print_command(destination, "Check setup before monitoring:", f"{prefix} --doctor <github_target>")
    destination.write(f"Full options: {colorize('section', prefix + ' --help')}\n")
    destination.write(f"\nGuide:        {colorize('link', QUICK_START_GUIDE_URL)}\n\n")
    if not interactive:
        return 1
    try:
        start_setup = wizard_ask_yes_no("Run the guided setup wizard now?", True, input_func, destination)
    except WizardCancelled:
        destination.write(colorize("warning", "Setup cancelled.") + "\n")
        return 1
    if not start_setup:
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
    global CLI_CONFIG_PATH, CONFIG_DISCOVERY_DISABLED, DOTENV_FILE, LOCAL_TIMEZONE, LIVENESS_REMINDER_SECONDS, GITHUB_TOKEN, GITHUB_API_URL, CSV_FILE, DISABLE_LOGGING, GITHUB_LOGFILE, PROFILE_NOTIFICATION, EVENT_NOTIFICATION, REPO_NOTIFICATION, REPO_UPDATE_DATE_NOTIFICATION, ERROR_NOTIFICATION, GITHUB_CHECK_INTERVAL, SMTP_PASSWORD, stdout_bck, DO_NOT_MONITOR_GITHUB_EVENTS, TRACK_REPOS_CHANGES, REPOS_TO_MONITOR, GET_ALL_REPOS, CONTRIB_NOTIFICATION, TRACK_CONTRIB_CHANGES, WEBHOOK_REPO_NOTIFICATION, WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION, WEBHOOK_CONTRIB_NOTIFICATION, WEBHOOK_EVENT_NOTIFICATION, VERBOSE_MODE, DEBUG_MODE, COLORED_OUTPUT, TRUNCATE_CHARS, TARGET_GITHUB_USERNAME, WEBHOOK_ENABLED

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
        except ConfigExistsError as exc:
            advice = make_recovery_advice("file.exists", "The generated configuration would replace an existing file", recovery_fix_with_guide(str(exc), CONFIG_GUIDE_URL), False, f"{type(exc).__name__}: {exc}")
            print_recovery_advice(advice)
            sys.exit(1)
        except OSError as exc:
            debug_print("Generated configuration write", path=locals().get('output_file', '<unknown>'), outcome="failed", error=f"{type(exc).__name__}: {exc}")
            advice = make_recovery_advice("file.unwritable", "The generated configuration could not be written", recovery_fix_with_guide("Check the destination path and file permissions", CONFIG_GUIDE_URL), False, f"{type(exc).__name__}: {exc}")
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

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if CLEAR_SCREEN and DEBUG_MODE:
        debug_print("Terminal screen clear skipped because debug mode is active")
    clear_screen(CLEAR_SCREEN and not keep_terminal_history() and not DEBUG_MODE)
    print_startup_banner()

    parser = ColoredHelpParser(
        prog="github_monitor",
        description=(f"Monitor a GitHub user's profile and activity with customizable email or webhook alerts [ {PROJECT_URL}/ ]"), formatter_class=argparse.RawTextHelpFormatter,
        epilog=help_examples(), **argparse_color_kwargs()
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
        help="Location of the optional config file (auto-search if not set, disable with 'none')",
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
        help="Run the guided setup and write a ready-to-run configuration",
    )
    conf.add_argument(
        "--env-file",
        dest="env_file",
        metavar="PATH",
        help="Path to optional dotenv file (auto-search if not set, disable with 'none')",
    )
    conf.add_argument(
        "--set-github-token",
        dest="set_github_token",
        action="store_true",
        help="Validate and save a GitHub token through a hidden prompt",
    )
    conf.add_argument(
        "--set-smtp-password",
        dest="set_smtp_password",
        action="store_true",
        help="Enter the SMTP password privately, check it against the mail server and save it to the dotenv file",
    )
    conf.add_argument(
        "--set-webhook-url",
        dest="set_webhook_url",
        action="store_true",
        help="Save a Discord or ntfy webhook URL through a hidden prompt",
    )
    conf.add_argument(
        "--doctor",
        dest="doctor",
        action="store_true",
        help="Run read-only preflight checks and report what is ready and what is not",
    )

    # API settings
    creds = parser.add_argument_group("API settings")
    creds.add_argument(
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
    notify = parser.add_argument_group("Email notifications")
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
    listing = parser.add_argument_group("User information & listing")
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
        if isinstance(args.config_file, str) and args.config_file.casefold() == "none":
            print_recovery_advice(make_recovery_advice("file.unwritable", "--setup has nowhere to write the configuration", recovery_fix_with_guide(f"Replace '--config-file none' with a writable path, or drop the flag to write {DEFAULT_CONFIG_FILENAME} in the current directory", CONFIG_GUIDE_URL), False))
            sys.exit(1)
        if isinstance(args.env_file, str) and args.env_file.casefold() == "none":
            print_recovery_advice(make_recovery_advice("file.unwritable", "--setup has nowhere to write the private settings", recovery_fix_with_guide("Replace '--env-file none' with a writable path, or drop the flag to write .env in the current directory", SECRETS_GUIDE_URL), False))
            sys.exit(1)
        sys.exit(run_setup_wizard(parser, args.config_file, args.env_file, show_banner=False))

    if args.set_github_token and args.github_token:
        parser.error("--set-github-token cannot be combined with -t/--github-token")

    selected_secret_actions = [flag for flag, selected in (("--set-github-token", args.set_github_token), ("--set-smtp-password", args.set_smtp_password), ("--set-webhook-url", args.set_webhook_url)) if selected]
    if len(selected_secret_actions) > 1:
        parser.error(f"{selected_secret_actions[0]} cannot be combined with {selected_secret_actions[1]}")

    # Reached only when --generate-config did not already handle and exit, so --force would do nothing here
    if args.force:
        parser.error("--force only applies to --generate-config with a filename")

    apply_diagnostic_cli_overrides(args)

    if args.doctor:
        incompatible = (args.setup, args.generate_config, args.set_github_token, args.set_smtp_password, args.set_webhook_url, args.send_test_email, args.send_test_webhook, args.list_repos, args.list_starred_repos, args.list_followers_and_followings, args.list_recent_events)
        if any(incompatible):
            parser.error("--doctor cannot be combined with setup, listing or one-shot delivery commands")
        doctor_exit = run_doctor(args, parser, show_banner=False)
        print_doctor_next_steps(terminal_surface_stream(sys.stdout), args.username, TARGET_GITHUB_USERNAME, doctor_exit)
        sys.exit(doctor_exit)

    CONFIG_DISCOVERY_DISABLED = isinstance(args.config_file, str) and args.config_file.casefold() == "none"
    if args.config_file and not CONFIG_DISCOVERY_DISABLED:
        CLI_CONFIG_PATH = os.path.expanduser(args.config_file)
    elif CONFIG_DISCOVERY_DISABLED:
        CLI_CONFIG_PATH = None

    cfg_path = None if CONFIG_DISCOVERY_DISABLED else find_config_file(CLI_CONFIG_PATH)
    configured_settings = set()

    if not cfg_path and CLI_CONFIG_PATH:
        config_command = render_command(["--generate-config", "github_monitor.conf"], include_paths=False)
        advice = make_recovery_advice("config.missing", f"Config file '{CLI_CONFIG_PATH}' does not exist", recovery_fix_with_guide(f"Correct --config-file or generate a new configuration with: {config_command}", CONFIG_GUIDE_URL), False, f"FileNotFoundError: {CLI_CONFIG_PATH}")
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
            advice = make_recovery_advice("config.value_invalid", "The saved GitHub target is invalid", recovery_fix_with_guide("Set TARGET_GITHUB_USERNAME to a GitHub username or complete profile URL", CONFIG_GUIDE_URL), False, f"Rejected target: {TARGET_GITHUB_USERNAME}")
            print_recovery_advice(advice)
            sys.exit(1)
        args.username = saved_target

    if len(sys.argv) == 1 and not args.username:
        sys.exit(print_welcome_screen(parser, show_banner=False))

    if args.set_github_token:
        try:
            run_set_github_token(args.env_file, api_url=args.github_url, config_path=cfg_path)
        except Exception as e:
            print_recovery_error(e, "github_token")
            sys.exit(1)
        sys.exit(0)

    if args.set_smtp_password:
        # Runs after the config file so the mail server it signs in to is the one monitoring would use
        try:
            run_set_smtp_password(args.env_file, config_path=cfg_path)
        except Exception as e:
            print_recovery_error(e, "email")
            sys.exit(1)
        sys.exit(0)

    if args.set_webhook_url:
        try:
            run_set_webhook_url(args.env_file, config_path=cfg_path)
        except Exception as e:
            print_recovery_error(e, "webhook")
            sys.exit(1)
        sys.exit(0)

    apply_webhook_cli_overrides(args, parser)
    trace_unresolved_secrets()
    apply_monitoring_cli_overrides(args, parser)

    try:
        TRUNCATE_CHARS = resolve_truncate_chars(args.truncate, TRUNCATE_CHARS, DISABLE_LOGGING)
    except OSError as exc:
        print_recovery_error(exc, "terminal")
        sys.exit(1)

    if type(GITHUB_CHECK_INTERVAL) is not int or GITHUB_CHECK_INTERVAL <= 0:
        advice = make_recovery_advice("config.value_invalid", "The GitHub polling interval is invalid", recovery_fix_with_guide("Set GITHUB_CHECK_INTERVAL or --check-interval to a positive number of seconds", CONFIG_GUIDE_URL), False, f"GITHUB_CHECK_INTERVAL={GITHUB_CHECK_INTERVAL}")
        print_recovery_advice(advice)
        sys.exit(1)

    timezone_advice = resolve_local_timezone()
    if timezone_advice is not None:
        print_recovery_advice(timezone_advice)
        sys.exit(1)

    if not check_internet():
        sys.exit(1)

    if args.send_test_email:
        # Checked before the attempt is announced, so a mail server that was never usable is not reported as a failed send
        validation_error = validate_email_settings()
        if validation_error is not None:
            print_recovery_advice(email_settings_advice(validation_error))
            sys.exit(1)
        print("* Sending test email notification ...\n")
        if send_email("github_monitor: test email", "This test email was sent by --send-test-email. Your SMTP settings work.", "", SMTP_SSL, smtp_timeout=5) == 0:
            print("* Email sent successfully !")
        else:
            sys.exit(1)
        sys.exit(0)

    if args.send_test_webhook:
        if not validate_webhook_url():
            print_webhook_error("WEBHOOK_URL must contain a complete HTTPS link")
            sys.exit(1)
        print("* Sending test webhook notification ...\n")
        if send_webhook("github_monitor: test webhook", "This test notification was sent by --send-test-webhook. Your webhook settings work.", "event", force=True) == 0:
            print("* Webhook sent successfully !")
        else:
            sys.exit(1)
        sys.exit(0)

    # Checked before the token, so a first run is told the simplest missing thing first
    if not args.username:
        advice = make_recovery_advice("target.missing", "No GitHub username was provided", recovery_fix_with_guide("Add the GitHub username to the monitoring command", QUICK_START_GUIDE_URL), False, "The positional GITHUB_USERNAME argument was empty")
        print_recovery_advice(advice)
        sys.exit(1)

    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_classic_personal_access_token":
        token_command = render_command(["--set-github-token"])
        advice = make_recovery_advice("auth.github_token_missing", "No usable GitHub token is configured", recovery_fix_with_guide(f"Create a token then run: {token_command}", AUTH_GUIDE_URL), False, "GITHUB_TOKEN is empty or still uses the generated placeholder")
        print_recovery_advice(advice)
        sys.exit(1)

    if not GITHUB_API_URL:
        advice = make_recovery_advice("config.value_invalid", "GITHUB_API_URL is empty", recovery_fix_with_guide("Set GITHUB_API_URL in config or pass --github-url with a complete HTTPS API URL", CONFIG_GUIDE_URL), False, "The effective GITHUB_API_URL was empty")
        print_recovery_advice(advice)
        sys.exit(1)

    if args.list_followers_and_followings:
        try:
            github_print_followers_and_followings(args.username)
        except Exception as e:
            print_recovery_error(e, "target")
            sys.exit(1)
        sys.exit(0)

    if args.list_repos:
        try:
            github_print_repos(args.username)
        except Exception as e:
            print_recovery_error(e, "target")
            sys.exit(1)
        sys.exit(0)

    if args.list_starred_repos:
        try:
            github_print_starred_repos(args.username)
        except Exception as e:
            print_recovery_error(e, "target")
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
                advice = make_recovery_advice("file.unwritable", "The CSV file cannot be opened for writing", recovery_fix_with_guide("Check CSV_FILE and its parent directory permissions", CSV_GUIDE_URL), False, f"{type(e).__name__}: {e}")
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
            print_recovery_error(e, "target")
            sys.exit(1)
        sys.exit(0)

    try:
        ascii_log_separators_enabled()
    except ValueError as e:
        advice = make_recovery_advice("config.value_invalid", "ASCII_LOG_SEPARATORS is invalid", recovery_fix_with_guide("Set ASCII_LOG_SEPARATORS to Auto, On or Off", CONFIG_GUIDE_URL), False, f"{type(e).__name__}: {e}")
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
            advice = make_recovery_advice("file.unwritable", "The output log could not be opened", recovery_fix_with_guide("Check GITHUB_LOGFILE and its parent directory permissions or use --disable-logging", CONFIG_GUIDE_URL), False, f"{type(e).__name__}: {e}")
            print_recovery_advice(advice)
            sys.exit(1)
    else:
        FINAL_LOG_PATH = None

    if SMTP_HOST.startswith("your_smtp_server_"):
        verbose_print("Email notifications are off because SMTP_HOST is still the shipped placeholder")
        EVENT_NOTIFICATION = False
        PROFILE_NOTIFICATION = False
        REPO_NOTIFICATION = False
        REPO_UPDATE_DATE_NOTIFICATION = False
        CONTRIB_NOTIFICATION = False
        ERROR_NOTIFICATION = False
    if WEBHOOK_ENABLED and not validate_webhook_url():
        verbose_print("Webhook notifications are off because WEBHOOK_URL is not a complete HTTPS link")
        WEBHOOK_ENABLED = False

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
