from __future__ import annotations

import argparse
import html
import io
import importlib.util
import json
import os
import re
import shutil
import subprocess
import struct
import sys
import textwrap
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import zlib
import yaml
from collections import defaultdict
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
if SCRIPT_PATH.parent.name == "tools":
    DEFAULT_DOCS_ROOT = SCRIPT_PATH.parents[1]
else:
    DEFAULT_DOCS_ROOT = Path("/Users/rickardmartensson/code/minecraft_plugins/foodplugin/heirloom-docs")

DOCS_ROOT = Path(os.environ.get("HEIRLOOM_DOCS_ROOT", DEFAULT_DOCS_ROOT)).resolve()
PAGE_SOURCE_ROOT = SCRIPT_PATH.parents[1] / "pages"
PLUGIN_ROOT = Path(os.environ.get("HEIRLOOM_PLUGIN_ROOT", DOCS_ROOT.parent / "foodplugin")).resolve()
if not PLUGIN_ROOT.exists():
    PLUGIN_ROOT = Path("/Users/rickardmartensson/code/minecraft_plugins/foodplugin/foodplugin")
FETCH_ICONS = False
USE_VISUAL_PACK_ICONS = False
ICON_MANIFEST: dict[str, dict[str, str]] = {}
RECIPE_VARIANT_MANIFEST: dict[str, dict[str, str]] = {}
SOURCE_LOGO_MANIFEST: dict[str, str] = {}
MISSING_ICON_ROWS: list[tuple[str, str, str]] = []
MINECRAFT_ASSET_INDEX: dict[str, dict] | None = None
MINECRAFT_CLIENT_JAR: zipfile.ZipFile | None = None
MINECRAFT_ASSET_VERSION: str | None = None


def load_existing_icon_manifest() -> dict:
    manifest_path = DOCS_ROOT / "docs/images/items/icon-manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


EXISTING_ICON_MANIFEST = load_existing_icon_manifest()


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


ORCHARD_RESOURCES = PLUGIN_ROOT / "heirloom-orchard/src/main/resources"
ORCHARD_CATALOG = read_json(ORCHARD_RESOURCES / "catalog-orchard.json")
ORCHARD_MIXOLOGY = ORCHARD_CATALOG["mixology"]
DISTILLERY_RESOURCES = PLUGIN_ROOT / "heirloom-distillery/src/main/resources"
PASTURE_CATALOG = read_json(PLUGIN_ROOT / "heirloom-pasture/src/main/resources/catalog-pasture.json")


def module_version(module: str) -> str:
    """Read the published module version, including an inherited parent version."""
    project = ET.parse(PLUGIN_ROOT / module / "pom.xml").getroot()
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    version = project.findtext("m:version", namespaces=ns) or project.findtext("m:parent/m:version", namespaces=ns)
    if not version:
        raise ValueError(f"Missing release version for {module}")
    return version


RELEASE_VERSIONS = {
    "core": module_version("heirloom-core"),
    "cafe": module_version("heirloom-cafe"),
    "distillery": module_version("heirloom-distillery"),
    "mixology": module_version("heirloom-orchard"),
    "pasture": module_version("heirloom-pasture"),
}


def orchard_recipe_availability(recipe_id: str) -> str:
    """Describe bundled source definitions; the server selects its active mode."""
    if recipe_id in ORCHARD_CATALOG.get("food_expansion", {}).get("item_ids", []):
        return "All Mixology modes"
    if recipe_id == "ORCHARD_DEATH_IN_THE_AFTERNOON":
        return "Distillery Sparkling Wine capability 3 required"
    if recipe_id in ORCHARD_MIXOLOGY["fallback_spirit_ids"]:
        return "Distillery absent"
    if recipe_id not in ORCHARD_MIXOLOGY["recipe_ids"]:
        return ""
    if recipe_id in {"ORCHARD_VIRGIN_MOJITO", "ORCHARD_SPARKLING_LEMONADE"}:
        return "Virgin: all Mixology modes; spirit variant: Distillery absent or compatible integration"
    if recipe_id in ORCHARD_MIXOLOGY["non_alcoholic_recipe_ids"]:
        return "All Mixology modes; non-alcoholic"
    requirement = "Distillery absent or compatible Mixology integration"
    if recipe_id in {"ORCHARD_SWEET_VERMOUTH", "ORCHARD_NEGRONI", "ORCHARD_MANHATTAN", "ORCHARD_AMERICANO", "ORCHARD_DRY_MARTINI", "ORCHARD_CORPSE_REVIVER_NO_2"}:
        requirement = "Distillery absent or wine capability 2"
    if recipe_id in ORCHARD_MIXOLOGY["cafe_recipe_ids"]:
        requirement += "; Cafe required"
    return requirement


def load_cheese_affinity_catalog() -> dict:
    path = PLUGIN_ROOT / "heirloom-pasture/src/main/resources/cheese-affinities.json"
    catalog = read_json(path)
    if catalog.get("version") != 2 or not isinstance(catalog.get("styles"), dict):
        raise ValueError(f"Unsupported cheese affinity catalog: {path}")
    return catalog


def load_direct_whey_cheese_routes() -> list[dict[str, str]]:
    """Load non-affinity whey cheeses from the same item and recipe resources used in game."""
    resources = PLUGIN_ROOT / "heirloom-pasture/src/main/resources"
    items = {
        str(item["id"]): item
        for item in read_json(resources / "custom_items-pasture.json").get("custom_items", [])
    }
    recipes = {
        str(recipe["id"]): recipe
        for recipe in read_json(resources / "recipes-pasture.json").get("recipes", [])
    }
    routes = []
    for recipe_id in ("REHEAT_WHEY_RICOTTA", "REDUCE_WHEY_BRUNOST"):
        recipe = recipes.get(recipe_id)
        if not recipe:
            continue
        output_id = str(recipe["output"])
        item = items.get(output_id, {})
        routes.append({
            "item_id": output_id,
            "display_name": str(item.get("name", title_from_id(output_id))),
            "description": str(recipe.get("description", "")),
        })
    return routes


