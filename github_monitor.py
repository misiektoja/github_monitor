#!/usr/bin/env python3
"""
Author: Michal Szymanski <misiektoja-github@rm-rf.ninja>
v1.2

Script implementing real-time monitoring of Github users activity:
https://github.com/misiektoja/github_monitor/

Python pip3 requirements:

PyGithub
pytz
tzlocal
python-dateutil
requests
"""

VERSION = 1.2

# ---------------------------
# CONFIGURATION SECTION START
# ---------------------------

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
GITHUB_CHECK_INTERVAL = 600  # 10 mins

# Specify your local time zone so we convert Github API timestamps to your time (for example: 'Europe/Warsaw')
# If you leave it as 'Auto' we will try to automatically detect the local timezone
LOCAL_TIMEZONE = 'Auto'

# What kind of events we want to monitor, if you put 'ALL' then all of them will be monitored
EVENTS_TO_MONITOR = ['ALL', 'PushEvent', 'PullRequestReviewEvent', 'CreateEvent', 'DeleteEvent', 'PullRequestEvent', 'PullRequestReviewCommentEvent', 'IssuesEvent', 'WatchEvent', 'ForkEvent', 'ReleaseEvent', 'IssueCommentEvent']

# How many last events we check when we get signal that last event ID has changed
EVENTS_NUMBER = 10

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

TOOL_ALIVE_COUNTER = TOOL_ALIVE_INTERVAL / GITHUB_CHECK_INTERVAL

stdout_bck = None
csvfieldnames = ['Date', 'Type', 'Name', 'Old', 'New']

event_notification = False
profile_notification = False
track_repos_changes = False


import sys
import time
import string
import os
from datetime import datetime
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
    pass
import platform
import re
import ipaddress
from github import Github
from github import Auth


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


# Function to check internet connectivity
def check_internet():
    url = CHECK_INTERNET_URL
    try:
        _ = req.get(url, timeout=CHECK_INTERNET_TIMEOUT)
        print("OK")
        return True
    except Exception as e:
        print(f"No connectivity, please check your network - {e}")
        sys.exit(1)
    return False


# Function to convert absolute value of seconds to human readable format
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


# Function to calculate time span between two timestamps in seconds
def calculate_timespan(timestamp1, timestamp2, show_weeks=True, show_hours=True, show_minutes=True, show_seconds=True, granularity=3):
    result = []
    intervals = ['years', 'months', 'weeks', 'days', 'hours', 'minutes', 'seconds']
    ts1 = timestamp1
    ts2 = timestamp2

    if type(timestamp1) is int:
        dt1 = datetime.fromtimestamp(int(ts1))
    elif type(timestamp1) is float:
        ts1 = int(round(ts1))
        dt1 = datetime.fromtimestamp(ts1)
    elif type(timestamp1) is datetime:
        dt1 = timestamp1
        ts1 = int(round(dt1.timestamp()))
    else:
        return ""

    if type(timestamp2) is int:
        dt2 = datetime.fromtimestamp(int(ts2))
    elif type(timestamp2) is float:
        ts2 = int(round(ts2))
        dt2 = datetime.fromtimestamp(ts2)
    elif type(timestamp2) is datetime:
        dt2 = timestamp2
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
        weeks = date_diff.weeks
        if not show_weeks:
            weeks = 0
        days = date_diff.days
        if weeks > 0:
            days = days - (weeks * 7)
        hours = date_diff.hours
        if (not show_hours and ts_diff > 86400):
            hours = 0
        minutes = date_diff.minutes
        if (not show_minutes and ts_diff > 3600):
            minutes = 0
        seconds = date_diff.seconds
        if (not show_seconds and ts_diff > 60):
            seconds = 0
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


# Function to send email notification
def send_email(subject, body, body_html, use_ssl):
    fqdn_re = re.compile(r'(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}\.?$)')
    email_re = re.compile(r'[^@]+@[^@]+\.[^@]+')

    try:
        is_ip = ipaddress.ip_address(str(SMTP_HOST))
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
            smtpObj = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            smtpObj.starttls(context=ssl_context)
        else:
            smtpObj = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        smtpObj.login(SMTP_USER, SMTP_PASSWORD)
        email_msg = MIMEMultipart('alternative')
        email_msg["From"] = SENDER_EMAIL
        email_msg["To"] = RECEIVER_EMAIL
        email_msg["Subject"] = Header(subject, 'utf-8')

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


# Function to write CSV entry
def write_csv_entry(csv_file_name, timestamp, object_type, object_name, old, new):
    try:
        csv_file = open(csv_file_name, 'a', newline='', buffering=1, encoding="utf-8")
        csvwriter = csv.DictWriter(csv_file, fieldnames=csvfieldnames, quoting=csv.QUOTE_NONNUMERIC)
        csvwriter.writerow({'Date': timestamp, 'Type': object_type, 'Name': object_name, 'Old': old, 'New': new})
        csv_file.close()
    except Exception as e:
        raise


# Function to return the timestamp in human readable format; eg. Sun, 21 Apr 2024, 15:08:45
def get_cur_ts(ts_str=""):
    return (f"{ts_str}{calendar.day_abbr[(datetime.fromtimestamp(int(time.time()))).weekday()]}, {datetime.fromtimestamp(int(time.time())).strftime("%d %b %Y, %H:%M:%S")}")


# Function to print the current timestamp in human readable format; eg. Sun, 21 Apr 2024, 15:08:45
def print_cur_ts(ts_str=""):
    print(get_cur_ts(str(ts_str)))
    print("---------------------------------------------------------------------------------------------------------")


# Function to return the timestamp/datetime object in human readable format (long version); eg. Sun, 21 Apr 2024, 15:08:45
def get_date_from_ts(ts):
    if type(ts) is datetime:
        ts_new = int(round(ts.timestamp()))
    elif type(ts) is int:
        ts_new = ts
    elif type(ts) is float:
        ts_new = int(round(ts))
    else:
        return ""

    return (f"{calendar.day_abbr[(datetime.fromtimestamp(ts_new)).weekday()]} {datetime.fromtimestamp(ts_new).strftime("%d %b %Y, %H:%M:%S")}")


# Function to return the timestamp/datetime object in human readable format (short version); eg.
# Sun 21 Apr 15:08
# Sun 21 Apr 24, 15:08 (if show_year == True and current year is different)
# Sun 21 Apr (if show_hour == False)
def get_short_date_from_ts(ts, show_year=False, show_hour=True):
    if type(ts) is datetime:
        ts_new = int(round(ts.timestamp()))
    elif type(ts) is int:
        ts_new = ts
    elif type(ts) is float:
        ts_new = int(round(ts))
    else:
        return ""

    if show_hour:
        hour_strftime = " %H:%M"
    else:
        hour_strftime = ""

    if show_year and int(datetime.fromtimestamp(ts_new).strftime("%Y")) != int(datetime.now().strftime("%Y")):
        if show_hour:
            hour_prefix = ","
        else:
            hour_prefix = ""
        return (f"{calendar.day_abbr[(datetime.fromtimestamp(ts_new)).weekday()]} {datetime.fromtimestamp(ts_new).strftime(f"%d %b %y{hour_prefix}{hour_strftime}")}")
    else:
        return (f"{calendar.day_abbr[(datetime.fromtimestamp(ts_new)).weekday()]} {datetime.fromtimestamp(ts_new).strftime(f"%d %b{hour_strftime}")}")


