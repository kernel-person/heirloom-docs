#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/generate_reference_pages.py"
PLUGIN_ROOT = Path(os.environ.get("HEIRLOOM_PLUGIN_ROOT", ROOT.parent / "foodplugin")).resolve()
if not PLUGIN_ROOT.exists():
    PLUGIN_ROOT = Path("/Users/rickardmartensson/code/minecraft_plugins/foodplugin/foodplugin")


def load_generator(temp_docs: Path):
    os.environ["HEIRLOOM_DOCS_ROOT"] = str(temp_docs)
    os.environ["HEIRLOOM_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    module_name = f"heirloom_content_pack_generator_{id(temp_docs)}"
    spec = importlib.util.spec_from_file_location(module_name, GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load generate_reference_pages.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        temp_docs = Path(tmp)
        generator = load_generator(temp_docs)

        packs = {pack["id"]: pack for pack in generator.CONTENT_PACKS}
        asian = packs["heirloom_asian_food"]
        assert asian["name"] == "Heirloom Asian Food Pack"
        assert asian["version"] == "1.0.0"
        assert len(asian["items"]) == 47
        assert len(asian["recipes"]) == 29
        american = packs["heirloom_american_food"]
        assert american["name"] == "Heirloom American Food Pack"
        assert american["version"] == "1.0.1"
        assert american["status"] == "release"
        assert american["requires_heirloom"] == "2.10.1+ (shared Soda Water build)"
        assert len(american["base_items"]) == 40
        assert len(american["base_recipes"]) == 30
        assert len(american["overlay_items"]) == 3
        assert len(american["overlay_recipes"]) == 4
        assert len(american["items"]) == 43
        assert len(american["recipes"]) == 34

        assert generator.RECIPE_ID_COUNTS["BLT"] == 1
        assert generator.RECIPE_ID_COUNTS["BREAD"] == 1
        assert generator.RECIPE_BY_ID["BLT"]["_source"] == "Heirloom American Food Pack"
        assert generator.RECIPE_BY_ID["BREAD"]["_source"] == "Heirloom American Food Pack"
        orchard_soda = next(recipe for recipe in generator.RECIPES if recipe.get("id") == "AMERICAN_SODA")
        assert orchard_soda["_compatibility"] == "orchard"
        assert orchard_soda["_source"] == "Heirloom American Food Pack (Orchard compatibility)"
        assert "Lemon Soda" in {
            variant["label"] for variant in generator.recipe_output_variant_data(orchard_soda)
        }
        smore = next(recipe for recipe in generator.RECIPES if recipe.get("id") == "AMERICAN_SMORE")
        assert {option.get("custom_item") or option.get("item")
                for option in smore["ingredients"][0]["options"]} == {"BREAD"}

        asian_item = next(item for item in generator.ITEMS if item.get("id") == "ASIAN_RICE_FLOUR")
        assert asian_item["_source"] == "Heirloom Asian Food Pack"
        assert asian_item["_pack_id"] == "heirloom_asian_food"

        asian_recipe = next(recipe for recipe in generator.RECIPES if recipe.get("id") == "ASIAN_MISO_SOUP")
        assert asian_recipe["_source"] == "Heirloom Asian Food Pack"
        assert asian_recipe["_pack_id"] == "heirloom_asian_food"

        generator.USE_VISUAL_PACK_ICONS = True
        generator.write_all()

        pack_page = temp_docs / "docs/content-packs/heirloom-asian-food-pack.md"
        assert pack_page.is_file()
        page = pack_page.read_text(encoding="utf-8")
        assert "47 custom items" in page
        assert "29 recipe entries" in page
        assert "ASIAN_MISO_SOUP" in page
        assert "ASIAN_NIGIRI_UNAGI" in page
        assert "Nexo" in page
        assert "ItemsAdder" in page
        assert "CraftEngine" in page
        assert "MMOItems" in page
        assert 'src="../../images/items/visual-pack/asian-dumpling-meat.png"' in page
        assert 'src="../images/items/visual-pack/' not in page
        assert 'href="../../reference/items/' in page
        assert 'src="../../images/content-packs/heirloom-asian-food-pack-banner.png"' in page
        assert 'src="../../images/content-packs/heirloom-asian-food-pack-catalog.png"' in page
        assert "source textures are not published" in page

        american_page = temp_docs / "docs/content-packs/heirloom-american-food-pack.md"
        assert american_page.is_file()
        american_text = american_page.read_text(encoding="utf-8")
        assert "40 base custom items" in american_text
        assert "30 base recipe entries" in american_text
        assert "3 optional custom items" in american_text
        assert "4 optional recipe entries" in american_text
        assert "development draft" not in american_text
        assert "Heirloom 2.10.1+ (shared Soda Water build)" in american_text
        assert "43 raw PNG sprites" in american_text
        assert "Nexo, ItemsAdder, CraftEngine" in american_text
        assert 'src="../../images/content-packs/heirloom-american-food-pack-banner.png"' in american_text
        assert 'src="../../images/content-packs/heirloom-american-food-pack-catalog.png"' in american_text
        for kind, export in (
            ("banner", "heirloom-american-food-banner-marketplace.png"),
            ("catalog", "heirloom-american-food-item-catalog-provider-marketplace.png"),
        ):
            assert (temp_docs / f"docs/images/content-packs/heirloom-american-food-pack-{kind}.png").read_bytes() == (PLUGIN_ROOT / "logo/exports" / export).read_bytes()
        assert "AMERICAN_CORN_DOG" in american_text
        assert "carrying `CORNMEAL`" in american_text
        assert "Optional Compatibility" in american_text
        assert "Orchard Overlay" in american_text
        assert "AMERICAN_LEMON_SODA" in american_text
        assert "AMERICAN_BANANA_MILKSHAKE" in american_text
        assert "BANANA_SPLIT_SUNDAE" in american_text
        assert "AMERICAN_SODA" in american_text
        assert "AMERICAN_MILKSHAKE" in american_text
        assert "effects: Nausea" in american_text

        banner = temp_docs / "docs/images/content-packs/heirloom-asian-food-pack-banner.png"
        assert banner.is_file()
        catalog = temp_docs / "docs/images/content-packs/heirloom-asian-food-pack-catalog.png"
        assert catalog.is_file()

        source_preview = PLUGIN_ROOT / "packs/Heirloom-Asian-Food-Pack-v1.0.0/textures/asian_dumpling_meat.png"
        public_preview = temp_docs / "docs/images/items/visual-pack/asian-dumpling-meat.png"
        width, height, pixels = generator.read_png_rgba(public_preview.read_bytes())
        assert (width, height) == (63, 63)
        assert all(alpha == 255 for _red, _green, _blue, alpha in pixels)
        assert pixels[0] == (255, 253, 245, 255)
        assert generator.ICON_MANIFEST["ASIAN_DUMPLING_MEAT"]["render_style"] == "protected_preview_63_front_relief"
        assert public_preview.read_bytes() != source_preview.read_bytes()

        recipes = (temp_docs / "docs/recipes/default-recipes.md").read_text(encoding="utf-8")
        items = (temp_docs / "docs/reference/items.md").read_text(encoding="utf-8")
        nav = (temp_docs / "mkdocs.yml").read_text(encoding="utf-8")
        assert "ASIAN_MISO_SOUP" in recipes
        assert "Heirloom Asian Food Pack" in recipes
        assert "ASIAN_RICE_FLOUR" in items
        assert "Content Packs:" in nav
        assert "Heirloom Asian Food Pack: content-packs/heirloom-asian-food-pack.md" in nav
        assert "Heirloom American Food Pack: content-packs/heirloom-american-food-pack.md" in nav

        source_images = temp_docs / "docs/images/sources"
        for filename in ("core.png", "cafe.png", "heirloom-asian-food-pack.png", "heirloom-american-food-pack.png"):
            assert (source_images / filename).is_file()

        frying_pan = (temp_docs / "docs/recipes/station-frying-pan.md").read_text(encoding="utf-8")
        assert 'src="../../images/sources/core.png"' in frying_pan
        assert 'src="../../images/sources/heirloom-asian-food-pack.png"' in frying_pan
        assert 'title="Core"' in frying_pan
        assert 'title="Heirloom Asian Food Pack"' in frying_pan
        assert 'src="../../images/sources/heirloom-asian-food-pack.png"' in recipes
        assert "Heirloom American Food Pack (Orchard compatibility)" in recipes

        # The explicit release fallback must not broaden discovery to arbitrary
        # worktree drafts, and an integrated canonical pack always takes precedence.
        original_root = generator.PLUGIN_ROOT
        with tempfile.TemporaryDirectory() as fixture:
            generator.PLUGIN_ROOT = Path(fixture)
            name = "Heirloom-American-Food-Pack-v1.0.0"
            fallback = Path(fixture) / ".worktrees/american-food-pack/packs" / name
            canonical = Path(fixture) / "packs" / "Heirloom-American-Food-Pack-v1.0.1"

            def write_pack(directory: Path, status: str = "release") -> None:
                (directory / "content").mkdir(parents=True)
                metadata = {"id": "heirloom_american_food", "name": "Heirloom American Food Pack", "version": "1.0.0"}
                (directory / "content/custom_items.json").write_text(json.dumps({"pack": metadata, "custom_items": []}))
                (directory / "catalog.json").write_text(json.dumps({"pack": {**metadata, "status": status}}))

            try:
                (Path(fixture) / "packs").mkdir()
                write_pack(fallback)
                write_pack(Path(fixture) / ".worktrees/unapproved/packs/Draft", "development-draft")
                assert [pack["directory"] for pack in generator.discover_content_packs()] == [fallback]
                catalog = json.loads((fallback / "catalog.json").read_text())
                catalog["pack"]["status"] = "development-draft"
                (fallback / "catalog.json").write_text(json.dumps(catalog))
                try:
                    generator.discover_content_packs()
                except ValueError as error:
                    assert "expected release pack" in str(error)
                else:
                    raise AssertionError("An authoring draft must not become a released wiki pack")
                write_pack(canonical)
                assert [pack["directory"] for pack in generator.discover_content_packs()] == [canonical]
            finally:
                generator.PLUGIN_ROOT = original_root

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
