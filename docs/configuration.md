# Configuration

Examples on this page use the PyPI command `github_monitor`. Manual script users should keep the shown options and use the matching prefix under [Command Format by Installation Method](usage.md#command-format-by-installation-method).

<a id="configuration-file"></a>
## Configuration File

You can pass most settings as command-line options or save them in a configuration file for later runs.

The easiest way to create this file is `github_monitor --setup`.

To edit every available setting yourself, generate a default configuration file:

```sh
# On macOS, Linux or Windows Command Prompt (cmd.exe)
github_monitor --generate-config > github_monitor.conf

# On Windows PowerShell (recommended to avoid encoding issues)
github_monitor --generate-config github_monitor.conf
```

> **Windows PowerShell:** Pass the filename directly to `--generate-config`. PowerShell redirection can write UTF-16, which the tool rejects with a "null bytes" error.

When the named file already exists, `--generate-config` asks before replacing it and keeps a timestamped `.bak` backup next to it. Add `--force` to replace it without the question.

The file contains a short explanation above each setting.

A configuration file is read as data, not executed. The tool accepts only `SETTING = value` lines where the name is one of the documented settings and the value is a plain literal such as a string, number, `True`, `False`, `None`, a list or a dictionary. Comments and blank lines are fine.

Imports, function calls, expressions and unknown settings are rejected with the setting and line number to correct.

If the same setting appears in more than one place, the item later in this list wins:

1. Built-in defaults
2. The discovered or explicitly selected configuration file
3. Values from the selected `.env` file
4. Secret environment variables
5. Command-line options

By default the tool looks for a configuration file named `github_monitor.conf` in the current directory, the home directory (`~`) and the script directory. Use `--config-file` to name another location or `--config-file none` to disable automatic config discovery for one run.

<a id="github-api-url"></a>
## GitHub API URL

By default the tool uses the Public Web GitHub API URL: [https://api.github.com](https://api.github.com)

If you want to use a GitHub Enterprise API URL then change `GITHUB_API_URL` (or use the `-x` flag) to: `https://{your_hostname}/api/v3`

The startup connectivity check follows the effective GitHub API URL unless `CHECK_INTERNET_URL` names a separate endpoint. Its request uses the effective `CHECK_INTERNET_TIMEOUT`. A `--github-url` override is applied before this check runs.

<a id="events-to-monitor"></a>
## Events to Monitor

You can limit the type of events that will be monitored and reported by the tool. You can do it by changing the `EVENTS_TO_MONITOR` configuration option.

By default all events are monitored, but if you want to limit it, then remove the `ALL` keyword and leave the events you are interested in, for example:

```ini
EVENTS_TO_MONITOR=['PushEvent', 'PullRequestEvent', 'IssuesEvent', 'ForkEvent', 'ReleaseEvent', 'DiscussionEvent']
```

<a id="push-event-commits"></a>
## Push Event Commits

A push can carry hundreds of commits. Reporting every one in full costs an extra GitHub API request each and produces a notification nobody reads, so only `PUSH_COMMITS_LIMIT` commits of a push are reported with their date, author URL, statistics and changed files. The rest are replaced by one line naming how many were left out.

```ini
PUSH_COMMITS_LIMIT = 10
PUSH_COMMITS_ORDER = 'newest'
PUSH_COMMITS_OVERFLOW = 'count'
PUSH_FILES_LIMIT = 20
```

| Option | Values | Effect |
| --- | --- | --- |
| `PUSH_COMMITS_LIMIT` | integer, `0` for no limit | Commits of one push reported in full, also `--push-commits-limit` |
| `PUSH_COMMITS_ORDER` | `'newest'`, `'oldest'` | Which end of the push keeps the detailed commits |
| `PUSH_COMMITS_OVERFLOW` | `'count'`, `'summary'` | Whether the remaining commits become a single count or get one line each |
| `PUSH_FILES_LIMIT` | integer, `0` for no limit | Changed files listed per commit, also `--push-files-limit` |

With the built-in values a 300-commit push spends about 12 requests instead of about 300. It reports the 10 newest commits in full and replaces the other 290 with `Commits 1-290 not reported in full`. The compare URL in the same report links the complete diff.

The limits in effect appear as `Push commit details` and `Push changed files` in the startup summary, which `--verbose` and `--debug` print on screen and every run writes to the log file.

Set `PUSH_COMMITS_OVERFLOW = 'summary'` to list those commits one line each instead, with their SHA, author and first message line. Those lines are built from data the tool already fetched, so they cost no extra requests, but a large push then produces a long notification. Set `PUSH_COMMITS_LIMIT = 0` to report every commit of every push in full.

<a id="repositories-to-monitor"></a>
## Repositories to Monitor

When tracking repository changes (`-j` flag), you can limit which repositories will be monitored for detailed changes (stargazers, watchers, forks, issues, PRs, discussions, etc.). You can do it by changing the `REPOS_TO_MONITOR` configuration option or via the `--repos` command-line argument (see [Monitoring Mode](usage.md#monitoring-mode)).

By default all repositories are monitored (`REPOS_TO_MONITOR = ['ALL']`), but if you want to monitor only specific repositories, you can use the `'user/repo_name'` format:

```ini
REPOS_TO_MONITOR = ['user1/repo1', 'user2/repo2', 'user1/repo3']
```

This allows you to have different repository lists for different users. When the tool runs for a specific user, it will only monitor repositories where the user matches the user in the list.

A failed repository-detail request keeps that repository's last successful snapshot. Other repositories still update and changes made during the outage are compared when access recovers. A repository absent from a successfully fetched list is no longer retained for detail comparisons. Expected counts-only stargazer and watcher monitoring does not count as an outage.

Note: When using a specific list (not `'ALL'`), newly created repositories will NOT be automatically monitored - only repositories explicitly listed will be monitored.

!!! note "GitHub API change since 30 Jun 2026"
    GitHub restricts repository stargazer and watcher identity lists to repository admins and collaborators. When you monitor the account that owns the configured token, github_monitor continues tracking individual stargazers and watchers. When you monitor another account, github_monitor silently skips those identity list requests and tracks only the numeric stargazer and watcher counts. Other repository change tracking remains available. See [GitHub's announcement](https://github.blog/changelog/2026-06-30-upcoming-access-restrictions-to-public-api-endpoints-and-ui-views/).

<a id="monitored-target"></a>
## Monitored Target

The GitHub target is a positional argument. It is required to start monitoring:

```sh
github_monitor <github_target>
```

The target can be a GitHub username or a complete profile URL.

To stop repeating it, save it in the configuration file:

```ini
TARGET_GITHUB_USERNAME = "github_username"
```

`TARGET_GITHUB_USERNAME` accepts the same forms as the command line. Then `github_monitor` alone starts monitoring that user. A positional argument still wins, so you can watch someone else for one run without editing the file:

```sh
github_monitor other_username
```

<a id="time-zone"></a>
## Time Zone

By default, time zone is auto-detected using `tzlocal`. You can set it manually in `github_monitor.conf`:

```ini
LOCAL_TIMEZONE='Europe/Warsaw'
```

You can get the list of all time zones supported by pytz like this:

```sh
python3 -c "import pytz; print('\n'.join(pytz.all_timezones))"
```

<a id="smtp-settings"></a>
## SMTP Settings

Email notifications need SMTP server details for the sending account. Add them to `github_monitor.conf` or use the setup wizard. Setup checks the login without sending an email. To replace only the password, run `github_monitor --set-smtp-password`. Password entry is hidden and preserves spaces.

Send one test message to verify the settings:

```sh
github_monitor --send-test-email
```

Which alerts each channel sends is covered in [Email Notifications](usage.md#email-notifications).

<a id="webhook-settings"></a>
## Webhook Settings

GitHub Monitor can send activity alerts through Discord or the native [ntfy publish API](https://docs.ntfy.sh/publish/). Webhook alerts work with or without email.

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

A `WEBHOOK_URL` left unset, or left at its `your_webhook_url` placeholder, switches webhook alerts off at startup instead of failing at the first alert. `--verbose` reports why.

Known Discord and `ntfy.sh` URLs automatically select the matching request format even if the configured provider is stale. While `WEBHOOK_PROVIDER` is left at its default, that detection is silent and `--verbose` reports it. A warning appears only when your configuration file sets a provider the URL disagrees with. Set `WEBHOOK_PROVIDER` in `github_monitor.conf` or use `--webhook-provider {discord,ntfy}` for self-hosted ntfy or compatible endpoints.

Send one test webhook without starting monitoring:

```sh
github_monitor --send-test-webhook
```

For a one-run test, the provider and destination can be overridden without changing the config file:

```sh
github_monitor --webhook-provider ntfy --webhook-url "https://ntfy.sh/your-private-topic" --send-test-webhook
```

A URL passed on the command line may remain visible in shell history or process listings. Prefer `--set-webhook-url`, an environment variable or a dotenv file for normal setup.

Which alerts each channel sends is covered in [Webhook Notifications](usage.md#webhook-notifications).

<a id="ntfy"></a>
### ntfy

For ntfy.sh or a self-hosted ntfy server, choose a private topic and save its complete HTTPS URL such as `https://ntfy.sh/github-monitor-long-random-value`. Public `ntfy.sh` URLs select the ntfy request format automatically. Set the provider in `github_monitor.conf` for a self-hosted endpoint:

```ini
WEBHOOK_PROVIDER = "ntfy"
```

The ntfy provider needs no template. GitHub Monitor sends the alert body as a native ntfy message with the subject as its title. Query parameters already present in the topic URL are preserved. Long ntfy messages are visibly truncated below ntfy's 4 KB boundary so they remain notifications instead of temporary attachments.

Topics on the public ntfy.sh service are public unless protected through an account reservation. Treat an unprotected topic name like a password. For a protected topic, store the access token in an environment variable or dotenv file:

```ini
NTFY_ACCESS_TOKEN="tk_your_ntfy_access_token"
```

GitHub Monitor sends this value as `Authorization: Bearer <token>`. `NTFY_ACCESS_TOKEN` takes precedence over an `Authorization` entry in `WEBHOOK_HEADERS`.

For compatibility with advanced webhook integrations, custom headers are also supported:

```ini
WEBHOOK_HEADERS = {
    "X-Webhook-Title": "{title}",
}
```

Header values support the same placeholders as `WEBHOOK_TEMPLATE`. GitHub Monitor validates header names and values before and after placeholder expansion so formatted values cannot introduce line breaks or invalid headers. Headers apply to both Discord and ntfy. Prefer `NTFY_ACCESS_TOKEN` for ntfy bearer authentication. Basic authentication remains available through a custom `Authorization` header. Customize ntfy delivery further through `WEBHOOK_HEADERS`, for example `X-Priority` or `X-Tags`.

<a id="discord"></a>
### Discord

If you are new to Discord, follow these steps to get your private webhook URL:

1. Open your GitHub alerts server and choose the channel that should receive them.
2. Select **Edit Channel**, open **Integrations** then choose **Webhooks**.
3. Create a webhook, choose a name if you want then copy its private URL.
4. Save it through the hidden prompt:

```sh
github_monitor --set-webhook-url
```

The command writes only `WEBHOOK_URL` to `.env` so the link does not appear in your command history. Treat this link like a password because anyone who has it can post through it.

Keep the default provider in `github_monitor.conf`:

```ini
WEBHOOK_PROVIDER = "discord"
```

Discord alerts carry the same emphasis as the HTML email, since Discord renders markdown in an embed. Bold values stay bold and links stay clickable. Only Discord gets that wording: ntfy receives the plain body, because it would show the markers literally.

<a id="advanced-discord-format-customization"></a>
### Advanced Discord-format customization

`WEBHOOK_USERNAME` and `WEBHOOK_AVATAR_URL` change the sender name and HTTPS avatar for Discord-format payloads:

```ini
WEBHOOK_USERNAME = "GitHub Monitor"
WEBHOOK_AVATAR_URL = "https://example.com/path/avatar.png"
```

`WEBHOOK_TEMPLATE` controls the Discord-format request body. It supports these placeholders:

- `{title}`
- `{description}`
- `{version}`
- `{image_url}`
- `{fields}` and `{fields_str}`
- `{color}`
- `{timestamp}`
- `{username}`
- `{avatar_url}`

Discord templates must produce a JSON object. Use a dictionary or a JSON string encoding an object, including legacy strings with doubled object braces. Lists, non-JSON strings and unsupported placeholders are rejected before delivery. Alert text is kept literal and all payloads replace `allowed_mentions` with `{"parse": []}` so alert text cannot trigger Discord mentions. Reloaded settings apply to the next delivery.

`WEBHOOK_TRANSFORMS` applies string methods to shared placeholder values before the template and headers are rendered:

```ini
WEBHOOK_TRANSFORMS = [
    ("title", "upper"),
    ("description", "replace", "**", ""),
    ("description", "strip"),
]
```

The tuple format is `(field_to_target, method_name, *optional_arguments)`. Invalid templates, avatar URLs, transforms or formatted headers fail before a request is attempted. `WEBHOOK_TEMPLATE`, `WEBHOOK_USERNAME` and `WEBHOOK_AVATAR_URL` apply only to the Discord request format and are ignored when `WEBHOOK_PROVIDER` is `"ntfy"`. ntfy continues to use its native publish API while transformations and header placeholders use the same shared title and description values.

If a webhook service returns a rate limit or temporary server error, GitHub Monitor retries once and waits at most five seconds. GitHub monitoring continues normally if delivery fails.

<a id="terminal-colours"></a>
## Terminal Colours

`COLORED_OUTPUT` controls whether live terminal output is coloured. It defaults to `True` and is read before the startup banner is printed, so a configured value applies to the first line. `--no-color` disables colour for one run. Colour also switches itself off when output is redirected or piped, when `TERM` is unset or `dumb` and when the standard [`NO_COLOR`](https://no-color.org/) environment variable is set. Log files always remain plain text with ANSI escape sequences stripped.

The `--help` screen is coloured too. Group headings, option names, the values those options take, the example commands and the comments above them each get their own colour, so the screen can be scanned instead of read.

`COLOR_THEME` overrides individual colours. It is merged over the built-in theme, so name only the parts you want to change:

The built-in colours apply unless you set `COLOR_THEME`. Older configurations may set every colour explicitly. Remove that block to use current defaults or edit individual values to keep a custom theme.

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
| `timestamp_value` | Timestamp values |
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
| `link` | HTTP and HTTPS links |
| `help_heading` | The `--help` group headings and example task names |
| `help_usage` | The `usage:` label |
| `help_option` | Option names such as `--doctor` |
| `help_metavar` | The value each option takes, such as a path or a number of seconds |
| `help_placeholder` | Values to replace in the help examples |
| `help_command` | The commands in the help examples |
| `help_comment` | The `#` comment above each help example |
| `help_default` | The `(default: ...)` notes |

Static counts stay plain. Only values that report a change receive `count_up` or `count_down`.

On Windows install the optional `colorama` package for the best results in classic Command Prompt. Windows Terminal needs no additional package.

<a id="storing-secrets"></a>
## Storing Secrets

Use `--set-github-token`, `--set-smtp-password` or `--set-webhook-url` to enter secrets through hidden prompts. Token setup validates with GitHub. SMTP setup checks sign-in without sending an email and requires the other mail settings first. Store `NTFY_ACCESS_TOKEN` in an environment variable or dotenv file.

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

By default the tool will auto-search for a dotenv file named `.env` in the current directory and then upward from it.

You can specify a custom file with `DOTENV_FILE` or the `--env-file` flag:

```sh
github_monitor <github_target> --env-file /path/.env-github_monitor
```

You can also disable `.env` auto-search with `DOTENV_FILE = "none"` or `--env-file none`:

```sh
github_monitor <github_target> --env-file none
```

Exported secret environment variables continue to work when dotenv auto-search is disabled or no dotenv file exists.

The final fallback is storing secrets in the configuration file or source code.

Sending a `SIGHUP` signal reloads `GITHUB_TOKEN`, `SMTP_PASSWORD`, `WEBHOOK_URL` and `NTFY_ACCESS_TOKEN` from the active dotenv file without restarting the tool.

<a id="tls-verification"></a>
## TLS Verification

The tool verifies the TLS certificate of every server it contacts: the GitHub API, the GitHub web pages it reads, the connectivity check endpoint, the mail server that delivers email alerts and, when enabled, the webhook service.

Set `VERIFY_SSL` to `False` only on a network that intercepts TLS with its own certificate authority, such as a corporate proxy. With verification off, an intercepted connection cannot be told apart from the real service.

The startup summary shows `TLS verification` and [`--doctor`](troubleshooting.md#doctor-preflight) reports a warning while it is off.

