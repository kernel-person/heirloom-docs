#!/usr/bin/env python3
"""Verify Distillery references follow the same editable catalog as gameplay."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = Path(os.environ.get("HEIRLOOM_PLUGIN_ROOT", ROOT.parent / "foodplugin")).resolve()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["HEIRLOOM_DOCS_ROOT"] = tmp
        os.environ["HEIRLOOM_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        spec = importlib.util.spec_from_file_location("heirloom_distillery_generator", ROOT / "tools/generate_reference_pages.py")
        assert spec and spec.loader
        generator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = generator
        spec.loader.exec_module(generator)
        grape_ids = {"RENOIT_GRAPE", "CHERIMOLA_BLAN_GRAPE", "MELOIRE_GRAPE",
                     "CRANERLET_NUALA_GRAPE", "GRALLADINA_FRAN_GRAPE"}
        grape_items = [item for item in generator.ITEMS if item.get("id") in grape_ids]
        grape_crops = [crop for crop in generator.CROPS if crop.get("id") in grape_ids]
        assert {item["id"] for item in grape_items} == grape_ids, "Distillery-owned grape items missing from wiki discovery"
        assert {crop["id"] for crop in grape_crops} == grape_ids, "Distillery-owned grape crops missing from wiki discovery"
        assert len(grape_items) == len(grape_crops) == 5, "Grape definitions must be indexed once"
        assert all(row["_source"] == "Distillery" and row["_addon"] == "distillery"
                   for row in grape_items + grape_crops), "Grapes must be attributed to Distillery"
        catalog = json.loads((PLUGIN_ROOT / "heirloom-distillery/src/main/resources/beverage-affinities.json").read_text())
        families = generator.distillery_family_reference(catalog)
        styles = generator.distillery_maturation_reference(catalog)
        preparations = generator.distillery_recipe_reference(catalog)
        for recipe in catalog["recipes"]:
            assert recipe["name"] in preparations, recipe["id"]
        assert "Skinned" in preparations and "Roasted" in preparations
        assert "95%" in preparations and "21" in preparations
        assert "3 cool days" in preparations
        for name in ("Irish Red Ale", "Taxi Vodka", "Spirytus Rektyfikowany"):
            assert name in preparations, name
        renamed = copy.deepcopy(catalog)
        renamed["recipes"][0]["name"] = "Custom High Proof"
        assert "Custom High Proof" in generator.distillery_recipe_reference(renamed)
        for family in catalog["families"]:
            assert family["fermented_name"] in families, family["id"]
            assert family["distilled_name"] in families, family["id"]
            for ingredient in family["ingredients"]:
                assert ingredient.replace("_", " ").title() in families, ingredient
        family_by_id = {family["id"]: family for family in catalog["families"]}
        for style in catalog["styles"]:
            for family_id in style["families"]:
                family = family_by_id[family_id]
                base = family["distilled_name"] if style["stage"] == "DISTILLED" else family["fermented_name"]
                name = style["name"].replace("{base}", base) if style["name"] else base
                assert name in styles, (style["id"], family_id)
        assert "Honey Spirit | 3 days (1h) | Temperate / Normal | Neutral" in styles
        assert "Rice Spirit | 3 days (1h) | Cool / Normal | Neutral" in styles
        assert "45 days Oak or Dark Oak, then 15 days Cherry" in styles
        assert "45 days Oak or Dark Oak, then 15 days Acacia" in styles
        assert "360 days (120h)" in styles
        assert "Sparkling Wine" in styles

        changed = copy.deepcopy(catalog)
        changed["minutes_per_day"] = 7
        honey = next(style for style in changed["styles"] if style["id"] == "HONEY_SPIRIT")
        honey.update(days=4.5, temperature="COOL")
        potato = next(family for family in changed["families"] if family["id"] == "POTATO")
        potato.update(distilled_name="Test Potato Spirit", preferred_runs=4)
        whiskey = next(style for style in changed["styles"] if style["id"] == "WHISKEY")
        whiskey["days"] = 4
        finish = next(style for style in changed["styles"] if style["id"] == "SAKURA_WHISKEY")
        finish.update(base_days=40, finish_days=20)
        assert "Honey Spirit | 4.5 days (31.5m) | Cool / Normal | Neutral" in generator.distillery_maturation_reference(changed)
        assert "40 days Oak or Dark Oak, then 20 days Cherry" in generator.distillery_maturation_reference(changed)
        assert "45 days Oak or Dark Oak, then 15 days Acacia" in generator.distillery_maturation_reference(changed)
        assert "Test Potato Spirit | No | 4" in generator.distillery_family_reference(changed)

        generator.write_all()
        docs = Path(tmp) / "docs/addons/distillery"
        assert families in (docs / "families.md").read_text()
        assert "b8ce8a802031ad53dee7a05b94f2f118d383495228070437aa7dced6cf9aadfa" in (docs / "families.md").read_text()
        assert "intentionally reuse" in (docs / "families.md").read_text()
        assert styles in (docs / "cellar-aging.md").read_text()
        nav = (Path(tmp) / "mkdocs.yml").read_text()
        for name in ("families", "cellar-aging", "craftsmanship"):
            assert f"addons/distillery/{name}.md" in nav
        guide = (docs / "mashables-traits.md").read_text()
        assert "Old trait powers have been retired" in guide
        assert "Brewing Traits and Brew History" not in guide
        assert "universal chemistry-balance" in guide
        overview = (docs / "index.md").read_text()
        assert "Distillery Drinks" in overview and "Distillery Guide" in overview
        preview = (docs / "recipe-preview.md").read_text()
        assert "Normal" in preview and "retained" in preview
        assert "Right-click" in preview and "skinned" in preview and "roasted" in preview
        assert "40% spirit" in preview and "4h40m" in preview
        assert "Perfect chance" not in preview
        flow = (docs / "brewing-flow.md").read_text()
        for text in ("Shears", "Flint and Steel", "96%", "20%", "37.8%", "80.7%", "95.2%"):
            assert text in flow, text
        assert "0, 1, 2, 3, 5, 8, 13, 21" in preview
        assert "process icons also act as controls" in preview
        for text in ("AUTO", "ON", "OFF", "Next improvement:", "Ready as shown.", "raw grain or rice", "unsupported"):
            assert text in preview, text
        assert "Reset stays in zero-based slot **34**" in preview
        assert "including Rosé" in preview
        browser = (Path(tmp) / "docs/getting-started/recipe-browser.md").read_text()
        for text in ("**Previous Page** uses an up-arrow head", "**Next Page** uses a down-arrow head",
                     "rightmost two slots of the bottom row", "43 and 44", "Back and Forward"):
            assert text in browser, text
        assert "no skip switch" not in preview
        assert "must first be boiled" not in flow
        assert "Boil for full process credit" in families
        assert "boiling does not change ABV" in flow
        assert "4.51%" in (docs / "mashables-traits.md").read_text()
        assert "Wheat" in generator.distillery_fermentation_reference()
        altered_curve = generator.distillery_strength_reference(catalog, {
            "max_abv": 90, "base_extraction": .25, "run_penalty": 0, "min_gain": 0})
        assert "25%" in altered_curve and "90%" in altered_curve and "42.2%" in altered_curve
        orchard = (Path(tmp) / "docs/addons/orchard/index.md").read_text()
        assert "Average" in orchard
        assert "Spirit ingredient cards, including Rum" in orchard
        assert "keep the recipe's required quantities" in orchard
        assert "five real days" in (docs / "cellar-aging.md").read_text()
        assert "after secondary fermentation" in (docs / "brewing-flow.md").read_text()
        print(f"Distillery generation: {len(catalog['families'])} families, {len(catalog['styles'])} style rules; catalog mutation and generated-page checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
