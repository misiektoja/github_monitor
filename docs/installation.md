# Installation

## Requirements

* Python 3.10 or higher
* Libraries: [PyGithub](https://github.com/PyGithub/PyGithub) (2.8 or newer), `requests`, `urllib3`, `python-dateutil`, `pytz`, `tzlocal`, `python-dotenv`
* Optional terminal libraries: `colorama` for classic Windows Command Prompt colours and `wcwidth` for display-width-aware `TRUNCATE_CHARS`

Tested on:

* **macOS**: Tahoe, Sequoia, Sonoma, Ventura
* **Linux**: Raspberry Pi OS (Trixie, Bookworm, Bullseye), Ubuntu 24/25, Rocky Linux 8.x/9.x, Kali Linux 2026/2025/2024
* **Windows**: 11, 10

It should work on other versions of macOS, Linux, Unix and Windows as well.

## Install from PyPI

```sh
pip install github_monitor
```

## Manual Installation

Download the *[github_monitor.py](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/github_monitor.py)* file to the desired location.

Install dependencies via pip:

```sh
pip install PyGithub requests urllib3 python-dateutil pytz tzlocal python-dotenv
```

Alternatively, from the downloaded *[requirements.txt](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/requirements.txt)*:

```sh
pip install -r requirements.txt
```

A manual install is run as `python3 github_monitor.py` instead of `github_monitor`. Every command in this documentation is shown in the PyPI form.

## Upgrading

To upgrade to the latest version when installed from PyPI:

```sh
pip install github_monitor -U
```

If you installed manually, download the newest *[github_monitor.py](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/github_monitor.py)* file to replace your existing installation.
