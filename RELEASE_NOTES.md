# github_monitor release notes

This is a high-level summary of the most important changes. 

# Changes in 1.0 (11 May 2024)

**Features and Improvements**:

- Possbility to define GITHUB_TOKEN via command line argument (**-t** / **--github_token**)"
- Possibility to limit the type of events to monitor via **EVENTS_TO_MONITOR** variable (if you use 'ALL' then all events are monitored)
- Showing the latest event for the user after the tool is started
- Added support for detecting changes in user's blog URL
- Added support for detecting account changes
- Email sending function send_email() has been rewritten to detect invalid SMTP settings
- Strings have been converted to f-strings for better code visibility
- Info about CSV file name in the start screen
- In case of getting an exception in main loop we will send the error email notification only once (until the issue is resolved)

**Bugfixes**:

- Fixed the crash of the tool if the user have not generated any events yet (for example new accounts)
- Fixed the issue of duplicated events showing up as it turned out event IDs are not always returned as increasing sequentially (we assumed earlier that new event ID value is always greater than the old one)

