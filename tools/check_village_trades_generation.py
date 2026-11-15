"""Check candidate page persistence and source-derived catalogue tables without publishing."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import generate_village_trades_reference as reference


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--addon-root", type=Path, required=True)
    args = parser.parse_args()
    data = (args.addon_root / "catalog.json").read_bytes()
    catalog = json.loads(data)
    source = reference.ROOT / "pages" / reference.RELATIVE
    template = source.read_text()
    current = reference.render(template, catalog, hashlib.sha256(data).hexdigest())
    assert current == template
    changed = copy.deepcopy(catalog)
    changed["products"][0]["name"] = "Source mutation sentinel"
    changed["products"].pop()
    mutated = reference.render(template, changed, "test")
    assert "Source mutation sentinel" in mutated
    assert f'| Products | {len(changed["products"])} |' in mutated
    assert current != mutated
    try:
        invalid = copy.deepcopy(catalog)
        invalid["products"].append(invalid["products"][0])
        reference.catalogue_section(invalid, "test")
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate catalogue identity accepted")
    for page in ("index", "setup", "survival", "reference"):
        relative = Path(f"addons/village-trades/{page}.md")
        authored = (reference.ROOT / "pages" / relative).read_text()
        assert authored == (reference.ROOT / "docs" / relative).read_text(), relative
        assert "1.0.0-rc.1" in authored and "pending" in authored.lower(), relative
        assert "—" not in authored, relative
        assert str(relative) in (reference.ROOT / "mkdocs.yml").read_text(), relative
        assert str(relative) in (reference.ROOT / "tools/generate_reference_pages.py").read_text(), relative
    setup = (reference.ROOT / "pages/addons/village-trades/setup.md").read_text()
    assert "Never replace a complete MMOItems" in setup
    assert "not disabled merely" in setup
    assert "resource-pack-id" in setup
    subprocess.run([sys.executable, str(reference.ROOT / "tools/generate_village_trades_reference.py"),
                    "--addon-root", str(args.addon_root), "--check"], check=True)
    print("Village Trades candidate page and generation checks passed")


if __name__ == "__main__":
    main()