# Function to convert UTC string returned by Github API to datetime object in specified timezone
def convert_utc_str_to_tz_datetime(utc_string, timezone, version=1):
    try:
        if version == 1:
            utc_string_sanitize = utc_string.split('+', 1)[0]
            utc_string_sanitize = utc_string_sanitize.split('.', 1)[0]
            dt_utc = datetime.strptime(utc_string_sanitize, '%Y-%m-%d %H:%M:%S')
        elif version == 2:
            utc_string_sanitize = utc_string
            dt_utc = datetime.strptime(utc_string_sanitize, '%Y-%m-%dT%H:%M:%SZ')

        old_tz = pytz.timezone("UTC")
        new_tz = pytz.timezone(timezone)
        dt_new_tz = old_tz.localize(dt_utc).astimezone(new_tz)
        return dt_new_tz
    except Exception as e:
        return datetime.fromtimestamp(0)


def print_v(text=""):
    print(text)
    return text + "\n"


# Signal handler for SIGUSR1 allowing to switch email notifications for profile changes
def toggle_profile_changes_notifications_signal_handler(sig, frame):
    global profile_notification
    profile_notification = not profile_notification
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications: [profile changes = {profile_notification}]")
    print_cur_ts("Timestamp:\t\t\t")


# Signal handler for SIGUSR2 allowing to switch email notifications for new events
def toggle_new_events_notifications_signal_handler(sig, frame):
    global event_notification
    event_notification = not event_notification
    sig_name = signal.Signals(sig).name
    print(f"* Signal {sig_name} received")
    print(f"* Email notifications: [new events = {event_notification}]")
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


# Function converting Github API URL to HTML URL
def github_convert_api_to_html_url(url):
    html_url = ""
    if "https://api.github.com/repos/" in url:
        url_suffix = url.split('https://api.github.com/repos/', 1)[1]
        html_url = "https://github.com/" + url_suffix
    return html_url


# Function printing followers & followings for Github user
def github_print_followers_and_followings(user):
    print(f"Getting followers & followings for user '{user}' ...")

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)

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

    print(f"\nUsername:\t{user_name_str}")
    print(f"URL:\t\t{user_url}/")

    print(f"\nFollowers:\t{followers_count}")
    if followers_list:

        for follower in followers_list:
            follower_str = f"\n- {follower.login}"
            if follower.name:
                follower_str += f" ({follower.name})"
            if follower.html_url:
                follower_str += f"\n[ {follower.html_url}/ ]"
            print(follower_str)

    print(f"\nFollowings:\t{followings_count}")
    if followings_list:

        for following in followings_list:
            following_str = f"\n- {following.login}"
            if following.name:
                following_str += f" ({following.name})"
            if following.html_url:
                following_str += f"\n[ {following.html_url}/ ]"
            print(following_str)

    g.close()


# Function processing items of all passed repos and returning list of dictionaries
def github_process_repos(repos_list):
    list_of_repos = []
    stargazers = []
    forked_repos = []

    if repos_list:
        for repo in repos_list:
            try:
                repo_created_date = repo.created_at
                repo_created_date_ts = convert_utc_str_to_tz_datetime(str(repo_created_date), LOCAL_TIMEZONE, 1).timestamp()
                repo_updated_date = repo.updated_at
                repo_updated_date_ts = convert_utc_str_to_tz_datetime(str(repo_updated_date), LOCAL_TIMEZONE, 1).timestamp()
                stargazers = [star.login for star in repo.get_stargazers()]
                forked_repos = [fork.full_name for fork in repo.get_forks()]
                list_of_repos.append({"name": repo.name, "descr": repo.description, "is_fork": repo.fork, "forks": repo.forks_count, "stars": repo.stargazers_count, "watchers": repo.watchers_count, "url": repo.html_url, "language": repo.language, "date": repo_created_date_ts, "update_date": repo_updated_date_ts, "stargazers": stargazers, "forked_repos": forked_repos})
            except Exception as e:
                print(f"Error while processing info for repo '{repo.name}', skipping for now - {e}")
                print_cur_ts("Timestamp:\t\t")
                continue

    return list_of_repos


# Function printing list of public repositories for Github user
def github_print_repos(user):
    print(f"Getting public repositories for user '{user}' ...")

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)

    g_user = g.get_user(user)
    user_login = g_user.login
    user_name = g_user.name
    user_url = g_user.html_url

    repos_count = g_user.public_repos
    repos_list = g_user.get_repos()

    user_name_str = user_login
    if user_name:
        user_name_str += f" ({user_name})"

    print(f"\nUsername:\t{user_name_str}")
    print(f"URL:\t\t{user_url}/")

    print(f"\nRepos:\t\t{repos_count}")
    if repos_list:

        for repo in repos_list:
            repo_str = f"\n- '{repo.name}' (fork: {repo.fork})"
            repo_str += f"\n[ {repo.language}, forks: {repo.forks_count}, stars: {repo.stargazers_count}, watchers: {repo.watchers_count} ]"
            if repo.html_url:
                repo_str += f"\n[ {repo.html_url}/ ]"
            repo_created_date = repo.created_at
            repo_created_date_ts = convert_utc_str_to_tz_datetime(str(repo_created_date), LOCAL_TIMEZONE, 1).timestamp()
            repo_updated_date = repo.updated_at
            repo_updated_date_ts = convert_utc_str_to_tz_datetime(str(repo_updated_date), LOCAL_TIMEZONE, 1).timestamp()
            repo_str += f"\n[ date: {get_date_from_ts(repo_created_date_ts)} - {calculate_timespan(int(time.time()), int(repo_created_date_ts), granularity=2)} ago) ]"
            repo_str += f"\n[ update: {get_date_from_ts(repo_updated_date_ts)} - {calculate_timespan(int(time.time()), int(repo_updated_date_ts), granularity=2)} ago) ]"
            if repo.description:
                repo_str += f"\n'{repo.description}'"

            print(repo_str)

    g.close()


