# 🔧 Creating Custom Recipes

This guide teaches you how to create your own recipes for Heirloom. Whether you want to add a simple snack or a complex multi-variant dish, you'll learn everything here!

***

## Getting Started

Recipes are defined in `plugins/Heirloom/recipes.json`. Each recipe is a JSON object in the `recipes` array.

### Minimal Recipe

Here's the simplest possible recipe:

```json
{
  "id": "MY_SNACK",
  "station": "CUTTING_BOARD",
  "output": "MY_SNACK",
  "processing_time": 0,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "item": "APPLE" }]
    }
  ],
  "actions": [],
  "rules": []
}
```

{% hint style="warning" %}
**Don't forget:** You also need to create the custom item `MY_SNACK` in `custom_items.json`!
{% endhint %}

***

## Recipe Structure

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier (UPPER_SNAKE_CASE) |
| `station` | string | Which cooking station processes this |
| `output` | string | Custom item ID for the result |
| `processing_time` | int | Ticks to cook (20 = 1 second) |
| `ingredients` | array | Input requirements |
| `actions` | array | Output modifications |
| `rules` | array | Conditional logic |

### Station Types

| Station | Value | Best For |
|---------|-------|----------|
| 🔥 Oven | `OVEN` | Baking, roasting |
| 🫕 Boiling Pot | `BOILING_POT` | Soups, boiling, deep-frying |
| 🥣 Mixing Bowl | `MIXING_BOWL` | Cold prep (instant) |
| 🔪 Cutting Board | `CUTTING_BOARD` | Slicing, assembly (instant) |
| 🍳 Frying Pan | `FRYING_PAN` | Pan-frying |

### Processing Time

```json
"processing_time": 100
```

- **0** = Instant (good for prep stations)
- **60** = 3 seconds (quick recipes)
- **100** = 5 seconds (standard)
- **200** = 10 seconds (complex dishes)

{% hint style="info" %}
**20 ticks = 1 second** in Minecraft time.
{% endhint %}

***

## Defining Ingredients

### Basic Format

```json
{
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [
        { "item": "VANILLA_ITEM" },
        { "custom_item": "CUSTOM_ITEM_ID" }
      ]
    }
  ]
}
```

### Ingredient Properties

| Property | Values | Description |
|----------|--------|-------------|
| `type` | `REQUIRED`, `OPTIONAL` | Must this ingredient be present? |
| `max` | int (1-64) | Maximum quantity accepted |
| `options` | array | List of acceptable items |

### Vanilla vs Custom Items

{% tabs %}
{% tab title="Vanilla Items" %}

Use Minecraft material names:

```json
{ "item": "WHEAT" }
{ "item": "APPLE" }
{ "item": "EGG" }
{ "item": "MILK_BUCKET" }
{ "item": "COOKED_BEEF" }
```

{% endtab %}

{% tab title="Custom Items" %}

Use your custom item IDs:

```json
{ "custom_item": "DOUGH" }
{ "custom_item": "CHEESE" }
{ "custom_item": "BACON" }
{ "custom_item": "BAG_OF_FLOUR" }
```

{% endtab %}
{% endtabs %}

### Multiple Options

Allow any of several items:

```json
{
  "type": "REQUIRED",
  "max": 1,
  "options": [
    { "item": "BEEF" },
    { "item": "PORKCHOP" },
    { "custom_item": "PLANT_PROTEIN" }
  ]
}
```

The player can use **any** of these to satisfy this ingredient slot.

### Quantity Limits

Allow multiple of an ingredient:

```json
{
  "type": "REQUIRED",
  "max": 3,
  "options": [{ "item": "EGG" }]
}
```

Player can add 1, 2, or 3 eggs.

### Optional Ingredients

Ingredients that enhance but aren't required:

```json
{
  "type": "OPTIONAL",
  "max": 4,
  "options": [
    { "custom_item": "BACON" },
    { "custom_item": "CHEESE" },
    { "item": "BROWN_MUSHROOM" }
  ]
}
```

***

## Example Recipes

### Simple Recipe

<details>

<summary>📋 Grilled Cheese Sandwich</summary>

```json
{
  "id": "GRILLED_CHEESE",
  "station": "FRYING_PAN",
  "output": "GRILLED_CHEESE",
  "processing_time": 100,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [
        { "custom_item": "BREAD" },
        { "item": "BREAD" }
      ]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "CHEESE" }]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "BUTTER" }]
    }
  ],
  "actions": [
    { "type": "SET_QUALITY", "value": "0.5" }
  ],
  "rules": []
}
```

</details>

### Recipe with Optional Ingredients

<details>

<summary>📋 Omelette with Fillings</summary>

```json
{
  "id": "OMELETTE",
  "station": "FRYING_PAN",
  "output": "OMELETTE",
  "processing_time": 80,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 3,
      "options": [{ "item": "EGG" }]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "BUTTER" }]
    },
    {
      "type": "OPTIONAL",
      "max": 1,
      "options": [{ "custom_item": "CHEESE" }]
    },
    {
      "type": "OPTIONAL",
      "max": 1,
      "options": [{ "custom_item": "BACON" }]
    },
    {
      "type": "OPTIONAL",
      "max": 1,
      "options": [{ "item": "BROWN_MUSHROOM" }]
    }
  ],
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Omelette" },
    { "type": "SET_QUALITY", "value": "0.4" }
  ],
  "rules": [
    {
      "trigger": "HAS_INPUT",
      "matcher": { "custom_item": "CHEESE" },
      "actions": [
        { "type": "SET_PROPERTY", "key": "NAME", "value": "§eCheese Omelette" },
        { "type": "ADD_QUALITY", "value": "0.1" }
      ]
    },
    {
      "trigger": "HAS_INPUT",
      "matcher": { "custom_item": "BACON" },
      "actions": [
        { "type": "SET_PROPERTY", "key": "NAME", "value": "§cBacon Omelette" },
        { "type": "ADD_QUALITY", "value": "0.1" }
      ]
    }
  ]
}
```

</details>

### Recipe Chain (Ingredient → Product → Final)

<details>

<summary>📋 Pizza from Scratch</summary>

**Step 1: Flour**

```json
{
  "id": "FLOUR",
  "station": "CUTTING_BOARD",
  "output": "BAG_OF_FLOUR",
  "processing_time": 0,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "item": "WHEAT" }]
    }
  ],
  "actions": [],
  "rules": []
}
```

**Step 2: Dough**

```json
{
  "id": "DOUGH",
  "station": "MIXING_BOWL",
  "output": "DOUGH",
  "processing_time": 0,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "BAG_OF_FLOUR" }]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "item": "WATER_BUCKET" }]
    }
  ],
  "actions": [
    { "type": "SET_RETURN_ITEM", "value": "BUCKET" }
  ],
  "rules": []
}
```

**Step 3: Pizza**

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
    }
  ],
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Pizza" }
  ],
  "rules": []
}
```

</details>

***

## Testing Your Recipe

1. **Save** your changes to `recipes.json`
2. **Validate** the JSON (use an online JSON validator)
3. **Reload** the plugin: `/hl reload`
4. **Check** the recipe browser: `/hl recipes`
5. **Test** at the cooking station

{% hint style="danger" %}
**JSON Errors:** If reload fails, check your JSON syntax! Common issues:
- Missing commas between objects
- Trailing commas at end of arrays
- Unclosed brackets
{% endhint %}

***

## What's Next?

{% content-ref url="recipe-rules.md" %}
[recipe-rules.md](recipe-rules.md)
{% endcontent-ref %}

Learn about dynamic recipe rules and actions for advanced customization!

