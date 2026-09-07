# github_monitor release notes

This is a high-level summary of the most important changes.

# Changes in 2.7 (TBD)

Version **2.7** focuses on making GitHub Monitor easier to set up, safer to configure and easier to recover when something goes wrong. It adds **guided setup**, a **`--set-smtp-password`** command, a read-only **Doctor preflight check**, verbose and debug diagnostics modes. New diagnostics explain failures and recovery steps. It also parses configuration files as data, guards config replacement and blocks webhook redirects. Daily contribution alerts are more reliable and release downloads can be verified. It also adds clearer security and support guidance and moves the full documentation to a published site.

**Features and improvements**:

- **NEW:** **Coloured terminal output and ASCII startup banner** - `COLORED_OUTPUT`, `COLOR_THEME` and `--no-color` add one shared theme across monitoring events, setup, Doctor, recovery guidance, listing and one-shot commands. Logins and display names are `bright_cyan underline`, identifiers such as event, review and commit IDs are `bright_magenta` and URLs are `blue underline`, so a name is never mistaken for a link, and the same three colours mean the same three things in every monitor in this family. `COLOR_THEME` ships commented out in generated configuration files, so the built-in defaults apply until you uncomment it. Startup, setup, welcome and Doctor screens now use a boxed GitHub ASCII banner with a standard FIGlet wordmark. The GitHub wordmark, Monitor line and version share one body column. The Setup Wizard heading uses the same header colour as the sibling monitors. Colours switch off for redirected output, piped stdin, `NO_COLOR` and unsupported terminals, and argparse is stopped from adding a palette of its own, so on Python 3.14 `--no-color` leaves the `--help` screen plain as well. Log files remain plain. `TRUNCATE_CHARS` and `--truncate` measure visible text before colour is applied. Wide Unicode characters are measured correctly when the optional `wcwidth` package is installed, otherwise each character counts as one column. The terminal sanitizer now preserves SGR style sequences while still removing cursor movement, screen clearing, title changes and other terminal controls
- **NEW:** **Guided setup and a useful first screen** - `--setup` clears an interactive terminal before showing the startup banner, matching the sibling monitors when `CLEAR_SCREEN` is enabled. It collects the GitHub target, whether to persist it, a polling duration, authentication, notifications and output settings. Duration prompts accept seconds or `s`, `m`, `h` and `d` units and show both seconds and a readable default. Setup retains the existing automatic timezone setting without asking for it. It links to GitHub's token page then validates hidden token input. Every answer setup cannot use offers a way out, so a value you cannot produce right now no longer costs you the answers already given: a blank answer asks whether to continue without it and names what stops working, a rejected one offers another attempt and declining a webhook destination leaves that channel and its alerts off. The rebuilt file starts from the settings already in place with your answers applied over them, so **a declined section is cleared rather than carried over** and a rerun that declines email leaves no mail server behind. A CSV path answered without an extension is saved with `.csv` added. **The mail server is signed in to before setup saves it**, so a wrong password or an unreachable host is reported during setup instead of at the first alert, and no email is sent. A refused sign-in offers the mail server questions again and giving up switches email alerts off, while an unreachable server keeps the answers for `--doctor` to check later. The questions show the values already saved as defaults and end with the hidden password prompt, where a blank answer keeps the stored password. The SMTP port question now refuses a number outside 1 through 65535, so setup can no longer save a port `--doctor` would then reject. Declining the retry offer at a number question keeps the value already saved instead of asking the same question again. A question that needs an answer now says `This value is required.` and asks again instead of accepting a blank. The hints under a question now print plain rather than as warnings, matching the sibling monitors. Email and webhook alerts are chosen from a short menu - status and errors, every supported alert, or a custom choice per type - and alerts the current tracking settings cannot produce are left off. A saved webhook URL or ntfy token can be kept, replaced or, for the token, switched off, without ever being displayed. **Both destinations are checked before the first question**, so an unwritable path or a directory given by mistake is reported straight away instead of after you have answered everything, and **a configuration file already in place is replaced only after you agree**, with the option to write somewhere else instead. Nothing is written until you choose **Save settings**. Review actions, section choices, retry guidance and saved-file labels use the same wording and block structure as the sibling monitors. The summary lists the selected email and webhook alert categories and names the webhook provider. `--set-github-token` and `--set-webhook-url` end with the same labelled next-step commands the wizard prints. A final review lets you edit one section, return without changing answers or discard all changes. The summary's **File destinations** section changes where the configuration and dotenv files are written. Moving the dotenv file asks the sections holding secrets again, since a secret you chose to keep was never going to reach the new file. Both files are replaced atomically and an existing configuration file is backed up first, while **the dotenv file is replaced without a backup**, so the credential you replaced is not left behind in a `.bak` file. A saved target lets monitoring and Doctor run without a positional target while an explicit target still wins. The dotenv file is written only when a secret was entered, so a run that stores none leaves no empty file beside the config and the commands it prints name the config alone. The final screen offers Doctor whenever a target was given, so a setup that still has no token can see what is missing, then offers monitoring, both with default-yes prompts when the saved setup is ready. **Ctrl+C is answered by the question, not by the shared signal handler**: before the save it reports `Setup cancelled. Destination files were not changed.` and at the `Run doctor now?` and `Start monitoring now?` questions that follow it says the setup is saved and prints the next-step commands. Running the tool with no arguments shows the shared first screen only when no target is saved. It prints short portable commands with `manual` or `pip` install labels. Non-interactive setup points to the manual `--generate-config` workflow. After saving, setup offers `--doctor` whenever a target was given and offers to start monitoring only after that run passed. The review menu uses the same section labels as the sibling monitors and a switched-off destination such as `--config-file none` is refused with the same message they print.
- **NEW:** **Read-only Doctor setup checks** - `--doctor` checks the environment, configuration, connectivity, GitHub credentials, target, monitoring feeds and notification channels. It opens with the detected install method, reports the Python version with the minimum the tool supports, names the active configuration and dotenv files plus each secret's source without revealing values, reports the local time zone including whether an `Auto` setting can be detected, and names the log and CSV files monitoring would write with whether each one can be created. **Settings that control timing and counts are checked for usable values**. Every one that is wrong is named in a single row, so a negative interval or an out-of-range port is caught before the run rather than during it. **A check interval short enough to invite rate limiting is warned about separately**, since a rate-limited account looks like a broken tool rather than a setting. Each row is colour-coded by status, a link in a row's detail is shown in the link colour and the sections render in the same order as the sibling monitors, with the connectivity endpoint probed before the token. The connectivity row reports whether that endpoint answers at all, the same test monitoring runs at startup, so a temporary error returned by the server does not read as a broken setup. Every `[WARN]` and `[FAIL]` row includes an indented `To fix:` action under its marker, plus a `Guide:` link when a documentation page covers that row specifically, since the report already ends with the link to this one. A `[SKIP]` row names a check that could not run and says why, so a target that could not be looked up without a valid token is `[SKIP]` rather than a failure. The email check signs in to the configured SMTP server without sending anything, and each ready notification row lists the alert categories that channel would deliver. The command writes no files and sends test notifications only after confirmation. It reports the optional `colorama` package only on Windows, since the classic Command Prompt is the only place it changes anything. The report ends with the command that starts monitoring, carrying the same configuration and dotenv files it just checked, so a clean report leads straight into a run
- **NEW:** **A startup summary** - Monitoring mode now opens with the settings that are actually in effect: the target, the polling interval, which email and webhook alerts can fire, where output is going, and the configuration and dotenv files in use. Optional features appear once you switch them on. **`--verbose` or `--debug` prints the complete list** instead, adding the log and CSV files, the GitHub API URL, the monitoring feature switches, the time zone, the install method and which secrets came from the dotenv file, the environment, the configuration file or the command line, by name only. Only secrets that actually hold a value are listed, so a setting left at its placeholder, such as `WEBHOOK_URL = "your_webhook_url"`, is not reported as loaded. **The log file always keeps the complete list**, whichever view the terminal was shown. The rows appear in the same order as in the sibling monitors, so a setting sits in the same place whichever of them you are reading
- **NEW:** **Verbose and debug diagnostics modes** - `--verbose` expands the startup summary, reports notification delivery results and says when an alert channel was switched off because `SMTP_HOST` or `WEBHOOK_URL` is still a placeholder. It also identifies unavailable GitHub lookups so you know which alerts cannot run, reported once when a lookup stops working and again when it works, and a check that reported them closes those lines with the same `Timestamp:` line and separator as every other block, so they are never left floating between blocks. It **stays quiet between events** instead of printing a line per check, which `--debug` records instead. A `--debug` run also leaves the terminal as it was instead of clearing it, so the output you are comparing against stays on screen, while `--verbose` clears it like an ordinary run. `--debug` adds timestamped traces for configuration loading, GitHub requests, connectivity, email, webhooks, files, retries and poll timing. Each trace line **names the operation then lists its details as comma-separated `key=value` fields**, and every outbound call reports `outcome=OK` or `outcome=failed`, matching the sibling monitors. The modes are independent and can also be enabled with `VERBOSE_MODE` and `DEBUG_MODE`. Command-line flags take precedence. Secret values remain redacted and secret-entry prompts suppress debug output
- **NEW:** **Actionable failure recovery** - Errors now include a stable recovery code, a plain-language summary, a `To fix:` action and a `Guide:` link. `--verbose` shows retryability while `--debug` adds the technical cause. Suggested commands match the install method with platform-correct quoting and carry the `--config-file` or `--env-file` you started with, so a suggested retest reads the same settings that failed. `--config-file none` and `--env-file none` are carried too, each except into a command that writes the file it switches off, since `--setup` and the commands that save a secret need somewhere to write. **Monitoring failures are classified the same way**, so a rejected token, a refused request, a rate limit and an unreachable network each get their own summary and fix instead of the raw exception text. An error alert now names what actually failed. **A monitoring failure now reads the same in every monitor in this family**: `* Error: <what failed> (retrying in <time>)`, with the `To fix:` paragraph under it the first time that category appears. **A failure that lasts is reported once, not on every check**: the liveness banner takes over with `* Monitoring degraded for <github_target>` and what is still failing, once per **`LIVENESS_CHECK_INTERVAL`** however often the failing run retries. Once it clears, `* Monitoring recovered for <github_target>` reports how long the outage lasted. With **`LIVENESS_CHECK_INTERVAL`** set to 0 there is no banner to carry the reminder, so the one-line summary keeps printing on every check. **A run that has neither a username nor a token names the missing username first**, since that is the simpler of the two to supply
- **NEW:** **One TLS verification switch** - **`VERIFY_SSL`** controls certificate verification for every outbound connection: the GitHub API, the GitHub web pages the tool reads, the connectivity check, the mail server that sends email alerts and webhook delivery. It defaults to `True`. Set it to `False` only on a network that intercepts TLS with its own certificate authority, such as a corporate proxy. Switching it off is reported rather than silent: the startup summary gains a `TLS verification` row and `--doctor` warns while it is off
- **NEW:** **A published documentation site** - The full documentation now lives at **[misiektoja.github.io/github_monitor](https://misiektoja.github.io/github_monitor/)**, with a separate searchable page for installation, setup and first run, configuration, usage, troubleshooting and testing. The README is now a short landing page that links to it. Every `Guide:` link the tool prints, in error messages, `--doctor` output, the welcome screen and `--help`, opens the matching page instead of a README anchor. Webhook problems now link to the webhook settings rather than the email ones
- **IMPROVE:** **Deleted accounts are flagged in removal alerts** - When a stargazer, watcher, follower or following disappears, the alert now checks whether that GitHub account still exists and appends **`(account no longer exists)`** when it is gone, so a deleted account is not mistaken for someone unstarring or unfollowing. Removed forks get the same note when the fork owner's account is gone and removed starred or public repositories when the repository itself no longer exists. When the existence check fails the item is listed without a note
- **IMPROVE:** **Clearer ntfy customization** - `WEBHOOK_TEMPLATE`, `WEBHOOK_USERNAME` and `WEBHOOK_AVATAR_URL` are documented as Discord-only settings. ntfy uses `WEBHOOK_HEADERS` for options such as `X-Priority` and `X-Tags`
- **IMPROVE:** **Verifiable releases and gated publishing** - Release archives now include `github_monitor_<tag>_SHA256SUMS.txt`, signed build provenance and an attached `.intoto.jsonl` attestation bundle. Verify an archive with `gh attestation verify github_monitor_<tag>.zip --repo misiektoja/github_monitor`. Publishing also checks that the module docstring, runtime version, package metadata and unreleased release-notes heading all declare the same version
- **IMPROVE:** **Minimum dependency versions without known advisories** - The package now requires **`requests` 2.33.0, `urllib3` 2.7.0 and `python-dotenv` 1.2.2** or newer, the first releases of each with no published vulnerability. A fresh `pip install` already gets these versions. An environment that pins an older one needs an upgrade before installing
- **IMPROVE:** **Security, support and contribution guidance** - New security and support policies explain private vulnerability reporting and where to ask questions or report bugs. Guided issue forms, a pull request template, contribution guidance, a code of conduct and a third-party license notice document the project workflow
- **IMPROVE:** **Replace questions and the provider warning read like the sibling monitors** - `--set-github-token` asked `Replace GITHUB_TOKEN in '<path>'?`, naming the dotenv key where `--set-webhook-url` and `--set-smtp-password` name the secret. It now asks `Replace the saved GitHub token in '<path>'?`. The startup warning for a `WEBHOOK_PROVIDER` that disagrees with the destination URL now prints the display name, such as `Discord`, instead of the internal key
- **IMPROVE:** **A clearer `--help` screen** - The argument groups now appear in the order shared with the sibling monitors, with **`Email notifications`** and **`Webhook notifications`** named apart so one group name no longer stands for both. `--setup`, `--doctor`, `--generate-config` and `--set-github-token` sit together under **`Configuration & dotenv files`**. `--config-file` now names the `none` value that switches config discovery off, matching `--env-file`. `--setup` refuses both values, since it needs somewhere to write the files it saves. The examples are grouped by task with a comment above each command saying what it is for. Every command is written for the detected install method. The one-shot commands - `--setup`, `--doctor`, the `--set-*` commands and the `--send-test-*` commands - describe themselves with the same sentence in every monitor, so the same command no longer reads as a different one in each tool
- **IMPROVE:** **Test commands send the same message in every monitor** - **`--send-test-email`** and **`--send-test-webhook`** now use one subject and one body shared by the sibling monitors. The body names the command that sent it, so a test message arriving beside real alerts is easy to place

**Bug fixes**:

- **BUGFIX:** **The liveness banner now follows the clock** - Its cadence was counted in checks derived from **`GITHUB_CHECK_INTERVAL`**, so with a check interval longer than **`LIVENESS_CHECK_INTERVAL`** the banner printed after every check instead of once per interval. The banner and the outage reminder now print once per **`LIVENESS_CHECK_INTERVAL`** of elapsed time. The banner also names what was checked rather than printing a bare timestamp, whether or not **`--verbose`** is on
- **BUGFIX:** **Stable daily contribution counts** - Daily queries now end at the next midnight instead of two days after the requested date. This prevents false increase and decrease alerts caused by inconsistent results for later boundaries
- **BUGFIX:** **Exported secrets work without a dotenv file** - Exported `GITHUB_TOKEN`, `SMTP_PASSWORD`, `WEBHOOK_URL` and `NTFY_ACCESS_TOKEN` values now apply on their own and override values from the dotenv file. Explicit command-line values still take precedence
- **BUGFIX:** **Connectivity and screen settings take effect** - The startup connectivity check now honors `CHECK_INTERNET_URL` and `CHECK_INTERNET_TIMEOUT` from the configuration file. A `--github-url` override applies before the check. `CLEAR_SCREEN` applies after configuration loading so errors remain visible
- **BUGFIX:** **An unset webhook destination switches the channel off** - With `WEBHOOK_ENABLED = True` and a `WEBHOOK_URL` left unset or still holding its `your_webhook_url` placeholder, every alert failed with `WEBHOOK_URL must contain a complete HTTPS link`. Webhook alerts are now switched off at startup instead, and `--verbose` reports why
- **BUGFIX:** **Webhook redirects are refused** - Discord and ntfy deliveries no longer follow redirects. The destination is revalidated at delivery time after a dotenv reload, so alerts and headers cannot be forwarded to an unchecked host
- **NEW:** **`--set-smtp-password` saves the mail server password privately** - Enter `SMTP_PASSWORD` through a hidden prompt instead of editing the dotenv file by hand. The mail server has to accept the password before it is written and no email is sent, so a wrong password, or an app password the provider requires, is reported straight away. A refused sign-in leaves the dotenv file unchanged, and a password already saved there is replaced only after you confirm. The command ends with the same labelled next-step commands the other one-shot commands print.
- **BUGFIX:** **Exported dotenv values are replaced** - `--set-github-token` and `--set-webhook-url` now replace lines such as `export GITHUB_TOKEN="..."` in place while preserving the `export` prefix. The old secret is no longer left in a duplicate assignment
- **BUGFIX:** **Safe config generation** - When `--generate-config` names an existing file it now asks before replacement and creates a timestamped `.bak` backup. Non-interactive use requires `--force`, which creates the same backup. Shell redirection with `>` still overwrites through the shell without prompting or backup
- **BUGFIX:** **Configuration files are parsed as data** - Configuration files no longer execute as Python. Only documented assignments with literal values or references to another setting are accepted. Invalid content names the rejected line and setting without applying part of the file
- **BUGFIX:** **A cancelled secret command says it was cancelled** - Ctrl+C or an `n` at the `Replace ...?` question of `--set-github-token`, `--set-webhook-url` or `--set-smtp-password` was reported as `GitHub token setup could not be completed` followed by `Correct the problem then run: ...`, which described neither outcome. A cancel now says so and names the command that resumes it. A declined replacement says the saved value was left as it is and names the answer that replaces it
- **BUGFIX:** **The screen is cleared only on a real terminal** - Redirecting output to a file, a pipe or a service manager still ran the terminal clear command, which wrote `TERM environment variable not set.` into the captured output. The clear now happens only when a terminal is attached. One-shot commands also keep what is already on the screen: **`--doctor`**, **`--help`**, the `--set-*` commands and the `--send-test-*` commands no longer scroll away the run you wanted to compare against. Monitoring runs and `--setup` still start on a clean screen when `CLEAR_SCREEN` is on.

# Changes in 2.6.3 (04 Aug 2026)

**Bug fixes**:

- **BUGFIX:** Fixed indentation of ASCII log separators in summary screen

# Changes in 2.6.2 (04 Aug 2026)

Version **2.6.2** makes HTML notifications easier to navigate, improves timezone recovery and adds portable log separators.

**Features and improvements**:

- **IMPROVE:** **Clickable GitHub mentions** - Plain `@username` mentions in HTML notifications now link to the user's GitHub profile
- **IMPROVE:** **Clear timezone recovery** - When automatic detection fails, the startup error now identifies the optional `tzlocal` dependency, shows how to install it and explains that `LOCAL_TIMEZONE` can be set manually
- **IMPROVE:** **Portable log separators** - The new `ASCII_LOG_SEPARATORS` setting controls whether separator-only lines saved to log files use ASCII hyphens. `"Auto"` enables them on Windows by default, `"On"` enables them on every operating system and `"Off"` preserves Unicode separators. Terminal separators stay Unicode. Log files and all other logged text remain UTF-8.

# Changes in 2.6.1 (30 Jul 2026)

Version **2.6.1** makes daily contribution monitoring reliable by avoiding incomplete GitHub GraphQL counts from narrow calendar windows.

**Bug fixes**:

- **BUGFIX:** Prevented false daily contribution increase and decrease alerts by fetching a wider contribution calendar window and rejecting responses that omit the requested date

# Changes in 2.6 (30 Jul 2026)

Version **2.6** expands GitHub Monitor with **repository discussion tracking** and independent **Discord, ntfy and custom webhook notifications**. It also makes **secret setup safer**, aligns activity filtering with supported GitHub API events and strengthens release confidence through offline multi-version testing.

**Features and improvements**:

- **NEW:** Added tracking and notifications for **opened and closed discussions** in monitored repositories
- **NEW:** Added **Discord, ntfy and custom webhook notifications** with **per-event controls**, automatic runtime detection for Discord and `ntfy.sh` URLs, secure secret loading, test delivery and advanced payload customization
- **IMPROVE:** Added compact **email and webhook category rollups** to the startup summary with short labels and unstarred continuation lines when needed
- **IMPROVE:** Added a hidden and validated **`--set-github-token` flow** as the preferred credential setup method
- **IMPROVE:** Aligned the configured event list with **event types supported by the GitHub Events API**
- **IMPROVE:** Added an **offline pytest suite** and **multi-version GitHub Actions test workflow**

**Bug fixes**:

- **BUGFIX:** Added detection and notifications when a user **removes the name, company, email, location, bio or blog URL** from their GitHub profile
- **BUGFIX:** Removed trailing whitespace from **clickable issue, pull request and discussion links** in HTML notifications
- **BUGFIX:** Made `SIGHUP` recreate the active GitHub API client after token rotation and redetect Discord or ntfy when the private webhook destination changes

# Changes in 2.5.1 (22 Jul 2026)

**Features and Improvements**:

- **IMPROVE:** Adapted repository monitoring to GitHub's 30 Jun 2026 stargazer and watcher API restrictions
- **IMPROVE:** Continued tracking stargazer and watcher counts for other users while limiting identity-level tracking to the token owner's repositories

**Bug fixes**:

- **BUGFIX:** Prevented restricted stargazer and watcher list endpoints from causing otherwise accessible repositories to be skipped

# Changes in 2.5 (26 May 2026)

**Features and Improvements**:

- **NEW:** Added **clickable commit hashes** to HTML emails
- **IMPROVE:** Enhanced `--generate-config` to support writing directly to a file to avoid UTF-16 encoding issues on Windows PowerShell
- **IMPROVE:** Expanded tabs to spaces in output log files to ensure **consistent alignment across different viewers**

# Changes in 2.4 (13 Dec 2025)

**Features and Improvements**:

- **NEW:** Implemented HTML formatting (with markdown to HTML conversion) for email notifications, enhancing readability and visual presentation
- **NEW:** Added progress bar functionality for repository processing
- **IMPROVE:** Enhanced contribution data retrieval by handling long date ranges more effectively

**Bug fixes**:

- **BUGFIX:** Corrected date calculation for yearly contribution chunks to handle leap years accurately
- **BUGFIX:** Prevented displaying "after" timestamp for older events in GitHub print output
- **BUGFIX:** Added handling for network errors when fetching user data
- **BUGFIX:** Prevented false positives for repository list changes in notifications

# Changes in 2.3 (11 Nov 2025)

**Features and Improvements**:

- **NEW:** Implemented support for selected repository monitoring (see `--repos` flag and `REPOS_TO_MONITOR` config option)
- **NEW:** Added signal handler for daily contributions notifications (`SIGURG`)

**Bug fixes**:

- **BUGFIX:** Corrected daily contributions count by widening GraphQL query window to avoid timezone boundary errors

# Changes in 2.2.1 (14 Oct 2025)

**Bug fixes**:

- **BUGFIX:** Replaced hard coded github.com links with dynamic base URL for GHE compatibility (thanks [@commitSpectral](https://github.com/commitSpectral))

# Changes in 2.2 (13 Oct 2025)

**Features and Improvements**:

- **NEW:** Added daily contributions tracking and notifications (`-m` and `-y` flags)
- **IMPROVE:** Added support to show original repo details for ForkEvent instead of fork target
- **IMPROVE:** Added RateLimitExceededException handling in gh_call with safe sleep logic and header parsing

**Bug fixes**:

- **BUGFIX:** Restored missing PushEvent commits using compare API after GitHub Events API payload change in Aug 25

# Changes in 2.1 (15 Jul 2025)

**Features and Improvements**:

- **NEW:** Added `GET_ALL_REPOS` option and `-a` flag to toggle between all repos and user-owned only (default)
- **NEW:** Added `BLOCKED_REPOS` to toggle alerts for blocked repos (403 TOS, 451 DMCA) in monitoring mode; always shown in listing mode (`-r`)
- **IMPROVE:** Silently handle GitHub 403 (TOS violation) and 451 (DMCA block) repo errors in monitoring mode

# Changes in 2.0 (24 Jun 2025)

**Features and Improvements**:

- **NEW:** Added block status detection identifying when a tracked user has blocked/unblocked the token owner
- **NEW:** Introduced profile visibility detection distinguishing public profiles from private ones

# Changes in 1.9.1 (13 Jun 2025)

**Bug fixes**:

- **BUGFIX:** Fixed config file generation to work reliably on Windows systems

# Changes in 1.9 (22 May 2025)

**Features and Improvements**:

- **NEW:** The tool can now be installed via pip: `pip install github_monitor`
- **NEW:** Added support for external config files, environment-based secrets and dotenv integration with auto-discovery
- **NEW:** Introduced retry-enabled GitHub API call wrapper with fallback on failure
- **NEW:** Display GitHub user profile URL for the token owner and for event actors
- **NEW:** Display truncated GitHub repo description in relevant places
- **IMPROVE:** Increased GitHub event fetch size to 30 and removed fragile timestamp-based filtering
- **IMPROVE:** Enhanced startup summary to show loaded config and dotenv file paths
- **IMPROVE:** Simplified and renamed command-line arguments for improved usability
- **NEW:** Implemented SIGHUP handler for dynamic reload of secrets from dotenv files
- **IMPROVE:** Added configuration option to control clearing the terminal screen at startup
- **IMPROVE:** Changed connectivity check to use GitHub API endpoint for reliability
- **IMPROVE:** Added check for missing pip dependencies with install guidance
- **IMPROVE:** Allow disabling liveness check by setting interval to 0 (default changed to 12h)
- **IMPROVE:** Improved handling of log file creation
- **IMPROVE:** Refactored CSV file initialization and processing
- **IMPROVE:** Added support for `~` path expansion across all file paths
- **IMPROVE:** Refactored code structure to support packaging for PyPI
- **IMPROVE:** Enforced configuration option precedence: code defaults < config file < env vars < CLI flags
- **IMPROVE:** Display monitoring check interval range in output
- **IMPROVE:** Removed short option for `--send-test-email` to avoid ambiguity

**Bug fixes**:

- **BUGFIX:** Fixed account update date saving logic to CSV file

# Changes in 1.8 (08 Apr 2025)

**Features and Improvements**:

- **NEW:** Added monitoring of repository issues and PRs
- **NEW:** Added support for additional GitHub event types (Member, Public, Discussion, Discussion Comment)
- **NEW:** Added logic to fetch parent/previous comments for all new comments (issues, PRs, commits, etc.)
- **NEW:** Detection of forced pushes, tag pushes, branch resets and other ref updates
- **IMPROVE:** Extended event logging with more detailed information
- **IMPROVE:** Enhanced visual output of the repository list with some nice emojis for better readability
- **IMPROVE:** Display event number in event list output
- **IMPROVE:** Refactored and cleaned up code to reduce redundant API requests
- **IMPROVE:** Improved exception and error handling in several places
- **IMPROVE:** Enhanced output formatting for readability

**Bug fixes**:

- **BUGFIX:** Fixed issue where manually defined LOCAL_TIMEZONE wasn't applied during timestamp conversion (fixes [#3](https://github.com/misiektoja/github_monitor/issues/3))

# Changes in 1.7.1 (25 Mar 2025)

**Features and Improvements**:

- **IMPROVE:** Refactored code around event processing to limit API fetch and simplify logic

# Changes in 1.7 (21 Mar 2025)

**Features and Improvements**:

- **NEW:** Added new parameter (-k) to disable monitoring of new Github events for the user
- **NEW:** Added the ability to export GitHub events to a CSV file (when -b is used together with -l)
- **IMPROVE:** Refactored code around event processing to address some corner cases and added awareness of the actual available number of events (as it can be less than EVENTS_NUMBER)
- **IMPROVE:** Email notification flags are now automatically disabled if the SMTP configuration is invalid
- **IMPROVE:** Setting events notifications flag to false when GitHub events are not monitored
- **IMPROVE:** Increased the default check interval to 20 minutes
- **IMPROVE:** Exception handling in a few places
- **IMPROVE:** Code cleanup & linting fixes

# Changes in 1.6 (15 Nov 2024)

**Features and Improvements**:

- **NEW:** Support for Github Enterprise (thanks [@LunaticMuch](https://github.com/LunaticMuch))
- **NEW:** Added new Github API URL parameter (**-x** / **--github_url**) to override the default value defined within the script
- **IMPROVE:** Showing current timestamp when we cannot get last event ID

# Changes in 1.5 (11 Sep 2024)

**Features and Improvements**:

- **IMPROVE:** Saving event date timestamp to CSV file (instead of current ts) as events can be delayed by Github API

**Bug fixes**:

- **BUGFIX:** Better exception handling while processing repos and events
- **BUGFIX:** Fixed wrong representation of repo update date in CSV file

# Changes in 1.4 (05 Aug 2024)

**Features and Improvements**:

- **IMPROVE:** Update date for repo is checked/reported before other repo attributes

**Bug fixes**:

- **BUGFIX:** Better exception handling in few places (some possible crashes fixed)
- **BUGFIX:** Indentation + type casting fixes in the code

# Changes in 1.3 (18 Jun 2024)

**Features and Improvements**:

- **NEW:** Added support for tracking watchers/subscribers changes in public repositories (when **-j** parameter is used)
- **NEW:** Added new parameter (**-z** / **--send_test_email_notification**) which allows to send test email notification to verify SMTP settings defined in the script
- **IMPROVE:** Switched watchers_count to subscribers_count as in fact it corresponds to the number of watchers whereas watchers_count and stargazers_count correspond to the number of users that have starred a repository
- **IMPROVE:** Email notifications for repositories changes (new **-q** parameter) have been separated from regular profile changes notifications (**-p**); also signal handler for SIGCONT has been added to switch repos changes email notifications
- **IMPROVE:** Email notifications for repositories update date changes (new **-u** parameter) have been separated from regular repo changes notifications (**-q**) as they can be quite verbose; also signal handler for SIGPIPE has been added to switch repos update date changes email notifications
- **IMPROVE:** Possibility to define email sending timeout (default set to 15 secs)

**Bug fixes**:

- **BUGFIX:** Fixed "SyntaxError: f-string: unmatched (" issue in older Python versions
- **BUGFIX:** Fixed "SyntaxError: f-string expression part cannot include a backslash" issue in older Python versions
- **BUGFIX:** Missing \t character added when displaying forked repositories

# Changes in 1.2 (27 May 2024)

**Features and Improvements**:

- **NEW:** Feature allowing to track changes of user's public repos like new stargazers, forks, changed description etc.; it is disabled by default, you can enable it via **-j** / **--track_repos_changes** command line argument
- **IMPROVE:** CSV file format changed slightly to accommodate new features
- **IMPROVE:** Rewritten date/time related functions to automatically detect it time object is timestamp (int / float) or datetime
- **IMPROVE:** Info about output log file name in the start screen

# Changes in 1.1 (18 May 2024)

**Features and Improvements**:

- **IMPROVE:** Improvements for running the code in Python under Windows
- **NEW:** Automatic detection of local timezone if you set LOCAL_TIMEZONE variable to 'Auto' (it is default now); requires tzlocal pip module
- **IMPROVE:** Information about time zone is displayed in the start screen now
- **IMPROVE:** Event dates are displayed differently now, it also includes date of the previous event
- **IMPROVE:** Better checking for wrong command line arguments
- **IMPROVE:** pep8 style convention corrections

# Changes in 1.0 (11 May 2024)

**Features and Improvements**:

- **NEW:** Possibility to define GITHUB_TOKEN via command line argument (**-t** / **--github_token**)"
- **NEW:** Possibility to limit the type of events to monitor via **EVENTS_TO_MONITOR** variable (if you use 'ALL' then all events are monitored)
- **NEW:** Showing the latest event for the user after the tool is started
- **NEW:** Added support for detecting changes in user's blog URL
- **NEW:** Added support for detecting account changes
- **IMPROVE:** Email sending function send_email() has been rewritten to detect invalid SMTP settings
- **IMPROVE:** Strings have been converted to f-strings for better code visibility
- **IMPROVE:** Info about CSV file name in the start screen
- **IMPROVE:** In case of getting an exception in main loop we will send the error email notification only once (until the issue is resolved)

**Bug fixes**:

- **BUGFIX:** Fixed the crash of the tool if the user have not generated any events yet (for example new accounts)
- **BUGFIX:** Fixed the issue of duplicated events showing up as it turned out event IDs are not always returned as increasing sequentially (we assumed earlier that new event ID value is always greater than the old one)
