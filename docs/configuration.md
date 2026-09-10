# Configuration

## Configuration File

Most settings can be configured via command-line arguments.

If you want to have it stored persistently, generate a default config template and save it to a file named `github_monitor.conf`:

```sh
# On macOS, Linux or Windows Command Prompt (cmd.exe)
github_monitor --generate-config > github_monitor.conf

# On Windows PowerShell (recommended to avoid encoding issues)
github_monitor --generate-config github_monitor.conf
```

!!! important
    On **Windows PowerShell**, using redirection (`>`) can cause the file to be encoded in UTF-16, which will lead to "null bytes" errors when running the tool. It is highly recommended to provide the filename directly as an argument to `--generate-config` to ensure UTF-8 encoding.

When the named file already exists, `--generate-config` asks before replacing it and keeps the previous version in a timestamped `.bak` file next to it. Outside a terminal it refuses and names `--force`, which replaces the file after taking the same backup. Shell redirection (`>`) is handled by the shell, so it still truncates without asking.

Edit the `github_monitor.conf` file and change any desired configuration options (detailed comments are provided for each).

By default the tool looks for a configuration file named `github_monitor.conf` in the current directory, the home directory (`~`) and the script directory. Use `--config-file` to name another location, or `--config-file none` to disable automatic config discovery for one run. The startup summary reports `Discovery disabled` when it is in effect.

`TARGET_GITHUB_USERNAME` stores the optional default monitoring target. The setup wizard writes it only when you choose to persist the target. A positional GitHub username or profile URL takes precedence.

Startup resolves values in this order:

1. Built-in defaults
2. The selected configuration file
3. The selected dotenv file
4. Exported secret environment variables
5. Explicit command-line options

An exported secret overrides the same key from a dotenv file. An explicit command-line option overrides every saved source. This includes `--no-color` in Doctor. Startup checks use these effective values instead of the defaults that existed when the module was imported.

## Liveness output

`LIVENESS_CHECK_INTERVAL` accepts a finite, nonnegative number of seconds. Set it to `0` to disable liveness output. The default is now 86400 seconds (24 hours), up from 43200 seconds (12 hours) in 2.6.3. Startup reports invalid values before making network requests.

## GitHub API URL

