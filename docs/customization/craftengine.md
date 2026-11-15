# CraftEngine Integration

CraftEngine is a soft dependency. Use provider-neutral `visual_id` mappings when a normal Heirloom item only needs a different presentation, or use an exact `provider_item` reference when a recipe must consume or emit a CraftEngine-owned stack.

## Exact item references

```json
{ "provider_item": "craftengine:my_pack:tomato" }
```

The `craftengine` provider name is case-insensitive, while `my_pack:tomato` is passed to CraftEngine unchanged. If CraftEngine or the referenced item is unavailable, affected recipes remain visible and unavailable instead of consuming ingredients.