# Function printing list of starred repositories by Github user
def github_print_starred_repos(user):
    print(f"Getting repositories starred by user '{user}' ...")

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)

    g_user = g.get_user(user)
    user_login = g_user.login
    user_name = g_user.name
    user_url = g_user.html_url

    starred_list = g_user.get_starred()
    starred_count = starred_list.totalCount

    user_name_str = user_login
    if user_name:
        user_name_str += f" ({user_name})"

    print(f"\nUsername:\t\t{user_name_str}")
    print(f"URL:\t\t\t{user_url}/")

    print(f"\nRepos starred by user:\t{starred_count}")

    if starred_list:
        for star in starred_list:
            star_str = f"\n- {star.full_name}"
            if star.html_url:
                star_str += f" [ {star.html_url}/ ]"
            print(star_str)

    g.close()


def github_print_event(event, g, time_passed=False, ts=0):

    event_date_ts = 0
    repo_name = ""
    repo_url = ""
    st = ""
    tp = ""

    event_date_ts = convert_utc_str_to_tz_datetime(str(event.created_at), LOCAL_TIMEZONE, 1).timestamp()
    if time_passed and not ts:
        tp = f" ({calculate_timespan(int(time.time()), int(event_date_ts), show_seconds=False, granularity=2)} ago)"
    elif time_passed and ts:
        tp = f" (after {calculate_timespan(int(event_date_ts), int(ts), show_seconds=False, granularity=2)}: {get_short_date_from_ts(int(ts))})"
    st += print_v(f"Event date:\t\t\t{get_date_from_ts(event_date_ts)}{tp}")
    st += print_v(f"Event ID:\t\t\t{event.id}")
    st += print_v(f"Event type:\t\t\t{event.type}")

    if event.repo.id:
        repo_name = event.repo.name
        repo_url = github_convert_api_to_html_url(event.repo.url)
        st += print_v(f"\nRepo name:\t\t\t{repo_name}")
        st += print_v(f"Repo URL:\t\t\t{repo_url}")
        repo = g.get_repo(event.repo.name)

    if hasattr(event.actor, 'login'):
        if event.actor.login:
            st += print_v(f"\nEvent actor login:\t\t{event.actor.login}")
    if hasattr(event.actor, 'name'):
        if event.actor.name:
            st += print_v(f"Event actor name:\t\t{event.actor.name}")

    if event.payload.get("ref"):
        st += print_v(f"\nObject name:\t\t\t{event.payload.get("ref")}")
    if event.payload.get("ref_type"):
        st += print_v(f"Object type:\t\t\t{event.payload.get("ref_type")}")
    if event.payload.get("description"):
        st += print_v(f"Description:\t\t\t'{event.payload.get("description")}'")

    if event.payload.get("action"):
        st += print_v(f"\nAction:\t\t\t\t{event.payload.get("action")}")

    if event.payload.get("commits"):
        st += print_v(f"\nNumber of commits:\t\t{len(event.payload.get("commits"))}")
        commits = event.payload["commits"]
        for commit in commits:
            commit_details = repo.get_commit(sha=commit["sha"])
            commit_date_ts = convert_utc_str_to_tz_datetime(str(commit_details.commit.author.date), LOCAL_TIMEZONE, 1).timestamp()
            st += print_v(f" - Commit date:\t\t\t{get_date_from_ts(commit_date_ts)}")
            st += print_v(f" - Commit sha:\t\t\t{commit["sha"]}")
            st += print_v(f" - Commit author:\t\t{commit["author"]["name"]}")
            st += print_v(f" - Commit URL:\t\t\t{github_convert_api_to_html_url(commit["url"])}")
            st += print_v(f" - Commit message:\t\t'{commit["message"]}'")
            if commit != commits[-1]:
                st += print_v()

    if event.payload.get("release"):
        st += print_v(f"\nRelease name:\t\t\t{event.payload["release"].get("name")}")
        st += print_v(f"Release URL:\t\t\t{event.payload["release"].get("html_url")}")
        st += print_v(f"Release tag name:\t\t{event.payload["release"].get("tag_name")}")

        if event.payload["release"].get("assets"):
            assets = event.payload["release"].get("assets")
            for asset in assets:
                st += print_v(f" - Asset name:\t\t\t{asset.get("name")}")
                st += print_v(f" - Asset size:\t\t\t{asset.get("size")}")
                st += print_v(f" - Download URL:\t\t{asset.get("browser_download_url")}")
                if asset != assets[-1]:
                    st += print_v()

        st += print_v(f"Release description:\n\n'{event.payload["release"].get("body")}'")

    if event.payload.get("pull_request"):
        st += print_v(f"\nPR title:\t\t\t{event.payload["pull_request"].get("title")}")

        pr_date_ts = convert_utc_str_to_tz_datetime(str(event.payload["pull_request"].get("created_at")), LOCAL_TIMEZONE, 2).timestamp()
        st += print_v(f"PR date:\t\t\t{get_date_from_ts(pr_date_ts)}")

        st += print_v(f"PR URL:\t\t\t\t{event.payload["pull_request"].get("html_url")}")

        if event.payload["pull_request"].get("issue_url"):
            st += print_v(f"Issue URL:\t\t\t{github_convert_api_to_html_url(event.payload["pull_request"].get("issue_url"))}")

        if event.payload["pull_request"].get("state"):
            st += print_v(f"PR state:\t\t\t{event.payload["pull_request"].get("state")}")

        st += print_v(f"Commits:\t\t\t{event.payload["pull_request"].get("commits", 0)}")

        st += print_v(f"Comments:\t\t\t{event.payload["pull_request"].get("comments", 0)}")

        additions = event.payload["pull_request"].get("additions", 0)
        deletions = event.payload["pull_request"].get("deletions", 0)
        st += print_v(f"Additions/deletions:\t\t{additions}/{deletions}")

        st += print_v(f"Changed files:\t\t\t{event.payload["pull_request"].get("changed_files", 0)}")

        if event.payload["pull_request"].get("body"):
            st += print_v(f"PR description:\n\n'{event.payload["pull_request"].get("body")}'")

        if event.payload["pull_request"].get("requested_reviewers"):
            for requested_reviewer in event.payload["pull_request"].get("requested_reviewers"):
                st += print_v(f"\n - Requested reviewer name:\t{requested_reviewer.get("login")}")
                st += print_v(f" - Requested reviewer URL:\t{requested_reviewer.get("html_url")}")

        if event.payload["pull_request"].get("assignees"):
            for assignee in event.payload["pull_request"].get("assignees"):
                st += print_v(f"\n - Assignee name:\t\t{assignee.get("login")}")
                st += print_v(f" - Assignee URL:\t\t{assignee.get("html_url")}")

    if event.payload.get("review"):
        review_date_ts = convert_utc_str_to_tz_datetime(str(event.payload["review"].get("submitted_at")), LOCAL_TIMEZONE, 2).timestamp()
        st += print_v(f"\nRequested review date:\t\t{get_date_from_ts(review_date_ts)}")
        st += print_v(f"Requested review URL:\t\t{event.payload["review"].get("html_url")}")

        if event.payload["review"].get("state"):
            st += print_v(f"Requested review state:\t\t{event.payload["review"].get("state")}")

        if event.payload["review"].get("body"):
            st += print_v(f"Requested review description:\n'{event.payload["review"].get("body")}'")

    if event.payload.get("comment"):
        comment_date_ts = convert_utc_str_to_tz_datetime(str(event.payload["comment"].get("created_at")), LOCAL_TIMEZONE, 2).timestamp()
        st += print_v(f"\nComment date:\t\t\t{get_date_from_ts(comment_date_ts)}")

        if event.payload["comment"].get("body"):
            st += print_v(f"Comment body:\t\t\t'{event.payload["comment"].get("body")}'")

        st += print_v(f"Comment URL:\t\t\t{event.payload["comment"].get("html_url")}")

        if event.payload["comment"].get("path"):
            st += print_v(f"Comment path:\t\t\t{event.payload["comment"].get("path")}")

    if event.payload.get("issue"):
        st += print_v(f"\nIssue title:\t\t\t{event.payload["issue"].get("title")}")
        issue_date_ts = convert_utc_str_to_tz_datetime(str(event.payload["issue"].get("created_at")), LOCAL_TIMEZONE, 2).timestamp()
        st += print_v(f"Issue date:\t\t\t{get_date_from_ts(issue_date_ts)}")

        st += print_v(f"Issue URL:\t\t\t{event.payload["issue"].get("html_url")}")

        if event.payload["issue"].get("state"):
            st += print_v(f"Issue state:\t\t\t{event.payload["issue"].get("state")}")

        st += print_v(f"Issue comments:\t\t\t{event.payload["issue"].get("comments", 0)}")

        if event.payload["issue"].get("assignees"):
            assignees = event.payload["issue"].get("assignees")
            for assignee in assignees:
                st += print_v(f" - Assignee name:\t\t{assignee.get("name")}")
                if assignee != assignees[-1]:
                    st += print_v()

        if event.payload["issue"].get("body"):
            st += print_v(f"Issue body:\n'{event.payload["issue"].get("body")}'")

    if event.payload.get("forkee"):
        st += print_v(f"\nForked to repo:\t\t{event.payload["forkee"].get("full_name")}")
        st += print_v(f"Forked to repo (URL):\t\t{event.payload["forkee"].get("html_url")}")

    return event_date_ts, repo_name, repo_url, st


