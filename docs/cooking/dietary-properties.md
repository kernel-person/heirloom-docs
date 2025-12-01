# 🍽️ Dietary Properties

Heirloom automatically labels food items with **dietary properties**, making it easy for players to identify foods that match their dietary preferences or roleplay needs!

***

## Overview

Every food item in Heirloom is analyzed for dietary compliance:

| Property | Icon | Meaning |
|----------|------|---------|
| 🌱 **Vegan** | `§aVegan` | Contains no animal products |
| 🥬 **Vegetarian** | `§2Vegetarian` | Contains no meat or fish |
| 🌾 **Gluten-Free** | `§bGluten-Free` | Contains no wheat or gluten |

{% hint style="info" %}
**Automatic Detection:** Dietary properties are calculated automatically based on ingredients used. No manual tagging required!
{% endhint %}

***

## How It Works

### Property Detection

When you craft a food item, Heirloom analyzes all ingredients and checks against a list of **violators** for each dietary property.

```
┌─────────────────────────────────────────────┐
│   Making: Garden Salad                       │
│   Ingredients: Lettuce, Tomato, Carrot      │
├─────────────────────────────────────────────┤
│   ✓ No meat/fish         → Vegetarian       │
│   ✓ No animal products   → Vegan            │
│   ✓ No wheat/flour       → Gluten-Free      │
├─────────────────────────────────────────────┤
│   Result: 🌱 Vegan  🥬 Vegetarian  🌾 GF    │
└─────────────────────────────────────────────┘
```

### Property Hierarchy

Some properties imply others:

{% hint style="success" %}
**Vegan implies Vegetarian:** If a food is vegan, it's automatically also vegetarian!
{% endhint %}

```
Vegan → Vegetarian
  │
  └── A vegan item automatically gets the vegetarian label too
```

***

## Dietary Labels

### 🌱 Vegan

Foods containing **no animal products whatsoever**.

**Violating ingredients:**

{% tabs %}
{% tab title="Vanilla Items" %}

- Eggs
- Milk Bucket
- All raw/cooked meats (Beef, Porkchop, Chicken, Mutton, Rabbit)
- All fish (Cod, Salmon, Tropical Fish, Pufferfish)
- Rabbit Stew
- Honey Bottle, Honeycomb

{% endtab %}

{% tab title="Custom Items" %}

- Cheese
- Bacon
- Minced Meat
- Heavy Cream
- Fried Egg

{% endtab %}
{% endtabs %}

**Example Vegan Foods:**
- Garden Salad (with vinegar dressing)
- Plain Dough (no egg)
- Flatbread (no butter dough)
- Fries (with oil)
- Plant Protein
- Most Jams

### 🥬 Vegetarian

Foods containing **no meat or fish** (but may contain eggs, dairy, honey).

**Violating ingredients:**

- All raw/cooked meats (Beef, Porkchop, Chicken, Mutton, Rabbit)
- All fish (Cod, Salmon, Tropical Fish, Pufferfish)
- Bacon
- Minced Meat
- Rabbit Stew

**Example Vegetarian Foods:**
- Cheese (✓ vegetarian, ✗ vegan)
- Omelette
- Mac & Cheese
- Waffles
- Pancakes
- Ice Cream

### 🌾 Gluten-Free

Foods containing **no wheat or gluten-containing ingredients**.

**Violating ingredients:**

{% tabs %}
{% tab title="Vanilla Items" %}

- Wheat
- Wheat Seeds
- Bread
- Cookie
- Cake
- Pumpkin Pie

{% endtab %}

{% tab title="Custom Items" %}

- Dough
- Bag of Flour
- Bread (custom)

{% endtab %}
{% endtabs %}

**Example Gluten-Free Foods:**
- Fried Rice (uses rice, not wheat)
- Sushi
- Bacon
- Fried Eggs
- Cheese
- Salads (without croutons)

***

## Display in Game

### Item Lore

Dietary properties appear in the item's lore (tooltip):

