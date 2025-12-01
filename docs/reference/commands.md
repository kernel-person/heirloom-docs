# 💬 Commands

Heirloom provides a set of commands for browsing recipes, managing items, and administrating the plugin.

***

## Command Overview

| Command | Description | Permission |
|---------|-------------|------------|
| `/hl help` | Show help message | `heirloom.use` |
| `/hl cookbook` | Get a cookbook item | `heirloom.cookbook` |
| `/hl recipes` | Open recipe browser | `heirloom.recipes` |
| `/hl list <type>` | List items/recipes/dietary | `heirloom.use` |
| `/hl give <item> [amt]` | Give custom items | `heirloom.give` |
| `/hl reload` | Reload all configs | `heirloom.reload` |

{% hint style="info" %}
**Aliases:** All commands work with both `/heirloom` and `/hl`
{% endhint %}

***

## Player Commands

### `/hl help`

Displays the help menu with all available commands.

```
/hl help
```

**Output:**

```
═══════ Heirloom Commands ═══════
/hl cookbook - Get a free cookbook
/hl recipes - Browse all recipes
/hl list <items|recipes|dietary> - List things
/hl help - Show this help
```

{% hint style="success" %}
**Tip:** Operators see additional admin commands in the help output.
{% endhint %}

---

### `/hl cookbook`

Gives the player a **Heirloom Cookbook** item.

```
/hl cookbook
```

**Aliases:** `/hl book`

**Behavior:**
- Adds a Written Book item to your inventory
- Book has custom name "📖 Heirloom Cookbook"
- Right-clicking the book opens the recipe browser
- Only one cookbook per player (won't give duplicates)

**Response:**

```
✓ You received an Heirloom Cookbook!
Right-click the book or use /hl recipes to browse.
```

{% hint style="warning" %}
If you already have a cookbook, you'll see:
"You already have a cookbook! Use /hl recipes to browse."
{% endhint %}

---

### `/hl recipes`

Opens the interactive **Recipe Browser GUI**.

```
/hl recipes
```

**Aliases:** `/hl browse`

**GUI Features:**
- Browse recipes by cooking station
- Click recipes to see full details
- Click ingredients to see how to craft them
- Navigate with back/forward buttons
- Paginated lists for large recipe collections

---

### `/hl list <type>`

Lists available items, recipes, or dietary properties.

{% tabs %}
{% tab title="Items" %}

```
/hl list items
```

Lists all registered custom items with their IDs.

**Output:**

```
═══ Custom Items (50+) ═══
• DOUGH ✗
• CHEESE ✓
• PIZZA ✓
• BACON ✓
...
```

- ✓ = Edible item
- ✗ = Ingredient (not edible)

{% endtab %}

{% tab title="Recipes" %}

```
/hl list recipes
```

Shows recipe count and directs to the interactive browser.

**Output:**

```
═══ Recipes (60+) ═══
Use /hl recipes to browse interactively!
```

{% endtab %}

{% tab title="Dietary" %}

```
/hl list dietary
```

Lists all dietary properties with descriptions.

**Output:**

```
═══ Dietary Properties ═══
• §aVegan
  Contains no animal products
• §2Vegetarian
  Contains no meat or fish
• §bGluten-Free
  Contains no gluten
```

{% endtab %}
{% endtabs %}

***

## Admin Commands

{% hint style="warning" %}
**These commands require operator permissions!**
{% endhint %}

### `/hl give <item> [amount]`

Gives a custom food item to yourself.

```
/hl give PIZZA
/hl give BACON 16
/hl give BAG_OF_FLOUR 64
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `item` | ✅ | Custom item ID (case-insensitive) |
| `amount` | ❌ | Stack size (default: 1, max: 64) |

**Examples:**

```bash
# Give 1 pizza
/hl give pizza

# Give 32 cheese
/hl give CHEESE 32

# Give max stack of flour
/hl give bag_of_flour 64
```

**Invalid Item Response:**

```
Unknown item: INVALID_ITEM
Use /hl list items to see available items.
```

---

### `/hl reload`

Reloads all configuration files without restarting the server.

```
/hl reload
```

**What gets reloaded:**
- ✅ Custom items (`custom_items.json`)
- ✅ Dietary properties (`dietary_properties.json`)
- ✅ Recipes (`recipes.json`)
- ✅ Crops (`crops.json`)
- ✅ Recipe tracker index
- ✅ GUI cache (cleared)

**Response:**

```
✓ Heirloom reloaded successfully!
  • Custom items: 54
  • Dietary properties: 3
  • Recipes: 62
  • Crops: 4
```

{% hint style="danger" %}
**Active crops are preserved!** Reload doesn't affect currently growing crops, but changes to crop configs will apply to newly planted crops.
{% endhint %}

***

## Tab Completion

All commands support intelligent **tab completion**:

```
/hl <TAB>
→ cookbook, recipes, list, help, give, reload

/hl give <TAB>
→ DOUGH, CHEESE, PIZZA, BACON, HAMBURGER, ...

/hl give PIZZA <TAB>
→ 1, 16, 32, 64

/hl list <TAB>
→ items, recipes, dietary
```

***

## Console Usage

Most commands can be run from the server console, but some require a player:

| Command | Console Support |
|---------|-----------------|
| `/hl help` | ✅ Works |
| `/hl cookbook` | ❌ Player only |
| `/hl recipes` | ❌ Player only |
| `/hl list <type>` | ✅ Works |
| `/hl give <item>` | ❌ Player only |
| `/hl reload` | ✅ Works |

***

## What's Next?

{% content-ref url="permissions.md" %}
[permissions.md](permissions.md)
{% endcontent-ref %}

Learn about all available permissions!

