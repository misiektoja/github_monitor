# github_monitor release notes

This is a high-level summary of the most important changes.

# Changes in 2.7 (TBD)

Version **2.7** focuses on making GitHub Monitor easier to set up, safer to configure and easier to recover when something goes wrong. It adds **guided setup**, a read-only **Doctor preflight check**, a **`--set-smtp-password`** command for hidden password entry, a **coloured terminal output**  plus verbose and debug diagnostics modes. New diagnostics explain failures and recovery steps. It also parses configuration files as data, guards config replacement and blocks webhook redirects. Daily contribution alerts are more reliable and release downloads can be verified. It also adds clearer security and support guidance and moves the full documentation to a published site.

**Features and improvements**:

- **NEW:** **Guided setup** - `--setup` wizard walks through the target, check interval, credentials, notifications and output files. Review or edit answers before saving, with hidden secret entry and confirmation before replacing settings. Save the target to start future runs without arguments
- **NEW:** **Doctor preflight check** - `--doctor` checks configuration, GitHub access, monitoring feeds, notifications and output destinations before monitoring. Problems include suggested fixes. It writes no files and sends test notifications only after confirmation
- **NEW:** **Coloured terminal output** - Names, IDs, links and errors have distinct colours. Customize them with `COLOR_THEME` or disable them with `--no-color`. Logs remain plain text. Optional `wcwidth` support improves screen truncation for wide Unicode characters
- **NEW:** **Startup summary and diagnostics** - Monitoring opens with the active target, intervals, alerts and output destinations. `--verbose` adds operational updates and delivery results. `--debug` adds technical traces. Secrets stay redacted and logs always retain the full startup summary
- **NEW:** **Private SMTP password setup** - `--set-smtp-password` takes a hidden password and checks it with the mail server before saving. Guided setup also checks email credentials without sending a message
- **IMPROVE:** **Clearer errors and recovery** - Failures explain what to fix and link to the guide. Persistent outages produce periodic reminders instead of repeating full errors, followed by a recovery notice. Liveness messages now follow elapsed time and describe what was checked
- **IMPROVE:** **Deleted accounts and repositories identified** - Removal alerts now distinguish deleted accounts or repositories from unfollows, unstars and other removals when GitHub can confirm that the account or repository no longer exists
- **IMPROVE:** **Updated dependency requirements** - The package now requires `requests >= 2.33.0`, `urllib3 >= 2.7.0` and `python-dotenv >= 1.2.2`. Update older dependency pins before upgrading
- **IMPROVE:** **Documentation and verifiable downloads** - A [searchable guide](https://misiektoja.github.io/github_monitor/) covers installation, setup and troubleshooting. Releases include checksums and signed build attestations. New security and support guidance explains where to report problems

**Bug fixes**:

- **BUGFIX:** **Stable daily contribution alerts** - Corrected daily query boundaries prevent false contribution increase and decrease alerts
- **BUGFIX:** **Safer configuration replacement** - `--generate-config FILE` asks before replacing an existing file and creates a backup. Non-interactive replacement requires `--force`. Shell redirection with `>` still bypasses these protections
- **BUGFIX:** **Safer configuration loading** - Configuration files are read as settings instead of executed as Python. Plain values and references to other settings still work. Files using imports, function calls or calculations must be rewritten as plain settings
- **BUGFIX:** **Reliable secret handling** - Exported secrets work without a dotenv file. Secret commands correctly replace `export` assignments without leaving duplicate credentials. Setup replaces secrets without retaining backup copies
- **BUGFIX:** **Safer network connections** - Webhooks refuse redirects and unconfigured destinations are disabled. `VERIFY_SSL` controls certificate checks for all outbound connections, including email. Verification is enabled by default and disabling it produces a warning
- **BUGFIX:** **Startup settings and captured output** - Startup now respects configured connectivity and screen settings. Redirected output no longer triggers terminal-clearing errors and help, Doctor and secret commands preserve terminal history

Smaller fixes and development changes are listed in the [full change history](https://github.com/misiektoja/github_monitor/compare/v2.6.3...v2.7).

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