def cheese_flowchart_svg(catalog: dict, whey_routes: list[dict[str, str]] | None = None) -> str:
    """Render a deterministic, score-free overview from runtime route definitions."""
    whey_routes = load_direct_whey_cheese_routes() if whey_routes is None else whey_routes
    ordered_ids = [style_id for style_id in catalog.get("tie_order", []) if style_id in catalog["styles"]]
    ordered_ids.extend(style_id for style_id in catalog["styles"] if style_id not in ordered_ids)
    route_rows = max(1, (len(ordered_ids) + 1) // 2)
    route_bottom = 332 + (route_rows - 1) * 112 + 92
    direct_divider_y = route_bottom + 40
    direct_title_y = direct_divider_y + 38
    direct_card_y = direct_title_y + 20
    width, height = 1200, direct_card_y + 140
    flow_nodes = [
        ("Milk sources", "Cold • Temperate • Warm", "Cow • Goat • Sheep"),
        ("Boiling Pot", "Boil three mixed pails", "Fresh Curds + whey"),
        ("Fresh Curds", "Milk blend remembered", "Try different paths"),
        ("Treatments", "Acid • boil • wash", "Whey • water • stretch"),
        ("Salt or brine", "Mixing Bowl", "Optional cheese culture"),
        ("Farmhouse Press", "Prepared Cheese", "Feta may finish here"),
        ("Aging Rack", "Climate shapes result", "Remove after one day"),
    ]
    node_width, node_height, gap, start_x = 144, 92, 20, 20
    top_y = 150
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Pasture affinity cheesemaking recommended paths</title>',
        f'<desc id="desc">Recommended paths from milk sources through curds, treatments, preparation, pressing, aging, {len(ordered_ids)} affinity cheeses, and direct whey cheeses. Experimentation remains valid.</desc>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#9a6938"/></marker></defs>',
        f'<rect width="1200" height="{height}" rx="28" fill="#fffaf0"/>',
        '<text x="600" y="56" text-anchor="middle" font-family="system-ui,sans-serif" font-size="30" font-weight="700" fill="#3d2c1e">Heirloom Pasture Cheesemaking</text>',
        '<text x="600" y="91" text-anchor="middle" font-family="system-ui,sans-serif" font-size="17" fill="#72563c">Recommended paths — experimentation is always welcome</text>',
        '<text x="30" y="130" font-family="system-ui,sans-serif" font-size="15" font-weight="700" fill="#9a6938">SHARED FLOW</text>',
    ]
    for index, lines in enumerate(flow_nodes):
        x = start_x + index * (node_width + gap)
        if index:
            previous_right = x - gap
            out.append(f'<path d="M{previous_right} {top_y + node_height / 2} H{x - 5}" stroke="#9a6938" stroke-width="3" fill="none" marker-end="url(#arrow)"/>')
        out.append(f'<g id="flow-{slug(lines[0])}">')
        out.append(f'<rect x="{x}" y="{top_y}" width="{node_width}" height="{node_height}" rx="14" fill="#f6e7c6" stroke="#c49256" stroke-width="2"/>')
        out.append(f'<text x="{x + node_width / 2}" y="{top_y + 26}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="700" fill="#3d2c1e">{html.escape(lines[0])}</text>')
        out.append(f'<text x="{x + node_width / 2}" y="{top_y + 51}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11.5" fill="#5d4a38">{html.escape(lines[1])}</text>')
        out.append(f'<text x="{x + node_width / 2}" y="{top_y + 70}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11.5" fill="#5d4a38">{html.escape(lines[2])}</text></g>')

    out.extend([
        '<rect x="28" y="274" width="1144" height="2" fill="#ead5ae"/>',
        f'<text x="30" y="311" font-family="system-ui,sans-serif" font-size="15" font-weight="700" fill="#9a6938">{len(ordered_ids)} SUGGESTED ROUTES</text>',
        '<text x="1170" y="311" text-anchor="end" font-family="system-ui,sans-serif" font-size="13" fill="#72563c">Lore recommends the next useful action as your affinities change</text>',
    ])
    for index, style_id in enumerate(ordered_ids):
        style = catalog["styles"][style_id]
        column, row = index % 2, index // 2
        x, y = 30 + column * 575, 332 + row * 112
        card_width, card_height = 540, 92
        route_id = f"route-{style_id.lower().replace('_', '-')}"
        out.append(f'<g id="{route_id}" data-item="{html.escape(str(style.get("item_id", style_id)))}">')
        out.append(f'<rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" rx="13" fill="#ffffff" stroke="#dfc28d" stroke-width="2"/>')
        out.append(f'<circle cx="{x + 28}" cy="{y + 28}" r="15" fill="#f0c96d"/>')
        out.append(f'<text x="{x + 28}" y="{y + 33}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="12" font-weight="700" fill="#3d2c1e">{index + 1}</text>')
        out.append(f'<text x="{x + 52}" y="{y + 33}" font-family="system-ui,sans-serif" font-size="17" font-weight="700" fill="#3d2c1e">{html.escape(str(style["display_name"]))}</text>')
        description = str(style.get("description", ""))
        wrapped = textwrap.wrap(description, width=73)[:2]
        for line_index, line in enumerate(wrapped):
            out.append(f'<text x="{x + 22}" y="{y + 59 + line_index * 18}" font-family="system-ui,sans-serif" font-size="12.5" fill="#5d4a38">{html.escape(line)}</text>')
        out.append('</g>')
    out.extend([
        f'<rect x="28" y="{direct_divider_y}" width="1144" height="2" fill="#ead5ae"/>',
        f'<text x="30" y="{direct_title_y}" font-family="system-ui,sans-serif" font-size="15" font-weight="700" fill="#9a6938">DIRECT WHEY ROUTES</text>',
        f'<text x="1170" y="{direct_title_y}" text-anchor="end" font-family="system-ui,sans-serif" font-size="13" fill="#72563c">Use the whey left by every curd batch</text>',
    ])
    for index, route in enumerate(whey_routes):
        x, y = 30 + index * 575, direct_card_y
        route_id = f'route-{slug(route["item_id"])}'
        out.append(f'<g id="{route_id}" data-item="{html.escape(route["item_id"])}">')
        out.append(f'<rect x="{x}" y="{y}" width="540" height="92" rx="13" fill="#fff7e3" stroke="#c49256" stroke-width="2"/>')
        out.append(f'<text x="{x + 22}" y="{y + 33}" font-family="system-ui,sans-serif" font-size="17" font-weight="700" fill="#3d2c1e">{html.escape(route["display_name"])}</text>')
        description = textwrap.wrap(route["description"], width=73)[:2]
        for line_index, line in enumerate(description):
            out.append(f'<text x="{x + 22}" y="{y + 59 + line_index * 18}" font-family="system-ui,sans-serif" font-size="12.5" fill="#5d4a38">{html.escape(line)}</text>')
        out.append('</g>')
    out.append(f'<text x="600" y="{height - 30}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" fill="#72563c">Affinity routes reward experimentation; direct whey routes turn the useful byproduct into fresh cheese.</text>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


def write_cheese_flowchart() -> Path:
    target = DOCS_ROOT / "docs/images/generated/pasture-cheese-flow.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(cheese_flowchart_svg(load_cheese_affinity_catalog()), encoding="utf-8")
    return target


def slug(value: str) -> str:
    value = value.strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "entry"


def md_escape(value) -> str:
    if value is None:
        return ""
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def title_from_id(value: str) -> str:
    return value.replace("_", " ").title()


def discover_content_packs() -> list[dict]:
    """Load distributable JSON content packs from the plugin repository."""
    packs_root = PLUGIN_ROOT / "packs"
    if not packs_root.exists():
        return []

    pack_dirs = [path for path in packs_root.iterdir() if path.is_dir()]
    # American's released source still lives in its authoring worktree. Prefer
    # the canonical pack once integrated; never discover other worktree drafts.
    american_folder = "Heirloom-American-Food-Pack-v1.0.0"
    american_fallback = PLUGIN_ROOT / ".worktrees/american-food-pack/packs" / american_folder
    if not any(path.name.startswith("Heirloom-American-Food-Pack-v") for path in pack_dirs) and american_fallback.is_dir():
        pack_dirs.append(american_fallback)

    discovered: list[dict] = []
    for pack_dir in sorted(pack_dirs):
        content_dir = pack_dir / "content"
        if not content_dir.is_dir():
            continue

        base_item_files = sorted(content_dir.glob("custom_items*.json"))
        base_recipe_files = sorted(content_dir.glob("recipes*.json"))
        overlay_item_files = sorted(pack_dir.glob("compatibility/*/custom_items*.json"))
        overlay_recipe_files = sorted(pack_dir.glob("compatibility/*/recipes*.json"))
        item_files = [*base_item_files, *overlay_item_files]
        recipe_files = [*base_recipe_files, *overlay_recipe_files]
        if not item_files and not recipe_files:
            continue

        metadata: dict | None = None
        base_items: list[dict] = []
        base_recipes: list[dict] = []
        overlay_items: list[dict] = []
        overlay_recipes: list[dict] = []
        for path in [*item_files, *recipe_files]:
            data = read_json(path)
            candidate = data.get("pack")
            if not isinstance(candidate, dict) or not candidate.get("id") or not candidate.get("name"):
                raise ValueError(f"Content pack metadata missing from {path}")
            normalized = {
                "id": str(candidate["id"]),
                "name": str(candidate["name"]),
                "version": str(candidate.get("version", "unknown")),
                "override_strength": int(candidate.get("override_strength", 0)),
            }
            if metadata is None:
                metadata = normalized
            elif metadata != normalized:
                raise ValueError(f"Conflicting content pack metadata in {pack_dir}")
            relative = path.relative_to(pack_dir)
            compatibility = relative.parts[1] if relative.parts[0] == "compatibility" else None
            target_items = overlay_items if compatibility else base_items
            target_recipes = overlay_recipes if compatibility else base_recipes
            for item in data.get("custom_items", []) or []:
                row = dict(item)
                if compatibility:
                    row["_compatibility"] = compatibility
                target_items.append(row)
            for recipe in data.get("recipes", []) or []:
                row = dict(recipe)
                if compatibility:
                    row["_compatibility"] = compatibility
                target_recipes.append(row)

        if metadata is None:
            continue
        catalog_path = pack_dir / "catalog.json"
        catalog = read_json(catalog_path) if catalog_path.is_file() else {}
        catalog_pack = catalog.get("pack", {}) if isinstance(catalog, dict) else {}
        if pack_dir == american_fallback and (
            metadata["id"] != "heirloom_american_food"
            or catalog_pack.get("id") != metadata["id"]
            or catalog_pack.get("status") != "release"
        ):
            raise ValueError(f"American authoring source is not the expected release pack: {pack_dir}")
        providers = []
        for provider, folder in (("Nexo", "nexo"), ("ItemsAdder", "itemsadder"), ("CraftEngine", "craftengine"), ("MMOItems", "mmoitems")):
            if (pack_dir / folder).is_dir():
                providers.append(provider)
        discovered.append({
            **metadata,
            "directory": pack_dir,
            "item_files": item_files,
            "recipe_files": recipe_files,
            "items": [*base_items, *overlay_items],
            "recipes": [*base_recipes, *overlay_recipes],
            "base_items": base_items,
            "base_recipes": base_recipes,
            "overlay_items": overlay_items,
            "overlay_recipes": overlay_recipes,
            "providers": providers,
            "texture_count": len(list((pack_dir / "textures").glob("*.png"))),
            "status": str(catalog_pack.get("status", "release")),
            "requires_heirloom": str(catalog_pack.get("requires_heirloom", "2.9+")),
            "catalog": catalog,
        })
    return discovered


def station_key(station: str | None) -> str:
    if not station:
        return "Unknown"
    normalized = station.replace("_", " ").strip().lower()
    aliases = {
        "oven": "Oven",
        "boiling pot": "Boiling Pot",
        "mixing bowl": "Mixing Bowl",
        "cutting board": "Cutting Board",
        "frying pan": "Frying Pan",
        "frying station": "Frying Pan",
        "barista machine": "Barista Machine",
        "mixology table": "Mixology Table",
        "stomping tub": "Stomping Tub",
        "fermentation barrel": "Fermentation Barrel",
        "distillation stand": "Distillation Stand",
        "farmhouse press": "Farmhouse Press",
        "aging rack": "Aging Rack",
    }
    return aliases.get(normalized, station.replace("_", " ").title())


CONTENT_PACKS = discover_content_packs()


def load_items():
    specs = [
        ("Core", PLUGIN_ROOT / "heirloom-core/src/main/resources/custom_items.json"),
        ("Core", PLUGIN_ROOT / "heirloom-core/src/main/resources/custom_items-soda-water.json"),
        ("World", PLUGIN_ROOT / "heirloom-core/src/main/resources/custom_items-world.json"),
        ("Festive", PLUGIN_ROOT / "heirloom-core/src/main/resources/custom_items-festive.json"),
        ("Distillery", DISTILLERY_RESOURCES / "custom_items-distillery.json"),
        ("Cafe", PLUGIN_ROOT / "heirloom-cafe/src/main/resources/custom_items-cafe.json"),
        ("Pasture", PLUGIN_ROOT / "heirloom-pasture/src/main/resources/custom_items-pasture.json"),
        ("Orchard", PLUGIN_ROOT / "heirloom-orchard/src/main/resources/custom_items-orchard.json"),
    ]
    items = []
    for source, path in specs:
        if not path.exists():
            continue
        for item in read_json(path).get("custom_items", []):
            row = dict(item)
            row["_source"] = source
            row["_addon"] = row.get("addon") or ({
                "Cafe": "cafe", "Distillery": "distillery", "Pasture": "pasture", "Orchard": "orchard"
            }.get(source, "core"))
            items.append(row)
    for pack in CONTENT_PACKS:
        for item in pack["items"]:
            row = dict(item)
            compatibility = row.get("_compatibility")
            row["_source"] = pack["name"] + (
                f" ({title_from_id(str(compatibility))} compatibility)" if compatibility else ""
            )
            row["_addon"] = pack["id"]
            row["_pack_id"] = pack["id"]
            items.append(row)
    return items


def normalize_primary_output(recipe: dict) -> dict:
    """Keep identity lookups simple while retaining typed-output quantities for documentation."""
    row = dict(recipe)
    output = row.get("output", "")
    row["_output_amount"] = 1
    if isinstance(output, dict):
        identities = [output[key] for key in ("custom_item", "item", "provider_item") if key in output]
        if len(identities) != 1:
            raise ValueError(f"Invalid primary output for {row.get('id')}: {output}")
        row["output"] = identities[0]
        row["_output_amount"] = int(output.get("amount", 1))
    for action in row.get("actions", []):
        if action.get("type") == "SET_AMOUNT":
            row["_output_amount"] = int(action["value"])
    return row


def load_recipes():
    specs = [
        ("Core", PLUGIN_ROOT / "heirloom-core/src/main/resources/recipes.json"),
        ("Core", PLUGIN_ROOT / "heirloom-core/src/main/resources/recipes-soda-water.json"),
        ("World", PLUGIN_ROOT / "heirloom-core/src/main/resources/recipes-world.json"),
        ("Festive", PLUGIN_ROOT / "heirloom-core/src/main/resources/recipes-festive.json"),
        ("Cafe", PLUGIN_ROOT / "heirloom-cafe/src/main/resources/recipes-cafe.json"),
        ("Pasture", PLUGIN_ROOT / "heirloom-pasture/src/main/resources/recipes-pasture.json"),
        ("Orchard", PLUGIN_ROOT / "heirloom-orchard/src/main/resources/recipes-orchard.json"),
    ]
    recipes = []
    for source, path in specs:
        if not path.exists():
            continue
        for recipe_index, recipe in enumerate(read_json(path).get("recipes", [])):
            row = normalize_primary_output(recipe)
            row["_source"] = source
            row["_addon"] = row.get("addon") or ({
                "Cafe": "cafe", "Pasture": "pasture", "Orchard": "orchard"
            }.get(source, "core"))
            row["_station"] = station_key(row.get("station") or row.get("stationName"))
            row["_sequence"] = len(recipes)
            row["_source_index"] = recipe_index
            row["_override_strength"] = 0
            recipes.append(row)
    for pack in CONTENT_PACKS:
        for recipe_index, recipe in enumerate(pack["recipes"]):
            row = normalize_primary_output(recipe)
            compatibility = row.get("_compatibility")
            row["_source"] = pack["name"] + (
                f" ({title_from_id(str(compatibility))} compatibility)" if compatibility else ""
            )
            row["_addon"] = pack["id"]
            row["_pack_id"] = pack["id"]
            row["_station"] = station_key(row.get("station") or row.get("stationName"))
            row["_sequence"] = len(recipes)
            row["_source_index"] = recipe_index
            row["_override_strength"] = int(row.get(
                "override_strength", pack["override_strength"]))
            recipes.append(row)
    return recipes


def resolve_active_recipes(recipes: list[dict]) -> list[dict]:
    """Mirror runtime override selection: highest strength wins, first wins ties."""
    winners: dict[str, dict] = {}
    for recipe in recipes:
        rid = str(recipe.get("id", "")).upper()
        if not rid:
            continue
        current = winners.get(rid)
        if current is None or int(recipe.get("_override_strength", 0)) > int(current.get("_override_strength", 0)):
            winners[rid] = recipe
    return sorted(winners.values(), key=lambda row: row.get("_sequence", 0))


def load_crops():
    specs = [
        ("Core", PLUGIN_ROOT / "heirloom-core/src/main/resources/crops.json"),
        ("Distillery", DISTILLERY_RESOURCES / "crops-distillery.json"),
        ("Cafe", PLUGIN_ROOT / "heirloom-cafe/src/main/resources/crops-cafe.json"),
        ("Orchard", ORCHARD_RESOURCES / "crops-orchard.json"),
    ]
    crops = []
    for source, path in specs:
        if not path.exists():
            continue
        data = read_json(path)
        for crop in data.get("crops", []):
            row = dict(crop)
            row["_source"] = source
            row["_addon"] = row.get("addon") or {
                "Cafe": "cafe", "Distillery": "distillery"
            }.get(source, "core")
            crops.append(row)
    return crops


ITEMS = load_items()
ALL_RECIPES = load_recipes()
RECIPES = resolve_active_recipes(ALL_RECIPES)
CROPS = load_crops()
DIET = read_json(PLUGIN_ROOT / "heirloom-core/src/main/resources/dietary_properties.json")
SEEDS = read_json(PLUGIN_ROOT / "heirloom-core/src/main/resources/seed_acquisition.json")
ENCHANTS = read_json(PLUGIN_ROOT / "heirloom-core/src/main/resources/enchantment_integrations.json")

ITEM_BY_ID = {item["id"].upper(): item for item in ITEMS if "id" in item}
ITEM_ID_BY_VISUAL_ID = {str(item.get("visual_id", "")).upper(): item["id"].upper() for item in ITEMS if item.get("visual_id") and item.get("id")}
RECIPE_BY_ID: dict[str, dict] = {}
RECIPE_ID_COUNTS = defaultdict(int)
for recipe in RECIPES:
    rid = str(recipe.get("id", "")).upper()
    if not rid:
        continue
    RECIPE_BY_ID.setdefault(rid, recipe)
    RECIPE_ID_COUNTS[rid] += 1
    suffix = "" if RECIPE_ID_COUNTS[rid] == 1 else f"-{RECIPE_ID_COUNTS[rid]}"
    recipe["_anchor"] = f"recipe-{slug(rid)}{suffix}"

RECIPES_BY_OUTPUT = defaultdict(list)
for recipe in RECIPES:
    output = str(recipe.get("output", "")).upper()
    if output:
        RECIPES_BY_OUTPUT[output].append(recipe)
    for variant in recipe.get("output_variants", []) or []:
        output = str(variant.get("output", "")).upper()
        if output and recipe not in RECIPES_BY_OUTPUT[output]:
            RECIPES_BY_OUTPUT[output].append(recipe)
    for weighted in recipe.get("weighted_outputs", []) or []:
        output = str(weighted.get("output", "")).upper()
        if output:
            RECIPES_BY_OUTPUT[output].append(recipe)
    for rule in recipe.get("rules", []) or []:
        for action in rule.get("actions", []) or []:
            if str(action.get("type", "")).upper() != "SET_VISUAL_ITEM":
                continue
            visual = str(action.get("value", "")).upper()
            output = ITEM_ID_BY_VISUAL_ID.get(visual, visual)
            if output in ITEM_BY_ID and recipe not in RECIPES_BY_OUTPUT[output]:
                RECIPES_BY_OUTPUT[output].append(recipe)


def collect_vanilla_item_ids() -> set[str]:
    ids: set[str] = set()
    for item in ITEMS:
        base = str(item.get("base_material", "")).upper()
        if base and base != "PLAYER_HEAD":
            ids.add(base)
    for recipe in RECIPES:
        for slot in recipe.get("ingredients", []) or []:
            for option in slot.get("options", []) or []:
                if "item" in option:
                    ids.add(str(option["item"]).upper())
    return {iid for iid in ids if iid and iid not in ITEM_BY_ID}


VANILLA_ITEM_IDS = collect_vanilla_item_ids()


WIKI_VISUAL_PREVIEW_PACKS = {"Heirloom-Asian-Food-Pack-v1.0.0"}


def load_local_visual_pack_icons() -> dict[str, tuple[str, Path]]:
    icons: dict[str, tuple[str, Path]] = {}
    packs_root = PLUGIN_ROOT / "packs"
    if not packs_root.exists():
        return icons
    for png in packs_root.glob("*/shared/assets/heirloom/textures/item/*.png"):
        pack_name = png.relative_to(packs_root).parts[0]
        icons[png.stem.upper()] = (pack_name, png)
    for png in packs_root.glob("*/textures/*.png"):
        pack_name = png.relative_to(packs_root).parts[0]
        icons[png.stem.upper()] = (pack_name, png)
    return icons


LOCAL_VISUAL_PACK_ICONS = load_local_visual_pack_icons()


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PLAYER_HEAD_RENDER_STYLE = "player_head_isometric_v2_80"
MINECRAFT_VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
MINECRAFT_RESOURCE_BASE = "https://resources.download.minecraft.net"
MINECRAFT_ASSET_VERSION_ENV = "HEIRLOOM_MINECRAFT_ASSET_VERSION"


MARKETING_IMAGE_ASSETS = {
    "station-oven": {"source": "station+oven.png", "target": "images/stations/oven", "max_width": 1400},
    "station-boiling-pot": {"source": "station boiling pot.png", "target": "images/stations/boiling-pot", "max_width": 1400},
    "station-mixing-bowl": {"source": "station+mixing+bowl.png", "target": "images/stations/mixing-bowl", "max_width": 1400},
    "station-cutting-board": {"source": "station+cuttingboard.png", "target": "images/stations/cutting-board", "max_width": 1400},
    "station-frying-pan": {"source": "station+frying+table.png", "target": "images/stations/frying-pan", "max_width": 1400},
    "station-barista-machine": {"source": "station-baristamachine.png", "target": "images/stations/barista-machine", "max_width": 1400},
    "crop-lettuce": {"source": "plant+lettuce.png", "target": "images/gardening/lettuce", "max_width": 1400},
    "crop-onion": {"source": "plant+onion.png", "target": "images/gardening/onion", "max_width": 1400},
    "crop-corn": {"source": "plant+cornfield.png", "target": "images/gardening/corn", "max_width": 1400},
    "crop-tomato": {"source": "plant+tomato.png", "target": "images/gardening/tomato", "max_width": 1400},
    "crop-rice": {"source": "plant+ricefield.png", "target": "images/gardening/rice", "max_width": 1400},
    "recipe-search-chat": {"source": "hl+search+chat.png", "target": "images/showcase/recipe-search-chat", "max_width": 1200},
    "recipe-search-gui": {"source": "hl+search+gui.png", "target": "images/showcase/recipe-search-gui", "max_width": 1200},
    "install-plugin-overview": {"source": "installation+pic1.png", "target": "images/showcase/install-plugin-overview", "max_width": 1200},
    "install-generated-files": {"source": "installation+pic+better.png", "target": "images/showcase/install-generated-files", "max_width": 1200},
    "first-meal-build-station": {"source": "getstarted-place-furnace-iron.png", "target": "images/showcase/first-meal-build-station", "max_width": 1400},
    "first-meal-place-egg": {"source": "getstarted-place-egg.png", "target": "images/showcase/first-meal-place-egg", "max_width": 1400},
    "first-meal-cooking-progress": {"source": "getstarted-egg-frying.png", "target": "images/showcase/first-meal-cooking-progress", "max_width": 1400},
    "first-meal-finished": {"source": "getstarted+egg+finished.png", "target": "images/showcase/first-meal-finished", "max_width": 1400},
    "first-meal-wrong-furnace": {"source": "getstarted-cant-use-regular-furnace-better.png", "target": "images/showcase/first-meal-wrong-furnace", "max_width": 1200},
    "food-quality-tooltip": {"source": "quality.png", "target": "images/showcase/food-quality-tooltip", "max_width": 900},
}


def should_update_asset(source: Path, target: Path) -> bool:
    if not target.exists() or target.stat().st_size == 0:
        return True
    return source.stat().st_mtime > target.stat().st_mtime


def convert_marketing_asset(source: Path, target_base: Path, max_width: int) -> None:
    webp_target = target_base.with_suffix(".webp")
    webp_target.parent.mkdir(parents=True, exist_ok=True)
    cwebp = shutil.which("cwebp")
    if cwebp and should_update_asset(source, webp_target):
        cmd = [cwebp, "-quiet", "-q", "82"]
        dimensions = png_dimensions(source)
        if dimensions and dimensions[0] > max_width:
            cmd += ["-resize", str(max_width), "0"]
        cmd += [str(source), "-o", str(webp_target)]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode == 0 and webp_target.exists() and webp_target.stat().st_size > 0:
            return

    png_target = target_base.with_suffix(".png")
    if not should_update_asset(source, png_target):
        return
    sips = shutil.which("sips")
    dimensions = png_dimensions(source)
    if sips and dimensions and dimensions[0] > max_width:
        result = subprocess.run(
            [sips, "-Z", str(max_width), str(source), "--out", str(png_target)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0 and png_target.exists() and png_target.stat().st_size > 0:
            return
    shutil.copy2(source, png_target)


def sync_marketing_images() -> None:
    source_root = PLUGIN_ROOT / "marketing/wikiimgs"
    if not source_root.exists():
        return
    for config in MARKETING_IMAGE_ASSETS.values():
        source = source_root / config["source"]
        if not source.exists():
            continue
        target_base = DOCS_ROOT / "docs" / config["target"]
        convert_marketing_asset(source, target_base, int(config.get("max_width", 1400)))


def source_logo_specs() -> dict[str, tuple[str, Path]]:
    exports = PLUGIN_ROOT / "logo/exports"
    core_logo = PLUGIN_ROOT / "logo/heirloom-logo.png"
    specs = {
        "Core": ("core.png", core_logo),
        "World": ("core.png", core_logo),
        "Festive": ("core.png", core_logo),
        "Cafe": ("cafe.png", exports / "heirloom-cafe-logo-transparent.png"),
        "Distillery": ("distillery.png", exports / "heirloom-distillery-logo-transparent.png"),
        "Pasture": ("core.png", core_logo),
        "Orchard": ("mixology.png", exports / "heirloom-mixology-logo-transparent.png"),
    }
    for pack in CONTENT_PACKS:
        if pack["id"] == "heirloom_asian_food":
            specs[pack["name"]] = (
                "heirloom-asian-food-pack.png",
                exports / "heirloom-chinese-japanese-food-pack-transparent.png",
            )
            continue
        if pack["id"] == "heirloom_american_food":
            specs[pack["name"]] = (
                "heirloom-american-food-pack.png",
                exports / "heirloom-american-food-food-pack-transparent.png",
            )
            continue
        pack_slug = slug(pack["name"])
        for candidate in (
            exports / f"{pack_slug}-transparent.png",
            exports / f"{pack_slug}-marketplace.png",
        ):
            if candidate.is_file():
                specs[pack["name"]] = (f"{pack_slug}.png", candidate)
                break
    return specs


def sync_source_logos() -> None:
    SOURCE_LOGO_MANIFEST.clear()
    target_root = DOCS_ROOT / "docs/images/sources"
    target_root.mkdir(parents=True, exist_ok=True)
    active_filenames: set[str] = set()
    for source, (filename, logo_source) in source_logo_specs().items():
        if not logo_source.is_file():
            continue
        target = target_root / filename
        if filename not in active_filenames:
            write_logo_thumbnail(logo_source, target)
            active_filenames.add(filename)
        SOURCE_LOGO_MANIFEST[source] = f"images/sources/{filename}"
    for stale in target_root.glob("*.png"):
        if stale.name not in active_filenames:
            stale.unlink()


def sync_mixology_branding() -> None:
    source = PLUGIN_ROOT / "logo/exports/heirloom-mixology-banner-marketplace.png"
    if source.is_file():
        convert_marketing_asset(source, DOCS_ROOT / "docs/images/addons/mixology/banner", 1600)


def sync_addon_release_banners() -> None:
    for addon in ("cafe", "distillery"):
        source = PLUGIN_ROOT / "logo/exports" / f"heirloom-{addon}-banner-marketplace.png"
        if not source.is_file():
            continue
        target = DOCS_ROOT / "docs/images/addons" / addon / "banner.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != source.read_bytes():
            shutil.copyfile(source, target)


def mixology_branding() -> str:
    for ext in ("webp", "png"):
        src = f"../../images/addons/mixology/banner.{ext}"
        if docs_image_exists(src):
            return image(src, "Cocktails, Juices & Fruit Trees", "Heirloom Mixology graphic banner")
    return ""


def marketing_asset_rel(key: str) -> str | None:
    config = MARKETING_IMAGE_ASSETS.get(key)
    if not config:
        return None
    for ext in (".webp", ".png"):
        rel = f"{config['target']}{ext}"
        if (DOCS_ROOT / "docs" / rel).exists():
            return rel
    return None


def marketing_asset_src(key: str, prefix: str) -> str | None:
    rel = marketing_asset_rel(key)
    if not rel:
        return None
    return f"{prefix}{rel}"


def attr(value) -> str:
    return html.escape(str(value), quote=True)


def source_badge(source: str, image_prefix: str = "../") -> str:
    logo = SOURCE_LOGO_MANIFEST.get(source)
    display_name = "Heirloom Mixology" if source == "Orchard" else source
    if not logo:
        return md_escape(display_name)
    label = attr(display_name)
    return (
        f'<span class="hl-source-badge" title="{label}">'
        f'<img class="hl-source-logo" src="{image_prefix}{logo}" alt="{label}">'
        f'</span>'
    )


def read_png_rgba(data: bytes) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a png")
    pos = len(PNG_SIGNATURE)
    width = height = color_type = bit_depth = None
    palette: list[tuple[int, int, int]] = []
    transparency: list[int] = []
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, _interlace = struct.unpack(">IIBBBBB", chunk)
        elif chunk_type == b"PLTE":
            palette = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk), 3)]
        elif chunk_type == b"tRNS":
            transparency = list(chunk)
        elif chunk_type == b"IDAT":
            idat.extend(chunk)
        elif chunk_type == b"IEND":
            break
    if width is None or height is None or color_type is None:
        raise ValueError("unsupported png")
    if color_type == 3:
        if bit_depth not in (1, 2, 4, 8):
            raise ValueError("unsupported indexed png bit depth")
        channels = 1
        stride = (width * bit_depth + 7) // 8
        filter_bpp = 1
    else:
        if bit_depth != 8:
            raise ValueError("unsupported png bit depth")
        channels_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
        channels = channels_by_type.get(color_type)
        if channels is None:
            raise ValueError("unsupported png color type")
        stride = width * channels
        filter_bpp = channels
    raw = zlib.decompress(bytes(idat))
    rows: list[bytearray] = []
    offset = 0
    prev = bytearray(stride)
    for _y in range(height):
        filter_type = raw[offset]
        scan = bytearray(raw[offset + 1:offset + 1 + stride])
        offset += 1 + stride
        for i, value in enumerate(scan):
            left = scan[i - filter_bpp] if i >= filter_bpp else 0
            up = prev[i]
            up_left = prev[i - filter_bpp] if i >= filter_bpp else 0
            if filter_type == 1:
                scan[i] = (value + left) & 255
            elif filter_type == 2:
                scan[i] = (value + up) & 255
            elif filter_type == 3:
                scan[i] = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                p = left + up - up_left
                pa = abs(p - left)
                pb = abs(p - up)
                pc = abs(p - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                scan[i] = (value + predictor) & 255
            elif filter_type != 0:
                raise ValueError("unsupported png filter")
        rows.append(scan)
        prev = scan
    pixels: list[tuple[int, int, int, int]] = []
    for row in rows:
        for x in range(width):
            if color_type == 3:
                if bit_depth == 8:
                    index = row[x]
                else:
                    bit_index = x * bit_depth
                    packed = row[bit_index // 8]
                    shift = 8 - bit_depth - (bit_index % 8)
                    index = (packed >> shift) & ((1 << bit_depth) - 1)
                r, g, b = palette[index] if index < len(palette) else (0, 0, 0)
                a = transparency[index] if index < len(transparency) else 255
                pixels.append((r, g, b, a))
                continue
            i = x * channels
            if color_type == 6:
                pixels.append((row[i], row[i + 1], row[i + 2], row[i + 3]))
            elif color_type == 2:
                pixels.append((row[i], row[i + 1], row[i + 2], 255))
            elif color_type == 4:
                pixels.append((row[i], row[i], row[i], row[i + 1]))
            else:
                pixels.append((row[i], row[i], row[i], 255))
    return width, height, pixels


def write_png_rgba(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for r, g, b, a in pixels[y * width:(y + 1) * width]:
            rows.extend([r, g, b, a])
    data = PNG_SIGNATURE
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    data += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_logo_thumbnail(source: Path, target: Path, size: int = 96) -> None:
    width, height, pixels = read_png_rgba(source.read_bytes())
    output: list[tuple[int, int, int, int]] = []
    for y in range(size):
        source_y = min(height - 1, int((y + 0.5) * height / size))
        for x in range(size):
            source_x = min(width - 1, int((x + 0.5) * width / size))
            output.append(pixels[source_y * width + source_x])
    write_png_rgba(target, size, size, output)


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        width, height, _pixels = read_png_rgba(path.read_bytes())
        return width, height
    except Exception:
        return None


def blend_pixel(base: tuple[int, int, int, int], overlay: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    if overlay[3] <= 0:
        return base
    if overlay[3] >= 255:
        return overlay
    alpha = overlay[3] / 255
    inv = 1 - alpha
    out_a = overlay[3] + base[3] * inv
    if out_a <= 0:
        return (0, 0, 0, 0)
    return (
        int((overlay[0] * alpha + base[0] * inv)),
        int((overlay[1] * alpha + base[1] * inv)),
        int((overlay[2] * alpha + base[2] * inv)),
        int(min(255, out_a)),
    )


def shade_pixel(pixel: tuple[int, int, int, int], factor: float) -> tuple[int, int, int, int]:
    if pixel[3] <= 0:
        return pixel
    return (
        max(0, min(255, int(pixel[0] * factor))),
        max(0, min(255, int(pixel[1] * factor))),
        max(0, min(255, int(pixel[2] * factor))),
        pixel[3],
    )


def extract_skin_face(width: int, height: int, pixels: list[tuple[int, int, int, int]], x0: int, y0: int, size: int) -> list[tuple[int, int, int, int]]:
    face: list[tuple[int, int, int, int]] = []
    for y in range(size):
        for x in range(size):
            px = x0 + x
            py = y0 + y
            if 0 <= px < width and 0 <= py < height:
                face.append(pixels[py * width + px])
            else:
                face.append((0, 0, 0, 0))
    return face


def merge_face_overlay(base: list[tuple[int, int, int, int]], overlay: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    return [blend_pixel(base_pixel, overlay_pixel) for base_pixel, overlay_pixel in zip(base, overlay)]


def draw_rgba_pixel(canvas: list[tuple[int, int, int, int]], width: int, height: int, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if color[3] <= 0 or not (0 <= x < width and 0 <= y < height):
        return
    idx = y * width + x
    canvas[idx] = blend_pixel(canvas[idx], color)


def point_in_polygon(px: float, py: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi
        if intersects:
            inside = not inside
        j = i
    return inside


def fill_polygon(canvas: list[tuple[int, int, int, int]], width: int, height: int, polygon: list[tuple[float, float]], color: tuple[int, int, int, int]) -> None:
    min_x = max(0, int(min(x for x, _y in polygon)) - 1)
    max_x = min(width - 1, int(max(x for x, _y in polygon)) + 1)
    min_y = max(0, int(min(y for _x, y in polygon)) - 1)
    max_y = min(height - 1, int(max(y for _x, y in polygon)) + 1)
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if point_in_polygon(x + 0.5, y + 0.5, polygon):
                draw_rgba_pixel(canvas, width, height, x, y, color)


def interp_quad(tl: tuple[float, float], tr: tuple[float, float], br: tuple[float, float], bl: tuple[float, float], u: float, v: float) -> tuple[float, float]:
    return (
        (1 - u) * (1 - v) * tl[0] + u * (1 - v) * tr[0] + u * v * br[0] + (1 - u) * v * bl[0],
        (1 - u) * (1 - v) * tl[1] + u * (1 - v) * tr[1] + u * v * br[1] + (1 - u) * v * bl[1],
    )


def draw_textured_quad(
    canvas: list[tuple[int, int, int, int]],
    width: int,
    height: int,
    face: list[tuple[int, int, int, int]],
    face_size: int,
    corners: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]],
    shade: float,
) -> None:
    tl, tr, br, bl = corners
    for y in range(face_size):
        for x in range(face_size):
            color = shade_pixel(face[y * face_size + x], shade)
            if color[3] <= 0:
                continue
            u0, v0 = x / face_size, y / face_size
            u1, v1 = (x + 1) / face_size, (y + 1) / face_size
            polygon = [
                interp_quad(tl, tr, br, bl, u0, v0),
                interp_quad(tl, tr, br, bl, u1, v0),
                interp_quad(tl, tr, br, bl, u1, v1),
                interp_quad(tl, tr, br, bl, u0, v1),
            ]
            fill_polygon(canvas, width, height, polygon, color)


def fallback_square_face(width: int, height: int, pixels: list[tuple[int, int, int, int]], size: int = 8) -> list[tuple[int, int, int, int]]:
    face_size = min(width, height)
    face_x = max((width - face_size) // 2, 0)
    face_y = max((height - face_size) // 2, 0)
    face: list[tuple[int, int, int, int]] = []
    for y in range(size):
        sy = face_y + y * face_size // size
        for x in range(size):
            sx = face_x + x * face_size // size
            face.append(pixels[sy * width + sx])
    return face


def render_isometric_head_icon(data: bytes, size: int = 80) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    width, height, pixels = read_png_rgba(data)
    unit = 8 if width >= 64 and height >= 16 else min(8, width, height)
    if width >= 64 and height >= 16:
        front = extract_skin_face(width, height, pixels, unit, unit, unit)
        top = extract_skin_face(width, height, pixels, unit, 0, unit)
        side = extract_skin_face(width, height, pixels, unit * 2, unit, unit)
        if width >= unit * 7 and height >= unit * 2:
            front = merge_face_overlay(front, extract_skin_face(width, height, pixels, unit * 5, unit, unit))
            top = merge_face_overlay(top, extract_skin_face(width, height, pixels, unit * 5, 0, unit))
            side = merge_face_overlay(side, extract_skin_face(width, height, pixels, unit * 6, unit, unit))
    else:
        front = fallback_square_face(width, height, pixels, unit)
        top = front
        side = front
    canvas = [(0, 0, 0, 0)] * (size * size)
    scale = size / 40
    def p(x: float, y: float) -> tuple[float, float]:
        return (x * scale, y * scale)
    # Front-facing cube with visible top and right side; source renders large enough for 48px wiki slots.
    top_quad = (p(7, 13), p(27, 13), p(32, 8), p(12, 8))
    side_quad = (p(27, 13), p(32, 8), p(32, 28), p(27, 33))
    front_quad = (p(7, 13), p(27, 13), p(27, 33), p(7, 33))
    draw_textured_quad(canvas, size, size, top, unit, top_quad, 1.08)
    draw_textured_quad(canvas, size, size, side, unit, side_quad, 0.78)
    draw_textured_quad(canvas, size, size, front, unit, front_quad, 1.0)
    return size, size, canvas


def write_system_icon(path: Path, fill: tuple[int, int, int, int], accent: tuple[int, int, int, int]) -> None:
    size = 32
    pixels: list[tuple[int, int, int, int]] = []
    for y in range(size):
        for x in range(size):
            border = x in (0, size - 1) or y in (0, size - 1)
            diagonal = abs(x - y) <= 1 or abs((size - 1 - x) - y) <= 1
            pixels.append(accent if border or diagonal else fill)
    write_png_rgba(path, size, size, pixels)


def fetch_binary(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Heirloom-Wiki-Icon-Generator/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_binary(url).decode("utf-8"))


def existing_manifest_entry(item_id: str) -> dict:
    return (EXISTING_ICON_MANIFEST.get("items") or {}).get(item_id.upper(), {})


def resolve_minecraft_asset_index() -> tuple[str | None, dict[str, dict]]:
    global MINECRAFT_ASSET_INDEX, MINECRAFT_ASSET_VERSION
    if MINECRAFT_ASSET_INDEX is not None:
        return MINECRAFT_ASSET_VERSION, MINECRAFT_ASSET_INDEX
    version_override = os.environ.get(MINECRAFT_ASSET_VERSION_ENV)
    manifest = fetch_json(MINECRAFT_VERSION_MANIFEST_URL)
    version_id = version_override or manifest.get("latest", {}).get("release")
    version_url = None
    for version in manifest.get("versions", []):
        if version.get("id") == version_id:
            version_url = version.get("url")
            break
    if not version_url:
        raise RuntimeError(f"Minecraft asset version not found: {version_id}")
    version_data = fetch_json(version_url)
    asset_url = version_data.get("assetIndex", {}).get("url")
    if not asset_url:
        raise RuntimeError(f"Minecraft asset index missing for {version_id}")
    asset_index = fetch_json(asset_url).get("objects", {})
    MINECRAFT_ASSET_INDEX = asset_index
    MINECRAFT_ASSET_VERSION = version_id
    return MINECRAFT_ASSET_VERSION, MINECRAFT_ASSET_INDEX


def minecraft_asset_candidates(item_id: str) -> list[str]:
    name = item_id.lower()
    aliases = {
        "cactus": ["block/cactus_side.png"],
        "water_bottle": ["item/potion.png"],
        "enchanted_golden_apple": ["item/golden_apple.png"],
        "knowledge_book": ["item/knowledge_book.png"],
        "leaf_litter": ["item/leaf_litter.png", "block/leaf_litter.png"],
        "lilac": ["block/lilac_top.png"],
        "peony": ["block/peony_top.png"],
        "pumpkin": ["block/pumpkin_side.png"],
        "rose_bush": ["block/rose_bush_top.png"],
        "sunflower": ["block/sunflower_front.png"],
    }
    paths: list[str] = []
    for alias in aliases.get(name, []):
        paths.append(f"minecraft/textures/{alias}")
    paths.extend([
        f"minecraft/textures/item/{name}.png",
        f"minecraft/textures/block/{name}.png",
    ])
    unique: list[str] = []
    for candidate in paths:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def fetch_minecraft_asset(asset_path: str, asset_index: dict[str, dict]) -> bytes | None:
    entry = asset_index.get(asset_path)
    if not entry:
        return None
    digest = entry.get("hash")
    if not digest:
        return None
    return fetch_binary(f"{MINECRAFT_RESOURCE_BASE}/{digest[:2]}/{digest}")


def resolve_minecraft_client_jar() -> tuple[str | None, zipfile.ZipFile]:
    global MINECRAFT_CLIENT_JAR, MINECRAFT_ASSET_VERSION
    if MINECRAFT_CLIENT_JAR is not None:
        return MINECRAFT_ASSET_VERSION, MINECRAFT_CLIENT_JAR
    version_override = os.environ.get(MINECRAFT_ASSET_VERSION_ENV)
    manifest = fetch_json(MINECRAFT_VERSION_MANIFEST_URL)
    version_id = version_override or manifest.get("latest", {}).get("release")
    version_url = None
    for version in manifest.get("versions", []):
        if version.get("id") == version_id:
            version_url = version.get("url")
            break
    if not version_url:
        raise RuntimeError(f"Minecraft client version not found: {version_id}")
    version_data = fetch_json(version_url)
    client_url = version_data.get("downloads", {}).get("client", {}).get("url")
    if not client_url:
        raise RuntimeError(f"Minecraft client jar missing for {version_id}")
    MINECRAFT_CLIENT_JAR = zipfile.ZipFile(io.BytesIO(fetch_binary(client_url)))
    MINECRAFT_ASSET_VERSION = version_id
    return MINECRAFT_ASSET_VERSION, MINECRAFT_CLIENT_JAR


def fetch_minecraft_texture_from_client(asset_path: str, client_jar: zipfile.ZipFile) -> bytes | None:
    jar_path = f"assets/{asset_path}"
    try:
        return client_jar.read(jar_path)
    except KeyError:
        return None


def record_missing(kind: str, item_id: str, reason: str) -> None:
    normalized = item_id.upper() if kind != "tag" else item_id
    if any(existing_kind == kind and existing_id == normalized for existing_kind, existing_id, _reason in MISSING_ICON_ROWS):
        return
    MISSING_ICON_ROWS.append((kind, normalized, reason))


def texture_hash(texture_url: str) -> str:
    return texture_url.rstrip("/").split("/")[-1]


def icon_rel_for_custom(item_id: str) -> str:
    return f"images/items/heirloom/{slug(item_id)}.png"


def icon_rel_for_vanilla(item_id: str) -> str:
    return f"images/items/minecraft/{slug(item_id)}.png"


def icon_rel_for_visual_pack(item_id: str) -> str:
    return f"images/items/visual-pack/{slug(item_id)}.png"


def write_public_visual_preview(source: Path, target: Path) -> None:
    """Render a crisp, nearly front-facing relief tile without publishing source pixels."""
    width, height, pixels = read_png_rgba(source.read_bytes())
    output_size = 63
    paper = (255, 253, 245, 255)
    canvas = [paper] * (output_size * output_size)
    scale = max(1, 48 // max(width, height))
    front_width = width * scale
    front_height = height * scale
    depth = 3
    origin_x = (output_size - front_width - depth) // 2
    origin_y = (output_size - front_height - depth) // 2

    def blend_pixel(x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if not (0 <= x < output_size and 0 <= y < output_size):
            return
        red, green, blue, alpha = color
        opacity = alpha / 255
        background = canvas[y * output_size + x]
        canvas[y * output_size + x] = (
            round(red * opacity + background[0] * (1 - opacity)),
            round(green * opacity + background[1] * (1 - opacity)),
            round(blue * opacity + background[2] * (1 - opacity)),
            255,
        )

    def draw_block(x: int, y: int, color: tuple[int, int, int, int]) -> None:
        for pixel_y in range(y, y + scale):
            for pixel_x in range(x, x + scale):
                blend_pixel(pixel_x, pixel_y, color)

    # A shallow lower-right extrusion provides depth while keeping the face almost flat.
    for offset in range(depth, 0, -1):
        for source_y in range(height):
            for source_x in range(width):
                red, green, blue, alpha = pixels[source_y * width + source_x]
                if alpha == 0:
                    continue
                draw_block(
                    origin_x + source_x * scale + offset,
                    origin_y + source_y * scale + offset,
                    (round(red * 0.48), round(green * 0.48), round(blue * 0.48), alpha),
                )

    for source_y in range(height):
        for source_x in range(width):
            red, green, blue, alpha = pixels[source_y * width + source_x]
            if alpha == 0:
                continue
            block_x = origin_x + source_x * scale
            block_y = origin_y + source_y * scale
            draw_block(block_x, block_y, (red, green, blue, alpha))

            above_clear = source_y == 0 or pixels[(source_y - 1) * width + source_x][3] == 0
            left_clear = source_x == 0 or pixels[source_y * width + source_x - 1][3] == 0
            highlight = (
                round(red + (255 - red) * 0.14),
                round(green + (255 - green) * 0.14),
                round(blue + (255 - blue) * 0.14),
                alpha,
            )
            if above_clear:
                for pixel_x in range(block_x, block_x + scale):
                    blend_pixel(pixel_x, block_y, highlight)
            if left_clear:
                for pixel_y in range(block_y, block_y + scale):
                    blend_pixel(block_x, pixel_y, highlight)

    write_png_rgba(target, output_size, output_size, canvas)


def icon_rel_for_recipe_variant(texture_url: str) -> str:
    return f"images/items/recipe-variants/{texture_hash(texture_url)}.png"


def resolve_visual_item_id(value: str) -> str:
    upper = str(value).upper()
    if upper in ITEM_BY_ID:
        return upper
    return ITEM_ID_BY_VISUAL_ID.get(upper, upper)


def output_name_after_actions(actions: list[dict], fallback: str) -> str:
    name = fallback
    for action in actions or []:
        action_type = str(action.get("type", "")).upper()
        if action_type == "SET_PROPERTY" and str(action.get("key", "")).upper() == "NAME":
            name = str(action.get("value", name))
        elif action_type == "PREPEND_NAME":
            name = str(action.get("value", "")) + name
        elif action_type == "APPEND_NAME":
            name = name + str(action.get("value", ""))
    return " ".join(name.split()) or fallback


def output_visual_source_from_actions(actions: list[dict]) -> tuple[str, str] | None:
    source = None
    visual_source = None
    for action in actions or []:
        action_type = str(action.get("type", "")).upper()
        value = str(action.get("value", "")).strip()
        if not value:
            continue
        if action_type == "SET_TEXTURE":
            source = ("texture", value)
        elif action_type == "SET_VISUAL_ITEM":
            item_id = resolve_visual_item_id(value)
            visual_source = ("item", item_id)
            if item_id in ITEM_BY_ID or source is None:
                source = ("item", item_id)
    if USE_VISUAL_PACK_ICONS and visual_source and visual_source[1] in LOCAL_VISUAL_PACK_ICONS:
        return visual_source
    return source


def output_item_visual_key(item_id: str) -> str:
    upper = item_id.upper()
    item = ITEM_BY_ID.get(upper)
    if item and item.get("texture"):
        return f"texture:{texture_hash(str(item["texture"]))}"
    return f"item:{upper}"


def output_variant_key(source: tuple[str, str]) -> str:
    source_type, value = source
    if source_type == "texture":
        return f"texture:{texture_hash(value)}"
    return output_item_visual_key(resolve_visual_item_id(value))


def output_variant_from_source(source: tuple[str, str], label: str) -> dict:
    source_type, value = source
    if source_type == "texture":
        return {
            "kind": "texture",
            "texture": value,
            "key": output_variant_key(source),
            "label": label,
        }
    item_id = resolve_visual_item_id(value)
    return {
        "kind": "item",
        "item_id": item_id,
        "key": output_variant_key(("item", item_id)),
        "label": label,
    }


def rule_matcher_label(rule: dict) -> str:
    matcher = rule.get("matcher") or {}
    for key in ("custom_item", "item"):
        if key in matcher:
            return title_from_id(str(matcher[key]).upper())
    matchers = rule.get("matchers") or []
    if matchers:
        labels = []
        for matcher in matchers:
            for key in ("custom_item", "item"):
                if key in matcher:
                    labels.append(title_from_id(str(matcher[key]).upper()))
                    break
        if labels:
            return " + ".join(labels)
    return ""


def recipe_output_variant_data(recipe: dict | None) -> list[dict]:
    if not recipe:
        return []
    output_id = str(recipe.get("output", "")).upper()
    if not output_id:
        return []
    fallback_name = ITEM_BY_ID.get(output_id, {}).get("name", title_from_id(output_id))
    base_name = output_name_after_actions(recipe.get("actions", []) or [], fallback_name)
    base_source = output_visual_source_from_actions(recipe.get("actions", []) or []) or ("item", output_id)

    variants: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add_variant(source: tuple[str, str], label: str) -> None:
        variant = output_variant_from_source(source, label)
        identity = (variant["key"], label.removeprefix("Default "))
        if identity in seen:
            return
        seen.add(identity)
        variants.append(variant)

    add_variant(base_source, f"Default {base_name}")
    for declared in recipe.get("output_variants", []) or []:
        item_id = str(declared.get("output", "")).upper()
        if item_id:
            add_variant(("item", item_id), ITEM_BY_ID.get(item_id, {}).get("name", title_from_id(item_id)))
    for rule in recipe.get("rules", []) or []:
        actions = rule.get("actions", []) or []
        source = output_visual_source_from_actions(actions)
        if not source:
            continue
        label = output_name_after_actions(actions, base_name)
        explicit_name = any(str(action.get("type", "")).upper() == "SET_PROPERTY"
                            and str(action.get("key", "")).upper() == "NAME" for action in actions)
        if label == base_name and not explicit_name:
            matcher_label = rule_matcher_label(rule)
            label = f"{matcher_label} {base_name}" if matcher_label else f"Variant {len(variants) + 1}"
        add_variant(source, label)
    return variants


def ensure_recipe_variant_texture_icon(texture_url: str, fetch_icons: bool, label: str = "recipe variant") -> None:
    key = texture_hash(texture_url)
    rel = icon_rel_for_recipe_variant(texture_url)
    target = DOCS_ROOT / "docs" / rel
    previous = EXISTING_ICON_MANIFEST.get("recipe_variants", {}).get(key, {})
    should_refresh = fetch_icons and previous.get("render_style") != PLAYER_HEAD_RENDER_STYLE
    if fetch_icons and (should_refresh or not target.exists()):
        try:
            w, h, pixels = render_isometric_head_icon(fetch_binary(texture_url))
            write_png_rgba(target, w, h, pixels)
        except Exception:
            if not target.exists():
                record_missing("recipe_variant", key, f"remote player-head fetch unavailable for {label}; add local variant icon")
    if target.exists():
        RECIPE_VARIANT_MANIFEST[key] = {
            "path": rel,
            "source_kind": "recipe_set_texture",
            "source_url": texture_url,
            "render_style": PLAYER_HEAD_RENDER_STYLE,
            "status": "ok",
        }
        return
    record_missing("recipe_variant", key, f"no cached recipe variant icon for {label}")
    RECIPE_VARIANT_MANIFEST[key] = {
        "path": "images/items/system/missing.png",
        "source_kind": "missing",
        "source_url": texture_url,
        "render_style": "missing",
        "status": "missing",
    }


def ensure_recipe_variant_assets(fetch_icons: bool) -> None:
    RECIPE_VARIANT_MANIFEST.clear()
    (DOCS_ROOT / "docs/images/items/recipe-variants").mkdir(parents=True, exist_ok=True)
    for recipe in RECIPES:
        for variant in recipe_output_variant_data(recipe):
            if variant.get("kind") == "texture":
                ensure_recipe_variant_texture_icon(str(variant["texture"]), fetch_icons, str(variant.get("label", "recipe variant")))


def ensure_custom_icon(item: dict, fetch_icons: bool, use_visual_pack_icons: bool = False) -> None:
    item_id = str(item.get("id", "")).upper()
    if not item_id:
        return
    texture = item.get("texture")
    base = str(item.get("base_material", "")).upper()
    model = str(item.get("item_model", ""))
    if model.startswith("minecraft:"):
        base = model.split(":", 1)[1].upper()
    previous = existing_manifest_entry(item_id)
    local_visual = LOCAL_VISUAL_PACK_ICONS.get(item_id)
    pack_name, local_pack_icon = local_visual if local_visual else ("", Path())
    if (
        use_visual_pack_icons
        and pack_name in WIKI_VISUAL_PREVIEW_PACKS
        and local_pack_icon.is_file()
    ):
        rel = icon_rel_for_visual_pack(item_id)
        target = DOCS_ROOT / "docs" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        write_public_visual_preview(local_pack_icon, target)
        ICON_MANIFEST[item_id] = {
            "path": rel,
            "source": f"visual_pack:{local_pack_icon.relative_to(PLUGIN_ROOT)}",
            "source_kind": "visual_pack",
            "source_url": "",
            "render_style": "protected_preview_63_front_relief",
            "minecraft_asset_version": "",
            "status": "ok",
        }
        return
    rel = icon_rel_for_custom(item_id)
    target = DOCS_ROOT / "docs" / rel
    if texture:
        should_refresh = fetch_icons and (
            previous.get("render_style") != PLAYER_HEAD_RENDER_STYLE
            or previous.get("source_kind") != "player_head_texture"
            or previous.get("source_url") != texture
        )
        if fetch_icons and (should_refresh or not target.exists()):
            try:
                w, h, pixels = render_isometric_head_icon(fetch_binary(texture))
                write_png_rgba(target, w, h, pixels)
            except Exception:  # noqa: BLE001 - generator should keep building docs
                if not target.exists():
                    record_missing("custom", item_id, "remote player-head fetch unavailable; add local icon")
        if target.exists():
            dimensions = png_dimensions(target)
            ICON_MANIFEST[item_id] = {
                "path": rel,
                "source": "player_head",
                "source_kind": "player_head_texture",
                "source_url": texture,
                "render_style": PLAYER_HEAD_RENDER_STYLE if dimensions == (80, 80) else previous.get("render_style", "cached_player_head"),
                "minecraft_asset_version": "",
                "status": "ok",
            }
            return
    if model == "minecraft:lingering_potion" and item.get("color"):
        ensure_vanilla_icon("LINGERING_POTION", fetch_icons)
        ensure_vanilla_icon("POTION_OVERLAY", fetch_icons)
        bottle = DOCS_ROOT / "docs" / icon_rel_for_vanilla("LINGERING_POTION")
        overlay = DOCS_ROOT / "docs" / icon_rel_for_vanilla("POTION_OVERLAY")
        if bottle.is_file() and overlay.is_file():
            width, height, pixels = read_png_rgba(bottle.read_bytes())
            ow, oh, mask = read_png_rgba(overlay.read_bytes())
            color = str(item["color"]).removeprefix("#")
            if (ow, oh) == (width, height) and re.fullmatch(r"[0-9a-fA-F]{6}", color):
                rgb = tuple(int(color[index:index + 2], 16) for index in (0, 2, 4))
                tinted = []
                for background, foreground in zip(mask, pixels):
                    liquid = tuple(background[channel] * rgb[channel] // 255 for channel in range(3))
                    alpha = foreground[3] / 255
                    tint_alpha = background[3] / 255
                    total_alpha = alpha + tint_alpha * (1 - alpha)
                    channels = tuple(round((foreground[channel] * alpha + liquid[channel] * tint_alpha * (1 - alpha)) / total_alpha)
                                     if total_alpha else 0 for channel in range(3))
                    tinted.append((*channels, round(total_alpha * 255)))
                target.parent.mkdir(parents=True, exist_ok=True)
                write_png_rgba(target, width, height, tinted)
                ICON_MANIFEST[item_id] = {
                    "path": rel, "source": model, "source_kind": "vanilla_item_model",
                    "source_url": "", "render_style": "minecraft_tinted_potion",
                    "minecraft_asset_version": ICON_MANIFEST["LINGERING_POTION"].get("minecraft_asset_version", ""),
                    "status": "ok",
                }
                return
    if base and base != "PLAYER_HEAD":
        ensure_vanilla_icon(base, fetch_icons)
        base_entry = ICON_MANIFEST.get(base)
        if base_entry and base_entry.get("status") == "ok":
            ICON_MANIFEST[item_id] = {
                "path": base_entry["path"],
                "source": f"base_material:{base}",
                "source_kind": "base_material",
                "source_url": "",
                "render_style": base_entry.get("render_style", "minecraft_texture"),
                "minecraft_asset_version": base_entry.get("minecraft_asset_version", ""),
                "status": "ok",
            }
            return
    record_missing("custom", item_id, "no cached custom icon")
    ICON_MANIFEST[item_id] = {
        "path": "images/items/system/missing.png",
        "source": "player_head" if texture else f"base:{base}" if base else "missing",
        "source_kind": "missing",
        "source_url": texture or "",
        "render_style": "missing",
        "minecraft_asset_version": "",
        "status": "missing",
    }


def ensure_vanilla_icon(item_id: str, fetch_icons: bool) -> None:
    upper = item_id.upper()
    rel = icon_rel_for_vanilla(upper)
    target = DOCS_ROOT / "docs" / rel
    previous = existing_manifest_entry(upper)
    if target.exists():
        ICON_MANIFEST[upper] = {
            "path": rel,
            "source": previous.get("source", "minecraft_cache"),
            "source_kind": previous.get("source_kind", "minecraft_cache"),
            "source_url": previous.get("source_url", ""),
            "render_style": "minecraft_texture",
            "minecraft_asset_version": previous.get("minecraft_asset_version", "cached"),
            "status": "ok",
        }
        return
    if fetch_icons:
        try:
            version_id, client_jar = resolve_minecraft_client_jar()
            for asset_path in minecraft_asset_candidates(upper):
                data = fetch_minecraft_texture_from_client(asset_path, client_jar)
                if not data:
                    continue
                read_png_rgba(data)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                ICON_MANIFEST[upper] = {
                    "path": rel,
                    "source": f"minecraft_client:{asset_path}",
                    "source_kind": "minecraft_client",
                    "source_url": asset_path,
                    "render_style": "minecraft_texture",
                    "minecraft_asset_version": version_id or "",
                    "status": "ok",
                }
                return
        except Exception:
            record_missing("minecraft", upper, "minecraft client texture fetch unavailable")
    record_missing("minecraft", upper, "no cached vanilla icon")
    ICON_MANIFEST[upper] = {
        "path": "images/items/system/missing.png",
        "source": "minecraft",
        "source_kind": "missing",
        "source_url": "",
        "render_style": "missing",
        "minecraft_asset_version": MINECRAFT_ASSET_VERSION or previous.get("minecraft_asset_version", ""),
        "status": "missing",
    }


def ensure_icon_assets(fetch_icons: bool, use_visual_pack_icons: bool = False) -> None:
    ICON_MANIFEST.clear()
    MISSING_ICON_ROWS.clear()
    items_root = DOCS_ROOT / "docs/images/items"
    (items_root / "heirloom").mkdir(parents=True, exist_ok=True)
    (items_root / "minecraft").mkdir(parents=True, exist_ok=True)
    (items_root / "visual-pack").mkdir(parents=True, exist_ok=True)
    (items_root / "recipe-variants").mkdir(parents=True, exist_ok=True)
    (items_root / "system").mkdir(parents=True, exist_ok=True)
    write_system_icon(items_root / "system/missing.png", (245, 242, 235, 255), (198, 93, 59, 255))
    write_system_icon(items_root / "system/tag.png", (250, 248, 245, 255), (85, 107, 47, 255))
    (DOCS_ROOT / "docs/images/stations").mkdir(parents=True, exist_ok=True)
    for iid in sorted(VANILLA_ITEM_IDS):
        ensure_vanilla_icon(iid, fetch_icons)
    for item in sorted(ITEMS, key=lambda i: str(i.get("id", ""))):
        ensure_custom_icon(item, fetch_icons, use_visual_pack_icons)
    ensure_recipe_variant_assets(fetch_icons)
    active_visual_previews = {
        Path(entry["path"]).name
        for entry in ICON_MANIFEST.values()
        if entry.get("source_kind") == "visual_pack" and entry.get("path")
    }
    for preview in (items_root / "visual-pack").glob("*.png"):
        if preview.name not in active_visual_previews:
            preview.unlink()
    manifest = {
        "generated_by": "tools/generate_reference_pages.py",
        "fetch_icons": fetch_icons,
        "use_visual_pack_icons": use_visual_pack_icons,
        "minecraft_asset_version": MINECRAFT_ASSET_VERSION or EXISTING_ICON_MANIFEST.get("minecraft_asset_version", ""),
        "items": ICON_MANIFEST,
        "recipe_variants": RECIPE_VARIANT_MANIFEST,
        "missing": [
            {"kind": kind, "id": item_id, "reason": reason}
            for kind, item_id, reason in sorted(MISSING_ICON_ROWS)
        ],
    }
    (items_root / "icon-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def item_markdown_href(item_id: str, prefix: str = "../reference/") -> str | None:
    upper = item_id.upper()
    if upper in ITEM_BY_ID:
        return f"{prefix}items.md#{item_anchor(upper)}"
    if upper in VANILLA_ITEM_IDS or upper in ICON_MANIFEST:
        return f"{prefix}vanilla-items.md#{vanilla_item_anchor(upper)}"
    return None


def item_html_href(item_id: str, prefix: str = "../reference/") -> str | None:
    upper = item_id.upper()
    if upper in ITEM_BY_ID:
        return f"{prefix}items/#{item_anchor(upper)}"
    if upper in VANILLA_ITEM_IDS or upper in ICON_MANIFEST:
        return f"{prefix}vanilla-items/#{vanilla_item_anchor(upper)}"
    return None


def icon_img(item_id: str, image_prefix: str = "../", title: str | None = None, css_class: str = "") -> str:
    upper = item_id.upper()
    entry = ICON_MANIFEST.get(upper, {"path": "images/items/system/missing.png", "status": "missing"})
    classes = "hl-item-icon"
    if entry.get("status") != "ok":
        classes += " hl-icon-missing"
    if css_class:
        classes += f" {css_class}"
    label = title or upper
    return f'<img class="{classes}" src="{image_prefix}{entry["path"]}" alt="{attr(upper)}" title="{attr(label)}">'


def icon_link(item_id: str, href_prefix: str = "../reference/", image_prefix: str = "../", title: str | None = None) -> str:
    href = item_html_href(item_id, href_prefix)
    image_html = icon_img(item_id, image_prefix, title)
    if href:
        return f'<a class="hl-icon-link" href="{attr(href)}">{image_html}</a>'
    return image_html


def tag_icon(tag: str, image_prefix: str = "../", title: str | None = None) -> str:
    label = title or f"tag: {tag}"
    src = f"{image_prefix}images/items/system/tag.png"
    record_missing("tag", tag, "tag ingredients use a generic icon")
    return f'<img class="hl-item-icon hl-icon-missing" src="{src}" alt="{attr(label)}" title="{attr(label)}">'


def vanilla_item_anchor(item_id: str) -> str:
    return f"vanilla-item-{slug(item_id)}"


def recipe_anchor(recipe: dict | str) -> str:
    if isinstance(recipe, dict):
        return recipe.get("_anchor") or f"recipe-{slug(str(recipe.get('id', 'recipe')))}"
    upper = str(recipe).upper()
    found = RECIPE_BY_ID.get(upper)
    if found:
        return recipe_anchor(found)
    return f"recipe-{slug(upper)}"


def item_anchor(item_id: str) -> str:
    return f"item-{slug(item_id)}"


def crop_anchor(crop_id: str) -> str:
    return f"crop-{slug(crop_id)}"


def item_link(item_id: str, prefix: str = "../reference/") -> str:
    upper = item_id.upper()
    href = item_markdown_href(upper, prefix)
    if href:
        return f"[`{upper}`]({href})"
    return f"`{upper}`"


def recipe_link(recipe: dict | str, prefix: str = "../recipes/") -> str:
    if isinstance(recipe, dict):
        upper = str(recipe.get("id", "")).upper()
        return f"[`{upper}`]({prefix}default-recipes.md#{recipe_anchor(recipe)})"
    upper = str(recipe).upper()
    return f"[`{upper}`]({prefix}default-recipes.md#{recipe_anchor(upper)})"


def recipe_output_markdown_href(output_id: str, recipe_prefix: str = "../recipes/", reference_prefix: str = "../reference/") -> str | None:
    upper = output_id.upper()
    if upper in RECIPES_BY_OUTPUT:
        first = RECIPES_BY_OUTPUT[upper][0]
        return f"{recipe_prefix}default-recipes.md#{recipe_anchor(first)}"
    return item_markdown_href(upper, reference_prefix)


def recipe_output_html_href(output_id: str, recipe_prefix: str = "../recipes/", reference_prefix: str = "../reference/", recipe: dict | None = None) -> str | None:
    upper = output_id.upper()
    if upper in RECIPES_BY_OUTPUT:
        target_recipe = recipe or RECIPES_BY_OUTPUT[upper][0]
        anchor = recipe_anchor(target_recipe)
        if recipe_prefix == "#":
            return f"#{anchor}"
        return f"{recipe_prefix}default-recipes/#{anchor}"
    return item_html_href(upper, reference_prefix)


def recipe_output_link(output_id: str, prefix: str = "../recipes/") -> str:
    upper = output_id.upper()
    href = recipe_output_markdown_href(upper, prefix, "../reference/")
    if href:
        return f"[`{upper}`]({href})"
    return f"`{upper}`"


def variant_icon_img(variant: dict, output_id: str, image_prefix: str = "../", css_class: str = "") -> str:
    classes = "hl-item-icon"
    if css_class:
        classes += f" {css_class}"
    label = variant.get("label") or output_id.upper()
    if variant.get("kind") == "item":
        return icon_img(str(variant.get("item_id", output_id)), image_prefix, label, css_class)
    key = texture_hash(str(variant.get("texture", "")))
    entry = RECIPE_VARIANT_MANIFEST.get(key, {"path": "images/items/system/missing.png", "status": "missing"})
    if entry.get("status") != "ok":
        classes += " hl-icon-missing"
    return f'<img class="{classes}" src="{image_prefix}{entry["path"]}" alt="{attr(label)}" title="{attr(label)}">'


def output_variant_tray(variants: list[dict], output_id: str, image_prefix: str = "../") -> str:
    if len(variants) <= 1:
        return ""
    entries = []
    for variant in variants:
        icon = variant_icon_img(variant, output_id, image_prefix, "hl-output-variant-icon")
        label = variant.get("label") or output_id.upper()
        entries.append(
            f'<span class="hl-output-variant-entry">{icon}'
            f'<span class="hl-output-variant-label">{attr(label)}</span></span>'
        )
    return f'<span class="hl-output-variant-tray" role="list">{"".join(entries)}</span>'


def output_variants_detail(recipe: dict, image_prefix: str = "../") -> str:
    variants = recipe_output_variant_data(recipe)
    if len(variants) <= 1:
        return ""
    return '<span class="hl-output-variant-list">' + "".join(
        f'<span class="hl-output-variant-entry">'
        f'{variant_icon_img(variant, str(recipe.get("output", "")), image_prefix, "hl-output-variant-icon")}'
        f'<span class="hl-output-variant-label">{attr(variant.get("label") or recipe.get("output", ""))}</span></span>'
        for variant in variants
    ) + "</span>"


def output_icon_cell(output_id: str, recipe_prefix: str = "../recipes/", reference_prefix: str = "../reference/", image_prefix: str = "../", recipe: dict | None = None) -> str:
    upper = output_id.upper()
    href = recipe_output_html_href(upper, recipe_prefix, reference_prefix, recipe)
    variants = recipe_output_variant_data(recipe) if recipe else []
    primary = variants[0] if variants else {"kind": "item", "item_id": upper, "label": upper}
    visual = variant_icon_img(primary, upper, image_prefix, "hl-output-icon")
    caret = '<span class="hl-output-variant-caret" aria-hidden="true"></span>' if len(variants) > 1 else ""
    body = f'<span class="hl-output-icon-frame">{visual}{caret}</span><span class="hl-output-name">{upper}</span>'
    if href:
        output = f'<a class="hl-output-item" href="{attr(href)}">{body}</a>'
    else:
        output = f'<span class="hl-output-item">{body}</span>'
    if len(variants) > 1:
        return f'<span class="hl-output-with-variants">{output}{output_variant_tray(variants, upper, image_prefix)}</span>'
    return output


def format_options(options: list[dict], prefix: str = "../reference/") -> str:
    parts = []
    for option in options:
        rendered = None
        if "custom_item" in option:
            rendered = item_link(option["custom_item"], prefix)
        elif "custom_tag" in option:
            rendered = f"`#{option['custom_tag']}`"
        elif "item" in option:
            rendered = item_link(option["item"], prefix)
        elif "tag" in option:
            rendered = f"`#{option['tag']}`"
        if rendered is not None:
            if option.get("qualifier"):
                rendered = "**" + title_from_id(str(option["qualifier"]).split(":", 1)[-1]) + "**"
            required_property = str(option.get("required_property", "")).strip().upper()
            if required_property:
                rendered += f" carrying `{required_property}`"
            parts.append(rendered)
    return " or ".join(parts) if parts else "any"


def slot_quantity_bounds(slot: dict) -> tuple[int, int]:
    max_count = int(slot.get("max", 1) or 1)
    min_value = slot.get("min")
    slot_type = str(slot.get("type", "REQUIRED")).lower()
    if min_value is None:
        min_count = 0 if slot_type == "optional" else 1
    else:
        min_count = int(min_value)
    return min_count, max_count


def slot_quantity_text(slot: dict) -> str:
    min_count, max_count = slot_quantity_bounds(slot)
    if min_count == max_count:
        return str(max_count)
    return f"{min_count}-{max_count}"


def slot_count_badge(slot: dict) -> str:
    min_count, max_count = slot_quantity_bounds(slot)
    if min_count == max_count:
        if max_count == 1:
            return ""
        label = str(max_count)
    else:
        label = f"{min_count}-{max_count}"
    return f'<span class="hl-slot-count">{attr(label)}</span>'


def ingredient_summary(recipe: dict, prefix: str = "../reference/") -> str:
    bits = []
    for slot in recipe.get("ingredients", []) or []:
        label = slot.get("type", "REQUIRED").lower()
        count = slot_quantity_text(slot)
        bits.append(f"{label}: {count} x {format_options(slot.get('options', []), prefix)}")
    return "<br>".join(bits) if bits else "none"


def slot_count_label(slot: dict) -> str:
    return f"{str(slot.get('type', 'REQUIRED')).lower()}: {slot_quantity_text(slot)}"


def option_label(option: dict) -> str:
    if option.get("qualifier"):
        return title_from_id(str(option["qualifier"]).split(":", 1)[-1])
    if "custom_item" in option:
        label = str(option["custom_item"]).upper()
    elif "custom_tag" in option:
        label = f"#{str(option['custom_tag']).upper()}"
    elif "item" in option:
        label = str(option["item"]).upper()
    elif "tag" in option:
        label = f"#{option['tag']}"
    else:
        label = "ANY"
    required_property = str(option.get("required_property", "")).strip().upper()
    if required_property:
        label += f" ({required_property})"
    return label


def option_icon(option: dict, href_prefix: str, image_prefix: str, title: str, linked: bool = True) -> str:
    if "custom_item" in option:
        item_id = str(option["custom_item"]).upper()
        return icon_link(item_id, href_prefix, image_prefix, title) if linked else icon_img(item_id, image_prefix, title)
    if "custom_tag" in option:
        return tag_icon(str(option["custom_tag"]), image_prefix, title)
    if "item" in option:
        item_id = str(option["item"]).upper()
        return icon_link(item_id, href_prefix, image_prefix, title) if linked else icon_img(item_id, image_prefix, title)
    if "tag" in option:
        return tag_icon(str(option["tag"]), image_prefix, title)
    return tag_icon("any", image_prefix, title)


def ingredient_icon_strip(recipe: dict, href_prefix: str = "../reference/", image_prefix: str = "../") -> str:
    slots: list[str] = []
    for index, slot in enumerate(recipe.get("ingredients", []) or [], start=1):
        options = list(slot.get("options", []) or [])
        if not options:
            continue
        slot_type = str(slot.get("type", "REQUIRED")).lower()
        slot_class = "hl-slot-optional" if slot_type == "optional" else "hl-slot-required"
        quantity = slot_quantity_text(slot)
        labels = [option_label(option) for option in options]
        readable_type = "Optional" if slot_type == "optional" else "Required"
        title = f"{readable_type} slot {index}: {quantity}; " + " or ".join(labels)
        count_badge = slot_count_badge(slot)
        if len(options) == 1:
            icon = option_icon(options[0], href_prefix, image_prefix, title, linked=True)
            slots.append(
                f'<span class="hl-ingredient-slot {slot_class}" title="{attr(title)}">'
                f'<span class="hl-slot-box">{icon}{count_badge}</span>'
                f'</span>'
            )
            continue
        alternatives = []
        for option_index, option in enumerate(options):
            if option_index:
                alternatives.append('<span class="hl-choice-separator">or</span>')
            alternatives.append(option_icon(option, href_prefix, image_prefix, f"{option_label(option)} - {title}", linked=True))
        slots.append(
            f'<span class="hl-ingredient-slot {slot_class}" title="{attr(title)}">'
            f'<span class="hl-slot-box"><span class="hl-slot-choice-icons" aria-label="{attr(title)}">'
            f'{"".join(alternatives)}</span>{count_badge}</span></span>'
        )
    if not slots:
        return '<span class="hl-small">none</span>'
    return '<span class="hl-recipe-slots">' + "".join(slots) + "</span>"


def output_visual_row(recipe: dict, recipe_prefix: str = "../recipes/", reference_prefix: str = "../reference/", image_prefix: str = "../") -> str:
    return output_icon_cell(str(recipe.get("output", "")), recipe_prefix, reference_prefix, image_prefix, recipe)

def actions_summary(recipe: dict) -> str:
    actions = list(recipe.get("actions", []) or [])
    for rule in recipe.get("rules", []) or []:
        actions.extend(rule.get("actions", []) or [])
    if recipe.get("weighted_outputs"):
        weighted = ", ".join(
            f"{entry.get('output')} ({entry.get('weight')})"
            for entry in recipe.get("weighted_outputs", [])
        )
        actions.append({"type": "weighted_outputs", "value": weighted})
    useful = []
    for action in actions:
        t = action.get("type", "")
        value = action.get("value", "")
        key = action.get("key")
        if key:
            useful.append(f"`{t}` `{key}` = `{value}`")
        elif value:
            useful.append(f"`{t}` = `{value}`")
        else:
            useful.append(f"`{t}`")
    return "<br>".join(useful) if useful else "-"


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(md_escape(cell) for cell in row) + " |")
    return "\n".join(out)


PAGES: dict[str, str] = {}


def add(path: str, content: str):
    PAGES[path] = content.strip() + "\n"


def page(title: str, body: str) -> str:
    return f"# {title}\n\n{body.strip()}\n"


def image(src: str, caption: str, alt: str | None = None) -> str:
    alt = alt or caption
    return (
        f'<figure class="hl-figure">\n'
        f'  <img src="{src}" alt="{alt}">\n'
        f'  <figcaption>{caption}</figcaption>\n'
        f'</figure>'
    )




STATION_CAPTURE_TARGETS = {
    "Oven": "docs/images/stations/oven.webp",
    "Boiling Pot": "docs/images/stations/boiling-pot.webp",
    "Mixing Bowl": "docs/images/stations/mixing-bowl.webp",
    "Cutting Board": "docs/images/stations/cutting-board.webp",
    "Frying Pan": "docs/images/stations/frying-pan.webp",
    "Barista Machine": "docs/images/stations/barista-machine.webp",
}


def docs_image_exists(src: str | None) -> bool:
    if not src or re.match(r"^[a-z]+:", src):
        return False
    normalized = src
    while normalized.startswith("../"):
        normalized = normalized[3:]
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return (DOCS_ROOT / "docs" / normalized).exists()


def image_if(src: str | None, caption: str, alt: str | None = None) -> str:
    if not docs_image_exists(src):
        return ""
    return image(src or "", caption, alt)


def media_card(src: str, caption: str, alt: str | None = None, href: str | None = None) -> str:
    alt = attr(alt or caption)
    caption_attr = attr(caption)
    image_html = f'<img src="{attr(src)}" alt="{alt}">'
    if href:
        image_html = f'<a class="hl-media-link" href="{attr(href)}">{image_html}</a>'
    return f'<figure class="hl-media-card">{image_html}<figcaption>{caption_attr}</figcaption></figure>'


def media_card_if(src: str | None, caption: str, alt: str | None = None, href: str | None = None) -> str:
    if not docs_image_exists(src):
        return ""
    return media_card(src or "", caption, alt, href)


def media_grid(cards: list[str]) -> str:
    visible = [card for card in cards if card]
    if not visible:
        return ""
    return '<div class="hl-media-grid">\n' + "\n".join(f"  {card}" for card in visible) + "\n</div>"


def station_media(title: str) -> str:
    candidates: dict[str, list[tuple[str | None, str]]] = {
        "Mixology Table": [("../../images/mixology/shaker-demo.gif", "Watch ingredients become a round of cocktails at the Mixology Table.")],
        "Juicer": [("../../images/mixology/juicer-demo.gif", "Insert three produce items, blend, then bottle the juice in two pours.")],
        "Oven": [(marketing_asset_src("station-oven", "../../"), "Oven station built from a stone pressure plate on a smoker.")],
        "Boiling Pot": [
            (marketing_asset_src("station-boiling-pot", "../../"), "Boiling Pot station built over a campfire."),
            ("../../images/showcase/jam.gif", "Boiling Pot cooking flow with visible station effects."),
        ],
        "Mixing Bowl": [(marketing_asset_src("station-mixing-bowl", "../../"), "Mixing Bowl station built with a flower pot on stripped wood.")],
        "Cutting Board": [
            (marketing_asset_src("station-cutting-board", "../../"), "Cutting Board station built with a wooden pressure plate on stripped wood."),
            ("../../images/showcase/wheat.gif", "Cutting Board chopping flow with visible prep interaction."),
        ],
        "Frying Pan": [
            (marketing_asset_src("station-frying-pan", "../../"), "Frying Pan station built from a heavy weighted pressure plate on a furnace."),
            ("../../images/stations/frying-pan.gif", "Frying Pan cooking flow on a furnace station."),
        ],
        "Barista Machine": [(marketing_asset_src("station-barista-machine", "../../"), "Cafe Barista Machine built from an iron trapdoor over quartz stairs.")],
    }
    figures = [image(src, caption) for src, caption in candidates.get(title, []) if docs_image_exists(src)]
    return "\n\n".join(figures)


def crop_media(crop_id: str) -> str:
    crop_assets = {
        "LETTUCE": ("crop-lettuce", "Lettuce crop planted as a short ground crop."),
        "ONION": ("crop-onion", "Onion crop planted as an allium-style ground crop."),
        "CORN": ("crop-corn", "Corn field showing tall crop visuals."),
        "TOMATO": ("crop-tomato", "Tomato crop growing as a vine."),
        "RICE": ("crop-rice", "Rice crop planted in water above soil."),
    }
    entry = crop_assets.get(crop_id)
    if not entry:
        return ""
    src = marketing_asset_src(entry[0], "../../")
    return image_if(src, entry[1])


def crop_media_cards(prefix: str, href_prefix: str) -> list[str]:
    crops = [
        ("LETTUCE", "crop-lettuce", "Lettuce", "Short ground crop."),
        ("ONION", "crop-onion", "Onion", "Allium-style ground crop."),
        ("CORN", "crop-corn", "Corn", "Tall crop with vertical room."),
        ("TOMATO", "crop-tomato", "Tomato", "Wall vine crop."),
        ("RICE", "crop-rice", "Rice", "Aquatic crop planted in water."),
    ]
    cards = []
    for crop_id, asset_key, label, caption in crops:
        src = marketing_asset_src(asset_key, prefix)
        href = f"{href_prefix}{slug(crop_id)}/"
        cards.append(media_card_if(src, f"{label}: {caption}", label, href))
    return cards


def gardening_crop_grid() -> str:
    grid = media_grid(crop_media_cards("../", ""))
    if not grid:
        return ""
    return "## Crop Gallery\n\n" + grid


def recipe_search_media() -> str:
    grid = media_grid([
        media_card_if(marketing_asset_src("recipe-search-gui", "../../"), "Recipe search GUI filtered to useful results.", "Recipe search GUI"),
        media_card_if(marketing_asset_src("recipe-search-chat", "../../"), "Chat search output for quick recipe lookup.", "Recipe search chat output"),
    ])
    if not grid:
        return ""
    return "## Search Examples\n\n" + grid


def first_farm_media() -> str:
    grid = media_grid(crop_media_cards("../../", "../../gardening/"))
    if not grid:
        return ""
    return "## Crop Examples\n\n" + grid


def installation_media() -> str:
    grid = media_grid([
        media_card_if(marketing_asset_src("install-plugin-overview", "../../"), "Core and addon jars beside their generated plugin folders.", "Heirloom plugin and addon folder overview"),
        media_card_if(marketing_asset_src("install-generated-files", "../../"), "Generated Heirloom resource files after the first startup.", "Generated Heirloom files"),
    ])
    if not grid:
        return ""
    return "## Install Layout\n\n" + grid


def first_meal_media() -> str:
    flow = media_grid([
        media_card_if(marketing_asset_src("first-meal-build-station", "../../"), "Build the Frying Pan from a furnace and heavy weighted pressure plate.", "Frying Pan setup"),
        media_card_if(marketing_asset_src("first-meal-place-egg", "../../"), "Right-click with an egg to place it as a visible ingredient.", "Egg placed on the Frying Pan"),
        media_card_if(marketing_asset_src("first-meal-cooking-progress", "../../"), "Start cooking with an empty hand and watch the progress feedback.", "Fried Egg cooking progress"),
        media_card_if(marketing_asset_src("first-meal-finished", "../../"), "Collect the finished Fried Egg from the station.", "Finished Fried Egg on the station"),
    ])
    warning = media_grid([
        media_card_if(marketing_asset_src("first-meal-wrong-furnace", "../../"), "The vanilla furnace GUI does not cook Heirloom recipes; interact with the physical station instead.", "Vanilla furnace GUI cannot cook Heirloom recipes"),
    ])
    sections = []
    if flow:
        sections.append("## First Meal Visual Flow\n\n" + flow)
    if warning:
        sections.append("## Common Wrong Turn\n\n" + warning)
    return "\n\n".join(sections)


def cooking_basics_media() -> str:
    grid = media_grid([
        media_card_if(marketing_asset_src("first-meal-place-egg", "../../"), "Ingredients are placed into the world as visible station contents.", "Egg displayed on station"),
        media_card_if(marketing_asset_src("first-meal-cooking-progress", "../../"), "Cooking starts from the station interaction, with progress shown in game.", "Station cooking progress"),
        media_card_if(marketing_asset_src("first-meal-wrong-furnace", "../../"), "Opening the vanilla furnace GUI is a sign you are using the wrong interaction path.", "Wrong furnace GUI interaction"),
    ])
    if not grid:
        return ""
    return "## Station Loop Example\n\n" + grid


def quality_media() -> str:
    src = marketing_asset_src("food-quality-tooltip", "../../")
    media = image_if(src, "Quality and dietary data are visible directly in item lore.", "Food quality tooltip")
    if not media:
        return ""
    return "## Quality Tooltip Example\n\n" + media


def gallery_media_sections() -> str:
    sections = []
    overview = media_grid([
        media_card_if("../images/showcase/recipe-browser.jpg", "Recipe browsing and ingredient lookup.", "Recipe browser"),
        media_card_if(marketing_asset_src("recipe-search-gui", "../"), "Recipe search GUI.", "Recipe search GUI", "../getting-started/recipe-browser/"),
        media_card_if(marketing_asset_src("recipe-search-chat", "../"), "Recipe search from chat.", "Recipe search chat", "../getting-started/recipe-browser/"),
        media_card_if(marketing_asset_src("install-plugin-overview", "../"), "Installation folder layout.", "Heirloom install folders", "../getting-started/installation/"),
        media_card_if(marketing_asset_src("first-meal-build-station", "../"), "First meal station setup.", "First meal station setup", "../getting-started/first-meal/"),
        media_card_if(marketing_asset_src("first-meal-cooking-progress", "../"), "First meal cooking progress.", "First meal cooking progress", "../getting-started/first-meal/"),
        media_card_if(marketing_asset_src("first-meal-wrong-furnace", "../"), "Wrong furnace interaction example.", "Furnace GUI warning", "../player-guide/cooking/"),
        media_card_if(marketing_asset_src("food-quality-tooltip", "../"), "Food quality tooltip.", "Food quality tooltip", "../player-guide/quality/"),
        media_card_if("../images/showcase/rice.gif", "Rice growth and display visuals.", "Rice crop"),
        media_card_if("../images/showcase/jam.gif", "Cooking flow and recipe variants.", "Jam cooking"),
        media_card_if("../images/showcase/christmas-placeable.png", "Placeable seasonal food.", "Placeable food"),
        media_card_if("../images/showcase/advancements.png", "Advancement UI.", "Advancements"),
        media_card_if("../images/showcase/cooking-mastery.png", "Cooking mastery UI.", "Cooking mastery"),
    ])
    if overview:
        sections.append("## Gameplay And UI\n\n" + overview)

    station_cards = []
    for title, asset_key, href in [
        ("Oven", "station-oven", "../stations/oven/"),
        ("Boiling Pot", "station-boiling-pot", "../stations/boiling-pot/"),
        ("Mixing Bowl", "station-mixing-bowl", "../stations/mixing-bowl/"),
        ("Cutting Board", "station-cutting-board", "../stations/cutting-board/"),
        ("Frying Pan", "station-frying-pan", "../stations/frying-pan/"),
        ("Barista Machine", "station-barista-machine", "../stations/barista-machine/"),
    ]:
        station_cards.append(media_card_if(marketing_asset_src(asset_key, "../"), f"{title} station.", title, href))
    station_grid = media_grid(station_cards)
    if station_grid:
        sections.append("## Cooking Stations\n\n" + station_grid)

    crop_grid = media_grid(crop_media_cards("../", "../gardening/"))
    if crop_grid:
        sections.append("## Crops\n\n" + crop_grid)

    distillery = media_grid([
        media_card_if("../images/distillery/D_stomp_grain.gif", "Stomping tub.", "Stomping grain"),
        media_card_if("../images/distillery/D_boil_wort.gif", "Boiling grain wort.", "Boiling wort"),
        media_card_if("../images/distillery/D_wine_ferment.gif", "Wine fermentation.", "Wine fermentation"),
        media_card_if("../images/distillery/D_whiskey.gif", "Distillation output.", "Whiskey distillation"),
    ])
    if distillery:
        sections.append("## Distillery Motion\n\n" + distillery)
    return "\n\n".join(sections)


def station_recipe_table(station: str, recipe_prefix: str = "../recipes/", reference_prefix: str = "../reference/", image_prefix: str = "../") -> str:
    rows = []
    for recipe in sorted([r for r in RECIPES if r["_station"] == station], key=lambda r: (r["id"], r.get("_sequence", 0))):
        rows.append([
            recipe_link(recipe),
            f"{recipe.get('_output_amount', 1)}× " + output_visual_row(recipe, recipe_prefix, reference_prefix, image_prefix),
            ingredient_icon_strip(recipe, reference_prefix, image_prefix),
            source_badge(recipe.get("_source", ""), image_prefix)
            + ("<br>" + orchard_recipe_availability(recipe["id"])
               if recipe.get("_source") == "Orchard" and orchard_recipe_availability(recipe["id"]) else ""),
        ])
    if not rows:
        return "No bundled recipes currently use this station."
    return table(["Recipe", "Output", "Inputs", "Source"], rows)


JUICER_GUIDE = """
## Blend And Bottle

Build an upward-facing `DROPPER`, place clear `GLASS` above it, and finish with any carpet. Heirloom Mixology's juice recipe enables the station. Click the glass with fruit or vegetables to insert exactly three items; repetitions and mixed produce are allowed. Empty-hand right-click starts a 200-tick blend (ten seconds). Ingredients keep the same size while resting and tumbling inside shaking glass. The completed batch appears as a low, flat liquid level until bottled. The recipe GUI has three independent ingredient selectors; its live preview reflects the selected mixture. Compare five private sound previews with `/hl debug juicer 1` through `5`, `all`, or `stop`; each lasts ten seconds. Pulsing Motor (5) is the default blending sound. Right-click the finished batch twice with Glass Bottles to collect two juices, one per click. The juice level halves after the first pour. No Water Bottle or earlier bottle insertion is required.

Before the first pour, left-click refunds original ingredients with their quality and provider data. After a pour, left-click discards the remainder and never returns consumed ingredients. Finished juice waits to be bottled. On interruption, unfinished blending resets; ingredients remain recoverable. The real glass stays in place for collision and protection while nearby players see its moving display.

Juice is drinkable and uses the vanilla lingering-potion appearance without a resource pack. It cannot be thrown and has no alcohol or Distillery brewing profile. Drinking returns one Glass Bottle. Food and saturation are half the combined input nutrition: round food down after summing, retain fractional saturation, and do not apply a second quality multiplier.

Juice inherits food properties and edible effects, including enchanted-apple benefits, Chorus teleport and poisonous-potato poison chance. Repeated ingredients do not multiply the same effect. Pure batches receive the fruit or vegetable name; mixed batches list their contents and blend their colors. Pure recipe ingredients require three matching produce items: adding one tomato to mixed juice does not make Tomato Juice.

Twenty-three base produce choices are available without Distillery. Registered Distillery grapes add up to five more. Existing owner-gated fruit remains gated.

## Suggested Blends

Try apple + beetroot + carrot (ABC), apple + carrot + orange, or pineapple + orange + mango. These use the same dynamic recipe and remain Mixed Juice. Each batch yields two bottles with the current per-bottle nutrition and effects. Original ingredients are refundable only before the first pour; saved half-full batches retain one serving after restart. Older saved single-serving batches stay single-serving. Both new stations play the shared completion bell.

## Cook With Juice

| Drink | Exact shaker ingredients |
| --- | --- |
| Bloody Mary | Vodka, pure Tomato Juice, Lemon, Salt |
| Garibaldi | Red Bitter Aperitif, pure Orange Juice |
| Virgin Mango Daiquiri | Pure Mango Juice, Lemon, Sugar |
| Virgin Banana Daiquiri | Pure Banana Juice, Lemon, Sugar |
| Shaken Piña Colada | Pure Pineapple Juice, Canned Coconut Milk, Sugar |

Every listed quantity is one. Juice supplies the bottle, so no extra empty bottle or Water Bottle is needed. Other input containers return once. The original Mixing Bowl Piña Colada recipe remains unchanged.
"""

STATION_GUIDES = {
    "Juicer": JUICER_GUIDE,
    "Mixology Table": """
## Shake A Drink

Add the exact ingredients, then start the station. Mixology reuses up to three bottles from bottled inputs for finished drinks, or one for reusable precursors. No extra Glass Bottle is required when a bottled ingredient is listed. Other emptied bottles, cans, and cream buckets are returned once. The shaken Piña Colada reuses its Pineapple Juice bottle; the coconut milk can is returned. Drinking returns one Glass Bottle. Chilled cocktails optionally accept one Ice (no quality bonus), Packed Ice (+0.10) or Blue Ice (+0.20); Core quality is capped at Perfect; ice improves the drink's single quality without changing ABV or serving volume. Spirits, liqueur production and B-52 do not accept ice. Each bundled liqueur or cocktail takes eight seconds: the metal shaker closes, shakes with the station sounds, and settles before the drink is ready to collect. The progress highlight travels through the filled part of the bar on a 16-tick cycle.

Begin with a Virgin Mango or Banana Daiquiri, selected by the pure juice in one shared recipe, or the shaken Piña Colada. These are always available. Gin, Sweet Vermouth, Red Bitter Aperitif and Aromatic Bitters join the three liqueurs as reusable ingredients. The authored Mixology catalog includes Negroni/Boulevardier, Old Fashioned/Rum Old Fashioned, Manhattan, White Lady, Bee’s Knees and Garibaldi. Cafe adds Coffee Liqueur and the Espresso Martini, Russian and B52 recipe families.

## Optional Addons

With no Distillery, Mixology provides all four Boiling Pot spirit recipes, including Rum without Cafe. Compatible Distillery replaces those spirits with genuine distilled bottles. Wine capability 2 additionally enables Sweet Vermouth from genuine Wine or Champagne plus Vodka, and its Negroni/Boulevardier and Manhattan recipes. Capability 1 retains the other alcoholic recipes. An enabled Distillery without even the spirit integration hides the alcoholic menu; the four non-alcoholic recipe families still produce five named drinks. Cafe controls the coffee branch independently.

See [Heirloom Mixology](../addons/orchard/index.md) for the complete mode table and source requirements. The existing Mixing Bowl Piña Colada recipe remains available.
""",
    "Oven": """
## How Recipes Behave Here

The Oven is the long-form heat station. It is where raw prep becomes shelf-stable or baked food: dough becomes bread, flat dough becomes pizza, wet coffee cherries become roast beans, and some addon chains use it as the first serious processing step.

## Common Chains

- `BAG_OF_FLOUR` -> `DOUGH` -> bread, pizza, pancakes, waffles, doughnuts, and pastry-style recipes.
- Cafe coffee cherries roast through light, medium, and dark beans before they become espresso drinks.
- Recipes with `SET_RETURN_ITEM` can give containers back after the craft, so check the output and your inventory before assuming a bucket or bottle vanished.

## Good First Recipes

Start with bread or baked potato-style recipes before testing pizzas and addon chains. They prove the station structure works without requiring several intermediate ingredients.

## What Can Go Wrong

If a recipe never starts, first confirm the station is the smoker plus stone pressure plate pair. If the station works but a recipe does not match, search the exact output or ingredient with `/hl search <query>`; many baked foods need an intermediate Heirloom item rather than the raw vanilla ingredient.
""",
    "Boiling Pot": """
## How Recipes Behave Here

The Boiling Pot is the liquid and simmering station. It handles soups, rice, pasta, cheese, jam, wet ingredient conversions, and recipes that care about buckets or bottles. It is also where property stacking becomes easy to understand: jam can become an ingredient in later foods while keeping the food properties created from its fruit.

## Common Chains

- Fruit + sugar + bottle -> `JAM`; glow berries, golden apples, and chorus fruit can add food properties to the jam.
- `RICE` + water -> `COOKED_RICE`, which then feeds sushi and fried rice chains.
- Milk bucket -> `CHEESE`, and milk plus vinegar can produce the alternate cheese path.
- Distillery grain and rice wort can ferment raw; use the Boiling Pot first for full process-quality credit. Boiling does not change ABV.

## Good First Recipes

Try `COOKED_RICE`, `CHEESE`, then `JAM`. Those three cover water inputs, bucket returns, bottle returns, and property-carrying ingredients.

## What Can Go Wrong

A bucket can be either a normal Minecraft interaction or a recipe ingredient. If you are testing a recipe, interact normally with the station and avoid vanilla cauldron habits. If the output keeps the wrong flavor or property, inspect the recipe rules: properties come from matching ingredient rules and from inherited input data.
""",
    "Mixing Bowl": """
## How Recipes Behave Here

The Mixing Bowl is for combining, folding, grinding, and cold prep. It often creates neutral intermediates that later become powerful when cooked elsewhere: dough, batter, cream, plant protein, and Cafe grinding steps all live here.

## Common Chains

- Flour and liquids become `DOUGH`, then the Oven or Frying Pan finishes the dish.
- Cafe uses grinding-style recipes for tea leaves, matcha chances, and other drink prep.
- Mixed ingredients can inherit dietary and food-property data from custom inputs, so the bowl is often where a server-owner recipe starts carrying metadata forward.

## Good First Recipes

Use the bowl for dough and cream before testing more advanced recipe chains. These are easier to debug because their ingredients are obvious.

## What Can Go Wrong

If a recipe looks right but does not match, check whether the input wants a custom item such as `BAG_OF_FLOUR` rather than vanilla `WHEAT`. For server owners, this station is a good place to test optional slots because it makes failures easy to see before cooking time is involved.
""",
    "Cutting Board": """
## How Recipes Behave Here

The Cutting Board is prep work: chopping, slicing, mincing, and turning raw ingredients into precise recipe components. It is intentionally not a generic table; many recipes need the prepared form before another station accepts them.

## Common Chains

- `WHEAT` can become flour-style ingredients used by dough and batter chains.
- Meat and plant alternatives can become minced or sliced components for later meals.
- Pasta and similar prep items are made here before being boiled or cooked.

## Good First Recipes

Start with flour or pasta prep. Those recipes teach the difference between vanilla ingredients and Heirloom intermediate items.

## What Can Go Wrong

Use the correct physical station: wooden pressure plate on a stripped block. If a food chain seems blocked, search the output you expected; the missing step is often a Cutting Board ingredient rather than the final station.
""",
    "Frying Pan": """
## How Recipes Behave Here

The Frying Pan is fast heat. It handles eggs, bacon, pancakes, fried rice, and other foods where toppings and optional ingredients change the final item. This station is one of the clearest places to see inherited properties: a special jam used as a pancake topping can carry `CHORUS`, `GOLDEN`, or other properties into the finished pancakes.

## Common Chains

- Eggs and bacon prove the station works with simple vanilla inputs.
- `PANCAKES` accept flour/cornmeal, eggs, milk, and optional toppings such as `JAM`, honey, or chocolate.
- `FRIED_RICE` and similar recipes usually depend on rice being cooked first at the Boiling Pot.

## Good First Recipes

Cook a plain egg, then pancakes, then pancakes with a custom jam. Compare the lore: the topping can change name, quality, return behavior, and inherited food properties.

## What Can Go Wrong

The recipe can be valid but still produce a plain-looking result if the optional ingredient did not match the rule you expected. For example, bundled honey pancakes add honey naming, quality, and bottle return behavior; they do not add `SWEET` unless a recipe or custom ingredient explicitly stores that food property.
""",
    "Barista Machine": """
## How Recipes Behave Here

The Barista Machine is Cafe's drink assembly station. Earlier Cafe steps happen on core stations: cherries roast in the Oven, leaves and powders use prep stations, and the Barista Machine turns those prepared ingredients into drinks.

## Common Chains

- Coffee cherry -> light beans -> medium beans -> dark beans -> espresso -> americano, latte, cappuccino, flat white, mocha, or iced coffee.
- Leaves -> dried or ground tea ingredients -> green tea, black tea, sweet tea, matcha latte, or boba tea.
- Milk bucket and oat milk variants often change names, returns, and dietary behavior.

## Good First Recipes

Pull `ESPRESSO`, then make `AMERICANO`, then a milk drink. That proves the chain, the station, and container returns.

## What Can Go Wrong

The station only registers when Cafe is installed. If the trapdoor and quartz stairs act like normal blocks, confirm the Cafe jar loaded, `/hlc help` works, and Cafe recipes appear in `/hl search cafe`.
""",
}


def station_page(title: str, build: str, use: str, station: str, tips: str) -> str:
    media = station_media(title)
    guide = STATION_GUIDES.get(title, "")
    return page(title, f"""
## Build

{build}

{media}

## Core Loop

{use}

{guide}

## Recipes

{station_recipe_table(station, "../../recipes/", "../../reference/", "../../")}

## Troubleshooting

{tips}

See the full [recipe index](../recipes/default-recipes.md) for ingredient links, processing time, recipe rules, and output actions.
""")


def crop_page(crop_id: str) -> str:
    crop = next((c for c in CROPS if c.get("id") == crop_id), None)
    if not crop:
        return page(title_from_id(crop_id), "This crop is not present in the current bundled data.")
    growth = crop.get("growth", {})
    planting = crop.get("planting", {})
    harvest = crop.get("harvest", {})
    rows = [
        ["Item", item_link(crop.get("item_id", crop_id))],
        ["Plant type", f"`{crop.get('plant_type', '')}`"],
        ["Base growth", f"{growth.get('base_duration_seconds', '?')} seconds"],
        ["Stages", str(growth.get("stages", "?"))],
        ["Permission", f"`{planting.get('permission', 'none')}`"],
        ["Replants", "`yes`" if harvest.get("replant_after_harvest", True) else "`no`"],
    ]
    drops = ", ".join(
        f"`{d.get('item_id')}` {d.get('min', 1)}-{d.get('max', 1)}"
        for d in harvest.get("drops", [])
    ) or "none"
    valid_blocks = ", ".join(f"`{b}`" for b in planting.get("valid_blocks", [])) or "see crop JSON"
    media = crop_media(crop_id)
    return page(title_from_id(crop_id), f"""
{media}

{table(["Field", "Value"], rows)}

## Planting

Valid blocks: {valid_blocks}

Use the crop item on the correct block or face. If the crop has a permission, the player must have that node before planting.

## Harvest

Main drops: {drops}.

If the crop keeps `replant_after_harvest` enabled, right-click harvest resets it to an early stage. Breaking the plant is treated as destruction, not a full harvest.

## Notes For Admins

Edit this crop in `crops.json` or the relevant addon crop file. Growth scale, stage count, valid blocks, sounds, drop chances, quality chance, and permission nodes are all data-driven.
""")
def build_recipe_index() -> str:
    sections = ["# Default Recipe Index", "", "This page is generated from the bundled recipe JSON files and addon catalogs. It is meant for lookup; the station pages explain how the systems feel in play. Optional Mixology ingredient choices are declared in the original Core recipes, which remain Core-owned.", ""]
    for station in sorted({r["_station"] for r in RECIPES}):
        sections.append(f"## {station}")
        sections.append("")
        for recipe in sorted([r for r in RECIPES if r["_station"] == station], key=lambda r: (r["id"], r.get("_sequence", 0))):
            rid = recipe["id"].upper()
            sections.append(f"### {rid} {{ #{recipe_anchor(recipe)} }}")
            rows = [
                ["Output", output_visual_row(recipe, "#", "../../reference/", "../../")],
                ["Yield", str(recipe.get("_output_amount", 1))],
                ["Source", source_badge(recipe.get("_source", ""), "../../")],
                ["Processing time", f"{recipe.get('processing_time', 0)} ticks"],
                ["Visual inputs", ingredient_icon_strip(recipe, "../../reference/", "../../")],
                ["Ingredients", ingredient_summary(recipe)],
                ["Rules and actions", actions_summary(recipe)],
            ]
            if recipe.get("description"):
                rows.insert(1, ["Description", recipe.get("description", "")])
            if recipe.get("_source") == "Orchard" and orchard_recipe_availability(rid):
                rows.insert(2, ["Availability", orchard_recipe_availability(rid)])
            sections.append(table(["Field", "Value"], rows))
            sections.append("")
    return "\n".join(sections)


def item_behavior_summary(item: dict) -> str:
    details = []
    if item.get("edible"):
        details.append("Half the combined ingredient nutrition (food rounded down)" if item.get("id", "").startswith("ORCHARD_") and item.get("id", "").endswith("_JUICE") else f'{item.get("food_value", 0)} hunger / {item.get("saturation", 0)} saturation')
        details.append(str(item.get("animation", "EAT")).lower())
    if item.get("consume_return"):
        details.append(f'returns {str(item["consume_return"]).lower().replace("_", " ")}')
    if item.get("placeable_servings"):
        details.append(f'{item["placeable_servings"]} placeable servings')
    if item.get("feast"):
        details.append("feast")
    effects = item.get("effects", []) or []
    if effects:
        details.append("effects: " + ", ".join(str(effect.get("type", "")).title() for effect in effects))
    return "; ".join(details) if details else "ingredient"


def build_content_pack_page(
    pack: dict,
    banner_rel: str | None = None,
    catalog_rel: str | None = None,
) -> str:
    pack_items = [item for item in ITEMS if item.get("_pack_id") == pack["id"]]
    pack_recipes = [recipe for recipe in ALL_RECIPES if recipe.get("_pack_id") == pack["id"]]
    base_pack_items = [item for item in pack_items if not item.get("_compatibility")]
    base_pack_recipes = [recipe for recipe in pack_recipes if not recipe.get("_compatibility")]
    overlay_pack_items = [item for item in pack_items if item.get("_compatibility")]
    overlay_pack_recipes = [recipe for recipe in pack_recipes if recipe.get("_compatibility")]
    configured = ", ".join(pack["providers"]) or "none"
    textures = int(pack.get("texture_count", 0))
    draft = pack.get("status") == "development-draft"
    requirement = pack.get("requires_heirloom", "2.9+")
    if overlay_pack_items or overlay_pack_recipes:
        inventory_summary = (
            f'{pack["name"]} {pack["version"]} contains **{len(base_pack_items)} base custom items** and '
            f'**{len(base_pack_recipes)} base recipe entries**, plus **{len(overlay_pack_items)} optional custom items** '
            f'and **{len(overlay_pack_recipes)} optional recipe entries**. '
        )
        count_rows = [
            ["Base items", str(len(base_pack_items))],
            ["Base recipe entries", str(len(base_pack_recipes))],
            ["Optional compatibility items", str(len(overlay_pack_items))],
            ["Optional compatibility recipe entries", str(len(overlay_pack_recipes))],
        ]
    else:
        inventory_summary = (
            f'{pack["name"]} {pack["version"]} contains **{len(base_pack_items)} custom items** and '
            f'**{len(base_pack_recipes)} recipe entries**. '
        )
        count_rows = [
            ["Items", str(len(base_pack_items))],
            ["Recipe entries", str(len(base_pack_recipes))],
        ]
    sections = [
        f'# {pack["name"]}',
        "",
    ]
    if banner_rel:
        sections.extend([image(f"../../{banner_rel}", f'{pack["name"]} promotional banner.'), ""])
    if catalog_rel:
        sections.extend([
            image(
                f"../../{catalog_rel}",
                f'{pack["name"]} protected catalog preview; source textures are not published.',
            ),
            "",
        ])
    sections.extend([
        inventory_summary
        + (f"This is a **development draft** for Heirloom {requirement}; player-head gameplay is available, and the integrated provider assets remain gated from release packaging pending final validation and marketing artwork."
           if draft and textures and pack["providers"]
           else f"This is a **development draft** for Heirloom {requirement}; player-head gameplay is available, but provider PNGs and release packaging remain gated on final artwork."
           if draft
           else f"The PNG sprites can be used as a visual pack without Heirloom. Heirloom {requirement} adds the cooking stations, recipe matching, food behavior, dynamic variants, and placeable feasts."),
        "",
        table(["Field", "Value"], [
            ["Pack ID", f'`{pack["id"]}`'],
            ["Version", f'`{pack["version"]}`'],
            ["Status", str(pack.get("status", "release"))],
            ["Requires Heirloom", requirement],
            ["Recipe override strength", str(pack["override_strength"])],
            *count_rows,
            ["PNG sprites", str(textures)],
            ["Bundled provider configuration", configured],
        ]),
        "",
        "## Installation And Visual Providers",
        "",
        "Copy the JSON files from `content/` directly into `plugins/Heirloom/`, then run `/hl reload` and check Installed Content. The pack always retains player-head fallbacks.",
        "",
        (f'This draft includes **{textures} integrated PNG sprites** and generated configuration for **{configured}**. Keep release packaging disabled until the remaining draft gates pass.'
         if draft and textures and pack["providers"]
         else "Provider assets are intentionally absent from this draft. Do not publish or build a release ZIP until the canonical atlas has been integrated and all provider checks pass."
         if draft
         else f'The release includes **{textures} raw PNG sprites** and ready-to-install configuration for **{configured}**. Install only the provider used by your server.'),
        "",
        "## Items",
        "",
    ])
    item_rows = []
    for item in sorted(base_pack_items, key=lambda row: str(row.get("id", ""))):
        iid = str(item.get("id", "")).upper()
        item_rows.append([
            icon_img(iid, "../../"),
            item_link(iid, "../reference/"),
            item.get("name", title_from_id(iid)),
            item_behavior_summary(item),
        ])
    sections.extend([table(["Icon", "Item ID", "Name", "Behavior"], item_rows), ""])

    sections.extend(["## Recipes", ""])
    for station in sorted({recipe["_station"] for recipe in base_pack_recipes}):
        sections.extend([f"### {station}", ""])
        recipe_rows = []
        for recipe in sorted(
            [row for row in base_pack_recipes if row["_station"] == station],
            key=lambda row: (str(row.get("id", "")), row.get("_source_index", 0)),
        ):
            recipe_rows.append([
                recipe_link(recipe, "../recipes/"),
                output_visual_row(recipe, "../../recipes/", "../../reference/", "../../"),
                ingredient_icon_strip(recipe, "../../reference/", "../../"),
                ingredient_summary(recipe, "../reference/"),
                f'{recipe.get("processing_time", 0)} ticks',
            ])
        sections.extend([table(["Recipe", "Output", "Inputs", "Ingredient rules", "Time"], recipe_rows), ""])

    override_ids = []
    non_pack_ids = {
        str(recipe.get("id", "")).upper()
        for recipe in ALL_RECIPES
        if recipe.get("_pack_id") != pack["id"]
    }
    for recipe in base_pack_recipes:
        rid = str(recipe.get("id", "")).upper()
        if rid in non_pack_ids and rid not in override_ids:
            override_ids.append(rid)
    if override_ids:
        sections.extend([
            "## Core Recipe Overrides",
            "",
            "This pack intentionally supplies stronger definitions for: " + ", ".join(f'`{rid}`' for rid in override_ids) + ".",
            "",
        ])

    compatibility = pack.get("catalog", {}).get("compatibility", {})
    if compatibility or overlay_pack_items or overlay_pack_recipes:
        sections.extend([
            "## Optional Compatibility",
            "",
            *[f'- **{title_from_id(name)}:** {description}' for name, description in compatibility.items()],
            "",
        ])
        compatibility_names = sorted({
            str(row.get("_compatibility"))
            for row in [*overlay_pack_items, *overlay_pack_recipes]
            if row.get("_compatibility")
        })
        for compatibility_name in compatibility_names:
            title = title_from_id(compatibility_name)
            optional_items = [
                row for row in overlay_pack_items
                if str(row.get("_compatibility")) == compatibility_name
            ]
            optional_recipes = [
                row for row in overlay_pack_recipes
                if str(row.get("_compatibility")) == compatibility_name
            ]
            sections.extend([
                f"### {title} Overlay",
                "",
                f"Install only when {title} is active: **{len(optional_items)} custom items** and **{len(optional_recipes)} recipe entries**.",
                "",
            ])
            if optional_items:
                optional_item_rows = []
                for item in sorted(optional_items, key=lambda row: str(row.get("id", ""))):
                    iid = str(item.get("id", "")).upper()
                    optional_item_rows.append([
                        icon_img(iid, "../../"),
                        item_link(iid, "../reference/"),
                        item.get("name", title_from_id(iid)),
                        item_behavior_summary(item),
                    ])
                sections.extend([
                    table(["Icon", "Optional item ID", "Name", "Behavior"], optional_item_rows),
                    "",
                ])
            if optional_recipes:
                optional_recipe_rows = []
                for recipe in sorted(optional_recipes, key=lambda row: str(row.get("id", ""))):
                    optional_recipe_rows.append([
                        recipe_link(recipe, "../recipes/"),
                        recipe["_station"],
                        output_visual_row(recipe, "../../recipes/", "../../reference/", "../../"),
                        ingredient_summary(recipe, "../reference/"),
                    ])
                sections.extend([
                    table(["Optional recipe", "Station", "Output", "Ingredient rules"], optional_recipe_rows),
                    "",
                ])

    variant_rows = []
    for recipe in base_pack_recipes:
        variants = recipe_output_variant_data(recipe)
        if len(variants) > 1:
            variant_rows.append([
                recipe_link(recipe, "../recipes/"),
                ", ".join(str(variant.get("label", "Variant")) for variant in variants),
            ])
    if variant_rows:
        sections.extend([
            "## Dynamic Variants",
            "",
            "These recipes select their output visual from the matched ingredient or carried food property.",
            "",
            table(["Recipe", "Generated variants"], variant_rows),
            "",
        ])

    sections.extend([
        "## Removing The Pack",
        "",
        "Remove both JSON files together and run `/hl reload`. Heirloom will restore any weaker built-in recipe definitions that this pack overrode.",
    ])
    return "\n".join(sections)


def content_pack_pages() -> None:
    for pack in CONTENT_PACKS:
        media: dict[str, str | None] = {"banner": None, "catalog": None}
        for kind in media:
            filename = f'{slug(pack["name"])}-{kind}.png'
            source = PLUGIN_ROOT / "docs/marketplace/assets" / filename
            if pack["id"] == "heirloom_american_food":
                export = {
                    "banner": "heirloom-american-food-banner-marketplace.png",
                    "catalog": "heirloom-american-food-item-catalog-provider-marketplace.png",
                }[kind]
                source = PLUGIN_ROOT / "logo/exports" / export
            if not source.is_file():
                continue
            media[kind] = f"images/content-packs/{filename}"
            target = DOCS_ROOT / "docs" / str(media[kind])
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != source.read_bytes():
                shutil.copyfile(source, target)
        add(
            f'content-packs/{slug(pack["name"])}.md',
            build_content_pack_page(pack, media["banner"], media["catalog"]),
        )


def build_item_reference() -> str:
    sections = ["# Item ID Reference", "", "Source-derived reference for bundled Heirloom custom items. Use these IDs in commands, recipes, visual mappings, and config files.", ""]
    seen_ids: set[str] = set()
    sources = []
    for item in ITEMS:
        source = item.get("_source", "Unknown")
        if source not in sources:
            sources.append(source)
    for source in sources:
        group = sorted([i for i in ITEMS if i["_source"] == source and i.get("id")], key=lambda i: i.get("id", ""))
        if not group:
            continue
        if source == "Orchard":
            sections.append('<a id="orchard-items"></a>')
        sections.append(f"## {'Heirloom Mixology' if source == 'Orchard' else source} Items")
        sections.append("")
        if source == "Orchard":
            sections.append("This is the full editable Heirloom Mixology inventory. Optional Cafe and Distillery integrations select the active items; see [Mixology's mode table](../addons/orchard/index.md#active-content). Fallback spirits are absent while Distillery is enabled.")
            sections.append("")
        rows = []
        for item in group:
            iid = str(item.get("id", "")).upper()
            if not iid or iid in seen_ids:
                continue
            seen_ids.add(iid)
            rows.append([
                icon_img(iid, "../../"),
                f'<span id="{item_anchor(iid)}"></span>`{iid}`',
                item.get("name", title_from_id(iid)),
                item.get("base_material", ""),
                "yes" if item.get("edible") else "no",
                item.get("visual_id", iid),
            ])
        sections.append(table(["Icon", "ID", "Name", "Base", "Edible", "Visual ID"], rows))
        sections.append("")
    return "\n".join(sections)




def build_vanilla_item_reference() -> str:
    sections = ["# Vanilla Ingredient Reference", "", "Source-derived list of vanilla Minecraft items used by bundled Heirloom recipes or as custom item base materials.", ""]
    rows = []
    for item_id in sorted(VANILLA_ITEM_IDS):
        rows.append([
            icon_img(item_id, "../../"),
            f'<span id="{vanilla_item_anchor(item_id)}"></span>`{item_id}`',
            title_from_id(item_id),
            ICON_MANIFEST.get(item_id, {}).get("status", "missing"),
        ])
    sections.append(table(["Icon", "ID", "Name", "Icon status"], rows))
    return "\n".join(sections)


def build_crop_reference() -> str:
    sections = ["# Crop ID Reference", "", "Source-derived reference for bundled crop definitions.", ""]
    rows = []
    for crop in sorted(CROPS, key=lambda c: (c["_source"], c.get("id", ""))):
        cid = crop.get("id", "")
        growth = crop.get("growth", {})
        planting = crop.get("planting", {})
        rows.append([
            f'<span id="{crop_anchor(cid)}"></span>`{cid}`',
            source_badge(crop.get("_source", ""), "../../"),
            crop.get("item_id", ""),
            crop.get("plant_type", ""),
            str(growth.get("base_duration_seconds", "")),
            planting.get("permission", ""),
        ])
    sections.append(table(["ID", "Source", "Item", "Type", "Base seconds", "Permission"], rows))
    return "\n".join(sections)


def build_recipe_reference() -> str:
    rows = []
    by_source = defaultdict(int)
    by_station = defaultdict(int)
    for recipe in RECIPES:
        by_source[recipe["_source"]] += 1
        by_station[recipe["_station"]] += 1
    for source, count in sorted(by_source.items()):
        rows.append([source_badge(source, "../../"), str(count)])
    station_rows = [[station, str(count)] for station, count in sorted(by_station.items())]
    return page("Recipe Reference", f"""
The full linked recipe index lives at [Default Recipe Index](../recipes/default-recipes.md).

These counts describe the canonical references, including conditional source definitions. Jam, Ice Cream and Taco remain Core-owned recipes; their optional Mixology ingredient choices do not add recipes to the addon counts. See [Mixology's active-content table](../addons/orchard/index.md#active-content) for the addon contribution.

## Recipes By Source

{table(["Source", "Recipes"], rows)}

## Recipes By Station

{table(["Station", "Recipes"], station_rows)}

## Data Files

- `recipes.json`: main core recipes.
- `recipes-world.json`: optional world-food recipes.
- `recipes-festive.json`: seasonal recipes and feast recipes.
- `recipes-cafe.json`: Cafe addon recipes.
""")


def build_visual_reference() -> str:
    rows = []
    for item in sorted([i for i in ITEMS if i.get("visual_id")], key=lambda i: i["id"]):
        rows.append([f"`{item['id']}`", item.get("visual_id", ""), source_badge(item.get("_source", ""), "../../")])
    return page("Visual ID Reference", f"""
`visual_id` is the logical name Heirloom asks visual providers to resolve. Nexo, ItemsAdder, CraftEngine, and MMOItems can provide the same logical visual without changing recipes.

{table(["Item", "Visual ID", "Source"], rows)}
""")




def missing_icon_section() -> str:
    rows = []
    for kind, item_id, reason in sorted(MISSING_ICON_ROWS):
        rows.append([kind, f"`{item_id}`", reason])
    if not rows:
        return "No missing recipe icons were detected in the last generator run."
    return table(["Kind", "ID", "Reason"], rows)


def basic_pages():
    add("index.md", page("Heirloom Wiki", f"""
{image("images/heirloom-wide-banner.png", "Heirloom is a physical cooking and gardening plugin for Paper servers.")}

Heirloom adds in-world cooking stations, custom crops, food quality, dietary labels, recipe discovery, and addon content without requiring a resource pack. Optional Nexo, ItemsAdder, CraftEngine, and MMOItems integrations can replace player-head fallback visuals when a server wants a resource-pack presentation.

## Start Here

- New players: [First Meal](getting-started/first-meal.md), [First Farm](getting-started/first-farm.md), then [Recipe Browser](getting-started/recipe-browser.md).
- Server owners: [Installation](getting-started/installation.md), [Configuration](server-owners/configuration.md), [Permissions](server-owners/permissions.md), and [Diagnostics](server-owners/diagnostics.md).
- Creators: [Custom Foods](customization/custom-foods.md), [Custom Recipes](customization/custom-recipes.md), [Custom Crops](customization/custom-crops.md), and [Visual Integrations](customization/visuals-overview.md).
- Plugin developers: [Developer API](developer/index.md), [Items & FoodFacts V2](developer/items-and-food-facts.md), [Bukkit Events](developer/events.md), and [Addons & Registration](developer/addons-and-registration.md).

## What The Wiki Covers

<div class="hl-grid">
  <div class="hl-card"><h3>Players</h3><p>Cooking, farming, recipe search, favourite food, advancements, mastery, and feasts.</p></div>
  <div class="hl-card"><h3>Server Owners</h3><p>Install, configure, protect claims, localize, debug, and update safely.</p></div>
  <div class="hl-card"><h3>Creators</h3><p>Write JSON content, tune food systems, and map visual items for Nexo, ItemsAdder, CraftEngine, or MMOItems.</p></div>
  <div class="hl-card"><h3>Addons</h3><p>Distillery, Cafe, and Heirloom Mixology extend the kitchen with brewing, coffee, fruit growing, and cocktails. Additional addon references are available in the navigation.</p></div>
</div>

## Useful Links

- Maven repository & SDK: `https://heirloom-maven.pages.dev/`
- Online API Javadocs: `https://heirloom-maven.pages.dev/javadoc/`
- Web recipe generator: `https://kernel-person.github.io/heirloom-generator/`
- Demo video: `https://youtu.be/t10v5fPzius?si=xZ4-q1KusBYcF8NP`
- Discord: `https://discord.gg/bPeuK6drX3`

## Current Public Addons

- [Distillery](addons/distillery/index.md): recognizable drink families, fermentation, distillation, cellar craftsmanship and inebriation.
- [Cafe](addons/cafe/index.md): coffee, tea, barista recipes, coffee cherries, and cafe visual packs.
- [Heirloom Mixology](addons/orchard/index.md): grow fruit, blend juices, and shake cocktails at physical stations with included player-head visuals.

## Current Release

Heirloom Core, Cafe and Distillery are **{RELEASE_VERSIONS['core']}**; Mixology is **{RELEASE_VERSIONS['mixology']}**. The [Asian Food Pack](content-packs/heirloom-asian-food-pack.md) and [American Food Pack](content-packs/heirloom-american-food-pack.md) add optional food and provider visuals. See [Installation](getting-started/installation.md) for the complete version, dependency and server compatibility table.
"""))

    add("gallery.md", page("Gallery", f"""
The gallery collects media that already exists in the docs project. Missing captures are tracked in [Media Needed](media-needed.md).

{gallery_media_sections()}
"""))


    add("roadmap.md", page("Future Addons", """
This wiki documents public, usable gameplay first. The repository also contains early work for future addon modules.

| Addon | Current wiki status | Notes |
| --- | --- | --- |
| Tides | Roadmap only | Fishing addon work exists, but command implementation is not ready for a public guide. |
| Neighbours | Roadmap only | Quest/social systems are experimental and should not be documented as stable gameplay yet. |

When these modules are ready, they should get the same treatment as Distillery and Cafe: player guide, server owner setup, commands, permissions, config, and media checklist.
"""))

    add("media-needed.md", page("Media Needed", f"""
Capture these in-game images and GIFs before publishing a fully visual version of the wiki. Keep captures clean: default UI scale, readable chat/action bars, no unrelated builds in frame, and one subject per shot.

## Highest Priority

| Page | Needed media | Notes |
| --- | --- | --- |
| Home | Current kitchen overview screenshot | Show all five core stations in one compact kitchen. |
| First Farm | Planting and harvest flow screenshots | Still crop images exist; capture the interaction flow. |
| Favourite Food | Favourite food GUI screenshot | Show current favourite and selection state. |
| Placeable Foods | Feast before/after serving screenshots | Include servings remaining if visible. |
| Cafe | Drink flow screenshot set | Barista Machine still exists; add espresso, latte, and tea flow. |

## Heirloom Mixology capture brief

Capture the released head-based content on the matching Core build. Use actual in-game scenes at 1920×1080 or higher, 16:9, with normal field of view, readable action bars and clean surroundings. Keep the source video with game audio; export short MP4/WebM clips and a lightweight GIF only where needed. No mock gameplay, fabricated interfaces or unfinished provider sprites. Record the Core/addon versions and optional addons with each capture.

| Capture | Required framing and action | Deliverable / placement | Filenames |
| --- | --- | --- | --- |
| Wide hero | A compact outdoor bar beside a mature fruit grove; frame the complete Mixology Table, Juicer and several ripe fruits. Show the active player-head visuals in daylight. Leave the upper corners clear for an optional title crop. | 2560×1440 still, with a clean 1600×800 crop; overview hero. | `orchard-hero.png`, `orchard-hero-marketplace.png` |
| Normal shaker | Fixed three-quarter view close enough to see body, lid and cap knob. Record one complete eight-second real recipe from ingredients through closing, shaking, colored particles, settling and three-drink output. Include the progress bar and game sound. | 12–15 second clip; Mixology Table guide and listing. | `orchard-shaker.mp4` |
| Perfect shaker | Use verified Perfect-quality ingredients/results. Capture both Toss and catch and Grand finale with sparkle trail and chime, followed by the output lore showing Perfect. Debug previews may be a separately labeled animation comparison, never evidence of crafting or quality. | Two 12–15 second clips plus one lore still; Mixology guide. | `orchard-perfect-shake.mp4` (Toss and catch), `orchard-perfect-grand-finale.mp4`, `orchard-perfect-lore.png` |
| Juicer blend and two pours | Frame the full Dropper → Glass → carpet structure. Insert three visibly different produce items, show the full ten-second blend, then pour twice with Glass Bottles. Hold briefly on the full, half-full and empty levels and show two bottles received. | 18–25 second clip; Juicer guide. | `orchard-juicer.mp4` |
| Orchard growth | Show one normal tree, one palm and Pineapple, with unripe and ripe fruit in the same view. Include direct fruit planting and a bonemeal growth step in a separate close shot. | Two stills and a short planting/growth clip; growing section. | `orchard-growing.png`, `orchard-ripe-fruit.png`, `orchard-planting.mp4` |
| Bow harvest | Aim at a ripe hanging fruit, fire one arrow, follow the quality-preserving dropped item and show that the node begins regrowing. Keep the tree attachment and fruit visible throughout. | 8–12 second clip; harvesting section. | `orchard-bow-harvest.mp4` |
| Recipe GUI and three-glass row | Show the filtered Mixology item/recipe browser, select a pure-juice drink and one dynamic variant, then capture a finished batch's centered three-glass row on the table. Keep input quantities and output count readable; include a matching item-lore still. | GUI stills plus one world still; overview and recipe guide. | `orchard-recipe-preview.png`, `orchard-recipe-variant.png`, `orchard-three-glass-row.png`, `orchard-drink-lore.png` |
| Station construction | In an uncluttered area, show an iron block with a wooden pressure plate and, separately, an upward-facing Dropper with clear Glass and any carpet. Use side and three-quarter angles; show the correct interaction surface. | One paired 1920×1080 construction sheet; station pages. | `orchard-station-builds.png` |

Store approved captures under `docs/images/addons/mixology/` or `docs/images/stations/` and add them only after checking the real files. Missing captures must leave the page readable without image placeholders. The graphic branding banner is not a gameplay screenshot. The owner has supplied the coconut bow-harvest, Juicer and Mixology Table clips, now shown in their guides. The remaining capture requests above still apply; automated checks do not prove client rendering.

## Advanced / Server Owner

| Page | Needed media | Notes |
| --- | --- | --- |
| Visual Integrations | Nexo/ItemsAdder/CraftEngine/MMOItems comparison | Same item with fallback and custom visual. |
| Diagnostics | `/hl debug test` output | Use a clean successful run. |
| Region Protection | Protected-region denial action bar | Show crop or station interaction blocked. |
| Dietary Properties | Item lore examples | Vegan/Vegetarian/Gluten-Free plus Contains line. |

## Recipe Icon Gaps

These are generated from the latest icon pass. Tag entries use a generic tag icon by design. Missing custom or Minecraft icons should be replaced with local PNGs under `docs/images/items/`.

{missing_icon_section()}

## Distillery

Existing Distillery GIFs are usable. Add still screenshots for the Distillery drink catalog, editable recipe preview, cellar controls, Brew Lab, and drunk level/status output.
"""))


def getting_started_pages():
    release_rows = [
        ["Heirloom Core", RELEASE_VERSIONS["core"], "Required for Heirloom gameplay"],
        ["[Cafe](../addons/cafe/index.md)", RELEASE_VERSIONS["cafe"], f"Use with Core {RELEASE_VERSIONS['core']}"],
        ["[Distillery](../addons/distillery/index.md)", RELEASE_VERSIONS["distillery"], f"Use with Core {RELEASE_VERSIONS['core']}"],
        ["[Mixology](../addons/orchard/index.md)", RELEASE_VERSIONS["mixology"], f"Core {ORCHARD_CATALOG['requires_heirloom']} or newer; Core {RELEASE_VERSIONS['core']} recommended"],
        ["[Pasture](../addons/pasture/dairy.md)", RELEASE_VERSIONS["pasture"], "; ".join(PASTURE_CATALOG["requirements"]) + "; matching Core candidate required"],
    ]
    for pack in CONTENT_PACKS:
        if pack["id"] in {"heirloom_asian_food", "heirloom_american_food"}:
            release_rows.append([
                f'[{pack["name"]}](../content-packs/{slug(pack["name"])}.md)',
                pack["version"],
                f'Heirloom {pack["requires_heirloom"]} for cooking; standalone sprites need no Heirloom',
            ])
    add("getting-started/installation.md", page("Installation", f"""
Install Heirloom Core first, then add optional gameplay addons or food packs. Cafe, Distillery, Mixology and Pasture each require Core; Cafe and Distillery are optional integrations for Mixology.

{installation_media()}

## Requirements

- Paper server; see the compatibility table below.
- Java version matching the server build you run.
- Heirloom core jar.
- Optional: HeirloomDistillery, HeirloomCafe, HeirloomOrchard (Mixology), and HeirloomPasture addon jars.
- Optional: PacketEvents for [interactive station tutorials](../tutorials/station-tutorials.md). Cooking, crops and addons work without it.
- Optional visual plugins: Nexo, ItemsAdder, CraftEngine, or MMOItems.
- Optional protection plugins: WorldGuard, Towny, GriefPrevention, Lands, or similar claim plugins.

## Versions and Dependencies

{table(["Product", "Version", "Dependency"], release_rows)}

Install matching Core, Cafe and Distillery updates together. Mixology keeps the internal name `HeirloomOrchard`, its `/hlo` command and the `plugins/HeirloomOrchard/` data folder. Addons do not require separate license keys when Core is active.

The current private **Pasture {RELEASE_VERSIONS['pasture']} candidate requires Java 25, Paper 26.2 and its matching Core {RELEASE_VERSIONS['core']} candidate**. Install both jars from the same candidate archive; earlier private builds can share the version label. This Pasture acceptance scope does not include Paper 1.21.11 or 26.1.2. Public Pasture publication remains gated on the candidate's release checks.

## Server Compatibility

| Java | Paper | Release verification |
| --- | --- | --- |
| Java 21 | Paper 1.21.11 | Compilation and automated tests |
| Java 25 | Paper 26.2 | API compilation and automated tests |

Heirloom targets Java 21 bytecode. Use the Java runtime required by your Paper build. Automated checks do not establish client-side visual acceptance for optional resource packs.

## Install Core

1. Stop the server.
2. Download Core from your purchasing account and put its jar in `plugins/`, replacing the previous Core jar.
3. Start the server and check that Heirloom enables successfully.
4. Confirm `plugins/Heirloom/` was created.
5. Join and run `/hl help`.

### Voxel Purchases

Voxel Core downloads activate automatically through RIC using the personalized proof included in your download. Existing buyers can re-download the current Core release from their Voxel account and replace the old jar while the server is stopped. No manual license key is needed for the normal Voxel installation.

The standard Voxel Core license is perpetual and allows **three server installations**. Each server creates its own installation identity. Keep that identity for updates and restarts on the same server; do not copy `license-installation-id` or `license-lease.json` into another server installation.

Core renews its signed license shortly after startup and then every two hours. Temporary connection errors allow Core to continue for the remaining validity of its current six-hour signed lease. A definitive refusal or an expired lease disables Heirloom addons and Core through their normal shutdown handlers. Restore connectivity or resolve the reported license issue, then restart the server.

If the console reports an unavailable or invalid Voxel proof, download a fresh Core jar from your Voxel account. The legacy `license-key` setting is not a replacement for a Voxel proof. Contact support if a fresh download still fails, including the error code and request ID from the log, without sharing license files.

### BuiltByBit and MCModels Purchases

BuiltByBit and MCModels downloads continue to use the existing Lukittu licensing flow. Keep the license setup supplied with that marketplace download. The Voxel RIC change does not require moving those installations to a different license system.

## Install Addons

Stop the server, put the Cafe, Distillery, Mixology or Pasture addon jars in `plugins/` beside Core, and start the server. Use the versions listed above. Mixology's downloadable jar is named `HeirloomOrchard`.

For the private Pasture candidate, install `Heirloom-2.10.1.jar` and `HeirloomPasture-2.10.1.jar` together on Java 25 / Paper 26.2. Pasture creates its editable config and content under `plugins/HeirloomPasture/`; do not copy its addon JSON into Core's folder. Check `/hl` → **Animal Care**, `/hl` → **Pasture Cheeses**, or `/hlp menu`. Natural animals stay wild by default; supported directly bred newborns join care. Review `plugins/HeirloomPasture/config.yml` and the [Pasture guide](../addons/pasture/dairy.md). No provider package is required for its head/vanilla visuals.

Use:

```text
/hld help
/hlc help
/hlo info
```

Food-pack JSON goes in `plugins/Heirloom/`; follow the individual pack guide for its exact files and optional provider setup. Use `/hl reload` for supported content edits. Restart after replacing jars or changing license credentials.

## First Files To Review

- `plugins/Heirloom/config.yml`
- `plugins/Heirloom/custom_items.json`
- `plugins/Heirloom/recipes.json`
- `plugins/Heirloom/crops.json`
- `plugins/Heirloom/dietary_properties.json`
- `plugins/Heirloom/seed_acquisition.json`

## Verify The Install

Run `/hl debug test` from an admin account. It checks item registration, recipe matching, crop registration, protection hooks, EcoEnchants detection, and runtime GUI loading.

!!! tip
    If you use a claim plugin, test planting, harvesting, and station use in both allowed and denied regions before opening the server to players.
"""))

    add("getting-started/first-meal.md", page("First Meal", f"""
This walkthrough makes a simple cooked food and teaches the physical station flow.

{first_meal_media()}

## Goal

Cook Fried Egg on a Frying Pan.

## Build The Frying Pan

Place a `FURNACE`, then place a `HEAVY_WEIGHTED_PRESSURE_PLATE` on top. The plate is the station block players interact with.

## Cook

1. Hold an egg.
2. Right-click the frying pan to add it.
3. Empty your hand.
4. Right-click the station to begin cooking.
5. Wait for the completion effects.
6. Left-click to collect the result, or add more ingredients if the result is part of another recipe chain.

## What To Notice

- The station stores visible ingredients as display entities.
- Some stations need tools for best results, such as chopping tools on the Cutting Board.
- Recipe quality can improve with correct station interaction and Cooking Mastery.

Next: [First Farm](first-farm.md) or [Recipe Browser](recipe-browser.md).
"""))

    add("getting-started/first-farm.md", page("First Farm", f"""
Start with Lettuce because it uses the simplest plant type.

{first_farm_media()}

## Get A Crop Item

Admins can test with:

```text
/hl give LETTUCE
```

Players normally discover seeds through grass drops, seed packets, chest loot, or world generation, depending on server configuration.

## Plant Lettuce

1. Hold `LETTUCE`.
2. Right-click grass, dirt, coarse dirt, podzol, or rooted dirt.
3. Wait for the display to mature.
4. Right-click the mature crop to harvest.

## Try The Other Core Crops

- Lettuce: short ground plant.
- Onion: allium-style ground plant.
- Corn: tall plant.
- Tomato: wall vine.
- Rice: aquatic crop planted in water above soil.

See [Gardening](../gardening/index.md) for conditions, permissions, and drops.
"""))

    add("getting-started/recipe-browser.md", page("Recipe Browser", f"""
{image("../../images/showcase/recipe-browser.jpg", "The recipe browser is the main in-game guide for players.")}

## Open It

```text
/hl
/hl recipes
/hl search pizza
```

`/hl` opens the main menu for players. `/hl search <query>` opens filtered results by recipe, station, addon, output, or ingredient.

{recipe_search_media()}

## How To Read It

- Open **Crafting** for equipment, containers and supported workstation recipes. The matching runtime indexes recipes registered on your server.
- Click a recipe to inspect inputs and output.
- Click ingredients to follow recipe chains backward.
- Use item-use pages to answer "what can I cook with this?"
- Addon recipes appear only when their addon is installed and registered.

Back and Forward use left/right arrow heads to move through your browsing history. **Previous Page** uses an up-arrow head and **Next Page** uses a down-arrow head in the rightmost two slots of the bottom row: zero-based slots 43 and 44 in a 45-slot browser, or the corresponding final two slots in other inventory sizes. Ingredient Bank keeps its existing top-row controls and uses the same directional heads.

## If Something Is Missing

- Make sure the addon is installed.
- Run `/hl reload` after JSON changes.
- Check startup logs for recipe validation warnings.
- Use `/hl debug test` for registration diagnostics.
"""))


def player_pages():
    add("player-guide/index.md", page("Player Guide", """
This section explains Heirloom as a game system rather than a config file. Read it when you want to know what a player is expected to do, what the item lore means, and why a recipe result changed.

Start with [Cooking Basics](cooking.md), then use [Recipe Search](recipe-search.md), [Favourite Food](favourite-food.md), [Food Quality](quality.md), and [Farming And Seed Discovery](seed-discovery.md).
"""))
    add("player-guide/cooking.md", page("Cooking Basics", f"""
Heirloom cooking is physical. You build a station in the world, add visible ingredients, process the station, then either collect the result or keep using that result as part of a recipe chain.

{cooking_basics_media()}

## The Station Loop

1. Build the correct station shape.
2. Right-click with ingredients to place them on the station.
3. Empty your hand and right-click to begin processing.
4. Wait for the station effects and progress to finish.
5. Left-click to collect the output, or keep the output in the station flow if the next recipe uses it.

## Chains Are The Point

Many foods are not one-step crafts. Flour can become dough, dough can become bread or pancakes, rice can become cooked rice and then a meal, and jam can become a topping that carries properties into another food. When a recipe says it wants `JAM`, it means the actual item you made, including quality, creator data, consume returns, and food properties.

## What Changes A Result

A finished food can be changed by recipe rules, optional ingredients, inherited properties, quality, and visual actions. That is why two foods with the same output ID can have different names, lore, textures, or effects.

## Container Returns

Some recipes and foods return buckets or bottles. There are two common cases:

- Craft return: the station gives something back when the recipe completes.
- Consume return: eating the food gives something back afterward, such as a bottle from jam.

## Common Failure Cases

- The station shape is wrong, so Heirloom never treats the block as a station.
- The ingredient is the wrong form, such as `WHEAT` instead of `BAG_OF_FLOUR`.
- The recipe belongs to another station or addon.
- An optional ingredient matched the base recipe but not the rule you expected.
- A protection plugin cancelled interaction in the region.

Use `/hl search <ingredient>` when stuck. It is usually faster than guessing the next station.
"""))
    add("player-guide/recipe-search.md", page("Recipe Search", f"""
`/hl search <query>` searches recipes by name, station, addon, ingredient, or output. It is the fastest way to follow a chain backward.

{recipe_search_media()}

Examples:

```text
/hl search pizza
/hl search rice
/hl search oven
/hl search cafe
/hl search jam
```

## How To Use Search Well

Search the ingredient you are holding, not only the food you want. If you have `RICE`, search rice to find cooked rice and later meal paths. If you have `JAM`, search jam to find pancakes, doughnuts, or any server-added recipes that use it.

## Recipe Detail Preview

The in-game recipe detail view simulates the selected inputs. When a selected ingredient has food properties or dietary data, the preview can show the resulting lore before you cook it.
"""))
    add("player-guide/favourite-food.md", page("Favourite Food", """
Favourite food is a personal RPG feature. You choose one custom food, then get extra effects whenever you eat that food ID.

## Command

```text
/hl favourite
```

Aliases:

```text
/hl favorite
/hl fav
```

## What You Get

Eating your favourite food applies:

| Effect | Duration | Strength |
| --- | --- | --- |
| Regeneration | 30 seconds | I |
| Saturation | 15 seconds | II |
| Luck | 60 seconds | I |

These effects are added after normal food-property effects. If your favourite food is also a property-stacked food, both systems apply.

## Why It Matters

A plain favourite is useful. A favourite with inherited properties is stronger. For example, pancakes made with `GOLDEN` and `CHORUS` jam can apply those property effects, then the favourite-food package if pancakes are your selected favourite.

## Social Cooking

Heirloom stores cooked-by data on edible outputs. If somebody else cooked your favourite food, the favourite check can reward the cook with a short regeneration effect. The `AFFINITY` food property also reads cooked-by data and becomes stronger when the food is also your favourite.

## Server Notes For Players

If `/hl favourite` is unavailable, ask staff whether `heirloom.favourite` is granted. The feature is permission-gated so servers can decide whether it is part of default progression.
"""))
    add("player-guide/quality.md", page("Food Quality", f"""
Food quality is stored on custom foods and ingredients. It is not just flavor text: quality is part of progression, advancement tracking, and recipe identity.

## What Changes Quality

- Recipe actions can set a base quality or add to it.
- Ingredient quality can carry into later foods; the crafting code keeps the best input quality when no explicit quality is supplied.
- Crops can store quality and keep it when replanted after harvest.
- Cooking Mastery adds a recipe-specific quality bonus as you repeat the same recipe.

## Reading Quality In Play

Quality appears in item names and lore. If two players make the same recipe but one uses better ingredients or has more mastery, their outputs can differ.

{quality_media()}

## Why It Matters

Quality supports long-term goals: better crops, better repeated cooking, and quality-based advancements. If a recipe feels unrewarding, check whether it is setting quality too low or never inheriting quality from its ingredients.

Server owners can inspect the data side in [Custom Recipes](../customization/custom-recipes.md).
"""))
    add("player-guide/advancements.md", page("Advancements", f"""
{image("../../images/showcase/advancements.png", "Heirloom has native advancement progress.")}

Heirloom tracks food discovery, crop harvesting, recipe progress, collection goals, and quality milestones.

Commands:

```text
/hl advancements
/hl adv
/hl progress
```

## How Progress Is Counted

Eating custom foods records the food ID and quality. Harvesting crops records crop progress. Collection advancements check whether you have eaten or harvested every item in a list, while counter advancements check totals.

Admins can customize bundled advancement data in `advancements.json`.
"""))
    add("player-guide/mastery.md", page("Cooking Mastery", f"""
{image("../../images/showcase/cooking-mastery.png", "Cooking Mastery rewards repeated practice with a recipe.")}

Cooking Mastery tracks how often you cook each recipe. Mastery is recipe-specific: being excellent at pancakes does not automatically make you excellent at sushi.

Command:

```text
/hl mastery
```

## Levels

| Level | Crafts | Quality bonus |
| --- | ---: | ---: |
| Novice | 0 | 0% |
| Apprentice | 5 | +5% |
| Competent | 15 | +10% |
| Skilled | 30 | +15% |
| Expert | 50 | +20% |
| Master | 80 | +30% |

The bonus is added to the recipe quality roll. This makes frequently cooked foods more reliable without making every recipe globally easier.
"""))
    add("player-guide/placeable-foods.md", page("Placeable Foods And Feasts", f"""
{image("../../images/showcase/christmas-placeable.png", "Some foods can be placed and eaten in servings.")}

Some Heirloom foods can be placed and eaten in servings. The placed block stores remaining servings, remaining nutrition, remaining saturation, and food properties in block data so state survives restarts.

## How To Eat

Right-click the placed food with an empty hand. Each bite consumes one serving and applies that serving's share of nutrition, saturation, and any stored food-property effects.

## Feasts

Feast foods track unique participants. When a new guest joins a feast, previous participants receive a small regeneration bonus. This rewards shared meals without giving the same player repeated guest credit.

## Breaking Placed Food

Breaking a placed food removes it and plays food-colored break particles. It does not return the whole food item.
"""))
    add("player-guide/seed-discovery.md", page("Farming And Seed Discovery", """
Players can obtain crop starts in several ways, depending on server settings.

## Discovery Methods

- Grass drops from valid grass or fern blocks.
- Seed packets that open into weighted seed drops.
- Chest loot in villages, dungeons, mineshafts, and temples.
- Natural crop patches in new chunks.
- Admin commands during testing.

## What To Try First

Break grass in a biome that matches the crop you want, explore village/farm-style loot, then use seed packets when you find them. Rice and other special crops may be weighted toward specific biome groups rather than appearing everywhere.

## Seed Packets

Temperate packets focus on lettuce, corn, tomato, onion, and some vanilla crops. Tropical packets focus on rice and warm-climate vanilla seeds.

See [Seed Packets](../gardening/seed-packets.md) for exact data.
"""))


def station_pages():
    add("stations/index.md", page("Cooking Stations", """
Stations are built from normal blocks. Players interact with the station block, while Heirloom validates the supporting structure below or nearby.

[Animated Kitchen](animated-kitchen.md) adds craftable furniture with moving parts for these stations. It is an optional installation; block-built stations continue to work.

Use `/hl tutorial` for private, clickable building and cooking lessons when PacketEvents is installed. See [In-game Station Tutorials](../tutorials/station-tutorials.md).

| Station | Build | Main Role |
| --- | --- | --- |
| Oven | Stone pressure plate on a smoker | Baking, roasting, drying, long heat chains |
| Boiling Pot | Cauldron or water cauldron over a campfire or soul campfire | Soups, rice, pasta, cheese, jam, wet recipes |
| Mixing Bowl | Flower pot on any stripped block | Dough, creams, mixed prep, grinding-style steps |
| Cutting Board | Wooden pressure plate on any stripped block | Chopping, slicing, mincing, flour and prep items |
| Frying Pan | Heavy weighted pressure plate on a furnace | Eggs, pancakes, fried meals, fast heat |
| Barista Machine | Iron trapdoor above quartz stairs, with Cafe installed | Cafe drink assembly |
| Mixology Table | Any wooden pressure plate on an iron block, with Heirloom Mixology installed | Liqueurs and shaken drinks |
| Juicer | Upward-facing Dropper, clear Glass, any carpet; Heirloom Mixology enabled | Three produce items into two bottles |

## How To Think About Stations

Stations are not skins for one crafting menu. Each station teaches a different kind of recipe: prep stations make intermediate ingredients, heat stations transform them, and addon stations finish specialized chains. If a recipe does not match, search the ingredient and check the station before assuming the item is broken.

Each station page lists practical first recipes, common chains, and its generated recipe table.
"""))
    add("stations/oven.md", station_page(
        "Oven",
        "Build an Oven with a `STONE_PRESSURE_PLATE` on top of a `SMOKER`.",
        "The Oven handles baking, roasting, drying, and some chain steps such as bread, pizza, and coffee roasting.",
        "Oven",
        "If the station does not activate, confirm the plate is directly above a smoker and that the clicked block is the plate.",
    ))
    add("stations/boiling-pot.md", station_page(
        "Boiling Pot",
        "Build a Boiling Pot with a `CAULDRON` or `WATER_CAULDRON` over a `CAMPFIRE` or `SOUL_CAMPFIRE`.",
        "The Boiling Pot handles wet recipes, soups, cheese, rice, pasta, and recipes that return buckets or bottles.",
        "Boiling Pot",
        "Water buckets are recipe ingredients for some recipes. Avoid sneak-right-clicking when you mean to add the bucket as an ingredient, because sneak interaction may allow vanilla cauldron behavior.",
    ))
    add("stations/mixing-bowl.md", station_page(
        "Mixing Bowl",
        "Build a Mixing Bowl with a `FLOWER_POT` on any `STRIPPED_` log, wood, stem, hyphae, or bamboo block.",
        "The Mixing Bowl handles dough, mixing, cold preparation, and Cafe grinding steps.",
        "Mixing Bowl",
        "Use a shovel-style tool for mixing interactions. In survival, use a pickaxe if you intend to break the station cleanly.",
    ))
    add("stations/cutting-board.md", station_page(
        "Cutting Board",
        "Build a Cutting Board with any wooden pressure plate on any `STRIPPED_` block.",
        "The Cutting Board handles prep work such as flour, pasta, minced ingredients, and sliced recipe steps.",
        "Cutting Board",
        "Use sword or axe-style tools for chopping interactions. Non-wood pressure plates are reserved for other stations or ignored.",
    ))
    add("stations/frying-pan.md", station_page(
        "Frying Pan",
        "Build a Frying Pan with a `HEAVY_WEIGHTED_PRESSURE_PLATE` on top of a `FURNACE`.",
        "The Frying Pan handles eggs, bacon, pancakes, fried rice, and other fast heated foods.",
        "Frying Pan",
        "If a recipe does not match, use `/hl search <ingredient>` and confirm every ingredient belongs at this station.",
    ))
    add("stations/barista-machine.md", station_page(
        "Barista Machine",
        "Build a Barista Machine with an `IRON_TRAPDOOR` above `QUARTZ_STAIRS`. The Cafe addon must be installed and registered.",
        "The Barista Machine pulls espresso, tea, cocoa, boba, iced drinks, and milk-based drinks from Cafe ingredients.",
        "Barista Machine",
        "If the station acts like normal blocks, confirm HeirloomCafe loaded and `/hlc help` works.",
    ))
    add("stations/mixology-table.md", station_page(
        "Mixology Table",
        "Place any wooden pressure plate directly on an `IRON_BLOCK`. Interact with the plate. Heirloom Mixology must be installed and registered.",
        "Add the exact ingredients; an existing bottled ingredient supplies the drink's container. Juice supplies the bottle for the shaken Piña Colada and Virgin Daiquiris. Start shaking, wait for the eight-second cycle, then collect three drinks from the centered row. Reusable infusions and liqueurs produce one bottle.",
        "Mixology Table",
        "Confirm `/hlo info` shows Heirloom Mixology active. If alcoholic recipes are missing, read the Distillery compatibility diagnostic and check Cafe for coffee recipes. Extra ingredients or old standalone spirit stock do not satisfy integrated recipes.",
    ))
    add("stations/juicer.md", station_page(
        "Juicer", "Build an upward-facing `DROPPER` with `GLASS` above it and any carpet on top.",
        "Blend three fruit or vegetable items for ten seconds, then bottle the juice. Heirloom Mixology must be active.",
        "Juicer", "Click the glass; use an empty hand to start and a Glass Bottle to collect. Left-click refunds ingredients.",
    ))


def recipes_pages():
    add("recipes/index.md", page("Recipes", """
Recipes are loaded from JSON and indexed into the in-game browser. Players usually use `/hl recipes` or `/hl search`, while server owners edit JSON files.

## How To Read Recipe Docs

- Station pages explain workflow and list recipes by station.
- [Default Recipe Index](default-recipes.md) is the full linked lookup.
- [Recipe Chains](recipe-chains.md) explains common progression paths.

## Important Concepts

- Required and optional ingredient slots.
- Recipe rules that change names, quality, properties, visuals, or return items.
- Weighted outputs for recipes with chance-based results.
- Addon recipes that appear only when their addon registers.
"""))
    for station, filename in [
        ("Oven", "station-oven.md"),
        ("Boiling Pot", "station-boiling-pot.md"),
        ("Mixing Bowl", "station-mixing-bowl.md"),
        ("Cutting Board", "station-cutting-board.md"),
        ("Frying Pan", "station-frying-pan.md"),
        ("Barista Machine", "station-barista-machine.md"),
        ("Mixology Table", "station-mixology-table.md"),
        ("Juicer", "station-juicer.md"),
    ]:
        add(f"recipes/{filename}", page(f"{station} Recipes", station_recipe_table(station, "../", "../../reference/", "../../")))
    add("recipes/default-recipes.md", build_recipe_index())
    add("recipes/recipe-chains.md", page("Recipe Chains", """
Some Heirloom recipes are deliberately chained. A station result can stay on the station and become an ingredient in the next step.

## Common Chains

- Flour -> dough -> bread, pizza, pasta, pancakes, doughnuts.
- Rice -> cooked rice -> sushi-style recipes.
- Corn -> cornmeal -> taco shell and related recipes.
- Coffee cherry -> light beans -> medium beans -> dark beans -> espresso drinks.
- Green tea leaves -> dried green tea -> chance for matcha powder -> matcha latte.
- Mixology spirits -> liqueurs, Gin, Sweet Vermouth, Red Bitter Aperitif or Aromatic Bitters -> shaken cocktails at the Mixology Table. Coffee Liqueur requires Cafe; Rum does not.

## How To Explore Chains In Game

Use `/hl search <ingredient>` or click ingredients in the recipe browser. The wiki index links recipe outputs back to the recipe that creates them where possible.
"""))


def gardening_pages():
    add("gardening/index.md", page("Gardening", f"""
{image("../images/showcase/rice.gif", "Heirloom crops use custom display visuals and growth stages.")}

Core crops are Lettuce, Onion, Corn, Tomato, and Rice. Addons can register additional crops, such as Distillery grapes and Cafe coffee cherries.

{gardening_crop_grid()}

## What A Crop Is

A crop is a real block plus a display entity and stored data. The block gives Minecraft something to protect, break, and interact with; the display gives Heirloom its custom visual stages; stored data tracks crop ID, growth state, facing, and optional quality.

## The Growth Loop

1. Obtain a crop item or seed packet.
2. Plant it on a valid block for its plant type.
3. Let the growth timer advance through stages.
4. Right-click the mature crop to harvest.
5. If `replant_after_harvest` is enabled, the crop resets to an early stage instead of disappearing.

## Crop Types At A Glance

- Lettuce is the simplest short ground crop.
- Onion uses allium-style placement.
- Corn is a tall crop and needs vertical room.
- Tomato is a vine and needs a wall face.
- Rice is aquatic and needs water above valid soil.

## Quality And Drops

Harvest settings define normal drops, bonus drops, replanting, sounds, and quality chance. Fortune can improve configured bonus drops, and compatible custom enchantments can add effective Fortune or force replanting.

## Acquisition

Survival access comes from grass drops, seed packets, chest loot, and natural patches. World generation and chest loot only affect new content, so old worlds may need starter items, seed packets, or admin seeding.
"""))
    for cid in ["LETTUCE", "ONION", "CORN", "TOMATO", "RICE"]:
        add(f"gardening/{slug(cid)}.md", crop_page(cid))
    add("gardening/plant-types.md", page("Plant Types", """
Plant types define the physical block behavior behind a crop. Pick the type that matches how the crop should exist in the world, not only how the final display should look.

| Type | Used By | Placement | Practical Notes |
| --- | --- | --- | --- |
| `SHORT_PLANT` | Lettuce | Ground plant on valid soil | Best default for simple crops |
| `ALLIUM` | Onion | Flower-style ground plant | Useful for small vegetable visuals |
| `TALL_PLANT` | Corn | Tall visual crop with vertical room | Needs space above the base block |
| `ORCHARD_PINEAPPLE` | Mixology Pineapple | Short fern on valid soil | Upright fruit grows in the fern |
| `VINE` | Tomato, grapes | Wall-attached vine | Needs a face to attach to; poor fit for random flat patches |
| `AQUATIC` | Rice | Soil under water | Needs water setup and should be tested in claims |
| `BUSH` | Addon/extended crops | Bush-style blocks | Good for berry-like crops |
| `HANGING` | Addon/extended crops | Ceiling-attached blocks | Best for decorative or cave crops |

Plant types are data-driven, but every type still depends on Minecraft block rules. If a crop uses a real plant block, protection plugins and physics can affect it.
"""))
    packets = SEEDS.get("seed_packets", {})
    packet_rows = []
    for pid, cfg in packets.items():
        seeds = ", ".join(f"`{s['item_id']}` ({s.get('weight', 1)})" for s in cfg.get("seeds", []))
        packet_rows.append([f"`{pid}`", cfg.get("description", ""), f"{cfg.get('drops_min')}-{cfg.get('drops_max')}", seeds])
    add("gardening/seed-packets.md", page("Seed Packets", f"""
Seed packets are custom items that roll weighted seeds when opened. They are useful when you want survival discovery without requiring every crop to drop from grass.

{table(["Packet", "Description", "Drops", "Weighted contents"], packet_rows)}

Players open packets by using the item. If their inventory is full, extra seeds drop nearby.

## Design Advice

Use seed packets for starter kits, market crates, quest rewards, and rare biome crops. Keep the drop count small if packets are common, otherwise a single packet can skip the early farming loop.
"""))
    add("gardening/wild-discovery.md", page("Wild Discovery And Loot", """
`seed_acquisition.json` controls non-command crop discovery.

## Grass Drops

Grass drops use a base chance plus biome modifiers. The bundled config makes lettuce and onion common in plains/meadows, tomato more common in forests, corn more common in plains/savanna, and rice more common in swamp/jungle-style areas.

## Chest Loot

Village, farm, dungeon, mineshaft, and temple loot tables can receive Heirloom crop items or seed packets. The chance is per generated chest, not a guarantee for every structure.

## World Generation

Natural patches are placed in new chunks only. Ground crops are the safest candidates. Vine crops need walls, and aquatic crops need water placement, so test those carefully before enabling broad worldgen.

!!! warning
    World generation and chest loot only affect newly generated or newly filled content. Use commands, seed packets, or custom events if you need to seed old worlds.
"""))
    add("gardening/ecoenchants.md", page("EcoEnchants Integration", """
Heirloom reads enchantment integration data from `enchantment_integrations.json` and resolves registered Bukkit enchantments by namespaced key.

## Bundled EcoEnchants Hooks

| Purpose | Keys | Behavior |
| --- | --- | --- |
| Force replant | `ecoenchants:replant`, `ecoenchants:replenish` | Crop resets after harvest even when it would normally be removed |
| Fortune bonus | `ecoenchants:prospector` | Adds +1 effective Fortune per enchantment level |

## How This Affects Players

A replant enchantment makes farming smoother but still respects whether the crop is mature and harvestable. A Fortune bonus improves configured drop rolls; it does not invent drops that the crop JSON never defines.

## Server Owner Notes

You can add other enchantment keys in the same `namespace:name` format. After editing, reload and harvest a mature test crop with the enchanted tool to confirm the integration is detected.
"""))


def food_system_pages():
    add("food-systems/index.md", page("Food Systems", """
Heirloom food is more than hunger points. Items can carry quality, dietary labels, food properties, potion effects, creator data, consume returns, and visual IDs.

## The Important Distinction

- Dietary properties answer "what is this food made from?" Examples: vegan, vegetarian, gluten-free.
- Food properties answer "what happens when I eat this?" Examples: golden, chorus, sweet, energizing.
- Quality answers "how well did this food turn out?"

These systems can overlap on one item. A high-quality vegan food can also be `GOLDEN`, `CHORUS`, and a player's favourite food.
"""))
    props = DIET.get("dietary_properties", {})
    prop_rows = []
    for pid, cfg in props.items():
        prop_rows.append([f"`{pid}`", cfg.get("display_name", ""), cfg.get("description", ""), ", ".join(f"`{p}`" for p in cfg.get("implies", []))])
    add("food-systems/dietary-properties.md", page("Dietary Properties", f"""
Dietary labels use a blacklist model. A recipe is assumed to satisfy a property unless one of its ingredients violates that property.

{table(["Property", "Display", "Meaning", "Implies"], prop_rows)}

## How Calculation Works

When a recipe is previewed or crafted, Heirloom checks the selected ingredients. Vanilla ingredients are compared against dietary config. Custom ingredients can already carry stored dietary data, so a later recipe does not need to know every raw ingredient that originally created them.

## Inheritance Example

If a custom sauce was made with milk, and that sauce is later used in a sandwich, the sandwich should not become vegan just because the sandwich recipe only sees `SAUCE`. Stored dietary data keeps that history attached to the ingredient.

## Example: Adding Kosher Or Halal

You can add server-specific dietary rules the same way the bundled file defines `VEGAN`, `VEGETARIAN`, and `GLUTEN_FREE`. The important idea is that a property describes what is allowed, and its `violators` list describes what breaks that rule.

For example, a simple halal-style rule might blacklist pork materials and pork-based custom foods:

```json
"HALAL": {{
  "display_name": "Halal",
  "description": "Contains no server-defined non-halal ingredients",
  "violators": {{
    "items": [
      "PORKCHOP",
      "COOKED_PORKCHOP"
    ],
    "custom_items": [
      "BACON",
      "CHRISTMAS_HAM"
    ]
  }}
}}
```

A simple kosher-style rule can use the same structure:

```json
"KOSHER": {{
  "display_name": "Kosher",
  "description": "Contains no server-defined non-kosher ingredients",
  "violators": {{
    "items": [
      "PORKCHOP",
      "COOKED_PORKCHOP"
    ],
    "custom_items": [
      "BACON",
      "CHRISTMAS_HAM"
    ]
  }}
}}
```

After adding those entries under `dietary_properties`, reload and test a few chains. If `BACON` is made from `PORKCHOP`, the bacon will not receive `HALAL` or `KOSHER`. If that bacon is later used in `EGGS_AND_BACON`, `BLT`, or a custom burger, the finished food also will not receive those properties because custom ingredients carry their stored dietary data forward.

!!! note
    Heirloom enforces the rules you configure; it does not decide real-world religious law. If your server also wants to treat alcohol, shellfish, meat-and-dairy combinations, or specific addon drinks as disallowed, add those vanilla or custom item IDs to the appropriate `violators` lists and test the recipe chains players actually use.

## Hierarchy

`hierarchy_rules` hide weaker labels when a stronger label is present. Bundled data treats `VEGAN` as implying `VEGETARIAN`, so vegan foods do not need to show both labels.

## Contains Lines

The `contains_settings` block controls "Contains:" lore. Use it for practical warnings, not just marketing labels. It is most useful for common allergens, roleplay restrictions, or server-specific diet rules.
"""))
    add("food-systems/food-properties.md", page("Food Properties", """
Food properties are gameplay tags stored on the item. They are not just wiki categories: when you eat the item, Heirloom loops over every stored property and applies the matching behavior.

## Where Properties Come From

A property can be added by a recipe action, usually `ADD_METADATA` with key `food_property`, or it can already exist on an ingredient. When a recipe finishes, Heirloom starts with properties already on the output, then adds every property found on every input item. The result is stored back on the output and shown in lore.

That means properties can stack through recipe chains.

## Worked Example: Powerful Pancakes

1. Make jam in the Boiling Pot with `CHORUS_FRUIT`. The jam rule adds `CHORUS`.
2. Make another jam with `GOLDEN_APPLE`. The jam rule adds `GOLDEN`.
3. Use property-bearing jam as a pancake topping in the Frying Pan. Pancakes inherit the jam's stored properties.
4. Eat the pancakes. The food applies every stored food property, then any JSON-defined effects, then favourite-food effects if pancakes are your favourite.

In bundled data, honey pancakes add honey naming, quality, and bottle return behavior. Honey does not add `SWEET` to pancakes unless a recipe or custom item explicitly stores `SWEET` as a food property. Server owners can add that behavior with recipe actions.

## Exact Property Effects

| Property | Effect when eaten |
| --- | --- |
| `GLOWING` | Glowing I for 30 seconds, beacon-style sound/message |
| `GOLDEN` | Regeneration II for 5 seconds and Absorption I for 2 minutes |
| `CHORUS` | Attempts a safe random teleport, like chorus fruit |
| `SWEET` | Speed I and Haste I for 10 seconds |
| `SPICY` | Fire Resistance I for 20 seconds, plus 1 second of visual fire |
| `COLD` | Slowness I for 5 seconds and Resistance II for 10 seconds |
| `ENERGIZING` | Speed II, Haste II, and Jump Boost I for 30 seconds |
| `NOURISHING` | Saturation III for 5 seconds |
| `HEALING` | Instant Health II |
| `AFFINITY` | If cooked by another player, Regeneration I for 10 seconds; Regeneration II if it is also your favourite food |
| `SOBERING` | If Distillery is loaded and inebriation is enabled, drains drunkenness by the configured amount, default 0.6‰, once per consumed serving |

## What Players See

The recipe browser preview can show food-property lore based on the selected ingredients. Finished items also carry the property lore. If the final food is placed as a serving food, the placed block stores the properties too, so bites can still apply the behavior.

## Server Owner Pattern

Use properties for intentional power chains. For example, a server could make maple syrup add `SWEET`, then pancakes made with `GOLDEN` jam and syrup would carry both the inherited jam property and the syrup property.

```json
{
  "type": "ADD_METADATA",
  "key": "food_property",
  "value": "SWEET"
}
```

Avoid relying on hidden balance. If a food should heal, sober, teleport, energize, or become a strong favourite-food candidate, put that behavior in the recipe or ingredient data.
"""))
    add("food-systems/quality-and-effects.md", page("Quality And Effects", """
Quality is stored on custom foods and ingredients. Crops can preserve and improve quality, recipes can set or add quality, and mastery can improve final results.

## Quality Sources

- `SET_QUALITY` gives an output a specific value.
- `ADD_QUALITY` increases the current value when a rule matches.
- If no explicit quality is supplied, crafted custom foods can inherit the best numeric quality from their inputs.
- Cooking Mastery adds a recipe-specific quality bonus to future crafts.
- Crops can store quality and keep it when replanted.

## Effect Sources

An eaten item can apply effects from:

- Its normal food value and saturation.
- Its `food_property` tags.
- Its JSON `effects` list.
- Favourite food behavior.
- Cooked-by social behavior.
- Distillery sobering integration if `SOBERING` is present.

## Debugging Balance

If a food is too weak, check whether the recipe actually adds a property or effect. If it is too strong, check inherited ingredients first; an intermediate item may be carrying properties into many later recipes.

Prepared foods should follow configured values. If a food needs regeneration, saturation, or another potion effect, define it explicitly in JSON.
"""))
    add("food-systems/favourite-social.md", page("Favourite And Social Bonuses", """
Favourite food and cooked-by metadata are player-data systems. They are separate from recipe matching, but they can combine with food properties at eating time.

## Favourite Food

Players choose a favourite with `/hl favourite`. Eating that custom food grants:

| Effect | Duration | Strength |
| --- | --- | --- |
| Regeneration | 30 seconds | I |
| Saturation | 15 seconds | II |
| Luck | 60 seconds | I |

The favourite check runs after food-property effects. A property-stacked favourite therefore applies both sets of behavior.

## Cooked By

When a player crafts edible output, Heirloom can store the crafter UUID. Later, favourite-food checks can reward the cook with a short regeneration effect if somebody else eats the favourite food they made.

## Affinity

`AFFINITY` also reads cooked-by metadata. If the food was cooked by someone else, it grants regeneration to the eater. If that same food is also the eater's favourite, the regeneration amplifier is increased.

## Data Storage

Player RPG data is saved under `plugins/Heirloom/playerdata/`. Favourite choice and mastery are stored per player.
"""))


def server_owner_pages():
    add("server-owners/index.md", page("Server Owner Guide", """
This section is for setup, permissions, diagnostics, claim protection, localization, updates, and operational safety.
"""))
    add("server-owners/configuration.md", page("Configuration", """
Core files live in `plugins/Heirloom/` after first startup.

| File | Purpose |
| --- | --- |
| `config.yml` | License key and locale |
| `custom_items.json` | Core item definitions |
| `recipes.json` | Core recipes |
| `crops.json` | Core crops |
| `dietary_properties.json` | Diet labels and hierarchy |
| `seed_acquisition.json` | Seed packets, grass drops, loot, world patches |
| `advancements.json` | Advancement definitions |
| `enchantment_integrations.json` | EcoEnchants and compatible enchantment keys |
| `lang/<locale>.yml` | Locale files |

Run `/hl reload` after supported JSON and language changes. Restart after jar, dependency, or large visual-pack changes.
"""))
    add("server-owners/permissions.md", page("Permissions", """
Use a permission plugin such as LuckPerms on production servers.

See [Permission Reference](../reference/permissions.md) for the full list.

Recommended default grants:

```text
/lp group default permission set heirloom.use true
/lp group default permission set heirloom.recipes true
/lp group default permission set heirloom.cookbook true
/lp group default permission set heirloom.advancements true
/lp group default permission set heirloom.favourite true
/lp group default permission set heirloom.mastery true
/lp group default permission set heirloom.tutorial true
```

Grant crop permissions if you keep the bundled crop permission nodes enabled.
"""))
    add("server-owners/commands.md", page("Commands", """
Core uses `/hl` or `/heirloom`. Distillery uses `/hld`. Cafe uses `/hlc`.

The full command list is in [Command Reference](../reference/commands.md).

## Admin Commands To Know

```text
/hl reload
/hl cheat
/hl give <item> [amount]
/hl debug test
/hld devmode status
/hlc list
```

`/hl give Orange_Liqueur` accepts a unique friendly alias, and tab completion includes these names. Full item IDs still work; use `ORCHARD_ORANGE_LIQUEUR` if an alias matches several items. Administrator drink grants receive the normal playable sample metadata.
"""))
    add("server-owners/language-files.md", page("Language Files", """
Heirloom bundles many locale files. Set the active locale in `config.yml`.

```yml
locale: en
```

Useful commands:

```text
/hl lang list
/hl lang missing <locale>
```

When making a custom translation, copy `lang/en.yml`, keep keys unchanged, translate only values, then run `/hl reload`.
"""))
    add("server-owners/region-protection.md", page("Region Protection", """
Heirloom uses two layers for protection compatibility.

## WorldGuard

- Cooking station interaction checks WorldGuard `INTERACT`.
- Planting and harvesting checks WorldGuard `BUILD`.

## Generic Claim Plugins

Planting fires a programmatic `BlockPlaceEvent`; harvesting fires a programmatic `BlockBreakEvent`. This gives plugins such as Towny, GriefPrevention, Lands, and similar systems a normal event to cancel.

## Test Before Launch

In a protected region, test:

- Planting a crop.
- Harvesting a crop.
- Using a cooking station.
- Breaking a station with ingredients.
"""))
    add("server-owners/diagnostics.md", page("Diagnostics", """
Use diagnostics after install, after updates, and after large config edits.

```text
/hl debug test
/hl debug runtests
/hl debug testall
```

The diagnostic suite checks item registry counts, cooked-rice recipe matching, crop registration, WorldGuard hook state, EcoEnchants detection, event bypass safety, and runtime GUI loading.

Other debug tools:

```text
/hl debug hunger
/hl debug actionbar <style>
```
"""))
    add("server-owners/updating.md", page("Updating And Migration Notes", """
## 2.5 Notes

- Startup banners are standardized and quieter.
- Recipe search is available through `/hl search`.
- Nexo and ItemsAdder visual resolution now share provider-neutral visual IDs.
- Prepared foods should no longer receive hidden hardcoded regeneration or bonus saturation.
- Onion and Allium crop content are bundled.
- Distillery grape crop definitions are restored.

## 2.0 Notes

- Region protection was rewritten around WorldGuard and standard Bukkit events.
- Generic `consume_return` was added.
- EcoEnchants replant and prospector hooks were added.
- Seed packets and world discovery were added.
- Native advancements, mastery, and favourite food systems were expanded.

## Update Checklist

1. Back up `plugins/Heirloom/`.
2. Stop the server.
3. Replace jars.
4. Start and read startup warnings.
5. Run `/hl debug test`.
6. Review custom food balance if you previously worked around hidden effects.
"""))


def customization_pages():
    add("customization/index.md", page("Customization", """
Heirloom content is mostly data-driven. Server owners can customize items, recipes, crops, diet labels, seed acquisition, advancements, and visual mappings.

## Recommended Workflow

1. Make one small JSON change.
2. Validate the file syntax.
3. Run `/hl reload` when the file supports reload.
4. Search the item or recipe in game.
5. Craft it once and inspect the output lore.
6. Only then build the next step of the chain.

This matters because Heirloom recipes can carry metadata forward. A mistake in an intermediate ingredient can affect every later recipe that uses it.
"""))
    add("customization/custom-foods.md", page("Custom Foods", """
Custom foods are defined in JSON under `custom_items` arrays. A custom food defines the item players can hold; recipes define how players make it.

## Minimum Edible Food

```json
{
  "id": "GOLDEN_PANCAKE",
  "name": "Golden Pancake",
  "base_material": "PLAYER_HEAD",
  "texture": "http://textures.minecraft.net/texture/...",
  "edible": true,
  "food_value": 8,
  "saturation": 6.0,
  "consume_seconds": 1.4,
  "animation": "EAT",
  "visual_id": "GOLDEN_PANCAKE"
}
```

## Advanced Fields To Know

- `consume_return`: gives an item back after eating.
- `item_model`: selects an item model such as `minecraft:lingering_potion` independently of `base_material`; a Potion remains drinkable. Juice also uses `color` for its tint.
- `placeable_servings`: makes the food placeable and eaten in servings.
- `feast`: enables shared-feast behavior.
- `effects`: applies explicit potion effects when eaten.
- `visual_id`: lets Nexo, ItemsAdder, CraftEngine, or MMOItems replace the visual without changing recipes.
- `station_texture`: uses a cosmetic player-head texture for the ingredient displayed on a station; the original inventory stack remains the source for matching, processing, refunds and recovery.

`station_texture` belongs to the custom item definition and accepts a real `textures.minecraft.net` texture URL. It does not change the inventory item or provider mapping. Heirloom Mixology uses it for fruit such as lemons and oranges; omitting it preserves the normal station visual.

## Common Mistakes

- Defining an item but never adding a recipe for it.
- Using a pretty `name` but forgetting the stable uppercase `id` used in recipes.
- Expecting a property effect without adding a recipe action or stored property.
- Using provider-specific visual IDs instead of stable Heirloom visual IDs.

## How To Test

Use `/hl give <id>` to inspect the item definition, then craft it through the intended recipe to inspect inherited quality, properties, and returns.
"""))
    add("customization/custom-recipes.md", page("Custom Recipes", """
Recipes define a station, output, processing time, ingredients, actions, and optional rules. The output can be changed by base actions, rule actions, inherited input metadata, and quality logic.

## Qualified ingredients

An ingredient may refine a canonical custom identity with an addon-owned qualifier, for example `{"custom_item":"DISTILLERY_WINE","qualifier":"distillery:sparkling_wine"}`. The addon registers its metadata predicate and cosmetic preview through `api.items().registerIngredientQualifier(addonId, qualifierId, canonicalCustomItemId, matches, preview)`. The owning addon and its item must be active. Matching checks the canonical identity first, then validates the original item's metadata. Missing registrations, missing originals and predicate failures do not match.

Recipes without a qualifier retain their normal meaning: ordinary Wine recipes also accept valid Sparkling Wine. A qualifier cannot be attached to vanilla items, provider items or tags. Rule matchers use `options` containing the qualified ingredient. Unavailable required qualifiers disable their recipe unless another alternative remains usable. Safe previews preserve appearance and tint without item identity, brewing credentials or effects; they cannot be extracted as genuine ingredients. Registrations participate in reload rollback and addon/item-removal cleanup.

## Declared Output Variants

Decorator-backed dynamic recipes can declare `"output_variants": [{"output": "ORCHARD_APPLE_JUICE", "selections": [0]}]`. Each entry links a named result to this recipe and supplies one zero-based ingredient-option index per slot for its preview. The decorator still constructs and validates the actual output. Remap selections when optional addon options are filtered. One Juicer recipe supports all pure outputs and mixed juice without duplicate recipes.

## Minimum Recipe

```json
{
  "id": "SWEET_PANCAKES",
  "station": "FRYING_PAN",
  "output": "PANCAKES",
  "processing_time": 160,
  "ingredients": [
    { "type": "REQUIRED", "max": 1, "options": [{ "custom_item": "BAG_OF_FLOUR" }] },
    { "type": "REQUIRED", "max": 1, "options": [{ "item": "EGG" }] },
    { "type": "OPTIONAL", "max": 1, "options": [{ "item": "HONEY_BOTTLE" }] }
  ],
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Sweet Pancakes" },
    { "type": "ADD_METADATA", "key": "food_property", "value": "SWEET" }
  ]
}
```

## Advanced Pattern: Property Chain

Put properties on intermediate ingredients when you want players to build stronger food through multiple steps. For example, jam can get `CHORUS` from chorus fruit, then pancakes inherit that property when the jam is used as a topping.

Use `required_property` on an individual ingredient option when a recipe must accept only a matching ingredient that carries a specific inherited property:

```json
{
  "type": "REQUIRED",
  "max": 1,
  "options": [
    { "custom_item": "DOUGH", "required_property": "CORNMEAL" }
  ]
}
```

This accepts Dough made from Cornmeal and rejects ordinary flour Dough. Property names are case-insensitive, and the required property appears in recipe previews.

## Universal recipe item references

Every recipe-emitted item position uses the same identity shape: exactly one of `item`, `custom_item`, or `provider_item`, plus an optional sibling `amount`. This applies to the primary `output`, each `weighted_outputs` entry, every `byproducts` entry, and the item emitted by `SET_RETURN_ITEM` or `SET_CONSUME_RETURN`.

```json
{
  "output": { "custom_item": "PANCAKES", "amount": 2 },
  "weighted_outputs": [
    { "item": "BOWL", "amount": 1, "weight": 5 },
    { "provider_item": "mmoitems:CONSUMABLE:Lucky_Bite", "amount": 1, "weight": 1 }
  ],
  "byproducts": [
    { "item": "GLASS_BOTTLE", "amount": 1 },
    { "provider_item": "craftengine:my_pack:spent_filter", "amount": 1 }
  ],
  "actions": [
    { "type": "SET_RETURN_ITEM", "provider_item": "itemsadder:my_pack:mixing_bowl", "amount": 1 },
    { "type": "SET_CONSUME_RETURN", "provider_item": "mmoitems:MISCELLANEOUS:Empty_Vial", "amount": 1 }
  ]
}
```

The object form is the preferred authoring format. Existing content remains valid: a legacy string primary `output`, a weighted entry's legacy `output` or `item`, a byproduct's legacy `item`, and an action's legacy `value` are all interpreted as item references. Do not put two identity fields in one object; `item`, `custom_item`, and `provider_item` are mutually exclusive. `amount` belongs next to the chosen identity (and is context-specific: stack size for outputs, byproducts, and returns, never part of the provider ID).

Provider names are normalized (`MMOITEMS`, `mmoitems`, and `MmoItems` name the same provider), but everything after the first colon is provider-owned and preserves its exact casing. For MMOItems, both the `TYPE` and `ID` therefore remain exact: `mmoitems:SWORD:POISONED_SWORD` is not interchangeable with a differently cased suffix.

## MMOItems sword example

This Cutting Board recipe consumes one MMOItems poison berry, a vanilla iron ingot, and a stick to create an MMOItems sword. The primary output uses the flattened reference directly; the recipe has no separate provider-specific output field.

```json
{
  "id": "MMOITEMS_POISONED_SWORD",
  "station": "CUTTING_BOARD",
  "output": { "provider_item": "mmoitems:SWORD:POISONED_SWORD", "amount": 1 },
  "processing_time": 100,
  "ingredients": [
    { "type": "REQUIRED", "max": 1, "options": [{ "provider_item": "mmoitems:MATERIAL:POISON_BERRIES" }] },
    { "type": "REQUIRED", "max": 1, "options": [{ "item": "IRON_INGOT" }] },
    { "type": "REQUIRED", "max": 1, "options": [{ "item": "STICK" }] }
  ]
}
```

## Availability and provider-owned stacks

Providers and their templates are optional. A missing provider or referenced template leaves the recipe registered and visible, but marks it unavailable with the missing reference as the reason. Heirloom preflights the primary result, every weighted alternative, byproducts, and required return references before consuming ingredients; it never partially crafts or consumes inputs after a failed preflight.

Stacks created by a provider are opaque. Heirloom does not add PDC, lore, quality, dietary data, names, textures, visuals, or any other output mutation to them. A provider byproduct cannot set `inherit_metadata: true`. If any possible primary result is provider-owned, output-mutating actions are invalid, including `SET_CONSUME_RETURN`; `SET_RETURN_ITEM` is a separate emitted stack and is not an output mutation. An ordinary Heirloom primary result may use either action to emit a provider craft return or consume return.

## Common Rule Actions

- `SET_PROPERTY` with key `NAME`: changes display name.
- `ADD_METADATA` with key `food_property`: adds a food property that can be inherited and applied when eaten.
- `SET_RETURN_ITEM`: emits a return stack when crafting completes; its item reference may be provider-owned.
- `SET_CONSUME_RETURN`: records an item reference to emit after eating; it may be provider-owned only when the primary result is an ordinary Heirloom item.
- `SET_VISUAL_ITEM`: swaps to a provider-neutral visual variant.
- `ADD_QUALITY` and `SET_QUALITY`: tune output quality.

## Common Mistakes

- Using `SET_PROPERTY` for `food_property`; bundled property recipes use `ADD_METADATA` for inherited food properties.
- Putting a custom item in `item` instead of `custom_item`.

## External provider ingredients

Use one provider-prefixed field to accept an exact item owned by Nexo, ItemsAdder, CraftEngine, or MMOItems:

```json
{ "provider_item": "nexo:tomato" }
{ "provider_item": "itemsadder:my_pack:tomato" }
{ "provider_item": "craftengine:my_pack:tomato" }
{ "provider_item": "mmoitems:MATERIAL:POISON_BERRIES" }
```

Only the first colon is a separator. The provider ID after it is passed unchanged to the provider API. `provider_item` works in ingredient options and dynamic rule matchers, as well as every recipe-emitted item position described above. Providers remain optional; unavailable options stay visible but cannot match, and other valid options continue to work. Exact provider identity is required, so an external item never matches as its underlying vanilla material.
- Forgetting that optional slots default to `0-max`, so rules must handle the missing-input case.
- Editing JSON and testing only `/hl give`; recipe actions and inheritance only appear when the recipe is crafted.

## How To Test

Run `/hl reload`, search the recipe, craft every branch you changed, and inspect lore. For inheritance tests, craft the intermediate ingredient first, then use that exact item in the next recipe.
"""))
    add("customization/custom-crops.md", page("Custom Crops", """
Crop JSON defines plant type, growth behavior, planting rules, textures, and harvest drops.

## Minimum Crop Shape

A crop needs an item ID, plant type, growth settings, planting rules, textures, and harvest rules. Use an existing crop close to your desired behavior as the starting point: lettuce for ground crops, tomato for vines, rice for aquatic crops, corn for tall crops.

## Important Sections

- `growth`: duration, variance, stages, and scale.
- `planting`: valid blocks, item consumption, and permission.
- `textures`: growing and ripe display textures.
- `harvest`: drops, bonus drops, replanting, sounds, and quality chance.

## Design Choices

Choose a plant type based on physical behavior. A tomato-like crop should be a vine because it needs a wall. A rice-like crop should be aquatic because the water requirement is part of gameplay. Do not use a display offset to fake a crop type that has different block rules.

## Common Mistakes

- Enabling world generation for a vine crop without natural wall positions.
- Giving aquatic crops to players before they know the water placement rule.
- Adding bonus drops that require Fortune, then testing with an unenchanted tool.
- Forgetting crop permissions when planting works for admins but not players.

## How To Test

Plant it, wait or speed up growth, harvest it, confirm drops, confirm replanting, then test in a protected region with a normal player.
"""))
    add("customization/seed-acquisition.md", page("Seed Acquisition", """
`seed_acquisition.json` controls how crops enter survival gameplay.

Use it to configure:

- Seed packets.
- Grass drops.
- Chest loot injection.
- Natural world patches.

## Balancing Advice

Use grass drops for common crops, seed packets for curated rewards, chest loot for exploration, and world patches for discovery. Avoid enabling all methods at high rates or rare crops stop feeling rare.

Keep world-generation changes conservative on live servers. They only affect new chunks and can make rare crops too common if patch chances are high.
"""))
    add("customization/advancements.md", page("Advancements", """
`advancements.json` controls Heirloom advancement definitions. Advancements can track foods eaten, crops harvested, quality milestones, and recipe progress.

## Useful Advancement Shapes

- First-time milestones teach players that a system exists.
- Collections encourage recipe exploration.
- Quality goals reward farming and mastery.
- Counters reward repeated cooking or harvesting.

After editing, run `/hl reload` and test with `/hl advancements`.
"""))
    add("customization/visuals-overview.md", page("Visual Integrations Overview", """
Heirloom works without a resource pack by using vanilla materials and player-head textures. Optional providers can replace that presentation.

## Provider-Neutral Flow

1. Item definitions declare `visual_id`.
2. Recipes can call `SET_VISUAL_ITEM`.
3. `VisualItemResolver` asks registered providers for that visual.
4. If no provider has it, Heirloom falls back to the normal item.

This keeps visual mapping data independent from Nexo, ItemsAdder, CraftEngine, or MMOItems. Direct `provider_item` recipe references are a different feature: use them only when the recipe deliberately requires or emits that provider's exact stack.

## Practical Rule

Use Heirloom item IDs and visual IDs as stable public names. Let Nexo, ItemsAdder, CraftEngine, or MMOItems map those names to models. Do not bake a provider namespace into a recipe unless the recipe deliberately needs that exact provider stack.
"""))
    add("customization/nexo.md", page("Nexo Integration", """
Nexo is a soft dependency. Heirloom should load without it.

## Recommended Mapping

Create Nexo items that match Heirloom visual IDs. A common naming convention is:

```text
heirloom_<lowercase_visual_id>
```

Examples:

```text
heirloom_tomato
heirloom_ice_cream_chorus
heirloom_espresso
```

## Testing

Start the server with Nexo installed, run `/hl reload`, then create the item through Heirloom rather than directly through Nexo. That proves the provider path is being used by recipes and commands.
"""))
    add("customization/itemsadder.md", page("ItemsAdder Integration", """
ItemsAdder is a soft dependency. Heirloom uses the same logical `visual_id` path for ItemsAdder as it does for Nexo.

## Recommended Mapping

Create ItemsAdder custom stacks for the visual IDs your server wants to replace. Keep IDs stable so recipe actions such as `SET_VISUAL_ITEM` do not need to change.

## Fallback Rule

If ItemsAdder is missing or an item is not mapped, the normal Heirloom item is still created. Test this fallback before launch so players are not blocked by a visual-pack mistake.
"""))
    add("customization/craftengine.md", page("CraftEngine Integration", """
CraftEngine is a soft dependency. Use provider-neutral `visual_id` mappings when a normal Heirloom item only needs a different presentation, or use an exact `provider_item` reference when a recipe must consume or emit a CraftEngine-owned stack.

## Exact item references

```json
{ "provider_item": "craftengine:my_pack:tomato" }
```

The `craftengine` provider name is case-insensitive, while `my_pack:tomato` is passed to CraftEngine unchanged. If CraftEngine or the referenced item is unavailable, affected recipes remain visible and unavailable instead of consuming ingredients.
"""))
    add("customization/mmoitems.md", page("MMOItems Integration", """
MMOItems is a soft, optional integration. Heirloom does not bundle MMOItems or MythicLib, and it continues to load when either is absent. Install and configure MMOItems and MythicLib separately before enabling recipes that reference MMOItems stacks.

## Exact MMOItems references

Use the flattened form `mmoitems:<TYPE>:<ID>` for inputs and every recipe-emitted item position:

```json
{ "provider_item": "mmoitems:MATERIAL:POISON_BERRIES" }
{ "provider_item": "mmoitems:SWORD:POISONED_SWORD", "amount": 1 }
```

The provider name is normalized, but the MMOItems suffix is exact and case-preserving. Keep both `TYPE` and `ID` exactly as MMOItems defines them. Missing MMOItems or a missing template does not hide or deregister the recipe; Heirloom shows it as unavailable, preflights every weighted result and required emitted reference, and consumes nothing.

## Resource-pack merge

Normal generated Heirloom visuals use the MMOItems type/id convention `MISCELLANEOUS:HEIRLOOM_<ID>`. In the supplied YAML fragment, merge each root `HEIRLOOM_<ID>` entry into `plugins/MMOItems/item/miscellaneous.yml`; keep its `model` field inside `base`. Separately merge `mmoitems/resourcepack/assets/heirloom/` into the resource pack your server builds and delivers. MMOItems does not build or distribute that pack for you, and Heirloom does not replace your pack's deployment workflow.

See the [official MMOItems item-textures documentation](https://docs.phoenixdevt.fr/mmoitems/features/item-textures.html) for the resource-pack side of the setup. When MMOItems reloads, Heirloom refreshes the provider on the next Bukkit tick so the refreshed MMOItems registry is ready first.

## Opaque result rule

An MMOItems stack created as a primary result remains owned by MMOItems: Heirloom cannot add lore, PDC, names, textures, quality, dietary data, or a consume return to it. Use an ordinary Heirloom primary output when you need output-mutating actions; that ordinary result may still return an MMOItems stack on craft or consumption.
"""))
    add("customization/web-generator.md", page("Web Generator Workflow", """
The web generator is useful when you do not want to hand-write recipe JSON.

Use it to draft recipes, then review the exported JSON before putting it on a production server.

Recommended workflow:

1. Build the recipe in the generator.
2. Export JSON.
3. Paste into the correct recipe file.
4. Validate JSON formatting.
5. Run `/hl reload`.
6. Test with `/hl search <recipe>`.
7. Craft the recipe once to confirm actions, inherited properties, return items, and visuals.

Generator link: `https://kernel-person.github.io/heirloom-generator/`
"""))


def orchard_gated_recipe_table() -> str:
    resources = PLUGIN_ROOT / "heirloom-orchard/src/main/resources"
    recipes = read_json(resources / "recipes-orchard-draft.json")["recipes"]
    draft_items = read_json(resources / "owner-assets-orchard.json")["draft_items"]
    nutrition = {item["id"]: item for item in draft_items}
    rows = []
    for recipe in recipes:
        ingredients = []
        for ingredient in recipe["ingredients"]:
            count = ingredient.get("min", 1)
            labels = []
            for option in ingredient["options"]:
                ingredient_id = option.get("custom_item", option.get("item"))
                labels.append(title_from_id(ingredient_id))
            ingredients.append(f"{count}× " + " or ".join(labels))
        item = nutrition[recipe["output"]]
        returns = [action["value"] for action in recipe.get("actions", [])
                   if action["type"] == "SET_CONSUME_RETURN"]
        rows.append([
            f"**{title_from_id(recipe['output'])}**<br>`{recipe['id']}`",
            recipe["station"],
            "<br>".join(ingredients),
            f"{item['food_value']} hunger / {item['saturation']} saturation",
            title_from_id(returns[0]) if returns else "None",
        ])
    return table(["Gated recipe", "Station", "Exact ingredients", "Nutrition", "Consume return"], rows)


def orchard_mode_table() -> str:
    """Check catalog counts against the selected source IDs before publishing them."""
    item_ids = {item["id"] for item in ITEMS if item.get("_source") == "Orchard"}
    recipe_ids = {recipe["id"] for recipe in ALL_RECIPES if recipe.get("_source") == "Orchard"}
    mixology = set(ORCHARD_MIXOLOGY["recipe_ids"])
    spirits = set(ORCHARD_MIXOLOGY["fallback_spirit_ids"])
    coffee = set(ORCHARD_MIXOLOGY["cafe_recipe_ids"])
    non_alcoholic = set(ORCHARD_MIXOLOGY["non_alcoholic_recipe_ids"])
    optional_juices = {"ORCHARD_" + row["id"] + "_JUICE" for row in
            read_json(ORCHARD_RESOURCES / "juice-produce-orchard.json")["produce"] if row.get("optional")}
    families = ORCHARD_MIXOLOGY.get("dynamic_recipe_families", {})
    def outputs_for(recipes: set[str]) -> set[str]:
        return recipes | {output for recipe in recipes for output in families.get(recipe, [])}
    if not mixology | spirits <= recipe_ids or not spirits <= item_ids:
        raise ValueError("Orchard Mixology catalog references missing source definitions")
    rows = []
    for key, label, cafe, alcohol in (
        ("standalone", "Mixology", False, "fallback"),
        ("standalone_cafe", "Mixology + Cafe", True, "fallback"),
        ("distillery", "Mixology + compatible Distillery", False, "integrated"),
        ("distillery_cafe", "Mixology + Cafe + compatible Distillery", True, "integrated"),
        ("unsupported_distillery", "Mixology + unsupported Distillery (with or without Cafe)", True, "unsupported"),
    ):
        excluded = set() if cafe else coffee.copy()
        if alcohol != "fallback":
            excluded |= spirits
        if alcohol != "integrated":
            excluded |= set(ORCHARD_MIXOLOGY.get("distillery_recipe_ids", []))
        if alcohol == "unsupported":
            excluded |= mixology - non_alcoholic
        optional_alcohol = set(ORCHARD_MIXOLOGY.get("optional_alcohol_variants", [])) if alcohol == "unsupported" else set()
        counts = {"items": len(item_ids - optional_alcohol - outputs_for(excluded) - (optional_juices if alcohol != "integrated" else set())), "recipes": len(recipe_ids - excluded)}
        if counts != ORCHARD_MIXOLOGY["runtime_modes"][key]:
            raise ValueError(f"Stale Orchard catalog counts for {key}: source={counts}")
        rows.append([label, str(counts["items"]), str(counts["recipes"])])
    return table(["Installed content", "Mixology items", "Authored Mixology recipes"], rows)


def orchard_core_recipes_table() -> str:
    """Read Core's declared ingredient uses; do not synthesize addon recipes."""
    rows = []
    for recipe in RECIPES:
        if recipe.get("_source") != "Core":
            continue
        ingredients = dict.fromkeys(
            option["custom_item"]
            for slot in recipe.get("ingredients", []) for option in slot.get("options", [])
            if ITEM_BY_ID.get(option.get("custom_item"), {}).get("_source") == "Orchard"
        )
        if not ingredients:
            continue
        links = ", ".join(
            f"[{ITEM_BY_ID[item_id].get('name', title_from_id(item_id))}]"
            f"({item_markdown_href(item_id, '../../reference/')})"
            for item_id in ingredients
        )
        rows.append([recipe_link(recipe, "../../recipes/"), recipe["_station"], links])
    return table(["Core recipe", "Station", "Mixology ingredient choices"], rows)


def orchard_menu_table(recipe_ids: list[str], include_station: bool = False) -> str:
    recipes = {recipe["id"]: recipe for recipe in ALL_RECIPES if recipe.get("_source") == "Orchard"}
    rows = []
    for recipe_id in recipe_ids:
        recipe = recipes[recipe_id]
        output_id = str(recipe["output"])
        output = ITEM_BY_ID.get(output_id, {})
        name = output.get("name", title_from_id(output_id))
        family = ORCHARD_MIXOLOGY.get("dynamic_recipe_families", {}).get(recipe_id, [])
        if family:
            name = " / ".join(ITEM_BY_ID.get(item_id, {}).get("name", title_from_id(item_id)) for item_id in family)
        if recipe_id == "ORCHARD_SHAKEN_PINA_COLADA":
            name = "Shaken " + name
        ingredients = []
        for slot in recipe["ingredients"]:
            labels = []
            for option in slot["options"]:
                item_id = option.get("custom_item", option.get("item", ""))
                labels.append(option_label(option) if option.get("qualifier") else ITEM_BY_ID.get(item_id, {}).get("name", title_from_id(item_id)))
            optional = "Optional: " if slot.get("type") == "OPTIONAL" else ""
            ingredients.append(optional + f"{slot_quantity_text(slot)}× " + " or ".join(labels))
        row = [
            f"**{name}**<br>{recipe_link(recipe, '../../recipes/')}<br>Yield: {recipe.get('_output_amount', 1)}",
            "<br>".join(ingredients),
            f"{recipe.get('processing_time', 0)} ticks",
            orchard_recipe_availability(recipe_id),
        ]
        if include_station:
            row.insert(1, recipe["_station"])
        rows.append(row)
    headers = ["Recipe", "Exact ingredients", "Time", "Availability"]
    if include_station:
        headers.insert(1, "Station")
    return table(headers, rows)


def load_beverage_affinity_catalog() -> dict:
    catalog = read_json(DISTILLERY_RESOURCES / "beverage-affinities.json")
    if catalog.get("version") not in (1, 2, 3, 4) or not isinstance(catalog.get("families"), list) or not isinstance(catalog.get("styles"), list):
        raise ValueError("Unsupported Distillery beverage affinity catalog")
    return catalog


def distillery_strength_reference(catalog: dict, settings: dict | None = None) -> str:
    """Read the same default curve and named targets that production loads."""
    if settings is None:
        settings = yaml.safe_load((DISTILLERY_RESOURCES / "config.yml").read_text())["distillation"]
    cap = max(0.0, min(96.0, float(settings["max_abv"])))
    extraction = max(0.0, float(settings["base_extraction"]))
    penalty = max(0.0, float(settings["run_penalty"]))
    minimum = max(0.0, float(settings["min_gain"]))
    strength = 5.0
    examples = []
    for run in range(21):
        gain = max(minimum, (cap - strength) * extraction / (1 + penalty * run))
        strength = max(strength, min(cap, strength + gain))
        if run + 1 in (2, 8, 21):
            examples.append(f"{strength:.1f}% after {run + 1} passes")
    targets = []
    for recipe in catalog["recipes"]:
        if recipe["id"] in ("TAXI", "SPIRYTUS"):
            targets.append(f"{recipe['name']} requires at least {cellar_number(recipe['minimum_abv'])}% and prefers {recipe['preferred_runs']} passes")
    return (f"With the bundled defaults, each distillation extracts **{cellar_number(extraction * 100)}% of the remaining headroom toward {cellar_number(cap)}% ABV**. "
            + "Starting from a 5% wash, this is " + ", ".join(examples) + ". "
            + "; ".join(targets) + ". These names depend on actual strength and suitable ingredients. "
            + "Customized extraction, caps and pass preferences remain effective; previews use the same production calculation. Existing bottles keep their strength; the revised curve applies to subsequent passes.")


def distillery_fermentation_reference() -> str:
    ingredients = yaml.safe_load((DISTILLERY_RESOURCES / "ingredients.yml").read_text())
    rows = []
    for ingredient in ("WHEAT", "WHEAT_SEEDS", "TORCHFLOWER_SEEDS", "BEETROOT_SEEDS", "MELON_SEEDS", "PUMPKIN_SEEDS", "CORN", "PITCHER_POD"):
        sugar = float(ingredients[ingredient]["sugar"])
        rows.append([title_from_id(ingredient), cellar_number(sugar), f"{sugar * .55:.2f}%"])
    return table(["Ingredient", "Fermentable sugar", "Average fermented ABV"], rows)


def cellar_number(value: float) -> str:
    return f"{float(value):g}"


def cellar_real_time(minutes: float) -> str:
    hours = int(minutes // 60)
    remainder = minutes - hours * 60
    return (f"{hours}h" if hours else "") + (f"{cellar_number(remainder)}m" if remainder or not hours else "")


def cellar_share(value: float) -> str:
    for fraction, label in ((1 / 6, "1/6"), (1 / 3, "1/3"), (1 / 2, "1/2"), (2 / 3, "2/3")):
        if abs(value - fraction) < 1e-9:
            return label
    return cellar_number(value * 100) + "%"


def distillery_recipe_reference(catalog: dict) -> str:
    """Named preparation routes come from the production catalog, in precedence order."""
    rows = []
    for recipe in catalog.get("recipes", []):
        conditions = []
        for fraction in recipe.get("fractions", []):
            subject = fraction.get("preparation", "").title()
            ingredients = ", ".join(title_from_id(item) for item in fraction.get("ingredients", []))
            subject = " ".join(part for part in (subject, ingredients or "ingredients") if part)
            minimum, maximum = fraction.get("minimum", 0), fraction.get("maximum", 1)
            denominator = "the whole batch" if fraction["denominator"] == "BATCH" else fraction["denominator"].lower() + " inputs"
            if minimum == maximum:
                comparison = cellar_share(minimum)
            else:
                low = ">" if fraction.get("minimum_exclusive") else "≥"
                high = "<" if fraction.get("maximum_exclusive") else "≤"
                comparison = f"{low}{cellar_share(minimum)} and {high}{cellar_share(maximum)}"
            conditions.append(f"{subject}: {comparison} of {denominator}")
        if recipe.get("minimum_abv"):
            conditions.append(f"At least {cellar_number(recipe['minimum_abv'])}% ABV")
        if recipe.get("cool_days"):
            conditions.append(f"{cellar_number(recipe['cool_days'])} cool days recorded in the rack")
        if recipe.get("preferred_runs"):
            conditions.append(f"Preferred distillations: {recipe['preferred_runs']}")
        rows.append([recipe["name"], recipe["stage"].title(), ", ".join(value.title() for value in recipe["families"]),
                     "<br>".join(conditions) or "Otherwise, after earlier matching routes"])
    return table(["Named drink", "Stage", "Eligible base", "Additional requirements"], rows)


def distillery_family_reference(catalog: dict) -> str:
    rows = []
    details = []
    for family in catalog["families"]:
        rows.append([family["id"].title(), family["fermented_name"], family["distilled_name"],
                     "Yes" if family["requires_boiling"] else "No", str(family["preferred_runs"])])
        title = family["fermented_name"] + " / " + family["distilled_name"]
        if family["id"] == "GENERIC":
            details.append(f"### {title}\n\nUnrelated mixtures remain in this family. They do not earn named-family mastery.")
            continue
        ingredients = ", ".join(ingredient.replace("_", " ").title() for ingredient in family["ingredients"])
        paragraph = f"Suitable ingredients: {ingredients}."
        for ingredient, share in family.get("minimum_ingredient_share", {}).items():
            paragraph += f" At least {cellar_number(share * 100)}% of the whole batch must be {ingredient.replace('_', ' ').title()}."
        details.append(f"### {title}\n\n{paragraph}")
    return table(["Base", "Fermented drink", "Spirit", "Boil for full process credit", "Preferred distillations"], rows) + "\n\n" + "\n\n".join(details)


def distillery_maturation_reference(catalog: dict) -> str:
    families = {family["id"]: family for family in catalog["families"]}
    rows = []
    for style in catalog["styles"]:
        names = []
        for family_id in style["families"]:
            family = families[family_id]
            base = family["distilled_name"] if style["stage"] == "DISTILLED" else family["fermented_name"]
            matching_named = next((recipe for recipe in catalog.get("recipes", [])
                                   if recipe.get("style") == style["id"] and family_id in recipe["families"]), None)
            if matching_named:
                base = matching_named["name"]
            if "SPARKLING" in style.get("required_treatments", []):
                base = "Sparkling Wine"
            names.append(style["name"].replace("{base}", base) if style["name"] else base)
        days = style["days"]
        target = f"{cellar_number(days)} {'day' if days == 1 else 'days'} ({cellar_real_time(days * catalog['minutes_per_day'])})"
        climate = style["temperature"].title() + " / " + style["humidity"].title()
        if style["finish_days"] > 0:
            base_days = style.get("base_days", style["days"] - style["finish_days"])
            woods = " or ".join(wood.removesuffix("_FINISH").replace("_", " ").title() for wood in style["treatments"])
            treatment = f"{cellar_number(base_days)} days Oak or Dark Oak, then {cellar_number(style['finish_days'])} days {woods}"
        else:
            treatment = " or ".join(wood.replace("_", " ").title() for wood in style["treatments"])
        rows.append([" / ".join(dict.fromkeys(names)), target, climate, treatment])
    return table(["Drink or style", "Target in the rack", "Preferred climate", "Treatment"], rows)


def distillery_pages():
    catalog = load_beverage_affinity_catalog()
    minutes = cellar_number(catalog["minutes_per_day"])
    perfect_chance = cellar_number(catalog["perfect_chance"] * 100)
    add("addons/distillery/index.md", page("Distillery Addon", f"""
{image("../../images/distillery-banner.svg", "Distillery adds mashing, fermentation, distillation and cellar craftsmanship.")}

Turn familiar ingredients into recognizable drinks, then develop their style through processing, climate and wood. Potatoes lead to Potato Vodka, cactus to Tequila, sugar cane to Rum, rice to Sake, and apples to Cider or Apple Brandy.

Distillery **{RELEASE_VERSIONS['distillery']}** requires Heirloom Core; install the matching **{RELEASE_VERSIONS['core']}** Core update. See [Installation](../../getting-started/installation.md) for Paper, Java and licensing requirements. It works without Pasture; if both are installed, drinks and cheese share the same Aging Rack. The addons also use Core's shared scoring and recommendation machinery while keeping their own ingredient and treatment rules. Existing cheese outcomes and culture yields are unchanged.

Open **Distillery Drinks** in `/hl`, or use `/hld menu`, to browse every named drink and style. Each opens an [editable recipe preview](recipe-preview.md): change the mash ingredients, processing or cellar conditions and see what the batch would become. **Distillery Guide** and `/hld guide` hold ingredients, station instructions, quality, personal history and Drunkenness & Sobering. Both use Core's normal silent navigation.

Start with [Getting Started](getting-started.md), then browse [Drink Families](families.md), [Cellar Aging](cellar-aging.md) and [Craftsmanship](craftsmanship.md).
"""))
    add("addons/distillery/getting-started.md", page("Distillery Getting Started", """
Install matching Heirloom Core and HeirloomDistillery jars, then restart. Open Distillery Drinks in `/hl` or use `/hld menu` to choose a drink. Its preview starts with a working example that you can edit freely. Administrators can inspect the available items with `/hld list` and use `/hld give <item> [amount]` for test ingredients.

For a first batch, collect six suitable fruits, such as grapes. Build a Stomping Tub with a composter on Granite or Polished Granite, add the ingredients and jump to mash them. Ferment the prepared must in a cauldron on a Blast Furnace (no fuel required), then collect the finished drink with a Glass Bottle.

The bottle is already usable. To develop it further, put it in a normal barrel directly on Scaffolding. The bottle's guidance explains its next useful step. Grain and rice wort can ferment raw, or you can first boil it in a cauldron over a Campfire for full process-quality credit. Boiling does not change ABV.

See [Brewing Flow](brewing-flow.md) for the stations and [Drink Families](families.md) for suitable bases. The default mash uses six ingredients; server owners can change that batch size.
"""))
    add("addons/distillery/recipe-preview.md", page("Interactive Recipe Preview", """
Choose a drink in **Distillery Drinks** or `/hld menu`. Its recipe opens with an example that produces that result. Six ingredient slots appear in two columns of three by default; repeated and mixed ingredients are supported. Click a slot to choose from the categorized ingredient picker, or right-click the main slot to cycle. In the picker, left-click selects the whole ingredient. Right-click selects skinned grapes or roasted grain where applicable. These are preview choices: your inventory is not consumed or changed.

The process icons also act as controls. Boiling starts in **AUTO**: grain and rice include the step, while other inputs omit it. Click Boil to skip it, or click Ferment when boiling is omitted to add it. An explicit **ON** or **OFF** choice is remembered when you change ingredients. You can ferment raw grain or rice; boiling first earns full process-quality credit without changing ABV. Forcing boiling on an unsupported fruit mash shows an unavailable method because there is no fruit-wort boiling recipe.

With boiling shown, the process row is Mash → Boil → Ferment → Distillation → Aging, followed by Wood, Climate and Secondary Fermentation. Without boiling, those process controls move forward by one position after Mash. Reset stays in zero-based slot **34** for every drink, including Rosé, regardless of boiling or secondary fermentation. Hiding age-dependent controls does not shift the remaining positions again. Distillation cycles through **0, 1, 2, 3, 5, 8, 13, 21**; a custom administrator preset can retain its exact count until you change that control. The preview assumes **Normal ingredient quality**. Reset Recipe restores the example you opened, including **AUTO** boiling, and Back returns to your catalog page. Catalog and picker pages use the [shared navigation arrows](../../getting-started/recipe-browser.md#how-to-read-it).

At zero aging, wood and climate controls are hidden; their selections are retained and restored when aging is enabled. Secondary fermentation is shown only for grape wine with no distillation. Its selection is also retained while hidden. Hidden settings do not affect the result. Sugar and Brown Mushroom appear separately from the mash when secondary fermentation is active.

The result appears on the right and updates with the drink's name, ordinary quality, ABV range and chemistry. Guidance consistently shows **Next improvement:** followed by the next useful step, or **Ready as shown.** Ready describes the current result, not an unfinished later style. Its cl range is the equivalent dose of a **40% spirit**, calculated from that ABV range and the serving volume. Changing controls does not roll a batch, create a real drink or add to your brewing history. Actual strength and the Perfect outcome use the single value saved when a real mash is created.

Default aging choices are **0, 1, 3, 14, 60 and 360 cellar days**. A single readable line combines cellar and real time, for example `⏳Aging: 14 days · (4h40m)` or `360 days · (120h)` at the default clock; administrator-configured recipe durations are preserved. Ordered treatments explain when to change planks: the default finished whiskies use 45 days of Oak or Dark Oak followed by 15 days of Cherry or Acacia.
"""))
    add("addons/distillery/brewing-flow.md", page("Distillery Brewing Flow", f"""
{image("../../../images/distillery/D_mashing_fruit.gif", "Start by mashing a suitable ingredient base.")}

1. **Prepare and mash:** add the required number of ingredients to a composter on Granite or Polished Granite, then jump. Before stomping, use **Shears** on the tub to skin its current grapes, or **Flint and Steel** to roast its current grains. Added ingredients begin whole, so prepare again after adding more. These tools do not light a fire or create separate inventory ingredients. The default is six inputs; each original item, its quality and its preparation are retained as ancestry. Canceling refunds the untouched original ingredients once.
2. **Prepare and ferment:** suitable bases, including raw grain and rice wort, can ferment directly. For full grain or rice process-quality credit, first boil the wort in a cauldron over a Campfire; boiling does not change ABV. The Fermentation Station is a cauldron on a Blast Furnace (no fuel required). Bottle the finished beverage.
3. **Distil when making spirits:** build two adjacent columns: Campfire → Cut Copper → Cut Copper Stairs, and Brewing Stand → Lightning Rod → Cut Copper Stairs. Keep the Campfire lit. All oxidation and wax variants of the copper components work. Follow the preferred pass count on the [family reference](families.md). One pass remains usable; further strength gains diminish.
4. **Mature:** place the beverage in a barrel directly on Scaffolding. Choose a [cellar style](cellar-aging.md), its climate and its wood or neutral-resting treatment. Remove the bottle to pause, and return it to resume.

{distillery_strength_reference(catalog)}

Ferment grape wine again with **one Sugar and one Brown Mushroom** to make Sparkling Wine. Its own maturation and quality assessment begin after secondary fermentation; earlier still-wine aging remains historical evidence. The fresh Sparkling Wine is already drinkable. This treatment is recorded once; repeating it cannot reset progress, award more points or reroll quality.

Re-distilling keeps the ingredient ancestry and the original batch quality roll, but starts fresh spirit maturation. Earlier aging remains historical evidence. Ordinary fermentation strength and diminishing repeated-distillation gains remain variable; the cellar itself never changes ABV, serving volume or total alcohol.

Genuine beverage profiles determine eligibility. Renamed items, recipe previews, Mixology Gin, liqueurs and finished cocktails are not Distillery rack inputs. Mixology still owns those preparations and recognizes compatible aged spirits by their validated families.
"""))
    add("addons/distillery/families.md", page("Drink Families", f"""
The table and ingredient lists below are generated from Distillery's bundled `beverage-affinities.json`. They describe the defaults; the in-game guide shows the server's current catalog and available ingredients.

A named base normally needs **at least two-thirds** suitable ingredients: four of a default six-item mash. Specific bases such as apples, grapes, rice and corn take precedence within their broader fruit or grain family. Pure suitable batches earn full composition credit. The rules use proportions when a server changes the batch size.

The boiling column describes full process-quality credit. Raw grain and rice wort can still ferment, and boiling does not change their ABV.

{distillery_family_reference(catalog)}

## Prepared wines, beers and high-proof spirits

Skin all grape inputs for White Wine, some for Rosé, or leave them whole for Wine. Skinning reduces the grapes' tannins and shifts their blended tint. Roasted shares are measured among grain inputs: at least half selects Irish Stout, one-third Porter, and one-sixth Irish Red Ale. Pale batches with at least two-thirds Wheat among their grains become Wheat Beer; the remaining pale batches start as Ale and can become Lager after three recorded cool rack days. Rice/Sake and Corn/Corn Beer keep their more specific family precedence. Ordinary beer craftsmanship takes one day; Lager takes three cool days.

Porter and Irish Stout intentionally reuse the same [dark-beer player head](https://textures.minecraft.net/texture/b8ce8a802031ad53dee7a05b94f2f118d383495228070437aa7dced6cf9aadfa). Their ingredient proportions and drink identities remain distinct.

The following ordered routes are generated from the same catalog as production. Earlier qualifying routes take precedence; administrator-edited thresholds and names appear here when the source is regenerated.

{distillery_recipe_reference(catalog)}

Ingredients supplied by another addon are usable only while their definitions are available. Family identity is separate from [maturation style](cellar-aging.md): a finished or reserve Whiskey remains in the same family for compatible Mixology recipes.
"""))
    add("addons/distillery/cellar-aging.md", page("Cellar Aging", f"""
Build the Aging Rack with a **normal barrel directly on Scaffolding**. Its vanilla inventory holds drinks and, with Pasture installed, cheese. Distillery needs no separate rack or timer and works without Pasture.

One aging day is **{minutes} real minutes** by default. The preview offers 0, 1, 3, 14, 60 and 360 days; at the standard twenty-minute day, 360 days means **five real days**. Aging happens only while a bottle is in a valid rack; inventory and chest storage pause it. Removing and returning a bottle preserves its earned progress. Eligible clean offline time is retained, while missing addon registrations and invalid rack intervals are excluded. Hoppers cannot transfer items into or out of the rack.

Fresh fermented drinks and spirits can be used immediately. Targets describe the work needed for a developed style and full craftsmanship. Quality safely plateaus: extra time never spoils a drink, and aging does not change its ABV, serving volume or total alcohol.

## Choose one wood type

Put Oak, Dark Oak, Cherry or Acacia planks in the same barrel. One unique supported species treats every eligible bottle; the planks are reusable and extra planks do not increase their effect. With no supported planks, bottles rest neutrally. Unsupported wood does nothing. Multiple supported species suspend wood-specific progress while ordinary maturation continues; the bottle asks you to use one wood type.

Swapping wood preserves earned exposure. Cheese ignores the plank treatment and keeps Pasture's finish-on-removal behavior. No wood is best for every drink.

## Find the right cellar climate

The rack reads the biome temperature and humidity at the barrel. An ordinary **Forest, Dark Forest or Taiga** is cool and humid. Birch Forest and Snowy Taiga do not meet the humid threshold. A roof or underground room is optional for Distillery drinks; placing water or ice nearby does not change their cellar climate.

Cool means a biome temperature below 0.8; humid means at least 80% biome humidity. These are Minecraft biome values, not degrees Celsius or a measurement of nearby water. Wine keeps aging in every climate, while its preferred cool/humid exposure helps craftsmanship.

You can mash, ferment and distil in any biome. Ingredients and processing determine the drink family: moving Wine to a warm biome does not turn it into Rum. Different drinks prefer different cellar climates, shown below. Some specific styles require recorded climate exposure, such as Lager's three cool aging days; ordinary aging still continues outside that preferred climate.

## Read the rack report

Open a real Aging Rack to see a formatted chat report with its named climate, the current drink wood treatment, and grouped contents. Each group shows progress, the style it is developing toward, and the next useful step. Hover the report entries for more detail; a full rack shows a short summary with additional groups in hover text.

The report uses the server's current aging rules and distinguishes time earned from any climate or wood work still needed. A young wine is not marked ready just because one cellar day passed. Cheese guidance describes its current aging progress without guaranteeing the final cheese before removal. A rack without ageable contents explains how to start.

For a hands-on demonstration, run `/hl tutorial aging` or `/hld tutorial aging`. The practice barrel supplies temporary bottles and wood, demonstrates mixing and removing wood, accelerates maturation, and lets you collect the result. Your real inventory is preserved.

## Default maturation routes

These routes are generated from `beverage-affinities.json`, including the neutral resting routes for Honey Spirit and Rice Spirit.

{distillery_maturation_reference(catalog)}

For specialty finishes, complete the Oak or Dark Oak base phase **before** the Cherry or Acacia phase. Earlier finishing-wood exposure cannot substitute for the later finish. Wood-named styles require actual exposure to that wood; neutral resting cannot replace it.

The listed climate is a preference for full craftsmanship. Full climate credit requires preferred exposure equal to **75% of the target duration**. The bottle gives a practical next step without requiring players to read a score dashboard. See [Craftsmanship](craftsmanship.md) for quality and [Configuration](configuration.md) for editable defaults.
"""))
    add("addons/distillery/craftsmanship.md", page("Beverage Craftsmanship", f"""
Quality uses Heirloom's existing **Poor → Normal → Good → Great → Excellent → Perfect** dice and names. Your ingredients, processing and cellar work shape it; there is no separate star rating.

Start with a suitable base, boil grain or rice wort for full process-quality credit, ferment, and use the preferred distillation count for spirits. Raw grain and rice fermentation is also allowed; boiling improves process quality without changing ABV. Then complete the maturation, climate and wood or neutral-resting requirements of a chosen style. Ingredient quality is averaged by quantity; ungraded vanilla ingredients count as Normal. A mixture of unrelated ingredients cannot earn named-family mastery.

Ordinary results reach Excellent. **Perfect has a {perfect_chance}% default chance for a fully qualified batch** with at least Normal average ingredient quality. The random value is generated once when the mash is created and remains shared by every serving and later processing stage. Opening, collection, splitting, wood changes, further distillation and reloads never reroll it. A mastered batch that misses Perfect stays Excellent; its guidance does not ask for another roll.

Earned contributions do not stack through repeated removal and do not decline merely because more time passes. A bottle explains its developing style, achieved characteristics and next useful improvement. Distillery and Pasture use the same Core ranking and recommendation implementation with separate domain catalogs.

## Existing stock

Valid old bottles retain their identity, ABV, serving amount and quality. Their creation dates are provenance, not earned cellar time. They can develop styles from future rack exposure, but missing ingredient ancestry is not invented and they receive no new Perfect lottery.

The longer aging defaults preserve validated styles and quality already earned by existing stock. Stored exposure remains its actual elapsed time; it is not multiplied to match new targets. Further development follows the current catalog. Unchanged previous timing defaults upgrade automatically while administrator-edited entries are retained.

Keep `beverage-affinities-v1.snapshot.json` with your server backups. Migration saves the exact old installed rules once so stored bottles can retain achievements earned under administrator-edited targets. Missing historical evidence is not reconstructed from current defaults.

Old Distillery brewing powers have been retired. Identifiable generated effects and power lore are removed lazily when genuine bottles are exposed or consumed; unrelated metadata, notes, names and effects of unknown ownership are preserved. The alcohol intake, drunkenness, recovery and Mixology serving calculations are unchanged. See [Inebriation](inebriation.md) for the existing gameplay scale.
"""))
    add("addons/distillery/mashables-traits.md", page("Ingredients And Flavour", f"""
Mashable ingredients still carry Sugar, Acid and Tannins, ingredient colors, grape varieties and readable flavour notes. Sugar affects fermentation potential. Acid and tannins describe character; a universal chemistry-balance formula no longer decides quality or overrides the drink's family.

Beer strength remains ingredient-based. These default grain values yield ordinary beers averaging about 4.1–5%; the actual mash roll varies strength by up to 20% in either direction. Grain and rice can ferment raw; boiling first earns full process-quality credit without changing ABV. Roasting selects beer styles without separately adding alcohol. Mixed batches average their ingredients by quantity. Existing mash keeps its stored chemistry; edits affect newly created mash.

{distillery_fermentation_reference()}

Choose a [drink family](families.md) for its suitable base, then follow [craftsmanship](craftsmanship.md) and [cellar](cellar-aging.md) guidance. `/hld stats <item>` and the Ingredients browser remain useful for inspecting available ingredients.

Open **Distillery Guide** in `/hl` or `/hld guide` for categorized ingredient pages, station instructions, quality, personal Brew History and Drunkenness & Sobering. Mashables shows the actual ingredients directly, with chemistry on hover. Pages share normal pagination, Back/Forward navigation and silent navigation. Right-click a saved brew to see its location when available. **Distillery Drinks** and `/hld menu` open editable recipe previews. The admin-only `/hld lab` uses production calculations and remains separate.

Old trait powers have been retired; mixing special ingredients does not recreate their former potion abilities. This existing page address remains available for older links. Administrators configure ingredient stats in `ingredients.yml` and family/style rules in `beverage-affinities.json`.
"""))


def addons_pages():
    orchard_items = [item for item in ITEMS if item.get("_source") == "Orchard"]
    orchard_recipes = [recipe for recipe in ALL_RECIPES if recipe.get("_source") == "Orchard"]
    precursors = [rid for rid in ORCHARD_MIXOLOGY["recipe_ids"] if rid.endswith("_LIQUEUR") or rid in {
        "ORCHARD_GIN", "ORCHARD_SWEET_VERMOUTH", "ORCHARD_RED_BITTER_APERITIF", "ORCHARD_AROMATIC_BITTERS", "ORCHARD_ABSINTHE"}]
    cocktails = [rid for rid in ORCHARD_MIXOLOGY["recipe_ids"] if rid not in precursors]
    add("addons/orchard/index.md", page("Heirloom Mixology", f"""
{mixology_branding() or "**Cocktails, Juices & Fruit Trees**"}

Grow a fruit grove, blend your harvest into fresh juice, and serve a round of cocktails from a moving, multipart shaker. Heirloom Mixology brings fruit trees, tropical crops, survival discovery and physical drink-making stations to your server. No resource pack is required: the release uses player-head fruit and cocktail visuals, with vanilla bottle models for juices.

## Grow → juice → shake

1. **Grow:** discover plantable fruit in the world or open a starter packet. Tend seven fruit trees and the Pineapple crop; harvest ripe fruit by hand or knock it down with an arrow.
2. **Juice:** add three fruit or vegetable items to the [Juicer](../../stations/juicer.md), blend for ten seconds, then pour **two bottles**. Choose one produce type for pure juice, or mix a blend.
3. **Shake:** bring exact ingredients to the [Mixology Table](../../stations/mixology-table.md). An eight-second batch serves **three finished drinks** in a row; reusable liqueurs and infusions make one bottle. Perfect-quality batches have special shaker motions.

Start with a Virgin Mango Daiquiri or the shaken Piña Colada, then explore the [Mixology recipe catalog](../../recipes/station-mixology-table.md). The [Juicer guide](../../stations/juicer.md) covers blending, nutrition and both pours; the [Mixology Table guide](../../stations/mixology-table.md) covers construction, bottles, ice and optional integrations.

!!! info "Heirloom Mixology {RELEASE_VERSIONS['mixology']}"
    The included player-head visuals work without a resource pack. Dates and the deferred dishes are excluded from this release, and provider packages are not included.

## Requirements and installation

Requires **Heirloom Core {ORCHARD_CATALOG['requires_heirloom']} or newer**. Use **Core {RELEASE_VERSIONS['core']}** with this release for the current Juicer, Mixology and licensing updates. Install the addon JAR beside Core in `plugins/` with the server stopped, then start it and check `/hlo info`. Follow [Core installation](../../getting-started/installation.md) for Paper, Java and marketplace licensing requirements. Distillery and Cafe are optional; WorldEdit is not a runtime dependency.

The public name is Heirloom Mixology. The plugin identity, `/hlo` commands, `ORCHARD_*` item IDs, `plugins/HeirloomOrchard/` folder and this `/addons/orchard/` guide URL remain unchanged, so existing saves and administrator edits keep their paths.

The default set contains {ORCHARD_CATALOG['installed_content']['base_trees']} fruit trees and one Pineapple crop. Its editable sources contain {len(orchard_items)} item definitions and {len(orchard_recipes)} recipe definitions, including conditional integrations. Use the active mode table below when counting what a server actually enables.

Finished cocktails and virgin drinks yield **three drinks per eight-second batch**, displayed side by side in a centered row. Left-click collects the row. Liqueurs, Gin, Vermouth, Red Bitter Aperitif, Aromatic Bitters and Absinthe remain one bottle per batch. The recipe browser previews the actual yield. Each serving preserves its original quality, nutrition and alcohol metadata, including after reload. Up to three input bottles are reused; surplus emptied bottles, cans and buckets return once. No additional empty bottles are required.

## Active Content

{orchard_mode_table()}

These counts include the active fruit foods and exclude all deferred owner-gated content. Every row includes Heirloom Core; optional addons change only the Mixology contribution. Compatible Distillery counts include all five registered grape juices; each missing grape lowers the item count by one. Unsupported Distillery counts exclude optional grapes, so add one item for each grape still registered. The shaken Piña Colada uses the existing `PINA_COLADA` item, so it adds a recipe without a duplicate item.

Jam, Ice Cream and Taco remain Core recipes and do not add to these totals. Their ingredient choices are declared directly in Core's recipe defaults; Mixology ingredients become available while their item definitions are registered.

## Starter packets and survival discovery

**Grove Starter Packet** contains Lemon, Orange and Avocado. **Tropical Starter Packet** contains Mango, Bananas, Coconut and Pineapple. Right-click either packet for 3–5 plantable fruits, selected by weight (repeats are possible). Their heads intentionally reuse Core's Temperate and Tropical packet artwork. The existing Tropical Seed Packet also retains its active fruit additions.

Default discovery routes:

| Source | Mixology rewards | Chance per eligible break |
| --- | --- | --- |
| Natural Oak/Birch leaves in Forest, Birch Forest or Flower Forest | Lemon or Orange | 1% |
| Natural Jungle leaves in Jungle, Sparse Jungle or Bamboo Jungle | Mango, Avocado, Bananas or Coconut | 1% |
| Grass and ferns in those jungle biomes | Pineapple | 0.5% |

Starter packets also join village house/farm and temple chest loot pools. These are weighted additions to Core's existing chest chances, not guaranteed rewards. Existing beach Coconut generation is unchanged. Placed persistent leaves do not provide Mixology discovery drops, and normal protection checks apply.

Edit `plugins/HeirloomOrchard/seed-acquisition-orchard.json`: `enabled_features.block_drops` and `enabled_features.chest_loot` independently disable Mixology's routes. `packet_definitions` controls packet contents and quantities; `block_drops` controls blocks, biomes, probabilities and reward weights; `chest_loot` adds weighted `items` to existing Core groups. Core's global acquisition switches still apply. Reload Mixology after editing. All contributions are owned by Mixology and removed when it is disabled; Core-only installations receive none. New defaults are merged once without replacing existing rules; subsequent administrator removals remain removed.

Ripe tree avocados use a whole-fruit head. Inventory avocados keep the cut-fruit icon, and the growing tree texture remains unchanged. Updates replace only the previous default ripe head, preserving customized tree textures.

Juicer action-bar feedback shows inserted contents, progress toward three ingredients, and remaining bottles after blending. Mixology feedback shows the target drink and missing ingredients using Heirloom's normal muted/highlight palette. These messages appear on interaction and preserve the existing processing bar and completion sounds.

## Plant Fruit Directly

Plant the harvested fruit directly: Lemon, Orange, Mango, and Avocado grow with `tree1.schem`; Coconut and Bananas grow with `palm1.schem`. Plant the Apple tree with a vanilla Apple. Palms plant on Sand; the other fruit trees use vanilla sapling soil rules. Pineapple is a separate five-stage crop: a short fern with an upright fruit. Leave the plant block clear when planting. Its base growth time and source are listed in the [crop reference](../../reference/crops.md#crop-pineapple).

| Plant | Mapping | Harvest |
| --- | --- | --- |
| Lemon, Orange, Mango, Avocado | `tree1.schem` | The same custom fruit used for planting |
| Coconut, Bananas | `palm1.schem` | The same custom fruit used for planting |
| Apple | `tree1.schem` | Vanilla Apple |

Ripe coconuts can generate naturally in Beach biomes using the authored 2% attempt chance. Tree fruit nodes use separate growing and ripe player-head textures and grow progressively larger as they mature. Bonemeal immediately advances their visible size. Regular fruit such as apples and mangoes uses 60% of the coconut/banana scale. Shoot any ripe tree fruit with an arrow, aiming at the hanging fruit itself; forgiving hit bounds extend below the attachment and around its sides. Each hit knocks down one fruit harvest with break particles; the item falls naturally, retains its quality, and the node regrows. Protection checks still apply.

{image_if("../../images/mixology/coconut-harvest.gif", "Bow harvesting ripe coconuts from a palm.")}

The bundled Sponge v3 schematics were created with WorldEdit, but Heirloom Core parses them directly. WorldEdit is an authoring tool and is not a runtime dependency.

## Soda Water

Soda Water uses shared Core infrastructure, enabled only while an active recipe consumes it. Mixology and the American Food Pack each enable it; bare Core hides the item and guide and disables filling. It retains `ORCHARD_SODA_WATER` for existing bottles; there is one item and one acquisition guide. Clicking its recipe shows a Soul Sand station icon and the filling instructions in-game. Core imports old Orchard edits once into `custom_items-soda-water.json` and `recipes-soda-water.json`. Mixology counts exclude this Core ingredient.

Use an empty Glass Bottle on the bubbling water above Soul Sand to bottle Soda Water. Ordinary water and downward Magma columns do not work. Fern represents mint. Virgin Mojito becomes Mojito with optional Rum; Sparkling Lemonade becomes John Collins with optional Gin. Americano combines Soda Water, Red Bitter Aperitif and Sweet Vermouth. These recipes accept optional ice and reuse the Soda Water bottle.

Mojito, Collins and Americano use actual ingredient strengths and liquid volumes for their final ABV. Both virgin recipes stay available without alcohol integration. Lime, yellow and red cocktail heads are intentionally reused. Soda itself uses a pale aqua drinkable lingering-style bottle with no alcohol or nutrition.

## Fruit foods

- **Canned Coconut Milk:** Coconut plus a Tin Can on the Cutting Board; drinking returns the can.
- **Banana Pancakes:** the banana-driven visual/name variant of the strengthened Pancakes recipe.
- **Banana Split Sundae:** Bananas, Ice Cream, and Chocolate in the Mixing Bowl; eating returns the bowl.
- **Tropical Fruit Salad:** Pineapple, Bananas, Mango and Orange in the Mixing Bowl.

## Savory fruit dishes

Use exactly one of each listed ingredient. Each recipe yields one dish and returns one Bowl after eating. Missing ingredients, duplicate units and unrelated extras are rejected. These recipes are available in every Mixology mode.

{orchard_menu_table(ORCHARD_CATALOG['food_expansion']['item_ids'], include_station=True)}

## Core recipe compatibility

Core's recipe defaults accept suitable Mixology fruit in Jam and Ice Cream, plus optional Guacamole for Taco. Fruit flavours retain the existing Core output identities and artwork.

{orchard_core_recipes_table()}

Choices whose item definitions are absent stay unavailable; other ingredients and recipes continue to work without Mixology. The addon does not copy, replace or take ownership of these recipes. Fresh Core installations receive the updated defaults. On existing installations, merge the `JAM`, `ICE_CREAM` and `TACO` ingredient options and flavour rules from the updated bundled `recipes.json` into your editable Core recipe file, preserving your customizations.

## Prepared alcohol-free drinks

**Fresh Coconut Drink** is an alcohol-free drink made from Coconut, Sugar and a Water Bottle in the Mixing Bowl. Crafting returns the empty Glass Bottle. Its existing recipe, nutrition and drink animation are unchanged. The original **Piña Colada** also remains available from Pineapple, Canned Coconut Milk and Sugar in the Mixing Bowl; the Mixology Table has its separate shaken recipe.

## Juicer

{JUICER_GUIDE.replace("## ", "### ")}

## Mixology Table

Build an iron block with any wooden pressure plate directly on top, then interact with the plate. Heirloom Mixology must be active for the station and its recipe-browser entry to appear. Add the exact ingredients, start the shaker, and collect the drink after 160 ticks (eight seconds). The three player-head shaker parts (body, lid, and cap knob) close, shake with sound and ingredient-colored block-break particles, and settle while the progress highlight moves across the filled bar on a 16-tick cycle.

Aim at an empty table and use `/hl debug shaker all` to compare five motions: classic tilt, diagonal, short rapid, rolling, and figure-eight. Use `/hl debug shaker 1` through `5` to replay one, or `/hl debug shaker stop` to cancel. Requires `heirloom.debug`; previews consume no ingredients. Aim at an empty table and use `/hl debug shaker perfect all` to compare Toss and catch and Grand finale. Use `/hl debug shaker perfect 2` or `/hl debug shaker perfect 5` to replay one; `/hl debug shaker stop` cancels either family. Normal batches use short rapid shake 80% of the time and each other normal motion 5%. A fixed-output batch whose expected food quality is Perfect uses one of these two special motions with equal probability, with a small sparkle trail and finishing chime. These animations do not change drink quality, ABV or serving volume.

Finished-drink recipes produce three drinks; reusable precursor recipes produce one bottle. Mixology reuses up to three bottles from bottled inputs for finished drinks, or one for reusable precursors. No extra Glass Bottle is required when a bottled ingredient is listed. Other emptied bottles, cans, and cream buckets are returned once. The shaken Piña Colada reuses its Pineapple Juice bottle; the coconut milk can is returned. Drinking returns one Glass Bottle.

### {len(precursors)} reusable ingredients

{orchard_menu_table(precursors)}

Gin uses Vodka, Sweet Berries and Dandelion. Sweet Vermouth is a berry-and-vodka infusion with Dandelion and Sugar in standalone mode; integrated mode replaces Sweet Berries with one genuine Distillery Wine or Champagne bottle. Red Bitter Aperitif combines Vodka, Orange, Dandelion and Sugar. Aromatic Bitters replaces that Sugar with Cocoa Beans. These preparations support multiple finished drinks. Absinthe infuses Vodka with Fern without adding dilution, and is used by Sazerac, Corpse Reviver No. 2 and Death in the Afternoon.

### {len(cocktails)} cocktail and non-alcoholic recipe families

{orchard_menu_table(cocktails)}

The Virgin Mango Daiquiri, Virgin Banana Daiquiri and shaken Piña Colada are non-alcoholic. The original Mixing Bowl Piña Colada is preserved as a separate recipe.

Dynamic families keep their named results in the item catalog and open the owning recipe with the matching ingredient selected:

- **Virgin Daiquiri:** choose pure Mango Juice or Banana Juice, with Lemon and Sugar. The juice supplies the bottle.
- **Russian:** Vodka and Coffee Liqueur make Black Russian; add Heavy Cream for White Russian or Irish Cream Liqueur for Mudslide. The optional slot accepts at most one of those additions.
- **Negroni / Boulevardier:** choose Gin or Whiskey, with Sweet Vermouth and Red Bitter Aperitif.
- **Old Fashioned / Rum Old Fashioned:** choose Whiskey or Rum, with Sugar and Aromatic Bitters.
- **Virgin Mojito / Mojito:** Fern, Lemon, Sugar and Soda Water; optional Rum selects Mojito.
- **Sparkling Lemonade / John Collins:** Lemon, Sugar and Soda Water; optional Gin selects John Collins.

The catalog includes Negroni, Boulevardier, Old Fashioned, Rum Old Fashioned, Manhattan, White Lady, Bee’s Knees and Garibaldi alongside classic, coffee and non-alcoholic drinks. Including reusable ingredients, there are {len(ORCHARD_MIXOLOGY['recipe_ids'])} authored Mixology recipes. Unlisted extras never form part of these exact contracts.

### Standalone spirits

Without Distillery, Mixology supplies these Boiling Pot recipes. Each takes 400 ticks (20 seconds). The Water Bottle supplies the finished spirit's container; it is not also returned empty when the spirit is made.

{orchard_menu_table(ORCHARD_MIXOLOGY['fallback_spirit_ids'])}

### Distillery and Cafe

When compatible Distillery is enabled, all four fallback spirit definitions and recipes are hidden. Mixology uses genuine distilled vodka, tequila, rum and whiskey instead, including valid older Distillery bottles. Renaming a potion does not make it a spirit. Existing standalone bottles remain in inventories but cannot substitute for genuine integrated ingredients.

Wine integration requires capability 2 and the `DISTILLERY_WINE` recognizer. It accepts genuine non-distilled Wine or Champagne profiles, including valid legacy bottles, and rejects Cider, Beer, Mead, malformed profiles and renamed impostors. Spirit capability 1 remains supported: Sweet Vermouth, Negroni/Boulevardier, Manhattan, Americano, Dry Martini and Corpse Reviver No. 2 are hidden without wine support. Corpse Reviver No. 2 also follows Vermouth availability. Death in the Afternoon additionally requires capability 3 and the `distillery:sparkling_wine` qualifier: genuine Sparkling Wine still has the ordinary `DISTILLERY_WINE` identity, but its recorded secondary fermentation must validate. Ordinary Wine, renamed bottles and metadata-free previews cannot substitute. The integrated counts above assume capability 3; Death is omitted in standalone mode and with older integration.

When enabled Distillery lacks even the spirit Mixology capability, the alcoholic recipes and fallback spirits stay hidden. An administrator diagnostic asks for the matching update; the four non-alcoholic Mixology recipes still produce five named drinks. Cafe independently enables Coffee Liqueur, Espresso Martini, Black Russian, White Russian, Mudslide and B52. Standalone Rum does not require Cafe.

### Alcohol Strength

Standalone Mixology does not add drunkenness behavior. With Distillery, mixed drinks retain diluted ABV and use the same Core quality for their lore, later crafting and quality-dependent alcohol effects. Retired brewing powers are not inherited, and mixed drinks cannot be fed back into distillation or used as genuine spirits.

### Alcohol servings and quality

Recipe previews show an **Average** alcohol estimate, calculated through the selected recipe and its linked source recipes. Both ABV and equivalent-40%-cl reflect ingredient amounts, intermediate volumes and the number of output drinks. Actual crafted drinks show their real values. Clicking a logical spirit such as Vodka opens its Distillery production preview; Back returns to your Mixology recipe. Editing that separate brewing preview does not silently change the parent recipe.

Spirit ingredient cards, including Rum, show the tint and brewing guidance of their linked Distillery production preview. They keep the recipe's required quantities. These are display previews; actual brewing and mixing still require genuine ingredients.

Drinks show their alcohol dose as the equivalent amount of a 40% spirit, for example `🪣Alcohol: 20% ABV · 4 cl`, and one Quality row using Heirloom's existing dice and names. The displayed cl is `actual liquid cl × ABV / 40`: an 8 cl drink at 20% has a 4 cl equivalent dose. Mocktails show 0 cl. Plain juices and Soda Water have no alcohol row. This is alcohol dose, not the physical amount in the glass.

Brewing profiles also show `◾Sugar`, `⚗Acid` and `♣Tannins`. Symbols touch their labels with no space: Alcohol uses cyan, Sugar cream, Acid yellow and Tannins green. Only the symbols receive these colors; labels retain the normal Heirloom theme.

Core quality controls the displayed quality, later crafting and quality-dependent alcohol effects. Station and ice bonuses improve this same quality without changing ABV or serving volume. Legacy beverages seed Core quality from their old alcohol quality only when Core quality is absent; an existing precise Core value is preserved.

One default liquid or squeezed-produce portion is 4 cl. Produced drinks remember their actual volume, so a liqueur made from two 4 cl liquids contains 8 cl. Gin, Aromatic Bitters and Absinthe infuse botanicals without adding juice; dry ingredients and ice add no modeled liquid. No item-definition volume fields are required.

Every mix uses the stored actual liquid volumes: batch alcohol is the sum of each input's volume × ABV / 100, final ABV is batch alcohol / total liquid × 100, and each output receives total liquid / output count. Mixing and splitting preserve the total equivalent alcohol dose; juice lowers ABV without removing alcohol. Fresh Juicer batches produce two 6 cl servings of actual juice; their actual volume contributes to later mixing, but juice itself has no alcohol row. Stored volume remains actual liquid volume and is never reinterpreted as equivalent cl. Missing legacy volume defaults to 4 cl actual volume, preserving the old ABV and quality; malformed explicit volume is rejected.

With Distillery, lore and intake use the same equivalent-alcohol conversion. The default meter holds 40 cl: a 10 cl dose fills one quarter before player sensitivity. The drunkenness readout uses a separate 0–4‰ game scale: `/hld drunk` shows ‰, while item lore continues to show equivalent cl. A 10 cl dose raises the default meter by 1‰ before sensitivity. Bare numbers in `/hld setdrunk` and `/hld adddrunk` retain their cl meaning; add an explicit `‰` suffix to use the game scale, for example `/hld setdrunk Alex 1.2‰`. Only presentation is rounded. Fractional amounts persist, and explicit administrator overrides remain effective. Distillery retains variable fermentation strength and emits standard 4 cl servings of actual liquid; its [brewing-flow reference](../distillery/brewing-flow.md) shows the current default extraction curve. Mixing conserves alcohol; distillation remains a game production mechanic. Standalone Mixology adds no drunkenness behavior.


## Included visuals and excluded content

The release uses player-head fruit and cocktail visuals, the supplied shaker body/lid textures, and vanilla bottle models for juices. Some named cocktails intentionally share approved head reuse; the recipe browser still shows each named result and its ingredients. No resource pack is required.

Dates and the deferred dishes are excluded from the release counts and buyer scope. The deferred dishes are Lemonade, Sticky Date Pudding, Mango Sticky Rice, Avocado Toast and the old standalone Orange Juice definition. Pure Orange Juice from the Juicer and Sparkling Lemonade remain active. The deferred editable owner-asset contracts remain gated. Nexo, ItemsAdder and CraftEngine provider packages are not included. No future visual package is required or included in this release.

## Admin operation

`/hlo info` reports the live item/tree counts and remaining owner-head count. `/hlo reload` validates editable files and swaps registrations transactionally. Editable resources live under `plugins/HeirloomOrchard/`; generated runtime files stay under its `.runtime/` child and never overwrite the editable sources.

The current settings are in `plugins/HeirloomOrchard/config.yml`. Core handles the marketplace license, so a normal Voxel installation does not need an addon license key. `warn-on-draft` controls the notice about deferred owner assets without enabling that excluded content. Edit `trees-orchard.json` for fruit trees, `crops-orchard.json` for Pineapple, `juice-produce-orchard.json` for juice choices, and `custom_items-orchard.json` / `recipes-orchard.json` for item and recipe rules. Acquisition controls are described above. Run `/hlo reload` after valid content edits and inspect `/hlo info`.

Defaults are added without replacing administrator edits. Optional-addon changes refresh the selected content and browser entries. Existing ingredients keep their original identity and metadata through station recovery; cosmetic fruit heads and the shaker are not additional refundable items. Verify the physical shaker, Juicer, GUI and fruit harvests in a real client before reporting visual acceptance. Capture requirements are in the [Mixology media brief](../../media-needed.md#heirloom-mixology-capture-brief).
"""))

    distillery_pages()
    add("addons/distillery/inebriation.md", page("Inebriation", """
Distillery tracks drunkenness separately from ordinary food. Drinks can raise a player's level, affect chat through slurring rules, and trigger blackout or wakeup behavior depending on configuration.

## Dose And The ‰ Scale

Drink lore shows alcohol dose as cl of a 40% spirit: `equivalent cl = actual liquid cl × ABV / 40`. An 8 cl drink at 20% shows 4 cl equivalent. Mocktails show 0 cl; plain juices and Soda Water have no alcohol row. Intake uses the same conversion before player sensitivity. Mixing and splitting preserve the total dose, and stored beverage volume remains actual liquid volume, including for legacy bottles.

Drunkenness readouts use a **0–4‰ gameplay scale**, where 4‰ is the configured meter maximum. This is a game value, not a real blood-alcohol or breath-test estimate. The default meter holds 40 cl equivalent, so a 10 cl dose raises it by 1‰ before sensitivity. `/hld drunk` displays up to two decimals; the action bar has no numeric amount. Fractional amounts survive consumption, recovery and restart. Existing customized intake limits and sensitivity settings remain effective.

## Quality And The Bar

The displayed quality is the alcohol-dose-weighted average of the drinks still contributing to drunkenness, using the Core Poor → Perfect dice and names. Recovery preserves that average until fully sober, then clears it so an old session cannot contaminate the next drink. Quality calculations retain fractions; only the displayed tier is rounded. Perfect has no decorative stars. Valid saved averages survive updates; demonstrably corrupt legacy quality is repaired to Normal without removing drunkenness.

The shared 20-cell bar shows drunkenness and quality without numbers or brackets. Drinking sweeps left-to-right; milk, sobering foods and other reductions sweep all the way left. Each wave travels for 12 ticks, clears its tail over six more ticks, then holds a clean steady bar for 60 ticks. The final four cells grade from warm gold toward muted red, with subdued empty cells. Natural recovery triggers a downward wave when a visible cell changes.

While drunk, a steady reminder becomes eligible **ten seconds after the last bar frame actually displayed**, including the final hold frame. The manager checks once per second, so a reminder can arrive up to a second later. Configure `inebriation.status_reminder_interval_seconds` (default `10`, `0` disables reminders). Reminders never interrupt workstation feedback or an active wave, and blocked attempts do not restart the timer. Logout, reload and disable clear pending presentation work.

Crossing upward into the danger zone at **3.2‰** immediately gives **four seconds of Blindness I**. Further drinks while already above the threshold do not retrigger this warning. It rearms after dropping below the threshold and preserves stronger or longer existing blindness. Administrators can configure the threshold and duration.

## Sobering

These are the default gameplay reductions; the in-game guide shows the effective server settings and applicable player recovery overrides.

| Source | Reduction |
| --- | ---: |
| Milk | 0.2‰ |
| One puking episode | 0.3‰ |
| Bread | 0.16‰ |
| Food with inherited `SOBERING` | 0.6‰ |
| Death | 0.8‰ |
| Natural recovery | 0.08‰ per minute |

Puking drains once when an episode begins, not once per particle or queued extension. Disabled or aborted episodes do not drain. Milk and puking trigger the same downward bar wave as other recovery. Values never take drunkenness below zero.

The Heirloom `SOBERING` food property works through ordinary consumption and placed food while Distillery and inebriation are enabled. Each serving drains once and supports fractional reductions. Use it for server foods such as coffee, meals or custom hangover cures.

Open `/hld guide` or **Distillery Guide** in `/hl`, then choose **Drunkenness & Sobering**. Recovery information is on that same destination. The guide marks disabled sources and reflects configured recovery values. **Distillery Drinks** and `/hld menu` open the drink catalog and editable recipe previews.

## Commands

```text
/hld drunk
/hld setdrunk Alex 1.2‰
/hld adddrunk Alex -0.2‰
/hld wakeup list
```

Administrator commands accept explicit `‰` values. Bare numbers remain equivalent cl for compatibility: `/hld setdrunk Alex 10` sets the same default-meter level as `1‰`. Set/add success messages use ‰. Beverage ABV and cl lore do not change.
"""))
    add("addons/distillery/configuration.md", page("Distillery Configuration", """
Important files:

- `plugins/HeirloomDistillery/config.yml`
- `plugins/HeirloomDistillery/ingredients.yml`
- `plugins/HeirloomDistillery/custom_items-distillery.json`
- `plugins/HeirloomDistillery/crops-distillery.json`
- `plugins/HeirloomDistillery/beverage-affinities.json`
- `plugins/HeirloomDistillery/words.yml`
- `plugins/HeirloomDistillery/lang/en.yml`

`/hld reload` validates and refreshes the supported runtime settings, catalog and registrations transactionally. Pending production batches are cancelled with their established refund behavior before availability changes. A failed refresh restores the previous registrations and rule snapshot. Restart after changing jars.

## Grape Items And Crops

Distillery owns all five grape varieties, their item definitions and their crop definitions. Core does not ship or activate them on its own. Edit the two Distillery JSON files above to customize grapes.

On the first startup with these files absent, Distillery imports existing grape settings from the Core data folder in the original file override order, including later crop-file customizations. Every source file stays intact and item and crop IDs stay the same. Core skips Distillery-owned grape definitions while keeping unrelated custom entries in those files available. Once a Distillery destination file exists, it is authoritative and later reloads do not replace it with the old Core copy. Use matching updated Core and Distillery builds when upgrading.

## Beverage Rules

`beverage-affinities.json` is the authoritative family and maturation catalog. Its `minutes_per_day` default is `20`, and `perfect_chance` is `0.05`. Family entries define suitable ingredient IDs, names, boiling requirements for full process-quality credit, preferred distillation runs and any minimum ingredient shares. `requires_boiling` does not block raw fermentation. Style entries define applicable families/stage, target days, climate and treatment. `base_days` and `finish_days` define ordered wood phases. `required_treatments` and `excluded_treatments` separate Sparkling maturation from still wine. The bundled [family](families.md) and [maturation](cellar-aging.md) references are generated from this same file.

Schema 4 retains per-input `preparation` and ordered named `recipes`. Preparation controls skinned-grape tannins and skinned/roasted colors. Named routes define suitable families/stages, preparation or ingredient fractions, their `BATCH`, `GRAPE` or `GRAIN` denominator, recorded `cool_days`, minimum ABV, preferred runs and their maturation style. This keeps White Wine, Rosé, beers, Taxi Vodka and Spirytus Rektyfikowany configurable. Existing entries and administrator order are preserved; missing defaults are inserted relative to their next known default so broad families do not shadow restored specific ones.

`config.yml` controls the shared still/Brew Lab/preview curve through `distillation.max_abv` (96), `base_extraction` (0.20), `run_penalty` (0) and `min_gain` (0). Only unchanged previous default values upgrade automatically. Explicit administrator settings remain intact. Higher proof names still require their configured strength threshold under the actual curve; changing a pass selector does not assign a fixed ABV.

Absent top-level settings and missing family/style IDs are appended on load. Unchanged previous timing defaults migrate to the new long-aging routes; administrator-edited entries are retained. Edit an existing entry to adjust a default; simply removing a bundled ID makes it eligible for re-addition. Invalid catalogs are rejected before activation. Keep configured Normal and Perfect quality centers in their matching Core tiers.

`ingredients.yml` retains ingredient chemistry, colors and the configured stomping batch size. Grain and rice can ferment raw; boiling first is needed for full process-quality credit but does not change ABV. `distillation` settings in `config.yml` retain the variable strength and diminishing-gain behavior. Core's shared Aging Rack handles permissions, persistence, eligible offline time and movement; no second aging ticker is added.

Only Distillery-produced fermented beverages and spirits can enter its rack rules. Mixology Gin, liqueurs and cocktails remain outside those rules. Pasture cheese uses the same runtime while keeping its own outcomes, culture yields and finish-on-removal behavior.

## Drunkenness And Recovery

Drunkenness displays a 0–4‰ game scale, relative to `inebriation.max_level`. Existing internal point values and integrations keep their units. The new recovery keys accept fractional ‰ directly:

| Key under `inebriation` | Default | Meaning |
| --- | ---: | --- |
| `decay.permille_per_minute` | `0.08` | Natural recovery per minute |
| `sobering.drain_permille_items.MILK_BUCKET` | `0.2` | Milk recovery |
| `sobering.drain_permille_items.BREAD` | `0.16` | Bread recovery |
| `sobering.food_property_drain_permille` | `0.6` | One inherited `SOBERING` serving |
| `death_sobering_permille` | `0.8` | Recovery on death |
| `puke.drain_permille` | `0.3` | Once per actual puking episode |
| `danger.threshold_permille` | `3.2` | Upward-crossing blindness threshold |
| `danger.blindness_seconds` | `4` | Warning duration; `0` disables it |
| `status_reminder_interval_seconds` | `10` | Delay after the last bar frame; `0` disables reminders |

Explicit ‰ settings take precedence over legacy point settings. Both `sobering.drain_items` and older `sobering.custom_drain_items` remain supported; `drain_items` wins for a material present in both. An unchanged legacy Milk default of 2 points upgrades to 0.2‰. Other administrator edits remain intact. Legacy point-based permission overrides for sensitivity and recovery keep their meaning. The player guide reports effective reductions and applicable overrides instead of assuming defaults.

Open `/hld menu` for recipe previews or `/hld guide` for reference after reload. Disabled recovery sources are marked in **Drunkenness & Sobering**.

Development mode can shorten processing loops:

```text
/hld devmode status
/hld devmode on
/hld devmode off
```

## Test After Changes

Run a fruit path and compare raw and boiled grain paths after config edits. Both grain paths should ferment with the same ABV; boiling adds its process-quality credit. In the preview, verify AUTO, remembered ON/OFF choices, reset and the blocked unsupported fruit-boiling method.
"""))
    add("addons/distillery/commands-permissions.md", page("Distillery Commands And Permissions", """
Use `/hld`.

| Command | Purpose | Permission |
| --- | --- | --- |
| `/hld help` | Help | `heirloom.distillery.use` |
| `/hld info` | Addon info | `heirloom.distillery.use` |
| `/hld menu` | Drink catalog and editable recipe previews | `heirloom.distillery.use` |
| `/hld guide` | Ingredients, stations, quality, history and sobering | `heirloom.distillery.use` |
| `/hld tutorial` | Interactive brewing lessons | `heirloom.distillery.use` + `heirloom.tutorial` |
| `/hld list` | List items | `heirloom.distillery.use` |
| `/hld stats <item>` | Ingredient stats | `heirloom.distillery.use` |
| `/hld drunk [player]` | Drunkenness in ‰, on the 0–4‰ game scale | self use, others admin |
| `/hld setdrunk <player> <cl\\|value‰>` | Set drunkenness; bare numbers retain equivalent cl | `heirloom.distillery.admin` |
| `/hld adddrunk <player> <cl\\|value‰>` | Adjust drunkenness; negative values sober | `heirloom.distillery.admin` |
| `/hld give <item> [amount]` | Give items | `heirloom.distillery.admin` |
| `/hld reload` | Reload | `heirloom.distillery.admin` |
| `/hld devmode [on|off|status]` | Fast processing mode | `heirloom.distillery.admin` |
| `/hld lab` | Brew Lab | `heirloom.distillery.admin` |

`heirloom.crop.grape` allows grape planting and defaults to `true`. Distillery owns this permission along with its grape definitions.
"""))
    add("addons/cafe/index.md", page("Cafe Addon", f"""
Cafe **{RELEASE_VERSIONS['cafe']}** adds coffee cherries, coffee roasting, tea processing, oat milk, espresso drinks, cocoa, boba, iced coffee, and the Barista Machine. Install the matching **Heirloom Core {RELEASE_VERSIONS['core']}** update. See [Installation](../../getting-started/installation.md) for Paper, Java and licensing requirements.

Cafe content registers into the normal Heirloom recipe browser, but the final drink assembly uses the Cafe Barista Machine.

Use `/hlc help` for addon commands.
"""))
    add("addons/cafe/getting-started.md", page("Cafe Getting Started", """
1. Install Heirloom core.
2. Install HeirloomCafe.
3. Restart the server.
4. Confirm `/hlc help` works.
5. Build a Barista Machine: iron trapdoor above quartz stairs.

Core station recipes handle roasting and grinding. Barista Machine recipes handle drink assembly.

## First Successful Flow

Roast coffee cherries into beans, pull espresso, then make an americano. That proves the Oven chain, the Barista Machine, and drink assembly before you add milk variants.
"""))
    add("addons/cafe/barista-machine.md", page("Barista Machine", """
The Barista Machine is Cafe's signature station.

Build:

```text
IRON_TRAPDOOR
QUARTZ_STAIRS
```

The iron trapdoor is the shared station anchor. Clicking either part resolves to the same station when Cafe is registered.

## What Belongs Here

Use the Barista Machine for finished drinks: espresso, americano, lattes, cappuccino, mocha, teas, cocoa, boba, and iced coffee. Use core stations for earlier prep such as roasting beans or grinding leaves.
"""))
    add("addons/cafe/coffee-tea.md", page("Coffee And Tea Flow", """
Cafe adds several chains:

- Coffee cherry -> light beans -> medium beans -> dark beans.
- Medium/dark beans -> espresso.
- Espresso + water -> americano.
- Espresso + milk/oat milk -> latte, cappuccino, flat white, mocha.
- Leaves -> leaf litter or dried green tea.
- Dried green tea -> chance at matcha powder.
- Tea leaves -> green tea, black tea, sweet tea, matcha latte.
- Tea + milk + sugar + boba ingredient -> boba tea.

## Core Stations Vs Cafe Station

The Oven and prep stations create the ingredients. The Barista Machine assembles the drinks. If a player tries to make a latte before pulling espresso, the recipe is missing an intermediate, not a permission.

## Ingredient Variants

Milk bucket and oat milk variants can change names, returns, and dietary behavior. Sweet or glow berry variants can change drink identity when the recipe has a matching rule.

See [Default Recipe Index](../../recipes/default-recipes.md) for exact recipes and links.
"""))
    add("addons/cafe/configuration.md", page("Cafe Configuration", """
Cafe writes editable resources to `plugins/HeirloomCafe/`:

- `custom_items-cafe.json`
- `crops-cafe.json`
- `recipes-cafe.json`
- `config.yml`
- `lang/en.yml`

Cafe unregisters and re-registers its addon-owned items, crops, and recipes on reload callbacks so the recipe browser can refresh.

## Test After Changes

After recipe edits, run `/hl reload`, search for `cafe`, then test one coffee chain and one tea chain. That catches both core-station prep and Barista Machine assembly.
"""))
    add("addons/cafe/commands-permissions.md", page("Cafe Commands And Permissions", """
Use `/hlc` for Cafe-specific addon commands. Cafe recipes also appear in the normal Heirloom `/hl` recipe browser.

| Command | Purpose | Permission |
| --- | --- | --- |
| `/hlc help` | Help | `heirloom.cafe.use` |
| `/hlc list` | List Cafe items | `heirloom.cafe.use` |
| `/hlc give <item> [amount]` | Give Cafe items | `heirloom.cafe.admin` |
| `/hlc reload` | Reload Cafe resources | `heirloom.cafe.admin` |

## Practical Notes

Players usually only need the normal Heirloom menu and recipe search. Admins use `/hlc list` and `/hlc give` while testing Cafe item IDs, then `/hl reload` or the addon reload path after resource edits.
"""))


def reference_pages():
    add("reference/index.md", page("Reference", """
Reference pages are for exact IDs, commands, permissions, and JSON fields. Use guide pages first when learning a system.
"""))
    add("reference/items.md", build_item_reference())
    add("reference/vanilla-items.md", build_vanilla_item_reference())
    add("reference/crops.md", build_crop_reference())
    add("reference/recipes.md", build_recipe_reference())
    add("reference/visual-ids.md", build_visual_reference())
    add("reference/commands.md", page("Command Reference", """
## Core

| Command | Purpose | Permission |
| --- | --- | --- |
| `/hl` | Open main menu | `heirloom.use` |
| `/hl help` | Help | `heirloom.use` |
| `/hl cookbook` | Give recipe book | `heirloom.cookbook` |
| `/hl recipes` | Recipe browser | `heirloom.recipes` |
| `/hl tutorial [lesson\\|stop]` | Private interactive station lessons | `heirloom.tutorial` |
| `/hl search <query>` | Recipe search | `heirloom.recipes` |
| `/hl advancements` | Advancement progress | `heirloom.advancements` |
| `/hl favourite` | Favourite food GUI | `heirloom.favourite` |
| `/hl mastery` | Cooking mastery | `heirloom.mastery` |
| `/hl list <items|recipes|dietary>` | List content | `heirloom.use` |
| `/hl give <item> [amount]` | Give item | `heirloom.give` |
| `/hl cheat` | Admin item GUI | `heirloom.cheat` |
| `/hl reload` | Reload supported data | `heirloom.reload` |
| `/hl lang list` | Locale list | `heirloom.reload` |
| `/hl lang missing <locale>` | Missing locale keys | `heirloom.reload` |
| `/hl debug test` | Diagnostics | `heirloom.debug` |
| `/hl cleanup [radius]` | Remove orphan entities | `heirloom.admin` |

## Addons

See [Distillery Commands](../addons/distillery/commands-permissions.md) and [Cafe Commands](../addons/cafe/commands-permissions.md).
"""))
    crop_perm_rows = []
    for crop in sorted([c for c in CROPS if c["_source"] == "Core"], key=lambda c: c.get("id", "")):
        perm = crop.get("planting", {}).get("permission")
        if perm:
            crop_perm_rows.append([f"`{perm}`", crop.get("id", "")])
    add("reference/permissions.md", page("Permission Reference", f"""
## Core

| Permission | Default | Purpose |
| --- | --- | --- |
| `heirloom.use` | true | Basic access |
| `heirloom.cookbook` | true | Recipe book command |
| `heirloom.recipes` | true | Recipe browser and search |
| `heirloom.tutorial` | true | Private interactive station lessons |
| `heirloom.advancements` | true | Advancement GUI |
| `heirloom.favourite` | true | Favourite food GUI |
| `heirloom.mastery` | true | Mastery GUI |
| `heirloom.give` | op | Give custom items |
| `heirloom.cheat` | op | Cheat item GUI |
| `heirloom.reload` | op | Reload data and language diagnostics |
| `heirloom.debug` | op | Debug tools |
| `heirloom.admin` | op | Parent admin node |

## Crop Planting

{table(["Permission", "Crop"], crop_perm_rows)}

## Addons

| Permission | Default | Purpose |
| --- | --- | --- |
| `heirloom.distillery.use` | true | Distillery commands and menus |
| `heirloom.distillery.admin` | op | Distillery admin tools |
| `heirloom.crop.grape` | true | Plant Distillery grape crops |
| `heirloom.cafe.use` | true | Cafe commands |
| `heirloom.cafe.admin` | op | Cafe item give |
"""))
    add("reference/config-files.md", page("Configuration Files", """
| File | Plugin | Purpose |
| --- | --- | --- |
| `config.yml` | Core | License and locale |
| `custom_items.json` | Core | Main items |
| `custom_items-world.json` | Core | World food items |
| `custom_items-festive.json` | Core | Seasonal foods |
| `recipes.json` | Core | Main recipes |
| `recipes-world.json` | Core | World recipes |
| `recipes-festive.json` | Core | Seasonal recipes |
| `crops.json` | Core | Core crops |
| `dietary_properties.json` | Core | Diet labels |
| `seed_acquisition.json` | Core | Seeds and world discovery |
| `enchantment_integrations.json` | Core | EcoEnchants hooks |
| `custom_items-cafe.json` | Cafe | Cafe items |
| `recipes-cafe.json` | Cafe | Cafe recipes |
| `crops-cafe.json` | Cafe | Coffee crop |
| `custom_items-distillery.json` | Distillery | Grape item definitions |
| `crops-distillery.json` | Distillery | Grape crop definitions |
| `ingredients.yml` | Distillery | Mashables and processing settings |
| `words.yml` | Distillery | Slur replacements |
"""))
    add("reference/recipe-actions-rules.md", page("Recipe Actions And Rules", """
Recipe actions modify output after a recipe matches.

| Action | Purpose |
| --- | --- |
| `SET_PROPERTY` | Set metadata such as display name or `food_property` |
| `ADD_QUALITY` | Add quality to output |
| `SET_QUALITY` | Set output quality |
| `SET_TEXTURE` | Change player-head texture; source-derived wiki recipe tables show distinct output variants when rules set different textures |
| `SET_VISUAL_ITEM` | Swap output to a provider-neutral visual item |
| `SET_RETURN_ITEM` | Emit a craft return; accepts a universal item reference and does not mutate the primary result |
| `SET_CONSUME_RETURN` | Store a consume return reference for an ordinary Heirloom primary result; invalid for provider-owned primary results |

Common triggers include `HAS_INPUT`, `HAS_ANY_INGREDIENT`, `HAS_ALL_INGREDIENTS`, `HAS_INGREDIENT_PROPERTY`, `HAS_ALL_INGREDIENT_PROPERTIES`, and `INPUT_COUNT_GTE`.
"""))
    add("reference/json-fields.md", page("JSON Field Reference", """
## Custom Item Fields

| Field | Meaning |
| --- | --- |
| `id` | Stable uppercase item ID |
| `name` | Display name |
| `base_material` | Vanilla base material |
| `texture` | Player-head texture URL |
| `station_texture` | Cosmetic station ingredient head URL; the original serialized stack retains identity and metadata |
| `item_model` | Item model resource key; vanilla models require no resource pack |
| `edible` | Whether the item can be consumed |
| `food_value` | Hunger restored |
| `saturation` | Saturation restored |
| `consume_seconds` | Consume duration |
| `animation` | `EAT` or `DRINK` style animation |
| `effects` | Potion effects |
| `visual_id` | Provider-neutral visual lookup key |
| `consume_return` | Item returned after consumption or recipe use |
| `placeable_servings` | Cake-like serving count |
| `feast` | Enables feast participant behavior |

## Recipe Fields

| Field | Meaning |
| --- | --- |
| `id` | Stable recipe ID |
| `station` | Cooking station |
| `output` | Main output reference: preferred object has exactly one of `item`, `custom_item`, or `provider_item`, plus optional `amount`; legacy string remains valid |
| `weighted_outputs` | Chance-based output references; every entry uses the same identity shape plus `weight` and optional `amount` |
| `byproducts` | Additional emitted references; `inherit_metadata: true` is invalid for provider-owned byproducts |
| `processing_time` | Ticks |
| `ingredients` | Required/optional slots |
| `actions` | Always-applied output changes |
| `rules` | Conditional output changes |

## Crop Fields

| Field | Meaning |
| --- | --- |
| `id` | Crop ID |
| `item_id` | Item used for planting/harvest |
| `plant_type` | Physical crop behavior |
| `growth` | Timing, scale, stages |
| `planting` | Valid blocks and permissions |
| `textures` | Growing/ripe display textures |
| `harvest` | Drops, sounds, replant, quality chance |
"""))


def legacy_path_pages():
    # Keep old URLs useful and included in nav.
    add("core/cooking-stations.md", page("Core Cooking Stations", "The station docs moved to [Cooking Stations](../stations/index.md)."))
    add("core/recipes.md", page("Core Recipes", "The recipe docs moved to [Recipes](../recipes/index.md) and the [Default Recipe Index](../recipes/default-recipes.md)."))
    add("core/custom-foods.md", page("Core Custom Foods", "The custom food docs moved to [Custom Foods](../customization/custom-foods.md) and [Item Reference](../reference/items.md)."))
    add("core/gardening.md", page("Core Gardening", "The gardening docs moved to [Gardening](../gardening/index.md)."))
    add("core/dietary-properties.md", page("Core Dietary Properties", "The dietary docs moved to [Dietary Properties](../food-systems/dietary-properties.md)."))
    add("core/visual-integrations.md", page("Core Visual Integrations", "Visual docs moved to [Visual Integrations Overview](../customization/visuals-overview.md), [Nexo](../customization/nexo.md), [ItemsAdder](../customization/itemsadder.md), [CraftEngine](../customization/craftengine.md), and [MMOItems](../customization/mmoitems.md)."))
    add("core/admin-configuration.md", page("Core Admin Configuration", "Server owner docs moved to [Configuration](../server-owners/configuration.md)."))
    add("distillery/overview.md", page("Distillery Overview", "Distillery docs moved to [Distillery Addon](../addons/distillery/index.md)."))
    add("distillery/getting-started.md", page("Distillery Getting Started", "Distillery docs moved to [Distillery Getting Started](../addons/distillery/getting-started.md)."))
    add("distillery/brewing-flow.md", page("Distillery Brewing Flow", "Distillery docs moved to [Brewing Flow](../addons/distillery/brewing-flow.md)."))
    add("distillery/mashables-traits.md", page("Distillery Mashables And Traits", "Distillery docs moved to [Mashables And Traits](../addons/distillery/mashables-traits.md)."))
    add("distillery/inebriation.md", page("Distillery Inebriation", "Distillery docs moved to [Inebriation](../addons/distillery/inebriation.md)."))
    add("distillery/admin-configuration.md", page("Distillery Admin Configuration", "Distillery docs moved to [Configuration](../addons/distillery/configuration.md)."))
    add("distillery/commands-permissions.md", page("Distillery Commands And Permissions", "Distillery docs moved to [Commands And Permissions](../addons/distillery/commands-permissions.md)."))
    add("reference/configuration-files.md", page("Configuration Files", "This reference moved to [Config Files](config-files.md)."))
    add("reference/customization.md", page("Customization Notes", "Customization docs moved to [Customization](../customization/index.md)."))


def build_nav() -> str:
    nav = """site_name: Heirloom Wiki
site_description: Wiki and server-owner manual for Heirloom cooking, gardening, Distillery, Cafe, and Pasture.
site_url: https://kernel-person.github.io/heirloom-docs/
repo_url: https://github.com/kernel-person/heirloom-docs
repo_name: kernel-person/heirloom-docs

theme:
  name: material
  language: en
  logo: images/heirloom-logo.png
  favicon: images/heirloom-logo.png
  palette:
    - scheme: default
      primary: green
      accent: deep orange
  features:
    - navigation.instant
    - navigation.instant.prefetch
    - navigation.instant.progress
    - navigation.sections
    - navigation.top
    - navigation.indexes
    - search.suggest
    - search.highlight
    - content.code.copy

extra_css:
  - stylesheets/extra.css

extra_javascript:
  - javascripts/navigation-scroll.js

markdown_extensions:
  - admonition
  - attr_list
  - md_in_html
  - tables
  - toc:
      permalink: true
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - First Meal: getting-started/first-meal.md
      - First Farm: getting-started/first-farm.md
      - Recipe Browser: getting-started/recipe-browser.md
  - Player Guide:
      - Overview: player-guide/index.md
      - Cooking Basics: player-guide/cooking.md
      - In-game Station Tutorials: tutorials/station-tutorials.md
      - Recipe Search: player-guide/recipe-search.md
      - Favourite Food: player-guide/favourite-food.md
      - Food Quality: player-guide/quality.md
      - Advancements: player-guide/advancements.md
      - Cooking Mastery: player-guide/mastery.md
      - Placeable Foods And Feasts: player-guide/placeable-foods.md
      - Seed Discovery: player-guide/seed-discovery.md
  - Mixology Tutorials:
      - Overview: tutorials/mixology.md
      - Juicer: tutorials/mixology-juicer.md
      - Mixology Table: tutorials/mixology-shaker.md
      - Fruit Trees and Harvesting: tutorials/mixology-fruit-harvesting.md
      - Espresso Martini: tutorials/mixology-espresso-martini.md
  - Cooking Stations:
      - Overview: stations/index.md
      - Animated Kitchen: stations/animated-kitchen.md
      - Oven: stations/oven.md
      - Boiling Pot: stations/boiling-pot.md
      - Mixing Bowl: stations/mixing-bowl.md
      - Cutting Board: stations/cutting-board.md
      - Frying Pan: stations/frying-pan.md
      - Barista Machine: stations/barista-machine.md
      - Mixology Table: stations/mixology-table.md
      - Juicer: stations/juicer.md
  - Recipes:
      - Overview: recipes/index.md
      - Default Recipe Index: recipes/default-recipes.md
      - Station Crafting: recipes/workstation-crafting.md
      - Oven Recipes: recipes/station-oven.md
      - Boiling Pot Recipes: recipes/station-boiling-pot.md
      - Mixing Bowl Recipes: recipes/station-mixing-bowl.md
      - Cutting Board Recipes: recipes/station-cutting-board.md
      - Frying Pan Recipes: recipes/station-frying-pan.md
      - Barista Recipes: recipes/station-barista-machine.md
      - Mixology Recipes: recipes/station-mixology-table.md
      - Juicer Recipes: recipes/station-juicer.md
      - Recipe Chains: recipes/recipe-chains.md
  - Gardening:
      - Overview: gardening/index.md
      - Lettuce: gardening/lettuce.md
      - Onion: gardening/onion.md
      - Corn: gardening/corn.md
      - Tomato: gardening/tomato.md
      - Rice: gardening/rice.md
      - Plant Types: gardening/plant-types.md
      - Seed Packets: gardening/seed-packets.md
      - Wild Discovery And Loot: gardening/wild-discovery.md
      - EcoEnchants: gardening/ecoenchants.md
  - Food Systems:
      - Overview: food-systems/index.md
      - Dietary Properties: food-systems/dietary-properties.md
      - Food Properties: food-systems/food-properties.md
      - Quality And Effects: food-systems/quality-and-effects.md
      - Favourite And Social Bonuses: food-systems/favourite-social.md
  - Server Owners:
      - Overview: server-owners/index.md
      - Configuration: server-owners/configuration.md
      - Permissions: server-owners/permissions.md
      - Commands: server-owners/commands.md
      - Language Files: server-owners/language-files.md
      - Region Protection: server-owners/region-protection.md
      - Diagnostics: server-owners/diagnostics.md
      - Updating: server-owners/updating.md
  - Customization:
      - Overview: customization/index.md
      - Custom Foods: customization/custom-foods.md
      - Custom Recipes: customization/custom-recipes.md
      - Custom Crops: customization/custom-crops.md
      - Seed Acquisition: customization/seed-acquisition.md
      - Advancements: customization/advancements.md
      - Visual Integrations: customization/visuals-overview.md
      - Nexo: customization/nexo.md
      - ItemsAdder: customization/itemsadder.md
      - CraftEngine: customization/craftengine.md
      - MMOItems: customization/mmoitems.md
      - Web Generator: customization/web-generator.md
  - Addons:
      - Distillery:
          - Overview: addons/distillery/index.md
          - Getting Started: addons/distillery/getting-started.md
          - Brewing Flow: addons/distillery/brewing-flow.md
          - Drink Families: addons/distillery/families.md
          - Recipe Preview: addons/distillery/recipe-preview.md
          - Cellar Aging: addons/distillery/cellar-aging.md
          - Craftsmanship: addons/distillery/craftsmanship.md
          - Ingredients And Flavour: addons/distillery/mashables-traits.md
          - Inebriation: addons/distillery/inebriation.md
          - Configuration: addons/distillery/configuration.md
          - Commands And Permissions: addons/distillery/commands-permissions.md
      - Cafe:
          - Overview: addons/cafe/index.md
          - Getting Started: addons/cafe/getting-started.md
          - Barista Machine: addons/cafe/barista-machine.md
          - Coffee And Tea Flow: addons/cafe/coffee-tea.md
          - Configuration: addons/cafe/configuration.md
          - Commands And Permissions: addons/cafe/commands-permissions.md
      - Pasture:
          - Overview And Cheese: addons/pasture/dairy.md
          - Animal Care: addons/pasture/animal-care.md
      - Heirloom Mixology:
          - Overview: addons/orchard/index.md
      - Village Trades (candidate):
          - Overview: addons/village-trades/index.md
          - Setup: addons/village-trades/setup.md
          - Survival Progression: addons/village-trades/survival.md
          - Reference: addons/village-trades/reference.md
      - Future Addons: roadmap.md
  - Developer API:
      - Overview & Quickstart: developer/index.md
      - Items & FoodFacts V2: developer/items-and-food-facts.md
      - Bukkit Events: developer/events.md
      - Addons & Registration: developer/addons-and-registration.md
  - Reference:
      - Overview: reference/index.md
      - Commands: reference/commands.md
      - Permissions: reference/permissions.md
      - Config Files: reference/config-files.md
      - Item IDs: reference/items.md
      - Vanilla Ingredients: reference/vanilla-items.md
      - Crop IDs: reference/crops.md
      - Recipe Summary: reference/recipes.md
      - Recipe Actions And Rules: reference/recipe-actions-rules.md
      - JSON Fields: reference/json-fields.md
      - Visual IDs: reference/visual-ids.md
      - Legacy Configuration Path: reference/configuration-files.md
      - Legacy Customization Path: reference/customization.md
  - Gallery: gallery.md
  - Media Needed: media-needed.md
  - Legacy Paths:
      - Core Cooking Stations: core/cooking-stations.md
      - Core Recipes: core/recipes.md
      - Core Custom Foods: core/custom-foods.md
      - Core Gardening: core/gardening.md
      - Core Dietary Properties: core/dietary-properties.md
      - Core Visual Integrations: core/visual-integrations.md
      - Core Admin Configuration: core/admin-configuration.md
      - Distillery Overview: distillery/overview.md
      - Distillery Getting Started: distillery/getting-started.md
      - Distillery Brewing Flow: distillery/brewing-flow.md
      - Distillery Mashables And Traits: distillery/mashables-traits.md
      - Distillery Inebriation: distillery/inebriation.md
      - Distillery Admin Configuration: distillery/admin-configuration.md
      - Distillery Commands And Permissions: distillery/commands-permissions.md
"""
    if CONTENT_PACKS:
        rows = ["  - Content Packs:"]
        for pack in CONTENT_PACKS:
            rows.append(f'      - {pack["name"]}: content-packs/{slug(pack["name"])}.md')
        nav = nav.replace("  - Addons:\n", "\n".join(rows) + "\n  - Addons:\n")
    return nav


def css() -> str:
    css_path = DOCS_ROOT / "docs/stylesheets/extra.css"
    old = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    marker = "/* Heirloom generated utility styles */"
    if marker in old:
        old = old.split(marker, 1)[0].rstrip()
    extra = """
/* Heirloom generated utility styles */

.md-typeset .hl-kbd {
  padding: 0.08rem 0.35rem;
  border: 1px solid var(--hl-border-strong);
  border-radius: 4px;
  background: var(--hl-inner);
  font-size: 0.78rem;
  font-weight: 700;
}

.md-typeset .hl-small {
  color: var(--hl-muted);
  font-size: 0.82rem;
}

.md-typeset .hl-card code,
.md-typeset td code {
  white-space: nowrap;
}

.md-typeset table:not([class]) {
  font-size: 0.78rem;
}

.md-typeset .hl-source-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  min-height: 34px;
  vertical-align: middle;
}

.md-typeset .hl-source-logo {
  display: block;
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 5px;
  filter: drop-shadow(0 1px 1px rgba(43, 33, 24, 0.18));
}

.md-typeset .hl-item-icon {
  width: 28px;
  height: 28px;
  image-rendering: pixelated;
  vertical-align: middle;
  border: 1px solid var(--hl-border-strong);
  border-radius: 4px;
  background: var(--hl-inner);
  box-shadow: 0 1px 2px var(--hl-shadow);
}

.md-typeset .hl-icon-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0.08rem 0.12rem 0.08rem 0;
  line-height: 1;
}

.md-typeset .hl-input-strip,
.md-typeset .hl-recipe-slots {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.32rem 0.42rem;
  align-items: center;
  min-width: 7rem;
}

.md-typeset .hl-ingredient-slot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 54px;
  vertical-align: middle;
}

.md-typeset .hl-slot-box {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.22rem;
  min-height: 54px;
  min-width: 54px;
  padding: 0.14rem 0.24rem;
  border: 1px solid color-mix(in srgb, var(--hl-border-strong) 78%, white);
  border-radius: 7px;
  background: color-mix(in srgb, var(--hl-inner) 94%, white);
  box-shadow: 0 1px 2px rgba(43, 33, 24, 0.16);
}

.md-typeset .hl-recipe-slots .hl-icon-link {
  margin: 0;
}

.md-typeset .hl-recipe-slots .hl-item-icon {
  width: 48px;
  height: 48px;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.md-typeset .hl-slot-choice-icons {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.18rem;
}

.md-typeset .hl-choice-separator {
  color: var(--hl-muted);
  font-size: 0.62rem;
  font-weight: 700;
  line-height: 1;
  text-transform: lowercase;
}

.md-typeset .hl-slot-count {
  position: absolute;
  right: 0.08rem;
  bottom: 0.08rem;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0.88rem;
  height: 0.78rem;
  padding: 0 0.1rem;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 3px;
  background: rgba(24, 20, 18, 0.9);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.42);
  color: #fff7e8;
  font-size: 0.54rem;
  font-weight: 900;
  line-height: 1;
  pointer-events: none;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.85);
  white-space: nowrap;
}

.md-typeset .hl-output-with-variants {
  position: relative;
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}

.md-typeset .hl-output-item {
  display: inline-flex;
  align-items: center;
  gap: 0.46rem;
  color: var(--hl-terracotta);
  font-weight: 700;
  white-space: nowrap;
}

.md-typeset .hl-output-icon-frame {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.md-typeset .hl-output-item .hl-item-icon,
.md-typeset .hl-output-variant-entry .hl-item-icon {
  width: 48px;
  height: 48px;
  border-color: color-mix(in srgb, var(--hl-border-strong) 78%, white);
  border-radius: 7px;
  background: color-mix(in srgb, var(--hl-inner) 94%, white);
  box-shadow: 0 1px 2px rgba(43, 33, 24, 0.16);
}

.md-typeset .hl-output-variant-caret {
  position: absolute;
  right: 0.08rem;
  bottom: 0.08rem;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 0.88rem;
  height: 0.78rem;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 3px;
  background: rgba(24, 20, 18, 0.9);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.42);
  pointer-events: none;
}

.md-typeset .hl-output-variant-caret::before {
  content: "";
  width: 0;
  height: 0;
  border-right: 0.22rem solid transparent;
  border-left: 0.22rem solid transparent;
  border-top: 0.28rem solid #fff7e8;
}

.md-typeset .hl-output-variant-tray {
  position: absolute;
  top: calc(100% + 0.34rem);
  left: 0;
  z-index: 25;
  display: none;
  flex-wrap: wrap;
  gap: 0.34rem;
  min-width: 14rem;
  max-width: min(28rem, 88vw);
  padding: 0.48rem;
  border: 1px solid var(--hl-border-strong);
  border-radius: 7px;
  background: color-mix(in srgb, var(--md-default-bg-color) 96%, white);
  box-shadow: 0 10px 24px rgba(43, 33, 24, 0.22);
}

.md-typeset .hl-output-with-variants:hover .hl-output-variant-tray,
.md-typeset .hl-output-with-variants:focus-within .hl-output-variant-tray {
  display: inline-flex;
}

.md-typeset .hl-output-variant-list {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.38rem;
}

.md-typeset .hl-output-variant-entry {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  color: var(--hl-ink);
  font-size: 0.72rem;
  font-weight: 700;
  white-space: nowrap;
}

.md-typeset .hl-output-item:hover {
  text-decoration: none;
}

.md-typeset .hl-output-name code,
.md-typeset .hl-output-name {
  white-space: nowrap;
}

.md-typeset .hl-icon-missing {
  border-style: dashed;
  opacity: 0.8;
}
"""
    return old.rstrip() + "\n" + extra


def helper_script() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def navigation_scroll_js() -> str:
    return """(function () {
  var NAV_SCROLLWRAP = '.md-sidebar[data-md-type="navigation"] .md-sidebar__scrollwrap';
  var rememberedScrollTop = null;
  var restorePending = false;
  var watchedScrollwrap = null;

  function getScrollwrap() {
    return document.querySelector(NAV_SCROLLWRAP);
  }

  function rememberScroll() {
    var scrollwrap = getScrollwrap();
    if (scrollwrap) {
      rememberedScrollTop = scrollwrap.scrollTop;
    }
  }

  function onSidebarScroll() {
    if (!restorePending) {
      rememberedScrollTop = this.scrollTop;
    }
  }

  function watchSidebar() {
    var scrollwrap = getScrollwrap();
    if (!scrollwrap || scrollwrap === watchedScrollwrap) {
      return;
    }
    if (watchedScrollwrap) {
      watchedScrollwrap.removeEventListener('scroll', onSidebarScroll);
    }
    watchedScrollwrap = scrollwrap;
    watchedScrollwrap.addEventListener('scroll', onSidebarScroll, { passive: true });
    if (rememberedScrollTop === null) {
      rememberedScrollTop = watchedScrollwrap.scrollTop;
    }
  }

  function isInternalLink(link) {
    if (!link || link.target || link.hasAttribute('download')) {
      return false;
    }
    var href = link.getAttribute('href') || '';
    if (!href || href.charAt(0) === '#' || /^(mailto|tel):/i.test(href)) {
      return false;
    }
    try {
      var url = new URL(link.href, window.location.href);
      return url.origin === window.location.origin;
    } catch (_error) {
      return false;
    }
  }

  function restoreScroll() {
    if (!restorePending || rememberedScrollTop === null) {
      return;
    }
    var expected = rememberedScrollTop;
    var apply = function () {
      var scrollwrap = getScrollwrap();
      if (scrollwrap) {
        scrollwrap.scrollTop = expected;
      }
    };

    window.requestAnimationFrame(function () {
      apply();
      window.requestAnimationFrame(function () {
        apply();
        restorePending = false;
      });
    });
  }

  document.addEventListener('click', function (event) {
    var target = event.target;
    if (!(target instanceof Element)) {
      return;
    }
    var link = target.closest('a[href]');
    if (!isInternalLink(link)) {
      return;
    }
    rememberScroll();
    restorePending = true;
  }, true);

  watchSidebar();
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(function () {
      watchSidebar();
      restoreScroll();
    });
  }
})();
"""


def animated_kitchen_pages():
    """Keep station crafting grids tied to the customer package's source."""
    source = PLUGIN_ROOT / "tools/kitchen-playtest/package_customer_release.py"
    if not source.is_file():
        add("recipes/workstation-crafting.md", page("Station crafting recipes",
            "Select an Animated Kitchen release checkout with `HEIRLOOM_PLUGIN_ROOT` "
            "to generate this reference. See [Animated Kitchen](../stations/animated-kitchen.md)."))
        return
    spec = importlib.util.spec_from_file_location("heirloom_wiki_kitchen_package", source)
    module = importlib.util.module_from_spec(spec)
    previous_path = list(sys.path)
    try:
        sys.path.insert(0, str(source.parent))
        spec.loader.exec_module(module)
        files = module.assemble()
    finally:
        sys.path[:] = previous_path
    catalog = json.loads(files["catalog.json"])
    reference = module.recipe_guide(catalog["stations"])
    if isinstance(reference, bytes):
        reference = reference.decode("utf-8")
    note = (
        "\n\nGenerated from the Animated Kitchen " + catalog["version"]
        + " installation catalog. Server overrides may differ; use `/hl` → **Crafting** "
        "for your server's available recipes. See [Animated Kitchen](../stations/animated-kitchen.md) "
        "for installation, controls and required gameplay addons.\n"
    )
    add("recipes/workstation-crafting.md", reference.rstrip() + note)


def write_all():
    PAGES.clear()
    sync_marketing_images()
    sync_source_logos()
    sync_mixology_branding()
    sync_addon_release_banners()
    ensure_icon_assets(FETCH_ICONS, USE_VISUAL_PACK_ICONS)
    basic_pages()
    getting_started_pages()
    player_pages()
    station_pages()
    recipes_pages()
    gardening_pages()
    food_system_pages()
    server_owner_pages()
    customization_pages()
    content_pack_pages()
    addons_pages()
    reference_pages()
    legacy_path_pages()
    animated_kitchen_pages()
    write_cheese_flowchart()

    # These guides are maintained in the wiki, independently of plugin releases.
    # Keep them in generation so linked pages survive regeneration unchanged.
    for source in sorted(PAGE_SOURCE_ROOT.rglob("*.md")):
        add(source.relative_to(PAGE_SOURCE_ROOT).as_posix(), source.read_text(encoding="utf-8"))

    docs_dir = DOCS_ROOT / "docs"
    for path, content in PAGES.items():
        target = docs_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    (DOCS_ROOT / "mkdocs.yml").write_text(build_nav(), encoding="utf-8")
    (docs_dir / "stylesheets").mkdir(parents=True, exist_ok=True)
    (docs_dir / "stylesheets/extra.css").write_text(css(), encoding="utf-8")
    (docs_dir / "javascripts").mkdir(parents=True, exist_ok=True)
    (docs_dir / "javascripts/navigation-scroll.js").write_text(navigation_scroll_js(), encoding="utf-8")
    (DOCS_ROOT / "tools").mkdir(parents=True, exist_ok=True)
    (DOCS_ROOT / "tools/generate_reference_pages.py").write_text(helper_script(), encoding="utf-8")

    keep = {str(Path(path)) for path in PAGES}
    for md in docs_dir.rglob("*.md"):
        rel = str(md.relative_to(docs_dir))
        if rel not in keep:
            md.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate the Heirloom MkDocs wiki from source JSON resources.")
    parser.add_argument("--fetch-icons", action="store_true", help="Download and cache missing player-head and vanilla item icons.")
    parser.add_argument("--use-visual-pack-icons", action="store_true", help="Prefer bundled Nexo/ItemsAdder visual-pack PNGs for wiki item icons. By default, player-head items use generated isometric icons and vanilla items use Minecraft textures.")
    args = parser.parse_args()
    FETCH_ICONS = args.fetch_icons
    USE_VISUAL_PACK_ICONS = args.use_visual_pack_icons
    write_all()
    missing_count = len([entry for entry in ICON_MANIFEST.values() if entry.get("status") != "ok"])
    print(f"Wrote {len(PAGES)} wiki pages to {DOCS_ROOT / 'docs'}")
    print(f"Icon manifest: {len(ICON_MANIFEST)} entries, {missing_count} missing")
