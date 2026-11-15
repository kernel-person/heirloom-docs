# Recipe Actions And Rules

Recipe actions modify output after a recipe matches.

| Action | Purpose |
| --- | --- |
| `SET_PROPERTY` | Set metadata such as display name or `food_property` |
| `ADD_QUALITY` | Add quality to output |
| `SET_QUALITY` | Set output quality |
| `SET_TEXTURE` | Change player-head texture; source-derived wiki recipe tables show distinct output variants when rules set different textures |
| `SET_VISUAL_ITEM` | Swap output to a provider-neutral visual item |
| `SET_RETURN_ITEM` | Emit a craft return; accepts a universal item reference and does not mutate the primary result |
| `SET_CONSUME_RETURN` | Store a consume return reference for an ordinary Heirloom primary result; invalid for provider-owned primary results |

Common triggers include `HAS_INPUT`, `HAS_ANY_INGREDIENT`, `HAS_ALL_INGREDIENTS`, `HAS_INGREDIENT_PROPERTY`, `HAS_ALL_INGREDIENT_PROPERTIES`, and `INPUT_COUNT_GTE`.
