"""Contract tests for governance documents, issue templates, workflows and repository metadata."""

import re
from pathlib import Path

import pytest

import github_monitor as gm

yaml = pytest.importorskip("yaml")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIRECTORY = PROJECT_ROOT / ".github" / "workflows"
DOCS_DIRECTORY = PROJECT_ROOT / "docs"
REPOSITORY_URL = "https://github.com/misiektoja/github_monitor"

# The published page set. Splitting the README moved every section onto exactly one of these, so the list is pinned here
DOCUMENTATION_PAGES = ("index.md", "installation.md", "setup-and-first-run.md", "configuration.md", "usage.md", "troubleshooting.md", "testing.md", "about.md")


# Every markdown file that links into the repository, and which a moved or renamed section can silently break
REPOSITORY_MARKDOWN = ("README.md", "SUPPORT.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "THIRD_PARTY_NOTICES.md", ".github/pull_request_template.md")

# The issue templates link out of YAML rather than markdown, which is where a stale README anchor survives longest
ISSUE_TEMPLATES = (".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/bug_report.yml", ".github/ISSUE_TEMPLATE/feature_request.yml")


# Returns the anchors one markdown file defines, from its headings and from any explicit anchor tags
def page_anchors(path):
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', text))
    in_fence = False
    for line in text.splitlines():
        # A commented shell command inside a fence starts with '#' too, and would otherwise register as a real anchor
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith("#"):
            title = line.lstrip("#").strip()
            anchors.add("".join(character for character in title.casefold().replace(" ", "-") if character.isalnum() or character in "-_"))
    return anchors


# Returns the local link targets one repository file names, reading a link to the project page as a README anchor
def repository_link_targets(text):
    targets = re.findall(r"\]\((?!https?:|mailto:)([^)]+)\)", text)
    return list(targets) + [f"README.md#{anchor}" for anchor in re.findall(rf"{re.escape(REPOSITORY_URL)}/?#([^\s)\"']+)", text)]


# Reads one repository file as text
def read_asset(relative_path):
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


# Reads one repository file as parsed YAML
def read_yaml_asset(relative_path):
    return yaml.safe_load(read_asset(relative_path))


class TestGovernanceDocuments:
    # Contributors are pointed to these documents from the README and templates, so a missing one is a broken promise
    def test_governance_documents_exist(self):
        for relative_path in ("SECURITY.md", "SUPPORT.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "THIRD_PARTY_NOTICES.md", "LICENSE", ".github/pull_request_template.md"):
            asset = PROJECT_ROOT / relative_path
            assert asset.is_file(), relative_path
            assert asset.stat().st_size > 200, relative_path

    # A CODEOWNERS entry is what actually requests review on every change
    def test_codeowners_covers_every_path(self):
        assert re.search(r"^\*\s+@\S+", read_asset(".github/CODEOWNERS"), re.M)

    # The policy must name the private reporting route, or reporters fall back to a public issue
    def test_security_policy_routes_reports_privately(self):
        policy = read_asset("SECURITY.md")
        assert "security/advisories/new" in policy
        assert "Do not open a public issue" in policy

    # Contributors need the setup, the checks and the branch to target
    def test_contributing_covers_setup_and_expectations(self):
        contributing = read_asset("CONTRIBUTING.md")
        for concept in ("pip install -e", "python -m pytest", "ruff check", "RELEASE_NOTES.md", "SECURITY.md", "GPL-3.0-or-later", "dev"):
            assert concept in contributing, concept

    # Every declared runtime dependency must carry a license attribution
    def test_third_party_notices_list_every_runtime_dependency(self):
        notices = read_asset("THIRD_PARTY_NOTICES.md").casefold()
        declared = re.search(r"^dependencies = \[(.*?)^\]", read_asset("pyproject.toml"), re.S | re.M)
        assert declared is not None
        for requirement in re.findall(r'"([A-Za-z0-9_.-]+)', declared.group(1)):
            assert requirement.casefold() in notices, requirement

    # Manual and packaged installs need the same runtime libraries, so both dependency lists must agree
    def test_runtime_dependency_declarations_agree(self):
        declared = re.search(r"^dependencies = \[(.*?)^\]", read_asset("pyproject.toml"), re.S | re.M)
        assert declared is not None
        packaged = {name.casefold().replace("_", "-") for name in re.findall(r'"([A-Za-z0-9_.-]+)', declared.group(1))}
        manual = {match.group(0).casefold().replace("_", "-") for line in read_asset("requirements.txt").splitlines() if line.strip() and not line.lstrip().startswith("#") if (match := re.match(r"[A-Za-z0-9_.-]+", line))}
        assert manual == packaged

    # A renamed README section leaves dead links behind in documents no site link test ever opens
    def test_no_repository_document_links_at_a_missing_local_target(self):
        broken = []
        for relative_path in REPOSITORY_MARKDOWN + ISSUE_TEMPLATES:
            path = PROJECT_ROOT / relative_path
            if not path.exists():
                continue
            for target in repository_link_targets(path.read_text(encoding="utf-8")):
                page_part, _, anchor = target.partition("#")
                target_page = path if not page_part else (PROJECT_ROOT / page_part)
                if page_part and not target_page.exists():
                    broken.append(f"{relative_path} -> {target}")
                    continue
                if anchor and anchor not in page_anchors(target_page):
                    broken.append(f"{relative_path} -> {target}")

        assert not broken, f"repository documents linking at missing targets: {broken}"

    # The support document must route each request type to a channel that exists
    def test_support_document_routes_every_request_type(self):
        support = read_asset("SUPPORT.md")
        for destination in (f"{REPOSITORY_URL}/discussions", f"{REPOSITORY_URL}/security/advisories/new"):
            assert destination in support, destination

    # A guide that lists the test files goes stale the moment one is added and nothing else notices
    def test_the_test_suite_guide_lists_every_test_file(self):
        listed = set(re.findall(r"^\| `([^`]+)` \|", (PROJECT_ROOT / "tests" / "README.md").read_text(encoding="utf-8"), re.M))
        present = {path.name for path in (PROJECT_ROOT / "tests").glob("test_*.py")} | {path.name for path in (PROJECT_ROOT / "tests").glob("conftest.py")}

        assert present - listed == set(), f"test files missing from tests/README.md: {sorted(present - listed)}"
        assert {name for name in listed if name.endswith(".py")} - present == set(), f"tests/README.md names files that do not exist: {sorted({name for name in listed if name.endswith('.py')} - present)}"


class TestIssueTemplates:
    # Blank issues bypass the forms, and the contact links are what route vulnerabilities away from public issues
    def test_template_config_disables_blank_issues_and_links_reporting(self):
        config = read_yaml_asset(".github/ISSUE_TEMPLATE/config.yml")
        assert config["blank_issues_enabled"] is False
        urls = [link["url"] for link in config["contact_links"]]
        assert any("security/advisories/new" in url for url in urls)

    # A malformed form is silently ignored by GitHub, so every template must parse and declare its required parts
    def test_every_issue_template_is_well_formed(self):
        templates = sorted((PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml"))
        assert [path.name for path in templates] == ["bug_report.yml", "config.yml", "feature_request.yml"]
        for path in templates:
            if path.name == "config.yml":
                continue
            form = yaml.safe_load(path.read_text(encoding="utf-8"))
            assert form["name"] and form["description"]
            assert any(field.get("validations", {}).get("required") for field in form["body"]), path.name

    # The bug form is where a user is most likely to paste a secret, so it must warn first
    def test_bug_report_warns_before_collecting_output(self):
        bug_report = read_asset(".github/ISSUE_TEMPLATE/bug_report.yml")
        assert "SECURITY.md" in bug_report
        assert "Never paste" in bug_report
        assert "Recovery code" in bug_report
        assert "--debug" in bug_report


class TestWorkflowSupplyChain:
    # Every third-party action is pinned to a commit, so a moved tag cannot change what runs with our secrets
    def test_actions_are_pinned_to_commit_shas(self):
        unpinned = []
        for workflow in sorted(WORKFLOW_DIRECTORY.glob("*.yml")):
            for match in re.finditer(r"uses:\s*(\S+)", workflow.read_text(encoding="utf-8")):
                reference = match.group(1)
                if reference.startswith("./"):
                    continue
                _action, _, ref = reference.partition("@")
                if not re.fullmatch(r"[0-9a-f]{40}", ref):
                    unpinned.append(f"{workflow.name}: {reference}")
        assert unpinned == []

    # Each pin records the human-readable version so updates stay reviewable
    def test_pinned_actions_carry_a_version_comment(self):
        missing = []
        for workflow in sorted(WORKFLOW_DIRECTORY.glob("*.yml")):
            for line in workflow.read_text(encoding="utf-8").splitlines():
                if "uses:" in line and "@" in line and "./" not in line and not re.search(r"#\s*v?\d", line):
                    missing.append(f"{workflow.name}: {line.strip()}")
        assert missing == []

    # Event and input values never reach a shell directly, which would allow script injection
    def test_run_steps_do_not_interpolate_event_values(self):
        offenders = []
        for workflow in sorted(WORKFLOW_DIRECTORY.glob("*.yml")):
            for block in re.findall(r"run: \|(.*?)(?=\n      [-a-zA-Z]|\Z)", workflow.read_text(encoding="utf-8"), re.S):
                for line in block.splitlines():
                    if "${{" in line:
                        offenders.append(f"{workflow.name}: {line.strip()}")
        assert offenders == []

    # Publishing must run the suite first, or a broken build reaches PyPI under the project's name
    def test_pypi_publish_depends_on_the_test_suite(self):
        publish = read_yaml_asset(".github/workflows/publish.yml")
        assert publish["jobs"]["test"]["uses"] == "./.github/workflows/tests.yml"
        assert "test" in publish["jobs"]["build-n-publish"]["needs"]

    # The scanning workflows are the automated half of the security posture the policy describes
    def test_security_workflows_cover_code_and_supply_chain(self):
        for workflow_name in ("codeql.yml", "scorecard.yml", "supply-chain.yml", "tests.yml"):
            assert (WORKFLOW_DIRECTORY / workflow_name).is_file(), workflow_name

        codeql = read_yaml_asset(".github/workflows/codeql.yml")
        assert any("python" in str(job).casefold() for job in codeql["jobs"].values())

        supply_chain = read_yaml_asset(".github/workflows/supply-chain.yml")
        assert {"gitleaks", "pip-audit", "sbom"} <= set(supply_chain["jobs"])

    # The suite is worthless if CI never runs it, so the workflow must invoke pytest and the linter
    def test_ci_runs_the_suite_and_the_linter(self):
        workflow = read_yaml_asset(".github/workflows/tests.yml")
        steps = [step for job in workflow["jobs"].values() for step in job["steps"]]
        assert any("pytest" in step.get("run", "") for step in steps)
        assert any("ruff check" in step.get("run", "") for step in steps)

    # Dependabot must watch every ecosystem this repository actually declares
    def test_dependabot_watches_actions_and_python_dependencies(self):
        updates = read_yaml_asset(".github/dependabot.yml")["updates"]
        assert {"github-actions", "pip"} <= {entry["package-ecosystem"] for entry in updates}


# Returns the page slugs the MkDocs navigation lists, in navigation order
def navigation_pages():
    navigation = read_asset("mkdocs.yml").split("nav:", 1)[1]
    return re.findall(r":\s*([a-z0-9-]+\.md)\s*$", navigation, flags=re.MULTILINE)


# Returns the headings of one documentation page as (level, title) pairs, ignoring fenced code
def page_headings(path):
    headings = []
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and (match := re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)):
            headings.append((len(match.group(1)), match.group(2)))
    return headings


# Resolves one published site URL to the documentation page that has to serve it
def documentation_page_for(url):
    suffix = url.removeprefix(gm.DOCUMENTATION_URL).lstrip("/")
    relative_path, _separator, anchor = suffix.partition("#")
    slug = relative_path.strip("/")
    return (DOCS_DIRECTORY / "index.md" if not slug else DOCS_DIRECTORY / f"{slug}.md"), anchor


class TestDocumentationSite:
    # A page missing from the navigation is unreachable, and a navigation entry without a page fails only at build time
    def test_the_navigation_and_the_page_set_agree(self):
        listed = navigation_pages()
        on_disk = sorted(path.name for path in DOCS_DIRECTORY.glob("*.md"))

        assert listed, "the navigation lists no pages"
        assert sorted(listed) == sorted(DOCUMENTATION_PAGES), f"the navigation no longer matches the pinned page set: {listed}"
        assert on_disk == sorted(DOCUMENTATION_PAGES), f"the published pages no longer match the pinned page set: {on_disk}"

    # Splitting a README can leave a page with two titles, which no build step and no link test notices
    def test_every_page_has_exactly_one_title(self):
        for name in DOCUMENTATION_PAGES:
            titles = [title for level, title in page_headings(DOCS_DIRECTORY / name) if level == 1]
            assert len(titles) == 1, f"{name} has {len(titles)} top-level titles: {titles}"

    # The same section landing on two pages splits the reader's answer in half and both copies then drift
    def test_no_section_appears_on_two_pages(self):
        seen = {}
        duplicated = []
        for name in DOCUMENTATION_PAGES:
            for level, title in page_headings(DOCS_DIRECTORY / name):
                if level != 2:
                    continue
                if title in seen:
                    duplicated.append(f"{title!r} on {seen[title]} and {name}")
                seen[title] = name

        assert not duplicated, f"sections published on two pages: {duplicated}"

    # A cross-page reference written while the section was still in one README is the migration's most likely leftover
    def test_every_documentation_link_resolves(self):
        broken = []
        for name in DOCUMENTATION_PAGES:
            page = DOCS_DIRECTORY / name
            for target in re.findall(r"\]\((?!https?:|mailto:)([^)]+)\)", page.read_text(encoding="utf-8")):
                page_part, _, anchor = target.partition("#")
                target_page = page if not page_part else (DOCS_DIRECTORY / page_part)
                if page_part and not target_page.is_file():
                    broken.append(f"{name} -> {target}")
                    continue
                if anchor and anchor not in page_anchors(target_page):
                    broken.append(f"{name} -> {target}")

        assert not broken, f"documentation pages linking at missing targets: {broken}"

    # The Guide: lines are the only documentation a stuck user is handed, and a renamed section breaks them in silence
    def test_runtime_guide_urls_resolve_to_a_real_page_and_anchor(self):
        guide_names = sorted(name for name in vars(gm) if name.endswith("_GUIDE_URL"))
        assert guide_names, "no runtime guide constants were found"

        for name in guide_names:
            url = getattr(gm, name)
            assert url.startswith(gm.DOCUMENTATION_URL + "/"), f"{name} does not point at the documentation site: {url}"
            page, anchor = documentation_page_for(url)
            assert page.is_file(), f"{name} points at a missing page: {page.name}"
            if anchor:
                assert anchor in page_anchors(page), f"{name} points at a missing anchor on {page.name}: #{anchor}"

    # The runtime links and the published site have to name the same origin, or every Guide: line lands off-site
    def test_the_site_url_matches_the_runtime_documentation_url(self):
        assert f"site_url: {gm.DOCUMENTATION_URL}/" in read_asset("mkdocs.yml")

    # Asserting the job name passes on a workflow whose build step was renamed or removed, so the run: lines are what count
    def test_the_documentation_build_is_a_ci_gate(self):
        commands = re.findall(r"^\s*run:\s*(.+)$", read_asset(".github/workflows/tests.yml"), flags=re.MULTILINE)
        assert any("mkdocs build --strict" in command for command in commands), "CI does not build the documentation site"
        assert any("docs/requirements.txt" in command for command in commands), "CI does not install the documentation dependencies"

    # A site nothing deploys is a site the runtime guide links point at and nobody can read
    def test_the_site_publishes_through_a_workflow(self):
        commands = re.findall(r"^\s*run:\s*(.+)$", read_asset(".github/workflows/docs.yml"), flags=re.MULTILINE)
        assert any("mkdocs gh-deploy" in command and "--strict" in command for command in commands), "no workflow deploys the documentation site"
