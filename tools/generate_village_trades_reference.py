"""Refresh only the unpublished Village Trades reference from a verified addon catalogue."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- village-trades-catalog:start -->"
END = "<!-- village-trades-catalog:end -->"
RELATIVE = Path("addons/village-trades/reference.md")
STATIONS = {"SMITHING_ANVIL": "Smithing Anvil", "WOODWORKING_BENCH": "Woodworking Bench",
            "BOILING_POT": "Boiling Pot", "MIXING_BOWL": "Mixing Bowl"}


def catalogue_section(catalog: dict, digest: str) -> str:
    if catalog["id"] != "village_trades" or catalog["status"] != "release-candidate":
        raise ValueError("Use the reviewed Village Trades candidate catalogue")
    products = catalog["products"]
    if len({product["id"] for product in products}) != len(products):
        raise ValueError("Duplicate product identity")
    counts = (("Products", len(products)), ("Public provider references", len(catalog["public_references"])),
              ("Workstation recipes", len(catalog["workstation_recipes"])),
              ("Native forge-blank recipes", len(catalog["blank_recipes"])),
              ("Bootstrap recipes", len(catalog["bootstrap_recipes"])), ("Crops", len(catalog["crops"])),
              ("Deposits", len(catalog["deposits"])), ("Arrow combinations", len(catalog["arrow_combinations"])))
    lines = [START, "", "## Collection", "", "| Definition | Count |", "| --- | ---: |"]
    lines += [f"| {name} | {count} |" for name, count in counts]
    lines += ["", "Workmanship grades are variants of a product. Internal loaded-tongs appearances",
              "and the retained test template are excluded from the public product list.", "",
              "## Products", "", "| Product | Station | Workmanship variants | Family ID |",
              "| --- | --- | ---: | --- |"]
    for product in products:
        name = product["name"].replace("|", "\\|")
        grade_count = len(product.get("grades", {}))
        variants = str(grade_count) if grade_count else "Single"
        lines.append(f'| {name} | {STATIONS[product["station"]]} | {variants} | `{product["id"]}` |')
    lines += ["", f"<!-- Source catalog.json SHA-256: {digest} -->", END]
    return "\n".join(lines)


def render(template: str, catalog: dict, digest: str) -> str:
    if template.count(START) != 1 or template.count(END) != 1:
        raise ValueError("Reference must contain exactly one generated section")
    before, remainder = template.split(START)
    _, after = remainder.split(END)
    return before + catalogue_section(catalog, digest) + after


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--addon-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = (args.addon_root / "catalog.json").read_bytes()
    source = ROOT / "pages" / RELATIVE
    output = render(source.read_text(), json.loads(data), hashlib.sha256(data).hexdigest())
    for path in (source, ROOT / "docs" / RELATIVE):
        if args.check:
            if not path.is_file() or path.read_text() != output:
                raise SystemExit(f"Stale Village Trades reference: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(output)
    print("Village Trades candidate reference verified" if args.check else "Village Trades candidate reference generated")


if __name__ == "__main__":
    main()
