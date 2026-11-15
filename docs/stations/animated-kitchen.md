# Animated Kitchen

Heirloom Animated Kitchen adds animated furniture for cooking on your server.
Bake on a sliding oven tray, toss food in a skillet, stir a bowl and chop on a
board. The stations use Heirloom's recipes, ingredients and quality rules.

!!! note "Release candidate"
    This page describes the upcoming Animated Kitchen 1.0.0 candidate. Use its
    matching runtime and resource files together. Final download details and
    client acceptance will accompany the public release.

## What is included

The default installation contains the oven, boiling pot, frying stove, mixing
bowl and cutting board. The pot and heated stations include their bases. Place
the bowl and board on a counter built from ordinary blocks.

An optional overlay adds the barista machine, mixology table, juicer, farmhouse
press, stomping tub, fermentation vat, distillation still and aging rack. Their
cooking behavior requires the gameplay addons listed below. The aging rack
belongs to Core; Distillery and Pasture supply aging recipes.

The optional menu theme covers the recipe browser's upper panel and leaves the
player inventory unchanged. Players without a loaded resource pack keep ordinary
menus. Core 3D Food is a separate optional pack and is not included.

## Craft and use a station

Open `/hl` and select **Crafting**. Choose a station to see its shaped recipe,
ingredients and output. Tin Cans, Farmer's Hoes and supported crafting recipes
from installed addons appear here too. Follow ingredient links to trace recipes,
then use a normal crafting table to make the item.
New Crafting labels fall back to English until your server supplies translations.

The menu shows recipes available on your server. Administrators can change
recipes or omit optional content. The [default crafting reference](../recipes/workstation-crafting.md)
is generated from the installation package and lists all thirteen station recipes.

Place the station item as furniture. Leave room for moving parts; the oven needs
a clear 2×2 footprint and two blocks of height. Place countertop pieces on a solid
counter. Existing block-built Heirloom stations continue to work.

- Insert ingredients with the normal Heirloom controls.
- Empty-hand right-click works the bowl's spoon or board's cleaver. Normal shovel
  mixing and tool chopping remain available.
- Empty-hand left-click collects contents.
- Heated stations use actual recipe durations. Fire and light effects do not
  replace the floor or counter.
- Jump inside the stomping tub to mash. Follow the owning addon's bottle and
  serving controls for fermentation and distillation.

Normal removal returns the station and its recoverable contents once. Denied
removal should leave both in place. An interrupted, unfinished batch retains its
inputs but restarts processing progress when loaded again. Completed outputs persist.

## Requirements

The target is **Minecraft Java/Paper 26.2**, **Java 25**, **CraftEngine 26.9.1** and
the matching Heirloom Core runtime. Different private builds can share `2.11.0`,
so use the release manifest and checksums to identify the matching JARs. Obtain
Heirloom and CraftEngine separately; the artwork ZIP contains no plugin JARs.

| Optional workstation | Gameplay requirement |
| --- | --- |
| Barista machine | Heirloom Café 2.11.0 |
| Mixology table and juicer | Heirloom Mixology / HeirloomOrchard 1.0.1 |
| Farmhouse press | Heirloom Pasture 2.11.0 |
| Stomping tub, fermentation vat, distillation still | Heirloom Distillery 2.11.0 |
| Aging rack | Core 2.11.0; Distillery or Pasture for their aging recipes |

Use the companion builds identified in the release manifest. Visual definitions
alone do not install their gameplay addon. This package does not claim Nexo,
ItemsAdder, MMOItems or Bedrock support.

## Install

1. Stop the server and back up worlds, plugin data and the resource pack.
2. Install the matching runtime, retaining existing configuration and license
   files. Keep one JAR per plugin.
3. Copy the ZIP's `install/plugins/` contents into `plugins/`. This includes the
   CraftEngine resource folder and required Heirloom
   `station-visuals/rustic-kitchen.json` manifest.
4. Copy `optional/addon-workstations/install/plugins/` for the optional stations
   and install their gameplay addons.
5. Enable CraftEngine's `furniture.light-system.enable` for cooking light. Set up
   automatic pack hosting at an address your players can reach.
6. Start the server. Run `ce reload all`, then `ce reload pack`. Reconnect, accept
   the pack, and open `/hl` → **Crafting**.

## Update or remove

Collect batches and stored items before updating. Remove old ovens without room
for the current model, then stop and back up the server. Follow the ZIP's guide
to replace the dedicated workstation resource folder and external manifests
together. Do not leave an old monolithic `rustic_workstations.yml` alongside the
new Core/addon configuration files.

Restart after changing JARs or station manifests. Rebuild the pack and reconnect;
avoid generic plugin hot-reloaders.

Before uninstalling, collect contents and remove furniture while both plugins
are active. Stop the server, remove only Animated Kitchen resources, manifests
and theme, then restart and rebuild the pack. To disable only the menu theme,
remove `plugins/Heirloom/gui-themes/animated-kitchen.json` and restart.

## Troubleshooting

- **Missing from Crafting:** check that the provider definition, recipe and
  gameplay owner are installed. Missing content does not receive invented recipes.
- **Static furniture or mismatched parts:** check matching JARs and external
  station manifests, then restart.
- **Old or missing textures:** rebuild the pack, check its hosting address,
  reconnect and accept the update.
- **No cooking light:** enable CraftEngine's furniture light system.
- **Cannot place or use:** check space, permissions and claim restrictions.
  Test both an allowed area and a denied area before opening to players.

The download includes `RECIPES.md`, `catalog.json`, checksums, audio credits and
the full installation guide. Keep its release manifest with your backup.
