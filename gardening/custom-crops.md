# 🌾 Custom Crops

This reference covers the technical details of Heirloom's custom crop system, including how to configure existing crops and understand the configuration format.

***

## Crop Configuration

All crops are defined in `crops.json`. Each crop entry contains:

| Section | Purpose |
|---------|---------|
| `id` | Unique identifier for the crop |
| `item_id` | Custom item ID that drops on harvest |
| `plant_type` | Growing behavior (SHORT_PLANT, TALL_PLANT, etc.) |
| `growth` | Growth timing and visual scaling |
| `planting` | Where the crop can be planted |
| `textures` | Custom textures for growing/ripe states |
| `harvest` | Drop configuration |
| `spreading` | (Vines only) Spreading behavior |

***

## Plant Types Reference

<details>

<summary>🌿 SHORT_PLANT</summary>

Small ground-level plants like lettuce and herbs.

```json
{
  "plant_type": "SHORT_PLANT",
  "block_material": "FERN",
  "display_offset_y": 0.5,
  "requires_water": false,
  "requires_wall": false,
  "can_spread": false
}
```

**Characteristics:**
- Uses a fern as the base block
- Floating display 0.5 blocks above ground
- No special requirements

</details>

<details>

<summary>🌾 TALL_PLANT</summary>

Tall crops like corn and sunflowers.

```json
{
  "plant_type": "TALL_PLANT",
  "block_material": "TALL_GRASS",
  "display_offset_y": 1.6,
  "requires_water": false,
  "requires_wall": false,
  "can_spread": false
}
```

**Characteristics:**
- Uses tall grass as the base block
- Display positioned higher (1.6 blocks)
- Needs 2 blocks of vertical space

</details>

<details>

<summary>🍇 VINE</summary>

Climbing plants that attach to walls.

```json
{
  "plant_type": "VINE",
  "block_material": "VINE",
  "display_offset_y": 0.5,
  "requires_water": false,
  "requires_wall": true,
  "can_spread": true,
  "spread_chance": 0.05,
  "spread_direction": "UP"
}
```

**Characteristics:**
- Uses vine as the base block
- Must be placed on a wall
- Can spread in a direction

</details>

<details>

<summary>💧 AQUATIC</summary>

Water plants like rice.

```json
{
  "plant_type": "AQUATIC",
  "block_material": "SMALL_DRIPLEAF",
  "display_offset_y": 1.6,
  "requires_water": true,
  "requires_wall": false,
  "can_spread": false
}
```

**Characteristics:**
- Uses small dripleaf as base
- Requires water block above the soil
- Display positioned to peek above water

</details>

<details>

<summary>🫐 BUSH</summary>

Bush-type plants like berries.

```json
{
  "plant_type": "BUSH",
  "block_material": "SWEET_BERRY_BUSH",
  "display_offset_y": 0.3,
  "requires_water": false,
  "requires_wall": false,
  "can_spread": false
}
```

**Characteristics:**
- Uses sweet berry bush as base
- Low-positioned display

</details>

<details>

<summary>🪴 HANGING</summary>

Plants that hang from ceilings.

```json
{
  "plant_type": "HANGING",
  "block_material": "HANGING_ROOTS",
  "display_offset_y": -0.3,
  "requires_water": false,
  "requires_wall": false,
  "requires_ceiling": true,
  "can_spread": false
}
```

**Characteristics:**
- Uses hanging roots as base
- Requires a solid block above
- Display positioned below attachment point

</details>

***

## Full Crop Example

<details>

<summary>📋 Lettuce Configuration</summary>

```json
{
  "id": "LETTUCE",
  "item_id": "LETTUCE",
  "plant_type": "SHORT_PLANT",
  "growth": {
    "base_duration_seconds": 300,
    "variance": 0.2,
    "stages": 4,
    "scale_start": 0.3,
    "scale_end": 1.0
  },
  "planting": {
    "valid_blocks": ["GRASS_BLOCK", "DIRT", "COARSE_DIRT", "PODZOL", "ROOTED_DIRT"],
    "consume_item": true
  },
  "textures": {
    "growing": "http://textures.minecraft.net/texture/e5196969afcc...",
    "ripe": "http://textures.minecraft.net/texture/9979fe7b32fb..."
  },
  "harvest": {
    "drops": [
      {"item_id": "LETTUCE", "min": 1, "max": 3, "chance": 1.0}
    ],
    "bonus_drops": [
      {"item_id": "LETTUCE", "min": 1, "max": 1, "chance": 0.15, "requires_fortune": true}
    ],
    "replant_after_harvest": true,
    "harvest_sound": "BLOCK_SWEET_BERRY_BUSH_PICK_BERRIES",
    "break_sound": "BLOCK_GRASS_BREAK"
  }
}
```

</details>

<details>

<summary>📋 Tomato (Vine) Configuration</summary>

