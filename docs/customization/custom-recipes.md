# Custom Recipes

Recipes define a station, output, processing time, ingredients, actions, and optional rules. The output can be changed by base actions, rule actions, inherited input metadata, and quality logic.

## Qualified ingredients

An ingredient may refine a canonical custom identity with an addon-owned qualifier, for example `{"custom_item":"DISTILLERY_WINE","qualifier":"distillery:sparkling_wine"}`. The addon registers its metadata predicate and cosmetic preview through `api.items().registerIngredientQualifier(addonId, qualifierId, canonicalCustomItemId, matches, preview)`. The owning addon and its item must be active. Matching checks the canonical identity first, then validates the original item's metadata. Missing registrations, missing originals and predicate failures do not match.

Recipes without a qualifier retain their normal meaning: ordinary Wine recipes also accept valid Sparkling Wine. A qualifier cannot be attached to vanilla items, provider items or tags. Rule matchers use `options` containing the qualified ingredient. Unavailable required qualifiers disable their recipe unless another alternative remains usable. Safe previews preserve appearance and tint without item identity, brewing credentials or effects; they cannot be extracted as genuine ingredients. Registrations participate in reload rollback and addon/item-removal cleanup.

## Declared Output Variants

Decorator-backed dynamic recipes can declare `"output_variants": [{"output": "ORCHARD_APPLE_JUICE", "selections": [0]}]`. Each entry links a named result to this recipe and supplies one zero-based ingredient-option index per slot for its preview. The decorator still constructs and validates the actual output. Remap selections when optional addon options are filtered. One Juicer recipe supports all pure outputs and mixed juice without duplicate recipes.

## Minimum Recipe

```json
{
  "id": "SWEET_PANCAKES",
  "station": "FRYING_PAN",
  "output": "PANCAKES",
  "processing_time": 160,
  "ingredients": [
    { "type": "REQUIRED", "max": 1, "options": [{ "custom_item": "BAG_OF_FLOUR" }] },
    { "type": "REQUIRED", "max": 1, "options": [{ "item": "EGG" }] },
    { "type": "OPTIONAL", "max": 1, "options": [{ "item": "HONEY_BOTTLE" }] }
  ],
  "actions": [
    { "type": "SET_PROPERTY", "key": "NAME", "value": "Sweet Pancakes" },
    { "type": "ADD_METADATA", "key": "food_property", "value": "SWEET" }
  ]
}
```

## Advanced Pattern: Property Chain

Put properties on intermediate ingredients when you want players to build stronger food through multiple steps. For example, jam can get `CHORUS` from chorus fruit, then pancakes inherit that property when the jam is used as a topping.

Use `required_property` on an individual ingredient option when a recipe must accept only a matching ingredient that carries a specific inherited property:

```json
{
  "type": "REQUIRED",
  "max": 1,
  "options": [
    { "custom_item": "DOUGH", "required_property": "CORNMEAL" }
  ]
}
```

This accepts Dough made from Cornmeal and rejects ordinary flour Dough. Property names are case-insensitive, and the required property appears in recipe previews.

## Universal recipe item references

Every recipe-emitted item position uses the same identity shape: exactly one of `item`, `custom_item`, or `provider_item`, plus an optional sibling `amount`. This applies to the primary `output`, each `weighted_outputs` entry, every `byproducts` entry, and the item emitted by `SET_RETURN_ITEM` or `SET_CONSUME_RETURN`.

```json
{
  "output": { "custom_item": "PANCAKES", "amount": 2 },
  "weighted_outputs": [
    { "item": "BOWL", "amount": 1, "weight": 5 },
    { "provider_item": "mmoitems:CONSUMABLE:Lucky_Bite", "amount": 1, "weight": 1 }
  ],
  "byproducts": [
    { "item": "GLASS_BOTTLE", "amount": 1 },
    { "provider_item": "craftengine:my_pack:spent_filter", "amount": 1 }
  ],
  "actions": [
    { "type": "SET_RETURN_ITEM", "provider_item": "itemsadder:my_pack:mixing_bowl", "amount": 1 },
    { "type": "SET_CONSUME_RETURN", "provider_item": "mmoitems:MISCELLANEOUS:Empty_Vial", "amount": 1 }
  ]
}
```

