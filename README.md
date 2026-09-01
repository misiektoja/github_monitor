# github_monitor

<p align="left">
  <img src="https://img.shields.io/github/v/release/misiektoja/github_monitor?style=flat-square&color=blue" alt="GitHub Release" />
  <img src="https://img.shields.io/pypi/v/github_monitor?style=flat-square&color=teal" alt="PyPI Version" />
  <img src="https://img.shields.io/github/stars/misiektoja/github_monitor?style=flat-square&color=magenta" alt="GitHub Stars" />
  <img src="https://img.shields.io/badge/python-3.10+-blueviolet?style=flat-square" alt="Python Versions" />
  <img src="https://img.shields.io/github/license/misiektoja/github_monitor?style=flat-square&color=blue" alt="License" />
  <img src="https://img.shields.io/github/last-commit/misiektoja/github_monitor?style=flat-square&color=green" alt="Last Commit" />
  <img src="https://img.shields.io/badge/maintenance-active-brightgreen?style=flat-square" alt="Maintenance" />
</p>

Powerful real-time GitHub OSINT tool that tracks everything from profile updates and contribution streaks to repository engagement and follower changes - even detecting when you've been blocked, all with instant email and webhook notifications.

### 🚀 Quick Install
```sh
pip install github_monitor
```

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor.png" alt="github_monitor_screenshot" width="100%"/>
</p>

<a id="features"></a>
## Features

- **Real-time tracking** of GitHub users' activities, including profile and repository changes:
   - **new GitHub events** for the user like new pushes, PRs, issues, forks, releases, reviews etc.
   - **repository changes** such as updated stargazers, watchers, forks, issues, PRs, discussions, description and repo update dates
   - added/removed **followings and followers**
   - added/removed **starred repositories**
   - added/removed **public repositories**
   - changes in **user name, email, location, company, bio and blog URL**
   - changes in **profile visibility** (public to private and vice versa)
   - changes in **user's daily contributions**
   - detection when a **user blocks or unblocks you**
   - detection of **account metadata** changes (such as account update date)
- **Email and webhook notifications** through **Discord**, **ntfy** and custom Discord-format integrations for different events
- **Saving all user activities** with timestamps to the **CSV file**
- **Clickable GitHub URLs** printed in the console & included in email notifications (repos, PRs, commits, issues, releases etc.)
- Possibility to **control the running copy** of the script via signals
- Support for **Public Web GitHub** and **GitHub Enterprise**
- **Functional, procedural Python** (minimal OOP)