```
┌──────────────────────────────┐
│  🧀 Cheese                   │
│  ────────────────────────    │
│  Food: 🍗🍗🍗                │
│  Saturation: ⭐⭐             │
│                              │
│  §7Diet: §2Vegetarian 🌾     │
└──────────────────────────────┘
```

### Configuration

The lore format is configurable in `dietary_properties.json`:

```json
{
  "lore_settings": {
    "show_in_lore": true,
    "lore_format": "single_line",
    "prefix": "§7Diet: ",
    "separator": " ",
    "show_violations": false
  }
}
```

{% hint style="info" %}
**Show Violations:** Set `show_violations` to `true` to display why a food *doesn't* qualify for certain diets (useful for debugging).
{% endhint %}

***

## Practical Examples

### Making a Vegan Pizza

Standard pizza isn't vegan (contains cheese). Here's how to work around it:

1. Make **Plant Protein** instead of cheese
2. Use **Dough** without egg
3. Add **Canned Tomatoes** and vegetables

{% hint style="warning" %}
**Note:** The current recipe system doesn't support substituting cheese with plant protein for pizza. Consider this a feature request for a future "Vegan Pizza" recipe!
{% endhint %}

### Vegetarian Alternatives

| Regular Dish | Vegetarian Version |
|--------------|-------------------|
| Hamburger | Plant Burger (use Plant Protein) |
| BLT | Veggie BLT (use Plant Protein) |
| Pasta Bolognese | Veggie Bolognese (use Plant Protein) |
| Taco | Veggie Taco (use Plant Protein) |

***

## Contains System

In addition to dietary properties, foods can display what they **contain**:

```json
{
  "contains_settings": {
    "show_in_lore": true,
    "prefix": "§7Contains: ",
    "separator": ", "
  }
}
```

This shows ingredients that were added during preparation:

```
┌──────────────────────────────┐
│  🍞 Brioche Bread            │
│  ────────────────────────    │
│  §7Contains: EGG, BUTTER,    │
│              SUGAR, YEAST    │
│  §7Diet: §2Vegetarian        │
└──────────────────────────────┘
```

***

## Creating Custom Dietary Properties

Want to add your own dietary labels? It's easy! Edit `dietary_properties.json` and add new property definitions.

### Basic Structure

```json
{
  "dietary_properties": {
    "YOUR_PROPERTY_ID": {
      "display_name": "§xDisplay Name",
      "display_icon": "🔖",
      "description": "Human-readable description",
      "implies": [],
      "violators": {
        "items": ["VANILLA_ITEM_1", "VANILLA_ITEM_2"],
        "custom_items": ["CUSTOM_ITEM_1", "CUSTOM_ITEM_2"]
      }
    }
  }
}
```

### Property Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `display_name` | Colored name shown in lore | `§9Dairy-Free` |
| `display_icon` | Emoji for visual flair | `🥛` |
| `description` | Tooltip explanation | `Contains no dairy products` |
| `implies` | Other properties this grants | `["LACTOSE_FREE"]` |
| `violators.items` | Vanilla items that break this diet | `["MILK_BUCKET"]` |
| `violators.custom_items` | Custom items that break this diet | `["CHEESE", "BUTTER"]` |

***

## Example: Dairy-Free

<details>

<summary>📋 Click to view Dairy-Free configuration</summary>

```json
{
  "DAIRY_FREE": {
    "display_name": "§9Dairy-Free",
    "display_icon": "🥛",
    "description": "Contains no dairy products",
    "implies": ["LACTOSE_FREE"],
    "violators": {
      "items": [
        "MILK_BUCKET"
      ],
      "custom_items": [
        "CHEESE",
        "BUTTER",
        "HEAVY_CREAM",
        "ICE_CREAM"
      ]
    }
  }
}
```

</details>

**What it does:**
- ❌ Items with milk, cheese, butter, or cream lose this label
- ✅ Most plant-based foods will qualify
- 🔗 Also grants "Lactose-Free" if you define that property

