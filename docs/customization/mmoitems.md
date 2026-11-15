# MMOItems Integration

MMOItems is a soft, optional integration. Heirloom does not bundle MMOItems or MythicLib, and it continues to load when either is absent. Install and configure MMOItems and MythicLib separately before enabling recipes that reference MMOItems stacks.

## Exact MMOItems references

Use the flattened form `mmoitems:<TYPE>:<ID>` for inputs and every recipe-emitted item position:

```json
{ "provider_item": "mmoitems:MATERIAL:POISON_BERRIES" }
{ "provider_item": "mmoitems:SWORD:POISONED_SWORD", "amount": 1 }
```

The provider name is normalized, but the MMOItems suffix is exact and case-preserving. Keep both `TYPE` and `ID` exactly as MMOItems defines them. Missing MMOItems or a missing template does not hide or deregister the recipe; Heirloom shows it as unavailable, preflights every weighted result and required emitted reference, and consumes nothing.

## Resource-pack merge

Normal generated Heirloom visuals use the MMOItems type/id convention `MISCELLANEOUS:HEIRLOOM_<ID>`. In the supplied YAML fragment, merge each root `HEIRLOOM_<ID>` entry into `plugins/MMOItems/item/miscellaneous.yml`; keep its `model` field inside `base`. Separately merge `mmoitems/resourcepack/assets/heirloom/` into the resource pack your server builds and delivers. MMOItems does not build or distribute that pack for you, and Heirloom does not replace your pack's deployment workflow.

See the [official MMOItems item-textures documentation](https://docs.phoenixdevt.fr/mmoitems/features/item-textures.html) for the resource-pack side of the setup. When MMOItems reloads, Heirloom refreshes the provider on the next Bukkit tick so the refreshed MMOItems registry is ready first.

## Opaque result rule

An MMOItems stack created as a primary result remains owned by MMOItems: Heirloom cannot add lore, PDC, names, textures, quality, dietary data, or a consume return to it. Use an ordinary Heirloom primary output when you need output-mutating actions; that ordinary result may still return an MMOItems stack on craft or consumption.
