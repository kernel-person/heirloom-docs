# Station crafting recipes

Use a crafting table. Each recipe makes one placeable station.
Spaces in the patterns are empty slots. Ingredients are ordinary Minecraft items.
Keep every empty cell clear; horizontal mirrors are accepted. The two-row boiling pot pattern can occupy either pair of rows.
Planks and wooden slabs use their Minecraft tags: any member works in each marked cell, including mixed woods. Stone slabs do not qualify.
The default install supplies five Core recipes. The optional addon-workstations overlay adds the other eight.

## Oven

Item: `heirloom:rustic_oven`; output: 1.
Gameplay requirement: Heirloom 2.11.0.
Installation: default Core.

```text
 B 
BTB
BFB
```

- F: furnace
- B: bricks
- T: iron trapdoor

Total: 5 × minecraft:bricks, 1 × minecraft:furnace, 1 × minecraft:iron_trapdoor.

## Boiling Pot

Item: `heirloom:rustic_boiling_pot`; output: 1.
Gameplay requirement: Heirloom 2.11.0.
Installation: default Core.

```text
 C 
BFB
```

- C: cauldron
- F: campfire
- B: bricks

Total: 2 × minecraft:bricks, 1 × minecraft:campfire, 1 × minecraft:cauldron.

## Frying Pan

Item: `heirloom:rustic_frying_pan`; output: 1.
Gameplay requirement: Heirloom 2.11.0.
Installation: default Core.

```text
 PS
NNN
NFN
```

- N: iron nugget
- S: stick
- F: furnace
- P: heavy weighted pressure plate

Total: 1 × minecraft:furnace, 1 × minecraft:heavy_weighted_pressure_plate, 5 × minecraft:iron_nugget, 1 × minecraft:stick.

## Mixing Bowl

Item: `heirloom:rustic_mixing_bowl`; output: 1.
Gameplay requirement: Heirloom 2.11.0.
Installation: default Core.

```text
 S 
B B
 B 
```

- B: brick
- S: wooden shovel

Total: 3 × minecraft:brick, 1 × minecraft:wooden_shovel.

## Cutting Board

Item: `heirloom:rustic_cutting_board`; output: 1.
Gameplay requirement: Heirloom 2.11.0.
Installation: default Core.

```text
  S
 I 
WWW
```

- W: any wooden slab (#minecraft:wooden_slabs)
- I: iron ingot
- S: stick

Total: 3 × #minecraft:wooden_slabs, 1 × minecraft:iron_ingot, 1 × minecraft:stick.

## Barista Machine

Item: `heirloom:rustic_barista_machine`; output: 1.
Gameplay requirement: HeirloomCafe 2.11.0.
Installation: optional addon-workstations overlay.

```text
CIC
IBI
CRC
```

- C: copper ingot
- I: iron ingot
- B: bucket
- R: redstone

Total: 1 × minecraft:bucket, 4 × minecraft:copper_ingot, 3 × minecraft:iron_ingot, 1 × minecraft:redstone.

## Mixology Table

Item: `heirloom:rustic_mixology_table`; output: 1.
Gameplay requirement: HeirloomOrchard 1.0.1.
Installation: optional addon-workstations overlay.

```text
 B 
ISI
PPP
```

- B: glass bottle
- I: iron ingot
- S: stick
- P: any planks (#minecraft:planks)

Total: 3 × #minecraft:planks, 1 × minecraft:glass_bottle, 2 × minecraft:iron_ingot, 1 × minecraft:stick.

## Juicer

Item: `heirloom:rustic_juicer`; output: 1.
Gameplay requirement: HeirloomOrchard 1.0.1.
Installation: optional addon-workstations overlay.

```text
GGG
GPG
IRI
```

- G: glass
- P: piston
- I: iron ingot
- R: redstone

Total: 5 × minecraft:glass, 2 × minecraft:iron_ingot, 1 × minecraft:piston, 1 × minecraft:redstone.

## Farmhouse Press

Item: `heirloom:rustic_farmhouse_press`; output: 1.
Gameplay requirement: HeirloomPasture 2.11.0.
Installation: optional addon-workstations overlay.

```text
IPI
B B
LLL
```

- I: iron ingot
- P: piston
- B: barrel
- L: any planks (#minecraft:planks)

Total: 3 × #minecraft:planks, 2 × minecraft:barrel, 2 × minecraft:iron_ingot, 1 × minecraft:piston.

## Stomping Tub

Item: `heirloom:rustic_stomping_tub`; output: 1.
Gameplay requirement: HeirloomDistillery 2.11.0.
Installation: optional addon-workstations overlay.

```text
P P
P P
SSS
```

- P: any planks (#minecraft:planks)
- S: any wooden slab (#minecraft:wooden_slabs)

Total: 4 × #minecraft:planks, 3 × #minecraft:wooden_slabs.

## Fermentation Vat

Item: `heirloom:rustic_fermentation_vat`; output: 1.
Gameplay requirement: HeirloomDistillery 2.11.0.
Installation: optional addon-workstations overlay.

```text
ICI
IBI
IHI
```

- I: iron nugget
- C: copper ingot
- B: barrel
- H: tripwire hook

Total: 1 × minecraft:barrel, 1 × minecraft:copper_ingot, 6 × minecraft:iron_nugget, 1 × minecraft:tripwire_hook.

## Distillation Still

Item: `heirloom:rustic_distillation_still`; output: 1.
Gameplay requirement: HeirloomDistillery 2.11.0.
Installation: optional addon-workstations overlay.

```text
CBC
CFC
CRC
```

- C: copper ingot
- B: bucket
- F: furnace
- R: redstone

Total: 1 × minecraft:bucket, 6 × minecraft:copper_ingot, 1 × minecraft:furnace, 1 × minecraft:redstone.

## Aging Rack

Item: `heirloom:rustic_aging_rack`; output: 1.
Gameplay requirement: Heirloom 2.11.0.
Installation: optional addon-workstations overlay.

```text
P P
SSS
P P
```

- P: any planks (#minecraft:planks)
- S: any wooden slab (#minecraft:wooden_slabs)

Total: 4 × #minecraft:planks, 3 × #minecraft:wooden_slabs.

## Administrator supply

An administrator can also supply a station with `/ce item give <player> <item-id> 1`.
Use the exact provider IDs above or in `catalog.json`. Crafting a station does not install its gameplay addon.
The aging rack is Core storage; Distillery/Pasture supply its aging recipes.

Generated from the Animated Kitchen 1.0.0 installation catalog. Server overrides may differ; use `/hl` → **Crafting** for your server's available recipes. See [Animated Kitchen](../stations/animated-kitchen.md) for installation, controls and required gameplay addons.