# Function listing recent events for the user
def github_list_events(user, number, g):

    g_user = g.get_user(user)
    events = g_user.get_events()

    for i in reversed(range(number)):
        event = events[i]
        if event.type in EVENTS_TO_MONITOR or 'ALL' in EVENTS_TO_MONITOR:
            github_print_event(event, g)
            print_cur_ts("\nTimestamp:\t\t\t")


# Main function monitoring activity of the specified Github user
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

    try:
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
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

        events = g_user.get_events()

    except Exception as e:
        print(f"Error - {e}")
        sys.exit(1)

    last_event_id = 0
    last_event_ts = 0
    events_list_of_ids = []

    try:
        for i in reversed(range(EVENTS_NUMBER)):
            event = events[i]
            if i == 0:
                last_event_id = event.id
                if last_event_id:
                    last_event_ts = convert_utc_str_to_tz_datetime(str(event.created_at), LOCAL_TIMEZONE, 1).timestamp()
            events_list_of_ids.append(event.id)
    except IndexError:
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
    events_list_of_ids_old = events_list_of_ids

    user_myself_name_str = user_myself_login
    if user_myself_name:
        user_myself_name_str += f" ({user_myself_name})"

    print(f"\nToken belongs to:\t\t{user_myself_name_str}")

    user_name_str = user_login
    if user_name:
        user_name_str += f" ({user_name})"

    print(f"\nUsername:\t\t\t{user_name_str}")
    print(f"URL:\t\t\t\t{user_url}/")

    if location:
        print(f"Location:\t\t\t{location}")

    if company:
        print(f"Company:\t\t\t{company}")

    if email:
        print(f"Email:\t\t\t\t{email}")

    if blog:
        print(f"Blog URL:\t\t\t{blog}")

    account_created_date_ts = convert_utc_str_to_tz_datetime(str(account_created_date), LOCAL_TIMEZONE, 1).timestamp()
    print(f"\nAccount creation date:\t\t{get_date_from_ts(account_created_date_ts)} ({calculate_timespan(int(time.time()), int(account_created_date_ts), granularity=2)} ago)")

    account_updated_date_ts = convert_utc_str_to_tz_datetime(str(account_updated_date), LOCAL_TIMEZONE, 1).timestamp()
    print(f"Account updated date:\t\t{get_date_from_ts(account_updated_date_ts)} ({calculate_timespan(int(time.time()), int(account_updated_date_ts), granularity=2)} ago)")
    account_updated_date_old_ts = account_updated_date_ts

    print(f"\nFollowers:\t\t\t{followers_count}")
    print(f"Followings:\t\t\t{followings_count}")
    print(f"Repos:\t\t\t\t{repos_count}")
    print(f"Starred repos:\t\t\t{starred_count}")

    if bio:
        print(f"\nBio:\n\n'{bio}'")

    print_cur_ts("\nTimestamp:\t\t\t")

    list_of_repos = []
    if repos_list and track_repos_changes:
        print("Processing list of public repositories (be patient, it might take a while) ...")
        list_of_repos = github_process_repos(repos_list)
        print_cur_ts("\nTimestamp:\t\t\t")

    list_of_repos_old = list_of_repos

    print(f"Latest event:\n")

    try:
        last_event = events[0]
        github_print_event(last_event, g, True)
    except IndexError:
        print("There are no events yet")

    print_cur_ts("\nTimestamp:\t\t\t")

    followers = []
    followings = []
    repos = []
    starred = []

    followers = [follower.login for follower in followers_list]
    followings = [following.login for following in followings_list]
    repos = [repo.name for repo in repos_list]
    starred = [star.full_name for star in starred_list]

    followers_old = followers
    followings_old = followings
    repos_old = repos
    starred_old = starred

    g.close()

    time.sleep(GITHUB_CHECK_INTERVAL)
    alive_counter = 0
    email_sent = False

    # main loop
    while True:
        try:
            g = Github(auth=auth)
            g_user = g.get_user(user)
            user_name = g_user.name
            location = g_user.location
            bio = g_user.bio
            company = g_user.company
            email = g_user.email
            blog = g_user.blog
            account_updated_date = g_user.updated_at
            if account_updated_date:
                account_updated_date_ts = convert_utc_str_to_tz_datetime(str(account_updated_date), LOCAL_TIMEZONE, 1).timestamp()

            followers_count = g_user.followers
            followings_count = g_user.following
            repos_count = g_user.public_repos

            if track_repos_changes:
                repos_list = g_user.get_repos()

            starred_list = g_user.get_starred()
            starred_count = starred_list.totalCount

            events = g_user.get_events()

            email_sent = False

        except Exception as e:
            print(f"Error, retrying in {display_time(GITHUB_CHECK_INTERVAL)} - {e}")
            if 'Redirected' in str(e) or 'login' in str(e) or 'Forbidden' in str(e) or 'Wrong' in str(e) or 'Bad Request' in str(e):
                print("* Session might not be valid anymore!")
                if error_notification and not email_sent:
                    m_subject = f"github_monitor: session error! (user: {user})"
                    m_body = f"Session might not be valid anymore: {e}{get_cur_ts("\n\nTimestamp: ")}"
                    print(f"Sending email notification to {RECEIVER_EMAIL}")
                    send_email(m_subject, m_body, "", SMTP_SSL)
                    email_sent = True

            print_cur_ts("Timestamp:\t\t\t")
            time.sleep(GITHUB_CHECK_INTERVAL)
            continue

        # Changed followings
        if followings_count != followings_old_count:
            followings_diff = followings_count - followings_old_count
            followings_diff_str = ""
            if followings_diff > 0:
                followings_diff_str = f"+{followings_diff}"
            else:
                followings_diff_str = f"{followings_diff}"
            print(f"* Followings number changed by user {user} from {followings_old_count} to {followings_count} ({followings_diff_str})")
            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Followings Count", user, followings_old_count, followings_count)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            added_followings_list = ""
            removed_followings_list = ""
            added_followings_mbody = ""
            removed_followings_mbody = ""

            try:
                followings_list = g_user.get_following()
                followings = []
                followings = [following.login for following in followings_list]
                if not followings and followings_count > 0:
                    print("* Empty followings list returned")
            except Exception as e:
                followings = followings_old
                print(f"Error - {e}")

            if not followings and followings_count > 0:
                followings = followings_old
            else:
                a, b = set(followings_old), set(followings)

                removed_followings = list(a - b)
                added_followings = list(b - a)

                if followings != followings_old:
                    print()

                    if removed_followings:
                        print("Removed followings:\n")
                        removed_followings_mbody = "\nRemoved followings:\n\n"
                        for f_in_list in removed_followings:
                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                removed_followings_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Removed Following", user, f_in_list, "")
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                    if added_followings:
                        print("Added followings:\n")
                        added_followings_mbody = "\nAdded followings:\n\n"
                        for f_in_list in added_followings:
                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                added_followings_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Added Following", user, "", f_in_list)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                followings_old = followings

            m_subject = f"Github user {user} followings number has changed! ({followings_diff_str}, {followings_old_count} -> {followings_count})"

            m_body = f"Followings number changed by user {user} from {followings_old_count} to {followings_count} ({followings_diff_str})\n{removed_followings_mbody}{removed_followings_list}{added_followings_mbody}{added_followings_list}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            followings_old_count = followings_count

            print_cur_ts("Timestamp:\t\t\t")

        # Changed followers
        if followers_count != followers_old_count:
            followers_diff = followers_count - followers_old_count
            followers_diff_str = ""
            if followers_diff > 0:
                followers_diff_str = f"+{followers_diff}"
            else:
                followers_diff_str = f"{followers_diff}"
            print(f"* Followers number changed for user {user} from {followers_old_count} to {followers_count} ({followers_diff_str})")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Followers Count", user, followers_old_count, followers_count)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            added_followers_list = ""
            removed_followers_list = ""
            added_followers_mbody = ""
            removed_followers_mbody = ""

            try:
                followers_list = g_user.get_followers()
                followers = []
                followers = [follower.login for follower in followers_list]

                if not followers and followers_count > 0:
                    print("* Empty followers list returned")

            except Exception as e:
                followers = followers_old
                print(f"Error - {e}")

            if not followers and followers_count > 0:
                followers = followers_old
            else:
                a, b = set(followers_old), set(followers)
                removed_followers = list(a - b)
                added_followers = list(b - a)

                if followers != followers_old:
                    print()

                    if removed_followers:
                        print("Removed followers:\n")
                        removed_followers_mbody = "\nRemoved followers:\n\n"
                        for f_in_list in removed_followers:
                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                removed_followers_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Removed Follower", user, f_in_list, "")
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                    if added_followers:
                        print("Added followers:\n")
                        added_followers_mbody = "\nAdded followers:\n\n"
                        for f_in_list in added_followers:
                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                added_followers_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Added Follower", user, "", f_in_list)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                followers_old = followers

            m_subject = f"Github user {user} followers number has changed! ({followers_diff_str}, {followers_old_count} -> {followers_count})"

            m_body = f"Followers number changed for user {user} from {followers_old_count} to {followers_count} ({followers_diff_str})\n{removed_followers_mbody}{removed_followers_list}{added_followers_mbody}{added_followers_list}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            followers_old_count = followers_count

            print_cur_ts("Timestamp:\t\t\t")

        # Changed repos
        if repos_count != repos_old_count:
            repos_diff = repos_count - repos_old_count
            repos_diff_str = ""
            if repos_diff > 0:
                repos_diff_str = f"+{repos_diff}"
            else:
                repos_diff_str = f"{repos_diff}"
            print(f"* Repos number changed for user {user} from {repos_old_count} to {repos_count} ({repos_diff_str})")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Repos Count", user, repos_old_count, repos_count)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            added_repos_list = ""
            removed_repos_list = ""
            added_repos_mbody = ""
            removed_repos_mbody = ""

            try:
                repos_list = g_user.get_repos()
                repos = []
                repos = [repo.name for repo in repos_list]

                if not repos and repos_count > 0:
                    print("* Empty repos list returned")

            except Exception as e:
                repos = repos_old
                print(f"Error - {e}")

            if not repos and repos_count > 0:
                repos = repos_old
            else:
                a, b = set(repos_old), set(repos)
                removed_repos = list(a - b)
                added_repos = list(b - a)

                if repos != repos_old:
                    print()

                    if removed_repos:
                        print("Removed repos:\n")
                        removed_repos_mbody = "\nRemoved repos:\n\n"
                        for f_in_list in removed_repos:
                                print(f"- {f_in_list} [ https://github.com/{user}/{f_in_list}/ ]")
                                removed_repos_list += f"- {f_in_list} [ https://github.com/{user}/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Removed Repo", user, f_in_list, "")
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                    if added_repos:
                        print("Added repos:\n")
                        added_repos_mbody = "\nAdded repos:\n\n"
                        for f_in_list in added_repos:
                                print(f"- {f_in_list} [ https://github.com/{user}/{f_in_list}/ ]")
                                added_repos_list += f"- {f_in_list} [ https://github.com/{user}/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Added Repo", user, "", f_in_list)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                repos_old = repos

            m_subject = f"Github user {user} repos number has changed! ({repos_diff_str}, {repos_old_count} -> {repos_count})"

            m_body = f"Repos number changed for user {user} from {repos_old_count} to {repos_count} ({repos_diff_str})\n{removed_repos_mbody}{removed_repos_list}{added_repos_mbody}{added_repos_list}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            repos_old_count = repos_count

            print_cur_ts("Timestamp:\t\t\t")

        # Changed starred repos
        if starred_count != starred_old_count:
            starred_diff = starred_count - starred_old_count
            starred_diff_str = ""
            if starred_diff > 0:
                starred_diff_str = f"+{starred_diff}"
            else:
                starred_diff_str = f"{starred_diff}"
            print(f"* Starred repos number changed by user {user} from {starred_old_count} to {starred_count} ({starred_diff_str})")
            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Starred Repos Count", user, starred_old_count, starred_count)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            added_starred_list = ""
            removed_starred_list = ""
            added_starred_mbody = ""
            removed_starred_mbody = ""

            try:
                starred = []
                starred = [star.full_name for star in starred_list]

                if not starred and starred_count > 0:
                    print("* Empty starred list returned")

            except Exception as e:
                starred = starred_old
                print(f"Error - {e}")

            if not starred and starred_count > 0:
                starred = starred_old
            else:
                a, b = set(starred_old), set(starred)
                removed_starred = list(a - b)
                added_starred = list(b - a)

                if starred != starred_old:
                    print()

                    if removed_starred:
                        print("Removed starred repos:\n")
                        removed_starred_mbody = "\nRemoved starred repos:\n\n"
                        for f_in_list in removed_starred:
                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                removed_starred_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Removed Starred Repo", user, f_in_list, "")
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                    if added_starred:
                        print("Added starred repos:\n")
                        added_starred_mbody = "\nAdded starred repos:\n\n"
                        for f_in_list in added_starred:
                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                added_starred_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Added Starred Repo", user, "", f_in_list)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                        print()

                starred_old = starred

            m_subject = f"Github user {user} starred repos number has changed! ({starred_diff_str}, {starred_old_count} -> {starred_count})"

            m_body = f"Starred repos number changed by user {user} from {starred_old_count} to {starred_count} ({starred_diff_str})\n{removed_starred_mbody}{removed_starred_list}{added_starred_mbody}{added_starred_list}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            starred_old_count = starred_count

            print_cur_ts("Timestamp:\t\t\t")

        # Changed bio
        if bio != bio_old:
            print(f"* Bio has changed for user {user} !\n")
            print(f"Old bio:\n\n{bio_old}\n")
            print(f"New bio:\n\n{bio}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Bio", user, bio_old, bio)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} bio has changed!"
            m_body = f"Github user {user} bio has changed\n\nOld bio:\n\n{bio_old}\n\nNew bio:\n\n{bio}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            bio_old = bio
            print_cur_ts("Timestamp:\t\t\t")

        # Changed location
        if location != location_old:
            print(f"* Location has changed for user {user} !\n")
            print(f"Old location:\t\t\t{location_old}\n")
            print(f"New location:\t\t\t{location}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Location", user, location_old, location)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} location has changed!"
            m_body = f"Github user {user} location has changed\n\nOld location: {location_old}\n\nNew location: {location}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            location_old = location
            print_cur_ts("Timestamp:\t\t\t")

        # Changed user name 
        if user_name != user_name_old:
            print(f"* User name has changed for user {user} !\n")
            print(f"Old user name:\t\t\t{user_name_old}\n")
            print(f"New user name:\t\t\t{user_name}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "User Name", user, user_name_old, user_name)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} name has changed!"
            m_body = f"Github user {user} name has changed\n\nOld user name: {user_name_old}\n\nNew user name: {user_name}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            user_name_old = user_name
            print_cur_ts("Timestamp:\t\t\t")

        # Changed company
        if company != company_old:
            print(f"* User company has changed for user {user} !\n")
            print(f"Old company:\t\t\t{company_old}\n")
            print(f"New company:\t\t\t{company}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Company", user, company_old, company)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} company has changed!"
            m_body = f"Github user {user} company has changed\n\nOld company: {company_old}\n\nNew company: {company}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            company_old = company
            print_cur_ts("Timestamp:\t\t\t")

        # Changed email
        if email != email_old:
            print(f"* User email has changed for user {user} !\n")
            print(f"Old email:\t\t\t{email_old}\n")
            print(f"New email:\t\t\t{email}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Email", user, email_old, email)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} email has changed!"
            m_body = f"Github user {user} email has changed\n\nOld email: {email_old}\n\nNew email: {email}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            email_old = email
            print_cur_ts("Timestamp:\t\t\t")

        # Changed blog URL
        if blog != blog_old:
            print(f"* User blog URL has changed for user {user} !\n")
            print(f"Old blog URL:\t\t\t{blog_old}\n")
            print(f"New blog URL:\t\t\t{blog}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Blog URL", user, blog_old, blog)
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} blog URL has changed!"
            m_body = f"Github user {user} blog URL has changed\n\nOld blog URL: {blog_old}\n\nNew blog URL: {blog}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            blog_old = blog
            print_cur_ts("Timestamp:\t\t\t")

        # Changed account update date
        if account_updated_date_ts != account_updated_date_old_ts:
            print(f"* User account has been updated for user {user} ! (after {calculate_timespan(account_updated_date_ts, account_updated_date_old_ts, show_seconds=False, granularity=2)})\n")
            print(f"Old account update date:\t{get_date_from_ts(account_updated_date_old_ts)}\n")
            print(f"New account update date:\t{get_date_from_ts(account_updated_date_ts)}\n")

            try:
                if csv_file_name:
                    write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Account Update Date", user, str(datetime.fromtimestamp(account_updated_date_old_ts)), str(datetime.fromtimestamp(account_updated_date_ts)))
            except Exception as e:
                print(f"* Cannot write CSV entry - {e}")

            m_subject = f"Github user {user} account has been updated! (after {calculate_timespan(account_updated_date_ts, account_updated_date_old_ts, show_seconds=False, granularity=2)})"
            m_body = f"Github user {user} account has been updated (after {calculate_timespan(account_updated_date_ts, account_updated_date_old_ts, show_seconds=False, granularity=2)})\n\nOld account update date: {get_date_from_ts(account_updated_date_old_ts)}\n\nNew account update date: {get_date_from_ts(account_updated_date_ts)}\n\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

            if profile_notification:
                print(f"Sending email notification to {RECEIVER_EMAIL}")
                send_email(m_subject, m_body, "", SMTP_SSL)

            account_updated_date_old_ts = account_updated_date_ts
            print_cur_ts("Timestamp:\t\t\t")

        list_of_repos = []

        # Changed repos details
        if track_repos_changes:
            if repos_list:
                list_of_repos = github_process_repos(repos_list)

                for repo in list_of_repos:
                    r_name = repo.get("name")
                    r_descr = repo.get("descr", "")
                    r_forks = repo.get("forks", 0)
                    r_stars = repo.get("stars", 0)
                    r_watchers = repo.get("watchers", 0)
                    r_url = repo.get("url", "")
                    r_update = repo.get("update_date", 0)
                    r_stargazers = repo.get("stargazers")
                    r_forked_repos = repo.get("forked_repos")

                    for repo_old in list_of_repos_old:
                        r_name_old = repo_old.get("name")
                        if r_name_old == r_name:
                            r_descr_old = repo_old.get("descr", "")
                            r_forks_old = repo_old.get("forks", 0)
                            r_stars_old = repo_old.get("stars", 0)
                            r_watchers_old = repo_old.get("watchers", 0)
                            r_url_old = repo_old.get("url", "")
                            r_update_old = repo_old.get("update_date", 0)
                            r_stargazers_old = repo_old.get("stargazers")
                            r_forked_repos_old = repo_old.get("forked_repos")

                            # Number of stars for repo changed
                            if r_stars != r_stars_old:
                                r_stars_diff = r_stars - r_stars_old
                                r_stars_diff_str = ""
                                if r_stars_diff > 0:
                                    r_stars_diff_str = "+" + str(r_stars_diff)
                                else:
                                    r_stars_diff_str = str(r_stars_diff)
                                print(f"* Repo '{r_name}': number of stargazers changed from {r_stars_old} to {r_stars} ({r_stars_diff_str})\n* Repo URL: {r_url}")
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Repo Stars Count", r_name, r_stars_old, r_stars)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")

                                added_stargazers_list = ""
                                removed_stargazers_list = ""
                                added_stargazers_mbody = ""
                                removed_stargazers_mbody = ""

                                a, b = set(r_stargazers_old), set(r_stargazers)

                                removed_stargazers = list(a - b)
                                added_stargazers = list(b - a)

                                if r_stargazers != r_stargazers_old:
                                    print()

                                    if removed_stargazers:
                                        print("Removed stargazers:\n")
                                        removed_stargazers_mbody = "\nRemoved stargazers:\n\n"
                                        for f_in_list in removed_stargazers:
                                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                                removed_stargazers_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                                try:
                                                    if csv_file_name:
                                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Removed Stargazer", user, f_in_list, "")
                                                except Exception as e:
                                                    print(f"* Cannot write CSV entry - {e}")
                                        print()

                                    if added_stargazers:
                                        print("Added stargazers:\n")
                                        added_stargazers_mbody = "\nAdded stargazers:\n\n"
                                        for f_in_list in added_stargazers:
                                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                                added_stargazers_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                                try:
                                                    if csv_file_name:
                                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Added Stargazer", user, "", f_in_list)
                                                except Exception as e:
                                                    print(f"* Cannot write CSV entry - {e}")
                                        print()

                                m_subject = f"Github user {user} number of stargazers for repo '{r_name}' has changed! ({r_stars_diff_str}, {r_stars_old} -> {r_stars})"
                                m_body = f"* Repo '{r_name}': number of stargazers changed from {r_stars_old} to {r_stars} ({r_stars_diff_str})\n* Repo URL: {r_url}\n{removed_stargazers_mbody}{removed_stargazers_list}{added_stargazers_mbody}{added_stargazers_list}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"
                                if profile_notification:
                                    print(f"Sending email notification to {RECEIVER_EMAIL}")
                                    send_email(m_subject, m_body, "", SMTP_SSL)
                                print_cur_ts("Timestamp:\t\t\t")

                            # Number of forks for repo changed
                            if r_forks != r_forks_old:
                                r_forks_diff = r_forks - r_forks_old
                                r_forks_diff_str = ""
                                if r_forks_diff > 0:
                                    r_forks_diff_str = "+" + str(r_forks_diff)
                                else:
                                    r_forks_diff_str = str(r_forks_diff)
                                print(f"* Repo '{r_name}': number of forks changed from {r_forks_old} to {r_forks} ({r_forks_diff_str})\n* Repo URL: {r_url}")
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Repo Forks Count", r_name, r_forks_old, r_forks)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")

                                added_forked_repos_list = ""
                                removed_forked_repos_list = ""
                                added_forked_repos_mbody = ""
                                removed_forked_repos_mbody = ""

                                a, b = set(r_forked_repos_old), set(r_forked_repos)

                                removed_forked_repos = list(a - b)
                                added_forked_repos = list(b - a)

                                if r_forked_repos != r_forked_repos_old:
                                    print()

                                    if removed_forked_repos:
                                        print("Removed forked repos:\n")
                                        removed_forked_repos_mbody = "\nRemoved forked repos:\n\n"
                                        for f_in_list in removed_forked_repos:
                                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                                removed_forked_repos_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                                try:
                                                    if csv_file_name:
                                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Removed Forked Repo", user, f_in_list, "")
                                                except Exception as e:
                                                    print(f"* Cannot write CSV entry - {e}")
                                        print()

                                    if added_forked_repos:
                                        print("Added forked repos:\n")
                                        added_forked_repos_mbody = "\nAdded forked repos:\n\n"
                                        for f_in_list in added_forked_repos:
                                                print(f"- {f_in_list} [ https://github.com/{f_in_list}/ ]")
                                                added_forked_repos_list += f"- {f_in_list} [ https://github.com/{f_in_list}/ ]\n"
                                                try:
                                                    if csv_file_name:
                                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Added Forked Repo", user, "", f_in_list)
                                                except Exception as e:
                                                    print(f"* Cannot write CSV entry - {e}")
                                        print()

                                m_subject = f"Github user {user} number of forks for repo '{r_name}' has changed! ({r_forks_diff_str}, {r_forks_old} -> {r_forks})"
                                m_body = f"* Repo '{r_name}': number of forks changed from {r_forks_old} to {r_forks} ({r_forks_diff_str})\n* Repo URL: {r_url}\n{removed_forked_repos_mbody}{removed_forked_repos_list}{added_forked_repos_mbody}{added_forked_repos_list}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"
                                if profile_notification:
                                    print(f"Sending email notification to {RECEIVER_EMAIL}")
                                    send_email(m_subject, m_body, "", SMTP_SSL)
                                print_cur_ts("Timestamp:\t\t\t")

                            # Update date for repo changed
                            if int(r_update) != int(r_update_old):
                                r_message = f"* Repo '{r_name}' update date changed (after {calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)})\n* Repo URL: {r_url}\n\nOld repo update date:\t{get_date_from_ts(r_update_old)}\n\nNew repo update date:\t{get_date_from_ts(r_update)}\n"
                                print(r_message)
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Repo Update Date", r_name, r_update_old, r_update)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                                m_subject = f"Github user {user} repo '{r_name}' update date has changed ! (after {calculate_timespan(r_update, r_update_old, show_seconds=False, granularity=2)})"
                                m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"
                                if profile_notification:
                                    print(f"Sending email notification to {RECEIVER_EMAIL}")
                                    send_email(m_subject, m_body, "", SMTP_SSL)
                                print_cur_ts("Timestamp:\t\t\t")

                            # Repo description changed
                            if r_descr != r_descr_old:
                                r_message = f"* Repo '{r_name}' description changed from:\n\n'{r_descr_old}'\n\nto:\n\n'{r_descr}'\n\n* Repo URL: {r_url}\n"
                                print(r_message)
                                try:
                                    if csv_file_name:
                                        write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), "Repo Description", r_name, r_descr_old, r_descr)
                                except Exception as e:
                                    print(f"* Cannot write CSV entry - {e}")
                                m_subject = f"Github user {user} repo '{r_name}' description has changed !"
                                m_body = f"{r_message}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"
                                if profile_notification:
                                    print(f"Sending email notification to {RECEIVER_EMAIL}")
                                    send_email(m_subject, m_body, "", SMTP_SSL)
                                print_cur_ts("Timestamp:\t\t\t")

                list_of_repos_old = list_of_repos

        try:
            last_event_id = events[0].id
            if last_event_id:
                last_event_ts = convert_utc_str_to_tz_datetime(str(events[0].created_at), LOCAL_TIMEZONE, 1).timestamp()
        except IndexError:
            last_event_id = 0
            last_event_ts = 0

        events_list_of_ids = []
        first_new = True

        # New events showed up
        if last_event_id != last_event_id_old:

            for i in reversed(range(EVENTS_NUMBER)):
                event = events[i]
                if i == 0:
                    last_event_id = event.id
                    if last_event_id:
                        last_event_ts = convert_utc_str_to_tz_datetime(str(event.created_at), LOCAL_TIMEZONE, 1).timestamp()
                events_list_of_ids.append(event.id)
                if event.id in events_list_of_ids_old:
                    continue
                if event.type in EVENTS_TO_MONITOR or 'ALL' in EVENTS_TO_MONITOR:
                    event_date_ts, repo_name, repo_url, event_text = github_print_event(event, g, first_new, last_event_ts_old)
                    first_new = False
                    try:
                        if csv_file_name:
                            write_csv_entry(csv_file_name, datetime.fromtimestamp(int(time.time())), str(event.type), str(repo_name), "", "")
                    except Exception as e:
                        print(f"* Cannot write CSV entry - {e}")
                    m_subject = f"Github user {user} has new {event.type} (repo: {repo_name})"
                    m_body = f"Github user {user} has new {event.type} event\n\n{event_text}\nCheck interval: {display_time(GITHUB_CHECK_INTERVAL)}{get_cur_ts("\nTimestamp: ")}"

                    if event_notification:
                        print(f"\nSending email notification to {RECEIVER_EMAIL}")
                        send_email(m_subject, m_body, "", SMTP_SSL)

                    print_cur_ts("Timestamp:\t\t\t")

            last_event_id_old = last_event_id
            last_event_ts_old = last_event_ts
            events_list_of_ids_old = events_list_of_ids

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
    except:
        print("* Cannot clear the screen contents")

    print(f"Github Monitoring Tool v{VERSION}\n")

    parser = argparse.ArgumentParser("github_monitor")
    parser.add_argument("GITHUB_USERNAME", nargs="?", help="Github username", type=str)
    parser.add_argument("-t", "--github_token", help="Github personal access token (classic) to override the value defined within the script (GITHUB_TOKEN)", type=str)
    parser.add_argument("-p", "--profile_notification", help="Send email notification once user profile changes", action='store_true')
    parser.add_argument("-s", "--event_notification", help="Send email notification once new event shows up", action='store_true')
    parser.add_argument("-e", "--error_notification", help="Disable sending email notifications in case of errors like expired token", action='store_false')
    parser.add_argument("-c", "--check_interval", help="Time between monitoring checks, in seconds", type=int)
    parser.add_argument("-b", "--csv_file", help="Write info about new events & profile changes to CSV file", type=str, metavar="CSV_FILENAME")
    parser.add_argument("-j", "--track_repos_changes", help="Track changes of user repos like new stargazers, forks, changed description", action='store_true')
    parser.add_argument("-r", "--repos", help="List repositories for user", action='store_true')
    parser.add_argument("-g", "--starred_repos", help="List repos starred by user", action='store_true')
    parser.add_argument("-f", "--followers_and_followings", help="List followers & followings for user", action='store_true')
    parser.add_argument("-l", "--list_recent_events", help="List recent events for the user", action='store_true')
    parser.add_argument("-n", "--number_of_recent_events", help="Number of events to display if used with -l", type=int)
    parser.add_argument("-d", "--disable_logging", help="Disable logging to file 'github_monitor_user.log' file", action='store_true')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    local_tz = None
    if LOCAL_TIMEZONE == "Auto":
        try:
            local_tz = get_localzone()
        except NameError:
            pass
        if local_tz:
            LOCAL_TIMEZONE = str(local_tz)
        else:
            print("* Error: Cannot detect local timezone, consider setting LOCAL_TIMEZONE to your local timezone manually !")
            sys.exit(1)

    if args.github_token:
        GITHUB_TOKEN = args.github_token

    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_classic_personal_access_token":
        print("* Error: GITHUB_TOKEN (-t / --github_token) value is empty or incorrect")
        sys.exit(1)

    if not args.GITHUB_USERNAME:
        print("* Error: GITHUB_USERNAME argument is required !")
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

    if args.list_recent_events:
        if args.number_of_recent_events and args.number_of_recent_events > 0:
            events_n = args.number_of_recent_events
        else:
            events_n = 5
        print(f"* Listing {events_n} recent events for {args.GITHUB_USERNAME}:\n")
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        github_list_events(args.GITHUB_USERNAME, events_n, g)
        g.close()
        sys.exit(0)

    sys.stdout.write("* Checking internet connectivity ... ")
    sys.stdout.flush()
    check_internet()
    print("")

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

    if not args.disable_logging:
        GITHUB_LOGFILE = f"{GITHUB_LOGFILE}_{args.GITHUB_USERNAME}.log"
        sys.stdout = Logger(GITHUB_LOGFILE)

    event_notification = args.event_notification
    profile_notification = args.profile_notification
    track_repos_changes = args.track_repos_changes

    print(f"* Github timers:\t\t[check interval: {display_time(GITHUB_CHECK_INTERVAL)}]")
    print(f"* Email notifications:\t\t[profile changes = {profile_notification}] [new events = {event_notification}]\n*\t\t\t\t[errors = {args.error_notification}]")
    print(f"* Track repos changes:\t\t{track_repos_changes}")
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
        signal.signal(signal.SIGTRAP, increase_check_signal_handler)
        signal.signal(signal.SIGABRT, decrease_check_signal_handler)

    github_monitor_user(args.GITHUB_USERNAME, args.error_notification, args.csv_file, csv_exists)

    sys.stdout = stdout_bck
    sys.exit(0)
