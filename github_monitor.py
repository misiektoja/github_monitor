#!/usr/bin/env python3
"""
Author: Michal Szymanski <misiektoja-github@rm-rf.ninja>
v1.8

OSINT tool implementing real-time tracking of Github users activities including profile and repositories changes:
https://github.com/misiektoja/github_monitor/

Python pip3 requirements:

PyGithub
pytz
tzlocal
python-dateutil
requests
"""

VERSION = "1.8"

# ---------------------------
# CONFIGURATION SECTION START
# ---------------------------

# The URL of the Github API
# For Public Web Github use the default: https://api.github.com
# For Github Enterprise change to: https://{your_hostname}/api/v3
# You can also change it by using -x parameter
GITHUB_API_URL = "https://api.github.com"

# Get your Github personal access token (classic) by going to: https://github.com/settings/apps
# Then click Personal access tokens -> Tokens (classic) -> Generate new token (classic)
# Put the token value below (or use -t parameter)
GITHUB_TOKEN = "your_github_classic_personal_access_token"

# SMTP settings for sending email notifications, you can leave it as it is below and no notifications will be sent
SMTP_HOST = "your_smtp_server_ssl"
SMTP_PORT = 587
SMTP_USER = "your_smtp_user"
SMTP_PASSWORD = "your_smtp_password"
SMTP_SSL = True
SENDER_EMAIL = "your_sender_email"
# SMTP_HOST = "your_smtp_server_plaintext"
# SMTP_PORT = 25
# SMTP_USER = "your_smtp_user"
# SMTP_PASSWORD = "your_smtp_password"
# SMTP_SSL = False
# SENDER_EMAIL = "your_sender_email"
RECEIVER_EMAIL = "your_receiver_email"

# How often do we perform checks for user activity, you can also use -c parameter; in seconds
GITHUB_CHECK_INTERVAL = 1800  # 30 mins

# Specify your local time zone so we convert Github API timestamps to your time (for example: 'Europe/Warsaw')
# You can get the list of all time zones supported by pytz like this:
# python3 -c "import pytz; print('\n'.join(pytz.all_timezones))"
# If you leave it as 'Auto' we will try to automatically detect the local timezone
LOCAL_TIMEZONE = 'Auto'

# What kind of events we want to monitor, if you put 'ALL' then all of them will be monitored
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

# How many last events we check when we get signal that last event ID has changed
EVENTS_NUMBER = 15

# How often do we perform alive check by printing "alive check" message in the output; in seconds
TOOL_ALIVE_INTERVAL = 21600  # 6 hours

# URL we check in the beginning to make sure we have internet connectivity
CHECK_INTERNET_URL = 'http://www.google.com/'

# Default value for initial checking of internet connectivity; in seconds
CHECK_INTERNET_TIMEOUT = 5

# The name of the .log file; the tool by default will output its messages to github_monitor_username.log file
GITHUB_LOGFILE = "github_monitor"

# Value used by signal handlers increasing/decreasing the user activity check (GITHUB_CHECK_INTERVAL); in seconds
GITHUB_CHECK_SIGNAL_VALUE = 60  # 1 minute

# -------------------------
# CONFIGURATION SECTION END
# -------------------------

# Width of main horizontal line (─)
HORIZONTAL_LINE1 = 105

# Width of horizontal line for repositories list output (─)
HORIZONTAL_LINE2 = 80

TOOL_ALIVE_COUNTER = TOOL_ALIVE_INTERVAL / GITHUB_CHECK_INTERVAL

stdout_bck = None
csvfieldnames = ['Date', 'Type', 'Name', 'Old', 'New']

event_notification = False
profile_notification = False
repo_notification = False
repo_update_date_notification = False
track_repos_changes = False

# to solve the issue: 'SyntaxError: f-string expression part cannot include a backslash'
nl_ch = "\n"


import sys

if sys.version_info < (3, 10):
    print("* Error: Python version 3.10 or higher required !")
    sys.exit(1)

import time
import string
import os
from datetime import datetime, timezone
from dateutil import relativedelta
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
import pytz
try:
    from tzlocal import get_localzone
except ImportError:
    get_localzone = None
import platform
import re
import ipaddress
from github import Github, Auth, GithubException, UnknownObjectException
from github.GithubException import BadCredentialsException
from itertools import islice
from dateutil.parser import isoparse
import textwrap


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
def check_internet():
    url = CHECK_INTERNET_URL
    try:
        _ = req.get(url, timeout=CHECK_INTERNET_TIMEOUT)
        print("OK")
        return True
    except Exception as e:
        print(f"No connectivity, please check your network - {e}")
        sys.exit(1)


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
        print(f"Error sending email - {e}")
        return 1
    return 0