The object form is the preferred authoring format. Existing content remains valid: a legacy string primary `output`, a weighted entry's legacy `output` or `item`, a byproduct's legacy `item`, and an action's legacy `value` are all interpreted as item references. Do not put two identity fields in one object; `item`, `custom_item`, and `provider_item` are mutually exclusive. `amount` belongs next to the chosen identity (and is context-specific: stack size for outputs, byproducts, and returns, never part of the provider ID).

Provider names are normalized (`MMOITEMS`, `mmoitems`, and `MmoItems` name the same provider), but everything after the first colon is provider-owned and preserves its exact casing. For MMOItems, both the `TYPE` and `ID` therefore remain exact: `mmoitems:SWORD:POISONED_SWORD` is not interchangeable with a differently cased suffix.

## MMOItems sword example

This Cutting Board recipe consumes one MMOItems poison berry, a vanilla iron ingot, and a stick to create an MMOItems sword. The primary output uses the flattened reference directly; the recipe has no separate provider-specific output field.

```json
{
  "id": "MMOITEMS_POISONED_SWORD",
  "station": "CUTTING_BOARD",
  "output": { "provider_item": "mmoitems:SWORD:POISONED_SWORD", "amount": 1 },
  "processing_time": 100,
  "ingredients": [
    { "type": "REQUIRED", "max": 1, "options": [{ "provider_item": "mmoitems:MATERIAL:POISON_BERRIES" }] },
    { "type": "REQUIRED", "max": 1, "options": [{ "item": "IRON_INGOT" }] },
    { "type": "REQUIRED", "max": 1, "options": [{ "item": "STICK" }] }
  ]
}
```

## Availability and provider-owned stacks

Providers and their templates are optional. A missing provider or referenced template leaves the recipe registered and visible, but marks it unavailable with the missing reference as the reason. Heirloom preflights the primary result, every weighted alternative, byproducts, and required return references before consuming ingredients; it never partially crafts or consumes inputs after a failed preflight.

Stacks created by a provider are opaque. Heirloom does not add PDC, lore, quality, dietary data, names, textures, visuals, or any other output mutation to them. A provider byproduct cannot set `inherit_metadata: true`. If any possible primary result is provider-owned, output-mutating actions are invalid, including `SET_CONSUME_RETURN`; `SET_RETURN_ITEM` is a separate emitted stack and is not an output mutation. An ordinary Heirloom primary result may use either action to emit a provider craft return or consume return.

## Common Rule Actions

- `SET_PROPERTY` with key `NAME`: changes display name.
- `ADD_METADATA` with key `food_property`: adds a food property that can be inherited and applied when eaten.
- `SET_RETURN_ITEM`: emits a return stack when crafting completes; its item reference may be provider-owned.
- `SET_CONSUME_RETURN`: records an item reference to emit after eating; it may be provider-owned only when the primary result is an ordinary Heirloom item.
- `SET_VISUAL_ITEM`: swaps to a provider-neutral visual variant.
- `ADD_QUALITY` and `SET_QUALITY`: tune output quality.

## Common Mistakes

- Using `SET_PROPERTY` for `food_property`; bundled property recipes use `ADD_METADATA` for inherited food properties.
- Putting a custom item in `item` instead of `custom_item`.

## External provider ingredients

Use one provider-prefixed field to accept an exact item owned by Nexo, ItemsAdder, CraftEngine, or MMOItems:

```json
{ "provider_item": "nexo:tomato" }
{ "provider_item": "itemsadder:my_pack:tomato" }
{ "provider_item": "craftengine:my_pack:tomato" }
{ "provider_item": "mmoitems:MATERIAL:POISON_BERRIES" }
```

Only the first colon is a separator. The provider ID after it is passed unchanged to the provider API. `provider_item` works in ingredient options and dynamic rule matchers, as well as every recipe-emitted item position described above. Providers remain optional; unavailable options stay visible but cannot match, and other valid options continue to work. Exact provider identity is required, so an external item never matches as its underlying vanilla material.
- Forgetting that optional slots default to `0-max`, so rules must handle the missing-input case.
- Editing JSON and testing only `/hl give`; recipe actions and inheritance only appear when the recipe is crafted.

## How To Test

Run `/hl reload`, search the recipe, craft every branch you changed, and inspect lore. For inheritance tests, craft the intermediate ingredient first, then use that exact item in the next recipe.
