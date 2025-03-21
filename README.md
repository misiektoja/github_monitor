# github_monitor

github_monitor is an OSINT tool that allows for real-time monitoring of GitHub users' activities, including profile and repository changes.

## Features

- Real-time tracking of GitHub users' activities, including profile and repository changes:
   - new GitHub events for the user like new pushes, PRs, issues, forks, releases etc.
   - repository changes such as updated stargazers, watchers, forks, description and repo update dates
   - added/removed followings and followers
   - added/removed starred repositories
   - added/removed public repositories
   - changes in user name, email, location, company, bio, and blog URL
   - detection of account changes
- Email notifications for different events (new GitHub events, changed followings, followers, repositories, user name, email, location, company, bio, blog URL etc.)
- Saving all user activities with timestamps to the CSV file
- Clickable GitHub URLs printed in the console & included in email notifications (repos, PRs, commits, issues, releases etc.)
- Possibility to control the running copy of the script via signals
- Support for Public Web GitHub and GitHub Enterprise

<p align="center">
   <img src="./assets/github_monitor.png" alt="github_monitor_screenshot" width="100%"/>
</p>

## Change Log

Release notes can be found [here](RELEASE_NOTES.md)

## Requirements

The tool requires Python 3.x.

It uses [PyGithub](https://github.com/PyGithub/PyGithub) library, also requires requests, python-dateutil, tzlocal and pytz.

It has been tested successfully on:
- macOS (Ventura, Sonoma & Sequoia)
- Linux:
   - Raspberry Pi OS (Bullseye & Bookworm)
   - Ubuntu 24
   - Rocky Linux (8.x, 9.x)
   - Kali Linux (2024, 2025)
- Windows (10 & 11)

It should work on other versions of macOS, Linux, Unix and Windows as well.

## Installation

Install the required Python packages:

```sh
python3 -m pip install requests python-dateutil pytz tzlocal PyGithub
```

Or from requirements.txt:

```sh
pip3 install -r requirements.txt
```

Copy the *[github_monitor.py](github_monitor.py)* file to the desired location. 

You might want to add executable rights if on Linux/Unix/macOS:

```sh
chmod a+x github_monitor.py
```

## Configuration

Edit the  *[github_monitor.py](github_monitor.py)* file and change any desired configuration variables in the marked **CONFIGURATION SECTION** (all parameters have detailed description in the comments).

### GitHub personal access token

In order to get your GitHub personal access token (classic), go to your GitHub app settings [https://github.com/settings/apps](https://github.com/settings/apps), then click *'Personal access tokens'* -> *'Tokens (classic)'* -> *'Generate new token (classic)'*.

Copy the value of the token to **GITHUB_TOKEN** variable (or use **-t** parameter). 

### GitHub API URL

By default the tool uses Public Web GitHub API URL ([https://api.github.com](https://api.github.com)).

If you want to use GitHub Enterprise API URL then change **GITHUB_API_URL** variable (or use **-x** parameter) to: [https://{your_hostname}/api/v3](https://{your_hostname}/api/v3)


### Events to monitor

You can limit the type of events that will be monitored and reported by the tool. You can do it by changing the **EVENTS_TO_MONITOR** variable.

By default all events are monitored, but if you want to limit it, then remove the *'ALL'* keyword and leave the events you are interested in, for example:

```
EVENTS_TO_MONITOR=['PushEvent','PullRequestEvent', 'IssuesEvent', 'ForkEvent', 'ReleaseEvent']
```

### Timezone

The tool will attempt to automatically detect your local time zone so it can convert GitHub API timestamps to your time. 

If you prefer to specify your time zone manually set the **LOCAL_TIMEZONE** variable from *'Auto'* to a specific location, e.g.

```
LOCAL_TIMEZONE='Europe/Warsaw'
```

In such case it is not needed to install *tzlocal* pip module.

### SMTP settings

If you want to use email notifications functionality you need to change the SMTP settings (host, port, user, password, sender, recipient) in the *[github_monitor.py](github_monitor.py)* file. If you leave the default settings then no notifications will be sent.

You can verify if your SMTP settings are correct by using **-z** parameter (the tool will try to send a test email notification):

```sh
./github_monitor.py -z
```

### Other settings

All other variables can be left at their defaults, but feel free to experiment with it.

## Getting started

### List of supported parameters

To get the list of all supported parameters:

```sh
./github_monitor.py -h
```

or 

```sh
python3 ./github_monitor.py -h
```

### Monitoring mode

To monitor specific user activities and profile changes, simply enter the GitHub username as a parameter (**github_username** in the example below):

```sh
./github_monitor.py github_username
```

It will track all user profile changes (e.g. changed followers, followings, starred repositories, username, email, bio, location, blog URL, number of repositories) and also all GitHub events (e.g. new pushes, PRs, issues, forks, releases etc.).

If you have not changed **GITHUB_TOKEN** variable in the *[github_monitor.py](github_monitor.py)* file, you can use **-t** parameter:

```sh
./github_monitor.py github_username -t "your_github_classic_personal_access_token"
```

If you also want to monitor changes to a user's public repositories (e.g. new stargazers, watchers, forks, changed descriptions etc.) then use the **-j** parameter:

```sh
./github_monitor.py github_username -j
```

If for any reason you do not want to monitor GitHub events for the user (e.g. new pushes, PRs, issues, forks, releases etc.), then use the **-k** parameter:

```sh
./github_monitor.py github_username -k
```

The tool will run indefinitely and monitor the user until the script is interrupted (Ctrl+C) or terminated in another way.

You can monitor multiple GitHub users by running multiple instances of the script.

It is recommended to use something like **tmux** or **screen** to keep the script running after you log out from the server (unless you are running it on your desktop).

The tool automatically saves its output to *github_monitor_{username}.log* file (can be changed in the settings via **GITHUB_LOGFILE** variable or disabled completely with **-d** parameter).

### Listing mode

There is another mode of the tool that displays various requested information (**-r**, **-g**, **-f** and **-l** parameters).

If you want to display a list of public repositories (with some basic statistics) for the user then use the **-r** parameter:

```sh
./github_monitor.py -r github_username
```

<p align="center">
   <img src="./assets/github_list_of_repos.png" alt="github_list_of_repos" width="70%"/>
</p>

If you want to display a list of repositories starred by the user then use the **-g** parameter:

```sh
./github_monitor.py -g github_username
```

If you want to display a list of followers and followings for the user then use the **-f** parameter.

```sh
./github_monitor.py -f github_username
```

If you want to get the list of recent GitHub events for the user then use the **-l** parameter. You can also add the **-n** parameter to specify how many events should be displayed. By default, it shows the last 5 events.

```sh
./github_monitor.py -l github_username -n 10
```

If you want to not only display, but also save the list of recent GitHub events for the user to a CSV file, use the **-l** parameter with **-b** indicating the CSV file. As before, you can add the **-n** parameter to specify how many events should be displayed/saved:

```sh
./github_monitor.py -l github_username -n 10 -b github_username.csv
```

You can use those functionalities in listing mode regardless of whether monitoring is used or not (it does not interfere).

## How to use other features

### Email notifications

If you want to receive email notifications for all user profile changes (e.g. changes in followers, followings, starred repositories, username, email, bio, location, blog URL, and number of repositories), use the **-p** parameter.

```sh
./github_monitor.py github_username -p
```

If you want to receive email notifications when new GitHub events appear for the user (e.g. new pushes, PRs, issues, forks, releases etc.) use the **-s** parameter:

```sh
./github_monitor.py github_username -s
```

If you want to receive email notifications when changes in user repositories are detected (e.g. changes in stargazers, watchers, forks, descriptions, etc., except for the update date) use the **-q** parameter:

```sh
./github_monitor.py github_username -q
```

If you want to receive email notifications whenever changes in the update date of user repositories are detected, use the **-u** parameter (keep in mind these email notifications might be quite verbose):

```sh
./github_monitor.py github_username -u
```

The last two options (**-q** and **-u**) only work if tracking of repositories changes is enabled (**-j**).

You can combine all email notifications parameters together if needed.

Make sure you defined your SMTP settings earlier (see [SMTP settings](#smtp-settings)).

Example email:

<p align="center">
   <img src="./assets/github_monitor_email_notifications.png" alt="github_monitor_email_notifications" width="90%"/>
</p>


### Saving user activities to the CSV file

If you want to save all GitHub user events, profile changes and repository updates in a CSV file, use the **-b** parameter with the name of the file (it will be automatically created if it does not exist):

```sh
./github_monitor.py github_username -b github_username.csv
```

### Check interval

If you want to change the check interval to 15 mins (900 seconds) use **-c** parameter:

```sh
./github_monitor.py github_username -c 900
```

It is generally not recommended to use values lower than 10 minutes as new events are very often delayed by GitHub API.

### Controlling the script via signals (only macOS/Linux/Unix)

The tool has several signal handlers implemented which allow changing the behavior of the tool without needing to restart it with new parameters.

List of supported signals:

| Signal | Description |
| ----------- | ----------- |
| USR1 | Toggle email notifications for all user's profile changes (-p) |
| USR2 | Toggle email notifications for new GitHub events (-s) |
| CONT | Toggle email notifications for user's repositories changes (except for update date) (-q) |
| PIPE | Toggle email notifications for user's repositories update date changes (-u) |
| TRAP | Increase the user check interval (by 1 min) |
| ABRT | Decrease the user check interval (by 1 min) |

So if you want to change the functionality of the running tool, just send the appropriate signal to the desired copy of the script.

I personally use the **pkill** tool. For example, to toggle new email notifications for tool instance monitoring the *github_username* user:

```sh
pkill -f -USR2 "python3 ./github_monitor.py github_username"
```

As Windows supports limited number of signals, this functionality is available only on Linux/Unix/macOS.

### Other

Check other supported parameters using **-h**.

You can combine all the parameters mentioned earlier in monitoring mode (listing mode only supports **-r**, **-g**, **-f**, **-l**, **-n**).

## Coloring log output with GRC

If you use [GRC](https://github.com/garabik/grc) and want to have the tool's log output properly colored you can use the configuration file available [here](grc/conf.monitor_logs)

Change your grc configuration (typically *.grc/grc.conf*) and add this part:

```
# monitoring log file
.*_monitor_.*\.log
conf.monitor_logs
```

Now copy the *conf.monitor_logs* to your *.grc* directory and github_monitor log files should be nicely colored when using *grc* tool.

## License

This project is licensed under the GPLv3 - see the [LICENSE](LICENSE) file for details