**Foods that would qualify:**
- Fried Rice (no butter)
- Salads (no cream dressing)
- Pasta Bolognese (tomato-based)
- Most jams and fruits

***

## Example: Kosher

<details>

<summary>📋 Click to view Kosher configuration</summary>

```json
{
  "KOSHER": {
    "display_name": "§fKosher",
    "display_icon": "✡️",
    "description": "Follows kosher dietary laws",
    "implies": [],
    "violators": {
      "items": [
        "PORKCHOP",
        "COOKED_PORKCHOP",
        "RABBIT",
        "COOKED_RABBIT",
        "RABBIT_STEW",
        "PUFFERFISH",
        "TROPICAL_FISH"
      ],
      "custom_items": [
        "BACON",
        "MINCED_MEAT"
      ]
    }
  }
}
```

</details>

**What it does:**
- ❌ Pork products (porkchop, bacon) are not kosher
- ❌ Rabbit is not kosher
- ❌ Shellfish/certain fish (represented by pufferfish, tropical fish)
- ✅ Beef, chicken, salmon, and cod are kosher

{% hint style="warning" %}
**Note:** True kosher laws are complex (meat/dairy separation, preparation methods). This simplified version only checks ingredients, not preparation context.
{% endhint %}

***

## Example: Halal

<details>

<summary>📋 Click to view Halal configuration</summary>

```json
{
  "HALAL": {
    "display_name": "§2Halal",
    "display_icon": "☪️",
    "description": "Permissible under Islamic dietary laws",
    "implies": [],
    "violators": {
      "items": [
        "PORKCHOP",
        "COOKED_PORKCHOP",
        "ROTTEN_FLESH",
        "SPIDER_EYE"
      ],
      "custom_items": [
        "BACON",
        "MINCED_MEAT"
      ]
    }
  }
}
```

</details>

**What it does:**
- ❌ Pork products forbidden
- ❌ Carrion/rotten items forbidden
- ✅ Most other meats permissible (in simplified form)

{% hint style="info" %}
**Minced Meat Note:** Since Heirloom's minced meat can be made from pork, it's listed as a violator. Consider creating separate `MINCED_BEEF` and `MINCED_PORK` items for more accurate dietary tracking!
{% endhint %}

***

## Example: Nut-Free (Allergy)

<details>

<summary>📋 Click to view Nut-Free configuration</summary>

```json
{
  "NUT_FREE": {
    "display_name": "§eNut-Free",
    "display_icon": "🥜",
    "description": "Contains no tree nuts or peanuts",
    "implies": [],
    "violators": {
      "items": [],
      "custom_items": [
        "PEANUT_BUTTER",
        "ALMOND_MILK",
        "WALNUT",
        "CASHEW"
      ]
    }
  }
}
```

</details>

{% hint style="success" %}
**Pro Tip:** Vanilla Minecraft has no nut items, so this property would only matter if you add custom nut items to your server!
{% endhint %}

***

## Example: Low-Carb / Keto

<details>

<summary>📋 Click to view Low-Carb configuration</summary>

```json
{
  "LOW_CARB": {
    "display_name": "§dLow-Carb",
    "display_icon": "🥩",
    "description": "Low in carbohydrates",
    "implies": [],
    "violators": {
      "items": [
        "BREAD",
        "WHEAT",
        "POTATO",
        "BAKED_POTATO",
        "COOKIE",
        "CAKE",
        "PUMPKIN_PIE",
        "APPLE",
        "MELON_SLICE",
        "SUGAR"
      ],
      "custom_items": [
        "DOUGH",
        "BAG_OF_FLOUR",
        "BREAD",
        "FLATBREAD",
        "DRY_PASTA",
        "PASTA_BOLOGNESE",
        "RICE",
        "COOKED_RICE",
        "FRIED_RICE",
        "PIZZA",
        "PANCAKES",
        "WAFFLES",
        "DOUGHNUT",
        "FRIES",
        "JAM",
        "ICE_CREAM"
      ]
    }
  }
}
```

