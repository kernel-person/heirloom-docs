# Items & FoodFacts V2

Heirloom provides item factory/identification helpers on `HeirloomAPI`, immutable `FoodFactsV2` evidence for ingredient lineage and dietary truth, and shared beverage/alcohol metadata helpers under `ke.ric.api.item`.

## Custom Item Lookups & Creation

All item helpers live on [`HeirloomAPI`](https://heirloom-maven.pages.dev/javadoc/ke/ric/api/HeirloomAPI.html):

| Method | Return | Behaviour |
| --- | --- | --- |
| `api.createItem(String itemId)` | `ItemStack` | Creates one custom item stack, or returns `null` if `itemId` is unknown. |
| `api.createItem(String itemId, int amount)` | `ItemStack` | Creates a custom item stack with the given amount, or returns `null` if unknown. |
| `api.isCustomItem(ItemStack item)` | `boolean` | Returns `true` if the stack carries a registered Heirloom custom item identity. |
| `api.getCustomItemId(ItemStack item)` | `String` | Returns the custom item ID (e.g. `"TOMATO_SOUP"`), or `null` for non-Heirloom items. |

```java
HeirloomAPI api = HeirloomAPI.getInstance();
if (api != null && api.isReady()) {
    ItemStack soup = api.createItem("TOMATO_SOUP");
    if (api.isCustomItem(heldItem)) {
        String customId = api.getCustomItemId(heldItem);
        getLogger().info("Player holds Heirloom item: " + customId);
    }
}
```

## Reading Dietary Evidence (`FoodFactsV2`)

Prefer `api.foodFactsV2(item)` (or `FoodFactsV2.read(item)`) for dietary checks. It inspects an `ItemStack` read-only and never reconstructs missing recipe history or mutates the item.

```java
import ke.ric.api.HeirloomAPI;
import ke.ric.api.food.FoodFactsV2;

FoodFactsV2 facts = HeirloomAPI.getInstance().foodFactsV2(itemStack);

// Access dietary truth conservatively via the map (absent keys mean UNKNOWN)
FoodFactsV2.Truth vegan = facts.dietaryFacts()
        .getOrDefault("VEGAN", FoodFactsV2.Truth.UNKNOWN);

if (vegan == FoodFactsV2.Truth.FALSE || facts.categories().contains("PORK")) {
    // Confirmed non-vegan or contains pork
} else if (vegan == FoodFactsV2.Truth.TRUE && facts.categoriesComplete()) {
    // Confirmed vegan with complete category classification
}
```

### `FoodFactsV2` Record Components

`ke.ric.api.food.FoodFactsV2` is an immutable Java record with seven accessors:

| Accessor | Type | Meaning |
| --- | --- | --- |
| `itemId()` | `String` | Source-qualified logical identity (`heirloom:<id>`, `minecraft:<material>`, or `<provider>:<item>`), or `null` for empty/air items. |
| `ingredientIds()` | `Set<String>` | Immutable sorted set of observed source-qualified ingredient IDs (flattened across crafted steps). |
| `categories()` | `Set<String>` | Immutable sorted set of uppercase dietary categories (see standard categories below). |
| `tags()` | `Set<String>` | Immutable sorted set of normalized uppercase custom tags. |
| `dietaryFacts()` | `Map<String, FoodFactsV2.Truth>` | Map of dietary flag keys to `TRUE`, `FALSE`, or `UNKNOWN`. An absent key also means `UNKNOWN`. |
| `complete()` | `boolean` | `true` when every contributing ingredient lineage is known. |
| `categoriesComplete()` | `boolean` | `true` when every known ingredient's category classification is complete (independent of `complete()`). |

### Tri-State Truth (`TRUE` / `FALSE` / `UNKNOWN`)

Heirloom uses three-valued logic (`FoodFactsV2.Truth`) so custom or unknown items never falsely claim to be safe:

- **`Truth.TRUE`** — Established from complete supported source evidence or an explicit producer certification with no contradicting adverse evidence.
- **`Truth.FALSE`** — An ingredient or classification explicitly violates the property (adverse evidence survives unknown ingredients).
- **`Truth.UNKNOWN`** — Evidence is incomplete or absent (for example an opaque third-party item or legacy stack without V2 lineage). Treat missing keys in `dietaryFacts()` identically to `Truth.UNKNOWN`.

### Built-In Dietary Flags & Standard Categories

Check these uppercase keys in `facts.dietaryFacts()` and uppercase elements in `facts.categories()`:

- **Built-in `dietaryFacts()` keys:** `PORK_FREE`, `BEEF_FREE`, `MEAT_FREE`, `VEGETARIAN`, `VEGAN`, `PESCATARIAN`, `ALCOHOL_FREE`, `GLUTEN_FREE`
- **Standard `categories()` values:** `PLANT`, `ANIMAL`, `PORK`, `BEEF`, `MEAT`, `FISH`, `DAIRY`, `EGG`, `HONEY`, `GLUTEN`, `ALCOHOL`, `MINERAL`, `WATER`

!!! note "Legacy V1 API"
    `api.foodFacts(ItemStack)` returns the legacy V1 `ke.ric.api.food.FoodFacts` record (`itemId`, `ingredientIds`, `categories`, `tags`, `dietaryFacts`, `complete`). Keep V1 only for backwards compatibility; use `FoodFactsV2` for new integrations.

## Propagating Lineage on Custom Station Outputs

If your plugin crafts or transforms food stacks using actual consumed input items, record the production boundary right where the real input `ItemStack`s are still available:

```java
// Read inputs before mutating output (supports in-place stack updates)
FoodFactsV2.writeProduced(outputStack, actualConsumedInputs, "myaddon:spiced_stew");
```

- The third argument is a source-qualified fallback output ID used only when `outputStack` has no actual custom owner.
- Include unknown/`null` input entries instead of omitting them so `complete()` stays honest.
- When merging snapshots in memory without direct stack mutation, call `FoodFactsV2.produced(resultFacts, inputFacts)` and apply the returned record via `FoodFactsV2.write(outputStack, merged)`.
- For identity-preserving refreshes (updating lore/visuals without consuming new ingredients), copy evidence directly instead of calling `FoodFactsV2.produced(...)`:

```java
FoodFactsV2.write(refreshedItem, FoodFactsV2.read(originalItem));
```

## Zero-Dependency PDC JSON Schema (`heirloom:food_facts_v2`)

External plugins that do not depend on `heirloom-api` at compile time (or support older Heirloom jars) can read the `PersistentDataContainer` key `heirloom:food_facts_v2` as `PersistentDataType.STRING`:

```json
{
  "version": 2,
  "itemId": "heirloom:vegetable_pie",
  "ingredientIds": ["heirloom:dough", "minecraft:carrot", "minecraft:wheat"],
  "categories": ["GLUTEN", "PLANT"],
  "tags": [],
  "dietaryFacts": {
    "GLUTEN_FREE": "FALSE",
    "VEGAN": "TRUE"
  },
  "complete": true,
  "categoriesComplete": true
}
```

- Only consume a payload whose integer `"version"` equals `2`.
- Always check actual alcohol evidence if present: positive actual ABV metadata always implies `ALCOHOL` and `ALCOHOL_FREE = FALSE`.

## Beverage, Quality & Tooltip Utilities (`ke.ric.api.item`)

The `ke.ric.api.item` package exposes shared helpers for drinks and generated lore without depending on Distillery internals:

| Class | Key Methods | Purpose |
| --- | --- | --- |
| `DrinkQuality` | `level(ItemStack)` / `level(ItemStack, int fallback)` | Read Heirloom item quality consistently across food and drink items. |
| `TerminalAlcohol` | `read(ItemStack)` / `isMarked(ItemStack)` / `write(ItemStack)` | Read or stamp terminal mixed-drink ABV, quality, and integration state (`record TerminalAlcohol(double abv, int quality, boolean integrated)`). |
| `DrinkServing` | `read(ItemStack)` / `write(ItemStack, double)` / `equivalentCl(double abv, double volumeCl)` / `DEFAULT_CL` (`4.0`) / `REFERENCE_ABV` (`40.0`) | Standardize drink serving volume and inebriation scaling. |
| `AlcoholLore` | `estimate(abv, servingCl)` / `range(minAbv, maxAbv, servingCl)` / `apply(...)` / `refresh(ItemStack)` | Render standardized alcohol lore and catalog preview lines. |
| `PotionTooltip` | `hideEmptyEffectTooltip(ItemStack)` / `hideEffectTooltip(ItemStack)` | Hide vanilla empty `"No Effects"` rows on custom potion-based items. |