By default the tool uses the Public Web GitHub API URL: [https://api.github.com](https://api.github.com)

If you want to use a GitHub Enterprise API URL then change `GITHUB_API_URL` (or use the `-x` flag) to: `https://{your_hostname}/api/v3`

The startup connectivity check follows the effective GitHub API URL unless `CHECK_INTERNET_URL` names a separate endpoint. Its request uses the effective `CHECK_INTERNET_TIMEOUT`. A `--github-url` override is applied before this check runs.

## Events to Monitor

You can limit the type of events that will be monitored and reported by the tool. You can do it by changing the `EVENTS_TO_MONITOR` configuration option.

By default all events are monitored, but if you want to limit it, then remove the `ALL` keyword and leave the events you are interested in, for example:

```ini
EVENTS_TO_MONITOR=['PushEvent', 'PullRequestEvent', 'IssuesEvent', 'ForkEvent', 'ReleaseEvent', 'DiscussionEvent']
```

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

## Time Zone

By default, time zone is auto-detected using `tzlocal`. You can set it manually in `github_monitor.conf`:

```ini
LOCAL_TIMEZONE='Europe/Warsaw'
```

You can get the list of all time zones supported by pytz like this:

```sh
python3 -c "import pytz; print('\n'.join(pytz.all_timezones))"
```

Path settings are validated before startup opens files. A monitoring run stops and names the setting to correct. `--doctor`, `--setup` and the `--set-...` commands report the same setting and continue on the built-in value, so it can still be repaired. Command-line path overrides still take precedence.

## SMTP Settings

Private password entry preserves leading and trailing spaces. The exact value checked with the mail server is saved.

Private entry preserves literal `${...}` text in saved passwords and other secrets. Assignments that need this protection carry a `# monitor:literal` comment. Keep that comment when editing the value. Unmarked assignments retain their existing interpolation behavior. The marker is read by this monitor. Other dotenv readers or shells may still interpolate the value.

If you want to use email notifications functionality, configure SMTP settings in the `github_monitor.conf` file.

Save the mail server password through the hidden prompt, which signs in to the server before saving without sending anything:

```sh
github_monitor --set-smtp-password
```

Verify your SMTP settings by using the `--send-test-email` flag (the tool will try to send a test email notification):

```sh
github_monitor --send-test-email
```

Which alerts each channel sends is covered in [Email Notifications](usage.md#email-notifications).

## Webhook Settings

A delivery keeps its original destination and credentials for every retry. Provider errors also redact Bearer and Basic credentials echoed without their Authorization scheme. Reloaded settings apply to the next delivery. Discord templates must produce a JSON object. Dictionary templates and JSON strings are supported, including strings with escaped format braces. A placeholder the alert cannot fill, such as `{title[0]}` or `{0}`, is reported with the template text that failed. Mentions remain disabled in every template.

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

A `WEBHOOK_URL` left unset, or left at its `your_webhook_url` placeholder, switches webhook alerts off at startup instead of failing at the first alert. `--verbose` reports why.

Send one test webhook without starting monitoring:

```sh
github_monitor --send-test-webhook
```

For a one-run test, the provider and destination can be overridden without changing the config file:

```sh
github_monitor --webhook-provider ntfy --webhook-url "https://ntfy.sh/your-private-topic" --send-test-webhook
```

Known Discord and `ntfy.sh` URLs automatically select the matching request format even if the configured provider is stale. While `WEBHOOK_PROVIDER` is left at its default, that detection is silent and `--verbose` reports it. A warning appears only when your configuration file sets a provider the URL disagrees with. Set `WEBHOOK_PROVIDER` in `github_monitor.conf` or use `--webhook-provider {discord,ntfy}` for self-hosted ntfy or compatible endpoints.

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

`WEBHOOK_TEMPLATE` controls the Discord-format request body. It supports `{title}`, `{description}`, `{version}`, `{image_url}`, `{fields}`, `{fields_str}`, `{color}`, `{timestamp}`, `{username}` and `{avatar_url}`. Use a dictionary or a JSON string encoding an object. Lists and non-JSON strings are rejected before delivery. All payloads replace `allowed_mentions` with `{"parse": []}` so alert text cannot trigger Discord mentions.

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

Which alerts each channel sends is covered in [Webhook Notifications](usage.md#webhook-notifications).

## Storing Secrets

Prefer `--set-github-token` for `GITHUB_TOKEN`, `--set-smtp-password` for `SMTP_PASSWORD` and `--set-webhook-url` for `WEBHOOK_URL` because all three commands keep input hidden. GitHub token setup validates the secret before saving it, and SMTP password setup signs in to the mail server before saving it without sending anything. SMTP password setup reports incomplete mail settings before asking for the password, naming the ones still to set. Store `NTFY_ACCESS_TOKEN` as an environment variable or in a dotenv file. A secret you clear, such as declining the ntfy access token during setup, has its line removed from the dotenv file rather than left behind as an empty value.

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

A forgotten `export` can shadow the dotenv file invisibly, so `--debug` names every secret and the source it resolved from, never the value:

```text
[DEBUG 12:00:00] Secret resolution: name=GITHUB_TOKEN, source=environment, value=set
[DEBUG 12:00:00] Secret resolution: name=SMTP_PASSWORD, source=dotenv file, value=set
```

A secret still holding its `your_...` placeholder counts as unset and is left out, and a run with no secret anywhere says so on one line.

When a `--set-*` command or the setup wizard replaces a secret, it rewrites that one assignment in place and leaves every other line alone. A line you wrote as `export NAME=...` keeps its `export`, so a dotenv file you also source in a shell still exports it. A value you clear has its line removed rather than left empty.

Secret commands finish writing the replacement before changing the existing dotenv file. A failed write leaves the original contents intact. On POSIX systems the replacement is readable and writable only by its owner. Existing dotenv symlinks continue to point to the updated file.

## TLS Verification

The tool verifies the TLS certificate of every server it contacts: the GitHub API, the GitHub web pages it reads, the connectivity check endpoint, the mail server that delivers email alerts and, when enabled, the webhook service.

Set `VERIFY_SSL` to `False` only on a network that intercepts TLS with its own certificate authority, such as a corporate proxy. With verification off, an intercepted connection cannot be told apart from the real service.

The startup summary shows `TLS verification` and [`--doctor`](troubleshooting.md#doctor-preflight) reports a warning while it is off.

## Check Intervals

If you want to customize the polling interval, use the `-c` flag (or the `GITHUB_CHECK_INTERVAL` configuration option):

```sh
github_monitor <github_target> -c 900
```

It is generally not recommended to use values lower than 10 minutes as new events are very often delayed by the GitHub API.

`NET_MAX_RETRIES` defaults to 5 and counts the first request as an attempt. `NET_BASE_BACKOFF_SEC` sets the base retry delay and defaults to 5 seconds. GitHub rate-limit headers can specify a different wait. If a monitored feed remains unavailable after its attempts, its previous snapshot is kept and monitoring tries again on the next check.

An interval below 30 seconds invites the GitHub rate limiter, which stops the tool seeing anything. `--doctor` warns when the configured interval is that short.


### Reloading secrets and backup contents

On systems with SIGHUP, reloading applies changes from the selected dotenv file. Removing a file-owned
assignment restores its independently configured fallback or clears the value when no fallback exists.
A read or parsing failure keeps the last usable credentials and reports how to correct the file.
An explicit reload can override a startup export with a value present in the file.


Setup's configuration backup blanks inline secret assignments from older configurations while retaining
other settings and comments. General `--generate-config` backups remain exact copies and can contain
inline credentials. The dotenv file is not backed up during secret replacement.
