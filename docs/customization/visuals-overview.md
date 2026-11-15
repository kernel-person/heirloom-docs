# Visual Integrations Overview

Heirloom works without a resource pack by using vanilla materials and player-head textures. Optional providers can replace that presentation.

## Provider-Neutral Flow

1. Item definitions declare `visual_id`.
2. Recipes can call `SET_VISUAL_ITEM`.
3. `VisualItemResolver` asks registered providers for that visual.
4. If no provider has it, Heirloom falls back to the normal item.

This keeps visual mapping data independent from Nexo, ItemsAdder, CraftEngine, or MMOItems. Direct `provider_item` recipe references are a different feature: use them only when the recipe deliberately requires or emits that provider's exact stack.

## Practical Rule

Use Heirloom item IDs and visual IDs as stable public names. Let Nexo, ItemsAdder, CraftEngine, or MMOItems map those names to models. Do not bake a provider namespace into a recipe unless the recipe deliberately needs that exact provider stack.
