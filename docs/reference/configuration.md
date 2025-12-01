# ⚙️ Configuration

Heirloom uses JSON configuration files for all customization. This reference covers all available configuration options.

***

## Configuration Files

| File | Purpose |
|------|---------|
| `custom_items.json` | Custom food item definitions |
| `recipes.json` | Cooking recipe definitions |
| `crops.json` | Custom crop configurations |
| `dietary_properties.json` | Dietary labeling rules |

{% hint style="info" %}
**Location:** All configuration files are stored in `plugins/Heirloom/`
{% endhint %}

***

## custom_items.json

Defines all custom food items in the plugin.

### Structure

```json
{
  "custom_items": [
    {
      "id": "ITEM_ID",
      "name": "§eDisplay Name",
      "base_material": "PLAYER_HEAD",
      "texture": "http://textures.minecraft.net/texture/...",
      "edible": true,
      "food_value": 6,
      "saturation": 4.0
    }
  ]
}
```

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | ✅ | Unique identifier (UPPER_SNAKE_CASE) |
| `name` | string | ✅ | Display name with color codes |
| `base_material` | string | ✅ | Minecraft material for base item |
| `texture` | string | ❌ | Texture URL (for PLAYER_HEAD items) |
| `edible` | boolean | ✅ | Whether the item can be eaten |
| `food_value` | int | ❌ | Hunger points restored (requires edible) |
| `saturation` | float | ❌ | Saturation restored (requires edible) |

### Example Items

<details>

<summary>📋 Click to view example items</summary>

```json
{
  "custom_items": [
    {
      "id": "PIZZA",
      "name": "§cPizza",
      "base_material": "PLAYER_HEAD",
      "texture": "http://textures.minecraft.net/texture/d6fa7f4c43c1cb19a8046620d9f43b88cce7fc507eb843329c0fc6e66eac3e63",
      "edible": true,
      "food_value": 10,
      "saturation": 8.0
    },
    {
      "id": "DOUGH",
      "name": "§fDough",
      "base_material": "PLAYER_HEAD",
      "texture": "http://textures.minecraft.net/texture/8166d79de64abb4457ab87fa8f6706d55ce682e10db849ea6dd124095b12276e",
      "edible": false
    },
    {
      "id": "SALT",
      "name": "§fSalt",
      "base_material": "SUGAR",
      "edible": false
    }
  ]
}
```

</details>

***

## recipes.json

Defines all cooking recipes.

### Structure

