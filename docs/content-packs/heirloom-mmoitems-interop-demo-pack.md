# Heirloom MMOItems Interop Demo Pack

Heirloom MMOItems Interop Demo Pack 1.0.0 contains **0 custom items** and **1 recipe entries**. The PNG sprites can be used as a visual pack without Heirloom. Heirloom 2.9+ adds the cooking stations, recipe matching, food behavior, dynamic variants, and placeable feasts.

| Field | Value |
| --- | --- |
| Pack ID | `heirloom_mmoitems_demo` |
| Version | `1.0.0` |
| Status | release |
| Requires Heirloom | 2.9+ |
| Recipe override strength | 0 |
| Items | 0 |
| Recipe entries | 1 |
| PNG sprites | 0 |
| Bundled provider configuration | MMOItems |

## Installation And Visual Providers

Copy the JSON files from `content/` directly into `plugins/Heirloom/`, then run `/hl reload` and check Installed Content. The pack always retains player-head fallbacks.

The release includes **0 raw PNG sprites** and ready-to-install configuration for **MMOItems**. Install only the provider used by your server.

## Items

| Icon | Item ID | Name | Behavior |
| --- | --- | --- | --- |

## Recipes

### Oven

| Recipe | Output | Inputs | Ingredient rules | Time |
| --- | --- | --- | --- | --- |
| [`MMOITEMS_POISONED_SWORD`](../recipes/default-recipes.md#recipe-mmoitems-poisoned-sword) | <a class="hl-output-item" href="../../recipes/default-recipes/#recipe-mmoitems-poisoned-sword"><span class="hl-output-icon-frame"><img class="hl-item-icon hl-icon-missing hl-output-icon" src="../../images/items/system/missing.png" alt="MMOITEMS:SWORD:POISONED_SWORD" title="Default Mmoitems:Sword:Poisoned Sword"></span><span class="hl-output-name">MMOITEMS:SWORD:POISONED_SWORD</span></a> | <span class="hl-recipe-slots"><span class="hl-ingredient-slot hl-slot-required" title="Required slot 1: 1; ANY"><span class="hl-slot-box"><img class="hl-item-icon hl-icon-missing" src="../../images/items/system/tag.png" alt="Required slot 1: 1; ANY" title="Required slot 1: 1; ANY"></span></span><span class="hl-ingredient-slot hl-slot-required" title="Required slot 2: 1; IRON_INGOT"><span class="hl-slot-box"><a class="hl-icon-link" href="../../reference/vanilla-items/#vanilla-item-iron-ingot"><img class="hl-item-icon" src="../../images/items/minecraft/iron-ingot.png" alt="IRON_INGOT" title="Required slot 2: 1; IRON_INGOT"></a></span></span><span class="hl-ingredient-slot hl-slot-required" title="Required slot 3: 1; STICK"><span class="hl-slot-box"><a class="hl-icon-link" href="../../reference/vanilla-items/#vanilla-item-stick"><img class="hl-item-icon" src="../../images/items/minecraft/stick.png" alt="STICK" title="Required slot 3: 1; STICK"></a></span></span></span> | required: 1 x any<br>required: 1 x [`IRON_INGOT`](../reference/vanilla-items.md#vanilla-item-iron-ingot)<br>required: 1 x [`STICK`](../reference/vanilla-items.md#vanilla-item-stick) | 100 ticks |

## Removing The Pack

Remove both JSON files together and run `/hl reload`. Heirloom will restore any weaker built-in recipe definitions that this pack overrode.
