"""Keeps the project documents from drifting apart. Rules live in AGENTS.md (CLAUDE.md only imports it), plans in
ROADMAP.md, evidence in BUILD_LOG.md, and the brand guide's tokens and contrast numbers must match theme.css."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["AGENTS.md", "CLAUDE.md", "README.md", "docs/ROADMAP.md", "docs/BUILD_LOG.md", "docs/BRAND.md", "docs/accounts.md", "docs/operations.md"]
STATUSES = {"Done", "In progress", "Planned"}


def read(rel: str) -> str:
    return (ROOT / rel).read_text()


def headings(text: str) -> set[str]:
    return {m.strip().lower() for m in re.findall(r"^#{2,3}\s+(.+)$", text, flags=re.M)}


# ---- CLAUDE.md / AGENTS.md -------------------------------------------------------------------------------

def test_claude_md_imports_agents_md_and_does_not_restate_it():
    claude, agents = read("CLAUDE.md"), read("AGENTS.md")
    assert re.search(r"^@AGENTS\.md\s*$", claude, flags=re.M), "CLAUDE.md must import AGENTS.md with a line '@AGENTS.md'"
    assert headings(claude).isdisjoint(headings(agents)), "CLAUDE.md repeats AGENTS.md headings: move rules to AGENTS.md"
    assert len(claude.splitlines()) < 80, "CLAUDE.md should stay small; rules belong in AGENTS.md"
    assert "CLAUDE.md" in agents and "single source of rules" in agents


def test_agents_md_points_at_the_documents_it_depends_on():
    agents = read("AGENTS.md")
    for rel in ("docs/ROADMAP.md", "docs/BUILD_LOG.md", "docs/BRAND.md", "docs/reference/original-handoff.md"):
        assert rel in agents, f"AGENTS.md should reference {rel}"


# ---- links ---------------------------------------------------------------------------------------------------

def test_relative_links_and_images_resolve():
    bad = []
    for rel in DOCS:
        base = (ROOT / rel).parent
        for target in re.findall(r"!?\[[^\]]*\]\(([^)\s]+)\)", read(rel)):
            if re.match(r"(https?:|mailto:|#)", target):
                continue
            if not (base / target.split("#")[0]).exists():
                bad.append(f"{rel} -> {target}")
    assert not bad, "broken links: " + ", ".join(bad)


# ---- roadmap and build log ---------------------------------------------------------------------------------

def _phases():
    text = read("docs/ROADMAP.md")
    sections = re.split(r"^## Phase (\d+): (.+)$", text, flags=re.M)[1:]
    out = {}
    for i in range(0, len(sections), 3):
        num, name, body = int(sections[i]), sections[i + 1].strip(), sections[i + 2]
        m = re.search(r"\*\*Status:\*\*\s*([A-Za-z ]+?)(?:[.(]|\s{2}|$)", body, flags=re.M)
        out[num] = (name, m.group(1).strip() if m else None)
    return out


def test_every_phase_has_a_valid_status_matching_the_at_a_glance_table():
    phases = _phases()
    assert phases, "no phases found"
    text = read("docs/ROADMAP.md")
    glance = text[text.index("## At a glance"):text.index("## Phase 1:")]  # only that table: other tables also have numbered rows
    table = dict(re.findall(r"^\|\s*(\d+)\s*\|\s*[^|]+\|\s*([^|]+?)\s*\|$", glance, flags=re.M))
    assert {int(k) for k in table} == set(phases), "at-a-glance table and phase sections list different phases"
    for num, (name, status) in phases.items():
        assert status in STATUSES, f"Phase {num} status {status!r} is not one of {sorted(STATUSES)}"
        assert table[str(num)] == status, f"Phase {num}: table says {table[str(num)]!r}, section says {status!r}"


def test_build_log_references_real_phases_and_every_done_phase_has_evidence():
    phases = _phases()
    log = read("docs/BUILD_LOG.md")
    entries = re.findall(r"^### (\d{4}-\d{2}-\d{2}) · (.+?) · (.+?) · (.+)$", log, flags=re.M)
    assert entries, "no build-log entries found"
    mentioned: set[int] = set()
    for _date, _commit, phase_field, _title in entries:
        for a, b in re.findall(r"Phases? (\d+)(?:-(\d+))?", phase_field):
            mentioned |= set(range(int(a), int(b or a) + 1))
        for n in re.findall(r"Phases? \d+(?:[, ]+and[, ]+|, )(\d+)", phase_field):
            mentioned.add(int(n))
    assert mentioned <= set(phases), f"build log mentions unknown phases: {sorted(mentioned - set(phases))}"
    missing = [n for n, (_, s) in phases.items() if s == "Done" and n not in mentioned]
    assert not missing, f"Done phases with no build-log entry: {missing}"


# ---- brand guide vs the real CSS --------------------------------------------------------------------------

def _pairs(block: str) -> dict[str, str]:
    return {k: re.sub(r"\s+", "", v).lower() for k, v in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", block)}


def _css_theme(name: str) -> dict[str, str]:
    css = read("web/src/theme.css")
    m = re.search(r":root\[data-theme='" + name + r"'\]\s*\{(.*?)\}", css, flags=re.S)
    assert m, f"theme {name} not found in theme.css"
    return _pairs(m.group(1))


def _brand_theme(name: str) -> dict[str, str]:
    m = re.search(r"/\* tokens:" + name + r" \*/\n(.*?)```", read("docs/BRAND.md"), flags=re.S)
    assert m, f"BRAND.md has no tokens block for {name}"
    return _pairs(m.group(1))


def test_brand_tokens_match_theme_css():
    derived = {"--on-accent", "--on-primary"}  # computed from other tokens, documented in prose
    for theme in ("fir", "redband", "nightbite"):
        css, brand = _css_theme(theme), _brand_theme(theme)
        for k in derived:
            css.pop(k, None)
        assert css == brand, f"{theme}: BRAND.md tokens differ from theme.css: " + str(
            {k: (css.get(k), brand.get(k)) for k in set(css) | set(brand) if css.get(k) != brand.get(k)})


def _lum(h: str) -> float:
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _ratio(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_brand_contrast_table_matches_the_real_colours():
    brand = read("docs/BRAND.md")
    themes = ("fir", "redband", "nightbite")
    tokens = {t: _css_theme(t) for t in themes}
    tokens["fir"]["--on-primary"] = tokens["fir"]["--text"]
    tokens["redband"]["--on-primary"] = tokens["redband"]["--text"]
    tokens["nightbite"]["--on-primary"] = "#ffffff"
    rows = re.findall(r"^\|\s*`(--[\w-]+)` on `(--[\w-]+)`\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|$", brand, flags=re.M)
    assert len(rows) >= 8, "contrast table not found in BRAND.md"
    for fg, bg, *claimed in rows:
        for theme, said in zip(themes, claimed):
            actual = _ratio(tokens[theme][fg], tokens[theme][bg])
            assert abs(actual - float(said)) < 0.06, f"{fg} on {bg} in {theme}: BRAND.md says {said}, tokens give {actual:.2f}"


# ---- pack list ids vs the gear matcher ------------------------------------------------------------------------

def test_gear_pack_rules_only_name_pack_items_that_exist():
    """The pack list is built in Python and matched to your gear in JavaScript. A renamed or removed item id would
    silently stop matching, so every rule's id must be one the pack list can actually produce."""
    from datetime import date
    from itertools import product

    from app.packlist import pack_list

    js = read("web/src/lib/gearPack.js")
    block = js[js.index("export const RULES = {"):js.index("/** Names of active gear")]
    rule_ids = set(re.findall(r"^\s{2}'?([\w-]+)'?:", block, flags=re.M))
    assert len(rule_ids) >= 10, f"could not read the rule ids: {rule_ids}"
    emitted = set()
    for fishery, kind, temp, precip, wind, month in product(("trout", "steelhead", "warmwater"), (None, "river", "lake"),
                                                           (30, 60, 85, None), (0, 60, None), (5, 20, None), (1, 5, 7, 10)):
        emitted |= {i["id"] for i in pack_list(date(2026, month, 15), fishery, temp, precip, wind, kind)["items"]}
    assert rule_ids <= emitted, f"gear rules for pack items that do not exist: {sorted(rule_ids - emitted)}"


# ---- license ---------------------------------------------------------------------------------------------------

def test_license_is_present_and_declared_consistently():
    text = read("LICENSE")
    assert "GNU GENERAL PUBLIC LICENSE" in text and "Version 3, 29 June 2007" in text
    assert "GPL-3.0" in read("README.md") and "LICENSE" in read("README.md")
    assert 'license = "GPL-3.0-only"' in read("pyproject.toml")
    assert '"license": "GPL-3.0-only"' in read("web/package.json")
    assert "GPL-3.0" in read("AGENTS.md")


# ---- versions --------------------------------------------------------------------------------------------------------
def test_python_and_web_versions_match_and_the_app_reports_it():
    import json
    import re
    py = re.search(r'^version = "([^"]+)"', read("pyproject.toml"), re.M).group(1)
    assert json.loads(read("web/package.json"))["version"] == py
    assert re.fullmatch(r"\d+\.\d+\.\d+", py)
    from app.version import __version__
    assert __version__ in (py, "dev")