```json
{
  "recipes": [
    {
      "id": "RECIPE_ID",
      "station": "STATION_TYPE",
      "output": "OUTPUT_ITEM_ID",
      "processing_time": 100,
      "ingredients": [...],
      "actions": [...],
      "rules": [...]
    }
  ]
}
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique recipe identifier |
| `station` | string | OVEN, BOILING_POT, MIXING_BOWL, CUTTING_BOARD, or FRYING_PAN |
| `output` | string | Custom item ID for result |
| `processing_time` | int | Cook time in ticks (20 = 1 second) |
| `ingredients` | array | Required and optional ingredients |
| `actions` | array | Output modifications |
| `rules` | array | Conditional modifications |

### Ingredient Format

```json
{
  "type": "REQUIRED",
  "max": 1,
  "options": [
    { "item": "WHEAT" },
    { "custom_item": "CORN" }
  ]
}
```

| Property | Values | Description |
|----------|--------|-------------|
| `type` | REQUIRED, OPTIONAL | Whether ingredient must be present |
| `max` | int | Maximum count of this ingredient |
| `options` | array | Accepted items (vanilla or custom) |

### Example Recipe

<details>

<summary>📋 Click to view example recipe</summary>

```json
{
  "id": "PIZZA",
  "station": "OVEN",
  "output": "PIZZA",
  "processing_time": 150,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "DOUGH" }]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "CHEESE" }]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "CANNED_TOMATOES" }]
    },
    {
      "type": "OPTIONAL",
      "max": 4,
      "options": [
        { "custom_item": "MINCED_MEAT" },
        { "custom_item": "BACON" },
        { "item": "BROWN_MUSHROOM" }
      ]
    }
  ],
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Pizza" },
    { "type": "SET_TEXTURE", "value": "http://textures..." },
    { "type": "SET_QUALITY", "value": "0.3" }
  ],
  "rules": [
    {
      "trigger": "HAS_INPUT",
      "matcher": { "custom_item": "MINCED_MEAT" },
      "actions": [
        { "type": "SET_PROPERTY", "key": "NAME", "value": "§cMeat Lovers Pizza" }
      ]
    }
  ]
}
```

</details>

***

## crops.json

Configures the farming system and custom crops.

### Global Settings

```json
{
  "settings": {
    "growth_check_radius": 32,
    "visual_update_interval_ticks": 40,
    "enable_particles": true,
    "enable_growth_sounds": true
  }
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `growth_check_radius` | 32 | Distance from player to check crops |
| `visual_update_interval_ticks` | 40 | How often to update visuals (2 sec) |
| `enable_particles` | true | Show growth particles |
| `enable_growth_sounds` | true | Play growth sounds |

### Plant Types

<details>

<summary>📋 Click to view plant types</summary>

```json
{
  "plant_types": {
    "SHORT_PLANT": {
      "description": "Small plants like lettuce",
      "block_material": "FERN",
      "display_offset_y": 0.5,
      "requires_water": false,
      "requires_wall": false,
      "can_spread": false
    },
    "TALL_PLANT": {
      "description": "Tall crops like corn",
      "block_material": "TALL_GRASS",
      "display_offset_y": 1.6,
      "requires_water": false,
      "requires_wall": false,
      "can_spread": false
    },
    "VINE": {
      "description": "Climbing plants like tomatoes",
      "block_material": "VINE",
      "display_offset_y": 0.5,
      "requires_water": false,
      "requires_wall": true,
      "can_spread": true
    },
    "AQUATIC": {
      "description": "Water plants like rice",
      "block_material": "SMALL_DRIPLEAF",
      "display_offset_y": 1.6,
      "requires_water": true,
      "requires_wall": false,
      "can_spread": false
    }
  }
}
```

</details>

### Crop Definition

<details>

<summary>📋 Click to view crop example</summary>

```json
{
  "crops": [
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
        "valid_blocks": ["GRASS_BLOCK", "DIRT", "COARSE_DIRT"],
        "consume_item": true
      },
      "textures": {
        "growing": "http://textures.minecraft.net/texture/...",
        "ripe": "http://textures.minecraft.net/texture/..."
      },
      "harvest": {
        "drops": [
          {"item_id": "LETTUCE", "min": 1, "max": 3, "chance": 1.0}
        ],
        "bonus_drops": [
          {"item_id": "LETTUCE", "min": 1, "max": 1, "chance": 0.15, "requires_fortune": true}
        ],
        "replant_after_harvest": true,
        "harvest_sound": "BLOCK_SWEET_BERRY_BUSH_PICK_BERRIES"
      }
    }
  ]
}
```

</details>

***

## dietary_properties.json

Configures dietary labeling for food items.

### Structure

```json
{
  "dietary_properties": {
    "PROPERTY_ID": {
      "display_name": "§aDisplay Name",
      "display_icon": "🌱",
      "description": "Human-readable description",
      "implies": ["OTHER_PROPERTY"],
      "violators": {
        "items": ["VANILLA_ITEM_1", "VANILLA_ITEM_2"],
        "custom_items": ["CUSTOM_ITEM_1"]
      }
    }
  },
  "hierarchy_rules": {
    "VEGAN": ["VEGETARIAN"]
  },
  "lore_settings": {
    "show_in_lore": true,
    "lore_format": "single_line",
    "prefix": "§7Diet: ",
    "separator": " ",
    "show_violations": false
  }
}
```

### Full Example

<details>

<summary>📋 Click to view full dietary config</summary>

```json
{
  "dietary_properties": {
    "VEGAN": {
      "display_name": "§aVegan",
      "display_icon": "🌱",
      "description": "Contains no animal products",
      "implies": ["VEGETARIAN"],
      "violators": {
        "items": [
          "EGG", "MILK_BUCKET",
          "BEEF", "COOKED_BEEF",
          "PORKCHOP", "COOKED_PORKCHOP",
          "CHICKEN", "COOKED_CHICKEN",
          "COD", "SALMON",
          "HONEY_BOTTLE"
        ],
        "custom_items": [
          "CHEESE", "BACON", "MINCED_MEAT",
          "HEAVY_CREAM", "FRIED_EGG"
        ]
      }
    },
    "VEGETARIAN": {
      "display_name": "§2Vegetarian",
      "display_icon": "🥬",
      "description": "Contains no meat or fish",
      "violators": {
        "items": [
          "BEEF", "COOKED_BEEF",
          "PORKCHOP", "COOKED_PORKCHOP",
          "CHICKEN", "COOKED_CHICKEN",
          "COD", "SALMON"
        ],
        "custom_items": ["BACON", "MINCED_MEAT"]
      }
    },
    "GLUTEN_FREE": {
      "display_name": "§bGluten-Free",
      "display_icon": "🌾",
      "description": "Contains no gluten",
      "violators": {
        "items": ["WHEAT", "BREAD", "COOKIE", "CAKE"],
        "custom_items": ["DOUGH", "BAG_OF_FLOUR", "BREAD"]
      }
    }
  },
  "hierarchy_rules": {
    "VEGAN": ["VEGETARIAN"]
  },
  "lore_settings": {
    "show_in_lore": true,
    "lore_format": "single_line",
    "prefix": "§7Diet: ",
    "separator": " ",
    "show_violations": false
  },
  "contains_settings": {
    "show_in_lore": true,
    "prefix": "§7Contains: ",
    "separator": ", "
  }
}
```

</details>

***

## Reloading Configuration

After making changes to any configuration file, reload them in-game:

```
/hl reload
```

{% hint style="warning" %}
**Validation:** Invalid JSON will cause the reload to fail. Use a JSON validator before saving!
{% endhint %}

***

## What's Next?

{% content-ref url="../advanced/custom-recipes.md" %}
[custom-recipes.md](../advanced/custom-recipes.md)
{% endcontent-ref %}

Learn how to create your own custom recipes!

