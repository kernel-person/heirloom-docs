# 🎨 Recipe Rules & Actions

Rules and actions are the secret sauce that makes Heirloom recipes dynamic! They allow recipes to change their output based on what ingredients are used.

***

## Overview

{% tabs %}
{% tab title="Actions" %}

**Actions** modify the output item directly:

```json
"actions": [
  { "type": "SET_PROPERTY", "key": "NAME", "value": "Pizza" },
  { "type": "SET_QUALITY", "value": "0.5" }
]
```

Actions always run when the recipe is crafted.

{% endtab %}

{% tab title="Rules" %}

**Rules** are conditional—they only apply when their trigger matches:

```json
"rules": [
  {
    "trigger": "HAS_INPUT",
    "matcher": { "custom_item": "BACON" },
    "actions": [
      { "type": "PREPEND_NAME", "value": "§cBacon " }
    ]
  }
]
```

This rule only triggers when bacon is added!

{% endtab %}
{% endtabs %}

***

## Action Types

### Name Actions

| Action | Description | Example |
|--------|-------------|---------|
| `SET_PROPERTY` | Set name directly | `"key": "NAME", "value": "Pizza"` |
| `PREPEND_NAME` | Add prefix to name | `"value": "§cBacon "` |
| `APPEND_NAME` | Add suffix to name | `"value": " (Spicy)"` |

**Examples:**

```json
// Set a new name
{ "type": "SET_PROPERTY", "key": "NAME", "value": "Cheese Pizza" }

// Add "Fresh " before existing name
{ "type": "PREPEND_NAME", "value": "§aFresh " }

// Add " (Mixed)" after existing name
{ "type": "APPEND_NAME", "value": " (Mixed)" }
```

{% hint style="info" %}
**Color Codes:** Use `§` color codes like `§c` (red), `§a` (green), `§e` (yellow), `§6` (gold), `§d` (pink).
{% endhint %}

---

### Quality Actions

| Action | Description | Example |
|--------|-------------|---------|
| `SET_QUALITY` | Set base quality | `"value": "0.5"` |
| `ADD_QUALITY` | Add to quality | `"value": "0.1"` |

**Quality Values:**

| Value | Stars | Effect |
|-------|-------|--------|
| 0.0-0.2 | ★ | Poor |
| 0.2-0.4 | ★★ | Standard |
| 0.4-0.6 | ★★★ | Good |
| 0.6-0.8 | ★★★★ | Great |
| 0.8-1.0 | ★★★★★ | Excellent |

**Examples:**

```json
// Set base quality to 50%
{ "type": "SET_QUALITY", "value": "0.5" }

// Add 10% quality for using premium ingredient
{ "type": "ADD_QUALITY", "value": "0.1" }
```

---

### Texture Actions

| Action | Description |
|--------|-------------|
| `SET_TEXTURE` | Change item texture |

```json
{ 
  "type": "SET_TEXTURE", 
  "value": "http://textures.minecraft.net/texture/abc123..." 
}
```

