# Distillery Commands And Permissions

Use `/hld`.

| Command | Purpose | Permission |
| --- | --- | --- |
| `/hld help` | Help | `heirloom.distillery.use` |
| `/hld info` | Addon info | `heirloom.distillery.use` |
| `/hld menu` | Drink catalog and editable recipe previews | `heirloom.distillery.use` |
| `/hld guide` | Ingredients, stations, quality, history and sobering | `heirloom.distillery.use` |
| `/hld tutorial` | Interactive brewing lessons | `heirloom.distillery.use` + `heirloom.tutorial` |
| `/hld list` | List items | `heirloom.distillery.use` |
| `/hld stats <item>` | Ingredient stats | `heirloom.distillery.use` |
| `/hld drunk [player]` | Drunkenness in ‰, on the 0–4‰ game scale | self use, others admin |
| `/hld setdrunk <player> <cl\|value‰>` | Set drunkenness; bare numbers retain equivalent cl | `heirloom.distillery.admin` |
| `/hld adddrunk <player> <cl\|value‰>` | Adjust drunkenness; negative values sober | `heirloom.distillery.admin` |
| `/hld give <item> [amount]` | Give items | `heirloom.distillery.admin` |
| `/hld reload` | Reload | `heirloom.distillery.admin` |
| `/hld devmode [on|off|status]` | Fast processing mode | `heirloom.distillery.admin` |
| `/hld lab` | Brew Lab | `heirloom.distillery.admin` |

`heirloom.crop.grape` allows grape planting and defaults to `true`. Distillery owns this permission along with its grape definitions.
