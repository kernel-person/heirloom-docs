# Drink Families

The table and ingredient lists below are generated from Distillery's bundled `beverage-affinities.json`. They describe the defaults; the in-game guide shows the server's current catalog and available ingredients.

A named base normally needs **at least two-thirds** suitable ingredients: four of a default six-item mash. Specific bases such as apples, grapes, rice and corn take precedence within their broader fruit or grain family. Pure suitable batches earn full composition credit. The rules use proportions when a server changes the batch size.

The boiling column describes full process-quality credit. Raw grain and rice wort can still ferment, and boiling does not change their ABV.

| Base | Fermented drink | Spirit | Boil for full process credit | Preferred distillations |
| --- | --- | --- | --- | --- |
| Potato | Potato Wash | Potato Vodka | No | 3 |
| Cactus | Cactus Wash | Tequila | No | 2 |
| Cane | Cane Wash | Rum | No | 2 |
| Honey | Mead | Honey Spirit | No | 2 |
| Apple | Cider | Apple Brandy | No | 2 |
| Grape | Wine | Brandy | No | 2 |
| Rice | Sake | Rice Spirit | Yes | 2 |
| Corn | Corn Beer | Corn Whiskey | Yes | 2 |
| Fruit | Fruit Wine | Fruit Brandy | No | 2 |
| Grain | Beer | Whiskey | Yes | 2 |
| Generic | Fermented Beverage | Moonshine | No | 2 |

### Potato Wash / Potato Vodka

Suitable ingredients: Potato, Poisonous Potato.

### Cactus Wash / Tequila

Suitable ingredients: Cactus.

### Cane Wash / Rum

Suitable ingredients: Sugar Cane, Sugar. At least 50% of the whole batch must be Sugar Cane.

### Mead / Honey Spirit

Suitable ingredients: Honey Bottle, Honeycomb.

### Cider / Apple Brandy

Suitable ingredients: Apple, Golden Apple, Enchanted Golden Apple.

### Wine / Brandy

Suitable ingredients: Renoit Grape, Cherimola Blan Grape, Meloire Grape, Cranerlet Nuala Grape, Gralladina Fran Grape.

### Sake / Rice Spirit

Suitable ingredients: Rice.

### Corn Beer / Corn Whiskey

Suitable ingredients: Corn.

### Fruit Wine / Fruit Brandy

Suitable ingredients: Renoit Grape, Cherimola Blan Grape, Meloire Grape, Cranerlet Nuala Grape, Gralladina Fran Grape, Apple, Golden Apple, Enchanted Golden Apple, Sweet Berries, Glow Berries, Melon Slice, Glistering Melon Slice, Chorus Fruit, Mango, Bananas, Coconut, Lemon, Orange, Pineapple, Avocado.

### Beer / Whiskey

Suitable ingredients: Wheat, Corn, Rice, Wheat Seeds, Beetroot Seeds, Pumpkin Seeds, Melon Seeds, Torchflower Seeds, Pitcher Pod.

### Fermented Beverage / Moonshine

Unrelated mixtures remain in this family. They do not earn named-family mastery.

## Prepared wines, beers and high-proof spirits

Skin all grape inputs for White Wine, some for Rosé, or leave them whole for Wine. Skinning reduces the grapes' tannins and shifts their blended tint. Roasted shares are measured among grain inputs: at least half selects Irish Stout, one-third Porter, and one-sixth Irish Red Ale. Pale batches with at least two-thirds Wheat among their grains become Wheat Beer; the remaining pale batches start as Ale and can become Lager after three recorded cool rack days. Rice/Sake and Corn/Corn Beer keep their more specific family precedence. Ordinary beer craftsmanship takes one day; Lager takes three cool days.

Porter and Irish Stout intentionally reuse the same [dark-beer player head](https://textures.minecraft.net/texture/b8ce8a802031ad53dee7a05b94f2f118d383495228070437aa7dced6cf9aadfa). Their ingredient proportions and drink identities remain distinct.

The following ordered routes are generated from the same catalog as production. Earlier qualifying routes take precedence; administrator-edited thresholds and names appear here when the source is regenerated.

| Named drink | Stage | Eligible base | Additional requirements |
| --- | --- | --- | --- |
| Spirytus Rektyfikowany | Distilled | Potato, Grain, Corn, Rice, Generic | Potato, Poisonous Potato, Wheat, Corn, Rice, Wheat Seeds, Beetroot Seeds, Pumpkin Seeds, Melon Seeds, Torchflower Seeds, Pitcher Pod: ≥2/3 and ≤100% of the whole batch<br>At least 95% ABV<br>Preferred distillations: 21 |
| Taxi Vodka | Distilled | Potato | At least 80% ABV<br>Preferred distillations: 8 |
| White Wine | Fermented | Grape | Skinned ingredients: 100% of grape inputs |
| Rosé | Fermented | Grape | Skinned ingredients: >0% and <100% of grape inputs |
| Irish Stout | Fermented | Grain | Roasted ingredients: ≥1/2 and ≤100% of grain inputs |
| Porter | Fermented | Grain | Roasted ingredients: ≥1/3 and ≤100% of grain inputs |
| Irish Red Ale | Fermented | Grain | Roasted ingredients: ≥1/6 and ≤100% of grain inputs |
| Wheat Beer | Fermented | Grain | Wheat: ≥2/3 and ≤100% of grain inputs |
| Lager | Fermented | Grain | Roasted ingredients: ≥0% and <1/6 of grain inputs<br>Wheat: ≥0% and <2/3 of grain inputs<br>3 cool days recorded in the rack |
| Ale | Fermented | Grain | Otherwise, after earlier matching routes |

Ingredients supplied by another addon are usable only while their definitions are available. Family identity is separate from [maturation style](cellar-aging.md): a finished or reserve Whiskey remains in the same family for compatible Mixology recipes.