</details>

**Foods that would qualify:**
- Bacon & Eggs
- Cheese
- Omelette (no toast!)
- Salads (no croutons)
- Grilled meats

***

## Combining Properties with Hierarchy

Use `implies` to create property relationships:

```json
{
  "VEGAN": {
    "display_name": "§aVegan",
    "implies": ["VEGETARIAN", "DAIRY_FREE", "EGG_FREE"],
    "violators": { ... }
  },
  "VEGETARIAN": {
    "display_name": "§2Vegetarian", 
    "implies": [],
    "violators": { ... }
  }
}
```

And in `hierarchy_rules`:

```json
{
  "hierarchy_rules": {
    "VEGAN": ["VEGETARIAN", "DAIRY_FREE", "EGG_FREE"]
  }
}
```

This means:
- 🌱 A vegan item automatically gets Vegetarian, Dairy-Free, AND Egg-Free labels
- No need to pass all checks individually

***

## Complete Custom Configuration

<details>

<summary>📋 Click to view full dietary_properties.json with custom properties</summary>

```json
{
  "dietary_properties": {
    "VEGAN": {
      "display_name": "§aVegan",
      "display_icon": "🌱",
      "description": "Contains no animal products",
      "implies": ["VEGETARIAN", "DAIRY_FREE"],
      "violators": {
        "items": ["EGG", "MILK_BUCKET", "BEEF", "COOKED_BEEF", "PORKCHOP", "COOKED_PORKCHOP", "CHICKEN", "COOKED_CHICKEN", "COD", "SALMON", "HONEY_BOTTLE"],
        "custom_items": ["CHEESE", "BACON", "MINCED_MEAT", "HEAVY_CREAM", "FRIED_EGG", "BUTTER"]
      }
    },
    "VEGETARIAN": {
      "display_name": "§2Vegetarian",
      "display_icon": "🥬",
      "description": "Contains no meat or fish",
      "violators": {
        "items": ["BEEF", "COOKED_BEEF", "PORKCHOP", "COOKED_PORKCHOP", "CHICKEN", "COOKED_CHICKEN", "COD", "SALMON"],
        "custom_items": ["BACON", "MINCED_MEAT"]
      }
    },
    "GLUTEN_FREE": {
      "display_name": "§bGluten-Free",
      "display_icon": "🌾",
      "description": "Contains no gluten",
      "violators": {
        "items": ["WHEAT", "BREAD", "COOKIE", "CAKE"],
        "custom_items": ["DOUGH", "BAG_OF_FLOUR", "BREAD", "DRY_PASTA"]
      }
    },
    "DAIRY_FREE": {
      "display_name": "§9Dairy-Free",
      "display_icon": "🥛",
      "description": "Contains no dairy products",
      "violators": {
        "items": ["MILK_BUCKET"],
        "custom_items": ["CHEESE", "BUTTER", "HEAVY_CREAM", "ICE_CREAM"]
      }
    },
    "KOSHER": {
      "display_name": "§fKosher",
      "display_icon": "✡️",
      "description": "Follows kosher dietary laws",
      "violators": {
        "items": ["PORKCHOP", "COOKED_PORKCHOP", "RABBIT", "COOKED_RABBIT", "PUFFERFISH"],
        "custom_items": ["BACON"]
      }
    },
    "HALAL": {
      "display_name": "§2Halal",
      "display_icon": "☪️",
      "description": "Permissible under Islamic dietary laws",
      "violators": {
        "items": ["PORKCHOP", "COOKED_PORKCHOP", "ROTTEN_FLESH"],
        "custom_items": ["BACON"]
      }
    }
  },
  "hierarchy_rules": {
    "VEGAN": ["VEGETARIAN", "DAIRY_FREE"]
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

After editing, reload with `/hl reload` to apply your new dietary properties!

***

## What's Next?

{% content-ref url="../gardening/farming.md" %}
[farming.md](../gardening/farming.md)
{% endcontent-ref %}

Learn about growing your own ingredients!

