#!/usr/bin/env python3
"""
Author: Michal Szymanski <misiektoja-github@rm-rf.ninja>
v2.2

OSINT tool implementing real-time tracking of GitHub users activities including profile and repositories changes:
https://github.com/misiektoja/github_monitor/

Python pip3 requirements:

PyGithub
requests
python-dateutil
pytz
tzlocal (optional)
python-dotenv (optional)
"""

VERSION = "2.2"

# ---------------------------
# CONFIGURATION SECTION START
# ---------------------------

CONFIG_BLOCK = """
# Get your GitHub personal access token (classic) by visiting:
# https://github.com/settings/apps
#
# Then go to: Personal access tokens -> Tokens (classic) -> Generate new token (classic)
#
# Provide the GITHUB_TOKEN secret using one of the following methods:
#   - Pass it at runtime with -t / --github-token
#   - Set it as an environment variable (e.g. export GITHUB_TOKEN=...)
#   - Add it to ".env" file (GITHUB_TOKEN=...) for persistent use
#   - Fallback: hard-code it in the code or config file
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
# PRs, description etc., except for update date)
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
    'DeploymentEvent',
    'CheckRunEvent',
    'WorkflowRunEvent',
]

# Number of recent events to fetch when a change in the last event ID is detected
# Note: if more than EVENTS_NUMBER events occur between two checks,
# any events older than the most recent EVENTS_NUMBER will be missed
EVENTS_NUMBER = 30  # 1 page

# If True, track user's repository changes (changed stargazers, watchers, forks, description, update date etc.)
# Can also be enabled using the -j flag
TRACK_REPOS_CHANGES = False

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

# Width of main horizontal line
HORIZONTAL_LINE1 = 105

# Width of horizontal line for repositories list output
HORIZONTAL_LINE2 = 80

# Whether to clear the terminal screen after starting the tool
CLEAR_SCREEN = True

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
GITHUB_CHECK_INTERVAL = 0
LOCAL_TIMEZONE = ""
EVENTS_TO_MONITOR = []
EVENTS_NUMBER = 0
TRACK_REPOS_CHANGES = False
DO_NOT_MONITOR_GITHUB_EVENTS = False
GET_ALL_REPOS = False
BLOCKED_REPOS = False
TRACK_CONTRIB_CHANGES = False
LIVENESS_CHECK_INTERVAL = 0
CHECK_INTERNET_URL = ""
CHECK_INTERNET_TIMEOUT = 0
CSV_FILE = ""
DOTENV_FILE = ""
GITHUB_LOGFILE = ""
DISABLE_LOGGING = False
HORIZONTAL_LINE1 = 0
HORIZONTAL_LINE2 = 0
CLEAR_SCREEN = False
NET_MAX_RETRIES = 0
NET_BASE_BACKOFF_SEC = 0
GITHUB_CHECK_SIGNAL_VALUE = 0

exec(CONFIG_BLOCK, globals())

# Default name for the optional config file
DEFAULT_CONFIG_FILENAME = "github_monitor.conf"

# List of secret keys to load from env/config
SECRET_KEYS = ("GITHUB_TOKEN", "SMTP_PASSWORD")

LIVENESS_CHECK_COUNTER = LIVENESS_CHECK_INTERVAL / GITHUB_CHECK_INTERVAL

stdout_bck = None
csvfieldnames = ['Date', 'Type', 'Name', 'Old', 'New']

CLI_CONFIG_PATH = None

# to solve the issue: 'SyntaxError: f-string expression part cannot include a backslash'
nl_ch = "\n"


import sys

if sys.version_info < (3, 10):
    print("* Error: Python version 3.10 or higher required !")
    sys.exit(1)

import time
import string
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
import csv
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
import ipaddress
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
from typing import Any, Callable
import shutil
from pathlib import Path
from typing import Optional
import datetime as dt
import requests

NET_ERRORS = (
    req.exceptions.RequestException,
    urllib3.exceptions.HTTPError,
    socket.gaierror,
    GithubException,
)


# Logger class to output messages to stdout and log file
class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.logfile = open(filename, "a", buffering=1, encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.logfile.write(message)
        self.terminal.flush()
        self.logfile.flush()

    def flush(self):
        pass


# Signal handler when user presses Ctrl+C
def signal_handler(sig, frame):
    sys.stdout = stdout_bck
    print('\n* You pressed Ctrl+C, tool is terminated.')
    sys.exit(0)


# Checks internet connectivity
def check_internet(url=CHECK_INTERNET_URL, timeout=CHECK_INTERNET_TIMEOUT):
    try:
        _ = req.get(url, timeout=timeout)
        return True
    except req.RequestException as e:
        print(f"* No connectivity, please check your network:\n\n{e}")
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
    except Exception:
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
        except Exception:
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
        except Exception:
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


# Sends email notification
def send_email(subject, body, body_html, use_ssl, smtp_timeout=15):
    fqdn_re = re.compile(r'(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}\.?$)')
    email_re = re.compile(r'[^@]+@[^@]+\.[^@]+')

    try:
        ipaddress.ip_address(str(SMTP_HOST))
    except ValueError:
        if not fqdn_re.search(str(SMTP_HOST)):
            print("Error sending email - SMTP settings are incorrect (invalid IP address/FQDN in SMTP_HOST)")
            return 1

    try:
        port = int(SMTP_PORT)
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        print("Error sending email - SMTP settings are incorrect (invalid port number in SMTP_PORT)")
        return 1

    if not email_re.search(str(SENDER_EMAIL)) or not email_re.search(str(RECEIVER_EMAIL)):
        print("Error sending email - SMTP settings are incorrect (invalid email in SENDER_EMAIL or RECEIVER_EMAIL)")
        return 1

    if not SMTP_USER or not isinstance(SMTP_USER, str) or SMTP_USER == "your_smtp_user" or not SMTP_PASSWORD or not isinstance(SMTP_PASSWORD, str) or SMTP_PASSWORD == "your_smtp_password":
        print("Error sending email - SMTP settings are incorrect (check SMTP_USER & SMTP_PASSWORD variables)")
        return 1

    if not subject or not isinstance(subject, str):
        print("Error sending email - SMTP settings are incorrect (subject is not a string or is empty)")
        return 1

    if not body and not body_html:
        print("Error sending email - SMTP settings are incorrect (body and body_html cannot be empty at the same time)")
        return 1

    try:
        if use_ssl:
            ssl_context = ssl.create_default_context()
            smtpObj = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=smtp_timeout)
            smtpObj.starttls(context=ssl_context)
        else:
            smtpObj = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=smtp_timeout)
        smtpObj.login(SMTP_USER, SMTP_PASSWORD)
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
    except Exception as e:
        print(f"Error sending email: {e}")
        return 1
    return 0


# Initializes the CSV file
def init_csv_file(csv_file_name):
    try:
        if not os.path.isfile(csv_file_name) or os.path.getsize(csv_file_name) == 0:
            with open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
    except Exception as e:
        raise RuntimeError(f"Could not initialize CSV file '{csv_file_name}': {e}")


# Writes CSV entry
def write_csv_entry(csv_file_name, timestamp, object_type, object_name, old, new):
    try:

        with open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8") as csv_file:
            csvwriter = csv.DictWriter(csv_file, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
            csvwriter.writerow({'Date': timestamp, 'Type': object_type, 'Name': object_name, 'Old': old, 'New': new})

    except Exception as e:
        raise RuntimeError(f"Failed to write to CSV file '{csv_file_name}': {e}")


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
    return (f'{ts_str}{calendar.day_abbr[(now_local_naive()).weekday()]}, {now_local_naive().strftime("%d %b %Y, %H:%M:%S")}')


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
        except Exception:
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
        except Exception:
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
        except Exception:
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
                load_dotenv(env_path, override=True)
            else:
                print("* No .env file found, skipping env-var reload")
        except ImportError:
            env_path = None
            print("* python-dotenv not installed, skipping env-var reload")

    if env_path:
        for secret in SECRET_KEYS:
            old_val = globals().get(secret)
            val = os.getenv(secret)
            if val is not None and val != old_val:
                globals()[secret] = val
                print(f"* Reloaded {secret} from {env_path}")

    print_cur_ts("Timestamp:\t\t\t")


# List subclass used as a safe fallback for paginated responses
class EmptyPaginatedList(list):
    def __init__(self):
        super().__init__()
        self.totalCount = 0


# Wraps GitHub API call with retry and linear back-off, returning a specified default on failure
def gh_call(fn: Callable[..., Any], retries=NET_MAX_RETRIES, backoff=NET_BASE_BACKOFF_SEC, default: Any = None,) -> Callable[..., Any]:
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        for i in range(1, retries + 1):
            try:
                return fn(*args, **kwargs)
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

                print(f"* {fn.__name__} rate limited, sleeping {sleep_for}s (retry {i}/{retries})")
                time.sleep(sleep_for)
                continue

            except NET_ERRORS as e:
                print(f"* {fn.__name__} error: {e} (retry {i}/{retries})")
                time.sleep(backoff * i)
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
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(base_url=GITHUB_API_URL, auth=auth)

        g_user = g.get_user(user)
        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url

        followers_count = g_user.followers
        followings_count = g_user.following

        followers_list = g_user.get_followers()
        followings_list = g_user.get_following()

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user {user} details: {e}")

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
        print(f"* Cannot fetch user's followers list: {e}")

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
        print(f"* Cannot fetch user's followings list: {e}")

    g.close()


# Processes items from all passed repositories and returns a list of dictionaries
def github_process_repos(repos_list):
    import logging
    list_of_repos = []
    stargazers_list = []
    subscribers_list = []
    forked_repos = []

    if repos_list:
        for repo in repos_list:
            try:
                repo_created_date = repo.created_at
                repo_updated_date = repo.updated_at

                github_logger = logging.getLogger('github')
                original_level = github_logger.level
                github_logger.setLevel(logging.ERROR)

                try:
                    stargazers_list = [star.login for star in repo.get_stargazers()]
                    subscribers_list = [subscriber.login for subscriber in repo.get_subscribers()]
                    forked_repos = [fork.full_name for fork in repo.get_forks()]
                except GithubException as e:
                    if e.status in [403, 451]:
                        if BLOCKED_REPOS:
                            print(f"* Repo '{repo.name}' is blocked, skipping for now: {e}")
                            print_cur_ts("Timestamp:\t\t\t")
                        continue
                    raise
                finally:
                    github_logger.setLevel(original_level)

                issues = list(repo.get_issues(state='open'))
                pulls = list(repo.get_pulls(state='open'))

                real_issues = [i for i in issues if not i.pull_request]
                issue_count = len(real_issues)
                pr_count = len(pulls)

                issues_list = [f"#{i.number} {i.title} ({i.user.login}) [ {i.html_url} ]" for i in real_issues]
                pr_list = [f"#{pr.number} {pr.title} ({pr.user.login}) [ {pr.html_url} ]" for pr in pulls]

                list_of_repos.append({"name": repo.name, "descr": repo.description, "is_fork": repo.fork, "forks": repo.forks_count, "stars": repo.stargazers_count, "subscribers": repo.subscribers_count, "url": repo.html_url, "language": repo.language, "date": repo_created_date, "update_date": repo_updated_date, "stargazers_list": stargazers_list, "forked_repos": forked_repos, "subscribers_list": subscribers_list, "issues": issue_count, "pulls": pr_count, "issues_list": issues_list, "pulls_list": pr_list})

            except GithubException as e:
                # Skip TOS-blocked (403) and legally blocked (451) repositories
                if e.status in [403, 451]:
                    if BLOCKED_REPOS:
                        print(f"* Repo '{repo.name}' is blocked, skipping for now: {e}")
                        print_cur_ts("Timestamp:\t\t\t")
                    continue
                else:
                    print(f"* Cannot process repo '{repo.name}', skipping for now: {e}")
                    print_cur_ts("Timestamp:\t\t\t")
                    continue
            except Exception as e:
                print(f"* Cannot process repo '{repo.name}', skipping for now: {e}")
                print_cur_ts("Timestamp:\t\t\t")
                continue

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
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(base_url=GITHUB_API_URL, auth=auth)

        g_user = g.get_user(user)
        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url

        if GET_ALL_REPOS:
            repos_list = g_user.get_repos()
            repos_count = g_user.public_repos
        else:
            repos_list = [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login]
            repos_count = len(repos_list)

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user {user} details: {e}")

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
                    pr_count = repo.get_pulls(state='open').totalCount
                    issue_count = repo.open_issues_count - pr_count
                except Exception:
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
                        print(f"\n* Repo '{repo.name}' is blocked: {e}")
                        print("─" * HORIZONTAL_LINE2)
                        continue
                finally:
                    github_logger.setLevel(original_level)

                print("─" * HORIZONTAL_LINE2)
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user's repositories list: {e}")

    g.close()


# Prints a list of starred repositories by a GitHub user (-g)
def github_print_starred_repos(user):
    user_name_str = user
    user_url = "-"
    starred_count = 0
    starred_list = []

    print(f"* Getting repositories starred by user '{user}' ...")

    try:
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(base_url=GITHUB_API_URL, auth=auth)

        g_user = g.get_user(user)
        user_login = g_user.login
        user_name = g_user.name
        user_url = g_user.html_url

        starred_list = g_user.get_starred()
        starred_count = starred_list.totalCount

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user {user} details: {e}")

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
        raise RuntimeError(f"Cannot fetch user's starred list: {e}")

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
        tp = f" (after {calculate_timespan(event_date, ts, show_seconds=False, granularity=2)}: {get_short_date_from_ts(ts)})"
    st += print_v(f"Event date:\t\t\t{get_date_from_ts(event_date)}{tp}")
    st += print_v(f"Event ID:\t\t\t{event.id}")
    st += print_v(f"Event type:\t\t\t{event.type}")

    if event.repo.id:
        try:
            desc_len = 80
            repo = g.get_repo(event.repo.name)

            # For ForkEvent, prefer the source repo if available
            if event.type == "ForkEvent" and repo is not None:
                try:
                    parent = gh_call(lambda: getattr(repo, "parent", None))()
                    if parent:
                        repo = parent
                except Exception:
                    pass

            repo_name = getattr(repo, "full_name", event.repo.name)
            repo_url = getattr(repo, "html_url", event.repo.url.replace("https://api.github.com/repos/", "https://github.com/"))

            st += print_v(f"\nRepo name:\t\t\t{repo_name}")
            st += print_v(f"Repo URL:\t\t\t{repo_url}")

            desc = (repo.description or "") if repo else ""
            cleaned = desc.replace('\n', ' ')
            short_desc = cleaned[:desc_len] + '...' if len(cleaned) > desc_len else cleaned
            if short_desc:
                st += print_v(f"Repo description:\t\t{short_desc}")

        except UnknownObjectException:
            repo = None
            st += print_v("\nRepository not found or has been removed")
        except GithubException as e:
            repo = None
            st += print_v(f"\n* Error occurred while getting repo details: {e}")

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
        st += print_v(f"Description:\t\t\t'{event.payload.get('description')}'")

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

            commit_details = None
            if repo:
                commit_details = gh_call(lambda: repo.get_commit(commit["sha"]))()

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
                except Exception:
                    file_count = "N/A"
                st += print_v(f" - Files changed:\t\t{file_count}")
                if file_count:
                    st += print_v(f" - Changed files list:")
                    for f in commit_details.files:
                        st += print_v(f"     • '{f.filename}' - {f.status} (+{f.additions} / -{f.deletions})")

            st += print_v(f"\n - Commit message:\t\t'{commit['message']}'")
            st += print_v("." * HORIZONTAL_LINE1)

    # Fallback for new Events API where PushEvent no longer includes commit summaries
    elif event.type == "PushEvent" and repo:
        before_sha = event.payload.get("before")
        head_sha = event.payload.get("head") or event.payload.get("after")
        size_hint = event.payload.get("size")

        # Debug when payload has no commits
        # st += print_v("\n[debug] PushEvent payload has no 'commits' array; using compare API")
        # st += print_v(f"[debug] before:\t\t\t{before_sha}")
        # st += print_v(f"[debug] head/after:\t\t{head_sha}")
        if size_hint is not None:
            st += print_v(f"[debug] size (hint):\t\t{size_hint}")

        if before_sha and head_sha and before_sha != head_sha:
            try:
                compare = gh_call(lambda: repo.compare(before_sha, head_sha))()
            except Exception as e:
                compare = None
                st += print_v(f"* Error using compare({before_sha[:12]}...{head_sha[:12]}): {e}")

            if compare:
                commits = list(compare.commits)
                commits_total = len(commits)
                short_repo = getattr(repo, "full_name", repo_name)
                compare_url = f"https://github.com/{short_repo}/compare/{before_sha[:12]}...{head_sha[:12]}"
                st += print_v(f"\nNumber of commits:\t\t{commits_total}")
                st += print_v(f"Compare URL:\t\t\t{compare_url}")

                for commit_count, c in enumerate(commits, start=1):
                    st += print_v(f"\n=== Commit {commit_count}/{commits_total} ===")
                    st += print_v("." * HORIZONTAL_LINE1)

                    commit_sha = getattr(c, "sha", None) or getattr(c, "id", None)
                    commit_details = gh_call(lambda: repo.get_commit(commit_sha))() if (repo and commit_sha) else None

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
                        except Exception:
                            file_count = "N/A"
                        st += print_v(f" - Files changed:\t\t{file_count}")
                        if file_count and file_count != "N/A":
                            st += print_v(" - Changed files list:")
                            for f in commit_details.files:
                                st += print_v(f"     • '{f.filename}' - {f.status} (+{f.additions} / -{f.deletions})")

                        st += print_v(f"\n - Commit message:\t\t'{commit_details.commit.message}'")
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
            if len(review_body) > 750:
                review_body = review_body[:750] + " ... <cut>"
            st += print_v(f"Review body:")
            st += print_v(format_body_block(review_body))

        if repo:
            try:
                pr_number = event.payload["pull_request"]["number"]
                pr_obj = repo.get_pull(pr_number)
                count = sum(1 for _ in pr_obj.get_single_review_comments(event.payload["review"].get("id")))
                st += print_v(f"Comments in this review:\t{count}")
            except Exception:
                pass

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
            issue_snippet = issue_body if len(issue_body) <= 750 else issue_body[:750] + " ... <cut>"
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
            if len(comment_body) > 750:
                comment_body = comment_body[:750] + " ... <cut>"
            st += print_v(f"\nComment body:")
            st += print_v(format_body_block(comment_body))

        if event.type == "PullRequestReviewCommentEvent":
            parent_id = comment.get("in_reply_to_id")
            if parent_id and repo:
                try:
                    pr_number = event.payload["pull_request"]["number"]
                    pr = repo.get_pull(pr_number)

                    parent = pr.get_review_comment(parent_id)
                    parent_date = get_date_from_ts(parent.created_at)

                    st += print_v(f"\nPrevious comment:\n\n↳ In reply to {parent.user.login} (@ {parent_date}):")

                    parent_body = parent.body
                    if len(parent_body) > 750:
                        parent_body = parent_body[:750] + " ... <cut>"
                    st += print_v(format_body_block(parent_body))

                    st += print_v(f"\nPrevious comment URL:\t\t{parent.html_url}")
                except Exception as e:
                    st += print_v(f"\n* Could not fetch parent comment (ID {parent_id}): {e}")
            else:
                st += print_v("\n(This is the first comment in its thread)")
        elif event.type in ("IssueCommentEvent", "CommitCommentEvent"):
            if repo:

                comment_id = comment["id"]
                comment_created = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00"))

                if event.type == "IssueCommentEvent":

                    issue_number = event.payload["issue"]["number"]
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
                        if len(parent_body) > 750:
                            parent_body = parent_body[:750] + " ... <cut>"
                        st += print_v(format_body_block(parent_body))

                        st += print_v(f"\nPrevious comment URL:\t\t{previous['html_url']}")
                    else:
                        st += print_v("\n(This is the first comment in this thread)")

                elif event.type == "CommitCommentEvent":
                    commit_sha = comment["commit_id"]
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
                        if len(parent_body) > 750:
                            parent_body = parent_body[:750] + " ... <cut>"
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
            if len(comment_body) > 750:
                comment_body = comment_body[:750] + " ... <cut>"
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
        print(f"* Error: {e}")

    list_operation = "* Listing & saving" if csv_file_name else "* Listing"

    print(f"{list_operation} {number} recent events for '{user}' ...\n")

    try:
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(base_url=GITHUB_API_URL, auth=auth)

        g_user = g.get_user(user)
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
        print(f"* Cannot fetch user details: {e}")
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
                        print(f"\n* Warning, cannot fetch all event details, skipping: {e}")
                        print_cur_ts("\nTimestamp:\t\t\t")
                        continue
                    try:
                        if csv_file_name:
                            write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                    except Exception as e:
                        print(f"* Error: {e}")
                    print_cur_ts("\nTimestamp:\t\t\t")
        except Exception as e:
            print(f"* Cannot fetch events: {e}")


# Detects and reports changes in a user's profile-level entities (followers, followings, public repos, starred repos)
def handle_profile_change(label, count_old, count_new, list_old, raw_list, user, csv_file_name, field):
    try:
        list_new = []
        list_new = [getattr(item, field) for item in raw_list]
        if not list_new and count_new > 0:
            return list_old, count_old
    except Exception as e:
        print(f"* Error while trying to get the list of {label.lower()}: {e}")
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
            print(f"* Error: {e}")

    added_list_str = ""
    removed_list_str = ""
    added_mbody = ""
    removed_mbody = ""

    removed_items = list(set(list_old) - set(list_new))
    added_items = list(set(list_new) - set(list_old))

    if removed_items:
        print(f"Removed {label.lower()}:\n")
        removed_mbody = f"\nRemoved {label.lower()}:\n\n"
        for item in removed_items:
            item_url = (f"https://github.com/{item}/" if label.lower() in ["followers", "followings", "starred repos"]
                        else f"https://github.com/{user}/{item}/")
            print(f"- {item} [ {item_url} ]")
            removed_list_str += f"- {item} [ {item_url} ]\n"
            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), f"Removed {label[:-1]}", user, item, "")
            except Exception as e:
                print(f"* Error: {e}")
        print()

    if added_items:
        print(f"Added {label.lower()}:\n")
        added_mbody = f"\nAdded {label.lower()}:\n\n"
        for item in added_items:
            item_url = (f"https://github.com/{item}/" if label.lower() in ["followers", "followings", "starred repos"]
                        else f"https://github.com/{user}/{item}/")
            print(f"- {item} [ {item_url} ]")
            added_list_str += f"- {item} [ {item_url} ]\n"
            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), f"Added {label[:-1]}", user, "", item)
            except Exception as e:
                print(f"* Error: {e}")
        print()

    if diff == 0:
        m_subject = f"GitHub user {user} {label.lower()} list changed"
        m_body = (f"{label} list changed {label_context} user {user}\n"
                  f"{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
    else:
        m_subject = f"GitHub user {user} {label.lower()} number has changed! ({diff_str}, {old_count} -> {new_count})"
        m_body = (f"{label} number changed {label_context} user {user} from {old_count} to {new_count} ({diff_str})\n"
                  f"{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")

    if PROFILE_NOTIFICATION:
        print(f"Sending email notification to {RECEIVER_EMAIL}")
        send_email(m_subject, m_body, "", SMTP_SSL)

    print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
    print_cur_ts("Timestamp:\t\t\t")
    return list_new, new_count


# Detects and reports changes in repository-level entities (like stargazers, watchers, forks, issues, pull requests)
def check_repo_list_changes(count_old, count_new, list_old, list_new, label, repo_name, repo_url, user, csv_file_name):
    if not list_new and count_new > 0:
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
            print(f"* Error: {e}")

    added_list_str = ""
    removed_list_str = ""
    added_mbody = ""
    removed_mbody = ""

    removed_items = list(set(list_old) - set(list_new))
    added_items = list(set(list_new) - set(list_old))

    removal_text = "Closed" if label in ["Issues", "Pull Requests"] else "Removed"

    if list_old != list_new:
        print()

        if removed_items:
            print(f"{removal_text} {label.lower()}:\n")
            removed_mbody = f"\n{removal_text} {label.lower()}:\n\n"
            for item in removed_items:
                item_line = f"- {item} [ https://github.com/{item}/ ]" if label.lower() in ["stargazers", "watchers", "forks"] else f"- {item}"
                print(item_line)
                removed_list_str += item_line + "\n"
                try:
                    if csv_file_name:
                        value = item.rsplit("(", 1)[0].strip() if label in ["Issues", "Pull Requests"] else item
                        write_csv_entry(csv_file_name, now_local_naive(), f"{removal_text} {label[:-1]}", repo_name, value, "")
                except Exception as e:
                    print(f"* Error: {e}")
            print()

        if added_items:
            print(f"Added {label.lower()}:\n")
            added_mbody = f"\nAdded {label.lower()}:\n\n"
            for item in added_items:
                item_line = f"- {item} [ https://github.com/{item}/ ]" if label.lower() in ["stargazers", "watchers", "forks"] else f"- {item}"
                print(item_line)
                added_list_str += item_line + "\n"
                try:
                    if csv_file_name:
                        value = item.rsplit("(", 1)[0].strip() if label in ["Issues", "Pull Requests"] else item
                        write_csv_entry(csv_file_name, now_local_naive(), f"Added {label[:-1]}", repo_name, "", value)
                except Exception as e:
                    print(f"* Error: {e}")
            print()

    if diff == 0:
        m_subject = f"GitHub user {user} {label.lower()} list changed for repo '{repo_name}'!"
        m_body = (f"* Repo '{repo_name}': {label.lower()} list changed\n"
                  f"* Repo URL: {repo_url}\n{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")
    else:
        m_subject = f"GitHub user {user} number of {label.lower()} for repo '{repo_name}' has changed! ({diff_str}, {old_count} -> {new_count})"
        m_body = (f"* Repo '{repo_name}': number of {label.lower()} changed from {old_count} to {new_count} ({diff_str})\n"
                  f"* Repo URL: {repo_url}\n{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")

    if REPO_NOTIFICATION:
        print(f"Sending email notification to {RECEIVER_EMAIL}")
        send_email(m_subject, m_body, "", SMTP_SSL)
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
        return str(p) if p.is_file() else None

    candidates = [
        Path.cwd() / DEFAULT_CONFIG_FILENAME,
        Path.home() / f".{DEFAULT_CONFIG_FILENAME}",
        Path(__file__).parent / DEFAULT_CONFIG_FILENAME,
    ]

    for p in candidates:
        if p.is_file():
            return str(p)
    return None


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

        response = req.get(f"{GITHUB_API_URL}/user", headers=headers, timeout=15)
        if response.status_code != 200:
            return False
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
        response_graphql = req.post(graphql_endpoint, json=payload, headers=headers, timeout=15)

        if response_graphql.status_code == 404:
            return False

        if not response_graphql.ok:
            return False

        data = response_graphql.json()
        can_follow = (data.get("data", {}).get("user", {}).get("viewerCanFollow", True))
        return not bool(can_follow)

    except Exception:
        return False


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
        response = req.post(graphql_endpoint, json=payload, headers=headers, timeout=15)

        if not response.ok:
            return 0

        data = response.json()

        return (data.get("data", {}).get("user", {}).get("starredRepositories", {}).get("totalCount", 0))

    except Exception:
        return 0


# Returns True if the user's GitHub page shows "activity is private"
def has_private_banner(user):
    try:
        url = f"{GITHUB_HTML_URL.rstrip('/')}/{user}"
        r = req.get(url, timeout=15)
        return r.ok and "activity is private" in r.text.lower()
    except Exception:
        return False


# Returns True if the user's GitHub profile is public
def is_profile_public(g: Github, user, new_account_days=30):

    if has_private_banner(user):
        return False

    try:
        u = g.get_user(user)

        if any([
            u.followers > 0,
            u.following > 0,
            get_starred_count(user) > 0,
        ]):
            return True

        try:
            events_iter = iter(u.get_events())
            next(events_iter)
            return True
        except (StopIteration, GithubException):
            pass

    except GithubException:
        pass

    return False


# Returns a dict mapping 'YYYY-MM-DD' -> int contribution count for the range
def get_daily_contributions(username: str, start: Optional[dt.date] = None, end: Optional[dt.date] = None, token: Optional[str] = None) -> dict:
    if token is None:
        raise ValueError("GitHub token is required")

    today = dt.date.today()
    if start is None:
        start = today
    if end is None:
        end = today

    url = GITHUB_API_URL.rstrip("/") + "/graphql"
    headers = {"Authorization": f"Bearer {token}"}

    start_iso = dt.datetime.combine(start, dt.time.min).isoformat()
    to_exclusive = end + dt.timedelta(days=1)
    end_iso = dt.datetime.combine(to_exclusive, dt.time.min).isoformat()

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
    r = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    days = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    out = {}
    for w in days:
        for d in w["contributionDays"]:
            date = d["date"]
            if start <= dt.date.fromisoformat(date) <= end:
                out[date] = d["contributionCount"]
    return out


# Return contribution count for a single day
def get_daily_contributions_count(username: str, day: dt.date, token: str) -> int:
    data = get_daily_contributions(username, day, day, token)
    return next(iter(data.values()), 0)


# Checks count for today and decides whether to notify based on stored state.
def check_daily_contribs(username: str, token: str, state: dict, min_delta: int = 1, fail_threshold: int = 3) -> tuple[bool, int, bool]:
    day = today_local()

    try:
        curr = get_daily_contributions_count(username, day, token=token)
        state["consecutive_failures"] = 0
        state["last_error"] = None
    except Exception as e:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        state["last_error"] = f"{type(e).__name__}: {e}"
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


# Monitors activity of the specified GitHub user
def github_monitor_user(user, csv_file_name):

    try:
        if csv_file_name:
            init_csv_file(csv_file_name)
    except Exception as e:
        print(f"* Error: {e}")

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
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(base_url=GITHUB_API_URL, auth=auth)
        g_user_myself = g.get_user()
        user_myself_login = g_user_myself.login
        user_myself_name = g_user_myself.name
        user_myself_url = g_user_myself.html_url

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

        followers_list = g_user.get_followers()
        followings_list = g_user.get_following()

        if GET_ALL_REPOS:
            repos_list = g_user.get_repos()
            repos_count = g_user.public_repos
        else:
            repos_list = [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login]
            repos_count = len(repos_list)

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
            events = list(islice(g_user.get_events(), EVENTS_NUMBER))
            available_events = len(events)

    except Exception as e:
        print(f"\n* Error: {e}")
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
                print(f"\n* Cannot get event IDs / timestamps: {e}\n")
                pass

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
        print("Processing list of public repositories (be patient, it might take a while) ...")
        try:
            list_of_repos = github_process_repos(repos_list)
        except Exception as e:
            print(f"* Cannot process list of public repositories: {e}")
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
                print(f"\n* Warning: cannot fetch last event details: {e}")

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
        print(f"* Error: {e}")
        sys.exit(1)

    g.close()

    time.sleep(GITHUB_CHECK_INTERVAL)
    alive_counter = 0
    email_sent = False

    # Primary loop
    while True:

        try:
            g_user = g.get_user(user)
            email_sent = False

        except (GithubException, Exception) as e:
            print(f"* Error, retrying in {display_time(GITHUB_CHECK_INTERVAL)}: {e}")

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

            if should_notify and ERROR_NOTIFICATION and not email_sent:
                m_subject = f"github_monitor: session error! (user: {user})"
                m_body = f"{reason_msg}\n{e}{get_cur_ts(nl_ch + nl_ch + 'Timestamp: ')}"
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)
                email_sent = True

            print_cur_ts("Timestamp:\t\t\t")
            time.sleep(GITHUB_CHECK_INTERVAL)
            continue

        # Changed followings
        followings_raw = list(gh_call(g_user.get_following)())
        followings_count = gh_call(lambda: g_user.following)()
        if followings_raw is not None and followings_count is not None:
            followings_old, followings_old_count = handle_profile_change("Followings", followings_old_count, followings_count, followings_old, followings_raw, user, csv_file_name, field="login")

        # Changed followers
        followers_raw = list(gh_call(g_user.get_followers)())
        followers_count = gh_call(lambda: g_user.followers)()
        if followers_raw is not None and followers_count is not None:
            followers_old, followers_old_count = handle_profile_change("Followers", followers_old_count, followers_count, followers_old, followers_raw, user, csv_file_name, field="login")

        # Changed public repositories
        if GET_ALL_REPOS:
            repos_raw = list(gh_call(g_user.get_repos)())
            repos_count = gh_call(lambda: g_user.public_repos)()
        else:
            repos_raw = list(gh_call(lambda: [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login])())
            repos_count = len(repos_raw)

        if repos_raw is not None and repos_count is not None:
            repos_old, repos_old_count = handle_profile_change("Repos", repos_old_count, repos_count, repos_old, repos_raw, user, csv_file_name, field="name")

        # Changed starred repositories
        starred_raw = gh_call(g_user.get_starred)()
        if starred_raw is not None:
            starred_list = list(starred_raw)
            starred_count = starred_raw.totalCount
            starred_old, starred_old_count = handle_profile_change("Starred Repos", starred_old_count, starred_count, starred_old, starred_list, user, csv_file_name, field="full_name")

        # Changed contributions in a day
        if TRACK_CONTRIB_CHANGES:
            contrib_notify, contrib_curr, contrib_error_notify = check_daily_contribs(user, GITHUB_TOKEN, contrib_state, min_delta=1, fail_threshold=3)
            if contrib_error_notify and ERROR_NOTIFICATION:
                failures = contrib_state.get("consecutive_failures", 0)
                last_err = contrib_state.get("last_error", "Unknown error")
                err_msg = f"Error: GitHub daily contributions check failed {failures} times. Last error: {last_err}\n"
                print(err_msg)
                send_email(f"GitHub monitor errors for {user}", err_msg + get_cur_ts(nl_ch + "Timestamp: "), "", SMTP_SSL)

            if contrib_notify:
                contrib_old = contrib_state.get("prev_count")
                print(f"* Daily contributions changed for user {user} on {get_short_date_from_ts(contrib_state['day'], show_hour=False)} from {contrib_old} to {contrib_curr}!\n")

                try:
                    if csv_file_name:
                        write_csv_entry(csv_file_name, now_local_naive(), "Daily Contribs", user, contrib_old, contrib_curr)
                except Exception as e:
                    print(f"* Error: {e}")

                m_subject = f"GitHub user {user} daily contributions changed from {contrib_old} to {contrib_curr}!"
                m_body = (f"GitHub user {user} daily contributions changed on {get_short_date_from_ts(contrib_state['day'], show_hour=False)} from {contrib_old} to {contrib_curr}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}")

                if CONTRIB_NOTIFICATION:
                    print(f"Sending email notification to {RECEIVER_EMAIL}")
                    send_email(m_subject, m_body, "", SMTP_SSL)

                print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
                print_cur_ts("Timestamp:\t\t\t")

        # Changed bio
        bio = gh_call(lambda: g_user.bio)()
        if bio is not None and bio != bio_old:
            print(f"* Bio has changed for user {user} !\n")
            print(f"Old bio:\n\n{bio_old}\n")
            print(f"New bio:\n\n{bio}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Bio", user, bio_old, bio)
            except Exception as e:
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} bio has changed!"
            m_body = f"GitHub user {user} bio has changed\n\nOld bio:\n\n{bio_old}\n\nNew bio:\n\n{bio}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            bio_old = bio
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed location
        location = gh_call(lambda: g_user.location)()
        if location is not None and location != location_old:
            print(f"* Location has changed for user {user} !\n")
            print(f"Old location:\t\t\t{location_old}\n")
            print(f"New location:\t\t\t{location}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Location", user, location_old, location)
            except Exception as e:
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} location has changed!"
            m_body = f"GitHub user {user} location has changed\n\nOld location: {location_old}\n\nNew location: {location}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            location_old = location
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed user name
        user_name = gh_call(lambda: g_user.name)()
        if user_name is not None and user_name != user_name_old:
            print(f"* User name has changed for user {user} !\n")
            print(f"Old user name:\t\t\t{user_name_old}\n")
            print(f"New user name:\t\t\t{user_name}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "User Name", user, user_name_old, user_name)
            except Exception as e:
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} name has changed!"
            m_body = f"GitHub user {user} name has changed\n\nOld user name: {user_name_old}\n\nNew user name: {user_name}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            user_name_old = user_name
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed company
        company = gh_call(lambda: g_user.company)()
        if company is not None and company != company_old:
            print(f"* User company has changed for user {user} !\n")
            print(f"Old company:\t\t\t{company_old}\n")
            print(f"New company:\t\t\t{company}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Company", user, company_old, company)
            except Exception as e:
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} company has changed!"
            m_body = f"GitHub user {user} company has changed\n\nOld company: {company_old}\n\nNew company: {company}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            company_old = company
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed email
        email = gh_call(lambda: g_user.email)()
        if email is not None and email != email_old:
            print(f"* User email has changed for user {user} !\n")
            print(f"Old email:\t\t\t{email_old}\n")
            print(f"New email:\t\t\t{email}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Email", user, email_old, email)
            except Exception as e:
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} email has changed!"
            m_body = f"GitHub user {user} email has changed\n\nOld email: {email_old}\n\nNew email: {email}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            email_old = email
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed blog URL
        blog = gh_call(lambda: g_user.blog)()
        if blog is not None and blog != blog_old:
            print(f"* User blog URL has changed for user {user} !\n")
            print(f"Old blog URL:\t\t\t{blog_old}\n")
            print(f"New blog URL:\t\t\t{blog}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Blog URL", user, blog_old, blog)
            except Exception as e:
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} blog URL has changed!"
            m_body = f"GitHub user {user} blog URL has changed\n\nOld blog URL: {blog_old}\n\nNew blog URL: {blog}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            blog_old = blog
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        # Changed account update date
        account_updated_date = gh_call(lambda: g_user.updated_at)()
        if account_updated_date is not None and account_updated_date != account_updated_date_old:
            print(f"* User account has been updated for user {user} ! (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})\n")
            print(f"Old account update date:\t{get_date_from_ts(account_updated_date_old)}\n")
            print(f"New account update date:\t{get_date_from_ts(account_updated_date)}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, convert_to_local_naive(account_updated_date), "Account Update Date", user, convert_to_local_naive(account_updated_date_old), convert_to_local_naive(account_updated_date))
            except Exception as e:
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} account has been updated! (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})"
            m_body = f"GitHub user {user} account has been updated (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})\n\nOld account update date: {get_date_from_ts(account_updated_date_old)}\n\nNew account update date: {get_date_from_ts(account_updated_date)}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

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
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} has changed profile visibility to '{_get_profile_status(public)}' !"
            m_body = f"GitHub user {user} has changed profile visibility to '{_get_profile_status(public)}' !\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

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
                print(f"* Error: {e}")

            m_subject = f"GitHub user {user} has {'blocked' if blocked else 'unblocked'} you!"
            m_body = f"GitHub user {user} has {'blocked' if blocked else 'unblocked'} you!\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

            if PROFILE_NOTIFICATION:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            blocked_old = blocked
            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
            print_cur_ts("Timestamp:\t\t\t")

        list_of_repos = []

        # Changed repos details
        if TRACK_REPOS_CHANGES:

            if GET_ALL_REPOS:
                repos_list = gh_call(g_user.get_repos)()
            else:
                repos_list = gh_call(lambda: [repo for repo in g_user.get_repos(type='owner') if not repo.fork and repo.owner.login == user_login])()

            if repos_list is not None:
                try:
                    list_of_repos = github_process_repos(repos_list)
                    list_of_repos_ok = True
                except Exception as e:
                    list_of_repos = list_of_repos_old
                    print(f"* Cannot process list of public repositories, keeping old list: {e}")
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
                        r_issues_list = repo.get("issues_list")
                        r_pulls_list = repo.get("pulls_list")

                        for repo_old in list_of_repos_old:
                            r_name_old = repo_old.get("name")
                            if r_name_old == r_name:
                                r_descr_old = repo_old.get("descr", "")
                                r_forks_old = repo_old.get("forks", 0)
                                r_stars_old = repo_old.get("stars", 0)
                                r_subscribers_old = repo_old.get("subscribers", 0)
                                r_url_old = repo_old.get("url", "")
                                r_update_old = repo_old.get("update_date")
                                r_stargazers_list_old = repo_old.get("stargazers_list")
                                r_subscribers_list_old = repo_old.get("subscribers_list")
                                r_forked_repos_old = repo_old.get("forked_repos")
                                r_issues_old = repo_old.get("issues")
                                r_pulls_old = repo_old.get("pulls")
                                r_issues_list_old = repo_old.get("issues_list")
                                r_pulls_list_old = repo_old.get("pulls_list")

                                # Update date for repo changed
                                if r_update != r_update_old:
                                    r_message = f"* Repo '{r_name}' update date changed (after {calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)})\n* Repo URL: {r_url}\n\nOld repo update date:\t{get_date_from_ts(r_update_old)}\n\nNew repo update date:\t{get_date_from_ts(r_update)}\n"
                                    print(r_message)
                                    try:
                                        if csv_file_name:
                                            write_csv_entry(csv_file_name, now_local_naive(), "Repo Update Date", r_name, convert_to_local_naive(r_update_old), convert_to_local_naive(r_update))
                                    except Exception as e:
                                        print(f"* Error: {e}")
                                    m_subject = f"GitHub user {user} repo '{r_name}' update date has changed ! (after {calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)})"
                                    m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
                                    if REPO_UPDATE_DATE_NOTIFICATION:
                                        print(f"Sending email notification to {RECEIVER_EMAIL}")
                                        send_email(m_subject, m_body, "", SMTP_SSL)
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

                                # Repo description changed
                                if r_descr != r_descr_old:
                                    r_message = f"* Repo '{r_name}' description changed from:\n\n'{r_descr_old}'\n\nto:\n\n'{r_descr}'\n\n* Repo URL: {r_url}\n"
                                    print(r_message)
                                    try:
                                        if csv_file_name:
                                            write_csv_entry(csv_file_name, now_local_naive(), "Repo Description", r_name, r_descr_old, r_descr)
                                    except Exception as e:
                                        print(f"* Error: {e}")
                                    m_subject = f"GitHub user {user} repo '{r_name}' description has changed !"
                                    m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"
                                    if REPO_NOTIFICATION:
                                        print(f"Sending email notification to {RECEIVER_EMAIL}")
                                        send_email(m_subject, m_body, "", SMTP_SSL)
                                    print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
                                    print_cur_ts("Timestamp:\t\t\t")

                    list_of_repos_old = list_of_repos

        # New GitHub events
        if not DO_NOT_MONITOR_GITHUB_EVENTS:
            events = list(gh_call(lambda: list(islice(g_user.get_events(), EVENTS_NUMBER)))())
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
                        print(f"* Cannot get last event ID / timestamp: {e}")
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
                                print(f"\n* Warning, cannot fetch all event details: {e}")

                            first_new = False

                            if event_date and repo_name and event_text:

                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                                except Exception as e:
                                    print(f"* Error: {e}")

                                m_subject = f"GitHub user {user} has new {event.type} (repo: {repo_name})"
                                m_body = f"GitHub user {user} has new {event.type} event\n\n{event_text}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)}){get_cur_ts(nl_ch + 'Timestamp: ')}"

                                if EVENT_NOTIFICATION:
                                    print(f"\nSending email notification to {RECEIVER_EMAIL}")
                                    send_email(m_subject, m_body, "", SMTP_SSL)

                            print(f"Check interval:\t\t\t{display_time(GITHUB_CHECK_INTERVAL)} ({get_range_of_dates_from_tss(int(time.time()) - GITHUB_CHECK_INTERVAL, int(time.time()), short=True)})")
                            print_cur_ts("Timestamp:\t\t\t")

                    last_event_id_old = last_event_id
                    last_event_ts_old = last_event_ts
                    events_list_of_ids_old = events_list_of_ids.copy()

        alive_counter += 1

        if LIVENESS_CHECK_COUNTER and alive_counter >= LIVENESS_CHECK_COUNTER:
            print_cur_ts("Liveness check, timestamp:\t")
            alive_counter = 0

        g.close()

        time.sleep(GITHUB_CHECK_INTERVAL)


def main():
    global CLI_CONFIG_PATH, DOTENV_FILE, LOCAL_TIMEZONE, LIVENESS_CHECK_COUNTER, GITHUB_TOKEN, GITHUB_API_URL, CSV_FILE, DISABLE_LOGGING, GITHUB_LOGFILE, PROFILE_NOTIFICATION, EVENT_NOTIFICATION, REPO_NOTIFICATION, REPO_UPDATE_DATE_NOTIFICATION, ERROR_NOTIFICATION, GITHUB_CHECK_INTERVAL, SMTP_PASSWORD, stdout_bck, DO_NOT_MONITOR_GITHUB_EVENTS, TRACK_REPOS_CHANGES, GET_ALL_REPOS, CONTRIB_NOTIFICATION, TRACK_CONTRIB_CHANGES

    if "--generate-config" in sys.argv:
        print(CONFIG_BLOCK.strip("\n"))
        sys.exit(0)

    if "--version" in sys.argv:
        print(f"{os.path.basename(sys.argv[0])} v{VERSION}")
        sys.exit(0)

    stdout_bck = sys.stdout

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    clear_screen(CLEAR_SCREEN)

    print(f"GitHub Monitoring Tool v{VERSION}\n")

    parser = argparse.ArgumentParser(
        prog="github_monitor",
        description=("Monitor a GitHub user's profile and activity with customizable email alerts [ https://github.com/misiektoja/github_monitor/ ]"), formatter_class=argparse.RawTextHelpFormatter
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
        action="store_true",
        help="Print default config template and exit",
    )
    conf.add_argument(
        "--env-file",
        dest="env_file",
        metavar="PATH",
        help="Path to optional dotenv file (auto-search if not set, disable with 'none')",
    )

    # API settings
    creds = parser.add_argument_group("API settings")
    creds.add_argument(
        "-t", "--github-token",
        dest="github_token",
        metavar="GITHUB_TOKEN",
        type=str,
        help="GitHub personal access token (classic)"
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
        help="Email when user's repositories change (stargazers, watchers, forks, issues, PRs, description etc., except for update date)"
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
        "-j", "--track-repos-changes",
        dest="track_repos_changes",
        action="store_true",
        default=None,
        help="Track user's repository changes (changed stargazers, watchers, forks, description, update date etc.)"
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
        "-m", "--track-contribs-changes",
        dest="track_contribs_changes",
        action="store_true",
        default=None,
        help="Track user's daily contributions count and log changes"
    )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.config_file:
        CLI_CONFIG_PATH = os.path.expanduser(args.config_file)

    cfg_path = find_config_file(CLI_CONFIG_PATH)

    if not cfg_path and CLI_CONFIG_PATH:
        print(f"* Error: Config file '{CLI_CONFIG_PATH}' does not exist")
        sys.exit(1)

    if cfg_path:
        try:
            with open(cfg_path, "r") as cf:
                exec(cf.read(), globals())
        except Exception as e:
            print(f"* Error loading config file '{cfg_path}': {e}")
            sys.exit(1)

    if args.env_file:
        DOTENV_FILE = os.path.expanduser(args.env_file)
    else:
        if DOTENV_FILE:
            DOTENV_FILE = os.path.expanduser(DOTENV_FILE)

    if DOTENV_FILE and DOTENV_FILE.lower() == 'none':
        env_path = None
    else:
        try:
            from dotenv import load_dotenv, find_dotenv

            if DOTENV_FILE:
                env_path = DOTENV_FILE
                if not os.path.isfile(env_path):
                    print(f"* Warning: dotenv file '{env_path}' does not exist\n")
                else:
                    load_dotenv(env_path, override=True)
            else:
                env_path = find_dotenv() or None
                if env_path:
                    load_dotenv(env_path, override=True)
        except ImportError:
            env_path = DOTENV_FILE if DOTENV_FILE else None
            if env_path:
                print(f"* Warning: Cannot load dotenv file '{env_path}' because 'python-dotenv' is not installed\n\nTo install it, run:\n    pip3 install python-dotenv\n\nOnce installed, re-run this tool\n")

    if env_path:
        for secret in SECRET_KEYS:
            val = os.getenv(secret)
            if val is not None:
                globals()[secret] = val

    local_tz = None
    if LOCAL_TIMEZONE == "Auto":
        if get_localzone is not None:
            try:
                local_tz = get_localzone()
            except Exception:
                pass
        if local_tz:
            LOCAL_TIMEZONE = str(local_tz)
        else:
            print("* Error: Cannot detect local timezone, consider setting LOCAL_TIMEZONE to your local timezone manually !")
            sys.exit(1)
    else:
        if not is_valid_timezone(LOCAL_TIMEZONE):
            print(f"* Error: Configured LOCAL_TIMEZONE '{LOCAL_TIMEZONE}' is not valid. Please use a valid pytz timezone name.")
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

    if args.github_token:
        GITHUB_TOKEN = args.github_token

    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_classic_personal_access_token":
        print("* Error: GITHUB_TOKEN (-t / --github_token) value is empty or incorrect")
        sys.exit(1)

    if not args.username:
        print("* Error: GITHUB_USERNAME argument is required !")
        sys.exit(1)

    if args.github_url:
        GITHUB_API_URL = args.github_url

    if not GITHUB_API_URL:
        print("* Error: GITHUB_API_URL (-x / --github_url) value is empty")
        sys.exit(1)

    if args.get_all_repos is True:
        GET_ALL_REPOS = True

    if args.list_followers_and_followings:
        try:
            github_print_followers_and_followings(args.username)
        except Exception as e:
            print(f"* Error: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.list_repos:
        try:
            github_print_repos(args.username)
        except Exception as e:
            print(f"* Error: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.list_starred_repos:
        try:
            github_print_starred_repos(args.username)
        except Exception as e:
            print(f"* Error: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.check_interval:
        GITHUB_CHECK_INTERVAL = args.check_interval
        LIVENESS_CHECK_COUNTER = LIVENESS_CHECK_INTERVAL / GITHUB_CHECK_INTERVAL

    if args.csv_file:
        CSV_FILE = os.path.expanduser(args.csv_file)
    else:
        if CSV_FILE:
            CSV_FILE = os.path.expanduser(CSV_FILE)

    if CSV_FILE:
        try:
            with open(CSV_FILE, 'a', newline='', buffering=1, encoding="utf-8") as _:
                pass
        except Exception as e:
            print(f"* Error: CSV file cannot be opened for writing: {e}")
            sys.exit(1)

    if args.list_recent_events:
        if args.recent_events_count and args.recent_events_count > 0:
            events_n = args.recent_events_count
        else:
            events_n = 5
        try:
            github_list_events(args.username, events_n, CSV_FILE)
        except Exception as e:
            print(f"* Error: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.disable_logging is True:
        DISABLE_LOGGING = True

    if not DISABLE_LOGGING:
        log_path = Path(os.path.expanduser(GITHUB_LOGFILE))
        if log_path.parent != Path('.'):
            if log_path.suffix == "":
                log_path = log_path.parent / f"{log_path.name}_{args.username}.log"
        else:
            if log_path.suffix == "":
                log_path = Path(f"{log_path.name}_{args.username}.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        FINAL_LOG_PATH = str(log_path)
        sys.stdout = Logger(FINAL_LOG_PATH)
    else:
        FINAL_LOG_PATH = None

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

    if args.track_contribs_changes is True:
        TRACK_CONTRIB_CHANGES = True

    if args.no_monitor_events is True:
        DO_NOT_MONITOR_GITHUB_EVENTS = True

    if not TRACK_REPOS_CHANGES:
        REPO_NOTIFICATION = False
        REPO_UPDATE_DATE_NOTIFICATION = False

    if not TRACK_CONTRIB_CHANGES:
        CONTRIB_NOTIFICATION = False

    if DO_NOT_MONITOR_GITHUB_EVENTS:
        EVENT_NOTIFICATION = False

    if SMTP_HOST.startswith("your_smtp_server_"):
        EVENT_NOTIFICATION = False
        PROFILE_NOTIFICATION = False
        REPO_NOTIFICATION = False
        REPO_UPDATE_DATE_NOTIFICATION = False
        CONTRIB_NOTIFICATION = False
        ERROR_NOTIFICATION = False

    print(f"* GitHub polling interval:\t[ {display_time(GITHUB_CHECK_INTERVAL)} ]")
    print(f"* Email notifications:\t\t[profile changes = {PROFILE_NOTIFICATION}] [new events = {EVENT_NOTIFICATION}]\n*\t\t\t\t[repos changes = {REPO_NOTIFICATION}] [repos update date = {REPO_UPDATE_DATE_NOTIFICATION}]\n*\t\t\t\t[contrib changes = {CONTRIB_NOTIFICATION}] [errors = {ERROR_NOTIFICATION}]")
    print(f"* GitHub API URL:\t\t{GITHUB_API_URL}")
    print(f"* Track repos changes:\t\t{TRACK_REPOS_CHANGES}")
    print(f"* Track contrib changes:\t{TRACK_CONTRIB_CHANGES}")
    print(f"* Monitor GitHub events:\t{not DO_NOT_MONITOR_GITHUB_EVENTS}")
    print(f"* Get owned repos only:\t\t{not GET_ALL_REPOS}")
    print(f"* Liveness check:\t\t{bool(LIVENESS_CHECK_INTERVAL)}" + (f" ({display_time(LIVENESS_CHECK_INTERVAL)})" if LIVENESS_CHECK_INTERVAL else ""))
    print(f"* CSV logging enabled:\t\t{bool(CSV_FILE)}" + (f" ({CSV_FILE})" if CSV_FILE else ""))
    print(f"* Output logging enabled:\t{not DISABLE_LOGGING}" + (f" ({FINAL_LOG_PATH})" if not DISABLE_LOGGING else ""))
    print(f"* Configuration file:\t\t{cfg_path}")
    print(f"* Dotenv file:\t\t\t{env_path or 'None'}")
    print(f"* Local timezone:\t\t{LOCAL_TIMEZONE}")

    out = f"\nMonitoring GitHub user {args.username}"
    print(out)
    print("-" * len(out))

    # We define signal handlers only for Linux, Unix & MacOS since Windows has limited number of signals supported
    if platform.system() != 'Windows':
        signal.signal(signal.SIGUSR1, toggle_profile_changes_notifications_signal_handler)
        signal.signal(signal.SIGUSR2, toggle_new_events_notifications_signal_handler)
        signal.signal(signal.SIGCONT, toggle_repo_changes_notifications_signal_handler)
        signal.signal(signal.SIGPIPE, toggle_repo_update_date_changes_notifications_signal_handler)
        signal.signal(signal.SIGTRAP, increase_check_signal_handler)
        signal.signal(signal.SIGABRT, decrease_check_signal_handler)
        signal.signal(signal.SIGHUP, reload_secrets_signal_handler)

    github_monitor_user(args.username, CSV_FILE)

    sys.stdout = stdout_bck
    sys.exit(0)


if __name__ == "__main__":
    main()
