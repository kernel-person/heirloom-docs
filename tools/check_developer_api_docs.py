#!/usr/bin/env python3
"""Verify Developer API documentation pages, navigation sync, and API signature accuracy."""
from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS_ROOT = Path(__file__).resolve().parents[1]
PAGES_DEV = DOCS_ROOT / "pages" / "developer"
DOCS_DEV = DOCS_ROOT / "docs" / "developer"

EXPECTED_FILES = [
    "index.md",
    "items-and-food-facts.md",
    "events.md",
    "addons-and-registration.md",
]

REQUIRED_NAV_LINES = [
    "  - Developer API:",
    "      - Overview & Quickstart: developer/index.md",
    "      - Items & FoodFacts V2: developer/items-and-food-facts.md",
    "      - Bukkit Events: developer/events.md",
    "      - Addons & Registration: developer/addons-and-registration.md",
]

REQUIRED_TERMS = {
    "index.md": [
        "https://heirloom-maven.pages.dev",
        "ke.ric:heirloom-api:2.11.0",
        "https://heirloom-maven.pages.dev/javadoc/",
        "HeirloomAPI.getInstance()",
        "isReady()",
        "compileOnly",
        "<scope>provided</scope>",
    ],
    "items-and-food-facts.md": [
        "createItem(",
        "isCustomItem(",
        "getCustomItemId(",
        "FoodFactsV2",
        "FoodFactsV2.read(",
        "FoodFactsV2.write(",
        "FoodFactsV2.produced(",
        "FoodFactsV2.writeProduced(",
        "heirloom:food_facts_v2",
        "DrinkQuality",
        "DrinkServing",
        "TerminalAlcohol",
        "AlcoholLore",
        "PotionTooltip",
    ],
    "events.md": [
        "HeirloomFoodConsumedEvent",
        "HeirloomPlacedFoodConsumedEvent",
        "HeirloomItemCraftedEvent",
        "HeirloomCropHarvestedEvent",
        "HeirloomAdminItemEvent",
        "CookingStation",
    ],
    "addons-and-registration.md": [
        "registerAddon(",
        "HeirloomAddon",
        "ItemRegistration.builder()",
        "RecipeRegistration.builder()",
        "CropRegistration.builder()",
        "PropertyRegistration.builder()",
        "SeedAcquisitionRegistration",
        "AdvancementDefinition",
        "AgingDefinition.builder()",
        "GuideDefinition",
        "GuideDestination",
    ],
}

FORBIDDEN_PATTERNS = [
    (r"\bHeirloomAPI\.get\(\)", "non-existent HeirloomAPI.get()"),
    (r"\bisAvailable\(\)", "non-existent isAvailable()"),
    (r"\.hasCategory\(", "non-existent FoodFactsV2.hasCategory()"),
    (r"\.hasIngredient\(", "non-existent FoodFactsV2.hasIngredient()"),
    (r"\.hasTag\(", "non-existent FoodFactsV2.hasTag()"),
    (r"\.isTrue\(", "non-existent FoodFactsV2.isTrue()"),
    (r"\.isFalse\(", "non-existent FoodFactsV2.isFalse()"),
    (r"\.fact\(", "non-existent FoodFactsV2.fact()"),
    (r"FoodFactsV2\.FLAGS\b", "package-private/private FoodFactsV2.FLAGS"),
    (r"FoodFactsV2\.PDC_KEY\b", "non-existent FoodFactsV2.PDC_KEY"),
    (r"FoodFactsV2\.fromLegacy\b", "non-existent FoodFactsV2.fromLegacy"),
    (r"AgingCondition\.DARK\b", "non-existent AgingCondition.DARK"),
    (r"DrinkServing\.(?:servingCl|scaleAbvToReference)\b", "non-existent DrinkServing method"),
    (
        r"(?:items|recipes|crops|properties)\(\)\.register\([^;]*?\.build\(\)\s*\)",
        "invalid .build() inside register(...) call for builder-taking facade",
    ),
]


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not PAGES_DEV.is_dir() or not DOCS_DEV.is_dir():
        fail("Expected both pages/developer and docs/developer directories")

    for name in EXPECTED_FILES:
        src = PAGES_DEV / name
        dst = DOCS_DEV / name
        if not src.is_file() or not dst.is_file():
            fail(f"Missing developer API page: {name}")
        src_text = src.read_text(encoding="utf-8")
        dst_text = dst.read_text(encoding="utf-8")
        if src_text != dst_text:
            fail(f"Mismatch between pages/developer/{name} and docs/developer/{name}")
        for term in REQUIRED_TERMS[name]:
            if term not in dst_text:
                fail(f"Missing required term {term!r} in docs/developer/{name}")
        for pattern, label in FORBIDDEN_PATTERNS:
            if re.search(pattern, dst_text, re.DOTALL):
                fail(f"Forbidden {label} matched in docs/developer/{name}")

    mkdocs_text = (DOCS_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    gen_text = (DOCS_ROOT / "tools" / "generate_reference_pages.py").read_text(encoding="utf-8")
    nav_block = "\n".join(REQUIRED_NAV_LINES)
    if nav_block not in mkdocs_text:
        fail("Developer API nav block missing from mkdocs.yml")
    if nav_block not in gen_text:
        fail("Developer API nav block missing from tools/generate_reference_pages.py")

    index_text = (DOCS_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    dev_bullet = "- Plugin developers: [Developer API](developer/index.md), [Items & FoodFacts V2](developer/items-and-food-facts.md), [Bukkit Events](developer/events.md), and [Addons & Registration](developer/addons-and-registration.md)."
    for target_name, text in [("docs/index.md", index_text), ("tools/generate_reference_pages.py", gen_text)]:
        if dev_bullet not in text:
            fail(f"Developer API landing bullet missing from {target_name}")
        if "https://heirloom-maven.pages.dev/" not in text or "https://heirloom-maven.pages.dev/javadoc/" not in text:
            fail(f"Maven/Javadoc landing links missing from {target_name}")

    print("[OK] Developer API docs, nav sync, and API contracts verified")


if __name__ == "__main__":
    main()
