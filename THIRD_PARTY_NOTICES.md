# Third-party notices

github_monitor original code is licensed under GPL-3.0-or-later. See [LICENSE](LICENSE).

The distributed package contains no vendored third-party source. It declares the dependencies below, which are installed from PyPI under their own licenses and remain the property of their authors.

## Runtime dependencies

| Component | License | Use |
| --- | --- | --- |
| [PyGithub](https://pypi.org/project/PyGithub/) | LGPL-3.0 | GitHub REST API client for profile, repository and event retrieval |
| [requests](https://pypi.org/project/requests/) | Apache-2.0 | HTTP for the monitored service, notifications and artwork |
| [urllib3](https://pypi.org/project/urllib3/) | MIT | Network exception handling shared with Requests and PyGithub |
| [python-dateutil](https://pypi.org/project/python-dateutil/) | Apache-2.0 or BSD-3-Clause | Timestamp parsing and relative date arithmetic |
| [pytz](https://pypi.org/project/pytz/) | MIT | Timezone conversion for displayed and logged times |
| [tzlocal](https://pypi.org/project/tzlocal/) | MIT | Local timezone detection |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | BSD-3-Clause | Reading secrets from `.env` |

## Build, test and lint dependencies

These are not part of the distributed package.

| Component | License | Use |
| --- | --- | --- |
| [pytest](https://pypi.org/project/pytest/) | MIT | Test suite |
| [PyYAML](https://pypi.org/project/PyYAML/) | MIT | Validating workflows and issue templates in the test suite |
| [Ruff](https://pypi.org/project/ruff/) | MIT | Linting the module and the test suite |
| [pip-audit](https://pypi.org/project/pip-audit/) | Apache-2.0 | Dependency vulnerability audit in the supply chain workflow |
| [CycloneDX](https://pypi.org/project/cyclonedx-bom/) | Apache-2.0 | Software bill of materials in the supply chain workflow |
| [setuptools](https://pypi.org/project/setuptools/), [wheel](https://pypi.org/project/wheel/) | MIT | Package build |

## External services

The tool contacts GitHub. Optional notification delivery contacts the SMTP server or webhook endpoint you configure. Nothing is sent anywhere you have not configured.

## Reporting a licensing problem

If you believe a dependency is misattributed here, open an issue or email <misiektoja-github@rm-rf.ninja>.
