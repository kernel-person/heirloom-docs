#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/generate_reference_pages.py"
PLUGIN_ROOT = Path(os.environ.get("HEIRLOOM_PLUGIN_ROOT", ROOT.parent / "foodplugin")).resolve()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        temp_docs = Path(tmp)
        os.environ["HEIRLOOM_DOCS_ROOT"] = str(temp_docs)
        os.environ["HEIRLOOM_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        spec = importlib.util.spec_from_file_location("heirloom_pasture_generator", GENERATOR)
        assert spec and spec.loader
        generator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = generator
        spec.loader.exec_module(generator)

        mozzarella = next(item for item in generator.ITEMS if item.get("id") == "MOZZARELLA")
        assert mozzarella["_source"] == "Pasture"
        assert mozzarella["_addon"] == "pasture"
        young_wheel = next(recipe for recipe in generator.RECIPES if recipe.get("id") == "AGE_YOUNG_CHEESE")
        assert young_wheel["_source"] == "Pasture"
        assert young_wheel["_station"] == "Aging Rack"

        generator.write_all()
        guide = (temp_docs / "docs/addons/pasture/dairy.md").read_text(encoding="utf-8")
        flowchart = temp_docs / "docs/images/generated/pasture-cheese-flow.svg"
        assert flowchart.exists()
        svg = flowchart.read_text(encoding="utf-8")
        catalog = json.loads((PLUGIN_ROOT / "heirloom-pasture/src/main/resources/cheese-affinities.json")
                             .read_text(encoding="utf-8"))
        for style_id, style in catalog["styles"].items():
            assert style["display_name"] in svg, style_id
            assert f'id="route-{style_id.lower().replace("_", "-")}"' in svg, style_id
        for item_id in ("RICOTTA", "BRUNOST"):
            assert f'id="route-{item_id.lower()}"' in svg, item_id
            assert f'data-item="{item_id}"' in svg, item_id
        for phrase in ("Milk sources", "Fresh Curds", "Treatments", "Salt or brine",
                       "Cold • Temperate • Warm", "Farmhouse Press", "Aging Rack", "Recommended paths", "experimentation"):
            assert phrase in svg, phrase
        assert "milk_scores" not in svg
        assert "treatment_scores" not in svg
        assert "points" not in svg.lower()
        assert "../../images/generated/pasture-cheese-flow.svg" in guide
        for phrase in (
            "Temperate Cow", "Cold Cow", "Warm Cow", "one actionable next step", "three freely mixed milk pails", "Farmhouse Press", "27-slot",
            "every climate", "20 real minutes", "Emmental", "hopper", "starter trades",
            "exact hidden epoch timestamps", "simulated", "⏳Aged: 3 days · (1h)",
            "Pasture Cheeses", "/hlp menu", "/hlp cheese", "18 cheeses", "16 affinity",
            "vanilla milk buckets", "legacy Dairy Milk", "0, 1, 1.5, 2, 3, 4, 5, 6 and 7",
            "Normal ingredients", "successful station completion", "no player mastery",
            "| 10, 19, 28 |", "| 11, 20, 29 |", "| 16 |", "| 34 |",
            "exactly once", "historical", "one Core quality row",
            "Ricotta", "Brunost", "three whey with lemon or vinegar", "three whey with Heavy Cream",
            "no GUI, accessible inventory, or molds", "Minecraft-Heads", "/hlp debug give <item-id> [amount]",
            "Pig Casings", "Garlic Pork Sausage", "Swedish Potato Sausage", "Cheese Sausage",
            "one Dough into two Dry Pasta", "two Cooking Oil", "four-stage temperate Allium",
            "no separate raw-link items", "Plain Links plus Bread", "Garlic Bread",
            "Raw Frog Legs", "French Fried Frog Legs are available only while Heirloom Orchard is installed",
            "outward-only horizontal velocity",
            "Autonomous Animal Care", "nourishment", "water", "rest", "company", "comfort",
            "Gold Nugget", "protected grass grazing", "four active minutes",
            "ten-second status display", "Server work waiting in a queue is never treated as poor care",
            "one-active-minute grace period", "Unloaded or inactive time",
            "**Wild**", "**Click to sell for meat**", "same-species managed witnesses",
            "private husbandry lens", "nearest twenty-four", "within twelve blocks",
            "line of sight to and", "private to its brush-holding player",
            "changes the animal's real passenger list", "Open the main Heirloom hub with `/hl`",
            "looking for a resource", "walking toward it", "actual blocked action",
            "Wishes stay until fulfilled", "Sneak-brush", "known parents", "birth-quality bonus",
            "Milk, meat, leather", "Milk, meat, wool", "Eggs, meat",
            "Ratings range from 0 to 100", "up to ten points", "never rerolled",
            "neutral ratings of 50", "between 35 and 65", "Unknown history adds no bonus",
            "excluded from", "up to three times", "Fractional rewards accumulate",
            "Sale rewards are fixed when quoted", "Horses, dogs, and hatch ancestry",
            "PastureLivestockSaleEvent", "Raw Goat Meat", "Minced Goat", "four coloured squares",
            "/hlp debug charge [true|false]", "/hlp debug press ready",
            "/hlp debug rack inspect", "/hlp debug rack advance <seconds>",
            "/hlp debug husbandry <enroll|inspect|mood> [tier]",
        ):
            assert phrase in guide, phrase
        for obsolete in ("/hlp debug item", "/hlp debug milk", "reusable Wheel", "at-most-once",
                         "four-piece seeded", "zero skylight", "Warm 15 minutes",
                         "deterministic weighted lottery", "three-to-five-minute request delay", "Failed Need",
                         "sixteen non-craftable", "Works in any cheese recipe", "Goat • Sheep • Vanilla"):
            assert obsolete not in guide, obsolete
        nav = (temp_docs / "mkdocs.yml").read_text(encoding="utf-8")
        assert "Overview And Cheese: addons/pasture/dairy.md" in nav
        assert "Animal Care: addons/pasture/animal-care.md" in nav
        care = (temp_docs / "docs/addons/pasture/animal-care.md").read_text(encoding="utf-8")
        for phrase in ("Your first farm", "optional bonuses", "Hover a bar", "Hover a product", "Yield / Quality", "four coloured squares", "First birth", "same material, grade and metadata", "If something looks wrong", "Moss blocks or moss carpet", "within 64 blocks", "do not fall"):
            assert phrase in care, phrase
        for obsolete in ("∅ WILD", "☞ CLICK TO SELL", "☺", "Attention 50%", "Production care uses", "green middle means balanced"):
            assert obsolete not in care, obsolete
        assert "MOZZARELLA" in (temp_docs / "docs/reference/items.md").read_text(encoding="utf-8")
        assert "AGE_YOUNG_CHEESE" in (temp_docs / "docs/recipes/default-recipes.md").read_text(encoding="utf-8")
        recipes = (temp_docs / "docs/recipes/default-recipes.md").read_text(encoding="utf-8")
        assert "#MINCED_MEAT" in recipes
        assert "#SAUSAGE" not in recipes
        assert "#CHEESE" in recipes
        assert "RAW_GOAT_MEAT" in recipes
        assert "MINCED_GOAT" in recipes
        installation = (temp_docs / "docs/getting-started/installation.md").read_text(encoding="utf-8")
        assert "[Pasture](../addons/pasture/dairy.md)" in installation
        assert "plugins/HeirloomPasture/" in installation
        assert "/hlp menu" in installation
        # The generated dependency row must follow the selected release catalog,
        # rather than silently retaining a copied platform/version declaration.
        original_requirements = generator.PASTURE_CATALOG["requirements"]
        try:
            generator.PASTURE_CATALOG["requirements"] = ["Java 99", "Paper 99.2", "Heirloom 99"]
            generator.getting_started_pages()
            changed = generator.PAGES["getting-started/installation.md"]
            assert "Java 99; Paper 99.2; Heirloom 99; matching Core candidate required" in changed
        finally:
            generator.PASTURE_CATALOG["requirements"] = original_requirements
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
