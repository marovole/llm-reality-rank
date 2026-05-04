import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def read_workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_runs_site_tests_and_build():
    text = read_workflow()
    assert "npm --prefix site install" in text or "npm --prefix site ci" in text or "working-directory: site" in text, (
        "CI must install site npm dependencies"
    )
    assert "npm --prefix site test" in text or re.search(r"working-directory: site\s+run: npm test", text), (
        "CI must run site tests (npm --prefix site test)"
    )
    assert "npm --prefix site run check" in text or re.search(r"working-directory: site\s+run: npm run check", text), (
        "CI must run astro check (npm --prefix site run check)"
    )
    assert "npm --prefix site run build" in text or re.search(r"working-directory: site\s+run: npm run build", text), (
        "CI must run site build (npm --prefix site run build)"
    )


def test_workflow_uses_supported_node_version():
    text = read_workflow()
    assert "actions/setup-node@" in text, "CI must use actions/setup-node"
    match = re.search(r"node-version:\s*['\"]?(\d+)", text)
    assert match, "CI must pin a node-version"
    major = int(match.group(1))
    assert major >= 22, f"site/package.json requires Node >=20.3 <21 || >=22; got {major}"