<a id="table-of-contents"></a>
## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
   * [Install from PyPI](#install-from-pypi)
   * [Manual Installation](#manual-installation)
   * [Upgrading](#upgrading)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
   * [Configuration File](#configuration-file)
   * [Terminal Colours](#terminal-colours)
   * [GitHub Personal Access Token](#github-personal-access-token)
   * [GitHub API URL](#github-api-url)
   * [Events to Monitor](#events-to-monitor)
   * [Repositories to Monitor](#repositories-to-monitor)
   * [Time Zone](#time-zone)
   * [SMTP Settings](#smtp-settings)
   * [Webhook Settings](#webhook-settings)
   * [Storing Secrets](#storing-secrets)
   * [TLS Verification](#tls-verification)
5. [Usage](#usage)
   * [Monitoring Mode](#monitoring-mode)
   * [Listing Mode](#listing-mode)
   * [Email Notifications](#email-notifications)
   * [Webhook Notifications](#webhook-notifications)
   * [CSV Export](#csv-export)
   * [Check Intervals](#check-intervals)
   * [Signal Controls (macOS/Linux/Unix)](#signal-controls-macoslinuxunix)
   * [Coloring Log Output with GRC](#coloring-log-output-with-grc)
   * [Doctor Preflight](#doctor-preflight)
   * [Debugging and Recovery](#debugging-and-recovery)
6. [Change Log](#change-log)
7. [Contributing](#contributing)
8. [Security](#security)
9. [License](#license)
10. [Support](#support)

<a id="requirements"></a>
## Requirements

* Python 3.10 or higher
* Libraries: [PyGithub](https://github.com/PyGithub/PyGithub) (2.8 or newer), `requests`, `urllib3`, `python-dateutil`, `pytz`, `tzlocal`, `python-dotenv`
* Optional terminal libraries: `colorama` for classic Windows Command Prompt colours and `wcwidth` for display-width-aware `TRUNCATE_CHARS`

Tested on:

* **macOS**: Tahoe, Sequoia, Sonoma, Ventura
* **Linux**: Raspberry Pi OS (Trixie, Bookworm, Bullseye), Ubuntu 24/25, Rocky Linux 8.x/9.x, Kali Linux 2026/2025/2024
* **Windows**: 11, 10

It should work on other versions of macOS, Linux, Unix and Windows as well.

<a id="installation"></a>
## Installation

<a id="install-from-pypi"></a>
### Install from PyPI

```sh
pip install github_monitor
```

<a id="manual-installation"></a>
### Manual Installation

Download the *[github_monitor.py](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/github_monitor.py)* file to the desired location.

Install dependencies via pip:

```sh
pip install PyGithub requests urllib3 python-dateutil pytz tzlocal python-dotenv
```

Alternatively, from the downloaded *[requirements.txt](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/requirements.txt)*:

```sh
pip install -r requirements.txt
```

<a id="upgrading"></a>
### Upgrading

To upgrade to the latest version when installed from PyPI:

```sh
pip install github_monitor -U
```

If you installed manually, download the newest *[github_monitor.py](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/github_monitor.py)* file to replace your existing installation.

<a id="quick-start"></a>
## Quick Start

The easiest first run is the guided setup wizard:

```sh
github_monitor --setup
```

It asks for the target, whether to save it, the polling interval, GitHub authentication, optional email and webhook alerts and output destinations. Polling accepts seconds or values such as `30s`, `2m`, `1.5h`, `1h 30m` and `1d`. The existing automatic timezone setting is retained instead of adding another setup question. Answers stay in memory until the complete summary is reviewed. Choose **Save settings** to write non-secret settings to `github_monitor.conf` and private values to a separate mode-0600 `.env` file. Existing destinations receive timestamped mode-0600 backups before replacement.

The wizard links to GitHub's token settings then validates a newly entered token before saving it. Every answer the wizard cannot use offers a way out, so one value you cannot produce right now does not cost you the answers already given: a blank answer asks whether to continue without it and names what stops working, a rejected one offers to enter it again and declining a webhook destination leaves that channel and its alerts off. After saving, the wizard offers the read-only Doctor preflight then monitoring. Both prompts default to yes when the saved setup is ready. Commands after setup match a PyPI install or downloaded script and include the selected config plus dotenv paths.

Run the tool without arguments to see the same first-run screen used across the monitor tools. It uses short portable commands instead of the active interpreter and absolute script paths:

```text
For <github_target>, use a GitHub username or complete profile URL.

Quickest start (already configured):
    python3 github_monitor.py <github_target>

Easiest start (guided setup wizard):
    python3 github_monitor.py --setup

Check setup before monitoring:
    python3 github_monitor.py --doctor <github_target>

Full options: python3 github_monitor.py --help
```

A PyPI install prints `github_monitor` instead of `python3 github_monitor.py`. Windows prints `python github_monitor.py`. An interactive terminal offers the setup wizard with a default-yes prompt. A non-interactive `--setup` run explains how to use `--generate-config` instead.

When setup saves the target, later runs can omit it. A positional target still overrides `TARGET_GITHUB_USERNAME` for one run. If no target is saved, running the tool without arguments shows the first-run screen above.

For manual setup, create a [GitHub personal access token](#github-personal-access-token) then validate and save it through the hidden prompt:

```sh
github_monitor --set-github-token
```

Start monitoring `github_username`:

```sh
github_monitor <github_username>
```

Or if you installed [manually](#manual-installation):

```sh
python3 github_monitor.py --setup
python3 github_monitor.py <github_username>
```

To get the list of all supported command-line arguments / flags:

```sh
github_monitor --help
```

<a id="configuration"></a>
## Configuration

<a id="configuration-file"></a>
### Configuration File

Most settings can be configured via command-line arguments.

If you want to have it stored persistently, generate a default config template and save it to a file named `github_monitor.conf`:

```sh
# On macOS Linux and Windows Command Prompt (cmd.exe)
github_monitor --generate-config > github_monitor.conf

# On Windows PowerShell (recommended to avoid encoding issues)
github_monitor --generate-config github_monitor.conf
```

> **IMPORTANT**: On **Windows PowerShell**, using redirection (`>`) can cause the file to be encoded in UTF-16, which will lead to "null bytes" errors when running the tool. It is highly recommended to provide the filename directly as an argument to `--generate-config` to ensure UTF-8 encoding.

When the named file already exists, `--generate-config` asks before replacing it and keeps the previous version in a timestamped `.bak` file next to it. Outside a terminal it refuses and names `--force`, which replaces the file after taking the same backup. Shell redirection (`>`) is handled by the shell, so it still truncates without asking.

Edit the `github_monitor.conf` file and change any desired configuration options (detailed comments are provided for each).

`--setup --config-file PATH --env-file PATH` selects custom wizard destinations. Setup parses an existing config as data and preserves its supported settings. It moves usable secrets found there into the dotenv output. Nothing is written during questioning or section edits. **Save settings** validates the complete generated config then prepares both files before replacing either destination.

`TARGET_GITHUB_USERNAME` stores the optional default monitoring target. The setup wizard writes it only when you choose to persist the target. A positional GitHub username or profile URL takes precedence.

Startup resolves values in this order:

1. Built-in defaults
2. The selected configuration file
3. The selected dotenv file
4. Exported secret environment variables
5. Explicit command-line options

An exported secret overrides the same key from a dotenv file. An explicit command-line option overrides every saved source. Startup checks use these effective values instead of the defaults that existed when the module was imported.

Use `--config-file none` to disable automatic config discovery for one run.

<a id="terminal-colours"></a>
### Terminal Colours

`COLORED_OUTPUT` controls whether live terminal output is coloured. It defaults to `True` and is read before the startup banner is printed, so a configured value applies to the first line. `--no-color` disables colour for one run. Colour also switches itself off when output is redirected or piped, when `TERM` is unset or `dumb` and when the standard [`NO_COLOR`](https://no-color.org/) environment variable is set. Log files always remain plain text with ANSI escape sequences stripped.

`COLOR_THEME` overrides individual colours. It is merged over the built-in theme, so name only the parts you want to change:

```ini
COLOR_THEME = { "repository": "bright_magenta bold", "username": "green" }
```

A value combines one colour with any number of style attributes separated by spaces or `+`. Examples include `"bright_cyan bold"`, `"red underline"` and `"bright_magenta bold underline"`. An empty string leaves that part uncoloured.

| Colours | Styles |
| --- | --- |
| `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white` and the matching `bright_` variants such as `bright_red` | `bold`, `dim`, `underline`, `blink` |

| Theme key | Colours |
| --- | --- |
| `header` | The startup banner plus Setup Wizard and Doctor headings |
| `section` | Commands the wizard tells you to run and Doctor section names |
| `username` | GitHub usernames, display names and user context values |
| `id` | Event, review and commit identifiers |
| `status_online` | Public, online, available and unblocked states, including `Public profile: Yes` and `Blocked by the user: No` |
| `status_offline` | Private, blocked and offline states, including `Public profile: No` and `Blocked by the user: Yes` |
| `status_other` | Unknown or any other reported status value |
| `repository` | Repository names |
| `event` | Event types plus release, issue and discussion titles |
| `commit` | Commit messages |
| `branch` | Branches, refs and target commitish values |
| `duration` | Polling intervals and elapsed times |
| `timestamp_label` | The `Timestamp:` label. Empty by default so the label stays plain |
| `timestamp` | Timestamp values |
| `info` | Informational lines, prompts and recovery actions |
| `warning` | Warning lines and wizard validation notices |
| `error` | Error lines and failed verdicts |
| `signal` | Received-signal lines |
| `email` | Email addresses and email delivery lines |
| `webhook` | Webhook delivery lines |
| `date` | Single dates and times |
| `date_range` | Date and hour ranges |
| `boolean_true` | `True`, `Enabled`, `On` and Doctor PASS values |
| `boolean_false` | `False`, `Disabled`, `Off` and Doctor FAIL values |
| `count_up` | Values in reported increases such as `from 10 to 12` and `(+2)` |
| `count_down` | Values in reported decreases such as `from 12 to 10` and `(-2)` |
| `url` | HTTP and HTTPS links |

Static counts stay plain. Only values that report a change receive `count_up` or `count_down`.

`TRUNCATE_CHARS` limits visible terminal width without shortening log lines. `--truncate N` overrides it for one run. Use `999` to detect the current terminal width. Truncation is ignored when logging is disabled. Install the optional `wcwidth` package for correct display widths with wide Unicode characters.

On Windows install the optional `colorama` package for the best results in classic Command Prompt. Windows Terminal needs no additional package.

<a id="github-personal-access-token"></a>
### GitHub Personal Access Token

Go to your GitHub token settings: [https://github.com/settings/tokens](https://github.com/settings/tokens)

Then create a personal access token with the access needed for the accounts and repositories you monitor.

The preferred method validates the token against the configured GitHub API before saving it to `.env`. Input is hidden and the dotenv file is changed only after GitHub returns the authenticated login:

```sh
github_monitor --set-github-token
```

Use `--env-file` to select another private settings file:

```sh
github_monitor --set-github-token --env-file /path/.env-github_monitor
```

GitHub Enterprise users can validate against their HTTPS API URL in the same step:

```sh
github_monitor --set-github-token --github-url "https://github.example/api/v3"
```

Fallback methods are:

- Set `GITHUB_TOKEN` as an [environment variable](#storing-secrets)
- Add `GITHUB_TOKEN=...` manually to a [dotenv file](#storing-secrets)
- Pass it for one run with `-t` or `--github-token`, which may leave it in shell history or process listings
- Hard-code it in the configuration file or source code

If you update `GITHUB_TOKEN` in the active dotenv file, send a `SIGHUP` signal to reload it without restarting the tool. More information is available in [Storing Secrets](#storing-secrets) and [Signal Controls (macOS/Linux/Unix)](#signal-controls-macoslinuxunix).

<a id="github-api-url"></a>
### GitHub API URL

By default the tool uses Public Web GitHub API URL: [https://api.github.com](https://api.github.com)

If you want to use GitHub Enterprise API URL then change `GITHUB_API_URL` (or use `-x` flag) to: `https://{your_hostname}/api/v3`

The startup connectivity check follows the effective GitHub API URL unless `CHECK_INTERNET_URL` names a separate endpoint. Its request uses the effective `CHECK_INTERNET_TIMEOUT`. A `--github-url` override is applied before this check runs.


<a id="events-to-monitor"></a>
### Events to Monitor

You can limit the type of events that will be monitored and reported by the tool. You can do it by changing the `EVENTS_TO_MONITOR` configuration option.

By default all events are monitored, but if you want to limit it, then remove the `ALL` keyword and leave the events you are interested in, for example:

```
EVENTS_TO_MONITOR=['PushEvent', 'PullRequestEvent', 'IssuesEvent', 'ForkEvent', 'ReleaseEvent', 'DiscussionEvent']
```

<a id="repositories-to-monitor"></a>
### Repositories to Monitor

When tracking repository changes (`-j` flag), you can limit which repositories will be monitored for detailed changes (stargazers, watchers, forks, issues, PRs, discussions, etc.). You can do it by changing the `REPOS_TO_MONITOR` configuration option or via the `--repos` command-line argument (see [Monitoring Mode](#monitoring-mode)).

By default all repositories are monitored (`REPOS_TO_MONITOR = ['ALL']`), but if you want to monitor only specific repositories, you can use the `'user/repo_name'` format:

```
REPOS_TO_MONITOR = ['user1/repo1', 'user2/repo2', 'user1/repo3']
```

This allows you to have different repository lists for different users. When the tool runs for a specific user, it will only monitor repositories where the user matches the user in the list.

Note: When using a specific list (not `'ALL'`), newly created repositories will NOT be automatically monitored - only repositories explicitly listed will be monitored.

> **GitHub API change since 30 Jun 2026:** GitHub restricts repository stargazer and watcher identity lists to repository admins and collaborators. When you monitor the account that owns the configured token, github_monitor continues tracking individual stargazers and watchers. When you monitor another account, github_monitor silently skips those identity list requests and tracks only the numeric stargazer and watcher counts. Other repository change tracking remains available. See [GitHub's announcement](https://github.blog/changelog/2026-06-30-upcoming-access-restrictions-to-public-api-endpoints-and-ui-views/).

<a id="time-zone"></a>
### Time Zone

By default, time zone is auto-detected using `tzlocal`. You can set it manually in `github_monitor.conf`:

```ini
LOCAL_TIMEZONE='Europe/Warsaw'
```

You can get the list of all time zones supported by pytz like this:

```sh
python3 -c "import pytz; print('\n'.join(pytz.all_timezones))"
```
<a id="smtp-settings"></a>
### SMTP Settings

If you want to use email notifications functionality, configure SMTP settings in the `github_monitor.conf` file.

Verify your SMTP settings by using `--send-test-email` flag (the tool will try to send a test email notification):

```sh
github_monitor --send-test-email
```

<a id="webhook-settings"></a>
### Webhook Settings

GitHub Monitor can send activity alerts through Discord or the native [ntfy publish API](https://docs.ntfy.sh/publish/). Webhook alerts work with or without email.

For Discord:

1. Open the server channel that should receive alerts.
2. Select **Edit Channel**, open **Integrations** then choose **Webhooks**.
3. Create a webhook and copy its private URL.
4. Save it through the hidden prompt:

```sh
github_monitor --set-webhook-url
```

For ntfy.sh or a self-hosted ntfy server, choose a private topic and save its complete HTTPS URL such as `https://ntfy.sh/github-monitor-long-random-value`. Public `ntfy.sh` URLs select the ntfy request format automatically. Set the provider in `github_monitor.conf` for a self-hosted endpoint:

```ini
WEBHOOK_PROVIDER = "ntfy"
```

Topics on the public ntfy.sh service are public unless protected through an account reservation. Treat an unprotected topic name like a password. For a protected topic, store the access token in an environment variable or dotenv file:

```ini
NTFY_ACCESS_TOKEN="tk_your_ntfy_access_token"
```

GitHub Monitor sends this value as `Authorization: Bearer <token>`. `NTFY_ACCESS_TOKEN` takes precedence over an `Authorization` entry in `WEBHOOK_HEADERS`. Query parameters already present in the topic URL are preserved.

Enable the master switch and select the alert categories you want:

```ini
WEBHOOK_ENABLED = True
WEBHOOK_PROVIDER = "discord"
WEBHOOK_PROFILE_NOTIFICATION = True
WEBHOOK_EVENT_NOTIFICATION = True
WEBHOOK_REPO_NOTIFICATION = False
WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION = False
WEBHOOK_CONTRIB_NOTIFICATION = False
WEBHOOK_ERROR_NOTIFICATION = True
```

Send one test webhook without starting monitoring:

```sh
github_monitor --send-test-webhook
```

For a one-run test, the provider and destination can be overridden without changing the config file:

```sh
github_monitor --webhook-provider ntfy --webhook-url "https://ntfy.sh/your-private-topic" --send-test-webhook
```

Known Discord and `ntfy.sh` URLs automatically select the matching request format even if the configured provider is stale. Set `WEBHOOK_PROVIDER` in `github_monitor.conf` or use `--webhook-provider {discord,ntfy}` for self-hosted ntfy or compatible endpoints.

A URL passed on the command line may remain visible in shell history or process listings. Prefer `--set-webhook-url`, an environment variable or a dotenv file for normal setup.

`WEBHOOK_USERNAME` and `WEBHOOK_AVATAR_URL` change the sender identity for Discord-format payloads. `WEBHOOK_HEADERS` adds validated static or placeholder-based headers to Discord and ntfy requests:

```ini
WEBHOOK_USERNAME = "GitHub Monitor"
WEBHOOK_AVATAR_URL = "https://example.com/path/avatar.png"
WEBHOOK_HEADERS = {
    "X-Webhook-Title": "{title}",
}
```

Header values support the same placeholders as `WEBHOOK_TEMPLATE`. GitHub Monitor validates header names and values before and after placeholder expansion so formatted values cannot introduce line breaks or invalid headers. Prefer `NTFY_ACCESS_TOKEN` for ntfy bearer authentication. Basic authentication remains available through a custom `Authorization` header. Long ntfy messages are visibly truncated below ntfy's 4 KB boundary so they remain notifications instead of temporary attachments.

`WEBHOOK_TEMPLATE` controls the Discord-format request body. It supports `{title}`, `{description}`, `{version}`, `{image_url}`, `{fields}`, `{fields_str}`, `{color}`, `{timestamp}`, `{username}` and `{avatar_url}`. A dictionary or list is sent as JSON. A string template is sent as the raw request body for compatible custom integrations. Dictionary payloads always replace `allowed_mentions` with `{"parse": []}` so alert text cannot trigger Discord mentions.

`WEBHOOK_TEMPLATE`, `WEBHOOK_USERNAME` and `WEBHOOK_AVATAR_URL` apply only to Discord and are ignored when `WEBHOOK_PROVIDER` is `"ntfy"`. The ntfy provider needs no template: it sends the alert body as a native ntfy message with the subject as its title. Customize ntfy delivery through `WEBHOOK_HEADERS` (for example `X-Priority` or `X-Tags`).

`WEBHOOK_TRANSFORMS` applies string methods before the template and headers are rendered:

```ini
WEBHOOK_TRANSFORMS = [
    ("title", "upper"),
    ("description", "replace", "**", ""),
    ("description", "strip"),
]
```

The tuple format is `(field_to_target, method_name, *optional_arguments)`. Invalid templates, avatar URLs, transforms or formatted headers fail before a request is attempted. If a webhook service returns a rate limit or temporary server error, GitHub Monitor retries once and waits at most five seconds. GitHub monitoring continues normally if delivery fails.

<a id="storing-secrets"></a>
### Storing Secrets

Prefer `--set-github-token` for `GITHUB_TOKEN` and `--set-webhook-url` for `WEBHOOK_URL` because both commands keep input hidden. GitHub token setup also validates the secret before saving it. Store `SMTP_PASSWORD` and `NTFY_ACCESS_TOKEN` as environment variables or in a dotenv file.

As a fallback, set environment variables using `export` on **Linux/Unix/macOS/WSL** systems:

```sh
export GITHUB_TOKEN="your_github_classic_personal_access_token"
export SMTP_PASSWORD="your_smtp_password"
export WEBHOOK_URL="https://discord.com/api/webhooks/your_id/your_token"
export NTFY_ACCESS_TOKEN="tk_your_ntfy_access_token"
```

On **Windows Command Prompt** use `set` instead of `export` and on **Windows PowerShell** use `$env`.

Alternatively add them manually to a dotenv file:

```ini
GITHUB_TOKEN="your_github_classic_personal_access_token"
SMTP_PASSWORD="your_smtp_password"
WEBHOOK_URL="https://discord.com/api/webhooks/your_id/your_token"
NTFY_ACCESS_TOKEN="tk_your_ntfy_access_token"
```

An `export ` prefix in front of a dotenv line is accepted, so the same file can be sourced by a shell. `--set-github-token`, `--set-webhook-url` and `--setup` replace such a line in place and keep its prefix, rather than leaving the old value behind.

If the same secret is set in more than one place, an exported environment variable wins over the dotenv file, which wins over the config file, and an explicit command-line value wins over all of them. `--verbose` and `--doctor` both report which source each secret came from, so a forgotten `export` is visible rather than silent.

By default the tool will auto-search for dotenv file named `.env` in current directory and then upward from it.

You can specify a custom file with `DOTENV_FILE` or `--env-file` flag:

```sh
github_monitor <github_username> --env-file /path/.env-github_monitor
```

 You can also disable `.env` auto-search with `DOTENV_FILE = "none"` or `--env-file none`:

```sh
github_monitor <github_username> --env-file none
```

Exported secret environment variables continue to work when dotenv auto-search is disabled or no dotenv file exists.

The final fallback is storing secrets in the configuration file or source code.

Sending a `SIGHUP` signal reloads `GITHUB_TOKEN`, `SMTP_PASSWORD`, `WEBHOOK_URL` and `NTFY_ACCESS_TOKEN` from the active dotenv file without restarting the tool.

<a id="tls-verification"></a>
### TLS Verification

The tool verifies the TLS certificate of every server it contacts: the GitHub API, the GitHub web pages it reads, the connectivity check endpoint and, when enabled, the webhook service.

Set `VERIFY_SSL` to `False` only on a network that intercepts TLS with its own certificate authority, such as a corporate proxy. With verification off, an intercepted connection cannot be told apart from the real service.

The startup summary shows `TLS verification` and [`--doctor`](#doctor-preflight) reports a warning while it is off.

<a id="usage"></a>
## Usage

<a id="monitoring-mode"></a>
### Monitoring Mode

To monitor specific user activities and profile changes, simply enter the GitHub username as a command-line argument (`github_username` in the example below):

```sh
github_monitor github_username
```

It will track all user profile changes (e.g. changed followers, followings, starred repositories, username, email, bio, location, blog URL, number of repositories) and also all GitHub events (e.g. new pushes, PRs, issues, forks, releases etc.).

If you have not saved `GITHUB_TOKEN`, the `-t` flag remains available as a one-run fallback. The value may remain in shell history or process listings:

```sh
github_monitor github_username -t "your_github_classic_personal_access_token"
```

By default, the tool looks for a configuration file named `github_monitor.conf` in:
 - current directory
 - home directory (`~`)
 - script directory

 If you generated a configuration file as described in [Configuration](#configuration), but saved it under a different name or in a different directory, you can specify its location using the `--config-file` flag:


```sh
github_monitor <github_username> --config-file /path/github_monitor_new.conf
```

If you want to monitor changes to user's public repositories (e.g. new stargazers, watchers, forks, issues, PRs, discussions, changed descriptions etc.) then use the `-j` flag:

```sh
github_monitor github_username -j
```

By default, only user-owned repos are tracked. To include forks and collaborations, set `GET_ALL_REPOS` to `True` or use the `-a` flag:

```sh
github_monitor github_username -j -a
```

If you want to monitor only specific repositories instead of all user-owned repositories, you can do it via the `--repos` command-line flag or the `REPOS_TO_MONITOR` configuration option (see [Repositories to Monitor](#repositories-to-monitor)). Use the `--repos` flag with a comma-separated list of repository names:

```sh
github_monitor github_username -j --repos "repo1,repo2,repo3"
```

This will only monitor detailed changes (stargazers, watchers, forks, issues, PRs, discussions, etc.) for the specified repositories. The `--repos` flag requires the `-j` flag to be enabled and overrides the `REPOS_TO_MONITOR` configuration option.

Note: When using a specific list, newly created repositories will NOT be automatically monitored - only repositories explicitly listed will be monitored.

If you want to track user's daily contributions then use the `-m` flag:

```sh
github_monitor github_username -m
```

Daily contribution checks read the requested day from a wider 30-day GitHub calendar window that ends at the following midnight. This avoids transient partial counts that narrow or farther-future GraphQL windows can return.

If for any reason you do not want to monitor GitHub events for the user (e.g. new pushes, PRs, issues, forks, releases etc.), then use the `-k` flag:

```sh
github_monitor github_username -k
```

The tool runs until interrupted (`Ctrl+C`). Use `tmux` or `screen` for persistence.

You can monitor multiple GitHub users by running multiple instances of the script.

The tool automatically saves its output to `github_monitor_<username>.log` file. It can be changed in the settings via `GITHUB_LOGFILE` configuration option or disabled completely via `DISABLE_LOGGING` / `-d` flag.

Set `ASCII_LOG_SEPARATORS` to `"Auto"` (default) to use ASCII separator-only lines on Windows, `"On"` to use them on every operating system or `"Off"` to preserve Unicode separators in logs everywhere. Terminal separators stay Unicode. Log files and all other logged text remain UTF-8.

<a id="listing-mode"></a>
### Listing Mode

There is another mode of the tool that displays various requested information (`-r`, `-g`, `-f` and `-l` flags).

If you want to display a list of public repositories (with some basic statistics) for the user then use the `-r` flag:

```sh
github_monitor github_username -r
```

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_list_of_repos.png" alt="github_list_of_repos" width="90%"/>
</p>

By default, only user-owned repos are listed. To include forks and collaborations, set `GET_ALL_REPOS` to `True` or use the `-a` flag:

```sh
github_monitor github_username -r -a
```

If you want to display a list of repositories starred by the user then use the `-g` flag:

```sh
github_monitor github_username -g
```

If you want to display a list of followers and followings for the user then use the `-f` flag.

```sh
github_monitor github_username -f
```

If you want to get the list of recent GitHub events for the user then use the `-l` flag. You can also add the `-n` flag to specify how many events should be displayed. By default, it shows the last 5 events.

```sh
github_monitor github_username -l -n 10
```

If you want to not only display, but also save the list of recent GitHub events to a CSV file, use the `-l` flag with `-b` indicating the CSV file. As before, you can add the `-n` flag to specify how many events should be displayed/saved:

```sh
github_monitor github_username -l -n 10 -b github_username.csv
```

<a id="email-notifications"></a>
### Email Notifications

To enable email notifications for all user profile changes (e.g. changes in followers, followings, starred repositories, username, email, bio, location, blog URL and number of repositories):
- set `PROFILE_NOTIFICATION` to `True`
- or use the `-p` flag

```sh
github_monitor github_username -p
```

To receive email notifications when new GitHub events appear for the user (e.g. new pushes, PRs, issues, forks, releases etc.):
- set `EVENT_NOTIFICATION` to `True`
- or use the `-s` flag

```sh
github_monitor github_username -s
```

To get email notifications when changes in user repositories are detected (e.g. changes in stargazers, watchers, forks, issues, PRs, discussions, descriptions, etc., except for the update date):
- set `REPO_NOTIFICATION` to `True`
- or use the `-q` flag

```sh
github_monitor github_username -j -q
```

To be informed whenever changes in the update date of user repositories are detected:
- set `REPO_UPDATE_DATE_NOTIFICATION` to `True`
- or use the `-u` flag

```sh
github_monitor github_username -j -u
```

The last two options (`-q` and `-u`) only work if tracking of repositories changes is enabled (`-j`).

To be informed about user's daily contributions:
- set `CONTRIB_NOTIFICATION` to `True`
- or use the `-y` flag

```sh
github_monitor github_username -m -y
```

The `-y` only works if tracking of daily contributions is enabled (`-m`).

To disable sending an email on errors (enabled by default):
- set `ERROR_NOTIFICATION` to `False`
- or use the `-e` flag

```sh
github_monitor github_username -e
```

You can combine all email notifications flags together if needed.

Make sure you defined your SMTP settings earlier (see [SMTP settings](#smtp-settings)).

Example email:

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor_email_notifications.png" alt="github_monitor_email_notifications" width="90%"/>
</p>

<a id="webhook-notifications"></a>
### Webhook Notifications

Webhook event controls mirror the email categories but work independently:

| Event | Config setting | CLI override |
| --- | --- | --- |
| Profile changes | `WEBHOOK_PROFILE_NOTIFICATION` | `--webhook-profile` |
| New GitHub events | `WEBHOOK_EVENT_NOTIFICATION` | `--webhook-events` |
| Repository changes | `WEBHOOK_REPO_NOTIFICATION` | `--webhook-repo-changes` |
| Repository update date changes | `WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION` | `--webhook-repo-update-date` |
| Daily contribution changes | `WEBHOOK_CONTRIB_NOTIFICATION` | `--webhook-daily-contribs` |
| Monitoring errors | `WEBHOOK_ERROR_NOTIFICATION` | Enable with `--webhook-errors` or disable with `--no-webhook-error-notify` |

Use `--webhook` or `--no-webhook` to turn all configured webhook alerts on or off for one run. A category override also enables the master webhook switch. For example:

```sh
github_monitor github_username --webhook-profile --webhook-events
```

Repository webhook categories only work with `-j` or `--track-repos-changes`. Contribution webhooks only work with `-m` or `--track-contribs-changes`. Event webhooks are disabled when `-k` or `--no-monitor-events` is used.

The provider and destination can also be overridden for one run:

```sh
github_monitor github_username --webhook-provider ntfy --webhook-url "https://ntfy.sh/your-private-topic" --webhook-events
```

See [Webhook Settings](#webhook-settings) for private URL setup, ntfy authentication and advanced payload customization.

<a id="csv-export"></a>
### CSV Export

If you want to save all GitHub user events, profile changes and repository updates to a CSV file, set `CSV_FILE` or use `-b` flag:

```sh
github_monitor <github_username> -b github_username.csv
```

The file will be automatically created if it does not exist.

<a id="check-intervals"></a>
### Check Intervals

If you want to customize the polling interval, use `-c` flag (or `GITHUB_CHECK_INTERVAL` configuration option):

```sh
github_monitor <github_username> -c 900
```

It is generally not recommended to use values lower than 10 minutes as new events are very often delayed by GitHub API.

<a id="signal-controls-macoslinuxunix"></a>
### Signal Controls (macOS/Linux/Unix)

The tool has several signal handlers implemented which allow to change behavior of the tool without a need to restart it with new configuration options / flags.

List of supported signals:

| Signal | Description |
| ----------- | ----------- |
| USR1 | Toggle email notifications for all user's profile changes (-p) |
| USR2 | Toggle email notifications for new GitHub events (-s) |
| CONT | Toggle email notifications for user's repositories changes (except for update date) (-q) |
| PIPE | Toggle email notifications for user's repositories update date changes (-u) |
| URG | Toggle email notifications for user's daily contributions changes (-y) |
| TRAP | Increase the user check interval (by 1 min) |
| ABRT | Decrease the user check interval (by 1 min) |
| HUP | Reload secrets from .env file |

Send signals with `kill` or `pkill`, e.g.:

```sh
pkill -USR1 -f "github_monitor <github_username>"
```

As Windows supports limited number of signals, this functionality is available only on Linux/Unix/macOS.

<a id="coloring-log-output-with-grc"></a>
### Coloring Log Output with GRC

You can use [GRC](https://github.com/garabik/grc) to color logs.

Add to your GRC config (`~/.grc/grc.conf`):

```
# monitoring log file
.*_monitor_.*\.log
conf.monitor_logs
```

Now copy the [conf.monitor_logs](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/grc/conf.monitor_logs) to your `~/.grc/` and log files should be nicely colored when using `grc` tool.

Example:

```sh
grc tail -F -n 100 github_monitor_<username>.log
```

<a id="doctor-preflight"></a>
### Doctor Preflight

Run the comprehensive preflight before monitoring a new target or when a working setup starts failing:

```sh
github_monitor --doctor <github_username>
```

Doctor is read-only by default. It checks the effective configuration after config, dotenv, environment and command-line precedence without creating logs, CSV files or directories. It opens with the detected install method, then reports these fixed sections:

* Environment: Python support, required dependencies and optional dependencies.
* Configuration: selected files, secret names and sources, [TLS verification](#tls-verification), GitHub URLs, timezone, polling interval, log separator mode and the log and CSV files monitoring would write.
* Authentication and connectivity: live token validation plus the configured connectivity endpoint.
* Target and monitoring: target access, repository, starred repository and event feeds and optional contribution tracking.
* Notifications: whether email and webhook alerts are disabled, unusable or ready.

Every check uses one of four stable markers: `[PASS]`, `[WARN]`, `[FAIL]` or `[SKIP]`. Warnings keep exit status `0`. Any failed check or approved delivery test returns exit status `1`, so doctor can be used in a container healthcheck or CI smoke test.

When stdin is interactive and a notification channel is ready, doctor offers a separate default-no approval for one real email and one real webhook. A piped or non-interactive run never sends messages. Review the sanitized report before posting it because targets, paths and recipient addresses can still identify your setup.

<a id="debugging-and-recovery"></a>
### Debugging and Recovery

Failures that stop an action use one consistent shape:

```text
* Error: What failed
To fix: The next action to take
Guide: A relevant documentation link
```

Verbose mode answers "what did the tool decide?" It expands the startup summary, includes stable recovery codes and states when missing data prevents a specific alert from firing during the current check:

```sh
github_monitor <github_username> --verbose
```

Debug mode answers "what did the tool do?" Every line is timestamped, names the operation, then lists its details as comma-separated `key=value` fields:

```
[DEBUG 23:53:52] Webhook delivery: channel=discord, host=https://discord.com, attempt=1/2, timeout=10s
[DEBUG 23:53:52] Webhook delivery: channel=discord, outcome=OK, attempt=2/2
```

The fields carry the endpoint, timeout, masked credential, response status, retry decision, file path and monitoring timing used by the relevant operation:

```sh
github_monitor <github_username> --debug
```

The modes cover the full runtime path:

* Direct HTTP, PyGithub and SMTP operations report their destination and timeout. Every configured credential is rendered as the fixed `<redacted>` marker inside the printer.
* Exceptions that would otherwise be swallowed name the failed operation and exception type in debug output.
* Degraded profile, repository, contribution and event checks state which alert cannot fire in verbose output.
* Email and webhook deliveries report the attempt, response, retryability, wait and confirmed outcome as `outcome=OK` or `outcome=failed`.
* Config, dotenv, CSV, log and private-setting file operations report both success and failure branches.
* Retries and monitoring sleeps report their reason, interval and next timestamp.
* Config loading reports its file and applied setting count. Private-setting resolution reports each setting name and source without printing its value.

`VERBOSE_MODE` and `DEBUG_MODE` provide the same controls in the configuration file. An explicit command-line flag takes precedence even when the selected config disables that mode, including while the config is being loaded. Diagnostic runs keep the terminal history visible instead of clearing it. Both printers sanitize internally so loaded secrets plus common GitHub token, authorization and Discord webhook shapes are redacted before terminal or log output.

Recovery codes are stable identifiers such as `config.invalid`, `auth.github_token_invalid`, `network.timeout`, `github.rate_limited` and `file.unwritable`. Include the code when asking for help. Commands printed after setup or inside recovery guidance automatically match a PyPI install or downloaded script with platform-correct quoting.

<a id="change-log"></a>
## Change Log

See [RELEASE_NOTES.md](https://github.com/misiektoja/github_monitor/blob/main/RELEASE_NOTES.md) for details.

<a id="contributing"></a>
## Contributing

Bug reports, documentation fixes and code contributions are welcome. See [CONTRIBUTING.md](https://github.com/misiektoja/github_monitor/blob/main/CONTRIBUTING.md) for the development setup, the checks CI enforces and what a change needs before it is merged. Participation is covered by the [Code of Conduct](https://github.com/misiektoja/github_monitor/blob/main/CODE_OF_CONDUCT.md).

<a id="security"></a>
## Security

Report a suspected vulnerability privately through [GitHub security advisories](https://github.com/misiektoja/github_monitor/security/advisories/new), never as a public issue. [SECURITY.md](https://github.com/misiektoja/github_monitor/blob/main/SECURITY.md) covers the reporting process, the supported versions and the security posture of stored credentials and configuration loading.

<a id="license"></a>
## License

Licensed under GPLv3. See [LICENSE](https://github.com/misiektoja/github_monitor/blob/main/LICENSE). Dependency licenses are listed in [THIRD_PARTY_NOTICES.md](https://github.com/misiektoja/github_monitor/blob/main/THIRD_PARTY_NOTICES.md).

<a id="support"></a>
## Support

Questions, bug reports and vulnerability reports each have a place, listed in [SUPPORT.md](https://github.com/misiektoja/github_monitor/blob/main/SUPPORT.md).

If the project is useful to you, you can support its development through [GitHub Sponsors](https://github.com/sponsors/misiektoja) or [Buy Me a Coffee](https://buymeacoffee.com/misiektoja).
