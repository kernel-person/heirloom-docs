# Cellar Aging

Build the Aging Rack with a **normal barrel directly on Scaffolding**. Its vanilla inventory holds drinks and, with Pasture installed, cheese. Distillery needs no separate rack or timer and works without Pasture.

One aging day is **20 real minutes** by default. The preview offers 0, 1, 3, 14, 60 and 360 days; at the standard twenty-minute day, 360 days means **five real days**. Aging happens only while a bottle is in a valid rack; inventory and chest storage pause it. Removing and returning a bottle preserves its earned progress. Eligible clean offline time is retained, while missing addon registrations and invalid rack intervals are excluded. Hoppers cannot transfer items into or out of the rack.

Fresh fermented drinks and spirits can be used immediately. Targets describe the work needed for a developed style and full craftsmanship. Quality safely plateaus: extra time never spoils a drink, and aging does not change its ABV, serving volume or total alcohol.

## Choose one wood type

Put Oak, Dark Oak, Cherry or Acacia planks in the same barrel. One unique supported species treats every eligible bottle; the planks are reusable and extra planks do not increase their effect. With no supported planks, bottles rest neutrally. Unsupported wood does nothing. Multiple supported species suspend wood-specific progress while ordinary maturation continues; the bottle asks you to use one wood type.

Swapping wood preserves earned exposure. Cheese ignores the plank treatment and keeps Pasture's finish-on-removal behavior. No wood is best for every drink.

## Find the right cellar climate

The rack reads the biome temperature and humidity at the barrel. An ordinary **Forest, Dark Forest or Taiga** is cool and humid. Birch Forest and Snowy Taiga do not meet the humid threshold. A roof or underground room is optional for Distillery drinks; placing water or ice nearby does not change their cellar climate.

Cool means a biome temperature below 0.8; humid means at least 80% biome humidity. These are Minecraft biome values, not degrees Celsius or a measurement of nearby water. Wine keeps aging in every climate, while its preferred cool/humid exposure helps craftsmanship.

You can mash, ferment and distil in any biome. Ingredients and processing determine the drink family: moving Wine to a warm biome does not turn it into Rum. Different drinks prefer different cellar climates, shown below. Some specific styles require recorded climate exposure, such as Lager's three cool aging days; ordinary aging still continues outside that preferred climate.

## Read the rack report

Open a real Aging Rack to see a formatted chat report with its named climate, the current drink wood treatment, and grouped contents. Each group shows progress, the style it is developing toward, and the next useful step. Hover the report entries for more detail; a full rack shows a short summary with additional groups in hover text.

The report uses the server's current aging rules and distinguishes time earned from any climate or wood work still needed. A young wine is not marked ready just because one cellar day passed. Cheese guidance describes its current aging progress without guaranteeing the final cheese before removal. A rack without ageable contents explains how to start.

For a hands-on demonstration, run `/hl tutorial aging` or `/hld tutorial aging`. The practice barrel supplies temporary bottles and wood, demonstrates mixing and removing wood, accelerates maturation, and lets you collect the result. Your real inventory is preserved.

## Default maturation routes

These routes are generated from `beverage-affinities.json`, including the neutral resting routes for Honey Spirit and Rice Spirit.

| Drink or style | Target in the rack | Preferred climate | Treatment |
| --- | --- | --- | --- |
| Beer / Corn Beer | 1 day (20m) | Temperate / Normal | Neutral |
| Sake | 3 days (1h) | Cool / Normal | Neutral |
| Cider | 3 days (1h) | Cool / Normal | Neutral |
| Mead | 14 days (4h40m) | Temperate / Normal | Neutral |
| Wine / Fruit Wine | 14 days (4h40m) | Cool / Humid | Neutral |
| Oak-aged Wine / Oak-aged Fruit Wine | 60 days (20h) | Cool / Humid | Oak or Dark Oak |
| Acacia-aged Wine / Acacia-aged Fruit Wine | 60 days (20h) | Cool / Humid | Acacia |
| Potato Vodka | 1 day (20m) | Cool / Dry | Neutral |
| Tequila Blanco | 1 day (20m) | Warm / Dry | Neutral |
| Tequila Reposado | 14 days (4h40m) | Warm / Dry | Oak or Dark Oak |
| Tequila Añejo | 60 days (20h) | Warm / Dry | Oak or Dark Oak |
| White Rum | 1 day (20m) | Warm / Humid | Neutral |
| Aged Rum | 14 days (4h40m) | Warm / Humid | Oak |
| Dark Rum | 60 days (20h) | Warm / Humid | Dark Oak |
| Whiskey / Corn Whiskey | 14 days (4h40m) | Temperate / Normal | Oak or Dark Oak |
| Reserve Whiskey / Reserve Corn Whiskey | 360 days (120h) | Temperate / Normal | Oak or Dark Oak |
| Brandy / Apple Brandy / Fruit Brandy | 14 days (4h40m) | Temperate / Dry | Oak or Dark Oak |
| Reserve Brandy / Reserve Apple Brandy / Reserve Fruit Brandy | 360 days (120h) | Temperate / Dry | Oak or Dark Oak |
| Sakura-finished Whiskey / Sakura-finished Corn Whiskey | 60 days (20h) | Temperate / Normal | 45 days Oak or Dark Oak, then 15 days Cherry |
| Acacia-finished Whiskey / Acacia-finished Corn Whiskey | 60 days (20h) | Temperate / Normal | 45 days Oak or Dark Oak, then 15 days Acacia |
| Honey Spirit | 3 days (1h) | Temperate / Normal | Neutral |
| Rice Spirit | 3 days (1h) | Cool / Normal | Neutral |
| Sparkling Wine | 60 days (20h) | Cool / Humid | Neutral |
| Oak-aged Sparkling Wine | 60 days (20h) | Cool / Humid | Oak or Dark Oak |
| Acacia-aged Sparkling Wine | 60 days (20h) | Cool / Humid | Acacia |
| Lager | 3 days (1h) | Cool / Normal | Neutral |
| Taxi Vodka | 1 day (20m) | Cool / Dry | Neutral |
| Spirytus Rektyfikowany | 1 day (20m) | Cool / Dry | Neutral |

For specialty finishes, complete the Oak or Dark Oak base phase **before** the Cherry or Acacia phase. Earlier finishing-wood exposure cannot substitute for the later finish. Wood-named styles require actual exposure to that wood; neutral resting cannot replace it.

The listed climate is a preference for full craftsmanship. Full climate credit requires preferred exposure equal to **75% of the target duration**. The bottle gives a practical next step without requiring players to read a score dashboard. See [Craftsmanship](craftsmanship.md) for quality and [Configuration](configuration.md) for editable defaults.
