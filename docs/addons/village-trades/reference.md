# Village Trades reference

!!! warning "Unpublished candidate reference"
    This reference describes **1.0.0-rc.1**. Public minimum Core compatibility is
    **pending**. Use the exact paired builds and hashes in the candidate manifest.
    The table below is generated from its `catalog.json`, not from a released
    Core installation.

<!-- village-trades-catalog:start -->

## Collection

| Definition | Count |
| --- | ---: |
| Products | 39 |
| Public provider references | 236 |
| Workstation recipes | 41 |
| Native forge-blank recipes | 19 |
| Bootstrap recipes | 2 |
| Crops | 3 |
| Deposits | 1 |
| Arrow combinations | 80 |

Workmanship grades are variants of a product. Internal loaded-tongs appearances
and the retained test template are excluded from the public product list.

## Products

| Product | Station | Workmanship variants | Family ID |
| --- | --- | ---: | --- |
| Iron Shortsword | Smithing Anvil | 6 | `VT_SHORTSWORD` |
| Woodcutter's Hatchet | Smithing Anvil | 6 | `VT_HATCHET` |
| Village Iron Helmet | Smithing Anvil | 6 | `VT_HELMET` |
| Village Iron Boots | Smithing Anvil | 6 | `VT_BOOTS` |
| Smith's Hammer | Smithing Anvil | 6 | `VT_SMITHS_HAMMER` |
| Ember Sword | Smithing Anvil | 6 | `VT_EMBER_SWORD` |
| Wayfarer’s Sword | Smithing Anvil | 6 | `VT_WAYFARER_SWORD` |
| Village Iron Chestplate | Smithing Anvil | 6 | `VT_CHESTPLATE` |
| Village Iron Leggings | Smithing Anvil | 6 | `VT_LEGGINGS` |
| Small Health Potion | Boiling Pot | 6 | `VT_HONEY_THYME_SYRUP` |
| Small Mana Potion | Boiling Pot | 6 | `VT_LEMON_BALM_CORDIAL` |
| Large Health Potion | Boiling Pot | 6 | `VT_STRONG_HONEY_THYME_SYRUP` |
| Large Mana Potion | Boiling Pot | 6 | `VT_STRONG_LEMON_BALM_CORDIAL` |
| Strength Potion | Boiling Pot | 6 | `VT_PHYSICAL_TONIC` |
| Spellpower Potion | Boiling Pot | 6 | `VT_MAGIC_TONIC` |
| Comfrey Poultice | Mixing Bowl | 6 | `VT_COMFREY_POULTICE` |
| Hearth Rune | Smithing Anvil | Single | `VT_HEARTH_RUNE` |
| Focus Rune | Smithing Anvil | Single | `VT_FOCUS_RUNE` |
| Greater Hearth Rune | Smithing Anvil | Single | `VT_GREATER_HEARTH_RUNE` |
| Tempering Compound | Mixing Bowl | Single | `VT_TEMPERING_COMPOUND` |
| Unbinding Wax | Mixing Bowl | Single | `VT_UNBINDING_WAX` |
| Repair Kit | Mixing Bowl | Single | `VT_REPAIR_KIT` |
| Rowan & Iron Charm | Smithing Anvil | Single | `VT_ROWAN_CHARM` |
| Doomsword | Smithing Anvil | 6 | `VT_DOOMSWORD` |
| Angel's Talon | Smithing Anvil | 6 | `VT_ANGELS_TALON` |
| Doomplate Helmet | Smithing Anvil | 6 | `VT_DOOMPLATE_HELMET` |
| Doomplate Chestplate | Smithing Anvil | 6 | `VT_DOOMPLATE_CHESTPLATE` |
| Doomplate Leggings | Smithing Anvil | 6 | `VT_DOOMPLATE_LEGGINGS` |
| Doomplate Boots | Smithing Anvil | 6 | `VT_DOOMPLATE_BOOTS` |
| Angelplate Helmet | Smithing Anvil | 6 | `VT_ANGELPLATE_HELMET` |
| Angelplate Chestplate | Smithing Anvil | 6 | `VT_ANGELPLATE_CHESTPLATE` |
| Angelplate Leggings | Smithing Anvil | 6 | `VT_ANGELPLATE_LEGGINGS` |
| Angelplate Boots | Smithing Anvil | 6 | `VT_ANGELPLATE_BOOTS` |
| Village Bow | Woodworking Bench | 6 | `VT_BOW` |
| Carved Staff | Woodworking Bench | 6 | `VT_STAFF` |
| Bramble Bow | Woodworking Bench | 6 | `VT_BRAMBLE_BOW` |
| Doom Staff | Woodworking Bench | 6 | `VT_DOOM_STAFF` |
| Rainbow Staff | Woodworking Bench | 6 | `VT_RAINBOW_STAFF` |
| Fletched Arrows | Woodworking Bench | Single | `VT_FLETCH_ARROWS` |

<!-- Source catalog.json SHA-256: b5ce90642689ebc9d5506ab9dff13ae7a22b5d5381a603f7030996889e846a1f -->
<!-- village-trades-catalog:end -->

## Definitions and ownership

`catalog.json` in the candidate archive lists every public provider reference,
exact workstation recipe, native preparation grid, crop and deposit. The
in-game recipe browser uses the server's installed definitions and available
providers. Do not substitute a renamed vanilla item for an exact MMOItems identity.

Provider names normalize, but provider-specific type/item IDs preserve case.
Finished equipment, durability, lore, effects, sockets and upgrades remain native
MMOItems data. Heirloom owns station work, grading and the persisted unfinished
workpieces. Displays are projections of saved work, not extra refundable items.

## Operator commands

| Command | Use |
| --- | --- |
| `/vtrades help` | Workshop instructions. |
| `/vtrades status` | Inspect workshop status. |
| `/vtrades integrations` | Report current native integration modes; it is not an acceptance test. |
| `/hl deposits place VT_MITHRAL_DEPOSIT` | Register a valid bottom Stone Slab as a deposit. |
| `/hl deposits inspect` | Read remaining cycles and replenishment status. |
| `/hl deposits remove` | Remove registration without removing the slab; pending rewards must resolve first. |

Testing kits and effect auditions are operator tools. The addon declares
`village-trades.kit` and `village-trades.debug`, both operator-only by default.
Ordinary survival progression does not depend on kits. The deposit commands use
Core's administrative permission checks.

## Files to customize

| Server path | Content |
| --- | --- |
| `plugins/HeirloomVillageTrades/config.yml` | Workshop controls, balance and pack identity. |
| `plugins/HeirloomVillageTrades/recipes-village-trades.json` | Workstation recipe definitions and outputs. |
| `plugins/HeirloomVillageTrades/patterns.yml` | Smithing patterns. |
| `plugins/HeirloomVillageTrades/crops-village-trades.json` | Cultivatable herbs. |
| `plugins/HeirloomVillageTrades/acquisition-village-trades.json` | Discovery routes. |
| `plugins/HeirloomVillageTrades/deposits-village-trades.json` | Deposit yields, appearance and replenishment. |
| `plugins/Heirloom/custom_items-village-trades.json` | Provider-item catalogue declarations. |
| `plugins/MMOItems/item/*.yml` | Native item templates merged from supplied fragments. |
| `plugins/MythicLib/script/village_trades.yml` and `skill/village_trades.yml` | Native skill definitions. |

`workshop.json` is runtime state, not a configuration template. Never replace it
with a default or clear paid work to bypass a failed reload. Preserve it alongside
worlds and inventories. [Setup](setup.md) covers reload order and rollback.
