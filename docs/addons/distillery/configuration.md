# Distillery Configuration

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