{% hint style="success" %}
**Pro Tip:** Find textures at [minecraft-heads.com](https://minecraft-heads.com/)!
{% endhint %}

---

### Return Item Actions

| Action | Description | Example |
|--------|-------------|---------|
| `SET_RETURN_ITEM` | Item returned after crafting | `"value": "BUCKET"` |
| `SET_CONSUME_RETURN` | Item returned when eating | `"value": "BOWL"` |

**Examples:**

```json
// Return bucket after using milk
{ "type": "SET_RETURN_ITEM", "value": "BUCKET" }

// Return glass bottle after eating jam
{ "type": "SET_CONSUME_RETURN", "value": "GLASS_BOTTLE" }

// Return bowl after eating soup
{ "type": "SET_CONSUME_RETURN", "value": "BOWL" }
```

---

### Metadata Actions

| Action | Description |
|--------|-------------|
| `SET_METADATA` | Set a metadata value |
| `ADD_METADATA` | Add to metadata list |
| `ADD_CONTAINS` | Add to "contains" list |

**Examples:**

```json
// Set a custom property
{ "type": "SET_METADATA", "key": "flavor", "value": "sweet" }

// Add a food property
{ "type": "ADD_METADATA", "key": "food_property", "value": "GLOWING" }

// Track ingredients
{ "type": "ADD_CONTAINS", "value": "EGG" }
{ "type": "ADD_CONTAINS", "value": "BUTTER" }
```

The "contains" list shows in item lore: `§7Contains: EGG, BUTTER`

***

## Rule Triggers

Rules only execute when their trigger condition is met.

### HAS_INPUT

Triggers when a specific item is present:

```json
{
  "trigger": "HAS_INPUT",
  "matcher": { "custom_item": "BACON" },
  "actions": [...]
}
```

**Matcher options:**

```json
{ "item": "APPLE" }           // Vanilla item
{ "custom_item": "CHEESE" }   // Custom item
```

---

### HAS_ANY_INGREDIENT

Triggers when ANY of several items is present:

```json
{
  "trigger": "HAS_ANY_INGREDIENT",
  "matchers": [
    { "item": "BROWN_MUSHROOM" },
    { "item": "RED_MUSHROOM" }
  ],
  "actions": [...]
}
```

---

### HAS_ALL_INGREDIENTS

Triggers only when ALL items are present:

```json
{
  "trigger": "HAS_ALL_INGREDIENTS",
  "matchers": [
    { "custom_item": "BACON" },
    { "custom_item": "LETTUCE" }
  ],
  "actions": [...]
}
```

**With alternatives:**

```json
{
  "trigger": "HAS_ALL_INGREDIENTS",
  "matchers": [
    { "options": [{ "item": "POTATO" }, { "item": "BAKED_POTATO" }] },
    { "custom_item": "HEAVY_CREAM" }
  ],
  "actions": [...]
}
```

This triggers if (potato OR baked potato) AND heavy cream are present.

---

### HAS_INGREDIENT_PROPERTY

Triggers based on properties carried from ingredients:

```json
{
  "trigger": "HAS_INGREDIENT_PROPERTY",
  "property": "YEAST",
  "actions": [...]
}
```

{% hint style="info" %}
**Example:** If dough was made with yeast (brown mushroom), pizzas using that dough can detect `YEAST` property!
{% endhint %}

---

### HAS_ALL_INGREDIENT_PROPERTIES

Triggers when multiple properties are present:

```json
{
  "trigger": "HAS_ALL_INGREDIENT_PROPERTIES",
  "properties": ["BUTTER", "EGG", "SUGAR"],
  "actions": [...]
}
```

---

### INPUT_COUNT_GTE

Triggers when ingredient count is at least N:

```json
{
  "trigger": "INPUT_COUNT_GTE",
  "slot_index": 0,
  "count": 2,
  "actions": [...]
}
```

`slot_index` refers to the ingredient array index (0 = first ingredient).

**Example use case:**

```json
// If 2+ eggs are used, make "Fried Eggs" plural
{
  "trigger": "INPUT_COUNT_GTE",
  "slot_index": 0,
  "count": 2,
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Fried Eggs" }
  ]
}
```

***

## Rule Execution Order

Rules are processed in array order. Later rules can override earlier ones!

```json
"rules": [
  // Rule 1: Base variant
  {
    "trigger": "HAS_INPUT",
    "matcher": { "custom_item": "CHEESE" },
    "actions": [{ "type": "SET_PROPERTY", "key": "NAME", "value": "§eCheese Pizza" }]
  },
  // Rule 2: Overrides if both present
  {
    "trigger": "HAS_ALL_INGREDIENTS",
    "matchers": [
      { "custom_item": "CHEESE" },
      { "custom_item": "BACON" }
    ],
    "actions": [{ "type": "SET_PROPERTY", "key": "NAME", "value": "§6Ultimate Pizza" }]
  }
]
```

If only cheese → "Cheese Pizza"
If cheese AND bacon → "Ultimate Pizza" (rule 2 overrides)

***

## Complete Examples

### Multi-Variant Jam Recipe

<details>

<summary>📋 Click to expand</summary>

```json
{
  "id": "JAM",
  "station": "BOILING_POT",
  "output": "JAM",
  "processing_time": 150,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 3,
      "options": [
        { "item": "SWEET_BERRIES" },
        { "item": "GLOW_BERRIES" },
        { "item": "APPLE" },
        { "item": "MELON_SLICE" }
      ]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "item": "SUGAR" }]
    },
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "item": "GLASS_BOTTLE" }]
    }
  ],
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Jam" },
    { "type": "SET_CONSUME_RETURN", "value": "GLASS_BOTTLE" }
  ],
  "rules": [
    {
      "trigger": "HAS_INPUT",
      "matcher": { "item": "APPLE" },
      "actions": [
        { "type": "PREPEND_NAME", "value": "§aApple " }
      ]
    },
    {
      "trigger": "HAS_INPUT",
      "matcher": { "item": "SWEET_BERRIES" },
      "actions": [
        { "type": "PREPEND_NAME", "value": "§cBerry " }
      ]
    },
    {
      "trigger": "HAS_INPUT",
      "matcher": { "item": "GLOW_BERRIES" },
      "actions": [
        { "type": "PREPEND_NAME", "value": "§eGlow " },
        { "type": "ADD_METADATA", "key": "food_property", "value": "GLOWING" }
      ]
    },
    {
      "trigger": "HAS_INPUT",
      "matcher": { "item": "MELON_SLICE" },
      "actions": [
        { "type": "PREPEND_NAME", "value": "§aMelon " }
      ]
    },
    {
      "trigger": "INPUT_COUNT_GTE",
      "slot_index": 0,
      "count": 2,
      "actions": [
        { "type": "APPEND_NAME", "value": " (Mixed)" }
      ]
    }
  ]
}
```

**Possible outputs:**
- Berry Jam
- Apple Jam
- Glow Jam (with glowing effect!)
- Melon Jam
- Berry Jam (Mixed)
- Apple Jam (Mixed)
- etc.

</details>

### Quality-Based Bread

<details>

<summary>📋 Click to expand</summary>

```json
{
  "id": "BREAD",
  "station": "OVEN",
  "output": "BREAD",
  "processing_time": 120,
  "ingredients": [
    {
      "type": "REQUIRED",
      "max": 1,
      "options": [{ "custom_item": "DOUGH" }]
    }
  ],
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Bread" },
    { "type": "SET_QUALITY", "value": "0.3" }
  ],
  "rules": [
    {
      "trigger": "HAS_INGREDIENT_PROPERTY",
      "property": "BUTTER",
      "actions": [
        { "type": "ADD_CONTAINS", "value": "BUTTER" },
        { "type": "ADD_QUALITY", "value": "0.1" }
      ]
    },
    {
      "trigger": "HAS_INGREDIENT_PROPERTY",
      "property": "EGG",
      "actions": [
        { "type": "ADD_CONTAINS", "value": "EGG" },
        { "type": "ADD_QUALITY", "value": "0.1" }
      ]
    },
    {
      "trigger": "HAS_INGREDIENT_PROPERTY",
      "property": "SUGAR",
      "actions": [
        { "type": "ADD_CONTAINS", "value": "SUGAR" },
        { "type": "ADD_QUALITY", "value": "0.1" }
      ]
    },
    {
      "trigger": "HAS_INGREDIENT_PROPERTY",
      "property": "YEAST",
      "actions": [
        { "type": "ADD_CONTAINS", "value": "YEAST" },
        { "type": "ADD_QUALITY", "value": "0.1" }
      ]
    },
    {
      "trigger": "HAS_ALL_INGREDIENT_PROPERTIES",
      "properties": ["BUTTER", "EGG", "SUGAR"],
      "actions": [
        { "type": "SET_PROPERTY", "key": "NAME", "value": "§6Brioche Bread" },
        { "type": "ADD_QUALITY", "value": "0.1" }
      ]
    }
  ]
}
```

**Quality progression:**
- Basic dough → 0.3 (★★)
- + Butter → 0.4 (★★)
- + Egg → 0.5 (★★★)
- + Sugar → 0.6 (★★★★)
- + Yeast → 0.7 (★★★★)
- Brioche (all three) → 0.8 (★★★★★)

</details>

***

## Tips & Best Practices

{% hint style="success" %}
**Rule Order Matters:** Put more specific rules AFTER general ones so they can override.
{% endhint %}

{% hint style="success" %}
**Test Incrementally:** Add one rule at a time and test with `/hl reload`.
{% endhint %}

{% hint style="success" %}
**Use Contains:** Track ingredients with `ADD_CONTAINS` to show players what's in their food.
{% endhint %}

{% hint style="warning" %}
**Quality Caps:** Quality is clamped between 0.0 and 1.0. Adding more doesn't help beyond 1.0.
{% endhint %}

***

*Happy cooking! 🍳*

