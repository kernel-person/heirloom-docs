# Beverage Craftsmanship

Quality uses Heirloom's existing **Poor → Normal → Good → Great → Excellent → Perfect** dice and names. Your ingredients, processing and cellar work shape it; there is no separate star rating.

Start with a suitable base, boil grain or rice wort for full process-quality credit, ferment, and use the preferred distillation count for spirits. Raw grain and rice fermentation is also allowed; boiling improves process quality without changing ABV. Then complete the maturation, climate and wood or neutral-resting requirements of a chosen style. Ingredient quality is averaged by quantity; ungraded vanilla ingredients count as Normal. A mixture of unrelated ingredients cannot earn named-family mastery.

Ordinary results reach Excellent. **Perfect has a 5% default chance for a fully qualified batch** with at least Normal average ingredient quality. The random value is generated once when the mash is created and remains shared by every serving and later processing stage. Opening, collection, splitting, wood changes, further distillation and reloads never reroll it. A mastered batch that misses Perfect stays Excellent; its guidance does not ask for another roll.

Earned contributions do not stack through repeated removal and do not decline merely because more time passes. A bottle explains its developing style, achieved characteristics and next useful improvement. Distillery and Pasture use the same Core ranking and recommendation implementation with separate domain catalogs.

## Existing stock

Valid old bottles retain their identity, ABV, serving amount and quality. Their creation dates are provenance, not earned cellar time. They can develop styles from future rack exposure, but missing ingredient ancestry is not invented and they receive no new Perfect lottery.

The longer aging defaults preserve validated styles and quality already earned by existing stock. Stored exposure remains its actual elapsed time; it is not multiplied to match new targets. Further development follows the current catalog. Unchanged previous timing defaults upgrade automatically while administrator-edited entries are retained.

Keep `beverage-affinities-v1.snapshot.json` with your server backups. Migration saves the exact old installed rules once so stored bottles can retain achievements earned under administrator-edited targets. Missing historical evidence is not reconstructed from current defaults.

Old Distillery brewing powers have been retired. Identifiable generated effects and power lore are removed lazily when genuine bottles are exposed or consumed; unrelated metadata, notes, names and effects of unknown ownership are preserved. The alcohol intake, drunkenness, recovery and Mixology serving calculations are unchanged. See [Inebriation](inebriation.md) for the existing gameplay scale.
