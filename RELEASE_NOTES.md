# github_monitor release notes

This is a high-level summary of the most important changes. 

# Changes in 1.2 (27 May 2024)

**Features and Improvements**:

- New feature allowing to track changes of user's public repos like new stargazers, forks, changed description etc.; it is disabled by default, you can enable it via **-j** / **--track_repos_changes** command line argument
- CSV file format changed slightly to accommodate new features
- Rewritten date/time related functions to automatically detect it time object is timestamp (int / float) or datetime
- Info about output log file name in the start screen

# Changes in 1.1 (18 May 2024)

**Features and Improvements**:

- Improvements for running the code in Python under Windows
- Automatic detection of local timezone if you set LOCAL_TIMEZONE variable to 'Auto' (it is default now); requires tzlocal pip module
- Information about time zone is displayed in the start screen now
- Event dates are displayed differently now, it also includes date of the previous event
- Better checking for wrong command line arguments
- pep8 style convention corrections

# Changes in 1.0 (11 May 2024)

**Features and Improvements**:

- Possibility to define GITHUB_TOKEN via command line argument (**-t** / **--github_token**)"
- Possibility to limit the type of events to monitor via **EVENTS_TO_MONITOR** variable (if you use 'ALL' then all events are monitored)
- Showing the latest event for the user after the tool is started
- Added support for detecting changes in user's blog URL
- Added support for detecting account changes
- Email sending function send_email() has been rewritten to detect invalid SMTP settings
- Strings have been converted to f-strings for better code visibility
- Info about CSV file name in the start screen
- In case of getting an exception in main loop we will send the error email notification only once (until the issue is resolved)

**Bug fixes**:

- Fixed the crash of the tool if the user have not generated any events yet (for example new accounts)
- Fixed the issue of duplicated events showing up as it turned out event IDs are not always returned as increasing sequentially (we assumed earlier that new event ID value is always greater than the old one)