# Writes CSV entry
def write_csv_entry(csv_file_name, timestamp, object_type, object_name, old, new):
    try:
        csv_file = open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8")
        csvwriter = csv.DictWriter(csv_file, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
        csvwriter.writerow({'Date': timestamp, 'Type': object_type, 'Name': object_name, 'Old': old, 'New': new})
        csv_file.close()
    except Exception:
        raise


def convert_to_local_naive(dt: datetime | None = None):
    tz = pytz.timezone(LOCAL_TIMEZONE)

    if dt is not None:
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)

        dt_local = dt.astimezone(tz)

        return dt_local.replace(tzinfo=None)
    else:
        return None


def now_local_naive():
    return datetime.now(pytz.timezone(LOCAL_TIMEZONE)).replace(microsecond=0, tzinfo=None)


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


# Checks if the timezone name is correct
def is_valid_timezone(tz_name):
    return tz_name in pytz.all_timezones


# Prints and returns the printed text with new line
def print_v(text=""):
    print(text)
    return text + "\n"


# Signal handler for SIGUSR1 allowing to switch email notifications for user's profile changes
def toggle_profile_changes_notifications_signal_handler(sig, frame):
    global profile_notification
    profile_notification = not profile_notification
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications: [profile changes = {profile_notification}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGUSR2 allowing to switch email notifications for user's new events
def toggle_new_events_notifications_signal_handler(sig, frame):
    global event_notification
    event_notification = not event_notification
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications: [new events = {event_notification}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGCONT allowing to switch email notifications for user's repositories changes (except for update date)
def toggle_repo_changes_notifications_signal_handler(sig, frame):
    global repo_notification
    repo_notification = not repo_notification
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications: [repos changes = {repo_notification}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGPIPE allowing to switch email notifications for user's repositories update date changes
def toggle_repo_update_date_changes_notifications_signal_handler(sig, frame):
    global repo_update_date_notification
    repo_update_date_notification = not repo_update_date_notification
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications: [repos update date = {repo_update_date_notification}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGTRAP allowing to increase check timer by GITHUB_CHECK_SIGNAL_VALUE seconds
def increase_check_signal_handler(sig, frame):
    global GITHUB_CHECK_INTERVAL
    GITHUB_CHECK_INTERVAL = GITHUB_CHECK_INTERVAL + GITHUB_CHECK_SIGNAL_VALUE
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Github timers: [check interval: {display_time(GITHUB_CHECK_INTERVAL)}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGABRT allowing to decrease check timer by GITHUB_CHECK_SIGNAL_VALUE seconds
def decrease_check_signal_handler(sig, frame):
    global GITHUB_CHECK_INTERVAL
    if GITHUB_CHECK_INTERVAL - GITHUB_CHECK_SIGNAL_VALUE > 0:
        GITHUB_CHECK_INTERVAL = GITHUB_CHECK_INTERVAL - GITHUB_CHECK_SIGNAL_VALUE
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Github timers: [check interval: {display_time(GITHUB_CHECK_INTERVAL)}]")
    print_cur_ts("Timestamp:\t\t\t")


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
        raise RuntimeError(f"Cannot fetch user {user} details - {e}")

    print(f"\nUsername:\t\t{user_name_str}")
    print(f"User URL:\t\t{user_url}/")
    print(f"Github API URL:\t\t{GITHUB_API_URL}")
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
        print(f"Cannot fetch user's followers list - {e}")

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
        print(f"Cannot fetch user's followings list - {e}")

    g.close()


# Processes items from all passed repositories and returns a list of dictionaries
def github_process_repos(repos_list):
    list_of_repos = []
    stargazers_list = []
    subscribers_list = []
    forked_repos = []

    if repos_list:
        for repo in repos_list:
            try:
                repo_created_date = repo.created_at
                repo_updated_date = repo.updated_at
                stargazers_list = [star.login for star in repo.get_stargazers()]
                subscribers_list = [subscriber.login for subscriber in repo.get_subscribers()]
                forked_repos = [fork.full_name for fork in repo.get_forks()]

                issues = list(repo.get_issues(state='open'))
                pulls = list(repo.get_pulls(state='open'))

                real_issues = [i for i in issues if not i.pull_request]
                issue_count = len(real_issues)
                pr_count = len(pulls)

                issues_list = [f"#{i.number} {i.title} ({i.user.login}) [ {i.html_url} ]" for i in real_issues]
                pr_list = [f"#{pr.number} {pr.title} ({pr.user.login}) [ {pr.html_url} ]" for pr in pulls]

                list_of_repos.append({"name": repo.name, "descr": repo.description, "is_fork": repo.fork, "forks": repo.forks_count, "stars": repo.stargazers_count, "subscribers": repo.subscribers_count, "url": repo.html_url, "language": repo.language, "date": repo_created_date, "update_date": repo_updated_date, "stargazers_list": stargazers_list, "forked_repos": forked_repos, "subscribers_list": subscribers_list, "issues": issue_count, "pulls": pr_count, "issues_list": issues_list, "pulls_list": pr_list})
            except Exception as e:
                print(f"Error while processing info for repo '{repo.name}', skipping for now - {e}")
                print_cur_ts("Timestamp:\t\t\t")
                continue

    return list_of_repos


# Prints a list of public repositories for a GitHub user (-r)
def github_print_repos(user):
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

        repos_count = g_user.public_repos
        repos_list = g_user.get_repos()

        user_name_str = user_login
        if user_name:
            user_name_str += f" ({user_name})"
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user {user} details - {e}")

    print(f"\nUsername:\t\t{user_name_str}")
    print(f"User URL:\t\t{user_url}/")
    print(f"Github API URL:\t\t{GITHUB_API_URL}")
    print(f"Local timezone:\t\t{LOCAL_TIMEZONE}")

    print(f"\nRepositories:\t\t{repos_count}\n")

    try:
        if repos_list:
            print("─" * HORIZONTAL_LINE2)
            for repo in repos_list:
                print(f"🔸 {repo.name} {'(fork)' if repo.fork else ''} \n")

                try:
                    pr_count = repo.get_pulls(state='open').totalCount
                    issue_count = repo.open_issues_count - pr_count
                except Exception:
                    pr_count = "?"
                    issue_count = "?"

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
                print("─" * HORIZONTAL_LINE2)
    except Exception as e:
        raise RuntimeError(f"Cannot fetch user's repositories list - {e}")

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
        raise RuntimeError(f"Cannot fetch user {user} details - {e}")

    print(f"\nUsername:\t\t{user_name_str}")
    print(f"User URL:\t\t{user_url}/")
    print(f"Github API URL:\t\t{GITHUB_API_URL}")
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
        raise RuntimeError(f"Cannot fetch user's starred list - {e}")

    g.close()


# Returns size in human readable format
def human_readable_size(num):
    value = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


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
        repo_name = event.repo.name
        repo_url = event.repo.url.replace("https://api.github.com/repos/", "https://github.com/")
        st += print_v(f"\nRepo name:\t\t\t{repo_name}")
        st += print_v(f"Repo URL:\t\t\t{repo_url}")

        try:
            repo = g.get_repo(event.repo.name)
        except UnknownObjectException:
            repo = None
            st += print_v("\nRepository not found or has been removed")
        except GithubException as e:
            repo = None
            st += print_v(f"\nAn error occurred while getting repo details: {e}")

    if hasattr(event.actor, 'login'):
        if event.actor.login:
            st += print_v(f"\nEvent actor login:\t\t{event.actor.login}")
    if hasattr(event.actor, 'name'):
        if event.actor.name:
            st += print_v(f"Event actor name:\t\t{event.actor.name}")

    if event.payload.get("ref"):
        st += print_v(f"\nObject name:\t\t\t{event.payload.get('ref')}")
    if event.payload.get("ref_type"):
        st += print_v(f"Object type:\t\t\t{event.payload.get('ref_type')}")
    if event.payload.get("description"):
        st += print_v(f"Description:\t\t\t'{event.payload.get('description')}'")

    if event.payload.get("action"):
        st += print_v(f"\nAction:\t\t\t\t{event.payload.get('action')}")

    if event.payload.get("commits"):
        commits = event.payload["commits"]
        commits_total = len(commits)
        st += print_v(f"\nNumber of commits:\t\t{commits_total}")
        for commit_count, commit in enumerate(commits, start=1):
            st += print_v(f"\n=== Commit {commit_count}/{commits_total} ===")
            st += print_v("." * HORIZONTAL_LINE1)

            commit_details = None
            if repo:
                commit_details = repo.get_commit(commit["sha"])

            if commit_details:
                commit_date = commit_details.commit.author.date
                st += print_v(f" - Commit date:\t\t\t{get_date_from_ts(commit_date)}")

            st += print_v(f" - Commit SHA:\t\t\t{commit['sha']}")
            st += print_v(f" - Commit author:\t\t{commit['author']['name']}")

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
                        st += print_v(f"     • '{f.filename}' — {f.status} (+{f.additions} / -{f.deletions})")

            st += print_v(f"\n - Commit message:\t\t'{commit['message']}'")
            st += print_v("." * HORIZONTAL_LINE1)

    if event.payload.get("commits") == []:
        st += print_v("\nNo new commits (forced push, tag push, branch reset or other ref update)")

    if event.payload.get("release"):
        st += print_v(f"\nRelease name:\t\t\t{event.payload['release'].get('name')}")
        st += print_v(f"Release tag name:\t\t{event.payload['release'].get('tag_name')}")
        st += print_v(f"Release URL:\t\t\t{event.payload['release'].get('html_url')}")

        st += print_v(f"\nPublished by:\t\t\t{event.payload['release']['author']['login']}")
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
                    st += print_v(f"\nCould not fetch parent comment (ID {parent_id}): {e}")
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
def github_list_events(user, number, csv_file_name, csv_enabled, csv_exists):
    events = []
    available_events = 0

    try:
        if csv_file_name:
            csv_file = open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8")
            csvwriter = csv.DictWriter(csv_file, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
            if not csv_exists:
                csvwriter.writeheader()
            csv_file.close()
    except Exception as e:
        print(f"* Error - {e}")

    if csv_file_name:
        list_operation = "* Listing & saving"
    else:
        list_operation = "* Listing"

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
        print(f"Cannot fetch user details - {e}")
        return

    print(f"Username:\t\t\t{user_name_str}")
    print(f"User URL:\t\t\t{user_url}/")
    print(f"Github API URL:\t\t\t{GITHUB_API_URL}")
    if csv_enabled:
        print(f"CSV export enabled:\t\t{csv_enabled} ({csv_file_name})")
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
                        print(f"\nWarning: cannot fetch all event details, skipping - {e}")
                        print_cur_ts("\nTimestamp:\t\t\t")
                        continue
                    try:
                        if csv_file_name:
                            write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                    except Exception as e:
                        print(f"* Cannot write CSV entry - {e}")
                    print_cur_ts("\nTimestamp:\t\t\t")
        except Exception as e:
            print(f"Cannot fetch events - {e}")


# Detects and reports changes in a user's profile-level entities (followers, followings, public repos, starred repos)
def handle_profile_change(label, count_old, count_new, list_old, raw_list, user, csv_file_name, field):
    try:
        list_new = []
        list_new = [getattr(item, field) for item in raw_list]
        if not list_new and count_new > 0:
            return list_old, count_old
    except Exception as e:
        print(f"Error while trying to get the list of {label.lower()} - {e}")
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
            print(f"* Cannot write CSV entry - {e}")

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
                print(f"* Cannot write CSV entry - {e}")
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
                print(f"* Cannot write CSV entry - {e}")
        print()

    if diff == 0:
        m_subject = f"Github user {user} {label.lower()} list changed"
        m_body = (f"{label} list changed {label_context} user {user}\n"
                  f"{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}")
    else:
        m_subject = f"Github user {user} {label.lower()} number has changed! ({diff_str}, {old_count} -> {new_count})"
        m_body = (f"{label} number changed {label_context} user {user} from {old_count} to {new_count} ({diff_str})\n"
                  f"{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}")

    if profile_notification:
        print(f"Sending email notification to {RECEIVER_EMAIL}")
        send_email(m_subject, m_body, "", SMTP_SSL)

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
            print(f"* Cannot write CSV entry - {e}")

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
                    print(f"* Cannot write CSV entry - {e}")
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
                    print(f"* Cannot write CSV entry - {e}")
            print()

    if diff == 0:
        m_subject = f"Github user {user} {label.lower()} list changed for repo '{repo_name}'!"
        m_body = (f"* Repo '{repo_name}': {label.lower()} list changed\n"
                  f"* Repo URL: {repo_url}\n{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}")
    else:
        m_subject = f"Github user {user} number of {label.lower()} for repo '{repo_name}' has changed! ({diff_str}, {old_count} -> {new_count})"
        m_body = (f"* Repo '{repo_name}': number of {label.lower()} changed from {old_count} to {new_count} ({diff_str})\n"
                  f"* Repo URL: {repo_url}\n{removed_mbody}{removed_list_str}{added_mbody}{added_list_str}\n"
                  f"Check interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}")

    if repo_notification:
        print(f"Sending email notification to {RECEIVER_EMAIL}")
        send_email(m_subject, m_body, "", SMTP_SSL)
    print_cur_ts("Timestamp:\t\t\t")


# Main function that monitors activity of the specified GitHub user
def github_monitor_user(user, error_notification, csv_file_name, csv_exists):

    try:
        if csv_file_name:
            csv_file = open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8")
            csvwriter = csv.DictWriter(csv_file, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
            if not csv_exists:
                csvwriter.writeheader()
            csv_file.close()
    except Exception as e:
        print(f"* Error - {e}")

    followers_count = 0
    followings_count = 0
    repos_count = 0
    starred_count = 0
    available_events = 0
    events = []
    repos_list = []
    event_date: datetime | None = None

    try:
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(base_url=GITHUB_API_URL, auth=auth)
        g_user_myself = g.get_user()
        user_myself_login = g_user_myself.login
        user_myself_name = g_user_myself.name

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
        repos_count = g_user.public_repos

        followers_list = g_user.get_followers()
        followings_list = g_user.get_following()
        repos_list = g_user.get_repos()

        starred_list = g_user.get_starred()
        starred_count = starred_list.totalCount

        if not do_not_monitor_github_events:
            events = list(islice(g_user.get_events(), EVENTS_NUMBER))
            available_events = len(events)

    except Exception as e:
        print(f"* Error - {e}")
        sys.exit(1)

    last_event_id = 0
    last_event_ts: datetime | None = None
    events_list_of_ids = set()

    if not do_not_monitor_github_events:
        if available_events:
            try:
                for event in reversed(events):
                    events_list_of_ids.add(event.id)

                newest = events[0]
                last_event_id = newest.id
                if last_event_id:
                    last_event_ts = newest.created_at
            except Exception as e:
                print(f"* Cannot get event IDs / timestamps - {e}\n")
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

    last_event_id_old = last_event_id
    last_event_ts_old = last_event_ts
    events_list_of_ids_old = events_list_of_ids.copy()

    user_myself_name_str = user_myself_login
    if user_myself_name:
        user_myself_name_str += f" ({user_myself_name})"

    print(f"Token belongs to:\t\t{user_myself_name_str}")

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

    print(f"\nAccount creation date:\t\t{get_date_from_ts(account_created_date)} ({calculate_timespan(int(time.time()), account_created_date, show_seconds=False)} ago)")
    print(f"Account updated date:\t\t{get_date_from_ts(account_updated_date)} ({calculate_timespan(int(time.time()), account_updated_date, show_seconds=False)} ago)")
    account_updated_date_old = account_updated_date

    print(f"\nFollowers:\t\t\t{followers_count}")
    print(f"Followings:\t\t\t{followings_count}")
    print(f"Repositories:\t\t\t{repos_count}")
    print(f"Starred repos:\t\t\t{starred_count}")
    if not do_not_monitor_github_events:
        print(f"Available events:\t\t{available_events}{'+' if available_events == EVENTS_NUMBER else ''}")

    if bio:
        print(f"\nBio:\n\n'{bio}'")

    print_cur_ts("\nTimestamp:\t\t\t")

    list_of_repos = []
    if repos_list and track_repos_changes:
        print("Processing list of public repositories (be patient, it might take a while) ...")
        try:
            list_of_repos = github_process_repos(repos_list)
        except Exception as e:
            print(f"Cannot process list of public repositories - {e}")
        print_cur_ts("\nTimestamp:\t\t\t")

    list_of_repos_old = list_of_repos

    if not do_not_monitor_github_events:
        print(f"Latest event:\n")

        if available_events == 0:
            print("There are no events yet")
        else:
            try:
                github_print_event(events[0], g, True)
            except Exception as e:
                print(f"\nWarning: cannot fetch last event details - {e}")

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
        print(f"* Error - {e}")
        sys.exit(1)

    g.close()

    time.sleep(GITHUB_CHECK_INTERVAL)
    alive_counter = 0
    email_sent = False

    # main loop
    while True:

        try:
            g_user = g.get_user(user)
            email_sent = False

        except (GithubException, Exception) as e:
            print(f"Error, retrying in {display_time(GITHUB_CHECK_INTERVAL)} - {e}")

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

            if should_notify and error_notification and not email_sent:
                m_subject = f"github_monitor: session error! (user: {user})"
                m_body = f"{reason_msg}\n{e}{get_cur_ts(nl_ch + nl_ch + 'Timestamp: ')}"
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)
                email_sent = True

            print_cur_ts("Timestamp:\t\t\t")
            time.sleep(GITHUB_CHECK_INTERVAL)
            continue

        # Changed followings
        followings_raw = list(g_user.get_following())
        followings_count = g_user.following
        followings_old, followings_old_count = handle_profile_change("Followings", followings_old_count, followings_count, followings_old, followings_raw, user, csv_file_name, field="login")

        # Changed followers
        followers_raw = list(g_user.get_followers())
        followers_count = g_user.followers
        followers_old, followers_old_count = handle_profile_change("Followers", followers_old_count, followers_count, followers_old, followers_raw, user, csv_file_name, field="login")

        # Changed public repositories
        repos_raw = list(g_user.get_repos())
        repos_count = g_user.public_repos
        repos_old, repos_old_count = handle_profile_change("Repos", repos_old_count, repos_count, repos_old, repos_raw, user, csv_file_name, field="name")

        # Changed starred repositories
        starred_list = g_user.get_starred()
        starred_raw = list(starred_list)
        starred_count = starred_list.totalCount
        starred_old, starred_old_count = handle_profile_change("Starred Repos", starred_old_count, starred_count, starred_old, starred_raw, user, csv_file_name, field="full_name")

        # Changed bio
        bio = g_user.bio
        if bio != bio_old:
            print(f"* Bio has changed for user {user} !\n")
            print(f"Old bio:\n\n{bio_old}\n")
            print(f"New bio:\n\n{bio}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Bio", user, bio_old, bio)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} bio has changed!"
            m_body = f"Github user {user} bio has changed\n\nOld bio:\n\n{bio_old}\n\nNew bio:\n\n{bio}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            bio_old = bio
            print_cur_ts("Timestamp:\t\t\t")

        # Changed location
        location = g_user.location
        if location != location_old:
            print(f"* Location has changed for user {user} !\n")
            print(f"Old location:\t\t\t{location_old}\n")
            print(f"New location:\t\t\t{location}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Location", user, location_old, location)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} location has changed!"
            m_body = f"Github user {user} location has changed\n\nOld location: {location_old}\n\nNew location: {location}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            location_old = location
            print_cur_ts("Timestamp:\t\t\t")

        # Changed user name
        user_name = g_user.name
        if user_name != user_name_old:
            print(f"* User name has changed for user {user} !\n")
            print(f"Old user name:\t\t\t{user_name_old}\n")
            print(f"New user name:\t\t\t{user_name}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "User Name", user, user_name_old, user_name)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} name has changed!"
            m_body = f"Github user {user} name has changed\n\nOld user name: {user_name_old}\n\nNew user name: {user_name}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            user_name_old = user_name
            print_cur_ts("Timestamp:\t\t\t")

        # Changed company
        company = g_user.company
        if company != company_old:
            print(f"* User company has changed for user {user} !\n")
            print(f"Old company:\t\t\t{company_old}\n")
            print(f"New company:\t\t\t{company}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Company", user, company_old, company)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} company has changed!"
            m_body = f"Github user {user} company has changed\n\nOld company: {company_old}\n\nNew company: {company}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            company_old = company
            print_cur_ts("Timestamp:\t\t\t")

        # Changed email
        email = g_user.email
        if email != email_old:
            print(f"* User email has changed for user {user} !\n")
            print(f"Old email:\t\t\t{email_old}\n")
            print(f"New email:\t\t\t{email}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Email", user, email_old, email)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} email has changed!"
            m_body = f"Github user {user} email has changed\n\nOld email: {email_old}\n\nNew email: {email}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            email_old = email
            print_cur_ts("Timestamp:\t\t\t")

        # Changed blog URL
        blog = g_user.blog
        if blog != blog_old:
            print(f"* User blog URL has changed for user {user} !\n")
            print(f"Old blog URL:\t\t\t{blog_old}\n")
            print(f"New blog URL:\t\t\t{blog}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Blog URL", user, blog_old, blog)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} blog URL has changed!"
            m_body = f"Github user {user} blog URL has changed\n\nOld blog URL: {blog_old}\n\nNew blog URL: {blog}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            blog_old = blog
            print_cur_ts("Timestamp:\t\t\t")

        # Changed account update date
        account_updated_date = g_user.updated_at
        if account_updated_date != account_updated_date_old:
            print(f"* User account has been updated for user {user} ! (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})\n")
            print(f"Old account update date:\t{get_date_from_ts(account_updated_date_old)}\n")
            print(f"New account update date:\t{get_date_from_ts(account_updated_date)}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, now_local_naive(), "Account Update Date", user, convert_to_local_naive(account_updated_date_old), convert_to_local_naive(account_updated_date))
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} account has been updated! (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})"
            m_body = f"Github user {user} account has been updated (after {calculate_timespan(account_updated_date, account_updated_date_old, show_seconds=False, granularity=2)})\n\nOld account update date: {get_date_from_ts(account_updated_date_old)}\n\nNew account update date: {get_date_from_ts(account_updated_date)}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            account_updated_date_old = account_updated_date
            print_cur_ts("Timestamp:\t\t\t")

        list_of_repos = []

        # Changed repos details
        if track_repos_changes:
            repos_list = g_user.get_repos()
            if repos_list:
                try:
                    list_of_repos = github_process_repos(repos_list)
                    list_of_repos_ok = True
                except Exception as e:
                    list_of_repos = list_of_repos_old
                    print(f"Cannot process list of public repositories, keeping old list - {e}")
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
                                        print(f"* Cannot write CSV entry - {e}")
                                    m_subject = f"Github user {user} repo '{r_name}' update date has changed ! (after {calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)})"
                                    m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"
                                    if repo_update_date_notification:
                                        print(f"Sending email notification to {RECEIVER_EMAIL}")
                                        send_email(m_subject, m_body, "", SMTP_SSL)
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
                                        print(f"* Cannot write CSV entry - {e}")
                                    m_subject = f"Github user {user} repo '{r_name}' description has changed !"
                                    m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"
                                    if repo_notification:
                                        print(f"Sending email notification to {RECEIVER_EMAIL}")
                                        send_email(m_subject, m_body, "", SMTP_SSL)
                                    print_cur_ts("Timestamp:\t\t\t")

                    list_of_repos_old = list_of_repos

        # New Github events
        if not do_not_monitor_github_events:
            events = list(islice(g_user.get_events(), EVENTS_NUMBER))
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
                    print(f"* Cannot get last event ID / timestamp - {e}")
                    print_cur_ts("Timestamp:\t\t\t")

            events_list_of_ids = set()
            first_new = True

            # New events showed up
            if last_event_id and last_event_id != last_event_id_old:

                for event in reversed(events):

                    events_list_of_ids.add(event.id)

                    if event.id in events_list_of_ids_old:
                        continue

                    if last_event_ts_old and event.created_at <= last_event_ts_old:
                        continue

                    if event.type in EVENTS_TO_MONITOR or 'ALL' in EVENTS_TO_MONITOR:

                        event_date = None
                        repo_name = ""
                        repo_url = ""
                        event_text = ""

                        try:
                            event_date, repo_name, repo_url, event_text = github_print_event(event, g, first_new, last_event_ts_old)
                        except Exception as e:
                            print(f"\nWarning: cannot fetch all event details - {e}")

                        first_new = False

                        if event_date and repo_name and event_text:

                            try:
                                if csv_file_name:
                                    write_csv_entry(csv_file_name, convert_to_local_naive(event_date), str(event.type), str(repo_name), "", "")
                            except Exception as e:
                                print(f"* Cannot write CSV entry - {e}")

                            m_subject = f"Github user {user} has new {event.type} (repo: {repo_name})"
                            m_body = f"Github user {user} has new {event.type} event\n\n{event_text}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts(nl_ch + 'Timestamp: ')}"

                            if event_notification:
                                print(f"\nSending email notification to {RECEIVER_EMAIL}")
                                send_email(m_subject, m_body, "", SMTP_SSL)

                        print_cur_ts("Timestamp:\t\t\t")

                last_event_id_old = last_event_id
                last_event_ts_old = last_event_ts
                events_list_of_ids_old = events_list_of_ids.copy()

        alive_counter += 1

        if alive_counter >= TOOL_ALIVE_COUNTER:
            print_cur_ts("Alive check, timestamp: ")
            alive_counter = 0

        g.close()

        time.sleep(GITHUB_CHECK_INTERVAL)


if __name__ == "__main__":

    stdout_bck = sys.stdout

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
    except Exception:
        print("* Cannot clear the screen contents")

    print(f"Github Monitoring Tool v{VERSION}\n")

    parser = argparse.ArgumentParser("github_monitor")
    parser.add_argument("GITHUB_USERNAME", nargs="?", help="Github username", type=str)
    parser.add_argument("-t", "--github_token", help="Github personal access token (classic) to override the value defined within the script (GITHUB_TOKEN)", type=str)
    parser.add_argument("-x", "--github_url", help="Github API URL to override the default value defined within the script (GITHUB_API_URL)", type=str)
    parser.add_argument("-p", "--profile_notification", help="Send email notification once user's profile changes (e.g. changed followers, followings, starred repos, username, email, bio, location, blog URL, number of repositories)", action='store_true')
    parser.add_argument("-s", "--event_notification", help="Send email notification once new Github events show up for the user (e.g. new pushes, PRs, issues, forks, releases etc.)", action='store_true')
    parser.add_argument("-q", "--repo_notification", help="Send email notification once changes in user's repositories are detected (e.g. changed stargazers, watchers, forks, issues, PRs, description etc., except for update date), works only if tracking of repos changes is enabled (-j)", action='store_true')
    parser.add_argument("-u", "--repo_update_date_notification", help="Send email notification once changes in user's repositories update date are detected, works only if tracking of repos changes is enabled (-j); these email notifications might be quite verbose, so be careful", action='store_true')
    parser.add_argument("-e", "--error_notification", help="Disable sending email notifications in case of errors like expired token", action='store_false')
    parser.add_argument("-c", "--check_interval", help="Time between monitoring checks, in seconds", type=int)
    parser.add_argument("-b", "--csv_file", help="Write info about new events & profile changes to CSV file", type=str, metavar="CSV_FILENAME")
    parser.add_argument("-j", "--track_repos_changes", help="Track changes of user repos like changed stargazers, watchers, forks, description, update date etc.", action='store_true')
    parser.add_argument("-k", "--do_not_monitor_github_events", help="Do not monitor Github events for the user (e.g. new pushes, PRs, issues, forks, releases etc.)", action='store_true')
    parser.add_argument("-r", "--repos", help="List repositories for the user with some basic statistics", action='store_true')
    parser.add_argument("-g", "--starred_repos", help="List repositories starred by the user", action='store_true')
    parser.add_argument("-f", "--followers_and_followings", help="List followers & followings for the user", action='store_true')
    parser.add_argument("-l", "--list_recent_events", help="List recent Github events for the user", action='store_true')
    parser.add_argument("-n", "--number_of_recent_events", help="Number of Github events to display if used with -l", type=int)
    parser.add_argument("-d", "--disable_logging", help="Disable logging to file 'github_monitor_user.log' file", action='store_true')
    parser.add_argument("-z", "--send_test_email_notification", help="Send test email notification to verify SMTP settings defined in the script", action='store_true')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

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

    sys.stdout.write("* Checking internet connectivity ... ")
    sys.stdout.flush()
    check_internet()
    print("")

    if args.send_test_email_notification:
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

    if not args.GITHUB_USERNAME:
        print("* Error: GITHUB_USERNAME argument is required !")
        sys.exit(1)

    if args.github_url:
        GITHUB_API_URL = args.github_url

    if not GITHUB_API_URL:
        print("* Error: GITHUB_API_URL (-x / --github_url) value is empty")
        sys.exit(1)

    if args.followers_and_followings:
        try:
            github_print_followers_and_followings(args.GITHUB_USERNAME)
        except Exception as e:
            print(f"* Error - {e}")
            sys.exit(1)
        sys.exit(0)

    if args.repos:
        try:
            github_print_repos(args.GITHUB_USERNAME)
        except Exception as e:
            print(f"* Error - {e}")
            sys.exit(1)
        sys.exit(0)

    if args.starred_repos:
        try:
            github_print_starred_repos(args.GITHUB_USERNAME)
        except Exception as e:
            print(f"* Error - {e}")
            sys.exit(1)
        sys.exit(0)

    if args.check_interval:
        GITHUB_CHECK_INTERVAL = args.check_interval
        TOOL_ALIVE_COUNTER = TOOL_ALIVE_INTERVAL / GITHUB_CHECK_INTERVAL

    if args.csv_file:
        csv_enabled = True
        csv_exists = os.path.isfile(args.csv_file)
        try:
            csv_file = open(args.csv_file, 'a', newline='', buffering=1, encoding="utf-8")
        except Exception as e:
            print(f"* Error: CSV file cannot be opened for writing - {e}")
            sys.exit(1)
        csv_file.close()
    else:
        csv_enabled = False
        csv_file = None
        csv_exists = False

    if args.list_recent_events:
        if args.number_of_recent_events and args.number_of_recent_events > 0:
            events_n = args.number_of_recent_events
        else:
            events_n = 5
        try:
            github_list_events(args.GITHUB_USERNAME, events_n, args.csv_file, csv_enabled, csv_exists)
        except Exception as e:
            print(f"* Error - {e}")
            sys.exit(1)
        sys.exit(0)

    if not args.disable_logging:
        GITHUB_LOGFILE = f"{GITHUB_LOGFILE}_{args.GITHUB_USERNAME}.log"
        sys.stdout = Logger(GITHUB_LOGFILE)

    event_notification = args.event_notification
    profile_notification = args.profile_notification
    repo_notification = args.repo_notification
    repo_update_date_notification = args.repo_update_date_notification
    track_repos_changes = args.track_repos_changes
    do_not_monitor_github_events = args.do_not_monitor_github_events
    error_notification = args.error_notification

    if not track_repos_changes:
        repo_notification = False
        repo_update_date_notification = False

    if do_not_monitor_github_events:
        event_notification = False

    if SMTP_HOST == "your_smtp_server_ssl" or SMTP_HOST == "your_smtp_server_plaintext":
        event_notification = False
        profile_notification = False
        repo_notification = False
        repo_update_date_notification = False
        error_notification = False

    print(f"* Github timers:\t\t[check interval: {display_time(GITHUB_CHECK_INTERVAL)}]")
    print(f"* Email notifications:\t\t[profile changes = {profile_notification}] [new events = {event_notification}]\n*\t\t\t\t[repos changes = {repo_notification}] [repos update date = {repo_update_date_notification}]\n*\t\t\t\t[errors = {error_notification}]")
    print(f"* Github API URL:\t\t{GITHUB_API_URL}")
    print(f"* Track repos changes:\t\t{track_repos_changes}")
    print(f"* Monitor Github events:\t{not do_not_monitor_github_events}")
    if not args.disable_logging:
        print(f"* Output logging enabled:\t{not args.disable_logging} ({GITHUB_LOGFILE})")
    else:
        print(f"* Output logging enabled:\t{not args.disable_logging}")
    if csv_enabled:
        print(f"* CSV logging enabled:\t\t{csv_enabled} ({args.csv_file})")
    else:
        print(f"* CSV logging enabled:\t\t{csv_enabled}")
    print(f"* Local timezone:\t\t{LOCAL_TIMEZONE}")

    out = f"\nMonitoring Github user {args.GITHUB_USERNAME}"
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

    github_monitor_user(args.GITHUB_USERNAME, error_notification, args.csv_file, csv_exists)

    sys.stdout = stdout_bck
    sys.exit(0)
