# Getting help

Start with the [README](README.md). [Requirements](README.md#requirements), [Installation](README.md#installation) and [Quick Start](README.md#quick-start) cover most first-run problems, and [Configuration](README.md#configuration) explains every setting the tool reads.

## Check your setup first

Confirm which version you are running and that the notification channels actually work, then include the results when you ask:

```sh
github_monitor --version
github_monitor --send-test-email
github_monitor --send-test-webhook
```

Most reports come down to an expired or under-scoped GitHub token, an SMTP server that rejects the message or a webhook URL the provider no longer accepts. The test commands above tell those apart before anything else.

When an error includes a recovery code, include that code in the report. Re-run the failing command with `--debug` when more context is needed. Technical detail is sanitized but you should still review copied output before posting it publicly.

## Where to ask

| You want to | Go to |
| --- | --- |
| Ask a question or discuss an idea | [Discussions](https://github.com/misiektoja/github_monitor/discussions) |
| Report something broken | [Bug report](https://github.com/misiektoja/github_monitor/issues/new?template=bug_report.yml) |
| Request a capability | [Feature request](https://github.com/misiektoja/github_monitor/issues/new?template=feature_request.yml) |
| Report a vulnerability | [Private security advisory](https://github.com/misiektoja/github_monitor/security/advisories/new), never a public issue |
| Contribute a change | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Before you post

Include the version, recovery code, how you installed it (PyPI or manual script), your operating system, the monitored user or repository form you passed and what you expected instead. Attach the relevant part of the monitoring log file, which the tool writes unless you pass `--disable-logging`.

Never post your GitHub personal access token, SMTP passwords, webhook URLs or a complete configuration file. Redact monitored usernames and private repository names if they matter to you.

## What to expect

This is a project maintained in spare time, so replies are best effort with no response time attached. Only the latest release receives fixes, so reproduce the problem on the current version before reporting it.

If the project is useful to you, you can support its development through [GitHub Sponsors](https://github.com/sponsors/misiektoja) or [Buy Me a Coffee](https://buymeacoffee.com/misiektoja).
