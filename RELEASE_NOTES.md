# github_monitor release notes

This is a high-level summary of the most important changes. 

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
