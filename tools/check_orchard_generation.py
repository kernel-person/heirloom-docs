#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/generate_reference_pages.py"
PLUGIN_ROOT = Path(os.environ.get("HEIRLOOM_PLUGIN_ROOT", ROOT.parent / "foodplugin")).resolve()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        temp_docs = Path(tmp)
        os.environ["HEIRLOOM_DOCS_ROOT"] = str(temp_docs)
        os.environ["HEIRLOOM_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        spec = importlib.util.spec_from_file_location("heirloom_orchard_generator", GENERATOR)
        assert spec and spec.loader
        generator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = generator
        spec.loader.exec_module(generator)

        # Optional addon choices are authored directly in Core JSON and rendered
        # by the ordinary recipe path, without duplicate extension definitions.
        recipe_index = generator.build_recipe_index()
        assert "which remain Core-owned" in recipe_index
        assert "attribute those extensions to Mixology" not in recipe_index
        core_source = json.loads((PLUGIN_ROOT / "heirloom-core/src/main/resources/recipes.json").read_text())["recipes"]
        for recipe_id, inputs in {
            "JAM": ("LEMON", "ORANGE", "MANGO", "PINEAPPLE"),
            "ICE_CREAM": ("BANANAS", "COCONUT", "LEMON", "MANGO", "ORANGE", "PINEAPPLE", "AVOCADO"),
            "TACO": ("ORCHARD_GUACAMOLE",),
        }.items():
            source_recipes = [recipe for recipe in core_source if recipe["id"] == recipe_id]
            assert source_recipes, recipe_id
            for recipe in source_recipes:
                custom_options = {option.get("custom_item") for slot in recipe["ingredients"] for option in slot["options"]}
                assert set(inputs) <= custom_options, (recipe_id, inputs)
            section = recipe_index.split(f"### {recipe_id} {{", 1)[1].split("\n### ", 1)[0]
            assert "| With Heirloom Mixology |" not in section, recipe_id
            assert generator.RECIPE_BY_ID[recipe_id]["_source"] == "Core"
            for item_id in inputs:
                assert f"`{item_id}`" in section, (recipe_id, item_id)
        assert "core_recipe_extensions" not in generator.ORCHARD_CATALOG
        assert generator.RECIPE_BY_ID["TACO"]["_station"] == "Oven"

        # Distinct named drinks must remain visible even while they share approved draft heads.
        for recipe_id, names in {
            "ORCHARD_NEGRONI": {"Negroni", "Boulevardier"},
            "ORCHARD_OLD_FASHIONED": {"Old Fashioned", "Rum Old Fashioned"},
            "ORCHARD_BLACK_RUSSIAN": {"Black Russian", "White Russian", "Mudslide"},
            "ORCHARD_VIRGIN_MANGO_DAIQUIRI": {"Virgin Mango Daiquiri", "Virgin Banana Daiquiri"},
        }.items():
            recipe = generator.RECIPE_BY_ID[recipe_id]
            labels = {variant["label"].removeprefix("Default ")
                      for variant in generator.recipe_output_variant_data(recipe)}
            assert labels == names, (recipe_id, labels)
        for output_id, recipe_id in {
            "ORCHARD_BOULEVARDIER": "ORCHARD_NEGRONI",
            "ORCHARD_RUM_OLD_FASHIONED": "ORCHARD_OLD_FASHIONED",
            "ORCHARD_WHITE_RUSSIAN": "ORCHARD_BLACK_RUSSIAN",
            "ORCHARD_MUDSLIDE": "ORCHARD_BLACK_RUSSIAN",
            "ORCHARD_VIRGIN_BANANA_DAIQUIRI": "ORCHARD_VIRGIN_MANGO_DAIQUIRI",
        }.items():
            assert generator.recipe_output_markdown_href(output_id).endswith(
                "#" + generator.recipe_anchor(recipe_id)), output_id
        assert generator.orchard_recipe_availability("ORCHARD_RUM") == "Distillery absent"
        for recipe_id in ("ORCHARD_COSMOPOLITAN", "ORCHARD_BLACK_RUSSIAN", "ORCHARD_VIRGIN_MANGO_DAIQUIRI"):
            assert generator.RECIPE_BY_ID[recipe_id]["_output_amount"] == 3
        assert generator.RECIPE_BY_ID["ORCHARD_ORANGE_LIQUEUR"]["_output_amount"] == 1
        assert generator.orchard_recipe_availability("ORCHARD_DEATH_IN_THE_AFTERNOON") == "Distillery Sparkling Wine capability 3 required"
        assert "wine capability 2" in generator.orchard_recipe_availability("ORCHARD_CORPSE_REVIVER_NO_2")
        qualified = {"custom_item": "DISTILLERY_WINE", "qualifier": "distillery:sparkling_wine"}
        assert "Sparkling Wine" in generator.format_options([qualified])
        assert "Sparkling Wine" in generator.option_label(qualified)


        juice_recipe = generator.RECIPE_BY_ID["ORCHARD_JUICE"]
        juice_variants = generator.recipe_output_variant_data(juice_recipe)
        assert len(juice_variants) == 29, len(juice_variants)
        assert generator.recipe_output_markdown_href("ORCHARD_TOMATO_JUICE").endswith("#recipe-orchard-juice")
        assert generator.station_key(juice_recipe["station"]) == "Juicer"

        coconut = next(item for item in generator.ITEMS if item.get("id") == "COCONUT")
        assert coconut["_source"] == "Orchard"
        assert coconut["_addon"] == "orchard"
        coconut_milk = next(recipe for recipe in generator.RECIPES
                            if recipe.get("id") == "CANNED_COCONUT_MILK")
        assert coconut_milk["_source"] == "Orchard"
        assert coconut_milk["_addon"] == "orchard"

        pineapple = next((crop for crop in generator.CROPS if crop.get("id") == "PINEAPPLE"), None)
        assert pineapple is not None, "Pineapple must be discovered from Mixology crop resources"
        assert pineapple["_source"] == "Orchard"
        assert pineapple["_addon"] == "orchard"
        assert generator.mixology_branding() == "", "Absent media must not emit a placeholder"
        generator.write_all()

        guide = temp_docs / "docs/addons/orchard/index.md"
        assert guide.is_file()
        page = guide.read_text(encoding="utf-8")
        references = (temp_docs / "docs/reference/recipes.md").read_text(encoding="utf-8")
        assert "remain Core-owned recipes" in references
        assert "attributes the active extensions to Mixology" not in references
        food_section = page.split("## Savory fruit dishes", 1)[1].split("\n## ", 1)[0]
        for phrase in ("Orange Chicken", "Yellow Coconut Curry", "Guacamole", "Frying Pan", "Boiling Pot", "Mixing Bowl", "160 ticks", "200 ticks", "80 ticks", "Bowl"):
            assert phrase in food_section, phrase
        extension_section = page.split("## Core recipe compatibility", 1)[1].split("\n## ", 1)[0]
        assert "#recipe-jam" in extension_section
        assert "#recipe-ice-cream" in extension_section
        assert "#recipe-taco" in extension_section
        assert "Orange Chicken" not in extension_section
        assert "does not copy, replace or take ownership" in extension_section
        assert "Fresh Core installations" in extension_section
        assert "existing installations" in extension_section
        for phrase in (
            "Heirloom Mixology", "Cocktails, Juices & Fruit Trees", "Grow → juice → shake", "Plant the harvested fruit directly", "tree1.schem", "palm1.schem",
            "Beach", "Grove Starter Packet", "Tropical Starter Packet", "seed-acquisition-orchard.json", "whole-fruit head", "Canned Coconut Milk", "Banana Pancakes", "Banana Split Sundae",
            "Dates and the deferred dishes are excluded", "No resource pack is required",
            "WorldEdit", "not a runtime dependency",
        ):
            assert phrase in page, phrase
        inebriation_page = (temp_docs / "docs/addons/distillery/inebriation.md").read_text(encoding="utf-8")
        for phrase in ("without numbers or brackets", "status_reminder_interval_seconds", "muted red", "six more ticks", "last bar frame actually displayed", "alcohol-dose-weighted", "0–4‰ gameplay scale", "| Milk | 0.2‰ |", "| One puking episode | 0.3‰ |", "3.2‰", "four seconds of Blindness I", "Drunkenness & Sobering"):
            assert phrase in inebriation_page, phrase
        for phrase in ("Alcohol servings and quality", "4 cl", "actual liquid cl × ABV / 40", "two 6 cl", "Fractional amounts persist", "No item-definition volume fields", "never reinterpreted as equivalent cl", "default meter holds 40 cl", "0–4‰", "`‰` suffix", "Plain juices and Soda Water have no alcohol row"):
            assert phrase in page, phrase
        assert "(6 × Gin" not in page
        assert "provider packages are not included" in page
        assert f"Heirloom Mixology {generator.RELEASE_VERSIONS['mixology']}" in page
        assert "Head-based v1 draft" not in page
        assert "is release-ready" not in page

        resources = PLUGIN_ROOT / "heirloom-orchard/src/main/resources"
        catalog = json.loads((resources / "catalog-orchard.json").read_text(encoding="utf-8"))
        source_items = json.loads((resources / "custom_items-orchard.json").read_text(encoding="utf-8"))["custom_items"]
        source_recipes = json.loads((resources / "recipes-orchard.json").read_text(encoding="utf-8"))["recipes"]
        mixology = catalog["mixology"]
        assert f"{len(source_items)} item definitions and {len(source_recipes)} recipe definitions" in page
        assert f"Core {catalog['requires_heirloom']} or newer" in page
        assert f"Core {generator.RELEASE_VERSIONS['core']}" in page
        assert "The minimum public Core version remains unconfirmed" not in page
        for counts in mixology["runtime_modes"].values():
            assert f"| {counts['items']} | {counts['recipes']} |" in page
        assert "eight items, and three recipes" not in page
        assert "Apple (owner-gated)" not in page
        for phrase in (
            "8 reusable ingredients", "26 cocktail and non-alcoholic recipe families", "160 ticks", "400 ticks", "No extra Glass Bottle",
            "Other emptied bottles, cans, and cream buckets are returned once", "Drinking returns one Glass Bottle",
            "/hl debug shaker all", "figure-eight", "three player-head shaker parts", "cap knob", "/hl debug shaker perfect all", "80%", "5%",
            "unsupported Distillery", "Core quality controls", "one Quality row",
            "🪣Alcohol", "◾Sugar", "⚗Acid", "♣Tannins",
            "all four fallback spirit definitions", "original Mixing Bowl Piña Colada",
            "capability 2", "Wine or Champagne", "berry-and-vodka", "16-tick",
            "approved head reuse",
            "Soul Sand", "Soda Water", "Fern represents mint", "John Collins", "Americano",
        ):
            assert phrase in page, phrase
        assert "/hl give Orange_Liqueur" in (temp_docs / "docs/server-owners/commands.md").read_text(encoding="utf-8")
        for recipe_id in mixology["recipe_ids"] + mixology["fallback_spirit_ids"]:
            assert f"`{recipe_id}`" in page, recipe_id
            recipe = next(entry for entry in source_recipes if entry["id"] == recipe_id)
            row = next(line for line in page.splitlines() if f"`{recipe_id}`" in line)
            assert f"{recipe['processing_time']} ticks" in row
            for slot in recipe["ingredients"]:
                assert f"{generator.slot_quantity_text(slot)}× " in row

        station = (temp_docs / "docs/stations/mixology-table.md").read_text(encoding="utf-8")
        for phrase in ("IRON_BLOCK", "wooden pressure plate", "Heirloom Mixology", "eight-second", "Cafe", "three drinks"):
            assert phrase in station, phrase
        for recipe_id in mixology["recipe_ids"]:
            assert f"`{recipe_id}`" in station, recipe_id
            recipe = next(entry for entry in source_recipes if entry["id"] == recipe_id)
            assert recipe["station"] in ("Mixology Table", "MIXOLOGY_TABLE"), recipe_id
            assert generator.station_key(recipe["station"]) == "Mixology Table", recipe_id
            vanilla_inputs = {option.get("item") for slot in recipe["ingredients"] for option in slot["options"]}
            assert "GLASS_BOTTLE" not in vanilla_inputs, recipe_id
            if "WATER_BOTTLE" in vanilla_inputs:
                assert "GLASS_BOTTLE" not in vanilla_inputs, recipe_id
                assert all(action["type"] != "SET_RETURN_ITEM" for action in recipe.get("actions", [])), recipe_id
        juicer = (temp_docs / "docs/stations/juicer.md").read_text(encoding="utf-8")
        for phrase in ("DROPPER", "GLASS", "carpet", "three", "ten seconds", "Glass Bottle", "poison"):
            assert phrase in juicer, phrase
        for phrase in ("Juicer", "Tomato Juice", "Pineapple Juice", "half the combined", "perfect 2", "perfect 5"):
            assert phrase in page, phrase
        foods = (temp_docs / "docs/customization/custom-foods.md").read_text(encoding="utf-8")
        assert "station_texture" in foods
        assert "original inventory stack" in foods

        # Buyer documentation must not advertise disabled owner-gated definitions.
        for disabled_id in ("DATE_TREE", "STICKY_DATE_PUDDING", "MANGO_STICKY_RICE", "AVOCADO_TOAST"):
            assert f"`{disabled_id}`" not in page
        assert "Dates (owner-gated)" not in page
        assert "Pure Orange Juice from the Juicer and Sparkling Lemonade remain active" in page
        assert "Exact owner-gated recipes" not in page
        assert "[Mixology Table](../../stations/mixology-table.md)" in page
        assert "[Juicer](../../stations/juicer.md)" in page
        assert "config.yml" in page and "warn-on-draft" in page
        assert "plugins/HeirloomOrchard/" in page
        media = (temp_docs / "docs/media-needed.md").read_text(encoding="utf-8")
        for phrase in ("Heirloom Mixology capture brief", "Wide hero", "Normal shaker", "Perfect shaker",
                       "Juicer blend and two pours", "Bow harvest", "Recipe GUI and three-glass row", "Station construction",
                       "1920×1080", "head-based", "No mock gameplay", "orchard-shaker.mp4",
                       "orchard-perfect-shake.mp4", "orchard-juicer.mp4", "orchard-growing.png",
                       "orchard-recipe-preview.png", "orchard-station-builds.png"):
            assert phrase in media, phrase
        for target in (page, (temp_docs / "docs/stations/mixology-table.md").read_text(encoding="utf-8"),
                       (temp_docs / "docs/stations/juicer.md").read_text(encoding="utf-8")):
            for src in re.findall(r'<img[^>]+src="([^"]+)"', target):
                assert generator.docs_image_exists(src), src
        if (PLUGIN_ROOT / "logo/exports/heirloom-mixology-logo-transparent.png").is_file():
            assert generator.SOURCE_LOGO_MANIFEST["Orchard"] == "images/sources/mixology.png"
            assert (temp_docs / "docs/images/sources/mixology.png").is_file()
        if (PLUGIN_ROOT / "logo/exports/heirloom-mixology-banner-marketplace.png").is_file():
            assert "Heirloom Mixology graphic banner" in page
        assert "PINEAPPLE" in (temp_docs / "docs/reference/crops.md").read_text(encoding="utf-8")
        assert "Heirloom Mixology" in generator.source_badge("Orchard", "../../")
        assert generator.orchard_recipe_availability("ORCHARD_DRY_MARTINI") == "Distillery absent or wine capability 2"

        nav = (temp_docs / "mkdocs.yml").read_text(encoding="utf-8")
        assert "Heirloom Mixology:\n          - Overview: addons/orchard/index.md" in nav
        assert "[Heirloom Mixology](addons/orchard/index.md)" in (temp_docs / "docs/index.md").read_text(encoding="utf-8")
        assert "Mixology Table: stations/mixology-table.md" in nav
        assert "Mixology Recipes: recipes/station-mixology-table.md" in nav
        assert "COCONUT" in (temp_docs / "docs/reference/items.md").read_text(encoding="utf-8")
        assert "CANNED_COCONUT_MILK" in (
            temp_docs / "docs/recipes/default-recipes.md").read_text(encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
