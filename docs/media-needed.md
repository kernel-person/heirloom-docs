# Media Needed

Capture these in-game images and GIFs before publishing a fully visual version of the wiki. Keep captures clean: default UI scale, readable chat/action bars, no unrelated builds in frame, and one subject per shot.

## Highest Priority

| Page | Needed media | Notes |
| --- | --- | --- |
| Home | Current kitchen overview screenshot | Show all five core stations in one compact kitchen. |
| First Farm | Planting and harvest flow screenshots | Still crop images exist; capture the interaction flow. |
| Favourite Food | Favourite food GUI screenshot | Show current favourite and selection state. |
| Placeable Foods | Feast before/after serving screenshots | Include servings remaining if visible. |
| Cafe | Drink flow screenshot set | Barista Machine still exists; add espresso, latte, and tea flow. |

## Heirloom Mixology capture brief

Capture the released head-based content on the matching Core build. Use actual in-game scenes at 1920×1080 or higher, 16:9, with normal field of view, readable action bars and clean surroundings. Keep the source video with game audio; export short MP4/WebM clips and a lightweight GIF only where needed. No mock gameplay, fabricated interfaces or unfinished provider sprites. Record the Core/addon versions and optional addons with each capture.

| Capture | Required framing and action | Deliverable / placement | Filenames |
| --- | --- | --- | --- |
| Wide hero | A compact outdoor bar beside a mature fruit grove; frame the complete Mixology Table, Juicer and several ripe fruits. Show the active player-head visuals in daylight. Leave the upper corners clear for an optional title crop. | 2560×1440 still, with a clean 1600×800 crop; overview hero. | `orchard-hero.png`, `orchard-hero-marketplace.png` |
| Normal shaker | Fixed three-quarter view close enough to see body, lid and cap knob. Record one complete eight-second real recipe from ingredients through closing, shaking, colored particles, settling and three-drink output. Include the progress bar and game sound. | 12–15 second clip; Mixology Table guide and listing. | `orchard-shaker.mp4` |
| Perfect shaker | Use verified Perfect-quality ingredients/results. Capture both Toss and catch and Grand finale with sparkle trail and chime, followed by the output lore showing Perfect. Debug previews may be a separately labeled animation comparison, never evidence of crafting or quality. | Two 12–15 second clips plus one lore still; Mixology guide. | `orchard-perfect-shake.mp4` (Toss and catch), `orchard-perfect-grand-finale.mp4`, `orchard-perfect-lore.png` |
| Juicer blend and two pours | Frame the full Dropper → Glass → carpet structure. Insert three visibly different produce items, show the full ten-second blend, then pour twice with Glass Bottles. Hold briefly on the full, half-full and empty levels and show two bottles received. | 18–25 second clip; Juicer guide. | `orchard-juicer.mp4` |
| Orchard growth | Show one normal tree, one palm and Pineapple, with unripe and ripe fruit in the same view. Include direct fruit planting and a bonemeal growth step in a separate close shot. | Two stills and a short planting/growth clip; growing section. | `orchard-growing.png`, `orchard-ripe-fruit.png`, `orchard-planting.mp4` |
| Bow harvest | Aim at a ripe hanging fruit, fire one arrow, follow the quality-preserving dropped item and show that the node begins regrowing. Keep the tree attachment and fruit visible throughout. | 8–12 second clip; harvesting section. | `orchard-bow-harvest.mp4` |
| Recipe GUI and three-glass row | Show the filtered Mixology item/recipe browser, select a pure-juice drink and one dynamic variant, then capture a finished batch's centered three-glass row on the table. Keep input quantities and output count readable; include a matching item-lore still. | GUI stills plus one world still; overview and recipe guide. | `orchard-recipe-preview.png`, `orchard-recipe-variant.png`, `orchard-three-glass-row.png`, `orchard-drink-lore.png` |
| Station construction | In an uncluttered area, show an iron block with a wooden pressure plate and, separately, an upward-facing Dropper with clear Glass and any carpet. Use side and three-quarter angles; show the correct interaction surface. | One paired 1920×1080 construction sheet; station pages. | `orchard-station-builds.png` |

Store approved captures under `docs/images/addons/mixology/` or `docs/images/stations/` and add them only after checking the real files. Missing captures must leave the page readable without image placeholders. The graphic branding banner is not a gameplay screenshot. The owner has supplied the coconut bow-harvest, Juicer and Mixology Table clips, now shown in their guides. The remaining capture requests above still apply; automated checks do not prove client rendering.

## Advanced / Server Owner

| Page | Needed media | Notes |
| --- | --- | --- |
| Visual Integrations | Nexo/ItemsAdder/CraftEngine/MMOItems comparison | Same item with fallback and custom visual. |
| Diagnostics | `/hl debug test` output | Use a clean successful run. |
| Region Protection | Protected-region denial action bar | Show crop or station interaction blocked. |
| Dietary Properties | Item lore examples | Vegan/Vegetarian/Gluten-Free plus Contains line. |

## Recipe Icon Gaps

These are generated from the latest icon pass. Tag entries use a generic tag icon by design. Missing custom or Minecraft icons should be replaced with local PNGs under `docs/images/items/`.

| Kind | ID | Reason |
| --- | --- | --- |
| custom | `PUFF_PASTRY` | no cached custom icon |

## Distillery

Existing Distillery GIFs are usable. Add still screenshots for the Distillery drink catalog, editable recipe preview, cellar controls, Brew Lab, and drunk level/status output.