```json
{
  "id": "TOMATO",
  "item_id": "TOMATO",
  "plant_type": "VINE",
  "growth": {
    "base_duration_seconds": 420,
    "variance": 0.2,
    "stages": 4,
    "scale_start": 0.25,
    "scale_end": 0.6
  },
  "planting": {
    "valid_wall_blocks": [
      "STONE", "COBBLESTONE", "STONE_BRICKS", "MOSSY_STONE_BRICKS",
      "DEEPSLATE", "BRICKS", "MUD_BRICKS",
      "OAK_PLANKS", "SPRUCE_PLANKS", "BIRCH_PLANKS", "JUNGLE_PLANKS",
      "ACACIA_PLANKS", "DARK_OAK_PLANKS", "MANGROVE_PLANKS",
      "CHERRY_PLANKS", "BAMBOO_PLANKS"
    ],
    "consume_item": true
  },
  "textures": {
    "growing": "http://textures.minecraft.net/texture/b77ad7b0ebfb...",
    "ripe": "http://textures.minecraft.net/texture/4f14b58f3df6..."
  },
  "spreading": {
    "enabled": true,
    "chance_per_check": 0.08,
    "direction": "UP",
    "max_chain_length": 4
  },
  "harvest": {
    "drops": [
      {"item_id": "TOMATO", "min": 1, "max": 2, "chance": 1.0}
    ],
    "replant_after_harvest": true,
    "harvest_sound": "BLOCK_SWEET_BERRY_BUSH_PICK_BERRIES",
    "break_sound": "BLOCK_VINE_BREAK"
  }
}
```

</details>

<details>

<summary>📋 Rice (Aquatic) Configuration</summary>

```json
{
  "id": "RICE",
  "item_id": "RICE",
  "plant_type": "AQUATIC",
  "growth": {
    "base_duration_seconds": 360,
    "variance": 0.15,
    "stages": 4,
    "scale_start": 0.3,
    "scale_end": 0.7
  },
  "planting": {
    "valid_blocks": ["DIRT", "CLAY", "MUD", "GRAVEL", "SAND"],
    "requires_water_above": true,
    "consume_item": true
  },
  "textures": {
    "growing": "http://textures.minecraft.net/texture/1ab4af751124...",
    "ripe": "http://textures.minecraft.net/texture/cb70f2fb5ebf..."
  },
  "harvest": {
    "drops": [
      {"item_id": "RICE", "min": 2, "max": 4, "chance": 1.0}
    ],
    "replant_after_harvest": true,
    "harvest_sound": "BLOCK_WET_GRASS_BREAK",
    "break_sound": "BLOCK_WET_GRASS_BREAK"
  }
}
```

</details>

***

## Configuration Properties

### Growth Settings

| Property | Type | Description |
|----------|------|-------------|
| `base_duration_seconds` | int | Base time to fully grow |
| `variance` | float | Random variance (0.2 = ±20%) |
| `stages` | int | Number of growth stages |
| `scale_start` | float | Initial visual scale (0.0-1.0) |
| `scale_end` | float | Final visual scale (0.0-1.0) |

### Planting Settings

| Property | Type | Description |
|----------|------|-------------|
| `valid_blocks` | array | Block types the crop can be planted on |
| `valid_wall_blocks` | array | (Vines) Wall blocks the crop attaches to |
| `requires_water_above` | bool | (Aquatic) Must have water above |
| `consume_item` | bool | Whether planting consumes the seed item |

### Harvest Settings

| Property | Type | Description |
|----------|------|-------------|
| `drops` | array | Main drop items with min/max/chance |
| `bonus_drops` | array | Extra drops (fortune, rare) |
| `replant_after_harvest` | bool | Auto-replant after harvest |
| `harvest_sound` | string | Sound played on harvest |
| `break_sound` | string | Sound played if destroyed |

### Drop Configuration

```json
{
  "item_id": "LETTUCE",
  "min": 1,
  "max": 3,
  "chance": 1.0,
  "requires_fortune": false
}
```

| Property | Description |
|----------|-------------|
| `item_id` | Custom item or vanilla material ID |
| `min` | Minimum drop count |
| `max` | Maximum drop count |
| `chance` | Drop probability (0.0-1.0) |
| `requires_fortune` | Only drops with Fortune enchantment |

***

## Spreading (Vines)

Vine-type plants can spread automatically:

```json
{
  "spreading": {
    "enabled": true,
    "chance_per_check": 0.08,
    "direction": "UP",
    "max_chain_length": 4
  }
}
```

| Property | Description |
|----------|-------------|
| `enabled` | Allow spreading |
| `chance_per_check` | Probability per growth tick |
| `direction` | Spread direction (UP, DOWN, HORIZONTAL) |
| `max_chain_length` | Maximum connected plants |

***

## Textures

Crops use **Minecraft skin textures** for custom appearances:

```json
{
  "textures": {
    "growing": "http://textures.minecraft.net/texture/...",
    "ripe": "http://textures.minecraft.net/texture/..."
  }
}
```

{% hint style="info" %}
**Finding Textures:** Use sites like [Minecraft Heads](https://minecraft-heads.com/) to find texture URLs for custom crop appearances!
{% endhint %}

***

## What's Next?

{% content-ref url="../reference/commands.md" %}
[commands.md](../reference/commands.md)
{% endcontent-ref %}

Learn all the available commands!

